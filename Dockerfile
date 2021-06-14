FROM python:3.9-buster AS builder-base
RUN curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/get-poetry.py | python - \
  && ln -s $HOME/.poetry/bin/poetry /usr/local/bin/poetry
WORKDIR /usr/src/app

### DEV

FROM builder-base AS python-analyser-dev
ENV PORT 8080
ENV APP analyser.api:app
COPY pyproject.toml .
COPY poetry.lock .
RUN poetry run python -m pip install -U pip==21.1.2
RUN poetry install
COPY . .
ENTRYPOINT poetry run uvicorn ${APP} --reload --host 0.0.0.0 --port ${PORT} --log-config logs.dev.yaml

### PROD

FROM builder-base AS builder-prod
COPY . .
RUN poetry build

# Note that some wheels are not available for python3.9 yet
FROM python:3.9-slim-buster
ENV PORT 8080
ENV APP analyser.api:app
RUN apt-get update && apt-get install -y git \
    && rm -rf /var/lib/apt/lists/*
RUN python -m pip install -U pip==21.1.2
COPY --from=builder-prod /usr/src/app/dist/*.whl /tmp/
RUN python -m pip install /tmp/*.whl
ENTRYPOINT python -m uvicorn ${APP} --host 0.0.0.0 --port ${PORT} --log-config /usr/local/lib/python3.9/site-packages/logs.prod.yaml
