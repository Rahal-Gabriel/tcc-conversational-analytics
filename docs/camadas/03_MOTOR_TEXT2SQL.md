# NL2SQL: Camada 3 - Motor Text-to-SQL

**Status**: VALIDADO (três motores; as cinco células de prompt medidas com o motor local na Etapa D, RES-011: C3 é a célula padrão, 72,2% estrito, Violation e Over-Refusal zero)
**Prioridade**: ALTA
**Última atualização**: 2026-09-20
**Alimenta (template TCC)**: Metodologia · Resultados e Discussão

---

## 1. Propósito

Descrever o motor que traduz uma pergunta em português para uma SQL somente
leitura sobre a camada Gold. O motor existe em três implementações
intercambiáveis, dois motores reais e um oráculo de referência, conforme
[DA-NL2SQL-001](../arquitetura/02_DECISOES_ARQUITETURAIS.md#da-nl2sql-001-motores-intercambiáveis-oráculo-api-e-local)
e [DA-NL2SQL-003](../arquitetura/02_DECISOES_ARQUITETURAIS.md#da-nl2sql-003-motor-local-com-modelo-aberto-servido-pelo-ollama).
O prompt enviado aos motores reais é uma variável experimental, com células
pré-registradas ([DA-NL2SQL-004](../arquitetura/02_DECISOES_ARQUITETURAIS.md#da-nl2sql-004-prompt-como-variável-experimental-pré-registrada)).

## 2. Os três motores

| Motor (`nome`) | Papel | Pré-requisito | Gera os números do TCC? |
|---|---|---|---|
| **Local** (`local`) | Tradução real por modelo aberto servido pelo Ollama na própria máquina (`qwen2.5-coder:14b`) | servidor do Ollama respondendo | **Sim** (fase de conclusão, Etapas D e E) |
| **LLM via API** (`llm`) | Tradução real via API Anthropic (`claude-sonnet-4-6`) | `ANTHROPIC_API_KEY` no ambiente | **Sim** (Resultados Preliminares; ponte, se houver crédito) |
| **Oráculo** (`oracle`) | Devolve a SQL de referência da pergunta | nenhum | Não (apenas autoteste da tubulação) |

> O oráculo nunca pode ser apresentado como desempenho do modelo
> ([RNC-002](../arquitetura/03_REGRAS_CRITICAS.md#rnc-002-integridade-dos-resultados-acurácia-só-vem-do-llm-real)).
> Ele serve só para confirmar que o pipeline (geração → governança → execução →
> avaliação) está correto, sem custo e sem modelo. A CI usa somente ele.

A escolha do motor local e do modelo está registrada no
[piloto de 2026-09-13](../tcc/etapas/2026-09-13_piloto-modelo-local.md): sem
verba para a API, o `qwen2.5-coder:14b` foi o menor modelo aberto que
sustentou o experimento no hardware disponível (o 7B foi descartado por
capacidade). Com o motor local nada sai do perímetro da máquina, o que
responde à pergunta da banca sobre o que é enviado a terceiros (P-18).

## 3. Contrato do prompt (motores reais)

Conforme [DA-NL2SQL-002](../arquitetura/02_DECISOES_ARQUITETURAIS.md#da-nl2sql-002-prompt-com-schema-gold-e-data-de-referência):

- **Instrução de sistema** (fixa, igual à dos Resultados Preliminares): traduzir
  para uma única SQL somente leitura sobre DuckDB, sem markdown e sem
  explicação, usando só o schema fornecido, projetando **apenas as colunas
  necessárias** e **sem arredondar** valores agregados (a tolerância numérica
  vive na avaliação, `src/evaluate.py:CASAS_DECIMAIS`). São esclarecimentos
  de especificação, não ajuste de resposta.
- **Prompt do usuário**: a descrição do schema Gold (conforme a variante), a
  data de referência (`SIM_TODAY`) para ancorar "hoje" e "agora", e a
  pergunta. No Role-Schema, uma frase avisa que só as tabelas listadas existem
  para o usuário.

### 3.1 Variantes de prompt e células pré-registradas

`nl2sql.VariantePrompt` tem três componentes; as combinações medidas na
Etapa D estão congeladas em `config.CELULAS`:

| Componente | Desligado | Ligado |
|---|---|---|
| `descricao` | **simples**: `gold.tabela(col1, col2, ...)`, uma linha por tabela (o prompt do preliminar) | **enriquecida**: dialeto DuckDB nomeado; por tabela, a nota de `config.GOLD_NOTAS` (o que é a tabela, se é snapshot sem coluna de data ou série histórica); por coluna, o tipo de `information_schema` e a unidade quando houver ("percentual, 0 a 100", "dias") |
| `value_linking` | nada | valores distintos das colunas VARCHAR com até `VALUE_LINKING_MAX_VALORES` (12) valores, por introspecção da Gold minimizada, no formato `{Enfermaria, Semi-intensiva, UTI}` |
| `schema_por_perfil` | Full-Schema: todas as tabelas Gold | Role-Schema: só as tabelas de `config.PERFIS[perfil]`, mais o aviso de que nenhuma outra existe para o usuário |

| Célula | Descrição | Value linking | Schema por perfil | Papel |
|---|---|---|---|---|
| C0 | simples | não | Full | prompt do preliminar (ponte com o Sonnet) |
| C1 | enriquecida | não | Full | base da matriz |
| C2 | enriquecida | sim | Full | caminho 1 da literatura |
| C3 | enriquecida | não | Role | caminho 2 da literatura |
| C4 | enriquecida | sim | Role | ambos |

A descrição enriquecida é um dicionário de dados (metadado, não dado), o que um
catálogo real teria; ela entra como base fixa, e não como terceiro fator,
porque o piloto mostrou que o prompt simples é inutilizável no modelo local.
As notas de `GOLD_NOTAS` foram escritas antes da medição e são fatos genéricos
do schema, mas foram motivadas pelos erros do piloto sobre as mesmas 18
perguntas; isso fica declarado como limitação no
[registro da Etapa D](../tcc/etapas/2026-09-20_etapa-D.md). O value linking e
o Role-Schema seguem os caminhos 1 e 2 de
[referencias/07](../referencias/07_MAPA_LITERATURA_PARA_CAMINHOS.md).

### 3.2 Configuração das chamadas

Tudo em `src/config.py`, seção "Configuração do LLM via API" e "Motor local";
nenhuma credencial no código ([RNC-004](../arquitetura/03_REGRAS_CRITICAS.md#rnc-004-nenhuma-credencial-no-código-ou-no-histórico-do-git)).

| Parâmetro | Motor local (Ollama) | Motor via API (Anthropic) |
|---|---|---|
| Endpoint | `OLLAMA_ENDPOINT` (padrão `http://localhost:11434`), `POST /api/chat` sem streaming | `https://api.anthropic.com/v1/messages`, `anthropic-version: 2023-06-01` |
| Modelo | `MODELO_LOCAL` (padrão `qwen2.5-coder:14b`), via ambiente | `ANTHROPIC_MODEL` (padrão `claude-sonnet-4-6`), via ambiente |
| Temperatura | `0` | `0` |
| Semente da amostragem | `SEED` (42) | não exposta pela API |
| Contexto e teto de saída | `num_ctx` 4096, `num_predict` 1024 | `max_tokens` 1024 |
| Credencial | nenhuma | `ANTHROPIC_API_KEY`, via ambiente |
| Cliente HTTP | `urllib` da biblioteca padrão ([DA-ARQ-003](../arquitetura/02_DECISOES_ARQUITETURAIS.md#da-arq-003-chamada-http-ao-llm-via-biblioteca-padrão)) | idem |
| Telemetria por chamada | `prompt_eval_count`, `eval_count`, latência, horário UTC | `usage.input_tokens`, `usage.output_tokens`, latência, horário UTC |
| Procedência registrada no relatório | versão do Ollama, digest, tamanho e quantização do modelo (`/api/version`, `/api/tags`) | nome do modelo |

Os dois motores expõem `ultima_chamada` (tokens, latência, horário) e
`descrever_ambiente()`, que o harness copia para o relatório de cada
execução; é o que permite reportar tokens de entrada por célula e dizer
exatamente quais pesos responderam.

## 4. Relação com as camadas vizinhas

- A SQL produzida pelo motor **não é executada diretamente**: passa antes pelos
  guardrails de entrada ([camadas/02](02_GOVERNANCA_ENTRADA.md)) e, após
  executar, pela validação de saída ([camadas/04](04_VALIDACAO_SAIDA.md)). Isso
  vale igualmente no Role-Schema: mostrar menos tabelas ao modelo não substitui
  o verificador determinista, que continua sendo quem garante o escopo.
- O motor só conhece o schema Gold; nunca recebe Bronze ou Silver
  ([DA-LAKE-003](../arquitetura/02_DECISOES_ARQUITETURAIS.md#da-lake-003-gold-é-a-única-camada-exposta-ao-llm)).
  A introspecção do schema e dos valores distintos usa a mesma conexão somente
  leitura à Gold isolada ([DA-LAKE-005](../arquitetura/02_DECISOES_ARQUITETURAIS.md#da-lake-005-isolamento-físico-da-gold-em-arquivo-próprio)).

## 5. Mapeamento para o código

| Item | Local | Status |
|---|---|---|
| Motores oráculo, API e local; interface comum | `src/nl2sql.py` (`MotorOraculo`, `MotorLLM`, `MotorLocal`, `obter_motor`) | IMPLEMENTADO |
| Variante de prompt e células | `src/nl2sql.py:VariantePrompt`; `src/config.py:CELULAS`, `CELULA_PADRAO` | IMPLEMENTADO |
| Introspecção e descrição do schema Gold | `src/nl2sql.py:introspectar_gold`, `descrever_schema` | IMPLEMENTADO |
| Dicionário de dados da Gold | `src/config.py:GOLD_NOTAS` | IMPLEMENTADO |
| Parâmetros dos motores | `src/config.py` (seções "Configuração do LLM via API" e "Motor local") | IMPLEMENTADO |
| Disponibilidade do servidor local | `src/nl2sql.py:ollama_disponivel` | IMPLEMENTADO |
| Execução da matriz de células | `src/matriz.py`; `run_all.py llm --motor local --matriz` | IMPLEMENTADO (execução real pendente) |
| Conjunto pergunta → SQL de referência | `src/questions.py` | IMPLEMENTADO (18 perguntas) |

## 6. Teste rápido

`python -m src.nl2sql`: o oráculo devolve a SQL de referência de cada pergunta;
as cinco células renderizam prompts distintos, C0 reproduz exatamente o formato
do preliminar, C2 traz os valores distintos, C3 omite as tabelas fora do perfil
e inclui o aviso. Os motores reais só são exercitados quando há chave (API) ou
servidor respondendo (local); sem eles são pulados, e a CI nunca os executa.
`python -m src.matriz` roda a tubulação da matriz com o oráculo em pasta
temporária. O execution match de 100% do oráculo é verificado de ponta a ponta
em `python run_all.py oracle`. Qualquer divergência indica erro no harness,
não no modelo (RNC-002).

Execução real (números do TCC), com o servidor do Ollama ativo:

```bash
python run_all.py llm --motor local --celula C2 --repeticoes 3   # uma célula
python run_all.py llm --motor local --matriz                     # cinco células, k=3
```
