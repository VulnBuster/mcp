# 🚀 Docker Setup для Security Tools MCP

## 📋 Быстрый старт

### 1. Создайте файл `.env`:
```bash
# Создайте .env в корне проекта
touch .env
```

### 2. Заполните `.env` файл:
```bash
# ======================
# API KEYS
# ======================
NEBIUS_API_KEY=your_api_key_here
CIRCLE_API_URL=https://api.example.com/protect/check_violation

# ======================
# SERVER CONFIGURATION
# ======================
GRADIO_SERVER_NAME=0.0.0.0

# ======================
# MAIN AGENT PORTS
# ======================
AGENT_EXTERNAL_PORT=7860
AGENT_INTERNAL_PORT=7860

# ======================
# MCP SERVERS PORTS
# ======================

# Bandit Security Scanner
BANDIT_EXTERNAL_PORT=7861
BANDIT_INTERNAL_PORT=7861

# Detect Secrets Scanner
DETECT_SECRETS_EXTERNAL_PORT=7862
DETECT_SECRETS_INTERNAL_PORT=7862

# Pip Audit Scanner
PIP_AUDIT_EXTERNAL_PORT=7863
PIP_AUDIT_INTERNAL_PORT=7863

# Circle Test Scanner
CIRCLE_TEST_EXTERNAL_PORT=7864
CIRCLE_TEST_INTERNAL_PORT=7864

# Semgrep Scanner
SEMGREP_EXTERNAL_PORT=7865
SEMGREP_INTERNAL_PORT=7865
```

### 3. Запуск:
```bash
# Запуск всех сервисов
docker-compose up --build

# Запуск в фоне
docker-compose up -d

# Только главный агент + MCP серверы
docker-compose up security-tools-agent
```

## 🌐 Доступ к приложениям:

- **🎯 Main Agent**: http://localhost:7860 (основное приложение)
- **🔒 Bandit**: http://localhost:7861
- **🔍 Detect Secrets**: http://localhost:7862  
- **🛡️ Pip Audit**: http://localhost:7863
- **📋 Circle Test**: http://localhost:7864
- **🔍 Semgrep**: http://localhost:7865

## ⚙️ Кастомизация портов:

Если порты заняты, измените в `.env`:
```bash
# Альтернативные порты
AGENT_EXTERNAL_PORT=8060
BANDIT_EXTERNAL_PORT=8061
DETECT_SECRETS_EXTERNAL_PORT=8062
PIP_AUDIT_EXTERNAL_PORT=8063
CIRCLE_TEST_EXTERNAL_PORT=8064
SEMGREP_EXTERNAL_PORT=8065
```

## 🔧 Полезные команды:

```bash
# Статус сервисов
docker-compose ps

# Логи главного агента
docker-compose logs security-tools-agent

# Логи всех сервисов
docker-compose logs -f

# Остановка
docker-compose down

# Полная очистка
docker-compose down -v --rmi all
```

## 🏗️ Архитектура:

```
┌─────────────────────────────────────────┐
│           Security Tools Agent          │
│              (main.py)                  │
│            Port: 7860                   │
└─────────────────┬───────────────────────┘
                  │
    ┌─────────────┼─────────────┐
    │             │             │
    ▼             ▼             ▼
┌─────────┐  ┌─────────┐  ┌─────────┐
│ Bandit  │  │Detect   │  │   ...   │
│ :7861   │  │Secrets  │  │         │
└─────────┘  │ :7862   │  └─────────┘
             └─────────┘
```

Все MCP серверы работают в Docker сети `mcp-network` и общаются через имена сервисов! 