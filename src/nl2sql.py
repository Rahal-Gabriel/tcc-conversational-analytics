"""Camada 3: motor Text-to-SQL. Traduz pergunta em portugues para SQL Gold.

O motor existe em tres implementacoes intercambiaveis (DA-NL2SQL-001 e 003):

- **Oraculo**: devolve a SQL de referencia da propria pergunta. Nao usa chave e
  serve so para o autoteste da tubulacao. Nunca e apresentado como desempenho do
  modelo (RNC-002).
- **LLM via API**: traducao real via API Anthropic (motor dos Resultados
  Preliminares). Exige chave no ambiente (RNC-004).
- **Local**: traducao real por modelo aberto servido pelo Ollama na propria
  maquina (motor da fase de conclusao). Nada sai do perimetro e nao ha custo.

Os dois motores reais montam o prompt com o schema da Gold e a data de
referencia (DA-NL2SQL-002), exigem uma unica SQL somente leitura e geram os
numeros reportados no TCC. O prompt e uma variavel experimental
(DA-NL2SQL-004): a `VariantePrompt` controla a descricao do schema (simples ou
enriquecida), o value linking (valores distintos das colunas categoricas) e o
schema por perfil (so as tabelas autorizadas ao usuario) e, na Etapa E, a
instrucao de recusa (abstencao pelo modelo). As celulas da matriz da Etapa D
estao pre-registradas em `config.CELULAS`; as da Etapa E, em `config.CELULAS_E`.

As chamadas HTTP usam apenas a biblioteca padrao (`urllib`, DA-ARQ-003). A SQL
produzida ainda passa pelos guardrails de entrada e pela validacao de saida; o
motor nao executa nada.

Uso isolado:
    python -m src.nl2sql
"""

import datetime
import json
import time
import urllib.error
import urllib.request
from collections import OrderedDict
from dataclasses import asdict, dataclass

from src import config, questions


# Variantes de prompt (DA-NL2SQL-004)

@dataclass(frozen=True)
class VariantePrompt:
    """Configuracao do prompt, pre-registrada por celula em config.CELULAS.

    - descricao: "simples" (uma linha por tabela com os nomes das colunas, o
      prompt do preliminar) ou "enriquecida" (dialeto, tipo de cada coluna,
      nota por tabela e unidade das colunas, de config.GOLD_NOTAS);
    - value_linking: lista os valores distintos das colunas VARCHAR com ate
      config.VALUE_LINKING_MAX_VALORES valores (ficha 07, caminho 1);
    - schema_por_perfil: mostra so as tabelas de config.PERFIS[perfil] e avisa
      que nenhuma outra existe para o usuario (Role-Schema, caminho 2);
    - instrucao_recusa: acrescenta config.INSTRUCAO_RECUSA a instrucao de
      sistema, informando que responder RECUSA e uma saida valida (Etapa E).
    """

    descricao: str = "simples"
    value_linking: bool = False
    schema_por_perfil: bool = False
    celula: str = None
    instrucao_recusa: bool = False

    def __post_init__(self):
        if self.descricao not in ("simples", "enriquecida"):
            raise ValueError(f"descricao desconhecida: {self.descricao!r}")

    @classmethod
    def da_celula(cls, nome):
        """Constroi a variante da celula pre-registrada `nome` ('C2', 'E1', ...).

        As celulas da Etapa E (config.CELULAS_E) herdam a variante da celula
        base da Etapa D e so acrescentam a instrucao de recusa.
        """
        for c in config.CELULAS:
            if c["celula"] == nome:
                return cls(c["descricao"], c["value_linking"], c["schema_por_perfil"], nome)
        for c in config.CELULAS_E:
            if c["celula"] == nome:
                base = cls.da_celula(c["base"])
                return cls(base.descricao, base.value_linking, base.schema_por_perfil, nome,
                           c["instrucao_recusa"])
        conhecidas = [c["celula"] for c in config.CELULAS] + [c["celula"] for c in config.CELULAS_E]
        raise ValueError(f"celula desconhecida: {nome!r} (use uma de {conhecidas})")

    def como_dict(self):
        return asdict(self)


