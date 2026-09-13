"""Transformacao do lakehouse: Bronze -> Silver -> Gold, em DuckDB.

A Silver limpa e pseudonimiza (RNC-005): remove a PII direta (nome, cpf,
data_nascimento), pseudonimiza id_paciente por hash com salt e deriva a
faixa etaria. A Gold expoe apenas metricas e e a unica camada visivel ao motor
de linguagem (DA-LAKE-003). Tudo e determinista: a idade e calculada contra
SIM_TODAY, nunca contra o relogio do sistema (RNC-003).

Isolamento fisico (DA-LAKE-005): alem de viver no lakehouse, a Gold e exportada
para um arquivo DuckDB proprio (config.GOLD_DB_PATH) que contem so as quatro
tabelas. O motor e o avaliador conectam-se apenas a esse arquivo, de modo que
Bronze e Silver nao existem para eles, independentemente do texto da SQL. A
verificacao textual dos guardrails passa a ser uma barreira a mais, nao a unica.

Depende da Bronze (rode src.data_gen antes, ou use o autoteste daqui que ja a
gera).

Uso isolado:
    python -m src.pipeline
"""

import hashlib

import duckdb

from src import config


def _pseudo(id_paciente):
    """Pseudonimiza um id_paciente: sha256(salt + id), truncado para 16 hex.

    Deterministico (RNC-003) e, por causa do salt, nao reversivel por forca
    bruta trivial sobre os poucos ids (RNC-005). 16 hex (64 bits) nao colidem
    no volume deste prototipo.
    """
    base = f"{config.PSEUDO_SALT}{id_paciente}".encode()
    return hashlib.sha256(base).hexdigest()[:16]


def _expr_faixa_etaria(col_nascimento):
    """Monta a expressao SQL que deriva a faixa etaria a partir da idade.

    A idade e a diferenca em anos entre SIM_TODAY e a data de nascimento. As
    faixas seguem config.FAIXAS_ETARIAS (limite inferior inclusivo). SIM_TODAY
    entra como literal de data para manter o determinismo.
    """
    hoje = config.SIM_TODAY.isoformat()
    idade = f"date_diff('year', {col_nascimento}, DATE '{hoje}')"
    return (
        "CASE "
        f"WHEN {idade} < 18 THEN '0-17' "
        f"WHEN {idade} < 40 THEN '18-39' "
        f"WHEN {idade} < 60 THEN '40-59' "
        f"WHEN {idade} < 80 THEN '60-79' "
        "ELSE '80+' END"
    )


def construir_silver(con):
    """Materializa o schema silver a partir da Bronze, ja anonimizado."""
    con.execute("CREATE SCHEMA IF NOT EXISTS silver")

    # paciente: sem PII direta; ganha pseudonimo e faixa etaria. O pseudonimo e
    # calculado em Python (registra a funcao como UDF nao vale a pena aqui) via
    # uma tabela de mapeamento id -> pseudo, juntada a bronze.paciente.
    mapa = [
        (id_paciente, _pseudo(id_paciente))
        for (id_paciente,) in con.execute(
            "SELECT id_paciente FROM bronze.paciente"
        ).fetchall()
    ]
    con.execute("CREATE OR REPLACE TEMP TABLE _pseudo_map (id_paciente INTEGER, id_paciente_pseudo VARCHAR)")
    con.executemany("INSERT INTO _pseudo_map VALUES (?, ?)", mapa)

    faixa = _expr_faixa_etaria("p.data_nascimento")
    con.execute(
        "CREATE OR REPLACE TABLE silver.paciente AS "
        "SELECT m.id_paciente_pseudo, "
        f"       {faixa} AS faixa_etaria, "
        "       p.sexo "
        "FROM bronze.paciente p "
        "JOIN _pseudo_map m USING (id_paciente)"
    )

    # internacao: troca id_paciente pelo pseudonimo; preserva as datas (nao sao
    # PII direta) para a Gold derivar tempo de permanencia e flag ativa.
    con.execute(
        "CREATE OR REPLACE TABLE silver.internacao AS "
        "SELECT i.id_internacao, m.id_paciente_pseudo, i.id_leito, "
        "       i.data_admissao, i.data_alta_prevista, i.data_alta_real "
        "FROM bronze.internacao i "
        "JOIN _pseudo_map m USING (id_paciente)"
    )

    # leito, unidade e ocupacao_diaria nao tem PII: espelho fiel da Bronze,
    # para a Silver ser auto-suficiente como fonte da Gold.
    con.execute("CREATE OR REPLACE TABLE silver.unidade AS SELECT * FROM bronze.unidade")
    con.execute("CREATE OR REPLACE TABLE silver.leito AS SELECT * FROM bronze.leito")
    con.execute(
        "CREATE OR REPLACE TABLE silver.ocupacao_diaria AS "
        "SELECT * FROM bronze.ocupacao_diaria"
    )

    con.execute("DROP TABLE _pseudo_map")


