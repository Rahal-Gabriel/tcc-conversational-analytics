"""Camada 2: governanca de entrada. Guardrails da SQL candidata e auditoria.

Antes de qualquer consulta tocar o banco, a SQL gerada pelo motor passa por uma
verificacao em camadas (CTRL-GOV-001 a 005), e a pergunta do usuario e
registrada na trilha de auditoria. A barreira final, a conexao DuckDB somente
leitura (CTRL-GOV-006), entra como defesa em profundidade e mora aqui como
helper, para ser usada na execucao.

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
)
_RE_PROIBIDAS = re.compile(r"\b(" + "|".join(PALAVRAS_PROIBIDAS) + r")\b", re.IGNORECASE)

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
    """Abre a conexao DuckDB em modo somente leitura (CTRL-GOV-006).

    Barreira final de defesa em profundidade: mesmo que a analise textual
    falhasse, o banco recusa qualquer escrita. Importa duckdb localmente para
    manter a analise de governanca utilizavel sem o banco presente.
    """
    import duckdb

    return duckdb.connect(str(config.DB_PATH), read_only=True)


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

    print("governance: autoteste OK")
    print(f"  {len(validos)} casos validos aprovados, {len(bloqueados)} casos bloqueados")
    print(f"  trilha de auditoria: {config.AUDIT_LOG_PATH}")


if __name__ == "__main__":
    _autoteste()
