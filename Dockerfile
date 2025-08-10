# Use the same Python version as in .python-version
FROM python:3.12.0-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y build-essential curl && rm -rf /var/lib/apt/lists/*

# Install pip and poetry
RUN pip install --upgrade pip && pip install poetry
RUN poetry config virtualenvs.create false

# Copy dependency files and install
COPY pyproject.toml poetry.lock* ./
RUN poetry install --no-root --only main

# Copy project
COPY . ./

# Entrypoint
COPY docker-entrypoint.sh /app/docker-entrypoint.sh
RUN chmod +x /app/docker-entrypoint.sh

EXPOSE 8000
ENTRYPOINT ["/app/docker-entrypoint.sh"]


