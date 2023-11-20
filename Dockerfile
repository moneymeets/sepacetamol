ARG PYTHON_VERSION_CONSTRAINT
FROM python:${PYTHON_VERSION_CONSTRAINT}-slim-bookworm as python-base

LABEL maintainer="moneymeets GmbH <admin@moneymeets.com>"

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    APP_PATH="/opt/app" \
    POETRY_HOME="/opt/poetry" \
    POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=true \
    VENV_PATH="/opt/app/.venv"

ENV PATH="$POETRY_HOME/bin:$VENV_PATH/bin:$PATH"

ARG POETRY_VERSION
FROM python-base as builder-deps

RUN apt-get update \
    && DEBIAN_FRONTEND=noninteractive apt install -y curl git  \
    && apt-get install -y --no-install-recommends build-essential \
    && curl -sSL https://install.python-poetry.org | python - --yes --version=${POETRY_VERSION} \
    && apt remove -y --purge curl \
    && rm -rf /var/lib/apt/lists/*

COPY .git/ ./.git/

RUN git archive -v -o app.tar.gz --format=tar.gz HEAD

WORKDIR $APP_PATH

ADD poetry.lock pyproject.toml ./

RUN --mount=type=cache,target=/root/.cache \
    poetry install --without dev


FROM python-base as prod

RUN apt update \
    && DEBIAN_FRONTEND=noninteractive apt install -y curl \
    && rm -rf /var/lib/apt/lists/*


# Copy Python dependencies from the previous build stage
COPY --from=builder-deps $APP_PATH $APP_PATH

RUN useradd -m appuser -d $APP_PATH && chown appuser:appuser -R $APP_PATH

USER appuser

WORKDIR $APP_PATH

COPY --from=builder-deps app.tar.gz $APP_PATH

RUN tar -xvf app.tar.gz && rm -rf app.tar.gz

ENTRYPOINT [ "bash", "-c", "gunicorn -c ./docker-gunicorn.conf.py" ]
