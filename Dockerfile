FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

ADD . /app

# Sync the project into a new environment, asserting the lockfile is up to date
WORKDIR /app
RUN uv sync --locked
#RUN mkdir -p /app/logs

CMD ["uv", "run", "main.py"]