FROM python:3.11-slim

# Метаданные образа
LABEL maintainer="VulnBuster"
LABEL description="Bandit Security Scanner MCP Server with Gradio Web Interface"
LABEL version="1.0"
LABEL application="bandit-mcp"

# Установка системных зависимостей
RUN apt-get update && apt-get install -y \
    git \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Создание рабочей директории
WORKDIR /app

# Копирование requirements
COPY requirements.txt ./requirements.txt

# Установка Python зависимостей
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Копирование исходного кода
COPY bandit_mcp.py .

# Переменные окружения для Bandit MCP
ENV GRADIO_SERVER_PORT=7861
ENV GRADIO_SERVER_NAME=0.0.0.0
ENV APP_NAME="Bandit Security Scanner MCP"

# Открытие порта
EXPOSE $GRADIO_SERVER_PORT

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:${GRADIO_SERVER_PORT}/ || exit 1

# Команда запуска
CMD ["python", "bandit_mcp.py"]