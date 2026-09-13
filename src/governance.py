"""Governanca de entrada (Camada 2) e de saida (Camada 4): guardrails e auditoria.

Antes de qualquer consulta tocar o banco, a SQL gerada pelo motor passa por uma
verificacao em camadas (CTRL-GOV-001 a 005), e a pergunta do usuario e
registrada na trilha de auditoria. As barreiras finais moram aqui como helper
de conexao: a execucao acontece em conexao DuckDB somente leitura
(CTRL-GOV-006) e apenas sobre o arquivo isolado da Gold (CTRL-GOV-007,
DA-LAKE-005), onde Bronze e Silver nao existem. A analise textual e, portanto,
uma camada a mais, e nao a unica: a banca simulada (rodada 01, P-09) mostrou
que, sozinha, ela era contornavel por funcoes de tabela, catalogo e alias.

Depois da execucao, a validacao de saida (Camada 4) e a ultima barreira:
aterramento contra o schema Gold conhecido (CTRL-VALID-001), filtro de campo
sensivel no resultado (CTRL-VALID-002) e o registro da resposta na trilha de
auditoria (CTRL-AUD-001).

A analise textual e conservadora: comentarios e literais de texto sao removidos
antes da inspecao, para que uma palavra proibida escondida num comentario ou
dentro de uma string nao escape (nem cause falso positivo). So instrucoes de
leitura, em escopo Gold autorizado ao perfil, passam.

Determinismo (RNC-003): o registro de auditoria ancora o horario em SIM_TODAY,
nunca no relogio do sistema.

Uso isolado:
    python -m src.governance
"""

import json
import re
from collections import namedtuple

from src import config

# Resultado estruturado de uma verificacao de entrada. Quando aprovado e True,
# controle e motivo sao None; quando False, controle traz o ID do guardrail que
# barrou (ex.: "CTRL-GOV-002") e motivo a explicacao legivel.
ResultadoGovernanca = namedtuple("ResultadoGovernanca", "aprovado controle motivo")

# CTRL-GOV-002: comandos de escrita ou administrativos, e funcoes de I/O que
# escapariam do escopo somente leitura sobre as tabelas Gold (leitura de
# arquivos arbitrarios via DuckDB). Casados como palavra inteira, sem distinguir
# maiusculas. Funcoes escalares legitimas (replace, round, etc.) ficam de fora
# de proposito, para nao gerar falso positivo.
PALAVRAS_PROIBIDAS = (
    "insert", "update", "delete", "drop", "alter", "create", "truncate",
    "attach", "detach", "copy", "pragma", "grant", "revoke", "vacuum",
    "install", "load", "set", "call", "export", "import", "reindex", "analyze",
    "merge", "replace",  # 'or replace' / 'insert or replace': formas de escrita
    "read_csv", "read_parquet", "read_json", "read_text", "read_blob",
    "parquet_scan", "glob", "sniff_csv",
    # Funcoes de tabela que recebem o nome da tabela como texto: o literal e
    # esvaziado por _limpar antes da inspecao, entao 'bronze.x' dentro de
    # query_table('bronze.x') escaparia de CTRL-GOV-004 (banca, rodada 01, P-09).
    "query", "query_table",
    # Catalogo: revela schemas, tabelas e colunas internas (inclusive as
    # sensiveis) sem citar bronze/silver no texto da SQL.
    "information_schema", "sqlite_master", "sqlite_schema",
)
# Familias de funcoes e views de catalogo e de I/O, casadas por prefixo:
# duckdb_tables(), duckdb_columns(), pragma_table_info(), read_*(), etc.
PREFIXOS_PROIBIDOS = ("duckdb_", "sqlite_", "pragma_", "read_")
_RE_PROIBIDAS = re.compile(
    r"\b(" + "|".join(PALAVRAS_PROIBIDAS) + r"|(?:"
    + "|".join(PREFIXOS_PROIBIDOS) + r")\w+)\b",
    re.IGNORECASE,
)

# CTRL-GOV-004: as camadas internas nunca podem ser referenciadas.
_RE_CAMADA_INTERNA = re.compile(r"\b(bronze|silver)\b", re.IGNORECASE)

# CTRL-GOV-005: extrai cada tabela referenciada no schema gold.
_RE_TABELA_GOLD = re.compile(r"\bgold\s*\.\s*(\w+)", re.IGNORECASE)