def construir_gold(con):
    """Materializa as quatro tabelas Gold a partir da Silver (DA-LAKE-003)."""
    con.execute("CREATE SCHEMA IF NOT EXISTS gold")
    hoje = config.SIM_TODAY.isoformat()

    # 1) leitos_status: snapshot do estado de cada leito em SIM_TODAY.
    con.execute(
        "CREATE OR REPLACE TABLE gold.leitos_status AS "
        "SELECT o.id_leito, l.id_unidade, l.tipo, o.situacao "
        "FROM silver.ocupacao_diaria o "
        "JOIN silver.leito l USING (id_leito) "
        f"WHERE o.data = DATE '{hoje}'"
    )

    # 2) ocupacao_unidade: metricas agregadas por unidade no snapshot de hoje.
    con.execute(
        "CREATE OR REPLACE TABLE gold.ocupacao_unidade AS "
        "SELECT u.id_unidade, u.nome AS unidade, u.especialidade, "
        "       COUNT(*) AS total_leitos, "
        "       SUM(CASE WHEN s.situacao = 'ocupado' THEN 1 ELSE 0 END) AS ocupados, "
        "       SUM(CASE WHEN s.situacao = 'livre' THEN 1 ELSE 0 END) AS livres, "
        "       SUM(CASE WHEN s.situacao = 'bloqueado' THEN 1 ELSE 0 END) AS bloqueados, "
        "       ROUND(100.0 * SUM(CASE WHEN s.situacao = 'ocupado' THEN 1 ELSE 0 END) "
        "             / COUNT(*), 1) AS taxa_ocupacao "
        "FROM gold.leitos_status s "
        "JOIN silver.unidade u USING (id_unidade) "
        "GROUP BY u.id_unidade, u.nome, u.especialidade "
        "ORDER BY u.id_unidade"
    )

    # 3) ocupacao_diaria: serie historica diaria do hospital inteiro.
    con.execute(
        "CREATE OR REPLACE TABLE gold.ocupacao_diaria AS "
        "SELECT o.data, "
        "       COUNT(*) AS total_leitos, "
        "       SUM(CASE WHEN o.situacao = 'ocupado' THEN 1 ELSE 0 END) AS ocupados, "
        "       SUM(CASE WHEN o.situacao = 'livre' THEN 1 ELSE 0 END) AS livres, "
        "       SUM(CASE WHEN o.situacao = 'bloqueado' THEN 1 ELSE 0 END) AS bloqueados, "
        "       ROUND(100.0 * SUM(CASE WHEN o.situacao = 'ocupado' THEN 1 ELSE 0 END) "
        "             / COUNT(*), 1) AS taxa_ocupacao "
        "FROM silver.ocupacao_diaria o "
        "GROUP BY o.data "
        "ORDER BY o.data"
    )

    # 4) internacoes: uma linha por internacao, com faixa etaria, tempo de
    # permanencia (so para encerradas) e flag ativa. Sem id_paciente_pseudo: a
    # Gold nao expoe nem o pseudonimo (minimizacao, DA-LAKE-003).
    con.execute(
        "CREATE OR REPLACE TABLE gold.internacoes AS "
        "SELECT i.id_internacao, l.id_unidade, l.tipo, "
        "       p.faixa_etaria, p.sexo, i.data_admissao, "
        "       CASE WHEN i.data_alta_real IS NULL THEN NULL "
        "            ELSE date_diff('day', i.data_admissao, i.data_alta_real) END "
        "            AS tempo_permanencia, "
        "       (i.data_alta_real IS NULL) AS ativa "
        "FROM silver.internacao i "
        "JOIN silver.leito l USING (id_leito) "
        "JOIN silver.paciente p USING (id_paciente_pseudo)"
    )


