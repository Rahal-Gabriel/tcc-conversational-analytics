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
o harness está correto (autoteste, não desempenho do modelo). Os **primeiros
números reais do LLM** já foram coletados: 61,1% de execution match estrito em 18
perguntas ([RES-007](#res-007-primeira-execução-real-do-motor-llm-e-refinamento-da-medição)),
com a maior parte das divergências sendo forma de resultado e governança, não erro
de cálculo
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

O fluxo completo está implementado e roda de ponta a ponta: para cada uma das 18
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

### RES-007: Primeira execução real do motor LLM e refinamento da medição

A primeira execução com o motor LLM real (`claude-sonnet-4-6`) sobre o conjunto
inicial de 10 perguntas deu **60,0% de execution match**. A análise caso a caso
mostrou que, dos quatro resultados não-`correto`, nenhum era erro de cálculo do
modelo:

| Pergunta | Evento | Natureza |
|---|---|---|
| Q01 | bloqueado | Resposta numérica correta (150 leitos), mas via `gold.ocupacao_diaria`, **fora do escopo** do perfil `enfermagem`; barrada por CTRL-GOV-005. É a governança funcionando. |
| Q04 | incorreto | Valores corretos, porém com **colunas extras** (`id_unidade`, `especialidade`). Estritez de projeção do execution match (padrão Spider/EHRSQL). |
| Q08 | incorreto | Mesma média; divergência só de **arredondamento** (referência `75,7` com `ROUND`, modelo `75,714…`). |
| Q10 | incorreto | Idem Q08 (referência `7,2`, modelo `7,184…`). |

Q08 e Q10 expuseram uma **inconsistência interna do harness**: a SQL de
referência pré-arredondava enquanto a normalização arredondava em outra precisão,
punindo o modelo por ser mais preciso. A correção (decidida **antes** de
re-executar, para não escolher critério olhando o placar — RNC-002) foi:

- a normalização passou a ser a única fonte de arredondamento, com tolerância de
  2 casas (`src/evaluate.py:CASAS_DECIMAIS`), e as SQL de referência deixaram de
  pré-arredondar;
- o contrato do prompt passou a pedir projeção mínima e a não arredondar
  agregados (esclarecimento de especificação, não ajuste de resposta);
- o conjunto foi ampliado de 10 para 18 perguntas, reduzindo o ruído da amostra
  (com 10 itens, cada questão valia 10 pontos percentuais).

Execução final (18 perguntas, `claude-sonnet-4-6`, temperatura 0, execução única).
Como a amostra é pequena, os valores são indicativos e vêm com IC95% (Wilson):

| Indicador | Valor | IC95% (Wilson) |
|---|---|---|
| Execution match estrito (**primária**) | 61,1% (11/18) | [38,6%; 79,7%] |
| Set match de conteúdo (**secundária, diagnóstica**) | 94,4% (17/18) | [74,2%; 99,0%] |
| Aprovação na governança (AVAL-002) | 88,9% (16/18) | — |
| Completude do log (AVAL-003) | 100% (18/18) | — |

A correção de arredondamento funcionou (Q08 e Q10 passaram a `correto`). Uma
execução-piloto anterior, com 10 perguntas, dera 60,0%. **Não se afirma
"estabilidade"**: com n=18 o intervalo é amplo (cerca de ±21 pontos); a ampliação
do conjunto está no plano de continuidade, para estreitá-lo.

A distância entre o estrito (61,1%) e o de conteúdo (94,4%) é o achado central: os
33 pontos de diferença vêm de **forma e governança, não de raciocínio**. Conteúdo
correto em 17 de 18.

| Categoria | Perguntas | n | Natureza |
|---|---|---|---|
| Correta (estrito) | — | 11 | Conjunto idêntico ao da referência. |
| Conteúdo certo, forma/projeção | Q04, Q13, Q14, Q15 | 4 | Valores certos, colunas extras ou shape diferente. Estritez de projeção do execution match. |
| Conteúdo certo, bloqueio de governança | Q01, Q11 | 2 | Valor correto, mas via tabela fora do escopo do perfil; barrado por CTRL-GOV-005. |
| Erro de conteúdo | Q12 | 1 | Filtragem de `tipo='enfermaria'` (caixa errada) → vazio. **Lacuna de desenho nossa** (ausência de value linking no prompt), não falha de raciocínio. |

**Trade-off de governança quantificado**: as 2 perguntas bloqueadas (Q01/Q11)
tinham conteúdo correto, logo o controle de acesso custou ≈ 11 pontos de execution
match. É um custo deliberado (menor privilégio) e mensurável, e responde com dados
à pergunta "a governança compromete a utilidade?".

Não se buscou elevar o número com novos ajustes (evitar overfitting sobre estas 18
perguntas). Q12 (value linking) e a ampliação do conjunto ficam na continuidade.

- **Status**: VALIDADO (números reais: estrito 61,1% e conteúdo 94,4% em 18
  perguntas, com IC). Nenhum número reportado sem execução real (RNC-002).
- **Evidência**: `results/avaliacao_llm.json`; `results/auditoria.log`;
  [avaliacao/01_METODOLOGIA_AVALIACAO.md](../avaliacao/01_METODOLOGIA_AVALIACAO.md).

## 5. O que ainda falta

Os primeiros números reais já foram coletados (RES-007: 61,1% de execution match
estrito em 18 perguntas). A hipótese de acurácia superior a 80% **ainda não se
confirma** sob execution match estrito; a análise de erros indica que o teto é
puxado pela forma do resultado e pela governança, não por erro de cálculo. As
próximas entregas atacam essas frentes:

| Próxima entrega | Onde | Resultado que habilita |
|---|---|---|
| Value linking (valores categóricos no prompt ou comparação sem caixa) | `nl2sql.py` / schema | Corrigir erros como Q12 (`'enfermaria'` vs `'Enfermaria'`) |
| Discussão da métrica forma-sensível | `evaluate.py` / `tcc` | Separar erro de cálculo de divergência de projeção na análise |
| Ampliação e estratificação do conjunto | `questions.py` | Reduzir ruído e medir por tipo de pergunta e por perfil |

Cada novo ajuste será medido e reportado de forma transparente (bruto × refinado),
sem iterar sobre o mesmo conjunto a ponto de overfittar (RNC-002).

## 6. Como este registro alimenta o template do TCC

Ver o índice reverso em [02_MAPA_DOC_PARA_TEMPLATE.md](02_MAPA_DOC_PARA_TEMPLATE.md).

- **Metodologia**: determinismo, ambiente versionado e harness de avaliação
  descrevem o material e os métodos de forma reprodutível.
- **Resultados Preliminares**: RES-001 a RES-007 são os resultados parciais
  apresentáveis.
- **Integridade**: os números do modelo (RES-007: 60,0% e 61,1%) vêm de execução
  real, com a metodologia decidida antes de re-rodar e os valores bruto e refinado
  reportados lado a lado; o 100% do oráculo (RES-006) é autoteste da tubulação, não
  desempenho do LLM.