def _limpar(sql):
    """Devolve a SQL pronta para inspecao: sem comentarios, strings nem aspas.

    Remove comentarios de bloco e de linha, esvazia literais entre aspas simples
    (para que palavras dentro de texto nao contem como comando) e apaga as aspas
    duplas (para que um identificador citado como "silver"."paciente" ainda seja
    detectado). E uma normalizacao para analise, nao a SQL que sera executada.
    """
    s = re.sub(r"/\*.*?\*/", " ", sql, flags=re.DOTALL)  # comentarios de bloco
    s = re.sub(r"--[^\n]*", " ", s)                        # comentarios de linha
    s = re.sub(r"'[^']*'", "''", s)                        # literais de texto
    s = s.replace('"', "")                                  # aspas de identificador
    return s


def validar_sql(sql, perfil):
    """Aplica os guardrails de entrada a uma SQL candidata para um perfil.

    Retorna um ResultadoGovernanca. A ordem das checagens determina qual
    controle e reportado quando mais de um se aplicaria: instrucao unica (003),
    ausencia de comando proibido (002), forma de leitura (001), camadas internas
    (004) e, por fim, escopo Gold autorizado ao perfil (005).
    """
    if perfil not in config.PERFIS:
        return ResultadoGovernanca(False, "CTRL-GOV-005", f"perfil desconhecido: {perfil}")

    if not isinstance(sql, str) or not sql.strip():
        return ResultadoGovernanca(False, "CTRL-GOV-001", "SQL vazia")

    limpa = _limpar(sql).strip()

    # CTRL-GOV-003: uma so instrucao. Um unico ponto e virgula final e tolerado;
    # qualquer outro indica multiplas instrucoes.
    nucleo = re.sub(r";\s*$", "", limpa)
    if ";" in nucleo:
        return ResultadoGovernanca(False, "CTRL-GOV-003", "multiplas instrucoes na mesma SQL")

    # CTRL-GOV-002: nenhum comando de escrita, administrativo ou de I/O.
    achado = _RE_PROIBIDAS.search(nucleo)
    if achado:
        return ResultadoGovernanca(
            False, "CTRL-GOV-002", f"comando nao permitido: {achado.group(1).lower()}"
        )

    # CTRL-GOV-001: a instrucao precisa ser de leitura (SELECT ou WITH).
    if not re.match(r"(?is)^\s*(select|with)\b", nucleo):
        return ResultadoGovernanca(
            False, "CTRL-GOV-001", "a SQL deve ser uma consulta de leitura (SELECT ou WITH)"
        )

    # CTRL-GOV-004: as camadas Bronze e Silver sao invisiveis ao motor.
    if _RE_CAMADA_INTERNA.search(nucleo):
        return ResultadoGovernanca(
            False, "CTRL-GOV-004", "acesso negado as camadas internas (bronze/silver)"
        )

    # CTRL-GOV-005: so as tabelas Gold autorizadas ao perfil.
    autorizadas = set(config.PERFIS[perfil])
    for tabela in _RE_TABELA_GOLD.findall(nucleo):
        nome = f"gold.{tabela.lower()}"
        if nome not in config.GOLD_TABLES:
            return ResultadoGovernanca(False, "CTRL-GOV-005", f"tabela Gold inexistente: {nome}")
        if nome not in autorizadas:
            return ResultadoGovernanca(
                False, "CTRL-GOV-005", f"tabela fora do escopo do perfil {perfil}: {nome}"
            )

    return ResultadoGovernanca(True, None, None)


def conectar_somente_leitura():
    """Abre a conexao de consulta: Gold isolada, somente leitura (CTRL-GOV-006 e 007).

    Duas barreiras no proprio banco, independentes do texto da SQL: o arquivo
    aberto contem apenas a Gold (Bronze e Silver nao existem nele, DA-LAKE-005)
    e a conexao e somente leitura (nenhuma escrita e possivel). Importa duckdb
    localmente para manter a analise de governanca utilizavel sem o banco.
    """
    import duckdb

    if not config.GOLD_DB_PATH.exists():
        raise FileNotFoundError(
            f"Gold isolada ausente em {config.GOLD_DB_PATH}; rode src.pipeline "
            "(ou run_all.py) para gera-la a partir do lakehouse."
        )
    return duckdb.connect(str(config.GOLD_DB_PATH), read_only=True)


