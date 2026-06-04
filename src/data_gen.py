"""Geracao sintetica dos dados brutos, materializados na camada Bronze.

Tudo e determinista: a mesma SEED e a mesma SIM_TODAY (definidas em config)
produzem exatamente o mesmo banco. A PII (nome, cpf, data_nascimento) existe de
proposito na tabela paciente, para que a anonimizacao na Silver seja real e
demonstravel. Nenhum dado real e usado em nenhuma etapa.

Uso isolado:
    python -m src.data_gen
"""

import random
from datetime import timedelta

import duckdb
from faker import Faker

from src import config

# Especialidades das oito unidades (uma por unidade).
ESPECIALIDADES = (
    "Cardiologia",
    "Pediatria",
    "Clinica Medica",
    "Cirurgia Geral",
    "Ortopedia",
    "Neurologia",
    "Oncologia",
    "Pronto-Socorro",
)

# Tipos de leito e seus pesos (Enfermaria mais comum, UTI mais rara).
TIPOS_LEITO = ("Enfermaria", "Semi-intensiva", "UTI")
PESOS_TIPO = (60, 25, 15)

# Fracao de leitos fora de servico (bloqueados em toda a janela).
FRACAO_BLOQUEADO = 0.05

# Faixa de tempo de permanencia (em dias) por tipo de leito.
LOS_POR_TIPO = {
    "UTI": (3, 20),
    "Semi-intensiva": (2, 12),
    "Enfermaria": (1, 10),
}

# Intervalo (em dias) entre uma alta e a proxima admissao no mesmo leito.
GAP_MAX = 4


def _janela():
    """Retorna (primeiro_dia, ultimo_dia) da janela historica, inclusive."""
    ultimo = config.SIM_TODAY
    primeiro = ultimo - timedelta(days=config.HIST_DAYS - 1)
    return primeiro, ultimo


def gerar_unidades():
    """Oito unidades, uma por especialidade, distribuidas em andares."""
    linhas = []
    for i, esp in enumerate(ESPECIALIDADES, start=1):
        andar = 1 + (i - 1) // 2  # duas unidades por andar
        linhas.append((i, f"Unidade {esp}", esp, andar))
    return linhas


def gerar_leitos(rng):
    """Distribui os leitos entre as unidades, com tipo e status."""
    linhas = []
    for id_leito in range(1, config.VOL_LEITOS + 1):
        id_unidade = 1 + (id_leito - 1) % config.VOL_UNIDADES
        tipo = rng.choices(TIPOS_LEITO, weights=PESOS_TIPO, k=1)[0]
        status = "bloqueado" if rng.random() < FRACAO_BLOQUEADO else "ativo"
        linhas.append((id_leito, id_unidade, tipo, status))
    return linhas


def gerar_pacientes(fake, rng):
    """Pacientes com PII proposital (nome, cpf, data_nascimento, sexo)."""
    linhas = []
    for id_paciente in range(1, config.VOL_PACIENTES + 1):
        sexo = rng.choice(("M", "F"))
        nome = fake.name_male() if sexo == "M" else fake.name_female()
        cpf = fake.cpf()
        nascimento = fake.date_of_birth(minimum_age=0, maximum_age=95)
        linhas.append((id_paciente, nome, cpf, nascimento, sexo))
    return linhas


def gerar_internacoes_e_ocupacao(leitos, rng):
    """Gera internacoes por leito e a serie diaria de ocupacao, coerentes entre si.

    Para cada leito ativo, percorre a janela criando estadias sem sobreposicao:
    um leito fica ocupado nos dias entre a admissao e a alta (libera no dia da
    alta). Estadias podem comecar antes da janela (left-censored) e podem seguir
    ativas em SIM_TODAY (alta real nula). Leitos bloqueados ficam bloqueados em
    todos os dias da janela.
    """
    primeiro, ultimo = _janela()
    internacoes = []
    ocupacao = []
    prox_id = 1

    for id_leito, _id_unidade, tipo, status in leitos:
        if status == "bloqueado":
            dia = primeiro
            while dia <= ultimo:
                ocupacao.append((dia, id_leito, "bloqueado", None))
                dia += timedelta(days=1)
            continue

        lo, hi = LOS_POR_TIPO[tipo]
        # dias ocupados deste leito -> id_internacao que o ocupa
        ocupado = {}
        # cursor pode comecar antes do inicio da janela, para evitar um pico
        # artificial de admissoes no primeiro dia
        cursor = primeiro - timedelta(days=rng.randint(0, hi))

        while cursor <= ultimo:
            los = rng.randint(lo, hi)
            admissao = cursor
            alta_prevista = admissao + timedelta(days=los)
            los_real = max(1, los + rng.randint(-2, 3))
            alta_calculada = admissao + timedelta(days=los_real)

            if alta_calculada > ultimo:
                # ainda internado em SIM_TODAY
                alta_real = None
                fim_ocup = ultimo
            else:
                # libera o leito no dia da alta, entao ocupa ate a vespera
                alta_real = alta_calculada
                fim_ocup = alta_calculada - timedelta(days=1)

            # so registra a internacao se ela intersecta a janela historica
            if fim_ocup >= primeiro:
                id_paciente = rng.randint(1, config.VOL_PACIENTES)
                internacoes.append(
                    (prox_id, id_paciente, id_leito, admissao, alta_prevista, alta_real)
                )
                dia = max(admissao, primeiro)
                limite = min(fim_ocup, ultimo)
                while dia <= limite:
                    ocupado[dia] = prox_id
                    dia += timedelta(days=1)
                prox_id += 1

            cursor = alta_calculada + timedelta(days=rng.randint(0, GAP_MAX))

        # serie diaria do leito: ocupado nos dias marcados, livre nos demais
        dia = primeiro
        while dia <= ultimo:
            if dia in ocupado:
                ocupacao.append((dia, id_leito, "ocupado", ocupado[dia]))
            else:
                ocupacao.append((dia, id_leito, "livre", None))
            dia += timedelta(days=1)

    return internacoes, ocupacao


