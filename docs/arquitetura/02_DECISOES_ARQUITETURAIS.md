# DA: Decisões Arquiteturais

**Status**: PARCIAL
**Prioridade**: ALTA
**Última atualização**: 2026-09-20
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

- **Decisão**: Chamar o modelo, seja a API da Anthropic, seja o servidor local
  do Ollama, com `urllib` da biblioteca padrão, sem SDK.
- **Motivação**: Manter o conjunto de dependências mínimo (apenas `faker` e
  `duckdb`), o que reduz superfície e facilita a reprodução.
- **Status**: IMPLEMENTADO (`src/nl2sql.py:_post_json`, usado por `MotorLLM` e
  `MotorLocal`).
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

### DA-NL2SQL-001: Motores intercambiáveis (oráculo, API e local)

- **Decisão**: O sistema tem motores intercambiáveis atrás de uma interface
  única (`gerar_sql(pergunta, perfil)`): os motores **reais** (via API e local,
  que geram os números do TCC) e o **oráculo** (que devolve a SQL de
  referência, só para autoteste da tubulação). O harness não distingue entre
  eles além do nome registrado no relatório.
- **Motivação**: Permite validar todo o harness sem custo e sem modelo, impede
  confundir autoteste com desempenho, e permitiu trocar o motor dos Resultados
  Preliminares (API) pelo motor local da fase de conclusão sem tocar no
  avaliador.
