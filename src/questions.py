"""Conjunto de avaliacao: pares (pergunta em portugues, SQL de referencia).

Cada item liga uma pergunta operacional do dominio de ocupacao de leitos a uma
SQL somente leitura sobre a camada Gold, ja no escopo de um perfil de acesso.

A SQL de referencia (`sql_ref`) e o oraculo da avaliacao (DA-NL2SQL-001): com
ela, o execution match deve dar 100% (autoteste da tubulacao). Ela nunca e
apresentada como desempenho do modelo (RNC-002). Toda `sql_ref` e determinista
(RNC-003): quando a pergunta menciona "hoje", a data e ancorada em SIM_TODAY
como literal, nunca no relogio do sistema.

Tipo de pergunta (DA-AVAL-003). A banca simulada (rodada 01, P-02) mostrou que
os rotulos originais nao tinham criterio explicito e nao correspondiam ao
conteudo de tres perguntas. O tipo agora e definido pela SQL de referencia, e o
autoteste confere o rotulo declarado contra a regra:

- `status_atual`: valor do hospital hoje, sem recorte por unidade (snapshot em
  `gold.leitos_status`, ou `gold.ocupacao_diaria` restrita a SIM_TODAY);
- `metrica_unidade`: recorte ou ranking por unidade hoje (`gold.ocupacao_unidade`);
- `serie_historica`: janela de mais de um dia em `gold.ocupacao_diaria`;
- `internacoes`: medidas sobre `gold.internacoes` (contagens e permanencia; o
  rotulo anterior, "faixa_etaria", descrevia so metade das perguntas).

Desfecho esperado (`esperado`, Etapa C): `responder` quando a pergunta e
legitima e cabe no perfil; `recusar` quando a resposta correta do sistema e nao
responder (conjunto adversarial, Etapa E). Serve a classificacao nos desfechos
de Fei et al. (2026) em `src/evaluate.py`.

Uso isolado:
    python -m src.questions
"""

import re
from collections import namedtuple

from src import config

# Um item do conjunto de avaliacao. `id` e estavel; `tipo` classifica a pergunta
# (regra em tipo_por_sql); `perfil` define o escopo Gold autorizado
# (config.PERFIS); `sql_ref` e a consulta de referencia sobre a Gold; `esperado`
# diz se o sistema deve responder ou recusar.
Pergunta = namedtuple(
    "Pergunta", "id texto perfil tipo sql_ref esperado", defaults=("responder",)
)

# Data de referencia da simulacao, usada como literal nas consultas que falam de
# "hoje". Mantida igual a config.SIM_TODAY para preservar o determinismo.
_HOJE = config.SIM_TODAY.isoformat()

# Tipos de pergunta cobertos (criterio no docstring do modulo).
TIPOS = ("status_atual", "metrica_unidade", "serie_historica", "internacoes")

# Desfechos esperados possiveis.
ESPERADOS = ("responder", "recusar")

_RE_TABELA_GOLD = re.compile(r"\bgold\s*\.\s*(\w+)", re.IGNORECASE)
_RE_SO_HOJE = re.compile(rf"\bdata\s*=\s*DATE\s*'{_HOJE}'", re.IGNORECASE)


def tipo_por_sql(sql_ref):
    """Deriva o tipo da pergunta a partir da SQL de referencia (DA-AVAL-003).

    A regra e mecanica para ser verificavel: a tabela Gold consultada define o
    tipo, e `gold.ocupacao_diaria` so e serie historica quando a janela passa de
    um dia (filtro diferente de `data = SIM_TODAY`).
    """
    tabelas = {f"gold.{t.lower()}" for t in _RE_TABELA_GOLD.findall(sql_ref)}
    if "gold.internacoes" in tabelas:
        return "internacoes"
    if "gold.ocupacao_diaria" in tabelas:
        return "status_atual" if _RE_SO_HOJE.search(sql_ref) else "serie_historica"
    if "gold.ocupacao_unidade" in tabelas:
        return "metrica_unidade"
    return "status_atual"


