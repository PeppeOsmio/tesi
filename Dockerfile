FROM python:3.12

WORKDIR /app

COPY pyproject.toml poetry.lock* poetry.toml /app/

RUN pip install --no--cache-dir poetry

RUN poetry install --no-interaction --no-ansi

COPY . /app

EXPOSE 8000

ENTRYPOINT [ "./entrypoint.sh" ]