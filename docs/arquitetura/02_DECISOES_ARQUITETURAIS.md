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
  Silver (limpa e pseudonimizada) e Gold (métricas e registros minimizados).
- **Motivação**: Separa claramente o dado de origem do dado consumível e cria
  um ponto natural para a remoção de identificadores e a pseudonimização (na
  transição Bronze→Silver) e para a minimização (na transição Silver→Gold).
- **Status**: IMPLEMENTADO.
- **Código**: `src/data_gen.py`; `src/pipeline.py`.

### DA-LAKE-002: PII proposital na Bronze

- **Decisão**: A camada Bronze contém PII de propósito (`nome`, `cpf`,
  `data_nascimento`).
- **Motivação**: Para que a remoção de identificadores e a pseudonimização na
  Silver sejam **reais e demonstráveis**, e não apenas afirmadas. Sem PII na
  Bronze, não haveria o que pseudonimizar.
- **Status**: IMPLEMENTADO.
- **Código**: `src/data_gen.py:gerar_pacientes`.
- **Relacionado**: [REG-LGPD-002](../governanca/01_CONFORMIDADE_REGULATORIA.md),
  [RNC-005](03_REGRAS_CRITICAS.md#rnc-005-pii-nunca-sobrevive-à-silver).

### DA-LAKE-003: Gold é a única camada exposta ao LLM

- **Decisão**: O motor de linguagem só enxerga as tabelas da camada Gold.
  Bronze e Silver ficam inacessíveis ao usuário e ao LLM.
- **Motivação**: Minimização na exposição (princípio da necessidade da LGPD):
  o consumo se restringe às tabelas Gold, sem identificadores diretos nem
  pseudônimos. Duas delas são agregadas (`ocupacao_unidade`, `ocupacao_diaria`)
  e duas são de nível de linha (`leitos_status`, por leito, sem atributo de
  pessoa; `internacoes`, minimizada e com k-anonimato verificado,
  DA-LAKE-006). Até 2026-09-13 a documentação chamava a Gold de "agregada",
  o que a banca simulada apontou como impreciso (rodada 01, P-16).
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

### DA-LAKE-006: Minimização da Gold com k-anonimato verificado e pseudonimização por HMAC

- **Decisão**: (1) `gold.internacoes` fica com quatro colunas (`tipo`,
  `faixa_etaria`, `ativa`, `tempo_permanencia`); saem `id_internacao`,
  `sexo`, `data_admissao` e `id_unidade`. (2) O pipeline mede o k-anonimato
  sobre os quase-identificadores (`tipo`, `faixa_etaria`) e exige
  `k >= K_MINIMO = 5` (CTRL-LAKE-001), reportando também a sensibilidade com
  `ativa` incluído. (3) A pseudonimização de `id_paciente` passa de SHA-256
  com salt no código para HMAC-SHA256 com chave lida do ambiente
  (`PSEUDO_KEY`), com valor padrão apenas para o dado sintético. (4) A idade
  passa a ser a idade completa (`age()`), não a diferença de ano-calendário.
- **Motivação**: A banca simulada mediu k = 1 em 1.763 grupos da Gold com as
  colunas originais (rodada 01, P-16) e apontou que hash com salt no código e
  ids sequenciais são revertíveis por quem tem o repositório (P-17). A
  literatura converge: datas de eventos, sexo, idade e localização são
  quase-identificadores (El Emam e Arbuckle 2013; HIPAA Safe Harbor, 45 CFR
  164.514(b), que exige remover datas exceto o ano); hash simples e hash com
  salt são fracos contra força bruta em domínio pequeno, e o recomendado é
  hash com chave, com a chave guardada como "informação adicional" fora do
  domínio de quem processa o dado pseudonimizado (ENISA 2022; EDPB 01/2025,
  par. 19-20 e 35); LLMs em Text-to-SQL tendem a expor identificadores
  substitutos e linhas quando um agregado bastaria (Ballesteros-Rodríguez et
  al. 2026). Os limiares: k >= 5 é o usual para liberação interna controlada;
  k >= 11 (nenhuma célula de 1 a 10) é a regra de supressão do CMS, adotada
  como referência mais estrita e também satisfeita.
- **Medição que fundamentou a escolha das colunas** (2.012 internações):

  | Quase-identificadores | grupos | k mínimo | linhas em k<5 | linhas em k<11 |
  |---|---|---|---|---|
  | unidade, tipo, faixa, sexo, data de admissão (original) | 1.883 | 1 | 100% | 100% |
  | unidade, tipo, faixa, mês de admissão | 387 | 1 | 23,1% | 59,6% |
  | unidade, tipo, faixa | 120 | 1 | 3,4% | 13,6% |
  | tipo, faixa, ativa (sensibilidade) | 30 | 3 | 0,4% | 3,2% |
  | **tipo, faixa (adotado)** | 15 | **29** | 0% | 0% |

- **Alternativa descartada**: agregar `gold.internacoes` em contagens e
  médias por grupo, com supressão de células pequenas. É a forma mais estrita
  e fica registrada como evolução; foi descartada nesta etapa porque as
  perguntas de tempo médio virariam médias ponderadas (mais difíceis para o
  motor), a coerência "150 internações ativas = 150 leitos ocupados" se
  perderia com supressão, e a comparabilidade com o preliminar cairia.
- **Custo de utilidade declarado**: perguntas de internações por unidade
  deixam de ser respondíveis por esta tabela (a ocupação por unidade continua
  em `gold.ocupacao_unidade`). Nenhuma das 18 perguntas do conjunto usa as
  colunas removidas.
- **Consequência para a redação**: a Silver é **pseudonimizada** (reversível
  por quem detém a chave; continua dado pessoal nos termos da LGPD, art. 13,
  par. 4); a Gold é **minimizada, sem identificadores e com risco de
  reidentificação medido**, e não "anonimizada" nem "agregada". A faixa
  etária corrigida altera a distribuição reportada em RES-005 (errata lá).
- **Status**: IMPLEMENTADO (2026-09-13). Teste rápido em `src/pipeline.py`.
- **Código**: `src/config.py` (`PSEUDO_KEY`, `QUASE_IDENTIFICADORES_INTERNACOES`,
  `K_MINIMO`); `src/pipeline.py:_pseudo`, `_expr_faixa_etaria`,
  `construir_gold`, `medir_k_anonimato`.
- **Relacionado**: [CTRL-LAKE-001](../camadas/01_PIPELINE_LAKEHOUSE.md),
  [RES-009](../tcc/01_RESULTADOS_PRELIMINARES.md),
  [REG-LGPD-001/002](../governanca/01_CONFORMIDADE_REGULATORIA.md),
  fichas em [referencias/09](../referencias/09_PRIVACIDADE_E_MINIMIZACAO.md).

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
