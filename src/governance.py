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

Trilha de auditoria (CTRL-AUD-001, Etapa C): cada interacao gera um registro de
entrada e um de saida, ligados por `id_interacao`, com dois horarios (o real,
do relogio, em UTC, e a data de simulacao SIM_TODAY), o motor, o controle que
barrou (se houve), o hash e o tamanho do resultado entregue. Os registros sao
encadeados por hash (cada um guarda o hash do anterior), e `verificar_trilha`
le o arquivo e detecta qualquer alteracao, remocao ou insercao posterior.
Determinismo (RNC-003): dados e metricas continuam deterministas; o horario
real do log fica explicitamente fora dessa exigencia, porque um registro sem
tempo real nao sustenta responsabilizacao (banca, rodada 01, P-20).

Dado pessoal na pergunta (CTRL-GOV-008, Etapa E): antes de qualquer chamada ao
motor e antes do registro na trilha, o texto da pergunta e verificado contra
padroes de CPF, e-mail e telefone (config.PADROES_PII). Se houver ocorrencia,
a pergunta e recusada na entrada e o trecho e mascarado; o texto original
nunca chega ao motor (que pode ser uma API externa) nem ao log. Nome proprio
nao e detectavel por padrao e fica declarado como limitacao (banca, rodada
01, P-18; mitigacao: implantacao local, DA-GOV-003).

Autenticacao: `usuario` e `perfil` sao recebidos do chamador. No prototipo nao
ha provedor de identidade; o ponto de integracao e a assinatura de
registrar_pergunta, que numa implantacao receberia a identidade verificada
(por exemplo, do token do sistema hospitalar) em vez de uma string livre.

Uso isolado:
    python -m src.governance
