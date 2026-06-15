# ARQ-001: Arquitetura - Visão Geral

**Status**: IMPLEMENTADO
**Prioridade**: CRÍTICA
**Última atualização**: 2026-06-15
**Alimenta (template TCC)**: Introdução · Metodologia · Resultados Preliminares

---

## 1. Propósito

Apresentar a visão macro da arquitetura de referência para Conversational
Analytics em ambiente hospitalar. O domínio de implementação e avaliação é a
**ocupação de leitos**, e toda a pesquisa usa dados **100% sintéticos**
(ver [RNC-001](03_REGRAS_CRITICAS.md#rnc-001-dados-100-sintéticos)).

A arquitetura organiza um pipeline de dados em camadas (Lakehouse
Bronze/Silver/Gold) sob um motor de consulta em linguagem natural baseado em
LLM, sustentado por um modelo de governança que atravessa todas as camadas e
endereça os requisitos da LGPD, das normas da ANVISA e das diretrizes da ANPD
(ver [governanca/01_CONFORMIDADE_REGULATORIA.md](../governanca/01_CONFORMIDADE_REGULATORIA.md)).

## 2. As quatro camadas

```
            +-------------------------------------------------------+
            |  Usuário (gestor | enfermagem | administrativo)       |
            |  pergunta em linguagem natural (português)            |
            +-------------------------------------------------------+
                                   |
            =======================|=================================
            |   CAMADA 2  GOVERNANÇA DE ENTRADA                     |
            |   autenticação por perfil, registro da pergunta,     |
            |   verificação de conformidade antes de executar      |
            =======================|=================================
                                   |
            =======================|=================================
            |   CAMADA 3  MOTOR DE IA (Text-to-SQL)                |
            |   LLM traduz pergunta -> SQL somente leitura na Gold |
            |   guardrails bloqueiam SQL fora do escopo            |
            =======================|=================================
                                   |  SQL validada
                                   v
            +-------------------------------------------------------+
            |   CAMADA 1  PIPELINE LAKEHOUSE (DuckDB)               |
            |                                                       |
            |   bronze  --->  silver  --->  gold                    |
            |   (PII       (limpa e      (métricas; ÚNICA          |
            |   proposital) anonimizada)  camada exposta ao LLM)    |
            +-------------------------------------------------------+
                                   |  resultado
                                   v
            =======================|=================================
            |   CAMADA 4  VALIDAÇÃO DE SAÍDA                        |
            |   aterramento anti-alucinação, filtro de sensíveis,  |
            |   auditoria da resposta entregue                      |
            =======================|=================================
                                   |
                                   v
                          resposta ao usuário
```

| # | Camada | Responsabilidade | Doc |
|---|---|---|---|
| 1 | Pipeline Lakehouse | Ingestão (Bronze), limpeza e anonimização (Silver), métricas (Gold) | [camadas/01](../camadas/01_PIPELINE_LAKEHOUSE.md) |
| 2 | Governança de entrada | Perfil, registro da pergunta, conformidade antes de executar | [camadas/02](../camadas/02_GOVERNANCA_ENTRADA.md) |
| 3 | Motor Text-to-SQL | Pergunta em português para SQL somente leitura na Gold | [camadas/03](../camadas/03_MOTOR_TEXT2SQL.md) |
| 4 | Validação de saída | Aterramento, filtro de sensíveis, auditoria | [camadas/04](../camadas/04_VALIDACAO_SAIDA.md) |

## 3. Fluxo de uma pergunta (ponta a ponta)

1. O usuário, autenticado em um perfil, faz uma pergunta em português.
2. A **governança de entrada** registra a pergunta e resolve as tabelas Gold
   autorizadas para o perfil ([CTRL-GOV-005](../camadas/02_GOVERNANCA_ENTRADA.md)).
3. O **motor** envia ao LLM o schema Gold e a data de referência, e recebe uma
   SQL candidata.
4. Os **guardrails** verificam que a SQL é uma única instrução somente leitura,
   sem comandos administrativos, restrita às tabelas autorizadas
   ([CTRL-GOV-001](../camadas/02_GOVERNANCA_ENTRADA.md) a CTRL-GOV-006).
5. A SQL aprovada executa em conexão DuckDB **somente leitura** sobre a Gold.
6. A **validação de saída** confere o aterramento e bloqueia colunas sensíveis
   ([CTRL-VALID-001](../camadas/04_VALIDACAO_SAIDA.md), CTRL-VALID-002).
7. A resposta e o evento (correto, incorreto, bloqueado, erro) entram no log de
   auditoria ([CTRL-AUD-001](../camadas/04_VALIDACAO_SAIDA.md)).

## 4. Componentes e mapeamento para o código

| Componente | Módulo de código | Status |
|---|---|---|
| Parâmetros centrais (SIM_TODAY, SEED, volumes, perfis, LLM) | `src/config.py` | IMPLEMENTADO |
| Geração sintética → Bronze | `src/data_gen.py` | IMPLEMENTADO |
| Bronze → Silver → Gold | `src/pipeline.py` | IMPLEMENTADO |
| Guardrails e auditoria | `src/governance.py` | IMPLEMENTADO |
| Motor Text-to-SQL + oráculo | `src/nl2sql.py` | IMPLEMENTADO |
| Conjunto de avaliação | `src/questions.py` | IMPLEMENTADO |
| Harness de avaliação | `src/evaluate.py` | IMPLEMENTADO |
| Orquestrador ponta a ponta | `run_all.py` | IMPLEMENTADO |

> A correspondência entre o protótipo local (DuckDB) e um ambiente produtivo
> (Delta Lake / Databricks) é uma decisão deliberada, registrada em
> [DA-ARQ-002](02_DECISOES_ARQUITETURAIS.md#da-arq-002-duckdb-como-lakehouse-local).

## 5. Relações com outros módulos

- O "porquê" de cada escolha está em [02_DECISOES_ARQUITETURAIS.md](02_DECISOES_ARQUITETURAIS.md).
- Os princípios inegociáveis estão em [03_REGRAS_CRITICAS.md](03_REGRAS_CRITICAS.md).
- A leitura regulatória de cada controle está em
  [governanca/01_CONFORMIDADE_REGULATORIA.md](../governanca/01_CONFORMIDADE_REGULATORIA.md).
- O que já é resultado verificável está em
  [tcc/01_RESULTADOS_PRELIMINARES.md](../tcc/01_RESULTADOS_PRELIMINARES.md).