def _criar_schema_e_tabelas(con):
    """Cria o schema bronze e recria as cinco tabelas (idempotente)."""
    con.execute("CREATE SCHEMA IF NOT EXISTS bronze")
    con.execute(
        "CREATE OR REPLACE TABLE bronze.unidade ("
        "id_unidade INTEGER, nome VARCHAR, especialidade VARCHAR, andar INTEGER)"
    )
    con.execute(
        "CREATE OR REPLACE TABLE bronze.leito ("
        "id_leito INTEGER, id_unidade INTEGER, tipo VARCHAR, status VARCHAR)"
    )
    con.execute(
        "CREATE OR REPLACE TABLE bronze.paciente ("
        "id_paciente INTEGER, nome VARCHAR, cpf VARCHAR, "
        "data_nascimento DATE, sexo VARCHAR)"
    )
    con.execute(
        "CREATE OR REPLACE TABLE bronze.internacao ("
        "id_internacao INTEGER, id_paciente INTEGER, id_leito INTEGER, "
        "data_admissao DATE, data_alta_prevista DATE, data_alta_real DATE)"
    )
    con.execute(
        "CREATE OR REPLACE TABLE bronze.ocupacao_diaria ("
        "data DATE, id_leito INTEGER, situacao VARCHAR, id_internacao INTEGER)"
    )


def construir():
    """Gera tudo e grava na Bronze. Retorna as contagens por tabela."""
    config.DATA_DIR.mkdir(parents=True, exist_ok=True)

    # determinismo: uma unica SEED governa Faker e os sorteios proprios
    fake = Faker("pt_BR")
    Faker.seed(config.SEED)
    rng = random.Random(config.SEED)

    unidades = gerar_unidades()
    leitos = gerar_leitos(rng)
    pacientes = gerar_pacientes(fake, rng)
    internacoes, ocupacao = gerar_internacoes_e_ocupacao(leitos, rng)

    con = duckdb.connect(str(config.DB_PATH))
    try:
        _criar_schema_e_tabelas(con)
        con.executemany("INSERT INTO bronze.unidade VALUES (?, ?, ?, ?)", unidades)
        con.executemany("INSERT INTO bronze.leito VALUES (?, ?, ?, ?)", leitos)
        con.executemany("INSERT INTO bronze.paciente VALUES (?, ?, ?, ?, ?)", pacientes)
        con.executemany(
            "INSERT INTO bronze.internacao VALUES (?, ?, ?, ?, ?, ?)", internacoes
        )
        con.executemany(
            "INSERT INTO bronze.ocupacao_diaria VALUES (?, ?, ?, ?)", ocupacao
        )
        contagens = {
            tabela: con.execute(f"SELECT COUNT(*) FROM bronze.{tabela}").fetchone()[0]
            for tabela in (
                "unidade",
                "leito",
                "paciente",
                "internacao",
                "ocupacao_diaria",
            )
        }
    finally:
        con.close()
    return contagens


def _autoteste():
    """Gera a Bronze e imprime as contagens de cada tabela."""
    primeiro, ultimo = _janela()
    contagens = construir()

    print("data_gen: Bronze gerada")
    print(f"  janela historica: {primeiro.isoformat()} a {ultimo.isoformat()} "
          f"({config.HIST_DAYS} dias)  SEED={config.SEED}")
    print("  contagens por tabela:")
    for tabela, n in contagens.items():
        print(f"    bronze.{tabela}: {n}")

    # invariantes determinadas pela configuracao
    assert contagens["unidade"] == config.VOL_UNIDADES
    assert contagens["leito"] == config.VOL_LEITOS
    assert contagens["paciente"] == config.VOL_PACIENTES
    assert contagens["ocupacao_diaria"] == config.VOL_LEITOS * config.HIST_DAYS
    # internacoes e um alvo aproximado (cerca de 2200), nao um valor exato
    assert 1500 <= contagens["internacao"] <= 2900, (
        f"internacoes fora da faixa esperada: {contagens['internacao']}"
    )
    print("data_gen: autoteste OK")


if __name__ == "__main__":
    _autoteste()