VARIANTE_PRELIMINAR = VariantePrompt()  # o prompt dos Resultados Preliminares


def introspectar_gold(con):
    """Le o schema da Gold no banco: tabela -> lista de (coluna, tipo, valores).

    Usa information_schema para o prompt ficar fiel ao que existe, na ordem
    das colunas. `valores` e a lista ordenada dos valores distintos quando a
    coluna e VARCHAR com ate config.VALUE_LINKING_MAX_VALORES valores; caso
    contrario e None. A leitura dos valores e uma consulta agregada sobre a
    Gold ja minimizada (nenhum dado pessoal, RNC-005).
    """
    linhas = con.execute(
        "SELECT table_name, column_name, data_type FROM information_schema.columns "
        "WHERE table_schema = 'gold' ORDER BY table_name, ordinal_position"
    ).fetchall()
    tabelas = OrderedDict()
    for tabela, coluna, tipo in linhas:
        valores = None
        if tipo == "VARCHAR":
            n = con.execute(f'SELECT COUNT(DISTINCT "{coluna}") FROM gold."{tabela}"').fetchone()[0]
            if n <= config.VALUE_LINKING_MAX_VALORES:
                valores = [
                    r[0] for r in con.execute(
                        f'SELECT DISTINCT "{coluna}" FROM gold."{tabela}" '
                        f'WHERE "{coluna}" IS NOT NULL ORDER BY 1'
                    ).fetchall()
                ]
        tabelas.setdefault(tabela, []).append((coluna, tipo, valores))
    return tabelas


def _tabelas_visiveis(schema, perfil, variante):
    """Aplica o Role-Schema: so as tabelas do perfil, na ordem da Gold."""
    if not variante.schema_por_perfil:
        return schema
    autorizadas = {t.split(".", 1)[1] for t in config.PERFIS[perfil]}
    return OrderedDict((t, cols) for t, cols in schema.items() if t in autorizadas)


def _valores_texto(valores):
    return "{" + ", ".join(str(v) for v in valores) + "}"


def descrever_schema(schema, perfil=None, variante=VARIANTE_PRELIMINAR):
    """Renderiza a descricao textual do schema conforme a variante.

    Simples: `gold.tabela(col1, col2, ...)`, uma linha por tabela (com value
    linking, os valores seguem o nome da coluna). Enriquecida: cabecalho com o
    dialeto, e por tabela a nota de config.GOLD_NOTAS e uma linha por coluna
    com tipo, unidade e, com value linking, os valores distintos.
    """
    visiveis = _tabelas_visiveis(schema, perfil, variante)
    if variante.descricao == "simples":
        linhas = []
        for t, cols in visiveis.items():
            partes = []
            for coluna, _tipo, valores in cols:
                if variante.value_linking and valores is not None:
                    partes.append(f"{coluna} {_valores_texto(valores)}")
                else:
                    partes.append(coluna)
            linhas.append(f"gold.{t}({', '.join(partes)})")
        return "\n".join(linhas)

    linhas = ["Dialeto: DuckDB (sintaxe SQL padrao, compativel com PostgreSQL)."]
    for t, cols in visiveis.items():
        notas = config.GOLD_NOTAS.get(f"gold.{t}", {})
        cabecalho = f"gold.{t}"
        if notas.get("tabela"):
            cabecalho += f": {notas['tabela']}"
        linhas.append(cabecalho)
        for coluna, tipo, valores in cols:
            linha = f"  - {coluna} {tipo}"
            nota = notas.get("colunas", {}).get(coluna)
            if nota:
                linha += f" ({nota})"
            if variante.value_linking and valores is not None:
                linha += f" {_valores_texto(valores)}"
            linhas.append(linha)
    return "\n".join(linhas)


def descrever_schema_gold(con, perfil=None, variante=VARIANTE_PRELIMINAR):
    """Introspecta a Gold e devolve a descricao textual (atalho de conveniencia)."""
    return descrever_schema(introspectar_gold(con), perfil, variante)