CONJUNTO = (
    # --- Status atual (snapshot de leitos em SIM_TODAY) ---
    Pergunta(
        "Q01",
        "Quantos leitos estao ocupados no hospital hoje?",
        "enfermagem",
        "status_atual",
        "SELECT COUNT(*) AS ocupados FROM gold.leitos_status WHERE situacao = 'ocupado'",
    ),
    Pergunta(
        "Q02",
        "Quantos leitos de UTI estao livres hoje?",
        "enfermagem",
        "status_atual",
        "SELECT COUNT(*) AS livres FROM gold.leitos_status "
        "WHERE tipo = 'UTI' AND situacao = 'livre'",
    ),
    Pergunta(
        "Q03",
        "Quantos leitos existem em cada situacao hoje?",
        "enfermagem",
        "status_atual",
        "SELECT situacao, COUNT(*) AS total FROM gold.leitos_status "
        "GROUP BY situacao ORDER BY situacao",
    ),
    # --- Metrica por unidade ---
    Pergunta(
        "Q04",
        "Qual a taxa de ocupacao de cada unidade hoje?",
        "gestor",
        "metrica_unidade",
        "SELECT unidade, taxa_ocupacao FROM gold.ocupacao_unidade ORDER BY unidade",
    ),
    Pergunta(
        "Q05",
        "Qual unidade tem a maior taxa de ocupacao hoje?",
        "administrativo",
        "metrica_unidade",
        "SELECT unidade, taxa_ocupacao FROM gold.ocupacao_unidade "
        "ORDER BY taxa_ocupacao DESC, unidade LIMIT 1",
    ),
    Pergunta(
        "Q06",
        "Quantos leitos ocupados ha na unidade de Cardiologia hoje?",
        "gestor",
        "metrica_unidade",
        "SELECT ocupados FROM gold.ocupacao_unidade WHERE especialidade = 'Cardiologia'",
    ),
    # --- Status atual do hospital lido da serie diaria (so o dia de hoje) ---
    # Re-rotulada de serie_historica para status_atual na Etapa C (P-02): a
    # pergunta e um valor de hoje; a tabela consultada nao muda o que se pergunta.
    Pergunta(
        "Q07",
        "Qual a taxa de ocupacao do hospital hoje?",
        "administrativo",
        "status_atual",
        f"SELECT taxa_ocupacao FROM gold.ocupacao_diaria WHERE data = DATE '{_HOJE}'",
    ),
    # --- Serie historica ---
    Pergunta(
        "Q08",
        "Qual foi a taxa de ocupacao media diaria nos ultimos 7 dias ate hoje?",
        "administrativo",
        "serie_historica",
        "SELECT AVG(taxa_ocupacao) AS media FROM gold.ocupacao_diaria "
        f"WHERE data BETWEEN DATE '{_HOJE}' - INTERVAL 6 DAY AND DATE '{_HOJE}'",
    ),
    # --- Internacoes (contagens por faixa etaria e tempo de permanencia) ---
    Pergunta(
        "Q09",
        "Quantas internacoes ativas ha por faixa etaria?",
        "gestor",
        "internacoes",
        "SELECT faixa_etaria, COUNT(*) AS total FROM gold.internacoes "
        "WHERE ativa GROUP BY faixa_etaria ORDER BY faixa_etaria",
    ),
    # Re-rotulada de faixa_etaria para internacoes na Etapa C (P-02): nao envolve
    # faixa etaria.
    Pergunta(
        "Q10",
        "Qual o tempo medio de permanencia das internacoes ja encerradas?",
        "gestor",
        "internacoes",
        "SELECT AVG(tempo_permanencia) AS media FROM gold.internacoes WHERE NOT ativa",
    ),
    # --- Ampliacao do conjunto (Q11 a Q18) ---
    # Status atual
    Pergunta(
        "Q11",
        "Quantos leitos estao bloqueados hoje?",
        "enfermagem",
        "status_atual",
        "SELECT COUNT(*) AS bloqueados FROM gold.leitos_status WHERE situacao = 'bloqueado'",
    ),
    Pergunta(
        "Q12",
        "Quantos leitos de enfermaria existem no hospital hoje?",
        "enfermagem",
        "status_atual",
        "SELECT COUNT(*) AS total FROM gold.leitos_status WHERE tipo = 'Enfermaria'",
    ),
    # Metrica por unidade
    Pergunta(
        "Q13",
        "Quantos leitos livres ha em cada unidade hoje?",
        "gestor",
        "metrica_unidade",
        "SELECT unidade, livres FROM gold.ocupacao_unidade ORDER BY unidade",
    ),
    Pergunta(
        "Q14",
        "Quais unidades estao com taxa de ocupacao acima de 80% hoje?",
        "administrativo",
        "metrica_unidade",
        "SELECT unidade, taxa_ocupacao FROM gold.ocupacao_unidade "
        "WHERE taxa_ocupacao > 80 ORDER BY unidade",
    ),
    # Serie historica
    Pergunta(
        "Q15",
        "Qual foi a maior taxa de ocupacao diaria registrada no historico?",
        "administrativo",
        "serie_historica",
        "SELECT MAX(taxa_ocupacao) AS maior FROM gold.ocupacao_diaria",
    ),
    Pergunta(
        "Q16",
        "Em quantos dias a taxa de ocupacao diaria passou de 85%?",
        "administrativo",
        "serie_historica",
        "SELECT COUNT(*) AS dias FROM gold.ocupacao_diaria WHERE taxa_ocupacao > 85",
    ),
    # Internacoes
    Pergunta(
        "Q17",
        "Quantas internacoes ja encerradas ha por faixa etaria?",
        "gestor",
        "internacoes",
        "SELECT faixa_etaria, COUNT(*) AS total FROM gold.internacoes "
        "WHERE NOT ativa GROUP BY faixa_etaria ORDER BY faixa_etaria",
    ),
    # Re-rotulada de faixa_etaria para internacoes na Etapa C (P-02): agrupa por
    # tipo de leito, nao por faixa etaria.
    Pergunta(
        "Q18",
        "Qual o tempo medio de permanencia por tipo de leito nas internacoes encerradas?",
        "gestor",
        "internacoes",
        "SELECT tipo, AVG(tempo_permanencia) AS media FROM gold.internacoes "
        "WHERE NOT ativa GROUP BY tipo ORDER BY tipo",
    ),
)


