# Conversational Analytics em saude (prototipo de TCC)

Prototipo funcional de uma arquitetura de referencia para consulta em linguagem
natural sobre dados clinicos, com governanca integrada e aderente a LGPD, as
normas da ANVISA e as diretrizes da ANPD. O dominio de avaliacao e a **ocupacao
de leitos hospitalares**, e toda a pesquisa usa dados **100% sinteticos**.

Orientacoes detalhadas de desenvolvimento estao em [GUIA_DESENVOLVIMENTO.md](GUIA_DESENVOLVIMENTO.md), e a
documentacao modular completa da arquitetura, governanca, avaliacao e dos
resultados preliminares esta em [docs/](docs/README.md).

## Arquitetura em quatro camadas

1. **Pipeline Lakehouse** (DuckDB local): Bronze (bruto, com PII proposital),
   Silver (limpa e pseudonimizada) e Gold (metricas e registros minimizados, unica camada exposta ao LLM).
2. **Governanca de entrada**: autenticacao por perfil, registro de toda
   pergunta e verificacao de conformidade antes de qualquer execucao.
3. **Motor Text-to-SQL**: traduz a pergunta em portugues para uma SQL somente
   leitura sobre a Gold, via LLM, restrita por guardrails.
4. **Validacao de saida**: aterramento anti-alucinacao, filtro de dados
   sensiveis e auditoria das respostas.

## Requisitos

- Python 3.12 (versao fixada em [.python-version](.python-version); a CI usa a
  mesma)
- Dependencias em [requirements.txt](requirements.txt) (faker, duckdb)

## Instalacao

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Alternativa reprodutivel (Docker)

Para reproduzir o experimento no mesmo ambiente em qualquer maquina (versao de
Python, do DuckDB e do sistema fixadas pela imagem):

```bash
docker build -t tcc-conversational-analytics:repro .
docker run --rm tcc-conversational-analytics:repro   # verificacao rapida, sem chave
```

A chave da API nunca entra na imagem; quando precisar do modo LLM, injete-a em
runtime com `-e ANTHROPIC_API_KEY="$ANTHROPIC_API_KEY"`. Detalhes em
[docs/avaliacao/02_REPRODUTIBILIDADE_CI.md](docs/avaliacao/02_REPRODUTIBILIDADE_CI.md).

## Configuracao do LLM

As credenciais e o modelo sao lidos do ambiente, nunca embutidos no codigo:

```bash
export ANTHROPIC_API_KEY="sua-chave"
export ANTHROPIC_MODEL="claude-sonnet-4-6"   # opcional, este e o padrao
```

Os demais parametros (data de referencia, semente, volumes, perfis de acesso)
ficam centralizados em [src/config.py](src/config.py).

## Estrutura

```
tcc-conversational-analytics/
  GUIA_DESENVOLVIMENTO.md            # orientacoes de desenvolvimento
  README.md
  requirements.txt
  run_all.py           # orquestrador (a implementar)
  src/
    config.py          # parametros centrais (SIM_TODAY, SEED, volumes, perfis, LLM)
    data_gen.py        # geracao sintetica -> Bronze (a implementar)
    pipeline.py        # Bronze -> Silver -> Gold (a implementar)
    governance.py      # guardrails, validacao de saida e trilha de auditoria
    nl2sql.py          # motor Text-to-SQL + oraculo (a implementar)
    questions.py       # conjunto de avaliacao (a implementar)
    evaluate.py        # execution match, desfechos de governanca e Soft F1
  data/                # lakehouse.duckdb (Bronze/Silver/Gold) e gold_isolada.duckdb (so Gold), nao versionados
  results/             # saidas de avaliacao e log de auditoria (nao versionado)
```

## Estado atual

Etapa inicial: estrutura de pastas e `src/config.py`. Os demais modulos ainda
nao foram implementados.

## Verificacao rapida

```bash
python -m src.config   # imprime os parametros e roda o autoteste
```
