"""Matriz de prompt da Etapa D: roda as celulas pre-registradas e consolida.

Cada celula de `config.CELULAS` e uma `VariantePrompt` (DA-NL2SQL-004). Para
cada uma, o harness roda k vezes (`evaluate.avaliar_repetido`) com o motor
pedido, sobre o mesmo conjunto e a mesma trilha de auditoria, e este modulo:

- grava um relatorio por celula (`avaliacao_<motor>_<celula>.json`, com SQL,
  resultado, hash, desfechos e telemetria de cada pergunta em cada execucao);
- consolida a matriz (`matriz_<motor>.json` e `.md`): estrito com IC de
  Wilson, set match, Soft F1, desfechos nos dois niveis, TARa@k, tokens de
  entrada e duracao, lado a lado, mais a comparacao pareada por pergunta de
  cada celula com a base (C1);
- exporta as SQL geradas por celula e pergunta (`sql_geradas_<motor>.md`),
  para que qualquer leitor confira os desfechos sem rodar nada (P-03).

A pasta de saida e versionada como artefato da execucao (docs/tcc/anexos/) e o
commit que gerou os numeros recebe tag git. Com o motor oraculo, o modulo so
exercita a tubulacao (autoteste, RNC-002): nenhum numero e desempenho.

Uso isolado:
    python -m src.matriz            # autoteste com o oraculo, em pasta temporaria
    python run_all.py llm --motor local --matriz    # execucao real
"""

import json
import sys
from pathlib import Path

from src import config, evaluate, governance, nl2sql

CELULA_BASE = "C1"


def _duracao_s(inicio_iso, fim_iso):
    import datetime

    a = datetime.datetime.fromisoformat(inicio_iso)
    b = datetime.datetime.fromisoformat(fim_iso)
    return round((b - a).total_seconds())


def _media_desfechos(execucoes, nivel):
    """Media, por desfecho, das contagens nas k execucoes."""
    k = len(execucoes)
    return {
        d: round(sum(m["AVAL-002_desfechos"][nivel][d] for m in execucoes) / k, 2)
        for d in evaluate.DESFECHOS
    }


def _linha_celula(relatorio, papel):
    a = relatorio["agregado"]
    execucoes = relatorio["execucoes"]
    acertos_medio = sum(m["corretas"] for m in execucoes) / len(execucoes)
    return {
        "celula": a["celula"],
        "papel": papel,
        "variante": a["variante"],
        "repeticoes": a["repeticoes"],
        "n_responder": a["n_responder"],
        "estrito": a["AVAL-001_estrito"],
        "acertos_medio": round(acertos_medio, 2),
        # IC de Wilson sobre a media de acertos (n = perguntas a responder).
        "ic95_wilson": evaluate.intervalo_wilson(round(acertos_medio), a["n_responder"]),
        "conteudo": a["match_conteudo_relaxado"],
        "soft_f1": a["soft_f1_medio"],
        "safe_ex_sistema": a["safe_ex_sistema"],
        "violation_modelo": a["violation_modelo"],
        "over_refusal_sistema": a["over_refusal_sistema"],
        "desfechos_modelo": _media_desfechos(execucoes, "modelo"),
        "desfechos_sistema": _media_desfechos(execucoes, "sistema"),
        "TARa": a["TARa"],
        "tokens_entrada_medio": a["tokens_entrada_medio"],
        "inicio_utc": a["inicio_utc"],
        "fim_utc": a["fim_utc"],
        "duracao_s": _duracao_s(a["inicio_utc"], a["fim_utc"]),
    }


def _acertos_por_pergunta(relatorio):
    """id -> numero de execucoes em que a pergunta acertou no estrito."""
    return {s["id"]: int(s["estrito"].split("/")[0]) for s in relatorio["estabilidade"]}


