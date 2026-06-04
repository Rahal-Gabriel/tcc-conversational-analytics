# REPRO: Reprodutibilidade, Versionamento e CI

**Status**: IMPLEMENTADO
**Prioridade**: ALTA
**Última atualização**: 2026-06-04
**Alimenta (template TCC)**: Metodologia · Resultados Preliminares

---

## 1. Propósito

Descrever a infraestrutura que torna o experimento reprodutível e íntegro:
determinismo, ambiente fixado, versionamento por etapa e integração contínua.
É o que permite a terceiros reproduzir exatamente os mesmos dados e números
([RNC-003](../arquitetura/03_REGRAS_CRITICAS.md#rnc-003-determinismo-e-reprodutibilidade)).

## 2. Determinismo

| Parâmetro | Valor | Local |
|---|---|---|
| `SEED` | 42 | `src/config.py:25` |
| `SIM_TODAY` | 2026-05-31 | `src/config.py:14` |
| `HIST_DAYS` | 90 | `src/config.py:22` |

Uma única `SEED` governa o Faker e todos os sorteios; `SIM_TODAY` ancora toda a
geração e qualquer consulta que mencione "hoje". A mesma configuração reproduz a
mesma Bronze, verificado entre Python 3.12 e 3.14.

## 3. Ambiente fixado

- Python 3.12, fixado em `.python-version`; a CI usa a mesma versão.
- Dependências mínimas em `requirements.txt` (`faker`, `duckdb`); a chamada ao
  LLM usa `urllib` da biblioteca padrão.

## 4. Versionamento por etapa

- Branch principal `main` sempre funcional e reprodutível; não se commita direto
  nela durante o desenvolvimento.
- Cada etapa vive em branch curto (`feat/`, `fix/`, `docs/`) e entra na `main`
  por Pull Request com squash merge (uma etapa, um commit na `main`).
- Marcos reprodutíveis são marcados com tag git, em especial o commit que gera
  os números do TCC (o par código + `SEED`).
- Commits em português, com prefixo semântico leve.

## 5. Integração contínua

O workflow `.github/workflows/ci.yml` roda a cada push e PR na `main`:

1. Configura Python 3.12 e instala dependências.
2. Executa os testes rápidos dos módulos (hoje `python -m src.config`;
   acrescentar os demais conforme implementados).
3. Quando `run_all.py` existir, roda o autoteste com o motor oráculo.

A CI usa **apenas** o motor oráculo, que não precisa de chave nem tem custo. O
modo LLM nunca roda na CI ([RNC-004](../arquitetura/03_REGRAS_CRITICAS.md#rnc-004-nenhuma-credencial-no-código-ou-no-histórico-do-git)).

## 6. Integridade dos resultados

A separação explícita entre o motor LLM (que gera os números do TCC) e o oráculo
(apenas autoteste) impede apresentar autoteste como desempenho do modelo
([RNC-002](../arquitetura/03_REGRAS_CRITICAS.md#rnc-002-integridade-dos-resultados-acurácia-só-vem-do-llm-real)).
Quando os resultados de avaliação forem gerados, o commit e a `SEED` que os
produziram serão registrados para permitir reprodução exata.

## 7. Estado atual

| Item | Situação |
|---|---|
| Determinismo (SEED, SIM_TODAY) | VALIDADO |
| Ambiente fixado (Python 3.12) | IMPLEMENTADO |
| Versionamento por etapa (branch + PR squash) | IMPLEMENTADO |
| CI verde a cada push/PR (motor oráculo) | IMPLEMENTADO |

Registrado como resultado parcial em
[RES-003](../tcc/01_RESULTADOS_PRELIMINARES.md#res-003-reprodutibilidade-e-integridade).
