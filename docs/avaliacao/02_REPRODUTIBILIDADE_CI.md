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
- Dependências em `requirements.txt` com versões travadas (`==`): `faker==40.21.0`
  e `duckdb==1.5.3`. A trava por `==` é parte do determinismo, não detalhe de
  empacotamento: a mesma `SEED` só reproduz a mesma Bronze se a versão do Faker
  e do DuckDB também for a mesma. A chamada ao LLM usa `urllib` da biblioteca
  padrão, sem dependência externa.

### 3.1. Imagem reprodutível (Docker)

O `Dockerfile` na raiz fecha a última lacuna de reprodutibilidade: o
determinismo garante "mesma configuração, mesmos dados", mas a reprodução exata
ainda dependia do ambiente de quem executa (versão de Python, do DuckDB, do
sistema operacional). A imagem fixa esse ambiente inteiro, de modo que a banca
ou um avaliador reproduza o experimento com um único comando.

- Base travada por **digest**, não apenas por tag
  (`python:3.12.12-slim-bookworm@sha256:593bd06...`): garante o mesmo binário ao
  longo do tempo, mesmo que a tag seja republicada.
- Roda como usuário sem privilégios (`appuser`), não como root.
- `.dockerignore` mantém `.venv/`, `data/`, `results/`, caches e segredos fora
  da imagem.
- A chave da API **nunca** entra na imagem
  ([RNC-004](../arquitetura/03_REGRAS_CRITICAS.md#rnc-004-nenhuma-credencial-no-código-ou-no-histórico-do-git));
  é injetada apenas em runtime por variável de ambiente.

```bash
docker build -t tcc-conversational-analytics:repro .
docker run --rm tcc-conversational-analytics:repro              # teste rápido (sem chave, sem custo)
docker run --rm -e ANTHROPIC_API_KEY="$ANTHROPIC_API_KEY" \
  tcc-conversational-analytics:repro python run_all.py llm      # modo LLM (quando run_all.py existir)
```

## 4. Versionamento por etapa

- Branch principal `main` sempre funcional e reprodutível; não se commita direto
  nela durante o desenvolvimento.
- Cada etapa vive em branch curto (`feat/`, `fix/`, `docs/`) e entra na `main`
  por Pull Request com squash merge (uma etapa, um commit na `main`).
- Marcos reprodutíveis são marcados com tag git, em especial o commit que gera
  os números do TCC (o par código + `SEED`). A execução da Etapa D recebe a
  tag `etapa-D`, e seus artefatos (relatórios por célula, matriz consolidada,
  SQL geradas e trilha de auditoria encadeada) ficam versionados em
  `docs/tcc/anexos/etapa-D/`, fora de `results/` (que não é versionado).
- Commits em português, com prefixo semântico leve.

## 5. Integração contínua

O workflow `.github/workflows/ci.yml` roda a cada push e PR na `main`:

1. Configura Python 3.12 e instala dependências.
2. Executa os testes rápidos dos módulos (`config`, `questions`, `governance`,
   `nl2sql`, `pipeline`, `evaluate`, `matriz`), todos sem modelo.
3. Roda `python run_all.py oracle`, o autoteste da tubulação com o oráculo.

Um segundo job (`imagem`) constrói a imagem Docker e roda o mesmo teste rápido
dentro do container. É o que prova, automaticamente e a cada push, que o
experimento roda igual na CI e na máquina local, sustentando a afirmação de
reprodutibilidade.

A CI usa **apenas** o motor oráculo, que não precisa de chave nem de servidor
e não tem custo. Os motores reais (API, que exige chave, e local, que exige o
Ollama na máquina) nunca rodam na CI
([RNC-004](../arquitetura/03_REGRAS_CRITICAS.md#rnc-004-nenhuma-credencial-no-código-ou-no-histórico-do-git)).
Os números do motor local são gerados na máquina do autor e versionados como
artefato com tag, o que é o que um terceiro confere.

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
| Ambiente fixado (Python 3.12, deps travadas em `==`) | IMPLEMENTADO |
| Imagem reprodutível (Docker, base por digest) | IMPLEMENTADO |
| Versionamento por etapa (branch + PR squash) | IMPLEMENTADO |
| CI verde a cada push/PR (motor oráculo) | IMPLEMENTADO |

Registrado como resultado parcial em
[RES-003](../tcc/01_RESULTADOS_PRELIMINARES.md#res-003-reprodutibilidade-e-integridade).
