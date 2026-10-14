FROM python:3.10-slim

# Системные зависимости
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Установка Python-зависимостей
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копирование исходного кода проекта
COPY . .

# Создание каталога данных с правами на запись
RUN mkdir -p /app/data && chmod 777 /app/data

ENV PYTHONUNBUFFERED=1 \
    FOREST_OPTIMA_DATA_DIR=/app/data \
    PORT=8890

EXPOSE 8890

HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8890/api/health || exit 1

CMD ["uvicorn", "forest_optima.web.app:app", "--host", "0.0.0.0", "--port", "8890"]