def resumir(relatorios, trilha=None):
    """Consolida os relatorios por celula em um unico resumo da matriz."""
    papeis = {c["celula"]: c["papel"] for c in config.CELULAS}
    linhas = [_linha_celula(r, papeis.get(r["agregado"]["celula"], "")) for r in relatorios]
    por_celula = {r["agregado"]["celula"]: r for r in relatorios}
    a0 = relatorios[0]["agregado"]

    # Comparacao pareada por pergunta com a base: o que cada celula muda.
    por_pergunta = {}
    for celula, r in por_celula.items():
        for s in r["estabilidade"]:
            por_pergunta.setdefault(s["id"], {})[celula] = s["estrito"]
    pareado = {}
    if CELULA_BASE in por_celula:
        base = _acertos_por_pergunta(por_celula[CELULA_BASE])
        for celula, r in por_celula.items():
            if celula == CELULA_BASE:
                continue
            outra = _acertos_por_pergunta(r)
            pareado[celula] = {
                "ganha": sorted(q for q in base if outra[q] > base[q]),
                "perde": sorted(q for q in base if outra[q] < base[q]),
            }

    resumo = {
        "motor": a0["motor"],
        "modelo": a0["modelo"],
        "temperatura": a0["temperatura"],
        "repeticoes": a0["repeticoes"],
        "ambiente": a0["ambiente"],
        "inicio_utc": min(l["inicio_utc"] for l in linhas),
        "fim_utc": max(l["fim_utc"] for l in linhas),
        "celula_base": CELULA_BASE,
        "celulas": linhas,
        "por_pergunta": por_pergunta,
        "pareado_com_base": pareado,
    }
    if trilha is not None:
        v = governance.verificar_trilha(trilha)
        resumo["trilha"] = {"arquivo": str(trilha), "integra": v["integra"],
                            "registros": v.get("registros"), "quebra": v.get("quebra")}
    return resumo


def _pct(x):
    return "n/a" if x is None else f"{x * 100:.1f}%"


def _fmt_agregado(e):
    return f"{_pct(e['media'])} (dp {e['desvio'] * 100:.1f})"


