# GOV: Camada 2 - Governança de Entrada

**Status**: PROJETADO
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

Cada perfil só enxerga as tabelas Gold autorizadas (`src/config.py:54-66`):

| Perfil | Tabelas Gold autorizadas |
|---|---|
| `gestor` | todas as tabelas Gold |
| `enfermagem` | `gold.leitos_status`, `gold.ocupacao_unidade` |
| `administrativo` | `gold.ocupacao_unidade`, `gold.ocupacao_diaria` |

## 3. Controles de governança (guardrails de entrada)

A serem implementados em `src/governance.py`. Cada controle tem identificador
estável e mapeia a um requisito regulatório (ver
[governanca/01_CONFORMIDADE_REGULATORIA.md](../governanca/01_CONFORMIDADE_REGULATORIA.md)).

| ID | Controle | Requisito |
|---|---|---|
| `CTRL-GOV-001` | A SQL gerada deve ser uma única instrução somente leitura (apenas `SELECT`/`WITH`) | REG-LGPD-005 |
| `CTRL-GOV-002` | Bloquear comandos de escrita ou administrativos (`insert`, `update`, `delete`, `drop`, `alter`, `create`, `attach`, `copy`, `pragma`, etc.) | REG-LGPD-005 |
| `CTRL-GOV-003` | Bloquear múltiplas instruções (presença de `;` no meio) | REG-LGPD-005 |
| `CTRL-GOV-004` | Bloquear acesso às camadas Bronze e Silver | REG-LGPD-003 |
| `CTRL-GOV-005` | Permitir apenas as tabelas Gold autorizadas para o perfil | REG-LGPD-004 |
| `CTRL-GOV-006` | Executar em conexão DuckDB somente leitura (defesa em profundidade) | REG-LGPD-005 |

### CTRL-GOV-001: SQL única e somente leitura

- **Descrição**: A SQL deve conter uma só instrução e iniciar por `SELECT` ou
  `WITH`. Qualquer outra forma é rejeitada antes da execução.
- **Status**: PROJETADO.
- **Origem**: `GUIA_DESENVOLVIMENTO.md` (seção Governança).

### CTRL-GOV-002 a CTRL-GOV-006

Demais guardrails de entrada conforme a tabela acima. O conjunto forma uma
verificação em camadas: análise textual da SQL (001-005) somada à barreira do
banco em modo somente leitura (006).

## 4. Registro da pergunta

Toda pergunta recebida é registrada antes da execução, com timestamp, usuário e
perfil. O registro de entrada compõe, junto com o registro de saída
([CTRL-AUD-001](04_VALIDACAO_SAIDA.md)), a trilha de auditoria completa exigida
por [REG-LGPD-007](../governanca/01_CONFORMIDADE_REGULATORIA.md).

## 5. Mapeamento para o código

| Item | Local | Status |
|---|---|---|
| Perfis e tabelas autorizadas | `src/config.py:54-66` | IMPLEMENTADO |
| Guardrails de entrada | `src/governance.py` | PROJETADO |
| Conexão somente leitura | `src/evaluate.py` / execução | PROJETADO |

## 6. Teste rápido (a implementar)

Casos de governança que **devem** ser bloqueados: SQL com `DROP`, SQL com duas
instruções separadas por `;`, SQL que referencia `bronze.*` ou `silver.*`, e SQL
que acessa tabela Gold fora do perfil. Cada caso vira um teste no bloco
`__main__` de `governance.py`.
