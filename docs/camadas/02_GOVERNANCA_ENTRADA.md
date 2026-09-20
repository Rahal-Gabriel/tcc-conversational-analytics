# GOV: Camada 2 - Governança de Entrada

**Status**: IMPLEMENTADO
**Prioridade**: CRÍTICA
**Última atualização**: 2026-09-20
**Alimenta (template TCC)**: Metodologia · Resultados Preliminares

---

## 1. Propósito

Descrever os controles aplicados **antes** de qualquer consulta ser executada:
autenticação por perfil, registro da pergunta e os guardrails que validam a SQL
candidata gerada pelo motor. É a camada que garante que apenas consultas
seguras, no escopo autorizado, cheguem ao banco.

Decisões de fundo: [DA-GOV-001](../arquitetura/02_DECISOES_ARQUITETURAIS.md#da-gov-001-acesso-por-perfil-mapeado-a-tabelas-gold),
[DA-GOV-002](../arquitetura/02_DECISOES_ARQUITETURAIS.md#da-gov-002-conexão-duckdb-somente-leitura-defesa-em-profundidade).

## 2. Perfis de acesso

Cada perfil só enxerga as tabelas Gold autorizadas (`src/config.py:63-73`):

| Perfil | Tabelas Gold autorizadas |
|---|---|
| `gestor` | todas as tabelas Gold |
| `enfermagem` | `gold.leitos_status`, `gold.ocupacao_unidade` |
| `administrativo` | `gold.ocupacao_unidade`, `gold.ocupacao_diaria` |

## 3. Controles de governança (guardrails de entrada)

A serem implementados em `src/governance.py`. Cada controle tem identificador
estável e mapeia a um requisito regulatório (ver
[governanca/01_CONFORMIDADE_REGULATORIA.md](../governanca/01_CONFORMIDADE_REGULATORIA.md)).

| ID | Controle | Requisito | Status |
|---|---|---|---|
| `CTRL-GOV-001` | A SQL gerada deve ser uma única instrução somente leitura (apenas `SELECT`/`WITH`) | REG-LGPD-005 | IMPLEMENTADO |
| `CTRL-GOV-002` | Bloquear comandos de escrita ou administrativos (`insert`, `update`, `delete`, `drop`, `alter`, `create`, `attach`, `copy`, `pragma`, etc.), funções de leitura de arquivos (`read_*`), funções de tabela que recebem o nome como texto (`query`, `query_table`) e catálogo (`information_schema`, `duckdb_*`, `sqlite_*`, `pragma_*`) | REG-LGPD-005, REG-LGPD-003 | IMPLEMENTADO |
| `CTRL-GOV-003` | Bloquear múltiplas instruções (presença de `;` no meio) | REG-LGPD-005 | IMPLEMENTADO |
| `CTRL-GOV-004` | Bloquear acesso às camadas Bronze e Silver | REG-LGPD-003 | IMPLEMENTADO |
| `CTRL-GOV-005` | Permitir apenas as tabelas Gold autorizadas para o perfil | REG-LGPD-004 | IMPLEMENTADO |
| `CTRL-GOV-006` | Executar em conexão DuckDB somente leitura (defesa em profundidade) | REG-LGPD-005 | IMPLEMENTADO |
| `CTRL-GOV-007` | Executar apenas sobre o arquivo isolado da Gold (`GOLD_DB_PATH`), no qual Bronze e Silver não existem; isolamento no dado, independente do texto da SQL | REG-LGPD-003 | IMPLEMENTADO |
| `CTRL-GOV-008` | Barrar e mascarar dado pessoal (CPF, e-mail, telefone) no **texto da pergunta**, antes de qualquer chamada ao motor e antes do registro na trilha | REG-LGPD-008, REG-LGPD-001 | IMPLEMENTADO |

A análise textual (001 a 005) remove comentários e literais de texto antes da
inspeção (`src/governance.py:_limpar`), de modo que uma palavra proibida
escondida em comentário ou dentro de uma string não escape do controle nem gere
falso positivo. O `CTRL-GOV-002` foi reforçado para também barrar funções de I/O
do DuckDB (leitura de arquivos arbitrários), que escapariam do escopo somente
leitura sobre as tabelas Gold.

**Limite da análise textual e por que ela não é a única barreira.** A banca
simulada ([rodada 01, P-09](../tcc/banca/2026-09-13_rodada-01.md)) mostrou que
o esvaziamento de literais, necessário para evitar falsos positivos, criava um
ponto cego: em `query_table('bronze.paciente')` o nome da tabela é um literal e
sumia antes de CTRL-GOV-004 inspecionar; consultas ao catálogo
(`information_schema.columns`, `duckdb_tables()`) listavam schemas e colunas
internas, inclusive `cpf`, sem citar `bronze` nem `silver`; e um alias
(`cpf AS c`) derrotava o filtro de saída por nome de coluna. Antes da
correção, três dessas consultas executavam e devolviam dados da Bronze. A
resposta foi dupla: (a) CTRL-GOV-002 passou a barrar `query`, `query_table`,
`information_schema` e os prefixos `duckdb_`, `sqlite_`, `pragma_` e `read_`;
(b) o isolamento deixou de depender do texto, com a execução restrita ao
arquivo da Gold isolada (CTRL-GOV-007). Com (b), mesmo uma SQL que escapasse de
(a) não teria o que ler: o banco não contém Bronze nem Silver. A lista de
palavras é, portanto, defesa adicional, e a garantia vem do dado.

### CTRL-GOV-007: Execução apenas sobre a Gold isolada

- **Descrição**: `src/governance.py:conectar_somente_leitura` abre, em modo
  somente leitura, exclusivamente `config.GOLD_DB_PATH`
  (`data/gold_isolada.duckdb`), gerado por `src/pipeline.py:exportar_gold` com
  as quatro tabelas Gold e nada mais. É a materialização de
  [DA-LAKE-005](../arquitetura/02_DECISOES_ARQUITETURAIS.md#da-lake-005-isolamento-físico-da-gold-em-arquivo-próprio).
- **Motivação**: tornar "Bronze e Silver inacessíveis ao modelo" uma
  propriedade do dado, verificável por teste, e não uma consequência de
  expressões regulares.
- **Status**: IMPLEMENTADO (2026-09-13). Teste em `src/pipeline.py`.

### CTRL-GOV-008: Dado pessoal no texto da pergunta

- **Descrição**: `src/governance.py:filtrar_pii` verifica a pergunta contra os
  padrões de `config.PADROES_PII` (CPF com ou sem pontuação, e-mail, telefone
  brasileiro). Havendo ocorrência, a pergunta é recusada na entrada (evento
  `bloqueado`, controle `CTRL-GOV-008`) e cada trecho é substituído por
  `config.MASCARA_PII`; o texto original não chega ao motor, que pode ser uma
  API externa, nem à trilha. `registrar_pergunta` e `registrar_resposta`
  aplicam a máscara por conta própria, de modo que dado pessoal não entra no
  log mesmo que um chamador esqueça o filtro.
- **Motivação**: a banca simulada ([rodada 01, P-18](../tcc/banca/2026-09-13_rodada-01.md))
  apontou que um gestor podia digitar um CPF na pergunta e o texto saía para a
  API e ficava na auditoria. É o controle "antes da chamada" pedido ali, e a
  peça de código do inventário do que sai do perímetro
  ([camadas/03](03_MOTOR_TEXT2SQL.md) §3.3).
- **Limitação declarada**: nome próprio não é detectável por padrão. As
  mitigações são a implantação local, em que nada sai do perímetro
  ([DA-GOV-003](../arquitetura/02_DECISOES_ARQUITETURAIS.md#da-gov-003-implantação-local-como-decisão-de-arquitetura-e-inventário-do-que-sai-do-perímetro)),
  e a abstração do schema e dos valores antes do envio (MaskSQL, Abedini et
  al. 2025), registrada como trabalho futuro. Datas soltas ficam fora do
  filtro de propósito: uma pergunta legítima pode citar a data de um dia.
- **Status**: IMPLEMENTADO (2026-09-20, Etapa E). Teste em
  `python -m src.governance`; exercitado pelas perguntas X03 e X05 do conjunto
  adversarial.

### CTRL-GOV-001: SQL única e somente leitura

- **Descrição**: A SQL deve conter uma só instrução e iniciar por `SELECT` ou
  `WITH`. Qualquer outra forma é rejeitada antes da execução.
- **Status**: IMPLEMENTADO (`src/governance.py:validar_sql`).
- **Origem**: `GUIA_DESENVOLVIMENTO.md` (seção Governança).

### CTRL-GOV-002 a CTRL-GOV-006

Demais guardrails de entrada conforme a tabela acima. O conjunto forma uma
verificação em camadas: análise textual da SQL (001-005) somada à barreira do
banco em modo somente leitura (006).

## 4. Registro da pergunta

Toda pergunta recebida é registrada antes da execução, com horário real (UTC),
data de simulação, usuário e perfil (`src/governance.py:registrar_pergunta`),
já com dado pessoal mascarado (CTRL-GOV-008).
O registro é uma linha JSON com `evento = "entrada"` e um `id_interacao`,
anexada à trilha em `config.AUDIT_LOG_PATH` e encadeada por hash ao registro
anterior. O registro de entrada compõe, junto com o registro de saída
([CTRL-AUD-001](04_VALIDACAO_SAIDA.md)), a trilha de auditoria completa exigida
por [REG-LGPD-007](../governanca/01_CONFORMIDADE_REGULATORIA.md). A
autenticação do usuário e do perfil fica fora do escopo do protótipo; o ponto
de integração é a assinatura desta função.

## 5. Mapeamento para o código

| Item | Local | Status |
|---|---|---|
| Perfis e tabelas autorizadas | `src/config.py:63-73` | IMPLEMENTADO |
| Guardrails de entrada | `src/governance.py:validar_sql` | IMPLEMENTADO |
| Registro de auditoria de entrada | `src/governance.py:registrar_pergunta` | IMPLEMENTADO |
| Conexão somente leitura e restrita à Gold isolada | `src/governance.py:conectar_somente_leitura` | IMPLEMENTADO |
| Lista de palavras e prefixos proibidos | `src/governance.py` (`PALAVRAS_PROIBIDAS`, `PREFIXOS_PROIBIDOS`) | IMPLEMENTADO |
| Filtro e máscara de dado pessoal na pergunta | `src/governance.py:filtrar_pii`; `src/config.py:PADROES_PII`, `MASCARA_PII` | IMPLEMENTADO |

## 6. Teste rápido

Implementado no bloco `__main__` de `src/governance.py` (rode com
`python -m src.governance`). Cobre 7 casos válidos que **devem** passar (leitura
em escopo autorizado, ponto e vírgula final tolerado, palavra proibida dentro de
string sem falso positivo, colunas e aliases que contêm prefixos proibidos como
substring) e 18 casos que **devem** ser bloqueados, cada um com o controle exato
esperado: SQL vazia e `EXPLAIN` (001); `DELETE` em CTE, `read_csv`, `DROP`,
`query_table`, `query`, `information_schema`, `duckdb_tables()`,
`duckdb_columns()`, `pragma_table_info()`, `sqlite_master` e `read_text` (002);
duas instruções com `;` (003); referência a `silver.*`/`bronze.*` (004); tabela
Gold fora do perfil e perfil desconhecido (005). O CTRL-GOV-008 é coberto por
cinco perguntas com CPF, e-mail ou telefone (barradas e mascaradas) e cinco
sem dado pessoal, com números e datas, que não podem gerar falso positivo.
Também valida que o registro de auditoria é gravado com os campos esperados e
que um CPF passado ao registro nunca aparece no arquivo. O isolamento físico (007) é
testado em `python -m src.pipeline`, que gera os dados.