def renderizar_markdown(resumo):
    """Tabela da matriz e comparacao pareada, em Markdown."""
    k = resumo["repeticoes"]
    out = [
        f"# Matriz de prompt: motor {resumo['motor']}, modelo {resumo['modelo']}",
        "",
        f"Temperatura {resumo['temperatura']}, k={k} por celula, janela UTC {resumo['inicio_utc']} a "
        f"{resumo['fim_utc']}. Estrito e as taxas sao media (desvio) das k execucoes; o IC de Wilson "
        "e calculado sobre a media de acertos. Desfechos sao contagens medias por execucao.",
        "",
        "| Celula | Papel | Estrito (AVAL-001) | IC95% | Set match | Soft F1 | Safe-EX sist. | "
        "Violation mod. | Over-Refusal sist. | TARa@k | Tokens entrada | Duracao |",
        "|---|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for l in resumo["celulas"]:
        ic = l["ic95_wilson"]
        out.append(
            f"| {l['celula']} | {l['papel']} | {_fmt_agregado(l['estrito'])} | "
            f"[{_pct(ic[0])}; {_pct(ic[1])}] | {_fmt_agregado(l['conteudo'])} | "
            f"{_fmt_agregado(l['soft_f1'])} | {_fmt_agregado(l['safe_ex_sistema'])} | "
            f"{_fmt_agregado(l['violation_modelo'])} | {_fmt_agregado(l['over_refusal_sistema'])} | "
            f"{_pct(l['TARa'])} | {l['tokens_entrada_medio'] if l['tokens_entrada_medio'] is not None else 'n/a'} | "
            f"{l['duracao_s']} s |"
        )
    out += ["", "## Desfechos (Fei et al. 2026), contagem media por execucao", "",
            "| Celula | Nivel | " + " | ".join(evaluate.DESFECHOS) + " |",
            "|---|---|" + "---|" * len(evaluate.DESFECHOS)]
    for l in resumo["celulas"]:
        for nivel in ("modelo", "sistema"):
            d = l[f"desfechos_{nivel}"]
            out.append(f"| {l['celula']} | {nivel} | " + " | ".join(str(d[x]) for x in evaluate.DESFECHOS) + " |")
    out += ["", f"## Comparacao pareada com a base ({resumo['celula_base']}), execution match estrito", ""]
    if resumo["pareado_com_base"]:
        for celula, p in resumo["pareado_com_base"].items():
            out.append(f"- {celula}: ganha {', '.join(p['ganha']) or 'nenhuma'}; perde {', '.join(p['perde']) or 'nenhuma'}")
    else:
        out.append(f"- (celula base {resumo['celula_base']} nao esta na matriz)")
    celulas = [l["celula"] for l in resumo["celulas"]]
    out += ["", "## Acertos por pergunta (estrito, acertos/k)", "",
            "| Pergunta | " + " | ".join(celulas) + " |", "|---|" + "---|" * len(celulas)]
    for q, por in resumo["por_pergunta"].items():
        out.append(f"| {q} | " + " | ".join(por.get(c, "") for c in celulas) + " |")
    if "trilha" in resumo:
        t = resumo["trilha"]
        out += ["", f"Trilha de auditoria: {t['registros']} registros, cadeia "
                    f"{'integra' if t['integra'] else 'QUEBRADA no registro ' + str(t['quebra'])}."]
    amb = resumo.get("ambiente") or {}
    if amb:
        out += ["", "Ambiente: " + ", ".join(f"{k2}={v}" for k2, v in amb.items()) + "."]
    return "\n".join(out) + "\n"


def exportar_sql_markdown(relatorios):
    """Lista, por celula e pergunta, a SQL gerada em cada execucao e o desfecho.

    Quando as k execucoes geraram a mesma SQL, ela aparece uma vez. Nada aqui
    contem chave ou dado pessoal: sao consultas sobre a Gold minimizada.
    """
    out = ["# SQL geradas por celula e pergunta", ""]
    for r in relatorios:
        a = r["agregado"]
        out += [f"## Celula {a['celula']} ({a['motor']}, {a['modelo']}, k={a['repeticoes']})", ""]
        n = len(r["detalhes_por_execucao"][0])
        for i in range(n):
            por_exec = [ex[i] for ex in r["detalhes_por_execucao"]]
            d0 = por_exec[0]
            out.append(f"### {d0['id']} [{d0['tipo']}, {d0['perfil']}]")
            sqls = {d["sql"] for d in por_exec}
            if len(sqls) == 1:
                d = d0
                extra = f" ({d['controle']}: {d['motivo']})" if d["controle"] else (
                    f" ({d['motivo']})" if d["motivo"] else "")
                out += [f"Identica nas {len(por_exec)} execucoes; evento `{d['evento']}`, "
                        f"modelo={d['desfecho_modelo']}, sistema={d['desfecho_sistema']}{extra}",
                        "", "```sql", d["sql"] or "(vazia)", "```", ""]
            else:
                for j, d in enumerate(por_exec, 1):
                    extra = f" ({d['controle']}: {d['motivo']})" if d["controle"] else (
                        f" ({d['motivo']})" if d["motivo"] else "")
                    out += [f"Execucao {j}: evento `{d['evento']}`, modelo={d['desfecho_modelo']}, "
                            f"sistema={d['desfecho_sistema']}{extra}",
                            "", "```sql", d["sql"] or "(vazia)", "```", ""]
    return "\n".join(out)


def imprimir_matriz(resumo):
    print(f"matriz ({resumo['motor']}, modelo {resumo['modelo']}, k={resumo['repeticoes']}): "
          f"{len(resumo['celulas'])} celulas; janela UTC {resumo['inicio_utc']} a {resumo['fim_utc']}")
    print(f"  {'celula':7}{'estrito':>22}{'set match':>12}{'Soft F1':>10}{'Viol. mod.':>12}"
          f"{'Over-Ref. sist.':>17}{'TARa':>8}{'tokens':>9}{'dur.':>7}")
    for l in resumo["celulas"]:
        tok = l["tokens_entrada_medio"] if l["tokens_entrada_medio"] is not None else "n/a"
        print(f"  {l['celula']:7}{_fmt_agregado(l['estrito']):>22}{_pct(l['conteudo']['media']):>12}"
              f"{_pct(l['soft_f1']['media']):>10}{_pct(l['violation_modelo']['media']):>12}"
              f"{_pct(l['over_refusal_sistema']['media']):>17}{_pct(l['TARa']):>8}{str(tok):>9}{l['duracao_s']:>6}s")
    for celula, p in resumo["pareado_com_base"].items():
        print(f"  {celula} vs {resumo['celula_base']}: ganha {', '.join(p['ganha']) or 'nenhuma'}; "
              f"perde {', '.join(p['perde']) or 'nenhuma'}")
    if "trilha" in resumo:
        t = resumo["trilha"]
        print(f"  trilha: {t['registros']} registros, {'integra' if t['integra'] else 'QUEBRADA'}")


def rodar_matriz(motor_nome, celulas=None, repeticoes=None, saida=None, conjunto=None):
    """Roda as celulas com o motor pedido e grava relatorios, matriz e SQL em `saida`.

    A trilha de auditoria da execucao fica na propria pasta (`auditoria.log`),
    de modo que o artefato versionado carrega a cadeia de hashes que o cobre.
    """
    celulas = list(celulas or [c["celula"] for c in config.CELULAS])
    repeticoes = repeticoes or config.REPETICOES_MATRIZ
    saida = Path(saida) if saida else config.MATRIZ_DIR
    saida.mkdir(parents=True, exist_ok=True)
    trilha = saida / "auditoria.log"

    relatorios = []
    for celula in celulas:
        motor = nl2sql.obter_motor(motor_nome, celula)
        print(f"== celula {celula} ({motor.nome}, {motor.modelo}), k={repeticoes} ==")
        r = evaluate.avaliar_repetido(motor, repeticoes, conjunto, trilha)
        evaluate.imprimir_resumo_repetido(r)
        caminho = evaluate.salvar_relatorio(r, pasta=saida)
        print(f"relatorio: {caminho}")
        relatorios.append(r)

    resumo = resumir(relatorios, trilha)
    nome = resumo["motor"]
    (saida / f"matriz_{nome}.json").write_text(
        json.dumps(resumo, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    (saida / f"matriz_{nome}.md").write_text(renderizar_markdown(resumo), encoding="utf-8")
    (saida / f"sql_geradas_{nome}.md").write_text(exportar_sql_markdown(relatorios), encoding="utf-8")
    imprimir_matriz(resumo)
    print(f"matriz e SQL geradas em {saida}")
    return resumo


def _autoteste():
    """A tubulacao da matriz roda com o oraculo em pasta temporaria (RNC-002)."""
    import tempfile

    from src import data_gen, pipeline

    if not (config.DB_PATH.exists() and config.GOLD_DB_PATH.exists()):
        data_gen.construir()
        pipeline.construir()

    with tempfile.TemporaryDirectory() as tmp:
        saida = Path(tmp) / "matriz"
        resumo = rodar_matriz("oracle", celulas=("C0", CELULA_BASE, "C3"), repeticoes=2, saida=saida)
        assert [l["celula"] for l in resumo["celulas"]] == ["C0", "C1", "C3"]
        for l in resumo["celulas"]:
            assert l["estrito"]["media"] == 1.0 and l["TARa"] == 1.0 and l["ic95_wilson"][1] == 1.0
            assert l["desfechos_sistema"]["Correct"] == 18.0 and l["repeticoes"] == 2
        assert resumo["pareado_com_base"] == {"C0": {"ganha": [], "perde": []},
                                              "C3": {"ganha": [], "perde": []}}
        assert resumo["por_pergunta"]["Q12"] == {"C0": "2/2", "C1": "2/2", "C3": "2/2"}
        assert resumo["trilha"]["integra"] and resumo["trilha"]["registros"] == 3 * 2 * 18 * 2
        for nome in ("avaliacao_oracle_C0.json", "avaliacao_oracle_C1.json", "avaliacao_oracle_C3.json",
                     "matriz_oracle.json", "matriz_oracle.md", "sql_geradas_oracle.md", "auditoria.log"):
            assert (saida / nome).exists(), nome
        md = (saida / "matriz_oracle.md").read_text(encoding="utf-8")
        assert "| C3 |" in md and "Acertos por pergunta" in md
        sqls = (saida / "sql_geradas_oracle.md").read_text(encoding="utf-8")
        assert "### Q01 [status_atual, enfermagem]" in sqls and "Identica nas 2 execucoes" in sqls
        # O relatorio por celula guarda a variante que gerou o prompt.
        rel = json.loads((saida / "avaliacao_oracle_C3.json").read_text(encoding="utf-8"))
        assert rel["agregado"]["variante"]["schema_por_perfil"] is True

    print("matriz: autoteste OK")
    print("  3 celulas x k=2 com o oraculo: relatorios, matriz (json e md), SQL geradas e trilha integra")


if __name__ == "__main__":
    _autoteste()
