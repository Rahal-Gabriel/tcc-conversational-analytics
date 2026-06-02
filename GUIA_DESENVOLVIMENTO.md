# GUIA_DESENVOLVIMENTO.md — Conversational Analytics em saúde (protótipo de TCC)

Este arquivo orienta o desenvolvimento do protótipo. Leia-o no início de cada
sessão antes de escrever ou alterar código.

## Objetivo

Protótipo funcional de uma arquitetura de referência para consulta em
linguagem natural sobre dados clínicos, com um modelo de governança integrado
e aderente à LGPD, às normas da ANVISA e às diretrizes da ANPD. O domínio de
implementação e avaliação é a **ocupação de leitos hospitalares**. Toda a
pesquisa usa dados **100% sintéticos**.

## Princípios inegociáveis

- Dados exclusivamente sintéticos. Nenhuma informação real, em nenhuma etapa.
- Integridade dos resultados: números de acurácia só são válidos quando vêm de
  uma execução real do harness com o motor LLM. O motor oráculo serve apenas
  para autoteste da tubulação e nunca deve ser apresentado como desempenho do
  modelo.
- Determinismo e reprodutibilidade: uma SEED fixa e uma data de referência
  (SIM_TODAY) controlam toda a geração de dados e as consultas que mencionam
  "hoje" ou "agora".
- Segurança: nenhuma chave de API no código ou no histórico do git. Sempre via
  variável de ambiente.

## Stack

- Python 3.12.
- DuckDB como Lakehouse local, com schemas `bronze`, `silver` e `gold`. A
  lógica de camadas mapeia para Delta/Databricks, mas o protótipo roda local.
- Faker (locale pt_BR) para geração sintética.
- Biblioteca padrão (urllib) para a chamada HTTP à API da Anthropic. Evitar
  dependências pesadas.

## Estrutura de pastas alvo

```
tcc-conversational-analytics/
  GUIA_DESENVOLVIMENTO.md
  README.md
  requirements.txt
  run_all.py            # orquestrador: gera dados, constroi pipeline, avalia
  src/
    config.py           # SIM_TODAY, SEED, volumes, perfis, modelo do LLM
    data_gen.py         # geracao sintetica -> camada Bronze
    pipeline.py         # Bronze -> Silver -> Gold
    governance.py       # guardrails de entrada/saida e auditoria
    nl2sql.py           # motor Text-to-SQL (LLM real) + motor oraculo
    questions.py        # conjunto de avaliacao (pergunta -> SQL de referencia)
    evaluate.py         # execution-match, governanca, indicadores
  data/                 # banco DuckDB gerado (nao versionar)
  results/              # saidas de avaliacao e log de auditoria (nao versionar)
```

## Modelo de dados

### Bronze (dados brutos, com PII proposital)

A PII existe de propósito para que a anonimização na Silver seja real e
demonstrável.

- `bronze.unidade(id_unidade, nome, especialidade, andar)`
- `bronze.leito(id_leito, id_unidade, tipo, status)`
  - tipo: `UTI` | `Semi-intensiva` | `Enfermaria`
- `bronze.paciente(id_paciente, nome, cpf, data_nascimento, sexo)`
  - nome, cpf e data_nascimento são PII e não podem sobreviver à Silver.
- `bronze.internacao(id_internacao, id_paciente, id_leito, data_admissao, data_alta_prevista, data_alta_real)`
- `bronze.ocupacao_diaria(data, id_leito, situacao, id_internacao)`
  - situacao: `ocupado` | `livre` | `bloqueado`
  - gerar uma série diária cobrindo a janela histórica (ex.: 90 dias até SIM_TODAY).

### Silver (limpa e anonimizada)

- Remover `nome` e `cpf`.
- Pseudonimizar `id_paciente` (hash).
- Derivar `faixa_etaria` a partir de `data_nascimento` (faixas: 0-17, 18-39,
  40-59, 60-79, 80+) e descartar a data de nascimento.
- Ao final, nenhuma coluna de identificação direta pode existir na Silver.

### Gold (única camada exposta ao motor de linguagem)

- `gold.leitos_status(id_leito, id_unidade, unidade, especialidade, tipo, situacao)`
  - snapshot do estado de cada leito em SIM_TODAY.
- `gold.ocupacao_unidade(id_unidade, unidade, especialidade, leitos_total, leitos_ocupados, leitos_livres, leitos_bloqueados, taxa_ocupacao)`
  - taxa_ocupacao em percentual (0 a 100).