def exportar_gold(con):
    """Copia as tabelas Gold para o arquivo isolado (DA-LAKE-005).

    Recria o arquivo do zero a cada execucao (idempotente e determinista). O
    schema dentro do arquivo tambem se chama `gold`, para que a SQL do motor
    (`gold.tabela`) seja identica nas duas bases.
    """
    config.GOLD_DB_PATH.unlink(missing_ok=True)
    con.execute(f"ATTACH '{config.GOLD_DB_PATH}' AS gold_isolada")
    try:
        con.execute("CREATE SCHEMA IF NOT EXISTS gold_isolada.gold")
        for tabela in config.GOLD_TABLES:
            nome = tabela.split(".", 1)[1]
            con.execute(
                f"CREATE OR REPLACE TABLE gold_isolada.gold.{nome} AS "
                f"SELECT * FROM gold.{nome}"
            )
    finally:
        con.execute("DETACH gold_isolada")


def construir():
    """Constroi Silver e Gold sobre a Bronze e exporta a Gold isolada."""
    con = duckdb.connect(str(config.DB_PATH))
    try:
        construir_silver(con)
        construir_gold(con)
        exportar_gold(con)
        contagens = {}
        for schema, tabela in (
            ("silver", "paciente"),
            ("silver", "internacao"),
            ("gold", "leitos_status"),
            ("gold", "ocupacao_unidade"),
            ("gold", "ocupacao_diaria"),
            ("gold", "internacoes"),
        ):
            n = con.execute(f"SELECT COUNT(*) FROM {schema}.{tabela}").fetchone()[0]
            contagens[f"{schema}.{tabela}"] = n
    finally:
        con.close()
    return contagens


def _colunas(con, schema, tabela):
    """Retorna o conjunto de nomes de coluna de uma tabela."""
    linhas = con.execute(
        "SELECT column_name FROM information_schema.columns "
        "WHERE table_schema = ? AND table_name = ?",
        [schema, tabela],
    ).fetchall()
    return {nome for (nome,) in linhas}


