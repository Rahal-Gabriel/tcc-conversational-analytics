# AVAL: Metodologia de Avaliação

**Status**: PROJETADO
**Prioridade**: ALTA
**Última atualização**: 2026-06-04
**Alimenta (template TCC)**: Metodologia · Resultados Preliminares

---

## 1. Propósito

Descrever como o protótipo será avaliado: a métrica de acurácia (execution
match), o conjunto de avaliação e os indicadores complementares de governança.
A hipótese do TCC (acurácia superior a 80%) só será testada após a
implementação do harness e uma execução real com o motor LLM
([RNC-002](../arquitetura/03_REGRAS_CRITICAS.md#rnc-002-integridade-dos-resultados-acurácia-só-vem-do-llm-real)).

## 2. Critérios e indicadores

| ID | Indicador | Como se mede |
|---|---|---|
| `AVAL-001` | Acurácia por execution match | Fração de perguntas cujo conjunto de resultados bate com a referência |
| `AVAL-002` | Taxa de aprovação na governança | Fração de SQL geradas que passam pelos guardrails sem bloqueio indevido |
| `AVAL-003` | Completude do log de auditoria | Fração de interações com registro completo (pergunta, resposta, SQL, evento) |

### AVAL-001: Acurácia por execution match

- **Descrição**: Executar a SQL gerada e a SQL de referência e comparar os
  conjuntos de resultados. Acurácia = fração de perguntas com conjuntos
  idênticos.
- **Normalização** antes de comparar
  ([DA-AVAL-002](../arquitetura/02_DECISOES_ARQUITETURAIS.md#da-aval-002-normalização-dos-resultados-antes-de-comparar)):
  floats arredondados, datas em ISO, linhas ordenadas.
- **Referência**: estilo do benchmark EHRSQL 2024.
- **Status**: PROJETADO.
- **Relacionado**: [DA-AVAL-001](../arquitetura/02_DECISOES_ARQUITETURAIS.md#da-aval-001-execution-match-no-estilo-ehrsql).

### AVAL-002 e AVAL-003

Indicadores de governança: medem se os controles funcionam (taxa de aprovação)
e se a trilha de auditoria é completa, alimentando a discussão de aderência
regulatória nos Resultados.

## 3. Conjunto de avaliação

A implementar em `src/questions.py`: cada item é um par (pergunta em português,
SQL de referência sobre a Gold). O conjunto cobre os tipos de pergunta
operacional do domínio de ocupação de leitos (status atual, métricas por
unidade, série histórica, internações por faixa etária).

## 4. Os dois motores na avaliação

- **LLM**: gera os números reportados no TCC.
- **Oráculo**: devolve a SQL de referência; com ele, o execution match deve dar
  100% (autoteste da tubulação). Ver
  [camadas/03_MOTOR_TEXT2SQL.md](../camadas/03_MOTOR_TEXT2SQL.md).

Defesa em profundidade: a execução usa conexão DuckDB somente leitura
([CTRL-GOV-006](../camadas/02_GOVERNANCA_ENTRADA.md)).

## 5. Mapeamento para o código

| Item | Local | Status |
|---|---|---|
| Conjunto pergunta → SQL de referência | `src/questions.py` | PROJETADO |
| Execution match e indicadores | `src/evaluate.py` | PROJETADO |
| Orquestração (`oracle` / `llm`) | `run_all.py` | PROJETADO |

## 6. Definição de pronto da avaliação

Os números de pesquisa só são coletados com `run_all.py llm` e chave válida. A
CI roda apenas `run_all.py oracle` (autoteste, sem custo). Ver
[avaliacao/02_REPRODUTIBILIDADE_CI.md](02_REPRODUTIBILIDADE_CI.md).
