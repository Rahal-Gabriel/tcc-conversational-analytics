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

# Chave da pseudonimizacao de id_paciente na Silver (HMAC-SHA256, DA-LAKE-006).
# Hash simples e hash com salt embutido sao considerados fracos contra forca
# bruta quando o dominio do identificador e pequeno (ENISA 2022); a chave e a
# "informacao adicional" que a LGPD (art. 13, par. 4) e o EDPB (01/2025) mandam
# guardar separada de quem processa o dado pseudonimizado. Por isso ela e lida
# do ambiente. O valor padrao existe SO porque o dado e 100% sintetico e a
# reprodutibilidade (RNC-003) exige pseudonimos estaveis entre execucoes; em
# producao, a variavel vem de um cofre e nunca do codigo (RNC-004).
PSEUDO_KEY = os.environ.get("PSEUDO_KEY", "tcc-leitos-2026-chave-sintetica")

# Campos sensiveis que jamais podem aparecer na saida ao usuario final
CAMPOS_SENSIVEIS = ("nome", "cpf", "data_nascimento", "id_paciente_pseudo")

# Minimizacao e risco de reidentificacao na Gold (DA-LAKE-006, CTRL-LAKE-001).
# Quase-identificadores de gold.internacoes: atributos que um terceiro poderia
# conhecer sobre uma pessoa (tipo de leito e faixa etaria). O pipeline verifica
# que todo grupo formado por eles tem pelo menos K_MINIMO linhas (k-anonimato).
# K_MINIMO = 5 e o limiar usual para liberacao interna e controlada (El Emam);
# o teste tambem reporta a fracao de linhas em grupos com k < 11, limiar de
# supressao de celula pequena do CMS, como referencia mais estrita.
QUASE_IDENTIFICADORES_INTERNACOES = ("tipo", "faixa_etaria")
K_MINIMO = 5

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
    assert PSEUDO_KEY and K_MINIMO >= 2 and QUASE_IDENTIFICADORES_INTERNACOES
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
    print(f"  pseudonimizacao: HMAC-SHA256, chave {'do ambiente' if 'PSEUDO_KEY' in os.environ else 'padrao (dado sintetico)'}")
    print(f"  k-anonimato Gold: k >= {K_MINIMO} sobre {QUASE_IDENTIFICADORES_INTERNACOES}")


if __name__ == "__main__":
    _autoteste()
