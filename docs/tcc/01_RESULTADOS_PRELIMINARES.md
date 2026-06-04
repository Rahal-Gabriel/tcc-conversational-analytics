# RES: Resultados Preliminares (Registro Vivo)

**Status**: documento vivo
**Prioridade**: ALTA
**Última atualização**: 2026-06-04
**Alimenta (template TCC)**: Resultados Preliminares · Metodologia

---

## 1. Propósito

Registrar o que já é **resultado verificável** do protótipo, distinguindo-o do
que ainda é projeto. Cada resultado tem identificador estável `RES-*` e cita as
evidências (código, dados, docs). Este módulo é a fonte direta da seção
Resultados Preliminares do TCC.

> **Data de referência:** 2026-06-04. Os números vêm de execução determinista
> (`SEED=42`, `SIM_TODAY=2026-05-31`) e são reprodutíveis
> ([RNC-003](../arquitetura/03_REGRAS_CRITICAS.md#rnc-003-determinismo-e-reprodutibilidade)).

## 2. Visão geral

O protótipo está na fase de construção do pipeline de dados. A Bronze já é
gerada de forma determinista e coerente, o mapeamento regulatório está
documentado, e a infraestrutura de reprodutibilidade está operacional. As
transformações Silver/Gold, a governança executável e o motor de IA ainda não
foram implementados, e por isso **ainda não há números de acurácia**, que só
serão coletados em execução real com o motor LLM
([RNC-002](../arquitetura/03_REGRAS_CRITICAS.md#rnc-002-integridade-dos-resultados-acurácia-só-vem-do-llm-real)).

## 3. Progresso por objetivo específico (do projeto de pesquisa)

| Objetivo | Descrição | Situação | Evidência |
|---|---|---|---|
| a | Revisão da literatura (Conversational Analytics, Text-to-SQL, governança de LLMs) | Em andamento | Fora do repositório (projeto de pesquisa) |
| b | Mapear requisitos regulatórios (LGPD, ANVISA, ANPD) | Concluído | [governanca/01_CONFORMIDADE_REGULATORIA.md](../governanca/01_CONFORMIDADE_REGULATORIA.md) |
| c | Projetar a arquitetura técnica (ingestão, Lakehouse, motor com guardrails) | Parcial | [arquitetura/01_VISAO_GERAL.md](../arquitetura/01_VISAO_GERAL.md); Bronze implementada |
| d | Desenvolver o modelo de governança (acesso, rastreabilidade, anonimização, validação) | Projetado | Controles mapeados ([CTRL-*](../camadas/02_GOVERNANCA_ENTRADA.md)); lógica a implementar |
| e | Implementar e avaliar o protótipo sobre dados sintéticos | Em andamento | Bronze pronta; transformação, motor e avaliação pendentes |

## 4. Resultados preliminares disponíveis

### RES-001: Camada Bronze gerada e coerente

A geração sintética produz, de forma determinista, o ambiente de dados de um
hospital de grande porte:

| Tabela | Linhas |
|---|---|
| `bronze.unidade` | 8 |
| `bronze.leito` | 200 |
| `bronze.paciente` | 600 (com PII proposital) |
| `bronze.internacao` | 2.012 |
| `bronze.ocupacao_diaria` | 18.000 (200 leitos × 90 dias) |

Snapshot da ocupação em `SIM_TODAY` (2026-05-31):

| Situação | Leitos |
|---|---|
| Ocupado | 150 |
| Livre | 42 |
| Bloqueado | 8 |
| **Taxa de ocupação** | **75,0%** |

Coerência verificada: as 150 internações ativas (sem alta) batem exatamente com
os 150 leitos ocupados no dia de referência. Números confirmados por consulta
direta ao DuckDB em 2026-06-04.

- **Status**: VALIDADO.
- **Evidência**: `src/data_gen.py`; `data/lakehouse.duckdb`;
  [camadas/01_PIPELINE_LAKEHOUSE.md](../camadas/01_PIPELINE_LAKEHOUSE.md).

### RES-002: Mapeamento regulatório completo

A tabela `requisito regulatório → controle → camada/módulo → situação` cobre
LGPD, ANVISA (SaMD) e ANPD, demonstrando que a governança atravessa as quatro
camadas e não se restringe ao motor de IA (11 requisitos `REG-*`).

- **Status**: VALIDADO (mapeamento); controles em implementação.
- **Evidência**: [governanca/01_CONFORMIDADE_REGULATORIA.md](../governanca/01_CONFORMIDADE_REGULATORIA.md).

### RES-003: Reprodutibilidade e integridade

- Determinismo por `SEED` e `SIM_TODAY`: a mesma configuração reproduz os mesmos
  dados e números, inclusive entre Python 3.12 e 3.14.
- Versionamento por etapa (branch curto + PR squash) e ambiente fixado em
  Python 3.12, com dependências travadas (`==`) e imagem Docker reprodutível
  (base por digest), de modo que o experimento roda igual em qualquer máquina.
- CI verde a cada push e PR na `main`, usando apenas o motor oráculo, sem chave
  e sem custo.
- Separação explícita entre motor LLM (números do TCC) e oráculo (autoteste).

- **Status**: VALIDADO.
- **Evidência**: [avaliacao/02_REPRODUTIBILIDADE_CI.md](../avaliacao/02_REPRODUTIBILIDADE_CI.md);
  `.github/workflows/ci.yml`; `Dockerfile`, `.dockerignore`, `requirements.txt`.

### RES-004: Arquitetura de referência documentada

A própria documentação modular (este conjunto `docs/`) consolida a arquitetura
de referência, com decisões (`DA-*`), regras críticas (`RNC-*`), controles
(`CTRL-*`) e requisitos regulatórios (`REG-*`) rastreáveis ao código. É o
principal resultado esperado do projeto e já existe em forma navegável.

- **Status**: PARCIAL (estrutura completa; módulos evoluem com o código).
- **Evidência**: [docs/README.md](../README.md).

## 5. O que ainda falta

| Próxima entrega | Módulo de código | Resultado que habilita |
|---|---|---|
| Transformação Silver e Gold | `pipeline.py` | Anonimização verificável e métricas Gold consultáveis |
| Governança executável | `governance.py` | Guardrails, aterramento, filtro de saída e auditoria |
| Conjunto de avaliação | `questions.py` | Perguntas em PT com SQL de referência |
| Motor Text-to-SQL e oráculo | `nl2sql.py` | Tradução pergunta para SQL |
| Harness de avaliação | `evaluate.py` | Acurácia por execution match, indicadores de governança |
| Orquestrador | `run_all.py` | Execução ponta a ponta (`oracle` e `llm`) |

Somente após `evaluate.py` e uma execução com o motor LLM e chave válida é que a
hipótese de acurácia superior a 80% poderá ser testada. Até lá, nenhum número de
acurácia é reportado.

## 6. Como este registro alimenta o template do TCC

Ver o índice reverso em [02_MAPA_DOC_PARA_TEMPLATE.md](02_MAPA_DOC_PARA_TEMPLATE.md).

- **Metodologia**: determinismo, ambiente versionado e harness de avaliação
  descrevem o material e os métodos de forma reprodutível.
- **Resultados Preliminares**: RES-001 a RES-004 são os resultados parciais
  apresentáveis.
- **Integridade**: a ausência de números de acurácia nesta fase é deliberada e
  documentada.