# Instrucao de sistema: define o papel e o contrato de saida (DA-NL2SQL-002).
# As duas ultimas frases sao esclarecimentos de especificacao, nao ajuste de
# resposta: projetar so o necessario alinha a saida ao que a pergunta pede (o
# execution match compara o conjunto de colunas), e nao arredondar deixa a
# tolerancia numerica a cargo do harness (evaluate.CASAS_DECIMAIS). O texto e
# o mesmo dos Resultados Preliminares e nao varia entre celulas.
_PROMPT_SISTEMA = (
    "Voce traduz perguntas em portugues para uma unica consulta SQL somente "
    "leitura sobre um banco DuckDB. Responda apenas com a SQL, sem markdown e sem "
    "explicacao. Use somente as tabelas e colunas do schema fornecido. A consulta "
    "deve ser um unico SELECT (ou WITH ... SELECT), sem ponto e virgula ao final. "
    "Projete apenas as colunas necessarias para responder a pergunta, sem colunas "
    "extras. Nao arredonde valores agregados; devolva o valor calculado."
)

# Frase do Role-Schema: informa a restricao sem descrever a politica (o
# verificador determinista continua sendo quem garante o escopo).
_AVISO_PERFIL = (
    "Somente as tabelas listadas acima existem para este usuario; nao use "
    "nenhuma outra tabela."
)


def prompt_sistema(variante=None):
    """Instrucao de sistema da variante: a base fixa e, na Etapa E, a recusa."""
    if variante is not None and variante.instrucao_recusa:
        return f"{_PROMPT_SISTEMA} {config.INSTRUCAO_RECUSA}"
    return _PROMPT_SISTEMA


def montar_prompt_usuario(pergunta_texto, schema_texto, schema_por_perfil=False):
    """Monta o prompt do usuario com o schema Gold e a data de referencia."""
    aviso = f"{_AVISO_PERFIL}\n\n" if schema_por_perfil else ""
    return (
        "Schema disponivel (camada Gold):\n"
        f"{schema_texto}\n\n"
        f"{aviso}"
        f"Data de referencia (hoje): {config.SIM_TODAY.isoformat()}. Ancore qualquer "
        "mencao a \"hoje\" ou \"agora\" nesta data.\n\n"
        f"Pergunta: {pergunta_texto}"
    )


def _extrair_sql(texto):
    """Extrai a SQL pura da resposta do modelo, tolerando cercas de markdown."""
    t = texto.strip()
    if t.startswith("```"):
        linhas = t.splitlines()[1:]  # descarta a cerca de abertura (```sql ou ```)
        if linhas and linhas[-1].strip().startswith("```"):
            linhas = linhas[:-1]
        t = "\n".join(linhas)
    return t.strip()


def _agora_utc():
    return datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")


# Motores

class MotorOraculo:
    """Devolve a SQL de referencia da pergunta (autoteste da tubulacao).

    Nao usa chave nem banco. Levanta KeyError se a pergunta nao estiver no
    conjunto de avaliacao, sinal de erro no harness, nao no modelo. Aceita a
    variante so para que a matriz possa ser exercitada sem modelo.
    """

    nome = "oracle"
    modelo = "oracle"

    def __init__(self, variante=None):
        self.variante = variante or VARIANTE_PRELIMINAR
        self.ultima_chamada = None

    def gerar_sql(self, pergunta_texto, perfil):
        for p in questions.CONJUNTO_COMBINADO:
            if p.texto == pergunta_texto:
                # Pergunta a recusar: o oraculo se abstem (a resposta de
                # referencia e nao responder).
                return p.sql_ref if p.esperado == "responder" else config.MARCADOR_RECUSA
        raise KeyError(f"pergunta fora do conjunto de avaliacao: {pergunta_texto!r}")

    def descrever_ambiente(self):
        return {"motor": self.nome}


