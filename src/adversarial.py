"""Etapa E: conjunto adversarial e abstencao. Roda as celulas E0 e E1 e consolida.

As celulas de `config.CELULAS_E` sao a celula vencedora da Etapa D (C3) sem e
com a instrucao de recusa (`VariantePrompt.instrucao_recusa`). Cada uma roda
k vezes sobre o conjunto combinado (`questions.CONJUNTO_COMBINADO`: 18
perguntas legitimas e 25 adversariais) com a mesma trilha, e este modulo:

- grava um relatorio por celula (`avaliacao_<motor>_<celula>.json`), como na
  matriz da Etapa D, agora com ponto de bloqueio, familia e RS por pergunta;
- consolida o resumo (`adversarial_<motor>.json` e `.md`): nas legitimas,
  estrito, Over-Refusal e Safe-EX (o custo da instrucao); nas adversariais,
  Proper Refusal e Violation Rate por familia e por nivel, pontos de bloqueio;
  Reliability Score RS(c) nos dois niveis; a regra contrafactual do resultado
  vazio; TARa@k; e a comparacao pareada E1 contra E0 por pergunta (desfecho do
  sistema);
- exporta as SQL geradas (`sql_geradas_<motor>.md`), reaproveitando a matriz.

Pre-registro (conjunto, hipoteses H5 a H8 e criterio de decisao) em
docs/tcc/etapas/2026-09-20_etapa-E.md, escrito antes da execucao (RNC-002).
Com o oraculo o modulo so exercita a tubulacao: ele responde as legitimas e se
abstem nas adversariais, entao nenhum numero e desempenho.

Uso isolado:
    python -m src.adversarial                          # autoteste com o oraculo
    python run_all.py llm --motor local --adversarial  # execucao real (Etapa E)
"""

import json
from collections import Counter
from pathlib import Path

from src import config, evaluate, governance, matriz, nl2sql, questions

CELULA_BASE = "E0"


def _media(valores):
    return round(sum(valores) / len(valores), 4) if valores else None


def _familias_media(execucoes):
    """Media, por familia, das contagens de cada execucao."""
    out = {}
    for familia in config.FAMILIAS_ADVERSARIAIS:
        itens = [m["por_familia"][familia] for m in execucoes if familia in m["por_familia"]]
        if not itens:
            continue
        out[familia] = {
            "n": itens[0]["n"],
            "proper_refusal_modelo": _media([f["proper_refusal_modelo"] for f in itens]),
            "proper_refusal_sistema": _media([f["proper_refusal_sistema"] for f in itens]),
            "violation_modelo": _media([f["violation_modelo"] for f in itens]),
            "violation_sistema": _media([f["violation_sistema"] for f in itens]),
            "pontos_bloqueio": dict(sum((Counter(f["pontos_bloqueio"]) for f in itens), Counter())),
        }
    return out


def _linha_celula(relatorio, papel):
    a = relatorio["agregado"]
    execucoes = relatorio["execucoes"]
    cv = [m["contrafactual_vazio"] for m in execucoes]
    return {
        "celula": a["celula"],
        "papel": papel,
        "variante": a["variante"],
        "repeticoes": a["repeticoes"],
        "total": a["total"],
        "n_responder": a["n_responder"],
        "n_recusar": a["n_recusar"],
        # legitimas: o custo da instrucao de recusa
        "estrito": a["AVAL-001_estrito"],
        "safe_ex_sistema": a["safe_ex_sistema"],
        "over_refusal_sistema": a["over_refusal_sistema"],
        # adversariais: a metade que faltava do AVAL-002
        "proper_refusal_modelo": a["proper_refusal_modelo"],
        "proper_refusal_sistema": a["proper_refusal_sistema"],
        "violation_modelo": a["violation_modelo"],
        "violation_sistema": a["violation_sistema"],
        "RS": a["RS"],
        "por_familia": _familias_media(execucoes),
        "pontos_bloqueio": dict(sum((Counter(m["pontos_bloqueio"]) for m in execucoes), Counter())),
        "contrafactual_vazio": {
            "perguntas_que_mudam": sorted({q for c in cv for q in c["perguntas_que_mudam"]}),
            "over_refusal_sistema": _media([c["indicadores_sistema"]["over_refusal_rate"] or 0.0 for c in cv]),
            "proper_refusal_sistema": _media([c["indicadores_sistema"]["proper_refusal_rate"] or 0.0 for c in cv]),
            "RS_sistema": {k: _media([c["RS_sistema"][k] for c in cv]) for k in cv[0]["RS_sistema"]},
        },
        "TARa": a["TARa"],
        "tokens_entrada_medio": a["tokens_entrada_medio"],
        "inicio_utc": a["inicio_utc"],
        "fim_utc": a["fim_utc"],
    }


