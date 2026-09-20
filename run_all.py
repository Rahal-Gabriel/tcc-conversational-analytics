"""Orquestrador do prototipo: garante os dados e roda a avaliacao.

Dois modos, conforme a Definicao de pronto do GUIA_DESENVOLVIMENTO.md:

    python run_all.py oracle                          # autoteste da tubulacao, sem modelo e sem custo
    python run_all.py llm --motor local --celula C2   # execucao real, uma celula de prompt
    python run_all.py llm --motor local --matriz      # execucao real, todas as celulas (Etapa D)

O modo `oracle` exige 100% de execution match: e o autoteste de que a tubulacao
(geracao -> governanca -> execucao -> avaliacao) esta correta. Esse numero nunca
representa o desempenho do modelo (RNC-002). A CI roda apenas este modo.

O modo `llm` faz a traducao real com o motor escolhido: `local` (modelo aberto
servido pelo Ollama na propria maquina, motor da fase de conclusao) ou `llm`
(API Anthropic, motor dos Resultados Preliminares, exige ANTHROPIC_API_KEY no
ambiente, RNC-004). Ele imprime os indicadores e nunca faz assercao sobre a
acuracia, que e justamente o que se quer medir.
"""

import argparse
import sys

from src import config, data_gen, evaluate, matriz, nl2sql, pipeline


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


def _motor_pronto(motor_nome):
    """Confere o pre-requisito do motor real antes de gerar dados ou chamar nada."""
    if motor_nome == "llm" and not config.ANTHROPIC_API_KEY:
        print(
            "FALHA: ANTHROPIC_API_KEY ausente no ambiente. O motor 'llm' (API) exige chave "
            "valida (RNC-004); use --motor local ou 'python run_all.py oracle' para o autoteste.",
            file=sys.stderr,
        )
        return False
    if motor_nome == "local" and not nl2sql.ollama_disponivel():
        print(
            f"FALHA: o servidor do Ollama nao responde em {config.OLLAMA_ENDPOINT}. Inicie-o "
            f"(app do Ollama ou `ollama serve`) e confira `ollama pull {config.MODELO_LOCAL}`.",
            file=sys.stderr,
        )
        return False
    return True


def rodar_llm(motor_nome="local", celula=None, repeticoes=1, matriz_completa=False, saida=None):
    """Execucao real com um motor de verdade. Gera os numeros do TCC; nao faz assercao.

    Com `repeticoes > 1`, roda a avaliacao k vezes e reporta media, desvio e a
    estabilidade por pergunta, para separar erro sistematico de variancia de uma
    rodada (mesmo a temperatura zero, um LLM nao e estritamente deterministico).
    Com `matriz_completa`, roda todas as celulas pre-registradas de
    config.CELULAS e consolida a matriz (Etapa D).
    """
    if not _motor_pronto(motor_nome):
        return 1
    garantir_dados()
    if matriz_completa:
        matriz.rodar_matriz(motor_nome, repeticoes=repeticoes, saida=saida)
        modelo = config.MODELO_LOCAL if motor_nome == "local" else config.ANTHROPIC_MODEL
        print(f"numeros gerados pelo motor real '{motor_nome}' (modelo {modelo}); "
              "estes sim representam o desempenho do modelo.")
        return 0
    motor = nl2sql.obter_motor(motor_nome, celula or config.CELULA_PADRAO)
    if repeticoes > 1:
        resultado = evaluate.avaliar_repetido(motor, repeticoes)
        evaluate.imprimir_resumo_repetido(resultado)
    else:
        resultado = evaluate.avaliar(motor)
        evaluate.imprimir_resumo(resultado)
    caminho = evaluate.salvar_relatorio(resultado, pasta=saida)
    print(f"relatorio: {caminho}")
    print(
        f"numeros gerados pelo motor real '{motor.nome}' (modelo {motor.modelo}, celula "
        f"{motor.variante.celula}); estes sim representam o desempenho do modelo."
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
        "--motor",
        choices=("local", "llm"),
        default="local",
        help="modo llm: 'local' (Ollama, padrao) ou 'llm' (API Anthropic, exige chave).",
    )
    celulas = [c["celula"] for c in config.CELULAS]
    parser.add_argument(
        "--celula",
        choices=celulas,
        default=None,
        help=f"celula de prompt pre-registrada (padrao {config.CELULA_PADRAO}); ver config.CELULAS.",
    )
    parser.add_argument(
        "--matriz",
        action="store_true",
        help=f"roda todas as celulas ({', '.join(celulas)}) e consolida a matriz (Etapa D).",
    )
    parser.add_argument(
        "--repeticoes",
        type=int,
        default=None,
        help=f"execucoes por celula (padrao 1; com --matriz, {config.REPETICOES_MATRIZ}).",
    )
    parser.add_argument(
        "--saida",
        default=None,
        help="pasta dos relatorios (padrao results/; com --matriz, results/matriz/).",
    )
    args = parser.parse_args(argv)
    if args.modo == "oracle":
        return rodar_oracle()
    repeticoes = args.repeticoes or (config.REPETICOES_MATRIZ if args.matriz else 1)
    return rodar_llm(
        motor_nome=args.motor, celula=args.celula, repeticoes=max(1, repeticoes),
        matriz_completa=args.matriz, saida=args.saida,
    )


if __name__ == "__main__":
    sys.exit(main())
