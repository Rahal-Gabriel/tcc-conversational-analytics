"""Orquestrador do prototipo: garante os dados e roda a avaliacao.

Dois modos, conforme a Definicao de pronto do GUIA_DESENVOLVIMENTO.md:

    python run_all.py oracle    # autoteste da tubulacao, sem chave e sem custo
    python run_all.py llm       # execucao real; gera os numeros do TCC

O modo `oracle` exige 100% de execution match: e o autoteste de que a tubulacao
(geracao -> governanca -> execucao -> avaliacao) esta correta. Esse numero nunca
representa o desempenho do modelo (RNC-002). A CI roda apenas este modo.

O modo `llm` exige ANTHROPIC_API_KEY no ambiente (RNC-004), faz a traducao real e
imprime os indicadores; ele nunca faz assercao sobre a acuracia, que e justamente
o que se quer medir.
"""

import argparse
import sys

from src import config, data_gen, evaluate, pipeline


def garantir_dados():
    """Constroi Bronze, Silver, Gold e a Gold isolada se algo ainda nao existe."""
    if config.DB_PATH.exists() and config.GOLD_DB_PATH.exists():
        return
    print("dados ausentes; gerando Bronze, Silver, Gold e Gold isolada...")
    data_gen.construir()
    pipeline.construir()


def rodar_oracle():
    """Autoteste da tubulacao com o motor oraculo. Exige 100% (RNC-002)."""
    garantir_dados()
    resultado = evaluate.avaliar("oracle")
    evaluate.imprimir_resumo(resultado)
    caminho = evaluate.salvar_relatorio(resultado)
    print(f"relatorio: {caminho}")

    m = resultado["metricas"]
    acuracia = m["AVAL-001_acuracia"]
    if acuracia != 1.0:
        print(
            f"FALHA: oraculo deveria dar 100% de execution match, deu "
            f"{acuracia * 100:.1f}%. Isso indica erro na tubulacao, nao no modelo.",
            file=sys.stderr,
        )
        return 1
    if m["AVAL-003_completude_log"] != 1.0 or not m["AVAL-003_trilha_integra"]:
        print(
            "FALHA: trilha de auditoria incompleta ou com cadeia de hashes quebrada "
            f"({config.AUDIT_LOG_PATH}). Isso indica erro na tubulacao, nao no modelo. "
            "Um arquivo gerado antes do encadeamento por hash (Etapa C) tambem cai "
            "aqui: mova-o para outro nome e rode de novo.",
            file=sys.stderr,
        )
        return 1
    print("oraculo: tubulacao consistente (100% de execution match; trilha integra).")
    return 0


def rodar_llm(repeticoes=1):
    """Execucao real com o motor LLM. Gera os numeros do TCC; nao faz assercao.

    Com `repeticoes > 1`, roda a avaliacao k vezes e reporta media, desvio e a
    estabilidade por pergunta, para separar erro sistematico de variancia de uma
    rodada (mesmo a temperatura zero, a API nao e estritamente deterministica).
    """
    if not config.ANTHROPIC_API_KEY:
        print(
            "FALHA: ANTHROPIC_API_KEY ausente no ambiente. O modo llm exige chave "
            "valida (RNC-004); use 'python run_all.py oracle' para o autoteste.",
            file=sys.stderr,
        )
        return 1
    garantir_dados()
    if repeticoes > 1:
        resultado = evaluate.avaliar_repetido("llm", repeticoes)
        evaluate.imprimir_resumo_repetido(resultado)
    else:
        resultado = evaluate.avaliar("llm")
        evaluate.imprimir_resumo(resultado)
    caminho = evaluate.salvar_relatorio(resultado)
    print(f"relatorio: {caminho}")
    print(
        "numeros gerados pelo motor LLM real (modelo "
        f"{config.ANTHROPIC_MODEL}); estes sim representam o desempenho do modelo."
    )
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(description="Orquestrador do prototipo de TCC.")
    parser.add_argument(
        "modo",
        choices=("oracle", "llm"),
        help="oracle: autoteste da tubulacao (CI); llm: execucao real (numeros do TCC).",
    )
    parser.add_argument(
        "--repeticoes",
        type=int,
        default=1,
        help="numero de execucoes do modo llm (>=3 recomendado para media e desvio).",
    )
    args = parser.parse_args(argv)
    if args.modo == "oracle":
        return rodar_oracle()
    return rodar_llm(repeticoes=max(1, args.repeticoes))


if __name__ == "__main__":
    sys.exit(main())
