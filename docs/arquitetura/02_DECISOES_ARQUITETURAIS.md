# DA: Decisões Arquiteturais

**Status**: PARCIAL
**Prioridade**: ALTA
**Última atualização**: 2026-09-13
**Alimenta (template TCC)**: Metodologia · Resultados Preliminares

---

## Propósito

Registrar as decisões arquiteturais do protótipo e, principalmente, a
justificativa de cada uma (o "porquê"). Cada decisão tem um identificador
estável `DA-[MOD]-[NUM]` citável pelos demais módulos e pela redação do TCC.

> Formato de cada decisão: **Decisão**, **Motivação**, **Alternativa
> descartada** (quando relevante), **Status**, **Código/origem**.

---

## Arquitetura geral (ARQ)

### DA-ARQ-001: Arquitetura em quatro camadas com governança transversal

- **Decisão**: Organizar o sistema em quatro camadas (pipeline Lakehouse,
  governança de entrada, motor Text-to-SQL, validação de saída), tratando a
  governança como preocupação transversal e não como um apêndice do motor.
- **Motivação**: A lacuna identificada no projeto de pesquisa é justamente a de
  iniciativas que focam só no modelo de linguagem e ignoram a governança
  integrada. Separar em camadas torna cada controle localizável e auditável.
- **Status**: PARCIAL (camadas definidas; Bronze implementada).
- **Origem**: `GUIA_DESENVOLVIMENTO.md`; [arquitetura/01_VISAO_GERAL.md](01_VISAO_GERAL.md).

### DA-ARQ-002: DuckDB como Lakehouse local

- **Decisão**: Usar DuckDB com schemas `bronze`, `silver` e `gold` como
  Lakehouse local, em vez de um ambiente Delta/Databricks real.
- **Motivação**: Permite reprodutibilidade total em qualquer máquina, sem custo
  e sem credenciais de nuvem, mantendo a mesma lógica de camadas. A arquitetura
  é descrita de forma que mapeie para Delta/Databricks em produção.
- **Alternativa descartada**: Databricks real (custo, dependência de nuvem,
  reprodução difícil por terceiros).
- **Status**: IMPLEMENTADO (Bronze em DuckDB).
- **Código**: `src/config.py:38` (`DB_PATH`); `src/data_gen.py` (criação do
  schema `bronze`).

### DA-ARQ-003: Chamada HTTP ao LLM via biblioteca padrão

- **Decisão**: Chamar a API da Anthropic com `urllib` da biblioteca padrão, sem
  SDK pesado.
- **Motivação**: Manter o conjunto de dependências mínimo (apenas `faker` e
  `duckdb`), o que reduz superfície e facilita a reprodução.
- **Status**: PROJETADO.
- **Origem**: `requirements.txt`; `GUIA_DESENVOLVIMENTO.md` (seção Configuração do LLM).

---

## Pipeline Lakehouse (LAKE)

### DA-LAKE-001: Modelo de camadas Bronze / Silver / Gold

- **Decisão**: Adotar o padrão Lakehouse de três camadas: Bronze (bruto),
  Silver (limpa e anonimizada) e Gold (métricas e agregações).
- **Motivação**: Separa claramente o dado de origem do dado consumível e cria
  um ponto natural para a anonimização (na transição Bronze→Silver).
- **Status**: PARCIAL (Bronze implementada; Silver e Gold projetadas).
- **Código**: `src/data_gen.py`; `src/pipeline.py` (a implementar).

### DA-LAKE-002: PII proposital na Bronze

- **Decisão**: A camada Bronze contém PII de propósito (`nome`, `cpf`,
  `data_nascimento`).
- **Motivação**: Para que a anonimização na Silver seja **real e demonstrável**,
  e não apenas afirmada. Sem PII na Bronze, não haveria o que anonimizar.