def _desfechos_sistema(relatorio):
    """Desfecho do sistema por pergunta, na primeira execucao (k identicas quando TARa=1)."""
    return {d["id"]: d["desfecho_sistema"] for d in relatorio["detalhes_por_execucao"][0]}


def resumir(relatorios, trilha=None):
    """Consolida os relatorios das celulas E0 e E1 em um unico resumo."""
    papeis = {c["celula"]: c["papel"] for c in config.CELULAS_E}
    linhas = [_linha_celula(r, papeis.get(r["agregado"]["celula"], "")) for r in relatorios]
    por_celula = {r["agregado"]["celula"]: r for r in relatorios}
    a0 = relatorios[0]["agregado"]

    # Pareado por pergunta: desfecho do sistema em cada celula e o que muda
    # em relacao a base (E0).
    por_pergunta = {}
    for celula, r in por_celula.items():
        for q, desfecho in _desfechos_sistema(r).items():
            por_pergunta.setdefault(q, {})[celula] = desfecho
    pareado = {}
    if CELULA_BASE in por_celula:
        base = _desfechos_sistema(por_celula[CELULA_BASE])
        for celula, r in por_celula.items():
            if celula == CELULA_BASE:
                continue
            outra = _desfechos_sistema(r)
            pareado[celula] = {
                q: {"de": base[q], "para": outra[q]} for q in base if outra.get(q) != base[q]
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


def _fmt(e):
    return f"{_pct(e['media'])} (dp {e['desvio'] * 100:.1f})"


def renderizar_markdown(resumo):
    """Tabelas do resumo da Etapa E em Markdown."""
    k = resumo["repeticoes"]
    out = [
        f"# Conjunto adversarial e abstencao: motor {resumo['motor']}, modelo {resumo['modelo']}",
        "",
        f"Temperatura {resumo['temperatura']}, k={k} por celula, janela UTC {resumo['inicio_utc']} a "
        f"{resumo['fim_utc']}. Conjunto combinado: {resumo['celulas'][0]['n_responder']} legitimas e "
        f"{resumo['celulas'][0]['n_recusar']} adversariais. Taxas sao media (desvio) das k execucoes.",
        "",
        "## Legitimas (custo da instrucao) e adversariais (recusa devida)", "",
        "| Celula | Papel | Estrito (legitimas) | Over-Refusal sist. (legitimas) | Proper Refusal mod. | "
        "Proper Refusal sist. | Violation mod. | Violation sist. | TARa@k | Tokens |",
        "|---|---|---|---|---|---|---|---|---|---|",
    ]
    for l in resumo["celulas"]:
        out.append(
            f"| {l['celula']} | {l['papel']} | {_fmt(l['estrito'])} | {_fmt(l['over_refusal_sistema'])} | "
            f"{_fmt(l['proper_refusal_modelo'])} | {_fmt(l['proper_refusal_sistema'])} | "
            f"{_fmt(l['violation_modelo'])} | {_fmt(l['violation_sistema'])} | {_pct(l['TARa'])} | "
            f"{l['tokens_entrada_medio'] if l['tokens_entrada_medio'] is not None else 'n/a'} |"
        )
    out += ["", "## Reliability Score RS(c) (Lee et al. 2024), media das k execucoes", "",
            "| Celula | Nivel | RS(0) | RS(10) | RS(N) |", "|---|---|---|---|---|"]
    for l in resumo["celulas"]:
        for nivel in ("modelo", "sistema"):
            rs = l["RS"][nivel]
            out.append(f"| {l['celula']} | {nivel} | " + " | ".join(str(rs[c]["media"]) for c in ("0", "10", "N")) + " |")
    out += ["", "## Por familia adversarial (contagens medias por execucao; n=5 cada)", "",
            "| Celula | Familia | Proper Refusal mod. | Proper Refusal sist. | Violation mod. | Violation sist. | Pontos de bloqueio |",
            "|---|---|---|---|---|---|---|"]
    for l in resumo["celulas"]:
        for fam, f in l["por_familia"].items():
            pontos = ", ".join(f"{p}={n}" for p, n in sorted(f["pontos_bloqueio"].items()))
            out.append(f"| {l['celula']} | {fam} | {f['proper_refusal_modelo']} | {f['proper_refusal_sistema']} | "
                       f"{f['violation_modelo']} | {f['violation_sistema']} | {pontos} |")
    out += ["", "## Contrafactual da regra do resultado vazio (sistema)", "",
            "| Celula | Perguntas que mudam | Over-Refusal (legitimas) | Proper Refusal (adversariais) | RS(10) |",
            "|---|---|---|---|---|"]
    for l in resumo["celulas"]:
        c = l["contrafactual_vazio"]
        out.append(f"| {l['celula']} | {', '.join(c['perguntas_que_mudam']) or 'nenhuma'} | "
                   f"{_pct(c['over_refusal_sistema'])} | {_pct(c['proper_refusal_sistema'])} | {c['RS_sistema']['10']} |")
    out += ["", f"## Comparacao pareada com a base ({resumo['celula_base']}), desfecho do sistema", ""]
    if resumo["pareado_com_base"]:
        for celula, p in resumo["pareado_com_base"].items():
            if p:
                out.append(f"- {celula}: " + "; ".join(f"{q} {m['de']} para {m['para']}" for q, m in p.items()))
            else:
                out.append(f"- {celula}: nenhuma pergunta muda de desfecho")
    else:
        out.append(f"- (celula base {resumo['celula_base']} nao esta no resumo)")
    celulas = [l["celula"] for l in resumo["celulas"]]
    out += ["", "## Desfecho do sistema por pergunta", "",
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


def imprimir_resumo(resumo):
    print(f"adversarial ({resumo['motor']}, modelo {resumo['modelo']}, k={resumo['repeticoes']}): "
          f"{len(resumo['celulas'])} celulas; janela UTC {resumo['inicio_utc']} a {resumo['fim_utc']}")
    print(f"  {'celula':7}{'estrito leg.':>20}{'Over-Ref. leg.':>20}{'PR mod.':>18}{'PR sist.':>18}"
          f"{'Viol. sist.':>16}{'RS(10) sist.':>14}{'TARa':>8}")
    for l in resumo["celulas"]:
        print(f"  {l['celula']:7}{_fmt(l['estrito']):>20}{_fmt(l['over_refusal_sistema']):>20}"
              f"{_fmt(l['proper_refusal_modelo']):>18}{_fmt(l['proper_refusal_sistema']):>18}"
              f"{_fmt(l['violation_sistema']):>16}{str(l['RS']['sistema']['10']['media']):>14}{_pct(l['TARa']):>8}")
        for fam, f in l["por_familia"].items():
            print(f"      {fam:16} PR {f['proper_refusal_modelo']} | {f['proper_refusal_sistema']}  "
                  f"V {f['violation_modelo']} | {f['violation_sistema']}  {f['pontos_bloqueio']}")
    for celula, p in resumo["pareado_com_base"].items():
        print(f"  {celula} vs {resumo['celula_base']}: " + ("; ".join(
            f"{q} {m['de']} para {m['para']}" for q, m in p.items()) or "nenhuma pergunta muda"))
    if "trilha" in resumo:
        t = resumo["trilha"]
        print(f"  trilha: {t['registros']} registros, {'integra' if t['integra'] else 'QUEBRADA'}")


def rodar_adversarial(motor_nome, celulas=None, repeticoes=None, saida=None, conjunto=None):
    """Roda as celulas da Etapa E sobre o conjunto combinado e grava tudo em `saida`."""
    celulas = list(celulas or [c["celula"] for c in config.CELULAS_E])
    repeticoes = repeticoes or config.REPETICOES_MATRIZ
    saida = Path(saida) if saida else config.ADVERSARIAL_DIR
    saida.mkdir(parents=True, exist_ok=True)
    trilha = saida / "auditoria.log"
    conjunto = questions.CONJUNTO_COMBINADO if conjunto is None else conjunto

    relatorios = []
    for celula in celulas:
        motor = nl2sql.obter_motor(motor_nome, celula)
        print(f"== celula {celula} ({motor.nome}, {motor.modelo}), k={repeticoes}, "
              f"{len(conjunto)} perguntas ==")
        r = evaluate.avaliar_repetido(motor, repeticoes, conjunto, trilha)
        evaluate.imprimir_resumo_repetido(r)
        caminho = evaluate.salvar_relatorio(r, pasta=saida)
        print(f"relatorio: {caminho}")
        relatorios.append(r)

    resumo = resumir(relatorios, trilha)
    nome = resumo["motor"]
    (saida / f"adversarial_{nome}.json").write_text(
        json.dumps(resumo, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    (saida / f"adversarial_{nome}.md").write_text(renderizar_markdown(resumo), encoding="utf-8")
    (saida / f"sql_geradas_{nome}.md").write_text(matriz.exportar_sql_markdown(relatorios), encoding="utf-8")
    imprimir_resumo(resumo)
    print(f"resumo e SQL geradas em {saida}")
    return resumo


def _autoteste():
    """A tubulacao da Etapa E roda com o oraculo em pasta temporaria (RNC-002)."""
    import tempfile

    from src import data_gen, pipeline

    if not (config.DB_PATH.exists() and config.GOLD_DB_PATH.exists()):
        data_gen.construir()
        pipeline.construir()

    with tempfile.TemporaryDirectory() as tmp:
        saida = Path(tmp) / "adversarial"
        resumo = rodar_adversarial("oracle", repeticoes=2, saida=saida)
        assert [l["celula"] for l in resumo["celulas"]] == ["E0", "E1"]
        for l in resumo["celulas"]:
            # O oraculo responde as 18 legitimas e se abstem nas 25 adversariais.
            assert l["n_responder"] == 18 and l["n_recusar"] == 25 and l["repeticoes"] == 2
            assert l["estrito"]["media"] == 1.0 and l["over_refusal_sistema"]["media"] == 0.0
            assert l["proper_refusal_modelo"]["media"] == 1.0 and l["proper_refusal_sistema"]["media"] == 1.0
            assert l["violation_modelo"]["media"] == 0.0 and l["violation_sistema"]["media"] == 0.0
            assert all(l["RS"][n][c]["media"] == 100.0 for n in ("modelo", "sistema") for c in ("0", "10", "N"))
            assert set(l["por_familia"]) == set(config.FAMILIAS_ADVERSARIAIS)
            # X03 e X05 sao barradas por CTRL-GOV-008 antes do motor; o resto o oraculo recusa.
            fam = l["por_familia"]["dado_pessoal"]
            assert fam["pontos_bloqueio"] == {"modelo": 6, "entrada:CTRL-GOV-008": 4}, fam
            assert l["pontos_bloqueio"]["entregue"] == 36 and l["TARa"] == 1.0
            assert l["contrafactual_vazio"]["perguntas_que_mudam"] == []
        assert resumo["pareado_com_base"] == {"E1": {}}
        assert resumo["por_pergunta"]["X21"] == {"E0": "Proper Refusal", "E1": "Proper Refusal"}
        assert resumo["trilha"]["integra"] and resumo["trilha"]["registros"] == 2 * 2 * 43 * 2
        for nome in ("avaliacao_oracle_E0.json", "avaliacao_oracle_E1.json", "adversarial_oracle.json",
                     "adversarial_oracle.md", "sql_geradas_oracle.md", "auditoria.log"):
            assert (saida / nome).exists(), nome
        # A trilha nunca guarda o CPF nem o e-mail ficticios de X03 e X05.
        log = (saida / "auditoria.log").read_text(encoding="utf-8")
        assert "123.456.789-09" not in log and "maria.silva@example.com" not in log
        assert config.MASCARA_PII in log
        md = (saida / "adversarial_oracle.md").read_text(encoding="utf-8")
        assert "| E1 | sistema |" in md and "nao_respondivel" in md
        rel = json.loads((saida / "avaliacao_oracle_E1.json").read_text(encoding="utf-8"))
        assert rel["agregado"]["variante"]["instrucao_recusa"] is True
        assert rel["detalhes_por_execucao"][0][18]["familia"] == "dado_pessoal"

    print("adversarial: autoteste OK")
    print("  2 celulas x k=2 com o oraculo sobre 43 perguntas: relatorios, resumo (json e md), SQL, trilha integra;")
    print("  oraculo recusa as 25 adversariais; CTRL-GOV-008 barra X03 e X05 antes do motor e mascara a trilha")


if __name__ == "__main__":
    _autoteste()
