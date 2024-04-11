# This file was added by Pulumi and should not be edited manually. To edit the contents of this file, please go
# to the github-management project in moneymeets-pulumi and call `pulumi up` after changing the template file.

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

# Copy Python dependencies from the previous build stage
COPY --from=builder-deps $APP_PATH $APP_PATH

# Install additional dependencies, if any
RUN apt update \
    && DEBIAN_FRONTEND=noninteractive apt install -y \
        curl \
        # If weasyprint is installed, we need the following packages as additional dependencies
        # https://doc.courtbouillon.org/weasyprint/stable/first_steps.html#debian-11
        $(test -f $VENV_PATH/bin/weasyprint && echo "libpango-1.0-0 libpangoft2-1.0-0") \
    && rm -rf /var/lib/apt/lists/*

RUN useradd -m appuser -d $APP_PATH && chown appuser:appuser -R $APP_PATH

USER appuser

WORKDIR $APP_PATH

COPY --from=builder-deps app.tar.gz $APP_PATH

RUN tar -xvf app.tar.gz && rm -rf app.tar.gz

# Default entry point for local usage, will be overridden by Pulumi for production usage
ENTRYPOINT [ "bash", "-c", "gunicorn --bind '0.0.0.0:8000' --keep-alive 35 --workers 1 --threads 1 --log-level debug --error-logfile '-' --access-logfile '-' --enable-stdio-inheritance --access-logformat '%({x-forwarded-for}i)s %(h)s %(l)s %(u)s %(t)s \"%(r)s\" %(s)s %(b)s \"%(f)s\" \"%(a)s\" \"%(M)s\"' config.wsgi" ]
