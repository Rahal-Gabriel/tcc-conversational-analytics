# GUIA_DESENVOLVIMENTO.md - Conversational Analytics em saúde (protótipo de TCC)

Hub de navegação e instruções para trabalhar neste repositório. Leia-o no início
de cada sessão. O conteúdo detalhado (arquitetura, camadas, governança,
avaliação) vive na documentação modular em [docs/](docs/), e este arquivo aponta
para ela (fonte única de verdade, sem duplicação).

> A forma desta documentação foi inspirada na arquitetura de documentação do
> projeto Command Center (HSL): portal de índice, modularização numerada,
> identificadores estáveis, ciclo de status e rastreabilidade ao código.

## Propósito

Protótipo funcional de uma arquitetura de referência para consulta em linguagem
natural sobre dados clínicos, com governança integrada e projetada para atender à LGPD, às
normas da ANVISA e às diretrizes da ANPD. O domínio é a **ocupação de leitos
hospitalares**. Toda a pesquisa usa dados **100% sintéticos**.

## Princípios inegociáveis (regras críticas)

Antes de qualquer alteração relevante, verifique
[docs/arquitetura/03_REGRAS_CRITICAS.md](docs/arquitetura/03_REGRAS_CRITICAS.md).
Em resumo:

- `RNC-001` Dados exclusivamente sintéticos, em toda etapa.
- `RNC-002` Acurácia só vem de execução real do LLM; o oráculo é apenas
  autoteste e nunca é apresentado como desempenho do modelo.
- `RNC-003` Determinismo por `SEED` e `SIM_TODAY`.
- `RNC-004` Nenhuma credencial no código ou no histórico do git.
- `RNC-005` PII nunca sobrevive à Silver.

## Como usar esta documentação

### Para entender o sistema rapidamente
1. [docs/README.md](docs/README.md) - portal e índice.
2. [docs/arquitetura/01_VISAO_GERAL.md](docs/arquitetura/01_VISAO_GERAL.md) - as
   quatro camadas e o fluxo de dados.
3. [docs/arquitetura/03_REGRAS_CRITICAS.md](docs/arquitetura/03_REGRAS_CRITICAS.md)
   - o que nunca pode ser violado.

### Para implementar uma camada ou controle
1. Leia o módulo da camada em [docs/camadas/](docs/camadas/).
2. Consulte as decisões relevantes (`DA-*`) em
   [docs/arquitetura/02_DECISOES_ARQUITETURAIS.md](docs/arquitetura/02_DECISOES_ARQUITETURAIS.md).
3. Para controles de governança, cruze com
   [docs/governanca/01_CONFORMIDADE_REGULATORIA.md](docs/governanca/01_CONFORMIDADE_REGULATORIA.md)
   (`REG-*` ↔ `CTRL-*`).
4. Atualize o status do módulo e os números do portal ao concluir.

### Para escrever o TCC (Resultados Preliminares e versão final)
1. [docs/tcc/02_MAPA_DOC_PARA_TEMPLATE.md](docs/tcc/02_MAPA_DOC_PARA_TEMPLATE.md)
   - qual módulo alimenta cada seção do template.
2. [docs/tcc/01_RESULTADOS_PRELIMINARES.md](docs/tcc/01_RESULTADOS_PRELIMINARES.md)
   - registro vivo dos resultados verificáveis (`RES-*`).
3. [docs/referencias/README.md](docs/referencias/README.md) - base de literatura
   em fichas por tema; toda citação do TCC deve sair daqui, e a lista formatada
   está em [docs/referencias/08_REFERENCIAS_FORMATADAS.md](docs/referencias/08_REFERENCIAS_FORMATADAS.md).
4. [docs/referencias/07_MAPA_LITERATURA_PARA_CAMINHOS.md](docs/referencias/07_MAPA_LITERATURA_PARA_CAMINHOS.md)
   - antes de desenhar qualquer experimento novo, ler o que a literatura já
   sabe sobre ele. Templates e manual oficiais ficam em `docs-tcc/`.
5. `/banca` - simula a banca examinadora com contexto limpo (agente em
   `.claude/agents/banca.md`) e registra a rodada em
   [docs/tcc/banca/](docs/tcc/banca/README.md). Rodar ao fim de cada etapa
   entregue e antes do depósito.

## Mapa de módulos por área

| Área | Conceito/decisão | Camada(s) | Regulatório | Avaliação |
|---|---|---|---|---|
| Pipeline de dados | DA-LAKE-* | [camadas/01](docs/camadas/01_PIPELINE_LAKEHOUSE.md) | REG-LGPD-001/002/003 | - |
| Governança de entrada | DA-GOV-* | [camadas/02](docs/camadas/02_GOVERNANCA_ENTRADA.md) | REG-LGPD-004/005 | AVAL-002 |
| Motor Text-to-SQL | DA-NL2SQL-* | [camadas/03](docs/camadas/03_MOTOR_TEXT2SQL.md) | REG-PESQ-001 | AVAL-001 |
| Validação de saída | DA-VALID-* | [camadas/04](docs/camadas/04_VALIDACAO_SAIDA.md) | REG-LGPD-006/007, REG-ANPD-001 | AVAL-003 |
| Avaliação | DA-AVAL-* | - | - | [avaliacao/01](docs/avaliacao/01_METODOLOGIA_AVALIACAO.md) |
| Reprodutibilidade | - | - | REG-PESQ-001 | [avaliacao/02](docs/avaliacao/02_REPRODUTIBILIDADE_CI.md) |

## Workflow recomendado

