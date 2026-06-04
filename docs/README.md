# Documentação Modular do TCC - Conversational Analytics em saúde

## Propósito

Documentação modular da **arquitetura de referência para Conversational
Analytics em ambiente hospitalar**, objeto do TCC do MBA em Engenharia de
Software (USP/Esalq). Cada arquivo `.md` reúne decisões, regras, controles e
evidências extraídas do **código real** do protótipo e do **projeto de
pesquisa**, com rastreabilidade por identificadores estáveis.

A documentação cumpre dois papéis ao mesmo tempo:

- **Engenharia**: registrar a arquitetura, as decisões e os controles do
  protótipo, com referências a `arquivo:linha`.
- **Acadêmico**: alimentar diretamente as seções do template de Resultados
  Preliminares do TCC. Cada módulo declara que seção do template ele sustenta,
  e o índice reverso está em [tcc/02_MAPA_DOC_PARA_TEMPLATE.md](tcc/02_MAPA_DOC_PARA_TEMPLATE.md).

> A forma desta documentação (portal, modularização numerada, identificadores
> estáveis, ciclo de status, rastreabilidade ao código) foi inspirada na
> arquitetura de documentação do projeto Command Center (HSL), adaptada à
> escala e ao propósito acadêmico deste trabalho.

## Estatísticas

| Métrica | Total |
|---|---|
| Arquivos de documentação | 12 |
| Decisões Arquiteturais (DA-*) | 15 |
| Regras Críticas (RNC-*) | 5 |
| Requisitos Regulatórios (REG-*) | 11 |
| Controles de Governança (CTRL-*) | 9 |
| Critérios de Avaliação (AVAL-*) | 3 |
| Resultados Preliminares (RES-*) | 5 |

> Os totais são mantidos manualmente. Ao adicionar ou remover um identificador,
> atualize esta tabela e a contagem no módulo de origem.

## Estrutura

```
docs/
├── README.md                          # Este arquivo (portal/índice)
├── arquitetura/                        # Visão macro, decisões e regras críticas
│   ├── 01_VISAO_GERAL.md               # 4 camadas, diagrama, fluxo de dados
│   ├── 02_DECISOES_ARQUITETURAIS.md    # DA-* (o "porquê" de cada escolha)
│   └── 03_REGRAS_CRITICAS.md           # RNC-* (princípios inegociáveis)
├── camadas/                            # Uma doc por camada da arquitetura
│   ├── 01_PIPELINE_LAKEHOUSE.md        # Bronze / Silver / Gold, anonimização
│   ├── 02_GOVERNANCA_ENTRADA.md        # Perfis, registro, guardrails de entrada
│   ├── 03_MOTOR_TEXT2SQL.md            # Motor LLM + oráculo
│   └── 04_VALIDACAO_SAIDA.md           # Aterramento, filtro de saída, auditoria
├── governanca/
│   └── 01_CONFORMIDADE_REGULATORIA.md  # REG-* (LGPD, ANVISA, ANPD)
├── avaliacao/
│   ├── 01_METODOLOGIA_AVALIACAO.md     # Execution match, EHRSQL, indicadores
│   └── 02_REPRODUTIBILIDADE_CI.md      # Determinismo, versionamento, CI
└── tcc/
    ├── 01_RESULTADOS_PRELIMINARES.md   # Registro vivo de resultados (RES-*)
    └── 02_MAPA_DOC_PARA_TEMPLATE.md    # Ponte doc → seção do template do TCC
```

A navegação por tarefa (como usar a doc, mapa cruzado de módulos, prioridades
de leitura) fica no [GUIA_DESENVOLVIMENTO.md](../GUIA_DESENVOLVIMENTO.md) na raiz do repositório.

## Stack do protótipo

| Camada | Tecnologia |
|---|---|
| Linguagem | Python 3.12 (fixada em `.python-version`) |
| Lakehouse | DuckDB (schemas `bronze`, `silver`, `gold`) |
| Geração sintética | Faker (locale `pt_BR`) |
| Motor de IA | API Anthropic via `urllib` (sem SDK pesado) |
| Avaliação | Execution match estilo EHRSQL 2024 |
| Integração contínua | GitHub Actions (apenas motor oráculo) |

## Módulos - Arquitetura

| # | Arquivo | Prefixo | Descrição |
|---|---|---|---|
| 01 | [01_VISAO_GERAL.md](arquitetura/01_VISAO_GERAL.md) | ARQ | Visão macro das 4 camadas, diagrama, fluxo de dados |
| 02 | [02_DECISOES_ARQUITETURAIS.md](arquitetura/02_DECISOES_ARQUITETURAIS.md) | DA | Decisões arquiteturais e suas justificativas |
| 03 | [03_REGRAS_CRITICAS.md](arquitetura/03_REGRAS_CRITICAS.md) | RNC | Princípios que nunca podem ser violados |

