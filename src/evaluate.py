"""Harness de avaliacao: execution match e indicadores de governanca.

Para cada pergunta do conjunto, o fluxo reproduz a arquitetura completa:
registro da pergunta, geracao da SQL pelo motor escolhido, guardrails de entrada
(Camada 2), execucao em conexao somente leitura (CTRL-GOV-006), validacao de
saida (Camada 4), comparacao com a SQL de referencia e registro da resposta.

Indicadores coletados (metodologia AVAL):
- AVAL-001: acuracia por execution match (fracao de perguntas com resultado
  identico ao da referencia, apos normalizacao).
- AVAL-002: taxa de aprovacao na governanca (fracao das SQL geradas que passam
  pelos guardrails sem bloqueio).
- AVAL-003: completude do log de auditoria (fracao de interacoes com registro
  completo: pergunta, resposta, SQL e evento).

Com o motor oraculo a acuracia deve dar 100% (autoteste da tubulacao); esse
numero nunca representa o desempenho do modelo (RNC-002). Os numeros do TCC so
saem do motor LLM real.

Uso isolado:
    python -m src.evaluate          # motor oraculo (autoteste)
"""

import datetime
import json
from decimal import Decimal

from src import config, governance, nl2sql, questions

# Usuario sintetico que assina as interacoes da avaliacao na trilha de auditoria.
USUARIO_AVAL = "avaliacao"


def _normalizar_celula(valor):
    """Normaliza um valor de celula para comparacao estavel (DA-AVAL-002).

    Floats e decimais sao arredondados; datas viram texto ISO; o resto fica como
    esta. O arredondamento absorve diferencas irrelevantes de precisao entre a
    SQL gerada e a de referencia.
    """
    if isinstance(valor, bool):
        return valor
    if isinstance(valor, Decimal):
        return round(float(valor), 4)
    if isinstance(valor, float):
        return round(valor, 4)
    if isinstance(valor, (datetime.date, datetime.datetime)):
        return valor.isoformat()
    return valor


def normalizar(linhas):
    """Normaliza e ordena um conjunto de linhas, para comparar resultados.

    Cada linha vira uma tupla de celulas normalizadas; a lista e ordenada de forma
    estavel (por representacao textual) para que a ordem das linhas nao influa no
    execution match.
    """
    normalizadas = [tuple(_normalizar_celula(c) for c in linha) for linha in linhas]
    return sorted(normalizadas, key=lambda linha: tuple(str(c) for c in linha))


def executar(con, sql):
    """Executa uma SQL e devolve (colunas, linhas)."""
    cur = con.execute(sql)
    colunas = [d[0] for d in cur.description]
    return colunas, cur.fetchall()


def avaliar(motor_nome):
    """Roda a avaliacao com o motor pedido e devolve metricas e detalhes.

    Abre uma unica conexao somente leitura (CTRL-GOV-006) para todas as consultas.
    Cada pergunta percorre o fluxo completo e e registrada na trilha de auditoria.
    """
    motor = nl2sql.obter_motor(motor_nome)
    con = governance.conectar_somente_leitura()

    total = len(questions.CONJUNTO)
    corretas = geradas = aprovadas_gov = registros_completos = 0
    detalhes = []

    try:
        for p in questions.CONJUNTO:
            governance.registrar_pergunta(USUARIO_AVAL, p.perfil, p.texto)

            sql = None
            evento = None
            aprovado_gov = False
            match = False
            motivo = None

            try:
                sql = motor.gerar_sql(p.texto, p.perfil)
                geradas += 1

                entrada = governance.validar_sql(sql, p.perfil)
                if not entrada.aprovado:
                    evento, motivo = "bloqueado", f"{entrada.controle}: {entrada.motivo}"
                else:
                    colunas, linhas = executar(con, sql)
                    saida = governance.validar_saida(sql, colunas)
                    if not saida.aprovado:
                        evento, motivo = "bloqueado", f"{saida.controle}: {saida.motivo}"
                    else:
                        aprovado_gov = True
                        aprovadas_gov += 1
                        _, linhas_ref = executar(con, p.sql_ref)
                        match = normalizar(linhas) == normalizar(linhas_ref)
                        evento = "correto" if match else "incorreto"
            except Exception as exc:  # SQL invalida, erro de banco, falha de API
                evento, motivo = "erro", f"{type(exc).__name__}: {exc}"

            if match:
                corretas += 1

            governance.registrar_resposta(
                USUARIO_AVAL, p.perfil, p.texto, sql or "", evento
            )
            # Registro completo (AVAL-003): pergunta, resposta, SQL e evento.
            if sql and evento:
                registros_completos += 1

            detalhes.append(
                {
                    "id": p.id,
                    "tipo": p.tipo,
                    "perfil": p.perfil,
                    "evento": evento,
                    "aprovado_governanca": aprovado_gov,
                    "match": match,
                    "motivo": motivo,
                }
            )
    finally:
        con.close()

    metricas = {
        "motor": motor_nome,
        "total": total,
        "AVAL-001_acuracia": round(corretas / total, 4) if total else 0.0,
        "AVAL-002_aprovacao_governanca": round(aprovadas_gov / geradas, 4) if geradas else 0.0,
        "AVAL-003_completude_log": round(registros_completos / total, 4) if total else 0.0,
        "corretas": corretas,
        "geradas": geradas,
        "aprovadas_governanca": aprovadas_gov,
        "registros_completos": registros_completos,
    }
    return {"metricas": metricas, "detalhes": detalhes}


def salvar_relatorio(resultado):
    """Grava o relatorio da avaliacao em results/ e devolve o caminho."""
    motor = resultado["metricas"]["motor"]
    config.RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    caminho = config.RESULTS_DIR / f"avaliacao_{motor}.json"
    with open(caminho, "w", encoding="utf-8") as f:
        json.dump(resultado, f, ensure_ascii=False, indent=2)
    return caminho


def imprimir_resumo(resultado):
    """Imprime um resumo legivel das metricas e dos eventos por pergunta."""
    m = resultado["metricas"]
    print(f"avaliacao ({m['motor']}): {m['total']} perguntas")
    print(f"  AVAL-001 acuracia (execution match): {m['AVAL-001_acuracia'] * 100:.1f}%")
    print(f"  AVAL-002 aprovacao na governanca:    {m['AVAL-002_aprovacao_governanca'] * 100:.1f}%")
    print(f"  AVAL-003 completude do log:          {m['AVAL-003_completude_log'] * 100:.1f}%")
    for d in resultado["detalhes"]:
        extra = f"  ({d['motivo']})" if d["motivo"] else ""
        print(f"    {d['id']} [{d['tipo']}] -> {d['evento']}{extra}")


def _autoteste():
    """Garante os dados e roda a avaliacao com o oraculo: deve dar 100%."""
    from src import data_gen, pipeline

    if not config.DB_PATH.exists():
        data_gen.construir()
        pipeline.construir()

    resultado = avaliar("oracle")
    imprimir_resumo(resultado)
    caminho = salvar_relatorio(resultado)

    acuracia = resultado["metricas"]["AVAL-001_acuracia"]
    assert acuracia == 1.0, (
        f"oraculo deveria dar 100% de execution match, deu {acuracia * 100:.1f}% "
        "(erro na tubulacao, nao no modelo)"
    )
    print(f"evaluate: autoteste OK  (relatorio em {caminho})")


if __name__ == "__main__":
    _autoteste()
