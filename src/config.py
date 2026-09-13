"""Parametros centrais do prototipo.

Tudo que controla geracao de dados, governanca e avaliacao mora aqui. Nenhum
valor magico deve ser espalhado pelos outros modulos. Importe deste arquivo.
"""

import os
from datetime import date
from pathlib import Path

# Determinismo e reprodutibilidade

# Data de referencia da simulacao. Toda consulta que menciona "hoje" ou "agora"
# e toda a geracao de dados se ancoram nesta data, e nao no relogio do sistema.
SIM_TODAY_ISO = "2026-05-31"
SIM_TODAY = date.fromisoformat(SIM_TODAY_ISO)

# Tamanho da janela historica diaria (em dias) gerada ate SIM_TODAY, inclusive.
HIST_DAYS = 90

# Semente unica que governa Faker e qualquer sorteio. Mantenha fixa.
SEED = 42

# Volumes sinteticos (aproximados; o numero de internacoes e alvo, nao exato)

VOL_UNIDADES = 8
VOL_LEITOS = 200
VOL_PACIENTES = 600
VOL_INTERNACOES = 2200

# Caminhos (data/ e results/ nao sao versionados)

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
RESULTS_DIR = BASE_DIR / "results"
DB_PATH = DATA_DIR / "lakehouse.duckdb"
# Arquivo separado que contem APENAS a camada Gold (DA-LAKE-005). E a unica
# base a que o motor e o avaliador se conectam: Bronze e Silver nao existem
# fisicamente para quem consulta por aqui, seja qual for a SQL (RNC-005).
GOLD_DB_PATH = DATA_DIR / "gold_isolada.duckdb"
AUDIT_LOG_PATH = RESULTS_DIR / "auditoria.log"

# Modelo de dados Gold (unica camada exposta ao motor de linguagem)

GOLD_TABLES = (
    "gold.leitos_status",
    "gold.ocupacao_unidade",
    "gold.ocupacao_diaria",
    "gold.internacoes",
)

# Faixas etarias derivadas na Silver (limite inferior inclusivo)
FAIXAS_ETARIAS = ("0-17", "18-39", "40-59", "60-79", "80+")

# Salt determinista da pseudonimizacao de id_paciente na Silver. Por se tratar
# de dado 100% sintetico, o salt mora no codigo de proposito: sem ele a
# reprodutibilidade (RNC-003) se perderia. Em producao com dado real, viria de
# um cofre de segredos. Com salt, reverter o hash dos poucos ids por forca bruta
# deixa de ser trivial (RNC-005).
PSEUDO_SALT = "tcc-leitos-2026"

# Campos sensiveis que jamais podem aparecer na saida ao usuario final
CAMPOS_SENSIVEIS = ("nome", "cpf", "data_nascimento", "id_paciente_pseudo")

# Governanca de acesso: cada perfil so enxerga as tabelas Gold autorizadas

PERFIS = {
    "gestor": GOLD_TABLES,  # acesso a todas as tabelas Gold
    "enfermagem": (
        "gold.leitos_status",
        "gold.ocupacao_unidade",
    ),
    "administrativo": (
        "gold.ocupacao_unidade",
        "gold.ocupacao_diaria",
    ),
}

# Configuracao do LLM (lida do ambiente; nunca embutir chave no codigo)

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")
ANTHROPIC_MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-6")
ANTHROPIC_ENDPOINT = "https://api.anthropic.com/v1/messages"
ANTHROPIC_VERSION = "2023-06-01"


def _autoteste():
    """Checagem rapida de invariantes da configuracao."""
    assert SIM_TODAY.isoformat() == SIM_TODAY_ISO
    assert HIST_DAYS > 0 and SEED >= 0
    assert all(v > 0 for v in (VOL_UNIDADES, VOL_LEITOS, VOL_PACIENTES, VOL_INTERNACOES))
    # Todo perfil so pode autorizar tabelas Gold conhecidas.
    for perfil, tabelas in PERFIS.items():
        assert tabelas, f"perfil sem tabelas: {perfil}"
        for t in tabelas:
            assert t in GOLD_TABLES, f"tabela desconhecida no perfil {perfil}: {t}"
    print("config: autoteste OK")
    print(f"  SIM_TODAY={SIM_TODAY_ISO}  HIST_DAYS={HIST_DAYS}  SEED={SEED}")
    print(
        f"  volumes: {VOL_UNIDADES} unidades, {VOL_LEITOS} leitos, "
        f"{VOL_PACIENTES} pacientes, ~{VOL_INTERNACOES} internacoes"
    )
    print(f"  perfis: {', '.join(PERFIS)}")
    print(f"  modelo LLM: {ANTHROPIC_MODEL}")
    print(f"  chave no ambiente: {'sim' if ANTHROPIC_API_KEY else 'nao'}")


if __name__ == "__main__":
    _autoteste()
