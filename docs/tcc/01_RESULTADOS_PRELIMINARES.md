# RES: Resultados Preliminares (Registro Vivo)

**Status**: documento vivo
**Prioridade**: ALTA
**Última atualização**: 2026-06-15
**Alimenta (template TCC)**: Resultados Preliminares · Metodologia

---

## 1. Propósito

Registrar o que já é **resultado verificável** do protótipo, distinguindo-o do
que ainda é projeto. Cada resultado tem identificador estável `RES-*` e cita as
evidências (código, dados, docs). Este módulo é a fonte direta da seção
Resultados Preliminares do TCC.

> **Data de referência:** 2026-06-15. Os números vêm de execução determinista
> (`SEED=42`, `SIM_TODAY=2026-05-31`) e são reprodutíveis
> ([RNC-003](../arquitetura/03_REGRAS_CRITICAS.md#rnc-003-determinismo-e-reprodutibilidade)).

## 2. Visão geral

O protótipo concluiu o pipeline de dados nas três camadas (Bronze determinista,
Silver anonimizada, Gold agregada), a governança de entrada e de saída, o motor
Text-to-SQL nas duas implementações (oráculo e LLM) e o harness de avaliação. A
tubulação completa (geração → governança → execução → avaliação) roda de ponta a
ponta com o motor oráculo e fecha em 100% de execution match, o que comprova que
o harness está correto. Esse 100% é **autoteste da tubulação**, não desempenho do
modelo: **ainda não há números de acurácia do LLM**, que só serão coletados em
execução real com o motor LLM e chave válida
([RNC-002](../arquitetura/03_REGRAS_CRITICAS.md#rnc-002-integridade-dos-resultados-acurácia-só-vem-do-llm-real)).

## 3. Progresso por objetivo específico (do projeto de pesquisa)

| Objetivo | Descrição | Situação | Evidência |
|---|---|---|---|
| a | Revisão da literatura (Conversational Analytics, Text-to-SQL, governança de LLMs) | Em andamento | Fora do repositório (projeto de pesquisa) |
| b | Mapear requisitos regulatórios (LGPD, ANVISA, ANPD) | Concluído | [governanca/01_CONFORMIDADE_REGULATORIA.md](../governanca/01_CONFORMIDADE_REGULATORIA.md) |
| c | Projetar a arquitetura técnica (ingestão, Lakehouse, motor com guardrails) | Parcial | [arquitetura/01_VISAO_GERAL.md](../arquitetura/01_VISAO_GERAL.md); Lakehouse e motor Text-to-SQL implementados |
| d | Desenvolver o modelo de governança (acesso, rastreabilidade, anonimização, validação) | Concluído (implementação) | Anonimização Silver ([RES-005](#res-005-camadas-silver-e-gold-anonimizadas-e-agregadas)); guardrails de entrada e saída, e auditoria de pergunta e resposta implementados |
| e | Implementar e avaliar o protótipo sobre dados sintéticos | Em andamento | Tubulação de avaliação verde no oráculo ([RES-006](#res-006-tubulação-de-avaliação-verde-com-o-motor-oráculo)); acurácia do LLM pendente de execução real |

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

### RES-005: Camadas Silver e Gold anonimizadas e agregadas

A transformação `src/pipeline.py` materializa, de forma determinista sobre a
Bronze, a Silver anonimizada e as quatro tabelas Gold expostas ao motor de
linguagem.

Anonimização (Silver), verificada no teste rápido
([RNC-005](../arquitetura/03_REGRAS_CRITICAS.md#rnc-005-pii-nunca-sobrevive-à-silver)):
`silver.paciente` não contém `nome`, `cpf` nem `data_nascimento`; `id_paciente`
vira `id_paciente_pseudo` (SHA-256 com salt, sem colisão nos 600 pacientes); a
data de nascimento dá lugar a `faixa_etaria`. Distribuição das faixas:

| Faixa etária | Pacientes |
|---|---|
| 0-17 | 105 |
| 18-39 | 142 |
| 40-59 | 127 |
| 60-79 | 128 |
| 80+ | 98 |

Snapshot Gold da ocupação por unidade em `SIM_TODAY` (2026-05-31):

| Unidade | Total | Ocupados | Livres | Bloqueados | Taxa |
|---|---|---|---|---|---|
| Cardiologia | 25 | 18 | 6 | 1 | 72,0% |
| Pediatria | 25 | 17 | 6 | 2 | 68,0% |
| Clínica Médica | 25 | 21 | 4 | 0 | 84,0% |
| Cirurgia Geral | 25 | 23 | 2 | 0 | 92,0% |
| Ortopedia | 25 | 16 | 5 | 4 | 64,0% |
| Neurologia | 25 | 20 | 5 | 0 | 80,0% |
| Oncologia | 25 | 17 | 7 | 1 | 68,0% |
| Pronto-Socorro | 25 | 18 | 7 | 0 | 72,0% |
| **Hospital** | **200** | **150** | **42** | **8** | **75,0%** |

Coerência verificada: a soma dos 200 leitos por unidade fecha com `VOL_LEITOS`, e
os 150 leitos ocupados batem com as 150 internações marcadas como `ativa` em
`gold.internacoes`. Números confirmados por consulta direta ao DuckDB em
2026-06-04.

- **Status**: VALIDADO.
- **Evidência**: `src/pipeline.py`; `data/lakehouse.duckdb`;
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

### RES-006: Tubulação de avaliação verde com o motor oráculo

O fluxo completo está implementado e roda de ponta a ponta: para cada uma das 10
perguntas do conjunto de avaliação, a SQL passa pelos guardrails de entrada, é
executada em conexão somente leitura, passa pela validação de saída e tem o
resultado comparado por execution match com a SQL de referência; toda interação
é registrada na trilha de auditoria.

Resultado de `python run_all.py oracle` (motor oráculo):

| Indicador | Valor |
|---|---|
| AVAL-001 acurácia (execution match) | 100,0% |
| AVAL-002 aprovação na governança | 100,0% |
| AVAL-003 completude do log | 100,0% |

Os 100% confirmam que a tubulação (geração → governança → execução → avaliação)
está correta. Por se tratar do **motor oráculo**, este número é autoteste da
tubulação e **nunca** representa o desempenho do modelo
([RNC-002](../arquitetura/03_REGRAS_CRITICAS.md#rnc-002-integridade-dos-resultados-acurácia-só-vem-do-llm-real)).
A CI executa este mesmo autoteste a cada push e PR, sem chave e sem custo.

- **Status**: VALIDADO (tubulação; acurácia do LLM pendente de execução real).
- **Evidência**: `src/questions.py`, `src/nl2sql.py`, `src/evaluate.py`,
  `run_all.py`, `src/governance.py`; `results/avaliacao_oracle.json`;
  [avaliacao/01_METODOLOGIA_AVALIACAO.md](../avaliacao/01_METODOLOGIA_AVALIACAO.md).

## 5. O que ainda falta

| Próxima entrega | Módulo de código | Resultado que habilita |
|---|---|---|
| Execução real com o motor LLM | `run_all.py llm` (chave válida) | Números de acurácia do modelo (teste da hipótese > 80%) |

Toda a tubulação já está pronta e verificada com o oráculo. Falta apenas rodar
`python run_all.py llm` com `ANTHROPIC_API_KEY` válida para coletar os números de
acurácia do modelo; só então a hipótese de acurácia superior a 80% poderá ser
testada. Até lá, nenhum número de acurácia do LLM é reportado (RNC-002).

## 6. Como este registro alimenta o template do TCC

Ver o índice reverso em [02_MAPA_DOC_PARA_TEMPLATE.md](02_MAPA_DOC_PARA_TEMPLATE.md).

- **Metodologia**: determinismo, ambiente versionado e harness de avaliação
  descrevem o material e os métodos de forma reprodutível.
- **Resultados Preliminares**: RES-001 a RES-006 são os resultados parciais
  apresentáveis.
- **Integridade**: a ausência de números de acurácia do modelo nesta fase é
  deliberada e documentada; o 100% do oráculo (RES-006) é autoteste da tubulação,
  não desempenho do LLM.