def por_id(id_pergunta):
    """Retorna a Pergunta de um dado id, ou None se nao existir."""
    for p in CONJUNTO:
        if p.id == id_pergunta:
            return p
    return None


def _autoteste():
    """Valida a coerencia do conjunto e que toda SQL de referencia e legitima."""
    from src import governance

    # ids unicos.
    ids = [p.id for p in CONJUNTO]
    assert len(ids) == len(set(ids)), f"ids repetidos no conjunto: {ids}"

    # todo tipo declarado e conhecido, todos os tipos sao exercitados, e o rotulo
    # declarado bate com a regra derivada da SQL de referencia (DA-AVAL-003).
    tipos_usados = {p.tipo for p in CONJUNTO}
    assert tipos_usados <= set(TIPOS), f"tipo desconhecido: {tipos_usados - set(TIPOS)}"
    assert tipos_usados == set(TIPOS), f"tipo sem pergunta: {set(TIPOS) - tipos_usados}"
    for p in CONJUNTO:
        derivado = tipo_por_sql(p.sql_ref)
        assert p.tipo == derivado, f"{p.id}: rotulo {p.tipo!r} diverge da regra ({derivado!r})"
        assert p.esperado in ESPERADOS, f"{p.id}: esperado desconhecido {p.esperado!r}"

    # toda SQL de referencia precisa passar pelos guardrails de entrada no escopo
    # do proprio perfil: se a referencia nao passa, a tubulacao esta errada.
    for p in CONJUNTO:
        if p.esperado != "responder":
            continue
        r = governance.validar_sql(p.sql_ref, p.perfil)
        assert r.aprovado, f"sql_ref de {p.id} bloqueada [{p.perfil}]: {r.controle}: {r.motivo}"

    print("questions: autoteste OK")
    print(f"  {len(CONJUNTO)} perguntas, {len(tipos_usados)} tipos cobertos (rotulo conferido pela SQL)")
    for tipo in TIPOS:
        itens = [p for p in CONJUNTO if p.tipo == tipo]
        perfis = sorted({p.perfil for p in itens})
        print(f"    {tipo}: {len(itens)}  (perfis: {', '.join(perfis)})")


if __name__ == "__main__":
    _autoteste()
