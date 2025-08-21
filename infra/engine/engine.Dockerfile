FROM python:3.11-slim
WORKDIR /app
COPY apps/engine-py/pyproject.toml apps/engine-py/poetry.lock ./
RUN pip install poetry && poetry config virtualenvs.create false && poetry install --no-interaction
COPY apps/engine-py /app
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