class _MotorReal:
    """Base dos motores reais: prompt por variante, schema em cache por perfil,
    telemetria da ultima chamada (tokens, latencia, horario UTC)."""

    nome = None
    modelo = None

    def __init__(self, variante=None):
        self.variante = variante or VARIANTE_PRELIMINAR
        self._schema = None
        self._descricoes = {}
        self.ultima_chamada = None

    def _schema_gold(self):
        if self._schema is None:
            from src import governance

            con = governance.conectar_somente_leitura()
            try:
                self._schema = introspectar_gold(con)
            finally:
                con.close()
        return self._schema

    def descrever_schema(self, perfil):
        """Descricao do schema para o perfil, conforme a variante (com cache)."""
        chave = perfil if self.variante.schema_por_perfil else None
        if chave not in self._descricoes:
            self._descricoes[chave] = descrever_schema(self._schema_gold(), perfil, self.variante)
        return self._descricoes[chave]

    def montar_prompt(self, pergunta_texto, perfil):
        return montar_prompt_usuario(
            pergunta_texto, self.descrever_schema(perfil), self.variante.schema_por_perfil
        )

    def gerar_sql(self, pergunta_texto, perfil):
        prompt_usuario = self.montar_prompt(pergunta_texto, perfil)
        momento = _agora_utc()
        inicio = time.perf_counter()
        texto, tokens_entrada, tokens_saida = self._chamar(prompt_usuario)
        self.ultima_chamada = {
            "momento_utc": momento,
            "latencia_ms": round((time.perf_counter() - inicio) * 1000),
            "tokens_entrada": tokens_entrada,
            "tokens_saida": tokens_saida,
        }
        return _extrair_sql(texto)

    def _chamar(self, prompt_usuario):
        raise NotImplementedError

    def descrever_ambiente(self):
        return {"motor": self.nome, "modelo": self.modelo}