def registrar_pergunta(usuario, perfil, pergunta, momento=None, caminho=None):
    """Anexa o registro de entrada de uma pergunta a trilha de auditoria.

    Grava uma linha JSON com horario, usuario, perfil e a pergunta original. O
    horario padrao ancora em SIM_TODAY (RNC-003) para que a trilha seja
    reproduzivel. Retorna o dicionario registrado.
    """
    if momento is None:
        momento = config.SIM_TODAY.isoformat()
    if caminho is None:
        caminho = config.AUDIT_LOG_PATH

    registro = {
        "momento": momento,
        "evento": "entrada",
        "usuario": usuario,
        "perfil": perfil,
        "pergunta": pergunta,
    }
    caminho.parent.mkdir(parents=True, exist_ok=True)
    with open(caminho, "a", encoding="utf-8") as f:
        f.write(json.dumps(registro, ensure_ascii=False) + "\n")
    return registro


# Eventos possiveis no registro de uma resposta (Camada 4, CTRL-AUD-001).
EVENTOS = ("correto", "incorreto", "bloqueado", "erro")


def validar_saida(sql, colunas_resultado):
    """Aplica a validacao de saida (Camada 4) a uma consulta ja executada.

    Retorna um ResultadoGovernanca. Duas barreiras, nesta ordem:

    - CTRL-VALID-001 (aterramento): toda tabela `gold.X` citada na SQL precisa
      existir no schema Gold conhecido (config.GOLD_TABLES). Uma tabela inventada
      pelo modelo bloqueia a resposta, mitigando alucinacao.
    - CTRL-VALID-002 (filtro de campo sensivel): se qualquer coluna do resultado
      tiver nome de campo sensivel (config.CAMPOS_SENSIVEIS), a resposta e barrada
      (RNC-005), mesmo que algo tenha escapado das camadas anteriores.
    """
    limpa = _limpar(sql)
    for tabela in _RE_TABELA_GOLD.findall(limpa):
        nome = f"gold.{tabela.lower()}"
        if nome not in config.GOLD_TABLES:
            return ResultadoGovernanca(
                False, "CTRL-VALID-001", f"tabela Gold inexistente na saida: {nome}"
            )

    sensiveis = set(config.CAMPOS_SENSIVEIS)
    for coluna in colunas_resultado:
        if str(coluna).lower() in sensiveis:
            return ResultadoGovernanca(
                False, "CTRL-VALID-002", f"campo sensivel na saida: {coluna}"
            )

    return ResultadoGovernanca(True, None, None)


def registrar_resposta(usuario, perfil, pergunta, sql, evento, momento=None, caminho=None):
    """Anexa o registro de saida de uma interacao a trilha de auditoria.

    Grava uma linha JSON com horario, usuario, perfil, pergunta, SQL e o evento
    (CTRL-AUD-001). O horario padrao ancora em SIM_TODAY (RNC-003). Retorna o
    dicionario registrado.
    """
    assert evento in EVENTOS, f"evento de auditoria desconhecido: {evento!r}"
    if momento is None:
        momento = config.SIM_TODAY.isoformat()
    if caminho is None:
        caminho = config.AUDIT_LOG_PATH

    registro = {
        "momento": momento,
        "evento": evento,
        "usuario": usuario,
        "perfil": perfil,
        "pergunta": pergunta,
        "sql": sql,
    }
    caminho.parent.mkdir(parents=True, exist_ok=True)
    with open(caminho, "a", encoding="utf-8") as f:
        f.write(json.dumps(registro, ensure_ascii=False) + "\n")
    return registro