```
1. Identificar a camada/módulo afetado pela tarefa
2. Ler o módulo (decisões, controles, mapeamento para o código)
3. Verificar as regras críticas (RNC-*) que podem ser impactadas
4. Implementar seguindo os padrões documentados
5. Rodar o teste rápido do módulo (python -m src.<modulo>)
6. Atualizar status do módulo e contagens no portal
```

## Prioridades de leitura

| Prioridade | Documento | Quando ler |
|---|---|---|
| CRÍTICA | arquitetura/03_REGRAS_CRITICAS | SEMPRE, antes de qualquer alteração |
| CRÍTICA | governanca/01_CONFORMIDADE_REGULATORIA | Ao mexer em governança, pseudonimização ou minimização |
| ALTA | arquitetura/01_VISAO_GERAL | Ao iniciar trabalho em qualquer camada |
| ALTA | camadas/[N] | Ao implementar a camada correspondente |
| ALTA | tcc/02_MAPA_DOC_PARA_TEMPLATE | Ao redigir qualquer seção do TCC |
| MÉDIA | avaliacao/02_REPRODUTIBILIDADE_CI | Ao mexer em CI, versionamento ou determinismo |

## Estrutura de pastas do código

```
tcc-conversational-analytics/
  GUIA_DESENVOLVIMENTO.md             # este hub de navegação
  README.md             # apresentação do protótipo
  docs/                 # documentação modular (ver docs/README.md)
  run_all.py            # orquestrador: gera dados, constroi pipeline, avalia (oracle / llm --motor local|llm)
  src/
    config.py           # SIM_TODAY, SEED, volumes, perfis, modelo do LLM
    data_gen.py         # geracao sintetica -> Bronze
    pipeline.py         # Bronze -> Silver -> Gold
    governance.py       # guardrails de entrada/saida e auditoria
    nl2sql.py           # motores Text-to-SQL (local via Ollama, API) + oraculo; variantes de prompt
    questions.py        # conjunto de avaliacao (pergunta PT + SQL de referencia)
    evaluate.py         # execution match, desfechos de governanca, Soft F1, auditoria
    matriz.py           # matriz de celulas de prompt (Etapa D): relatorios, resumo e SQL geradas
    adversarial.py      # conjunto adversarial e abstencao (Etapa E): celulas E0/E1, RS(c), familias
  data/                 # banco DuckDB gerado (nao versionar)
  results/              # saidas de avaliacao e log de auditoria (nao versionar)
```

## Convenções de código

- Comentários e mensagens em português, registro técnico mas acessível.
- Não usar travessões; preferir construções naturais com vírgula ou parêntese.
  Esta convenção vale também para a documentação em `docs/`.
- Centralizar parâmetros em `config.py`. Nada de valores mágicos espalhados.
- Cada módulo deve rodar isolado (`python -m` ou bloco `__main__`).
- Escrever um teste rápido por módulo (contagens, pseudonimização e k-anonimato, casos de
  governança que devem ser bloqueados).

## Convenções de identificadores (documentação)

| Prefixo | Tipo |
|---|---|
| `DA-[MOD]-[NUM]` | Decisão Arquitetural |
| `RNC-[NUM]` | Regra Crítica (inegociável) |
| `REG-[NORMA]-[NUM]` | Requisito Regulatório |
| `CTRL-[MOD]-[NUM]` | Controle de Governança |
| `AVAL-[NUM]` | Critério de Avaliação |
| `RES-[NUM]` | Resultado Preliminar |

Ciclo de status dos módulos: `PROJETADO` → `PARCIAL` → `IMPLEMENTADO` →
`VALIDADO`.

## Configuração dos motores reais

Lida do ambiente, nunca embutida no código (`src/config.py`, seções
"Configuração do LLM via API" e "Motor local"). O motor da fase de conclusão é
o **local** (Ollama na própria máquina, sem custo e sem saída de dados); o
motor via API foi o dos Resultados Preliminares.

```bash
# motor local (padrao): exige o servidor do Ollama ativo e o modelo baixado
ollama pull qwen2.5-coder:14b
export OLLAMA_ENDPOINT="http://localhost:11434"   # opcional, padrao
export MODELO_LOCAL="qwen2.5-coder:14b"           # opcional, padrao

# motor via API (opcional)
export ANTHROPIC_API_KEY="sua-chave"
export ANTHROPIC_MODEL="claude-sonnet-4-6"        # opcional, padrao
```

```bash
python run_all.py llm --motor local --celula C2 --repeticoes 3   # uma celula de prompt
python run_all.py llm --motor local --matriz                     # cinco celulas, k=3 (Etapa D)
python run_all.py llm --motor local --adversarial                # E0 e E1 sobre 18 legitimas + 25 adversariais (Etapa E)
```

As células de prompt (C0 a C4) estão pré-registradas em `config.CELULAS`.
Detalhes do contrato do prompt em
[docs/camadas/03_MOTOR_TEXT2SQL.md](docs/camadas/03_MOTOR_TEXT2SQL.md).

## Definição de pronto (por etapa)

- O módulo roda isolado sem erro e o teste rápido passa.
- `run_all.py oracle` completa com autoteste consistente (tubulação correta).
- Os números de pesquisa só são coletados com `run_all.py llm` e um motor real (local com Ollama ativo, ou API com chave válida).
- A documentação do módulo afetado foi atualizada (status, código, contagens).

## Versionamento e CI

Resumo em [docs/avaliacao/02_REPRODUTIBILIDADE_CI.md](docs/avaliacao/02_REPRODUTIBILIDADE_CI.md).
Branch `main` sempre funcional; cada etapa em branch curto e PR com squash; tag
git nos marcos reprodutíveis. A CI roda a cada push/PR usando apenas o motor
oráculo (sem chave, sem custo).