def _autoteste():
    """Gera Bronze, constroi Silver/Gold e valida os invariantes do pipeline."""
    from src import data_gen

    data_gen.construir()
    contagens = construir()

    print("pipeline: Silver e Gold construidas")
    print("  contagens por tabela:")
    for tabela, n in contagens.items():
        print(f"    {tabela}: {n}")

    con = duckdb.connect(str(config.DB_PATH))
    try:
        # RNC-005: nenhuma identificacao direta do paciente sobrevive a Silver.
        # A checagem foca a tabela de paciente, unica derivada da PII da Bronze;
        # nomes legitimos como silver.unidade.nome (nome da unidade) nao contam.
        cols_paciente = _colunas(con, "silver", "paciente")
        for proibida in ("nome", "cpf", "data_nascimento"):
            assert proibida not in cols_paciente, (
                f"coluna proibida em silver.paciente: {proibida}"
            )

        # faixa etaria sempre dentro do dominio configurado.
        faixas = {
            f for (f,) in con.execute(
                "SELECT DISTINCT faixa_etaria FROM silver.paciente"
            ).fetchall()
        }
        assert faixas <= set(config.FAIXAS_ETARIAS), (
            f"faixa etaria fora do dominio: {faixas - set(config.FAIXAS_ETARIAS)}"
        )

        # pseudonimo deterministico e sem colisao: distintos de pseudo na
        # silver.paciente devem igualar o numero de pacientes.
        n_pac = con.execute("SELECT COUNT(*) FROM silver.paciente").fetchone()[0]
        n_pseudo = con.execute(
            "SELECT COUNT(DISTINCT id_paciente_pseudo) FROM silver.paciente"
        ).fetchone()[0]
        assert n_pac == n_pseudo, (
            f"colisao de pseudonimo: {n_pac} pacientes, {n_pseudo} pseudonimos"
        )
        assert _pseudo(1) == _pseudo(1), "pseudonimo nao deterministico"

        # taxa de ocupacao sempre em [0, 100].
        for tabela in ("gold.ocupacao_unidade", "gold.ocupacao_diaria"):
            fora = con.execute(
                f"SELECT COUNT(*) FROM {tabela} "
                "WHERE taxa_ocupacao < 0 OR taxa_ocupacao > 100"
            ).fetchone()[0]
            assert fora == 0, f"taxa_ocupacao fora de [0,100] em {tabela}: {fora} linhas"

        # ativa <=> data_alta_real nula; tempo_permanencia nulo sse ativa.
        incoerentes = con.execute(
            "SELECT COUNT(*) FROM gold.internacoes "
            "WHERE (ativa AND tempo_permanencia IS NOT NULL) "
            "   OR (NOT ativa AND tempo_permanencia IS NULL)"
        ).fetchone()[0]
        assert incoerentes == 0, (
            f"coerencia ativa/tempo_permanencia violada: {incoerentes} linhas"
        )

        # as quatro tabelas Gold autorizadas existem.
        gold_existentes = {
            f"gold.{t}" for (t,) in con.execute(
                "SELECT table_name FROM information_schema.tables "
                "WHERE table_schema = 'gold'"
            ).fetchall()
        }
        assert set(config.GOLD_TABLES) <= gold_existentes, (
            f"tabelas Gold faltando: {set(config.GOLD_TABLES) - gold_existentes}"
        )

        # soma de leitos por unidade no snapshot == total de leitos.
        soma = con.execute(
            "SELECT SUM(total_leitos) FROM gold.ocupacao_unidade"
        ).fetchone()[0]
        assert soma == config.VOL_LEITOS, (
            f"soma de leitos por unidade ({soma}) != VOL_LEITOS ({config.VOL_LEITOS})"
        )
    finally:
        con.close()

    # DA-LAKE-005 / CTRL-GOV-007: o arquivo isolado tem as quatro tabelas Gold,
    # identicas as do lakehouse, e nada alem delas. Bronze e Silver nao existem
    # nele, mesmo para consultas que contornem a analise textual.
    iso = duckdb.connect(str(config.GOLD_DB_PATH), read_only=True)
    try:
        schemas = {
            s for (s,) in iso.execute(
                "SELECT DISTINCT table_schema FROM information_schema.tables"
            ).fetchall()
        }
        assert schemas == {"gold"}, f"schemas inesperados na Gold isolada: {schemas}"
        tabelas = {
            f"gold.{t}" for (t,) in iso.execute(
                "SELECT table_name FROM information_schema.tables WHERE table_schema = 'gold'"
            ).fetchall()
        }
        assert tabelas == set(config.GOLD_TABLES), f"tabelas na Gold isolada: {tabelas}"
        for tabela, n in contagens.items():
            if tabela.startswith("gold."):
                m = iso.execute(f"SELECT COUNT(*) FROM {tabela}").fetchone()[0]
                assert m == n, f"{tabela}: {m} linhas na isolada, {n} no lakehouse"
        colunas = {
            c for (c,) in iso.execute(
                "SELECT column_name FROM information_schema.columns"
            ).fetchall()
        }
        sensiveis = set(config.CAMPOS_SENSIVEIS) & colunas
        assert not sensiveis, f"campo sensivel na Gold isolada: {sensiveis}"
        # As tres consultas que contornavam a analise textual antes do isolamento
        # (banca, rodada 01, P-09) agora falham no proprio banco.
        for sql in (
            "SELECT nome, cpf FROM query_table('bronze.paciente') LIMIT 1",
            "SELECT * FROM silver.paciente LIMIT 1",
            "SELECT * FROM bronze.paciente LIMIT 1",
        ):
            try:
                iso.execute(sql)
                raise AssertionError(f"a Gold isolada respondeu a: {sql}")
            except duckdb.Error:
                pass
        # O catalogo da Gold isolada so revela a propria Gold.
        internas = iso.execute(
            "SELECT COUNT(*) FROM duckdb_tables() WHERE schema_name IN ('bronze', 'silver')"
        ).fetchone()[0]
        assert internas == 0, "catalogo da Gold isolada revela camadas internas"
    finally:
        iso.close()

    print("pipeline: autoteste OK")
    print(f"  Gold isolada em {config.GOLD_DB_PATH}: so schema gold, sem campo sensivel; "
          "bronze/silver inacessiveis")


if __name__ == "__main__":
    _autoteste()
