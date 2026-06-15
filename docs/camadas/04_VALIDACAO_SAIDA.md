# VALID: Camada 4 - Validação de Saída

**Status**: IMPLEMENTADO
**Prioridade**: CRÍTICA
**Última atualização**: 2026-06-15
**Alimenta (template TCC)**: Metodologia · Resultados Preliminares

---

## 1. Propósito

Descrever os controles aplicados **depois** da execução da SQL e antes de
entregar a resposta ao usuário: aterramento contra alucinação, filtro de dados
sensíveis e auditoria da resposta. É a última barreira de governança.

## 2. Controles de validação

A serem implementados em `src/governance.py`.

| ID | Controle | Requisito |
|---|---|---|
| `CTRL-VALID-001` | Aterramento: toda tabela referenciada na SQL deve existir no schema Gold conhecido | REG-ANPD-001 |
| `CTRL-VALID-002` | Filtro de saída: bloquear a resposta se qualquer coluna do resultado tiver nome de campo sensível | REG-LGPD-006 |
| `CTRL-AUD-001` | Auditoria: registrar toda pergunta e toda resposta com timestamp, usuário, perfil, SQL e evento | REG-LGPD-007 |

### CTRL-VALID-001: Aterramento (anti-alucinação)

- **Descrição**: Antes de aceitar o resultado, confirmar que todas as tabelas
  citadas na SQL pertencem ao schema Gold conhecido. Uma tabela inventada pelo
  LLM bloqueia a consulta.
- **Motivação**: Mitigar alucinação, risco destacado pela ANPD no Radar de IA
  Generativa.
- **Status**: IMPLEMENTADO (`src/governance.py:validar_saida`).
- **Relacionado**: [DA-VALID-001](../arquitetura/02_DECISOES_ARQUITETURAIS.md#da-valid-001-aterramento-contra-o-schema-gold-conhecido).

### CTRL-VALID-002: Filtro de campo sensível

- **Descrição**: Se qualquer coluna do resultado tiver nome de campo sensível
  (`nome`, `cpf`, `data_nascimento`, `id_paciente_pseudo`), a resposta é
  bloqueada.
- **Motivação**: Última barreira contra vazamento de dado sensível, mesmo que
  algo tenha escapado das camadas anteriores.
- **Status**: IMPLEMENTADO (`src/governance.py:validar_saida`).
- **Código**: `src/config.py:59` (`CAMPOS_SENSIVEIS`).
- **Relacionado**: [DA-VALID-002](../arquitetura/02_DECISOES_ARQUITETURAIS.md#da-valid-002-filtro-de-saída-por-nome-de-campo-sensível),
  [RNC-005](../arquitetura/03_REGRAS_CRITICAS.md#rnc-005-pii-nunca-sobrevive-à-silver).

### CTRL-AUD-001: Auditoria da pergunta e da resposta

- **Descrição**: Registrar em log toda pergunta recebida e toda resposta, com
  timestamp, usuário, perfil, SQL e o evento (`correto`, `incorreto`,
  `bloqueado`, `erro`).
- **Motivação**: Rastreabilidade e prestação de contas, exigidas tanto pela
  LGPD (responsabilização) quanto pelas normas da ANVISA (rastreabilidade do
  software de saúde).
- **Status**: IMPLEMENTADO. Registro de entrada em
  `src/governance.py:registrar_pergunta` e registro de resposta em
  `src/governance.py:registrar_resposta`, com o evento da interação.
- **Código**: `src/config.py:37` (`AUDIT_LOG_PATH`);
  `src/governance.py:registrar_pergunta` (entrada);
  `src/governance.py:registrar_resposta` (resposta e evento).
- **Relacionado**: [REG-LGPD-007](../governanca/01_CONFORMIDADE_REGULATORIA.md),
  [REG-ANVISA-001](../governanca/01_CONFORMIDADE_REGULATORIA.md).

## 3. Eventos de auditoria

| Evento | Significado |
|---|---|
| `correto` | Resultado bate com a referência (execution match positivo) |
| `incorreto` | Resultado não bate com a referência |
| `bloqueado` | Consulta barrada por algum guardrail (entrada ou saída) |
| `erro` | Falha de execução (SQL inválida, erro de banco) |

A completude do log é um dos indicadores de avaliação
([AVAL-003](../avaliacao/01_METODOLOGIA_AVALIACAO.md)).

## 4. Mapeamento para o código

| Item | Local | Status |
|---|---|---|
| Campos sensíveis | `src/config.py:59` (`CAMPOS_SENSIVEIS`) | IMPLEMENTADO |
| Caminho do log de auditoria | `src/config.py:37` (`AUDIT_LOG_PATH`) | IMPLEMENTADO |
| Registro de auditoria da entrada | `src/governance.py:registrar_pergunta` | IMPLEMENTADO |
| Aterramento e filtro de saída | `src/governance.py:validar_saida` | IMPLEMENTADO |
| Registro da resposta e evento | `src/governance.py:registrar_resposta` | IMPLEMENTADO |

## 5. Teste rápido

`python -m src.governance`: além dos casos de entrada, cobre os casos que
**devem** bloquear na saída — SQL que cita uma tabela Gold inexistente
(aterramento, CTRL-VALID-001) e resultado cuja projeção inclui uma coluna
sensível (filtro de saída, CTRL-VALID-002) — e confirma que `registrar_resposta`
grava a interação com o evento. O fluxo completo (entrada → execução → saída →
auditoria) é exercitado de ponta a ponta em `python run_all.py oracle`.