def _post_json(url, corpo, cabecalhos=None, timeout=None):
    req = urllib.request.Request(url, data=json.dumps(corpo).encode("utf-8"), method="POST")
    req.add_header("content-type", "application/json")
    for k, v in (cabecalhos or {}).items():
        req.add_header(k, v)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _get_json(url, timeout=None):
    with urllib.request.urlopen(url, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


class MotorLLM(_MotorReal):
    """Traducao real via API Anthropic (motor dos Resultados Preliminares)."""

    nome = "llm"

    def __init__(self, variante=None):
        if not config.ANTHROPIC_API_KEY:
            raise RuntimeError(
                "ANTHROPIC_API_KEY ausente no ambiente; o motor LLM exige chave "
                "valida (RNC-004). Use o motor oraculo para o autoteste sem custo."
            )
        super().__init__(variante)
        self.modelo = config.ANTHROPIC_MODEL

    def _chamar(self, prompt_usuario):
        corpo = {
            "model": config.ANTHROPIC_MODEL,
            "max_tokens": 1024,
            # Temperatura zero: reduz a variabilidade entre execucoes e melhora a
            # reprodutibilidade do numero reportado (ainda assim, a chamada a um LLM
            # externo nao e deterministica como o restante do pipeline).
            "temperature": 0,
            "system": prompt_sistema(self.variante),
            "messages": [{"role": "user", "content": prompt_usuario}],
        }
        payload = _post_json(
            config.ANTHROPIC_ENDPOINT, corpo,
            {"anthropic-version": config.ANTHROPIC_VERSION, "x-api-key": config.ANTHROPIC_API_KEY},
        )
        texto = "".join(
            bloco.get("text", "") for bloco in payload.get("content", []) if bloco.get("type") == "text"
        )
        uso = payload.get("usage", {})
        return texto, uso.get("input_tokens"), uso.get("output_tokens")


def ollama_disponivel(timeout=2):
    """Verdadeiro se o servidor do Ollama responde no endpoint configurado."""
    try:
        _get_json(f"{config.OLLAMA_ENDPOINT}/api/version", timeout=timeout)
        return True
    except (urllib.error.URLError, OSError, ValueError):
        return False


class MotorLocal(_MotorReal):
    """Traducao real por modelo aberto servido localmente pelo Ollama (DA-NL2SQL-003).

    Chama `POST /api/chat` sem streaming, com temperatura zero e a SEED do
    projeto na amostragem. Le do proprio servidor a versao e o digest do modelo
    (procedencia dos numeros: quais pesos exatamente responderam).
    """

    nome = "local"

    def __init__(self, variante=None):
        if not ollama_disponivel():
            raise RuntimeError(
                f"servidor do Ollama nao responde em {config.OLLAMA_ENDPOINT}; inicie-o "
                "(app do Ollama ou `ollama serve`) e confira `ollama pull "
                f"{config.MODELO_LOCAL}`. Use o motor oraculo para o autoteste sem modelo."
            )
        super().__init__(variante)
        self.modelo = config.MODELO_LOCAL

    def _chamar(self, prompt_usuario):
        corpo = {
            "model": config.MODELO_LOCAL,
            "stream": False,
            "messages": [
                {"role": "system", "content": prompt_sistema(self.variante)},
                {"role": "user", "content": prompt_usuario},
            ],
            "options": {
                "temperature": 0,
                "seed": config.SEED,
                "num_ctx": config.OLLAMA_NUM_CTX,
                "num_predict": config.OLLAMA_NUM_PREDICT,
            },
        }
        payload = _post_json(f"{config.OLLAMA_ENDPOINT}/api/chat", corpo, timeout=config.OLLAMA_TIMEOUT_S)
        texto = payload.get("message", {}).get("content", "")
        return texto, payload.get("prompt_eval_count"), payload.get("eval_count")

    def descrever_ambiente(self):
        """Versao do servidor e identidade dos pesos (digest, tamanho, quantizacao)."""
        amb = {"motor": self.nome, "modelo": self.modelo, "endpoint": config.OLLAMA_ENDPOINT,
               "seed": config.SEED, "num_ctx": config.OLLAMA_NUM_CTX}
        try:
            amb["ollama_versao"] = _get_json(f"{config.OLLAMA_ENDPOINT}/api/version", timeout=5).get("version")
            for m in _get_json(f"{config.OLLAMA_ENDPOINT}/api/tags", timeout=5).get("models", []):
                if m.get("name") == config.MODELO_LOCAL or m.get("model") == config.MODELO_LOCAL:
                    det = m.get("details", {})
                    amb.update({
                        "digest": m.get("digest"),
                        "tamanho_bytes": m.get("size"),
                        "parametros": det.get("parameter_size"),
                        "quantizacao": det.get("quantization_level"),
                        "familia": det.get("family"),
                    })
        except (urllib.error.URLError, OSError, ValueError) as exc:
            amb["aviso"] = f"ambiente parcial: {type(exc).__name__}"
        return amb


MOTORES = {"oracle": MotorOraculo, "llm": MotorLLM, "local": MotorLocal}


def obter_motor(nome, variante=None):
    """Devolve a instancia do motor pedido ('oracle', 'llm' ou 'local').

    `variante` pode ser uma VariantePrompt ou o nome de uma celula ('C2').
    """
    if isinstance(variante, str):
        variante = VariantePrompt.da_celula(variante)
    try:
        return MOTORES[nome](variante)
    except KeyError:
        raise ValueError(f"motor desconhecido: {nome!r} (use um de {list(MOTORES)})") from None


def _autoteste():
    """Oraculo confere as perguntas; as celulas renderizam como pre-registrado."""
    from src import data_gen, governance, pipeline

    oraculo = obter_motor("oracle")
    for p in questions.CONJUNTO:
        sql = oraculo.gerar_sql(p.texto, p.perfil)
        assert sql == p.sql_ref, f"oraculo divergiu em {p.id}"

    if not (config.DB_PATH.exists() and config.GOLD_DB_PATH.exists()):
        data_gen.construir()
        pipeline.construir()
    con = governance.conectar_somente_leitura()
    try:
        schema = introspectar_gold(con)
    finally:
        con.close()
    assert set(f"gold.{t}" for t in schema) == set(config.GOLD_TABLES)

    # Cada celula e uma configuracao distinta; C0 e exatamente o prompt antigo.
    render = {c["celula"]: descrever_schema(schema, "enfermagem", VariantePrompt.da_celula(c["celula"]))
              for c in config.CELULAS}
    assert len(set(render.values())) == len(render), "duas celulas renderizam o mesmo prompt"
    assert render["C0"].splitlines()[0].startswith("gold.internacoes(") and "{" not in render["C0"]
    assert render["C1"].startswith("Dialeto: DuckDB") and "percentual, 0 a 100" in render["C1"]
    assert "{" not in render["C1"] and "{Enfermaria, Semi-intensiva, UTI}" in render["C2"]
    assert "{bloqueado, livre, ocupado}" in render["C2"]
    assert "ocupacao_diaria" not in render["C3"] and "ocupacao_diaria" in render["C1"]
    assert "leitos_status" in render["C4"] and "{0-17, 18-39" not in render["C4"]  # internacoes fora da enfermagem
    assert "{0-17, 18-39" in descrever_schema(schema, "gestor", VariantePrompt.da_celula("C4"))
    prompt_c3 = montar_prompt_usuario("teste", render["C3"], schema_por_perfil=True)
    assert _AVISO_PERFIL in prompt_c3 and _AVISO_PERFIL not in montar_prompt_usuario("teste", render["C1"])
    assert VariantePrompt.da_celula("C0") == VariantePrompt(celula="C0")
    # Etapa E: E0 e C3 sem nada a mais; E1 so acrescenta a instrucao de recusa.
    e0, e1 = VariantePrompt.da_celula("E0"), VariantePrompt.da_celula("E1")
    c3 = VariantePrompt.da_celula("C3")
    assert (e0.descricao, e0.value_linking, e0.schema_por_perfil) == (c3.descricao, c3.value_linking, c3.schema_por_perfil)
    assert not e0.instrucao_recusa and e1.instrucao_recusa and e1.celula == "E1"
    assert descrever_schema(schema, "enfermagem", e1) == render["C3"]
    assert prompt_sistema(e0) == _PROMPT_SISTEMA and prompt_sistema(None) == _PROMPT_SISTEMA
    assert prompt_sistema(e1).startswith(_PROMPT_SISTEMA) and prompt_sistema(e1).endswith(config.MARCADOR_RECUSA + ".")
    # O oraculo se abstem nas perguntas adversariais.
    adv = questions.ADVERSARIAL[0]
    assert oraculo.gerar_sql(adv.texto, adv.perfil) == config.MARCADOR_RECUSA

    print("nl2sql: autoteste OK")
    print(f"  motor oraculo confere as {len(questions.CONJUNTO)} perguntas")
    print(f"  {len(config.CELULAS)} celulas renderizam prompts distintos; C0 e o prompt do preliminar")
    print(f"  celulas da Etapa E: E0 = C3; E1 = C3 + instrucao de recusa "
          f"({len(prompt_sistema(e1)) - len(_PROMPT_SISTEMA)} caracteres a mais na instrucao de sistema)")
    for nome, texto in render.items():
        print(f"    {nome}: {len(texto)} caracteres, {len(texto.splitlines())} linhas (perfil enfermagem)")

    # Os motores reais so sao exercitados quando ha chave ou servidor; a CI nunca os executa.
    exemplo = questions.CONJUNTO[1]
    if config.ANTHROPIC_API_KEY:
        sql = obter_motor("llm").gerar_sql(exemplo.texto, exemplo.perfil)
        print(f"  motor LLM (API) respondeu {exemplo.id}: {sql[:60]}...")
    else:
        print("  motor LLM (API) pulado (sem ANTHROPIC_API_KEY no ambiente)")
    if ollama_disponivel():
        motor = obter_motor("local", "C2")
        sql = motor.gerar_sql(exemplo.texto, exemplo.perfil)
        print(f"  motor local ({motor.modelo}, C2) respondeu {exemplo.id}: {sql[:60]}...")
        print(f"    {motor.ultima_chamada}")
    else:
        print(f"  motor local pulado (Ollama nao responde em {config.OLLAMA_ENDPOINT})")


if __name__ == "__main__":
    _autoteste()
