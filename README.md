# Conversational Analytics em saude (prototipo de TCC)

Prototipo funcional de uma arquitetura de referencia para consulta em linguagem
natural sobre dados clinicos, com governanca integrada e projetada para atender a LGPD, as
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

## Configuracao dos motores reais

O motor da fase de conclusao e **local**: um modelo aberto servido pelo Ollama
na propria maquina (sem custo, nada sai do perimetro). O motor via API
(Anthropic) foi o dos Resultados Preliminares e continua disponivel. Tudo e
lido do ambiente, nunca embutido no codigo:

```bash
# motor local (padrao)
ollama pull qwen2.5-coder:14b                     # uma vez; depois, servidor ativo
export MODELO_LOCAL="qwen2.5-coder:14b"           # opcional, este e o padrao
export OLLAMA_ENDPOINT="http://localhost:11434"   # opcional, este e o padrao

# motor via API (opcional)
export ANTHROPIC_API_KEY="sua-chave"
export ANTHROPIC_MODEL="claude-sonnet-4-6"        # opcional, este e o padrao
```

```bash
python run_all.py oracle                                         # autoteste, sem modelo
python run_all.py llm --motor local --celula C2 --repeticoes 3   # uma celula de prompt
python run_all.py llm --motor local --matriz                     # cinco celulas, k=3 (Etapa D)
python run_all.py llm --motor local --adversarial                # E0 e E1 sobre 18 legitimas + 25 adversariais (Etapa E)
```

Os demais parametros (data de referencia, semente, volumes, perfis de acesso)
ficam centralizados em [src/config.py](src/config.py).

## Estrutura

```
tcc-conversational-analytics/
  GUIA_DESENVOLVIMENTO.md            # orientacoes de desenvolvimento
  README.md
  requirements.txt
  run_all.py           # orquestrador: oracle (autoteste) e llm (motor local ou API)
  src/
    config.py          # parametros centrais (SIM_TODAY, SEED, volumes, perfis, LLM)
    data_gen.py        # geracao sintetica -> Bronze (a implementar)
    pipeline.py        # Bronze -> Silver -> Gold (a implementar)
    governance.py      # guardrails, validacao de saida e trilha de auditoria
    nl2sql.py          # motores Text-to-SQL (local, API) + oraculo; variantes de prompt
    questions.py       # conjunto de avaliacao (18 perguntas, SQL de referencia)
    evaluate.py        # execution match, desfechos de governanca e Soft F1
    matriz.py          # matriz de celulas de prompt (Etapa D)
    adversarial.py     # conjunto adversarial e abstencao (Etapa E)
  data/                # lakehouse.duckdb (Bronze/Silver/Gold) e gold_isolada.duckdb (so Gold), nao versionados
  results/             # saidas de avaliacao e log de auditoria (nao versionado)
```

## Estado atual

Pipeline, governanca, motores e harness implementados; fase de conclusao do
TCC em andamento (ver [docs/tcc/etapas/README.md](docs/tcc/etapas/README.md)).

## Verificacao rapida

```bash
python -m src.config   # imprime os parametros e roda o autoteste
```
