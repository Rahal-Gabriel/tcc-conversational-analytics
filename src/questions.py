"""Conjunto de avaliacao: pares (pergunta em portugues, SQL de referencia).

Cada item liga uma pergunta operacional do dominio de ocupacao de leitos a uma
SQL somente leitura sobre a camada Gold, ja no escopo de um perfil de acesso. O
conjunto cobre os quatro tipos de pergunta previstos na metodologia (AVAL):
status atual, metrica por unidade, serie historica e internacoes por faixa
etaria.

A SQL de referencia (`sql_ref`) e o oraculo da avaliacao (DA-NL2SQL-001): com
ela, o execution match deve dar 100% (autoteste da tubulacao). Ela nunca e
apresentada como desempenho do modelo (RNC-002). Toda `sql_ref` e determinista
(RNC-003): quando a pergunta menciona "hoje", a data e ancorada em SIM_TODAY
como literal, nunca no relogio do sistema.

Uso isolado:
    python -m src.questions
"""

from collections import namedtuple

from src import config

# Um item do conjunto de avaliacao. `id` e estavel; `tipo` classifica a pergunta
# para a discussao dos resultados; `perfil` define o escopo Gold autorizado
# (config.PERFIS); `sql_ref` e a consulta de referencia sobre a Gold.
Pergunta = namedtuple("Pergunta", "id texto perfil tipo sql_ref")

# Data de referencia da simulacao, usada como literal nas consultas que falam de
# "hoje". Mantida igual a config.SIM_TODAY para preservar o determinismo.
_HOJE = config.SIM_TODAY.isoformat()

# Tipos de pergunta cobertos (espelham a metodologia de avaliacao).
TIPOS = ("status_atual", "metrica_unidade", "serie_historica", "faixa_etaria")

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
    # --- Serie historica ---
    Pergunta(
        "Q07",
        "Qual a taxa de ocupacao do hospital hoje?",
        "administrativo",
        "serie_historica",
        f"SELECT taxa_ocupacao FROM gold.ocupacao_diaria WHERE data = DATE '{_HOJE}'",
    ),
    Pergunta(
        "Q08",
        "Qual foi a taxa de ocupacao media diaria nos ultimos 7 dias ate hoje?",
        "administrativo",
        "serie_historica",
        "SELECT ROUND(AVG(taxa_ocupacao), 1) AS media FROM gold.ocupacao_diaria "
        f"WHERE data BETWEEN DATE '{_HOJE}' - INTERVAL 6 DAY AND DATE '{_HOJE}'",
    ),
    # --- Internacoes por faixa etaria ---
    Pergunta(
        "Q09",
        "Quantas internacoes ativas ha por faixa etaria?",
        "gestor",
        "faixa_etaria",
        "SELECT faixa_etaria, COUNT(*) AS total FROM gold.internacoes "
        "WHERE ativa GROUP BY faixa_etaria ORDER BY faixa_etaria",
    ),
    Pergunta(
        "Q10",
        "Qual o tempo medio de permanencia das internacoes ja encerradas?",
        "gestor",
        "faixa_etaria",
        "SELECT ROUND(AVG(tempo_permanencia), 1) AS media FROM gold.internacoes "
        "WHERE NOT ativa",
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

    # todo tipo declarado e conhecido, e todos os tipos sao exercitados.
    tipos_usados = {p.tipo for p in CONJUNTO}
    assert tipos_usados <= set(TIPOS), f"tipo desconhecido: {tipos_usados - set(TIPOS)}"
    assert tipos_usados == set(TIPOS), f"tipo sem pergunta: {set(TIPOS) - tipos_usados}"

    # toda SQL de referencia precisa passar pelos guardrails de entrada no escopo
    # do proprio perfil: se a referencia nao passa, a tubulacao esta errada.
    for p in CONJUNTO:
        r = governance.validar_sql(p.sql_ref, p.perfil)
        assert r.aprovado, f"sql_ref de {p.id} bloqueada [{p.perfil}]: {r.controle}: {r.motivo}"

    print("questions: autoteste OK")
    print(f"  {len(CONJUNTO)} perguntas, {len(tipos_usados)} tipos cobertos")
    for tipo in TIPOS:
        qtd = sum(1 for p in CONJUNTO if p.tipo == tipo)
        print(f"    {tipo}: {qtd}")


if __name__ == "__main__":
    _autoteste()