"""

import datetime
import hashlib
import json
import re
import uuid
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

# CTRL-GOV-008: padroes de dado pessoal no texto da pergunta (config.PADROES_PII).
_RE_PII = {nome: re.compile(padrao) for nome, padrao in config.PADROES_PII.items()}

# Resultado do filtro de dado pessoal: `texto` e a pergunta mascarada (igual a
# original quando nada foi encontrado) e `achados` lista os tipos detectados.
ResultadoPII = namedtuple("ResultadoPII", "aprovado controle motivo texto achados")


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


def filtrar_pii(pergunta):
    """CTRL-GOV-008: barra e mascara dado pessoal no texto da pergunta.

    Roda antes do motor e antes da trilha. Devolve o texto com cada ocorrencia
    substituida por config.MASCARA_PII; a pergunta so segue quando nenhum
    padrao casa. E um filtro por padrao (CPF, e-mail, telefone): nao reconhece
    nomes, e essa limitacao e declarada.
    """
    texto = pergunta or ""
    achados = []
    for nome, padrao in _RE_PII.items():
        if padrao.search(texto):
            achados.append(nome)
            texto = padrao.sub(config.MASCARA_PII, texto)
    if achados:
        return ResultadoPII(
            False, "CTRL-GOV-008",
            f"dado pessoal no texto da pergunta ({', '.join(achados)}); nada foi enviado ao motor",
            texto, achados,
        )
    return ResultadoPII(True, None, None, texto, achados)


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


# Trilha de auditoria (CTRL-AUD-001)

# Campos obrigatorios de cada tipo de registro; verificar_trilha exige todos.
CAMPOS_ENTRADA = (
    "id_interacao", "momento_real", "data_simulacao", "evento", "usuario",
    "perfil", "pergunta", "hash_anterior", "hash",
)
CAMPOS_SAIDA = CAMPOS_ENTRADA + (
    "sql", "motor", "controle", "motivo", "hash_resultado", "n_linhas",
)

# Eventos possiveis no registro de uma resposta (Camada 4, CTRL-AUD-001).
EVENTOS = ("correto", "incorreto", "bloqueado", "erro", "recusado")


def _agora_utc():
    """Horario real, em UTC, com segundos. Unico ponto que le o relogio."""
    return datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")


def _hash_registro(registro):
    """Hash SHA-256 do registro serializado de forma canonica (sem o campo hash)."""
    base = {k: v for k, v in registro.items() if k != "hash"}
    texto = json.dumps(base, ensure_ascii=False, sort_keys=True, default=str)
    return hashlib.sha256(texto.encode("utf-8")).hexdigest()


def hash_resultado(colunas, linhas):
    """Hash SHA-256 do resultado entregue (colunas e linhas), para a auditoria.

    Registrar o hash, e nao o resultado, evita copiar dados para o log e ainda
    permite provar depois que uma resposta foi ou nao a entregue.
    """
    texto = json.dumps([list(colunas), [list(l) for l in linhas]], ensure_ascii=False, default=str)
    return hashlib.sha256(texto.encode("utf-8")).hexdigest()


def _ultimo_hash(caminho):
    """Hash do ultimo registro do arquivo, ou o genesis se ele nao existe/esta vazio."""
    if not caminho.exists():
        return config.AUDIT_HASH_GENESIS
    ultimo = None
    with open(caminho, encoding="utf-8") as f:
        for linha in f:
            if linha.strip():
                ultimo = linha
    if ultimo is None:
        return config.AUDIT_HASH_GENESIS
    return json.loads(ultimo).get("hash", config.AUDIT_HASH_GENESIS)


def _gravar(registro, caminho):
    """Encadeia o registro ao anterior, calcula seu hash e o anexa ao arquivo."""
    caminho.parent.mkdir(parents=True, exist_ok=True)
    registro["hash_anterior"] = _ultimo_hash(caminho)
    registro["hash"] = _hash_registro(registro)
    with open(caminho, "a", encoding="utf-8") as f:
        f.write(json.dumps(registro, ensure_ascii=False, default=str) + "\n")
    return registro


def registrar_pergunta(usuario, perfil, pergunta, id_interacao=None, caminho=None):
    """Anexa o registro de entrada de uma pergunta a trilha de auditoria.

    Gera (ou recebe) o `id_interacao` que liga esta entrada a resposta, grava o
    horario real e a data de simulacao, o usuario, o perfil e a pergunta.
    A pergunta e sempre gravada mascarada (CTRL-GOV-008): mesmo que o chamador
    esqueca o filtro, dado pessoal nao entra na trilha. Retorna o dicionario
    registrado (com o id, para a resposta).
    """
    registro = {
        "id_interacao": id_interacao or uuid.uuid4().hex,
        "momento_real": _agora_utc(),
        "data_simulacao": config.SIM_TODAY_ISO,
        "evento": "entrada",
        "usuario": usuario,
        "perfil": perfil,
        "pergunta": filtrar_pii(pergunta).texto,
    }
    return _gravar(registro, caminho or config.AUDIT_LOG_PATH)


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


def registrar_resposta(
    usuario, perfil, pergunta, sql, evento, id_interacao,
    motor=None, controle=None, motivo=None, resultado=None, caminho=None,
):
    """Anexa o registro de saida de uma interacao a trilha de auditoria.

    Grava, alem dos campos da entrada, a SQL, o motor que a gerou, o evento, o
    controle e o motivo (quando bloqueada) e o hash e o numero de linhas do
    resultado entregue (`resultado` = (colunas, linhas), so quando algo foi
    entregue). Retorna o dicionario registrado.
    """
    assert evento in EVENTOS, f"evento de auditoria desconhecido: {evento!r}"
    colunas, linhas = resultado if resultado is not None else (None, None)
    registro = {
        "id_interacao": id_interacao,
        "momento_real": _agora_utc(),
        "data_simulacao": config.SIM_TODAY_ISO,
        "evento": evento,
        "usuario": usuario,
        "perfil": perfil,
        "pergunta": filtrar_pii(pergunta).texto,
        "sql": sql,
        "motor": motor,
        "controle": controle,
        "motivo": motivo,
        "hash_resultado": hash_resultado(colunas, linhas) if resultado is not None else None,
        "n_linhas": len(linhas) if resultado is not None else None,
    }
    return _gravar(registro, caminho or config.AUDIT_LOG_PATH)


def verificar_trilha(caminho=None):
    """Le a trilha e verifica integridade e completude (AVAL-003 de fato).

    Devolve um dicionario com: `registros` (total lido), `integra` (a cadeia de
    hashes fecha do genesis ao ultimo registro e cada hash confere com o
    conteudo), `quebra` (numero da primeira linha invalida, ou None) e
    `interacoes`, um mapa id_interacao -> {"entrada": registro, "saida":
    registro, "completa": bool}. Uma interacao e completa quando tem entrada e
    saida com todos os campos obrigatorios presentes.
    """
    caminho = caminho or config.AUDIT_LOG_PATH
    resultado = {"registros": 0, "integra": True, "quebra": None, "interacoes": {}}
    if not caminho.exists():
        return resultado

    esperado_anterior = config.AUDIT_HASH_GENESIS
    with open(caminho, encoding="utf-8") as f:
        for numero, linha in enumerate(f, start=1):
            if not linha.strip():
                continue
            resultado["registros"] += 1
            try:
                reg = json.loads(linha)
            except json.JSONDecodeError:
                reg = None
            valido = (
                isinstance(reg, dict)
                and reg.get("hash_anterior") == esperado_anterior
                and reg.get("hash") == _hash_registro(reg)
            )
            if not valido:
                if resultado["integra"]:
                    resultado["integra"] = False
                    resultado["quebra"] = numero
                # A cadeia so pode ser retomada a partir de um registro valido.
                if isinstance(reg, dict) and reg.get("hash"):
                    esperado_anterior = reg["hash"]
                continue
            esperado_anterior = reg["hash"]

            campos = CAMPOS_ENTRADA if reg.get("evento") == "entrada" else CAMPOS_SAIDA
            papel = "entrada" if reg.get("evento") == "entrada" else "saida"
            item = resultado["interacoes"].setdefault(
                reg.get("id_interacao"), {"entrada": None, "saida": None, "completa": False}
            )
            if all(c in reg for c in campos):
                item[papel] = reg
            item["completa"] = item["entrada"] is not None and item["saida"] is not None

    return resultado


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

    # CTRL-GOV-008: dado pessoal no texto da pergunta e barrado e mascarado;
    # numeros que nao sao CPF nem telefone e datas nao geram falso positivo.
    com_pii = [
        ("cpf", "O paciente de CPF 123.456.789-09 esta internado hoje?"),
        ("cpf", "o cpf 12345678909 esta internado?"),
        ("email", "Confirme se o e-mail maria.silva@example.com pertence a algum paciente internado."),
        ("telefone", "Ligue para (11) 98765-4321 e confirme a alta."),
        ("telefone", "o telefone 3456-7890 e de qual paciente?"),
    ]
    for tipo, texto in com_pii:
        r = filtrar_pii(texto)
        assert not r.aprovado and r.controle == "CTRL-GOV-008" and tipo in r.achados, (texto, r)
        assert config.MASCARA_PII in r.texto and not any(
            _RE_PII[t].search(r.texto) for t in config.PADROES_PII), r.texto
    sem_pii = [
        "Quantos leitos estao ocupados no hospital hoje?",
        "Qual foi a taxa de ocupacao em 15/05/2026?",
        "Quantos leitos existem nas unidades 101, 205 e 310?",
        "Quantas internacoes duraram mais de 30 dias em 2026?",
        "Qual o diagnostico do paciente que esta no leito 12?",
    ]
    for texto in sem_pii:
        r = filtrar_pii(texto)
        assert r.aprovado and r.texto == texto and r.achados == [], (texto, r)
    assert filtrar_pii("").aprovado and filtrar_pii(None).texto == ""

    # Auditoria (CTRL-AUD-001): exercitada num arquivo temporario, para nao
    # misturar o autoteste com a trilha real.
    import tempfile
    from pathlib import Path

    with tempfile.TemporaryDirectory() as tmp:
        trilha = Path(tmp) / "auditoria.log"
        reg = registrar_pergunta("ana", "gestor", "qual a ocupacao hoje?", caminho=trilha)
        assert reg["evento"] == "entrada" and reg["data_simulacao"] == config.SIM_TODAY_ISO
        assert reg["hash_anterior"] == config.AUDIT_HASH_GENESIS and len(reg["hash"]) == 64
        # horario real em UTC, ISO 8601, e nao a data de simulacao.
        datetime.datetime.fromisoformat(reg["momento_real"])
        assert reg["momento_real"].endswith("+00:00") and reg["momento_real"][:10] != config.SIM_TODAY_ISO
        reg2 = registrar_resposta(
            "ana", "gestor", "qual a ocupacao hoje?", "SELECT 1", "correto",
            reg["id_interacao"], motor="oracle", resultado=(["x"], [(1,)]), caminho=trilha,
        )
        assert reg2["evento"] == "correto" and reg2["sql"] == "SELECT 1"
        assert reg2["hash_anterior"] == reg["hash"] and reg2["n_linhas"] == 1
        assert reg2["hash_resultado"] == hash_resultado(["x"], [(1,)])
        # interacao bloqueada: sem resultado, com controle e motivo.
        reg3 = registrar_pergunta("bia", "enfermagem", "cpf dos pacientes", caminho=trilha)
        registrar_resposta(
            "bia", "enfermagem", "cpf dos pacientes", "SELECT * FROM silver.paciente",
            "bloqueado", reg3["id_interacao"], motor="oracle",
            controle="CTRL-GOV-004", motivo="camada interna", caminho=trilha,
        )
        # entrada sem saida: interacao incompleta, cadeia integra.
        registrar_pergunta("caio", "gestor", "sem resposta", caminho=trilha)
        # dado pessoal na pergunta nunca chega ao arquivo, mesmo sem o filtro
        # explicito no chamador (CTRL-GOV-008).
        reg4 = registrar_pergunta("dora", "gestor", "o CPF 123.456.789-09 esta internado?", caminho=trilha)
        assert "123.456.789-09" not in reg4["pergunta"] and config.MASCARA_PII in reg4["pergunta"]
        assert "123.456.789-09" not in trilha.read_text(encoding="utf-8")
        v = verificar_trilha(trilha)
        assert v["integra"] and v["quebra"] is None and v["registros"] == 6
        completas = [i for i in v["interacoes"].values() if i["completa"]]
        assert len(v["interacoes"]) == 4 and len(completas) == 2
        # adulteracao: trocar um caractere da SQL do segundo registro quebra a
        # cadeia exatamente nele, e os registros seguintes continuam avaliaveis.
        linhas = trilha.read_text(encoding="utf-8").splitlines()
        linhas[1] = linhas[1].replace("SELECT 1", "SELECT 2")
        trilha.write_text("\n".join(linhas) + "\n", encoding="utf-8")
        v = verificar_trilha(trilha)
        assert not v["integra"] and v["quebra"] == 2, v
        # remocao de um registro do meio tambem e detectada.
        linhas = trilha.read_text(encoding="utf-8").splitlines()
        del linhas[2]
        trilha.write_text("\n".join(linhas) + "\n", encoding="utf-8")
        assert not verificar_trilha(trilha)["integra"]

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

    # Nota: o isolamento fisico da Gold (CTRL-GOV-007) e verificado em
    # src.pipeline, que gera os dados; aqui a analise roda sem banco.
    print("governance: autoteste OK")
    print(f"  {len(validos)} casos validos aprovados, {len(bloqueados)} casos bloqueados")
    print(f"  CTRL-GOV-008: {len(com_pii)} perguntas com dado pessoal barradas e mascaradas, "
          f"{len(sem_pii)} sem falso positivo; a trilha nunca guarda o dado")
    print("  validacao de saida: aterramento e filtro sensivel barram; saida limpa passa")
    print("  trilha de auditoria: horario real + data de simulacao, encadeada por hash;")
    print("    adulteracao e remocao de registro detectadas por verificar_trilha")
    print(f"  arquivo real: {config.AUDIT_LOG_PATH}")


if __name__ == "__main__":
    _autoteste()