## Módulos - Camadas da arquitetura

| # | Arquivo | Prefixo | Descrição |
|---|---|---|---|
| 01 | [01_PIPELINE_LAKEHOUSE.md](camadas/01_PIPELINE_LAKEHOUSE.md) | LAKE | Bronze, Silver e Gold; modelo de dados e anonimização |
| 02 | [02_GOVERNANCA_ENTRADA.md](camadas/02_GOVERNANCA_ENTRADA.md) | GOV | Perfis de acesso, registro e guardrails de entrada |
| 03 | [03_MOTOR_TEXT2SQL.md](camadas/03_MOTOR_TEXT2SQL.md) | NL2SQL | Tradução de pergunta em SQL (motor LLM e oráculo) |
| 04 | [04_VALIDACAO_SAIDA.md](camadas/04_VALIDACAO_SAIDA.md) | VALID | Aterramento, filtro de sensíveis e auditoria |

## Módulos - Governança e avaliação

| # | Arquivo | Prefixo | Descrição |
|---|---|---|---|
| - | [governanca/01_CONFORMIDADE_REGULATORIA.md](governanca/01_CONFORMIDADE_REGULATORIA.md) | REG | Mapeamento LGPD, ANVISA e ANPD para os controles |
| - | [avaliacao/01_METODOLOGIA_AVALIACAO.md](avaliacao/01_METODOLOGIA_AVALIACAO.md) | AVAL | Execution match, conjunto de avaliação, indicadores |
| - | [avaliacao/02_REPRODUTIBILIDADE_CI.md](avaliacao/02_REPRODUTIBILIDADE_CI.md) | REPRO | Determinismo, versionamento por etapa e CI |

## Módulos - TCC

| # | Arquivo | Prefixo | Descrição |
|---|---|---|---|
| 01 | [tcc/01_RESULTADOS_PRELIMINARES.md](tcc/01_RESULTADOS_PRELIMINARES.md) | RES | Registro vivo dos resultados parciais verificáveis |
| 02 | [tcc/02_MAPA_DOC_PARA_TEMPLATE.md](tcc/02_MAPA_DOC_PARA_TEMPLATE.md) | - | Ponte de cada módulo/ID para a seção do template |

## Convenções de identificadores

| Prefixo | Tipo | Exemplo |
|---|---|---|
| `DA-[MOD]-[NUM]` | Decisão Arquitetural | `DA-LAKE-003`: Gold é a única camada exposta ao LLM |
| `RNC-[NUM]` | Regra Crítica (inegociável) | `RNC-001`: Dados 100% sintéticos em toda etapa |
| `REG-[NORMA]-[NUM]` | Requisito Regulatório | `REG-LGPD-002`: Anonimização e pseudonimização |
| `CTRL-[MOD]-[NUM]` | Controle de Governança | `CTRL-GOV-001`: SQL única e somente leitura |
| `AVAL-[NUM]` | Critério de Avaliação | `AVAL-001`: Acurácia por execution match |
| `RES-[NUM]` | Resultado Preliminar | `RES-001`: Camada Bronze gerada e coerente |

Módulos (prefixo `[MOD]`): `ARQ` (arquitetura geral), `LAKE` (pipeline
Lakehouse), `GOV` (governança de entrada), `NL2SQL` (motor Text-to-SQL),
`VALID` (validação de saída), `REG` (regulatório), `AVAL` (avaliação),
`REPRO` (reprodutibilidade).

## Ciclo de status dos módulos

| Status | Descrição |
|---|---|
| `PROJETADO` | Definido no design; lógica ainda não implementada |
| `PARCIAL` | Implementação iniciada, mas incompleta |
| `IMPLEMENTADO` | Código pronto e com teste rápido passando |
| `VALIDADO` | Resultado verificado por execução real (números reprodutíveis) |

## Estado atual (2026-06-04)

| Módulo | Status |
|---|---|
| arquitetura/01_VISAO_GERAL | PARCIAL |
| arquitetura/02_DECISOES_ARQUITETURAIS | PARCIAL |
| arquitetura/03_REGRAS_CRITICAS | PARCIAL |
| camadas/01_PIPELINE_LAKEHOUSE | IMPLEMENTADO (Bronze, Silver e Gold) |
| camadas/02_GOVERNANCA_ENTRADA | IMPLEMENTADO |
| camadas/03_MOTOR_TEXT2SQL | PROJETADO |
| camadas/04_VALIDACAO_SAIDA | PROJETADO |
| governanca/01_CONFORMIDADE_REGULATORIA | PARCIAL |
| avaliacao/01_METODOLOGIA_AVALIACAO | PROJETADO |
| avaliacao/02_REPRODUTIBILIDADE_CI | IMPLEMENTADO |
| tcc/01_RESULTADOS_PRELIMINARES | documento vivo |
| tcc/02_MAPA_DOC_PARA_TEMPLATE | referência |