- **Status**: IMPLEMENTADO.
- **Código**: `src/data_gen.py:gerar_pacientes`.
- **Relacionado**: [REG-LGPD-002](../governanca/01_CONFORMIDADE_REGULATORIA.md),
  [RNC-005](03_REGRAS_CRITICAS.md#rnc-005-pii-nunca-sobrevive-à-silver).

### DA-LAKE-003: Gold é a única camada exposta ao LLM

- **Decisão**: O motor de linguagem só enxerga as tabelas da camada Gold.
  Bronze e Silver ficam inacessíveis ao usuário e ao LLM.
- **Motivação**: Minimização na exposição (princípio da necessidade da LGPD):
  o consumo se restringe a métricas agregadas, sem dado individual.
- **Status**: IMPLEMENTADO (enforcement textual em CTRL-GOV-004 e físico em
  DA-LAKE-005 / CTRL-GOV-007).
- **Código**: `src/config.py` (`GOLD_TABLES`, `GOLD_DB_PATH`);
  `src/governance.py:conectar_somente_leitura`.
- **Relacionado**: [CTRL-GOV-004](../camadas/02_GOVERNANCA_ENTRADA.md),
  [CTRL-GOV-007](../camadas/02_GOVERNANCA_ENTRADA.md),
  [REG-LGPD-003](../governanca/01_CONFORMIDADE_REGULATORIA.md).

### DA-LAKE-004: Faixa etária derivada substitui a data de nascimento

- **Decisão**: Na Silver, derivar `faixa_etaria` (0-17, 18-39, 40-59, 60-79,
  80+) a partir de `data_nascimento` e descartar a data original.
- **Motivação**: Preservar utilidade analítica (estratificação por idade) sem
  manter um dado que aproxima a reidentificação.
- **Status**: IMPLEMENTADO.
- **Código**: `src/config.py` (`FAIXAS_ETARIAS`); `src/pipeline.py:_expr_faixa_etaria`.

### DA-LAKE-005: Isolamento físico da Gold em arquivo próprio

- **Decisão**: Além de existir no lakehouse (`data/lakehouse.duckdb`, com
  Bronze, Silver e Gold), a Gold é exportada para um arquivo DuckDB separado
  (`data/gold_isolada.duckdb`) que contém apenas as quatro tabelas Gold. O
  motor Text-to-SQL e o harness de avaliação conectam-se **somente** a esse
  arquivo, em modo somente leitura. Bronze e Silver não existem nele.
- **Motivação**: A banca simulada (rodada 01, P-09) mostrou que a garantia
  "Bronze e Silver inacessíveis ao modelo" era sustentada apenas por análise
  textual da SQL, e que essa análise era contornável: uma função de tabela que
  recebe o nome como texto (`query_table('bronze.paciente')`), consultas ao
  catálogo (`information_schema`, `duckdb_tables()`) e um alias de coluna
  (`cpf AS c`) passavam por todos os guardrails e devolviam nome e CPF. A
  literatura fichada em `docs/referencias/03` (Miyamoto et al. 2026; Klisura et
  al. 2025) já indicava que imposição determinista fora do texto é necessária.
  Isolar o dado torna o isolamento independente da SQL: seja qual for o texto,
  não há o que ler além da Gold.
- **Alternativa descartada**: manter um único arquivo e reforçar só a lista de
  palavras proibidas. Descartada porque cada nova função ou view do DuckDB
  reabriria a brecha; a lista foi reforçada mesmo assim, como camada adicional
  (CTRL-GOV-002), não como garantia.
- **Consequência para a redação**: o texto do TCC deixa de afirmar que a
  análise textual isola as camadas e passa a descrever duas barreiras
  independentes (texto e dado), com o achado da rodada 01 relatado na
  Discussão como resultado (RES-008).
- **Status**: IMPLEMENTADO (2026-09-13). Teste rápido em `src/pipeline.py`.
- **Código**: `src/config.py` (`GOLD_DB_PATH`); `src/pipeline.py:exportar_gold`;
  `src/governance.py:conectar_somente_leitura`; `run_all.py:garantir_dados`.
- **Relacionado**: [CTRL-GOV-007](../camadas/02_GOVERNANCA_ENTRADA.md),
  [RNC-005](03_REGRAS_CRITICAS.md#rnc-005-pii-nunca-sobrevive-à-silver),
  [RES-008](../tcc/01_RESULTADOS_PRELIMINARES.md),
  [banca, rodada 01, P-09](../tcc/banca/2026-09-13_rodada-01.md).

---

## Governança de entrada (GOV)

### DA-GOV-001: Acesso por perfil mapeado a tabelas Gold

- **Decisão**: Cada perfil de usuário (`gestor`, `enfermagem`,
  `administrativo`) autoriza apenas um subconjunto das tabelas Gold.
- **Motivação**: Controle de acesso por finalidade e perfil, exigência tanto da
  LGPD (princípio da finalidade) quanto das normas da ANVISA.
- **Status**: PROJETADO (mapa pronto em config; enforcement a implementar).
- **Código**: `src/config.py:54-66` (`PERFIS`).

### DA-GOV-002: Conexão DuckDB somente leitura (defesa em profundidade)

- **Decisão**: A execução da SQL gerada usa conexão DuckDB em modo somente
  leitura, além dos guardrails textuais.
- **Motivação**: Defesa em profundidade. Mesmo que um guardrail textual falhe,
  o banco recusa qualquer escrita.
- **Status**: PROJETADO.
- **Relacionado**: [CTRL-GOV-006](../camadas/02_GOVERNANCA_ENTRADA.md).

---

## Motor Text-to-SQL (NL2SQL)

### DA-NL2SQL-001: Dois motores intercambiáveis (LLM e oráculo)

- **Decisão**: O sistema tem dois motores: o **LLM** (real, que gera os números
  do TCC) e o **oráculo** (que devolve a SQL de referência, só para autoteste
  da tubulação).
- **Motivação**: Permite validar todo o harness sem custo e sem chave, e impede
  confundir autoteste com desempenho do modelo.
- **Status**: PROJETADO.
- **Relacionado**: [RNC-002](03_REGRAS_CRITICAS.md#rnc-002-integridade-dos-resultados),
  [avaliacao/01_METODOLOGIA_AVALIACAO.md](../avaliacao/01_METODOLOGIA_AVALIACAO.md).

### DA-NL2SQL-002: Prompt com schema Gold e data de referência

- **Decisão**: O prompt do motor recebe o schema Gold e a data atual
  (`SIM_TODAY`), e exige uma única SQL somente leitura, sem markdown e sem
  explicação.
- **Motivação**: Reduzir ambiguidade, ancorar consultas que mencionam "hoje" na
  data de referência e facilitar a validação automática da saída.
- **Status**: PROJETADO.
- **Código**: `src/config.py:14-16` (`SIM_TODAY`); `src/nl2sql.py` (a implementar).

---

## Validação de saída (VALID)

### DA-VALID-001: Aterramento contra o schema Gold conhecido

- **Decisão**: Toda tabela referenciada na SQL deve existir no schema Gold
  conhecido; caso contrário, a consulta é bloqueada.
- **Motivação**: Mitigar alucinação do LLM (tabela ou coluna inventada),
  conforme alerta da ANPD.
- **Status**: PROJETADO.
- **Relacionado**: [REG-ANPD-001](../governanca/01_CONFORMIDADE_REGULATORIA.md),
  [CTRL-VALID-001](../camadas/04_VALIDACAO_SAIDA.md).

### DA-VALID-002: Filtro de saída por nome de campo sensível

- **Decisão**: Se qualquer coluna do resultado tiver nome de campo sensível
  (`nome`, `cpf`, `data_nascimento`, `id_paciente_pseudo`), a resposta é
  bloqueada.
- **Motivação**: Última barreira contra vazamento de dado sensível na resposta.
- **Status**: PROJETADO.
- **Código**: `src/config.py:51` (`CAMPOS_SENSIVEIS`).
- **Relacionado**: [CTRL-VALID-002](../camadas/04_VALIDACAO_SAIDA.md),
  [REG-LGPD-006](../governanca/01_CONFORMIDADE_REGULATORIA.md).

---

## Avaliação (AVAL)

### DA-AVAL-001: Execution match no estilo EHRSQL

- **Decisão**: A acurácia é medida por execution match: executar a SQL gerada e
  a SQL de referência e comparar os conjuntos de resultados.
- **Motivação**: Avaliar o efeito (o resultado correto), não a forma exata da
  SQL, que pode variar e ainda estar correta.
- **Status**: PROJETADO.
- **Relacionado**: [AVAL-001](../avaliacao/01_METODOLOGIA_AVALIACAO.md).

### DA-AVAL-002: Normalização dos resultados antes de comparar

- **Decisão**: Antes de comparar, normalizar os resultados (floats arredondados,
  datas em ISO, linhas ordenadas).
- **Motivação**: Evitar falsos negativos por diferenças irrelevantes de
  formatação ou ordem.
- **Status**: PROJETADO.
- **Relacionado**: [AVAL-001](../avaliacao/01_METODOLOGIA_AVALIACAO.md).
