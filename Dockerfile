# Imagem de execucao reprodutivel do prototipo.
#
# Objetivo: fechar a ultima lacuna de reprodutibilidade (RNC-003). O
# determinismo por SEED e SIM_TODAY garante "mesma configuracao, mesmos dados",
# mas a reproducao exata ainda dependia do ambiente de quem executa (versao de
# Python, do DuckDB, do SO). Esta imagem fixa esse ambiente: a banca ou um
# avaliador reproduz o experimento com um unico `docker run`.
#
# Base travada por digest (nao apenas por tag): garante o mesmo binario ao
# longo do tempo, mesmo que a tag "3.12.12-slim-bookworm" seja republicada.
FROM python:3.12.12-slim-bookworm@sha256:593bd06efe90efa80dc4eee3948be7c0fde4134606dd40d8dd8dbcade98e669c

# Boas praticas de runtime Python em container:
# - sem .pyc gravado em disco; logs sem buffer (saida imediata no `docker run`).
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Instala as dependencias antes de copiar o codigo, para aproveitar o cache de
# camadas: o requirements muda pouco, o codigo muda muito.
COPY requirements.txt ./
RUN python -m pip install --no-cache-dir --upgrade pip \
    && python -m pip install --no-cache-dir -r requirements.txt

# Copia o restante do projeto (o .dockerignore mantem .venv/, data/, results/
# e segredos fora da imagem).
COPY . .

# Roda como usuario sem privilegios (boa pratica de seguranca; nao roda root).
RUN useradd --create-home appuser
USER appuser

# RNC-004: NENHUMA credencial entra na imagem. A chave da API e injetada apenas
# em tempo de execucao, por variavel de ambiente:
#   docker run --rm -e ANTHROPIC_API_KEY="$ANTHROPIC_API_KEY" <imagem> python run_all.py llm
#
# Por padrao roda o teste rapido do modulo de configuracao (o mesmo da CI), que
# nao precisa de chave nem tem custo. Sobrescreva o comando para outros modos.
CMD ["python", "-m", "src.config"]