- **Status**: IMPLEMENTADO (`src/nl2sql.py:obter_motor`, `MOTORES`).
- **Relacionado**: [RNC-002](03_REGRAS_CRITICAS.md#rnc-002-integridade-dos-resultados),
  [DA-NL2SQL-003](#da-nl2sql-003-motor-local-com-modelo-aberto-servido-pelo-ollama),
  [avaliacao/01_METODOLOGIA_AVALIACAO.md](../avaliacao/01_METODOLOGIA_AVALIACAO.md).

### DA-NL2SQL-002: Prompt com schema Gold e data de referência

- **Decisão**: O prompt do motor recebe o schema Gold e a data atual
  (`SIM_TODAY`), e exige uma única SQL somente leitura, sem markdown e sem
  explicação.
- **Motivação**: Reduzir ambiguidade, ancorar consultas que mencionam "hoje" na
  data de referência e facilitar a validação automática da saída.
- **Status**: IMPLEMENTADO. A instrução de sistema é fixa desde os Resultados
  Preliminares; a forma como o schema é descrito virou variável experimental
  ([DA-NL2SQL-004](#da-nl2sql-004-prompt-como-variável-experimental-pré-registrada)).
- **Código**: `src/config.py` (`SIM_TODAY`); `src/nl2sql.py` (`_PROMPT_SISTEMA`,
  `montar_prompt_usuario`).

### DA-NL2SQL-003: Motor local com modelo aberto servido pelo Ollama

- **Decisão**: O motor real da fase de conclusão é um modelo aberto
  (`qwen2.5-coder:14b`, quantização padrão do Ollama) servido na própria
  máquina, chamado por `POST /api/chat` com temperatura zero e a `SEED` do
  projeto na amostragem. O relatório de cada execução registra versão do
  servidor, digest, tamanho e quantização do modelo, além de tokens e
  latência por chamada.
- **Motivação**: O autor não dispõe de verba para a API; o piloto de
  2026-09-13 mostrou que o 14B sustenta o experimento (o 7B não) e que nada
  precisa sair do perímetro (P-18 da banca). Modelos da família Qwen2.5-Coder
  aparecem na literatura fichada em português (Pedroso et al. 2025; Silva et
  al. 2025) e em SQL médico (Tanković et al. 2025). O digest fixa exatamente
  quais pesos responderam, o que a API não oferece.
- **Alternativas descartadas**: `qwen2.5-coder:7b` (22% a 39% no piloto,
  inventa colunas mesmo com nota explícita); continuar com a API (sem
  crédito); modelos maiores (não cabem em 16 GB).
- **Consequência declarada**: a comparação com os Resultados Preliminares
  passa a ter três diferenças (modelo, Gold minimizada, harness revisto). A
  célula C0 preserva o mesmo prompt para isolar a troca de modelo; se houver
  crédito, a ponte fecha com o Sonnet nas células C0 e vencedora.
- **Status**: IMPLEMENTADO (`src/nl2sql.py:MotorLocal`, `ollama_disponivel`;
  `src/config.py` seção "Motor local"). Números na execução da Etapa D.
- **Relacionado**: [piloto](../tcc/etapas/2026-09-13_piloto-modelo-local.md),
  [RNC-003](03_REGRAS_CRITICAS.md#rnc-003-determinismo-por-seed-e-sim_today)
  (a estabilidade do modelo é observada por TARa@k, não assumida),
  [camadas/03](../camadas/03_MOTOR_TEXT2SQL.md).

### DA-NL2SQL-004: Prompt como variável experimental pré-registrada

- **Decisão**: A descrição do schema no prompt é controlada por
  `VariantePrompt` com três componentes: descrição (simples ou enriquecida
  com tipos, notas de tabela e unidades de `config.GOLD_NOTAS`), value
  linking (valores distintos das colunas categóricas com até 12 valores) e
  schema por perfil (Role-Schema). As combinações medidas são cinco células
  fixadas em `config.CELULAS` antes da execução: C0 (prompt do preliminar),
  C1 (base enriquecida), C2 (+value linking), C3 (+Role-Schema), C4 (ambos).
  A instrução de sistema não varia.
- **Motivação**: Tratar o prompt como variável, e não como detalhe, é o que a
  literatura recomenda (Gao et al. 2024). Cada fator cruzado responde a uma
  pergunta existente: value linking fecha Q12 e a lacuna do caminho 1 (Liu et
  al. 2026; Tanković et al. 2025); Role-Schema responde à P-10 da banca e à
  lacuna do caminho 2 (Fei et al. 2026) sob verificador determinista. A
  descrição enriquecida é base fixa porque o piloto mostrou o prompt simples
  inutilizável no modelo local e porque a literatura já recomenda schema
  completo e bem descrito (Maamari et al. 2024); cruzá-la só confirmaria isso.
- **Alternativa descartada**: matriz 2×2×2 (oito células) com a descrição
  como terceiro fator: mais tempo de execução e de redação para um fator sem
  pergunta própria; a célula C0 já dá a comparação com o prompt antigo.
- **Limitação declarada**: as notas de `GOLD_NOTAS` são fatos genéricos do
  schema, mas foram motivadas pelos erros do piloto sobre as mesmas 18
  perguntas; a correção de literal pós-geração
  ([referencias/10](../referencias/10_CATALOGO_ALGORITMOS.md) §3) ficou fora
  desta matriz.
- **Status**: IMPLEMENTADO (`src/nl2sql.py:VariantePrompt`, `descrever_schema`;
  `src/config.py:CELULAS`, `GOLD_NOTAS`, `VALUE_LINKING_MAX_VALORES`;
  `src/matriz.py`). Hipóteses e critério de decisão no
  [registro da Etapa D](../tcc/etapas/2026-09-20_etapa-D.md).
- **Relacionado**: [referencias/07](../referencias/07_MAPA_LITERATURA_PARA_CAMINHOS.md)
  caminhos 1 e 2, [DA-AVAL-004](#da-aval-004-desfechos-de-governança-em-dois-níveis).

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

### DA-VALID-003: Trilha de auditoria com horário real e encadeamento por hash

- **Decisão**: Cada registro da trilha guarda o horário real (UTC, relógio do
  sistema) **e** a data de simulação (`SIM_TODAY`), um `id_interacao` que liga
  entrada e saída, o motor, o controle e o motivo de bloqueio, e o hash SHA-256
  e o número de linhas do resultado entregue (nunca o resultado em si). Os
  registros são encadeados: cada um carrega o hash do anterior e o próprio
  hash sobre o conteúdo canônico; `verificar_trilha` detecta alteração,
  remoção ou inserção posterior. Autenticação de usuário e perfil fica fora do
  escopo do protótipo, com o ponto de integração declarado (a assinatura de
  `registrar_pergunta`).
- **Motivação**: O log anterior tinha `momento = SIM_TODAY` sempre, não
  registrava o que foi entregue e não tinha proteção de integridade; um
  encarregado de dados não o aceitaria como rastreabilidade (P-20). O
  encadeamento por hash é a técnica clássica de log resistente a adulteração
  (Schneier e Kelsey 1999; Crosby e Wallach 2009) e a integridade do log é
  requisito de gestão de logs de segurança (NIST SP 800-92).
- **Alternativa descartada**: assinar cada registro com chave (exige gestão de
  chave que o protótipo não tem; o encadeamento detecta adulteração mas não
  autentica o autor, limitação declarada). Registrar o resultado completo
  (copiaria dados para o log; o hash prova a resposta sem copiá-la).
- **Efeito sobre RNC-003**: dados e métricas continuam deterministas; o horário
  real fica explicitamente fora dessa exigência.
- **Status**: IMPLEMENTADO (`src/governance.py:registrar_pergunta`,
  `registrar_resposta`, `verificar_trilha`, `hash_resultado`;
  `config.AUDIT_HASH_GENESIS`).
- **Relacionado**: [CTRL-AUD-001](../camadas/04_VALIDACAO_SAIDA.md),
  [AVAL-003](../avaliacao/01_METODOLOGIA_AVALIACAO.md),
  [REG-LGPD-007](../governanca/01_CONFORMIDADE_REGULATORIA.md).

## Avaliação (AVAL)

### DA-AVAL-001: Execution match no estilo EHRSQL

- **Decisão**: A acurácia é medida por execution match: executar a SQL gerada e
  a SQL de referência e comparar os conjuntos de resultados.
- **Motivação**: Avaliar o efeito (o resultado correto), não a forma exata da
  SQL, que pode variar e ainda estar correta.
- **Status**: IMPLEMENTADO (`src/evaluate.py:avaliar`).
- **Relacionado**: [AVAL-001](../avaliacao/01_METODOLOGIA_AVALIACAO.md).

### DA-AVAL-002: Normalização dos resultados antes de comparar

- **Decisão**: Antes de comparar, normalizar os resultados (floats arredondados,
  datas em ISO, linhas ordenadas).
- **Motivação**: Evitar falsos negativos por diferenças irrelevantes de
  formatação ou ordem.
- **Status**: IMPLEMENTADO (`src/evaluate.py:normalizar`, `CASAS_DECIMAIS`).
- **Relacionado**: [AVAL-001](../avaliacao/01_METODOLOGIA_AVALIACAO.md).

### DA-AVAL-003: Tipo de pergunta derivado da SQL de referência

- **Decisão**: O tipo de cada pergunta do conjunto é definido por uma regra
  mecânica sobre a SQL de referência (tabela Gold consultada; para
  `gold.ocupacao_diaria`, janela de um dia é status atual, mais de um dia é
  série histórica), e o autoteste confere o rótulo declarado contra a regra.
  Os tipos são `status_atual`, `metrica_unidade`, `serie_historica` e
  `internacoes`.
- **Motivação**: A banca simulada (rodada 01, P-02) mostrou que os rótulos
  originais não tinham critério e que três perguntas estavam mal rotuladas
  (Q07 como série histórica; Q10 e Q18 como "faixa etária" sem envolver faixa
  etária). Sem critério verificável, a estratificação por tipo não é um
  achado.
- **Alternativa descartada**: rotular pelo texto da pergunta (subjetivo, não
  verificável por teste).
- **Limitação declarada**: tipo e perfil continuam quase confundidos no
  conjunto de 18; os perfis foram mantidos pela comparabilidade com o
  preliminar.
- **Status**: IMPLEMENTADO (`src/questions.py:tipo_por_sql`, autoteste).
- **Relacionado**: [AVAL, §3](../avaliacao/01_METODOLOGIA_AVALIACAO.md).

### DA-AVAL-004: Desfechos de governança em dois níveis

- **Decisão**: Cada interação é classificada nos seis desfechos de Fei et al.
  (2026) (Correct, Wrong, Proper Refusal, Violation Correct, Violation Wrong,
  Over-Refusal), em dois níveis: **modelo** (o que a SQL gerada faria sem
  verificador) e **sistema** (o que o usuário recebeu depois do verificador
  determinista). Os indicadores Safe-EX, Violation Rate, Over-Refusal Rate e
  Proper Refusal Rate são reportados por nível. Substitui a "taxa de
  aprovação na governança".
- **Motivação**: A taxa de aprovação contava qualquer bloqueio e não dizia se
  o bloqueio era desejado ou custo (P-04). A taxonomia publicada dá nome a
  cada caso e torna o resultado comparável com a literatura. Os dois níveis
  isolam a contribuição do verificador determinista, que os benchmarks não
  medem (eles avaliam o modelo sozinho ou com verificador por LLM).
- **Regras de classificação**: bloqueio por controle de política de acesso
  (`evaluate.CONTROLES_POLITICA`: escrita ou I/O, camada interna, escopo do
  perfil ou tabela inexistente, campo sensível) é violação no nível do modelo,
  correta ou errada conforme execução diagnóstica; bloqueio por SQL malformada
  (instrução única, forma de leitura, aterramento) e erro de execução são
  Wrong; resposta vazia ou iniciada por `config.MARCADOR_RECUSA` é recusa.
  "Correct" exige execution match estrito, o mesmo critério da primária.
- **Status**: IMPLEMENTADO (`src/evaluate.py:classificar_desfechos`); autoteste
  com motor de falhas sintético cobre os seis desfechos nos dois níveis.
- **Relacionado**: [AVAL-002](../avaliacao/01_METODOLOGIA_AVALIACAO.md),
  ficha de Fei et al. (2026) em [referencias/03](../referencias/03_GOVERNANCA_E_SEGURANCA.md).

### DA-AVAL-005: Soft F1 do BIRD como segunda métrica secundária

- **Decisão**: Reportar, ao lado do set match de conteúdo, o Soft F1 do BIRD
  Mini-Dev (Li et al. 2023), seguindo a implementação de referência
  (`bird-bench/mini_dev`, `evaluation/evaluation_f1.py`): linhas deduplicadas
  e alinhadas por índice, células comparadas por pertinência dentro da linha,
  TP, FP e FN como frações do número de colunas da referência, micro-agregados
  em precisão, recall e F1. Desvio declarado: as linhas chegam ordenadas pela
  regra do execution match, o que remove a sensibilidade à ordem da
  implementação original.
- **Motivação**: O set match de conteúdo é métrica própria, de recall, sem par
  na literatura e permissiva por construção (P-14). O Soft F1 é a métrica
  publicada mais próxima, penaliza excesso (colunas extras) e torna a tabela
  de resultados comparável com o BIRD.
- **Alternativa descartada**: substituir o set match pelo Soft F1 (perderia a
  comparabilidade com o documento preliminar; os dois são reportados).
- **Status**: IMPLEMENTADO (`src/evaluate.py:soft_f1`).
- **Relacionado**: [AVAL, secundárias](../avaliacao/01_METODOLOGIA_AVALIACAO.md),
  ficha do BIRD em [referencias/02](../referencias/02_METRICAS_E_AVALIACAO.md).
