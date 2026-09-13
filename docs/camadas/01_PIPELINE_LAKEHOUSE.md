# LAKE: Camada 1 - Pipeline Lakehouse

**Status**: IMPLEMENTADO (Bronze, Silver, Gold e Gold isolada com teste rápido passando)
**Prioridade**: ALTA
**Última atualização**: 2026-09-13
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

## 3. Camada Silver (limpa e anonimizada) - IMPLEMENTADA

Transformação em `src/pipeline.py:construir_silver`:

- Remove `nome`, `cpf` e `data_nascimento` (não sobrevivem à Silver).
- Pseudonimiza `id_paciente` por `id_paciente_pseudo`, com SHA-256 sobre
  `PSEUDO_SALT + id`, truncado em 16 hex (`src/pipeline.py:_pseudo`,
  `src/config.py:56`). O salt determinista preserva a reprodutibilidade
  ([RNC-003](../arquitetura/03_REGRAS_CRITICAS.md#rnc-003-determinismo-e-reprodutibilidade))
  e dificulta reverter o hash por força bruta sobre os poucos ids.
- Deriva `faixa_etaria` a partir da idade contra `SIM_TODAY` (nunca o relógio do
  sistema) e descarta a data
  ([DA-LAKE-004](../arquitetura/02_DECISOES_ARQUITETURAIS.md#da-lake-004-faixa-etária-derivada-substitui-a-data-de-nascimento)).
- `silver.unidade`, `silver.leito` e `silver.ocupacao_diaria` são espelho da
  Bronze (não contêm PII), tornando a Silver auto-suficiente como fonte da Gold.
- Invariante de saída verificada no teste: **nenhuma coluna de identificação
  direta do paciente** (`nome`, `cpf`, `data_nascimento`) existe em
  `silver.paciente`
  ([RNC-005](../arquitetura/03_REGRAS_CRITICAS.md#rnc-005-pii-nunca-sobrevive-à-silver)).
  O nome legítimo de unidade (`silver.unidade.nome`) não é PII e não conta.

Faixas etárias (limite inferior inclusivo): `0-17, 18-39, 40-59, 60-79, 80+`
(`src/config.py:49`).

## 4. Camada Gold (única exposta ao LLM) - IMPLEMENTADA

Quatro tabelas, agregadas e sem dado individual identificável
([DA-LAKE-003](../arquitetura/02_DECISOES_ARQUITETURAIS.md#da-lake-003-gold-é-a-única-camada-exposta-ao-llm),
`src/config.py:42-47`):

| Tabela Gold | Conteúdo |
|---|---|
| `gold.leitos_status` | snapshot do estado de cada leito em `SIM_TODAY` |
| `gold.ocupacao_unidade` | métricas por unidade: total, ocupados, livres, bloqueados, taxa de ocupação (0-100) |
| `gold.ocupacao_diaria` | série histórica diária do hospital |
| `gold.internacoes` | internações com `faixa_etaria`, `tempo_permanencia`, flag `ativa` |

Regras de derivação (`src/pipeline.py:construir_gold`): `ativa = TRUE` quando
`data_alta_real` é nula; `tempo_permanencia` em dias apenas para internações
encerradas (nulo se ativa); `taxa_ocupacao` em percentual `[0,100]`. A Gold
**não** carrega `id_paciente_pseudo` (campo sensível em
`src/config.py:59`), preservando a minimização de exposição
([DA-LAKE-003](../arquitetura/02_DECISOES_ARQUITETURAIS.md#da-lake-003-gold-é-a-única-camada-exposta-ao-llm)).

> Números reprodutíveis da Silver/Gold (snapshot por unidade, distribuição de
> faixa etária, internações ativas) estão em
> [RES-005](../tcc/01_RESULTADOS_PRELIMINARES.md#res-005-camadas-silver-e-gold-anonimizadas-e-agregadas).

### 4.1. Gold isolada (arquivo próprio) - IMPLEMENTADA

Conforme [DA-LAKE-005](../arquitetura/02_DECISOES_ARQUITETURAIS.md#da-lake-005-isolamento-físico-da-gold-em-arquivo-próprio),
`src/pipeline.py:exportar_gold` copia as quatro tabelas Gold para
`data/gold_isolada.duckdb` (`config.GOLD_DB_PATH`), recriado do zero a cada
execução. O schema dentro do arquivo também se chama `gold`, para que a SQL do
motor (`gold.tabela`) seja idêntica nas duas bases. O nome do arquivo é
`gold_isolada`, e não `gold`, porque o DuckDB usa o nome do arquivo como nome
do catálogo, e catálogo e schema homônimos tornam `gold.tabela` ambíguo.

| Base | Conteúdo | Quem conecta |
|---|---|---|
| `data/lakehouse.duckdb` | Bronze, Silver e Gold | apenas o pipeline (geração e transformação) |
| `data/gold_isolada.duckdb` | somente as quatro tabelas Gold | motor Text-to-SQL, harness de avaliação, qualquer consulta de usuário |

O teste rápido verifica que a Gold isolada contém só o schema `gold`, com as
quatro tabelas e as mesmas contagens do lakehouse, nenhuma coluna de
`CAMPOS_SENSIVEIS`, e que consultas a Bronze e Silver (inclusive por função de
tabela) são recusadas pelo próprio banco.

## 5. Mapeamento para o código

| Item | Local | Status |
|---|---|---|
| Volumes e janela | `src/config.py:26-29` | IMPLEMENTADO |
| Geração Bronze | `src/data_gen.py:construir` | IMPLEMENTADO |
| Schema Bronze | `src/data_gen.py:_criar_schema_e_tabelas` | IMPLEMENTADO |
| Salt da pseudonimização | `src/config.py:56` (`PSEUDO_SALT`) | IMPLEMENTADO |
| Transformação Silver | `src/pipeline.py:construir_silver` | IMPLEMENTADO |
| Transformação Gold | `src/pipeline.py:construir_gold` | IMPLEMENTADO |
| Tabelas Gold autorizadas | `src/config.py:41-46` (`GOLD_TABLES`) | IMPLEMENTADO |
| Caminho da Gold isolada | `src/config.py` (`GOLD_DB_PATH`) | IMPLEMENTADO |
| Exportação da Gold isolada | `src/pipeline.py:exportar_gold` | IMPLEMENTADO |

## 6. Teste rápido

`python -m src.data_gen` gera a Bronze e valida invariantes: contagens de
unidade/leito/paciente exatas, `ocupacao_diaria = leitos × dias`, e internações
dentro da faixa esperada (1500 a 2900).

`python -m src.pipeline` gera a Bronze, constrói Silver e Gold e valida: nenhuma
coluna de PII direta em `silver.paciente` (RNC-005); `faixa_etaria` dentro do
domínio; pseudônimo determinista e sem colisão; `taxa_ocupacao ∈ [0,100]`;
`ativa ⟺ data_alta_real` nula com `tempo_permanencia` coerente; as quatro
tabelas Gold presentes; e soma de leitos por unidade igual a `VOL_LEITOS`.
Verifica ainda a Gold isolada (§4.1): só schema `gold`, contagens iguais às do
lakehouse, nenhum campo sensível, e recusa pelo banco das consultas que
contornavam a análise textual (`query_table('bronze.paciente')`,
`silver.paciente`, `bronze.paciente`). Este teste roda na CI.