def _autoteste():
    """Valida os guardrails com casos que devem passar e que devem ser barrados."""
    # Casos validos: leitura, escopo autorizado, e protecoes que nao podem gerar
    # falso positivo (ponto e virgula final, palavra proibida dentro de string).
    validos = [
        ("gestor", "SELECT * FROM gold.internacoes"),
        ("enfermagem", "SELECT * FROM gold.leitos_status"),
        ("gestor", "SELECT taxa_ocupacao FROM gold.ocupacao_unidade;"),
        ("gestor", "WITH x AS (SELECT * FROM gold.ocupacao_diaria) SELECT * FROM x"),
        ("enfermagem", "SELECT * FROM gold.leitos_status WHERE tipo = 'drop'"),
        # Colunas e aliases legitimos que contem os prefixos proibidos como
        # substring nao podem gerar falso positivo (prefixo casa so no inicio).
        ("gestor", "SELECT COUNT(*) AS n_read_ok, tipo FROM gold.internacoes GROUP BY tipo"),
        ("gestor", "SELECT unidade AS query_unidade_nome FROM gold.ocupacao_unidade"),
    ]
    for perfil, sql in validos:
        r = validar_sql(sql, perfil)
        assert r.aprovado, f"deveria aprovar [{perfil}]: {sql!r} -> {r.controle}: {r.motivo}"

    # Casos que devem ser bloqueados, com o controle exato esperado.
    bloqueados = [
        ("CTRL-GOV-001", "gestor", ""),
        ("CTRL-GOV-001", "gestor", "EXPLAIN SELECT * FROM gold.internacoes"),
        ("CTRL-GOV-002", "gestor", "WITH x AS (DELETE FROM gold.internacoes RETURNING *) SELECT * FROM x"),
        ("CTRL-GOV-002", "gestor", "SELECT * FROM read_csv('/etc/passwd')"),
        ("CTRL-GOV-002", "gestor", "DROP TABLE gold.internacoes"),
        ("CTRL-GOV-003", "gestor", "SELECT 1; SELECT 2"),
        ("CTRL-GOV-004", "gestor", "SELECT * FROM silver.paciente"),
        ("CTRL-GOV-004", "gestor", "SELECT * FROM bronze.paciente"),
        ("CTRL-GOV-005", "enfermagem", "SELECT * FROM gold.internacoes"),
        ("CTRL-GOV-005", "intruso", "SELECT * FROM gold.leitos_status"),
        # Desvios encontrados pela banca simulada (rodada 01, P-09): funcao de
        # tabela com o nome em texto, catalogo e view de sistema.
        ("CTRL-GOV-002", "enfermagem", "SELECT nome AS n, cpf AS c FROM query_table('bronze.paciente') LIMIT 2"),
        ("CTRL-GOV-002", "gestor", "SELECT * FROM query('SELECT cpf FROM silver.paciente')"),
        ("CTRL-GOV-002", "enfermagem", "SELECT table_schema, table_name, column_name FROM information_schema.columns"),
        ("CTRL-GOV-002", "enfermagem", "SELECT * FROM duckdb_tables()"),
        ("CTRL-GOV-002", "gestor", "SELECT * FROM duckdb_columns() WHERE column_name = 'cpf'"),
        ("CTRL-GOV-002", "gestor", "SELECT * FROM pragma_table_info('bronze.paciente')"),
        ("CTRL-GOV-002", "gestor", "SELECT * FROM sqlite_master"),
        ("CTRL-GOV-002", "gestor", "SELECT * FROM read_text('/etc/hostname')"),
    ]
    for esperado, perfil, sql in bloqueados:
        r = validar_sql(sql, perfil)
        assert not r.aprovado, f"deveria bloquear [{perfil}]: {sql!r}"
        assert r.controle == esperado, (
            f"controle errado para [{perfil}] {sql!r}: esperado {esperado}, veio {r.controle}"
        )

    # Auditoria: o registro de entrada e gravavel e tem os campos esperados.
    reg = registrar_pergunta("ana", "gestor", "qual a ocupacao hoje?")
    assert reg["evento"] == "entrada" and reg["momento"] == config.SIM_TODAY.isoformat()

    # Camada 4: validacao de saida.
    # CTRL-VALID-001 (aterramento): SQL citando tabela Gold inexistente bloqueia.
    r = validar_saida("SELECT * FROM gold.inexistente", ["x"])
    assert not r.aprovado and r.controle == "CTRL-VALID-001", "aterramento deveria barrar"
    # Saida legitima, sem coluna sensivel: aprovada.
    r = validar_saida(
        "SELECT unidade, taxa_ocupacao FROM gold.ocupacao_unidade",
        ["unidade", "taxa_ocupacao"],
    )
    assert r.aprovado, f"deveria aprovar a saida: {r.controle}: {r.motivo}"
    # CTRL-VALID-002 (filtro sensivel): coluna sensivel no resultado bloqueia.
    r = validar_saida("SELECT * FROM gold.internacoes", ["faixa_etaria", "cpf"])
    assert not r.aprovado and r.controle == "CTRL-VALID-002", "filtro sensivel deveria barrar"

    # CTRL-AUD-001: o registro da resposta e gravavel, com evento valido.
    reg2 = registrar_resposta("ana", "gestor", "qual a ocupacao hoje?", "SELECT 1", "correto")
    assert reg2["evento"] == "correto" and reg2["sql"] == "SELECT 1"
    assert reg2["momento"] == config.SIM_TODAY.isoformat()

    # Nota: o isolamento fisico da Gold (CTRL-GOV-007) e verificado em
    # src.pipeline, que gera os dados; aqui a analise roda sem banco.
    print("governance: autoteste OK")
    print(f"  {len(validos)} casos validos aprovados, {len(bloqueados)} casos bloqueados")
    print("  validacao de saida: aterramento e filtro sensivel barram; saida limpa passa")
    print(f"  trilha de auditoria: {config.AUDIT_LOG_PATH}")


if __name__ == "__main__":
    _autoteste()
