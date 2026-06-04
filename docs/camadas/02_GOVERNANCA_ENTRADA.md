# GOV: Camada 2 - Governança de Entrada

**Status**: IMPLEMENTADO
**Prioridade**: CRÍTICA
**Última atualização**: 2026-06-04
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
| `CTRL-GOV-002` | Bloquear comandos de escrita ou administrativos (`insert`, `update`, `delete`, `drop`, `alter`, `create`, `attach`, `copy`, `pragma`, etc.) e funções de leitura de arquivos (`read_csv`, `read_parquet`, etc.) | REG-LGPD-005 | IMPLEMENTADO |
| `CTRL-GOV-003` | Bloquear múltiplas instruções (presença de `;` no meio) | REG-LGPD-005 | IMPLEMENTADO |
| `CTRL-GOV-004` | Bloquear acesso às camadas Bronze e Silver | REG-LGPD-003 | IMPLEMENTADO |
| `CTRL-GOV-005` | Permitir apenas as tabelas Gold autorizadas para o perfil | REG-LGPD-004 | IMPLEMENTADO |
| `CTRL-GOV-006` | Executar em conexão DuckDB somente leitura (defesa em profundidade) | REG-LGPD-005 | IMPLEMENTADO |

A análise textual (001 a 005) remove comentários e literais de texto antes da
inspeção (`src/governance.py:_limpar`), de modo que uma palavra proibida
escondida em comentário ou dentro de uma string não escape do controle nem gere
falso positivo. O `CTRL-GOV-002` foi reforçado para também barrar funções de I/O
do DuckDB (leitura de arquivos arbitrários), que escapariam do escopo somente
leitura sobre as tabelas Gold.

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

Toda pergunta recebida é registrada antes da execução, com timestamp, usuário e
perfil (`src/governance.py:registrar_pergunta`). O registro é uma linha JSON com
`evento = "entrada"` anexada à trilha em `config.AUDIT_LOG_PATH`. O horário
ancora em `SIM_TODAY` (RNC-003) para que a trilha seja reproduzível. O registro
de entrada compõe, junto com o registro de saída
([CTRL-AUD-001](04_VALIDACAO_SAIDA.md)), a trilha de auditoria completa exigida
por [REG-LGPD-007](../governanca/01_CONFORMIDADE_REGULATORIA.md).

## 5. Mapeamento para o código

| Item | Local | Status |
|---|---|---|
| Perfis e tabelas autorizadas | `src/config.py:63-73` | IMPLEMENTADO |
| Guardrails de entrada | `src/governance.py:validar_sql` | IMPLEMENTADO |
| Registro de auditoria de entrada | `src/governance.py:registrar_pergunta` | IMPLEMENTADO |
| Conexão somente leitura | `src/governance.py:conectar_somente_leitura` | IMPLEMENTADO |

## 6. Teste rápido

Implementado no bloco `__main__` de `src/governance.py` (rode com
`python -m src.governance`). Cobre 5 casos válidos que **devem** passar (leitura
em escopo autorizado, ponto e vírgula final tolerado, palavra proibida dentro de
string sem falso positivo) e 10 casos que **devem** ser bloqueados, cada um com o
controle exato esperado: SQL vazia e `EXPLAIN` (001), `DELETE` em CTE e
`read_csv` e `DROP` (002), duas instruções com `;` (003), referência a
`silver.*`/`bronze.*` (004), tabela Gold fora do perfil e perfil desconhecido
(005). Também valida que o registro de auditoria é gravado com os campos
esperados.