- `gold.ocupacao_diaria(data, leitos_total, leitos_ocupados, leitos_livres, leitos_bloqueados, taxa_ocupacao)`
  - série histórica diária do hospital.
- `gold.internacoes(id_internacao, id_unidade, unidade, tipo_leito, faixa_etaria, sexo, data_admissao, data_alta_prevista, data_alta_real, tempo_permanencia, ativa)`
  - ativa = TRUE quando data_alta_real é nula; tempo_permanencia em dias,
    apenas para internações encerradas.

## Camadas da arquitetura (o que cada uma deve fazer)

1. **Pipeline de dados (Lakehouse)**: ingestão dos dados sintéticos na Bronze,
   limpeza e anonimização na Silver, métricas e agregações na Gold.
2. **Governança de entrada**: autenticação por perfil (tabelas Gold
   autorizadas por perfil), registro de toda pergunta e verificação de
   conformidade antes de qualquer execução.
3. **Motor de IA (Text-to-SQL)**: traduz a pergunta em português para uma SQL
   somente leitura sobre a Gold, via LLM, restrita por guardrails.
4. **Validação de saída**: checa aterramento (mitiga alucinação), filtra dados
   sensíveis e registra a resposta para auditoria.

## Governança (requisitos a implementar)

- **Entrada**: a SQL gerada deve ser uma única instrução somente leitura
  (apenas SELECT/WITH); bloquear comandos de escrita ou administrativos
  (insert, update, delete, drop, alter, create, attach, copy, pragma etc.);
  bloquear múltiplas instruções (presença de `;` no meio); bloquear acesso a
  Bronze/Silver; permitir apenas as tabelas Gold autorizadas para o perfil.
- **Aterramento (anti-alucinação)**: toda tabela referenciada na SQL deve
  existir no schema Gold conhecido; caso contrário, bloquear.
- **Saída**: se qualquer coluna do resultado tiver nome de campo sensível
  (nome, cpf, data_nascimento, id_paciente_pseudo), bloquear a resposta.
- **Auditoria**: registrar em log toda pergunta recebida e toda resposta, com
  timestamp, usuário, perfil, SQL e o evento (correto, incorreto, bloqueado,
  erro).

Perfis sugeridos e tabelas autorizadas:
- `gestor`: todas as tabelas Gold.
- `enfermagem`: `gold.leitos_status`, `gold.ocupacao_unidade`.
- `administrativo`: `gold.ocupacao_unidade`, `gold.ocupacao_diaria`.

## Metodologia de avaliação

- Estilo **execution match** do EHRSQL: executar a SQL gerada e a SQL de
  referência e comparar os conjuntos de resultados (normalizados: floats
  arredondados, datas em ISO, linhas ordenadas). Acurácia = fração de
  perguntas com conjuntos idênticos.
- Dois motores intercambiáveis: **LLM** (real, gera os números do TCC) e
  **oráculo** (devolve a SQL de referência, só para autoteste do harness).
- Indicadores adicionais: taxa de aprovação na governança e completude do log
  de auditoria.
- A execução deve usar conexão DuckDB em modo somente leitura (defesa em
  profundidade).

## Convenções de código

- Comentários e mensagens em português, registro técnico mas acessível.
- Não usar travessões; preferir construções naturais com vírgula ou parêntese.
- Centralizar parâmetros em `config.py` (SIM_TODAY, SEED, volumes, perfis,
  modelo do LLM). Nada de valores mágicos espalhados.
- Cada módulo deve poder rodar isolado (`python -m` ou bloco `__main__`).
- Escrever um teste rápido por módulo (contagens, anonimização, casos de
  governança que devem ser bloqueados).

## Configuração do LLM

- `ANTHROPIC_API_KEY`: chave, via ambiente.
- `ANTHROPIC_MODEL`: modelo (ex.: `claude-sonnet-4-6`), via ambiente.
- Endpoint: `https://api.anthropic.com/v1/messages`, header `anthropic-version: 2023-06-01`.
- O prompt do motor deve receber o schema Gold e a data atual, e exigir uma
  única SQL somente leitura, sem markdown e sem explicação.

## Definição de pronto (por etapa)

- O módulo roda isolado sem erro.
- O teste rápido do módulo passa.
- `run_all.py oracle` completa com autoteste consistente (a tubulação está
  correta).
- Os números de pesquisa só são coletados com `run_all.py llm` e chave válida.

## Versionamento

- Ao fim de cada etapa, sempre versionar com a sequência `git commit` seguido
  de `git push` para o repositório remoto (origin). Nenhuma etapa fica só no
  commit local.
- A mensagem de commit deve descrever a etapa em português, registro técnico.