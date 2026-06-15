# AVAL: Metodologia de Avaliação

**Status**: IMPLEMENTADO (tubulação verde no oráculo; acurácia do LLM pendente de execução real)
**Prioridade**: ALTA
**Última atualização**: 2026-06-15
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
| `AVAL-001` | Acurácia por execution match (estrito) | Fração de perguntas cujo conjunto de resultados bate exatamente com a referência. **Métrica primária.** |
| `AVAL-002` | Taxa de aprovação na governança | Fração de SQL geradas que passam pelos guardrails sem bloqueio indevido |
| `AVAL-003` | Completude do log de auditoria | Fração de interações com registro completo (pergunta, resposta, SQL, evento) |
| (secundária) | Set match de conteúdo (relaxado, diagnóstico) | Fração de perguntas em que todos os valores da referência aparecem no resultado gerado, ignorando colunas extras, ordem e bloqueio de governança. **Diagnóstica, nunca substitui a primária.** |

### AVAL-001: Acurácia por execution match

- **Descrição**: Executar a SQL gerada e a SQL de referência e comparar os
  conjuntos de resultados. Acurácia = fração de perguntas com conjuntos
  idênticos.
- **Normalização** antes de comparar
  ([DA-AVAL-002](../arquitetura/02_DECISOES_ARQUITETURAIS.md#da-aval-002-normalização-dos-resultados-antes-de-comparar)):
  floats arredondados a 2 casas (`src/evaluate.py:CASAS_DECIMAIS`), datas em ISO,
  linhas ordenadas (`src/evaluate.py:normalizar`). A normalização é a **única**
  fonte de arredondamento: as SQL de referência não pré-arredondam, para não punir
  uma resposta numericamente mais precisa que a referência.
- **Referência**: estilo do benchmark EHRSQL 2024.
- **Status**: IMPLEMENTADO (comparação por execution match em `src/evaluate.py:avaliar`).
- **Relacionado**: [DA-AVAL-001](../arquitetura/02_DECISOES_ARQUITETURAIS.md#da-aval-001-execution-match-no-estilo-ehrsql).

### Métrica secundária: set match de conteúdo (diagnóstica)

- **Descrição**: verifica se todos os valores do resultado de referência aparecem
  no resultado gerado, ignorando colunas extras, ordem e forma; a SQL gerada é
  executada mesmo quando a governança a barrou. Serve para separar "conteúdo
  correto" de divergência de projeção ou de bloqueio por escopo de perfil.
- **Papel**: estritamente **diagnóstica**. O execution match estrito (AVAL-001)
  permanece como métrica primária reportada; a secundária acompanha a análise de
  erros e nunca a substitui ([RNC-002](../arquitetura/03_REGRAS_CRITICAS.md#rnc-002-integridade-dos-resultados-acurácia-só-vem-do-llm-real)).
- **Código**: `src/evaluate.py:conteudo_coberto`.

### Procedência e reprodutibilidade do número do LLM

A acurácia reportada vem de execução real do motor LLM, com **`temperature=0`**
(`src/nl2sql.py`), modelo registrado no relatório (`config.ANTHROPIC_MODEL`) e
número de execuções anotado. Diferentemente do pipeline e dos dados (deterministas
e reprodutíveis), a chamada ao LLM externo não é estritamente reproduzível; o
número é, portanto, uma observação pontual, com modelo, temperatura e data
fixados e registrados. A CI executa apenas o oráculo, sem chave.

### AVAL-002 e AVAL-003

Indicadores de governança: medem se os controles funcionam (taxa de aprovação)
e se a trilha de auditoria é completa, alimentando a discussão de aderência
regulatória nos Resultados.

## 3. Conjunto de avaliação

Implementado em `src/questions.py`: cada item é um par (pergunta em português,
SQL de referência sobre a Gold), com perfil e tipo. O conjunto tem **18
perguntas** cobrindo os quatro tipos operacionais do domínio de ocupação de
leitos: status atual (5), métrica por unidade (5), série histórica (4) e
internações por faixa etária (4). Toda SQL de referência é determinista (ancorada
em `SIM_TODAY`), não pré-arredonda valores agregados e passa pelos guardrails de
entrada no escopo do próprio perfil.

O contrato do prompt ([DA-NL2SQL-002](../camadas/03_MOTOR_TEXT2SQL.md)) pede ao
motor que projete apenas as colunas necessárias e não arredonde agregados; são
esclarecimentos de especificação que alinham a saída ao que a pergunta pede,
sem ajustar a resposta em si.

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
| Conjunto pergunta → SQL de referência | `src/questions.py` | IMPLEMENTADO (18 perguntas) |
| Normalização dos resultados (tolerância 2 casas) | `src/evaluate.py:normalizar`, `CASAS_DECIMAIS` | IMPLEMENTADO |
| Set match de conteúdo (secundária, diagnóstica) | `src/evaluate.py:conteudo_coberto` | IMPLEMENTADO |
| Execution match e indicadores AVAL-001/002/003 | `src/evaluate.py:avaliar` | IMPLEMENTADO |
| Orquestração (`oracle` / `llm`) | `run_all.py` | IMPLEMENTADO |

## 6. Definição de pronto da avaliação

Os números de pesquisa só são coletados com `run_all.py llm` e chave válida. A
CI roda apenas `run_all.py oracle` (autoteste, sem custo). Ver
[avaliacao/02_REPRODUTIBILIDADE_CI.md](02_REPRODUTIBILIDADE_CI.md).
