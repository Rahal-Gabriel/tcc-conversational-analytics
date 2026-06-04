# LAKE: Camada 1 - Pipeline Lakehouse

**Status**: PARCIAL (Bronze implementada; Silver e Gold projetadas)
**Prioridade**: ALTA
**Última atualização**: 2026-06-04
**Alimenta (template TCC)**: Metodologia · Resultados Preliminares

---

## 1. Propósito

Descrever o pipeline de dados em três camadas (Bronze, Silver, Gold)
implementado em DuckDB. A Bronze recebe os dados sintéticos brutos com PII
proposital; a Silver limpa e anonimiza; a Gold expõe métricas agregadas, sendo
a **única camada visível ao motor de linguagem**.

Decisões de fundo: [DA-LAKE-001](../arquitetura/02_DECISOES_ARQUITETURAIS.md#da-lake-001-modelo-de-camadas-bronze--silver--gold)
a DA-LAKE-004. Regra crítica associada:
[RNC-005](../arquitetura/03_REGRAS_CRITICAS.md#rnc-005-pii-nunca-sobrevive-à-silver).

## 2. Camada Bronze (bruta, com PII proposital) - IMPLEMENTADA

A PII existe de propósito para que a anonimização na Silver seja real e
demonstrável ([DA-LAKE-002](../arquitetura/02_DECISOES_ARQUITETURAIS.md#da-lake-002-pii-proposital-na-bronze)).

| Tabela | Colunas | Observação |
|---|---|---|
| `bronze.unidade` | `id_unidade, nome, especialidade, andar` | 8 unidades, uma por especialidade |
| `bronze.leito` | `id_leito, id_unidade, tipo, status` | tipo ∈ {UTI, Semi-intensiva, Enfermaria} |
| `bronze.paciente` | `id_paciente, nome, cpf, data_nascimento, sexo` | `nome`, `cpf`, `data_nascimento` são PII |
| `bronze.internacao` | `id_internacao, id_paciente, id_leito, data_admissao, data_alta_prevista, data_alta_real` | estadias por leito, sem sobreposição |
| `bronze.ocupacao_diaria` | `data, id_leito, situacao, id_internacao` | situacao ∈ {ocupado, livre, bloqueado} |

Parâmetros de geração (em `src/data_gen.py`):

- Pesos de tipo de leito: Enfermaria 60, Semi-intensiva 25, UTI 15.
- Fração de leitos bloqueados em toda a janela: 5%.
- Tempo de permanência por tipo (dias): UTI 3-20, Semi-intensiva 2-12,
  Enfermaria 1-10.
- Janela histórica: `HIST_DAYS = 90` dias até `SIM_TODAY` (inclusive).

Coerência garantida pelo gerador: cada leito ocupado em um dia tem uma
internação correspondente; estadias podem ser left-censored (começar antes da
janela) ou seguir ativas em `SIM_TODAY` (alta real nula).

> Números reprodutíveis da Bronze e do snapshot de ocupação estão em
> [RES-001](../tcc/01_RESULTADOS_PRELIMINARES.md#res-001-camada-bronze-gerada-e-coerente).

## 3. Camada Silver (limpa e anonimizada) - PROJETADA

Transformação a implementar em `src/pipeline.py`:

- Remover `nome` e `cpf`.
- Pseudonimizar `id_paciente` por hash (`id_paciente_pseudo`).
- Derivar `faixa_etaria` a partir de `data_nascimento` e descartar a data
  ([DA-LAKE-004](../arquitetura/02_DECISOES_ARQUITETURAIS.md#da-lake-004-faixa-etária-derivada-substitui-a-data-de-nascimento)).
- Invariante de saída: **nenhuma coluna de identificação direta** pode existir
  na Silver ([RNC-005](../arquitetura/03_REGRAS_CRITICAS.md#rnc-005-pii-nunca-sobrevive-à-silver)).

Faixas etárias (limite inferior inclusivo): `0-17, 18-39, 40-59, 60-79, 80+`
(`src/config.py:50`).

## 4. Camada Gold (única exposta ao LLM) - PROJETADA

Quatro tabelas, agregadas e sem dado individual identificável
([DA-LAKE-003](../arquitetura/02_DECISOES_ARQUITETURAIS.md#da-lake-003-gold-é-a-única-camada-exposta-ao-llm),
`src/config.py:42-47`):

| Tabela Gold | Conteúdo |
|---|---|
| `gold.leitos_status` | snapshot do estado de cada leito em `SIM_TODAY` |
| `gold.ocupacao_unidade` | métricas por unidade: total, ocupados, livres, bloqueados, taxa de ocupação (0-100) |
| `gold.ocupacao_diaria` | série histórica diária do hospital |
| `gold.internacoes` | internações com `faixa_etaria`, `tempo_permanencia`, flag `ativa` |

Regras de derivação: `ativa = TRUE` quando `data_alta_real` é nula;
`tempo_permanencia` em dias apenas para internações encerradas;
`taxa_ocupacao` em percentual.

## 5. Mapeamento para o código

| Item | Local | Status |
|---|---|---|
| Volumes e janela | `src/config.py:28-36` | IMPLEMENTADO |
| Geração Bronze | `src/data_gen.py:construir` | IMPLEMENTADO |
| Schema Bronze | `src/data_gen.py:_criar_schema_e_tabelas` | IMPLEMENTADO |
| Transformação Silver/Gold | `src/pipeline.py` | PROJETADO |
| Tabelas Gold autorizadas | `src/config.py:42-47` (`GOLD_TABLES`) | IMPLEMENTADO |

## 6. Teste rápido

`python -m src.data_gen` gera a Bronze e valida invariantes: contagens de
unidade/leito/paciente exatas, `ocupacao_diaria = leitos × dias`, e internações
dentro da faixa esperada (1500 a 2900).
