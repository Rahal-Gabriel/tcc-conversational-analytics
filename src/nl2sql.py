"""Camada 3: motor Text-to-SQL. Traduz pergunta em portugues para SQL Gold.

O motor existe em duas implementacoes intercambiaveis (DA-NL2SQL-001):

- **Oraculo**: devolve a SQL de referencia da propria pergunta. Nao usa chave e
  serve so para o autoteste da tubulacao. Nunca e apresentado como desempenho do
  modelo (RNC-002).
- **LLM**: traducao real via API Anthropic. Monta o prompt com o schema da Gold e
  a data de referencia (DA-NL2SQL-002), exige uma unica SQL somente leitura, e
  gera os numeros reportados no TCC.

A chamada HTTP usa apenas a biblioteca padrao (`urllib`, DA-ARQ-003) e le a chave
do ambiente, nunca do codigo (RNC-004). A SQL produzida ainda passa pelos
guardrails de entrada e pela validacao de saida; o motor nao executa nada.

Uso isolado:
    python -m src.nl2sql
"""

import json
import urllib.request
from collections import OrderedDict

from src import config, questions


def descrever_schema_gold(con):
    """Monta a descricao textual do schema Gold a partir do banco.

    Introspecta as colunas via information_schema para o prompt ficar fiel ao que
    existe de fato, na ordem das colunas. Devolve uma linha por tabela, no formato
    `gold.tabela(col1, col2, ...)`.
    """
    linhas = con.execute(
        "SELECT table_name, column_name FROM information_schema.columns "
        "WHERE table_schema = 'gold' ORDER BY table_name, ordinal_position"
    ).fetchall()
    tabelas = OrderedDict()
    for tabela, coluna in linhas:
        tabelas.setdefault(tabela, []).append(coluna)
    return "\n".join(f"gold.{t}({', '.join(cols)})" for t, cols in tabelas.items())


# Instrucao de sistema: define o papel e o contrato de saida (DA-NL2SQL-002).
# As duas ultimas frases sao esclarecimentos de especificacao, nao ajuste de
# resposta: projetar so o necessario alinha a saida ao que a pergunta pede (o
# execution match compara o conjunto de colunas), e nao arredondar deixa a
# tolerancia numerica a cargo do harness (evaluate.CASAS_DECIMAIS).
_PROMPT_SISTEMA = (
    "Voce traduz perguntas em portugues para uma unica consulta SQL somente "
    "leitura sobre um banco DuckDB. Responda apenas com a SQL, sem markdown e sem "
    "explicacao. Use somente as tabelas e colunas do schema fornecido. A consulta "
    "deve ser um unico SELECT (ou WITH ... SELECT), sem ponto e virgula ao final. "
    "Projete apenas as colunas necessarias para responder a pergunta, sem colunas "
    "extras. Nao arredonde valores agregados; devolva o valor calculado."
)


def montar_prompt_usuario(pergunta_texto, schema_texto):
    """Monta o prompt do usuario com o schema Gold e a data de referencia."""
    return (
        "Schema disponivel (camada Gold):\n"
        f"{schema_texto}\n\n"
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


class MotorOraculo:
    """Devolve a SQL de referencia da pergunta (autoteste da tubulacao).

    Nao usa chave nem banco. Levanta KeyError se a pergunta nao estiver no
    conjunto de avaliacao, sinal de erro no harness, nao no modelo.
    """

    nome = "oracle"

    def gerar_sql(self, pergunta_texto, perfil):
        for p in questions.CONJUNTO:
            if p.texto == pergunta_texto:
                return p.sql_ref
        raise KeyError(f"pergunta fora do conjunto de avaliacao: {pergunta_texto!r}")


class MotorLLM:
    """Traducao real via API Anthropic. Gera os numeros do TCC (RNC-002).

    O schema Gold e introspectado uma vez (cache), em conexao somente leitura.
    """

    nome = "llm"

    def __init__(self):
        if not config.ANTHROPIC_API_KEY:
            raise RuntimeError(
                "ANTHROPIC_API_KEY ausente no ambiente; o motor LLM exige chave "
                "valida (RNC-004). Use o motor oraculo para o autoteste sem custo."
            )
        self._schema = None

    def _schema_gold(self):
        if self._schema is None:
            from src import governance

            con = governance.conectar_somente_leitura()
            try:
                self._schema = descrever_schema_gold(con)
            finally:
                con.close()
        return self._schema

    def gerar_sql(self, pergunta_texto, perfil):
        prompt_usuario = montar_prompt_usuario(pergunta_texto, self._schema_gold())
        resposta = self._chamar_api(prompt_usuario)
        return _extrair_sql(resposta)

    def _chamar_api(self, prompt_usuario):
        """Faz a chamada HTTP ao endpoint de mensagens e devolve o texto gerado."""
        corpo = {
            "model": config.ANTHROPIC_MODEL,
            "max_tokens": 1024,
            "system": _PROMPT_SISTEMA,
            "messages": [{"role": "user", "content": prompt_usuario}],
        }
        req = urllib.request.Request(
            config.ANTHROPIC_ENDPOINT,
            data=json.dumps(corpo).encode("utf-8"),
            method="POST",
        )
        req.add_header("content-type", "application/json")
        req.add_header("anthropic-version", config.ANTHROPIC_VERSION)
        req.add_header("x-api-key", config.ANTHROPIC_API_KEY)
        with urllib.request.urlopen(req) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
        partes = [
            bloco.get("text", "")
            for bloco in payload.get("content", [])
            if bloco.get("type") == "text"
        ]
        return "".join(partes)


def obter_motor(nome):
    """Devolve a instancia do motor pedido: 'oracle' ou 'llm'."""
    if nome == "oracle":
        return MotorOraculo()
    if nome == "llm":
        return MotorLLM()
    raise ValueError(f"motor desconhecido: {nome!r} (use 'oracle' ou 'llm')")


def _autoteste():
    """Confere que o oraculo devolve a SQL de referencia de cada pergunta."""
    oraculo = obter_motor("oracle")
    for p in questions.CONJUNTO:
        sql = oraculo.gerar_sql(p.texto, p.perfil)
        assert sql == p.sql_ref, f"oraculo divergiu em {p.id}"

    print("nl2sql: autoteste OK")
    print(f"  motor oraculo confere as {len(questions.CONJUNTO)} perguntas")

    # O motor LLM so e exercitado quando ha chave; a CI nunca o executa.
    if config.ANTHROPIC_API_KEY:
        motor = obter_motor("llm")
        exemplo = questions.CONJUNTO[0]
        sql = motor.gerar_sql(exemplo.texto, exemplo.perfil)
        print(f"  motor LLM respondeu {exemplo.id}: {sql[:60]}...")
    else:
        print("  motor LLM pulado (sem ANTHROPIC_API_KEY no ambiente)")


if __name__ == "__main__":
    _autoteste()
