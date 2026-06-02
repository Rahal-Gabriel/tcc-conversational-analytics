# Conversational Analytics em saude (prototipo de TCC)

Prototipo funcional de uma arquitetura de referencia para consulta em linguagem
natural sobre dados clinicos, com governanca integrada e aderente a LGPD, as
normas da ANVISA e as diretrizes da ANPD. O dominio de avaliacao e a **ocupacao
de leitos hospitalares**, e toda a pesquisa usa dados **100% sinteticos**.

Orientacoes detalhadas de desenvolvimento estao em [GUIA_DESENVOLVIMENTO.md](GUIA_DESENVOLVIMENTO.md).

## Arquitetura em quatro camadas

1. **Pipeline Lakehouse** (DuckDB local): Bronze (bruto, com PII proposital),
   Silver (limpa e anonimizada) e Gold (metricas, unica camada exposta ao LLM).
2. **Governanca de entrada**: autenticacao por perfil, registro de toda
   pergunta e verificacao de conformidade antes de qualquer execucao.
3. **Motor Text-to-SQL**: traduz a pergunta em portugues para uma SQL somente
   leitura sobre a Gold, via LLM, restrita por guardrails.
4. **Validacao de saida**: aterramento anti-alucinacao, filtro de dados
   sensiveis e auditoria das respostas.

## Requisitos

- Python 3.12
- Dependencias em [requirements.txt](requirements.txt) (faker, duckdb)

## Instalacao

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

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
    governance.py      # guardrails e auditoria (a implementar)
    nl2sql.py          # motor Text-to-SQL + oraculo (a implementar)
    questions.py       # conjunto de avaliacao (a implementar)
    evaluate.py        # execution-match e indicadores (a implementar)
  data/                # banco DuckDB gerado (nao versionado)
  results/             # saidas de avaliacao e log de auditoria (nao versionado)
```

## Estado atual

Etapa inicial: estrutura de pastas e `src/config.py`. Os demais modulos ainda
nao foram implementados.

## Verificacao rapida

```bash
python -m src.config   # imprime os parametros e roda o autoteste
```
