import asyncio
import os
import tempfile
import gradio as gr
from textwrap import dedent
from agno.agent import Agent
from agno.tools.mcp import MCPTools
from agno.models.nebius import Nebius
from mcp import ClientSession
from mcp.client.sse import sse_client
from dotenv import load_dotenv
import base64
import difflib
import re
import subprocess
import sys
import shutil
import time
import aiohttp
import logging
import signal
import socket
import json


# Настройка логирования
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def clean_and_validate_json(raw_text: str) -> str:
    """
    Агрессивно очищает и валидирует JSON из текста
    """
    logger.debug(f"Попытка очистки JSON из текста длиной {len(raw_text)}")
    
    # Убираем все возможные блоки думания и комментариев
    cleaned = re.sub(r"<think>.*?</think>", "", raw_text, flags=re.DOTALL)
    cleaned = re.sub(r"```json\s*", "", cleaned)
    cleaned = re.sub(r"```\s*", "", cleaned)
    cleaned = cleaned.strip()
    
    # Ищем JSON объект от первой { до соответствующей }
    start_idx = cleaned.find("{")
    if start_idx == -1:
        return raw_text
    
    # Найдем соответствующую закрывающую скобку
    bracket_count = 0
    end_idx = -1
    
    for i in range(start_idx, len(cleaned)):
        if cleaned[i] == '{':
            bracket_count += 1
        elif cleaned[i] == '}':
            bracket_count -= 1
            if bracket_count == 0:
                end_idx = i
                break
    
    if end_idx == -1:
        return raw_text
    
    # Извлекаем JSON часть
    json_part = cleaned[start_idx:end_idx + 1]
    
    try:
        # Проверяем, является ли это валидным JSON
        json.loads(json_part)
        logger.debug("JSON успешно очищен и валидирован")
        return json_part
    except json.JSONDecodeError as e:
        logger.debug(f"Ошибка при валидации очищенного JSON: {e}")
        return raw_text

def standardize_mcp_response(response_text: str, server_name: str) -> str:
    """
    Стандартизирует ответы от разных MCP серверов в единый формат
    """
    try:
        # Сначала пытаемся парсить как JSON
        parsed = json.loads(response_text)
        
        # Для Circle Test - ответы могут приходить в формате {"results": [...]}
        if server_name == "circle_test":
            if isinstance(parsed, dict) and "results" in parsed:
                return json.dumps(parsed, ensure_ascii=False)
            elif isinstance(parsed, list):
                # Если пришел список результатов без обертки
                standardized = {"results": parsed}
                return json.dumps(standardized, ensure_ascii=False)
        
        # Для Bandit - ответы могут приходить в формате {"results": [...], "metrics": {...}}
        elif server_name == "bandit":
            if isinstance(parsed, dict):
                return json.dumps(parsed, ensure_ascii=False)
            elif isinstance(parsed, list):
                # Если пришел список результатов без обертки
                standardized = {"results": parsed}
                return json.dumps(standardized, ensure_ascii=False)
        
        # Для других серверов - возвращаем как есть, если JSON валидный
        return json.dumps(parsed, ensure_ascii=False)
        
    except json.JSONDecodeError:
        # Если не JSON, возвращаем оригинальную строку
        logger.debug(f"Ответ от {server_name} не является валидным JSON")
        return response_text

def extract_json_payload(raw: str) -> str:
    """
    Извлекает первый JSON объект {...} из строки, удаляя Markdown-разметку и дополнительный текст.
    """
    logger.debug(f"Исходная строка для извлечения JSON (длина: {len(raw)}): {raw[:500]}...")
    
    # Убираем блоки <think>
    raw = re.sub(r"<think>.*?</think>", "", raw, flags=re.DOTALL).strip()
    
    # Убираем markdown блоки
    raw = re.sub(r"```json\s*", "", raw)
    raw = re.sub(r"```", "", raw)
    
    # Убираем возможные лишние символы в начале и конце
    raw = raw.strip()
    
    logger.debug(f"После очистки markdown (длина: {len(raw)}): {raw[:500]}...")
    
    # Ищем первый '{' и соответствующую ему закрывающую '}'
    start = raw.find("{")
    if start == -1:
        logger.warning("Не найден открывающий символ '{'")
        return raw
    
    # Ищем соответствующую закрывающую скобку
    bracket_count = 0
    end = -1
    for i in range(start, len(raw)):
        if raw[i] == '{':
            bracket_count += 1
        elif raw[i] == '}':
            bracket_count -= 1
            if bracket_count == 0:
                end = i
                break
    
    if end == -1:
        logger.warning("Не найден соответствующий закрывающий символ '}'")
        return raw
    
    json_candidate = raw[start:end + 1]
    logger.debug(f"Извлеченный JSON кандидат (длина: {len(json_candidate)}): {json_candidate[:500]}...")
    
    # Проверяем валидность JSON перед возвратом
    try:
        parsed = json.loads(json_candidate)
        logger.debug("JSON успешно распарсен в extract_json_payload")
        return json_candidate
    except json.JSONDecodeError as e:
        logger.warning(f"Извлеченный JSON невалидный: {str(e)}")
        logger.debug(f"Проблемный JSON: {json_candidate}")
        # Пытаемся вернуть полную строку без обработки
        try:
            # Проверяем, может быть вся строка уже является валидным JSON
            json.loads(raw)
            logger.debug("Полная строка является валидным JSON")
            return raw
        except json.JSONDecodeError:
            logger.warning("Даже полная строка не является валидным JSON, возвращаем как есть")
            return raw

# Глобальные переменные для переиспользования сессий
MCP_WRAPPERS = {}

# Загружаем переменные окружения из .env файла
load_dotenv()
api_key = os.getenv("NEBIUS_API_KEY")
if not api_key:
    raise ValueError("NEBIUS_API_KEY not found in .env file")

# Конфигурация MCP серверов (для Docker с переменными окружения)
BANDIT_PORT = os.getenv('BANDIT_INTERNAL_PORT', '7861')
DETECT_SECRETS_PORT = os.getenv('DETECT_SECRETS_INTERNAL_PORT', '7862')
PIP_AUDIT_PORT = os.getenv('PIP_AUDIT_INTERNAL_PORT', '7863')
CIRCLE_TEST_PORT = os.getenv('CIRCLE_TEST_INTERNAL_PORT', '7864')
SEMGREP_PORT = os.getenv('SEMGREP_INTERNAL_PORT', '7865')

MCP_SERVERS = {
    "bandit": {
        "url": f"http://bandit-security-scanner:{BANDIT_PORT}/gradio_api/mcp/sse",
        "description": "Python code security analysis",
        "port": int(BANDIT_PORT)
    },
    "detect_secrets": {
        "url": f"http://detect-secrets-scanner:{DETECT_SECRETS_PORT}/gradio_api/mcp/sse",
        "description": "Secret detection in code",
        "port": int(DETECT_SECRETS_PORT)
    },
    "pip_audit": {
        "url": f"http://pip-audit-scanner:{PIP_AUDIT_PORT}/gradio_api/mcp/sse",
        "description": "Python package vulnerability scanning",
        "port": int(PIP_AUDIT_PORT)
    },
    "circle_test": {
        "url": f"http://circle-test-scanner:{CIRCLE_TEST_PORT}/gradio_api/mcp/sse",
        "description": "Security policy compliance checking",
        "port": int(CIRCLE_TEST_PORT)
    },
    "semgrep": {
        "url": f"http://semgrep-scanner:{SEMGREP_PORT}/gradio_api/mcp/sse",
        "description": "Advanced static code analysis",
        "port": int(SEMGREP_PORT)
    }
}

def check_port(port: int) -> bool:
    """Проверяет доступность порта"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        result = sock.connect_ex(('127.0.0.1', port))
        return result == 0
    finally:
        sock.close()

def signal_handler(signum, frame):
    """Обработчик сигналов для корректного завершения"""
    logger.info("Получен сигнал завершения, закрываем серверы...")
    sys.exit(0)

# Регистрируем обработчики сигналов
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

def generate_simple_diff(original_content: str, updated_content: str, file_path: str) -> str:
    """
    Генерирует простой diff между оригинальным и обновленным содержимым
    """
    diff_lines = list(difflib.unified_diff(
        original_content.splitlines(keepends=True),
        updated_content.splitlines(keepends=True),
        fromfile=f"{file_path} (original)",
        tofile=f"{file_path} (modified)",
        n=3
    ))
    if not diff_lines:
        return "No changes detected."
    added_lines = sum(1 for l in diff_lines if l.startswith("+") and not l.startswith("+++"))
    removed_lines = sum(1 for l in diff_lines if l.startswith("-") and not l.startswith("---"))
    diff_content = "".join(diff_lines)
    stats = f"\n📊 Changes: +{added_lines} additions, -{removed_lines} deletions"
    return diff_content + stats

async def check_server_availability(url: str, max_retries: int = 5, delay: float = 5.0) -> bool:
    """Проверяет доступность MCP сервера с увеличенными таймаутами"""
    logger.debug(f"Проверка доступности сервера: {url}")
    for i in range(max_retries):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=30) as response:
                    if response.status == 200:
                        logger.info(f"Сервер {url} доступен")
                        return True
        except Exception as e:
            logger.warning(f"Попытка {i+1}/{max_retries} не удалась: {str(e)}")
        await asyncio.sleep(delay)
    logger.error(f"Сервер {url} недоступен после {max_retries} попыток")
    return False

async def init_all_tools():
    """Инициализирует все MCP инструменты один раз при старте приложения"""
    global MCP_WRAPPERS
    
    try:
        # Создаем SSE клиенты для каждого сервера
        for name, cfg in MCP_SERVERS.items():
            async with sse_client(cfg["url"]) as (read, write):
                async with ClientSession(read, write) as session:
                    MCP_WRAPPERS[name] = MCPTools(session=session)
            
        logger.info("Все MCP инструменты успешно инициализированы")
    except Exception as e:
        logger.error(f"Ошибка при инициализации MCP инструментов: {str(e)}")
        raise

async def run_mcp_agent(message, server_name):
    """Запускает агента для конкретного MCP сервера"""
    logger.info(f"Запуск MCP агента для {server_name}")
    
    if not api_key:
        logger.error("Nebius API key не найден в .env файле")
        return "Error: Nebius API key not found in .env file"
    
    if server_name not in MCP_SERVERS:
        logger.error(f"Неизвестный MCP сервер: {server_name}")
        return f"Error: Unknown MCP server {server_name}"
    
    if server_name not in MCP_WRAPPERS:
        logger.error(f"MCP инструмент {server_name} не инициализирован")
        return f"Error: MCP tool {server_name} not initialized"
    
    try:
        # Получаем инструмент из кэша
        mcp_tools = MCP_WRAPPERS[server_name]
        
        # Создаем агента
        agent = Agent(
            tools=[mcp_tools],
            instructions=dedent(f"""\
                You are an intelligent security assistant with access to MCP tools for {server_name}.
                
                IMPORTANT INSTRUCTIONS:
                1. Use the appropriate MCP tool to analyze the provided code
                2. Return ONLY the raw JSON result from the MCP tool
                3. Do NOT add any explanations, commentary, or additional formatting
                4. Do NOT wrap the result in markdown code blocks
                5. Do NOT add any text before or after the JSON
                6. If the tool returns a "results" field, return the complete response including that field
                
                The JSON output should be clean and parseable without any modifications.
            """),
            markdown=False,  # Отключаем Markdown для получения чистого JSON
            show_tool_calls=True,
            model=Nebius(
                id="Qwen/Qwen3-30B-A3B-fast",
                api_key=api_key
            )
        )
        
        # Форматируем сообщение
        formatted_message = f"Analyze this code using {server_name}: {message}"
        
        # Запускаем анализ
        response = await agent.arun(formatted_message)
        logger.info(f"Успешное выполнение для {server_name}")
        logger.debug(f"Полный ответ агента для {server_name}: {response.content}")
        
        # Сначала пробуем агрессивную очистку
        cleaned_response = clean_and_validate_json(response.content)
        
        # Если агрессивная очистка не помогла, используем обычную функцию
        if cleaned_response == response.content:
            cleaned_response = extract_json_payload(response.content)
        
        # Стандартизируем ответ для конкретного сервера
        standardized_response = standardize_mcp_response(cleaned_response, server_name)
        
        logger.debug(f"Стандартизированный ответ для {server_name}: {standardized_response}")
        return standardized_response
        
    except Exception as e:
        logger.error(f"Ошибка выполнения {server_name}: {str(e)}")
        # Возвращаем ошибку в формате JSON для консистентности
        error_response = {
            "success": False,
            "error": f"Error running {server_name}: {str(e)}",
            "results": {}
        }
        return json.dumps(error_response, ensure_ascii=False)

async def run_fix_agent(message):
    """Запускает агента для исправления кода"""
    if not api_key:
        return "Error: Nebius API key not found in .env file"
    
    agent = Agent(
        tools=[],
        instructions=dedent("""\
            You are an intelligent code refactoring assistant.
            Based on the vulnerabilities detected, propose a corrected version of the code.
            Return only the full updated source code, without any additional commentary or markup.
        """),
        markdown=False,
        show_tool_calls=False,
        model=Nebius(
            id="Qwen/Qwen3-30B-A3B-fast",
            api_key=api_key
        )
    )
    try:
        response = await agent.arun(message)
        return response.content
    except Exception as e:
        return f"Error proposing fixes: {e}"

async def process_file(file_obj, custom_checks, selected_servers):
    """Обрабатывает файл с помощью выбранных MCP серверов"""
    if not file_obj:
        return "", "", ""
    
    try:
        # Сохраняем загруженный файл
        temp_dir = tempfile.gettempdir()
        file_path = os.path.join(temp_dir, file_obj.name)
        
        # Получаем содержимое файла из объекта Gradio
        with open(file_obj.name, 'r', encoding='utf-8') as f:
            file_content = f.read()
            
        with open(file_path, "w", encoding='utf-8') as f:
            f.write(file_content)
        
        # Подготавливаем сообщение для всех серверов
        if custom_checks:
            user_message = (
                f"Please analyze this code for {custom_checks}, "
                f"using the most comprehensive settings available:\n\n{file_content}"
            )
        else:
            user_message = (
                f"Please perform a full vulnerability and security analysis on this code, "
                f"selecting the highest intensity settings:\n\n{file_content}"
            )
        
        # Запускаем все анализаторы параллельно
        tasks = {
            server: asyncio.create_task(run_mcp_agent(user_message, server))
            for server in selected_servers
        }
        
        # Собираем результаты
        raw_outputs = {
            server: re.sub(r"<think>.*?</think>", "", await task, flags=re.DOTALL).strip()
            for server, task in tasks.items()
        }

        # Преобразуем raw_outputs в читаемый текст для Markdown
        formatted_results = []
        for name, raw in raw_outputs.items():
            logger.debug(f"Обработка результата для {name}, длина: {len(raw)}")
            logger.debug(f"Полное содержимое для {name}: {raw}")
            
            try:
                # Пытаемся распарсить JSON
                parsed_data = json.loads(raw)
                logger.debug(f"JSON успешно распарсен для {name}")
                
                # Извлекаем результаты если они есть
                if isinstance(parsed_data, dict) and 'results' in parsed_data:
                    display_data = parsed_data['results']
                    logger.debug(f"Извлечены results для {name}")
                else:
                    display_data = parsed_data
                    logger.debug(f"Используются сырые данные для {name}")
                
                # Форматируем для отображения
                formatted_json = json.dumps(display_data, indent=2, ensure_ascii=False)
                formatted_results.append(f"### {name.upper()}:\n```json\n{formatted_json}\n```")
                
            except json.JSONDecodeError as e:
                # Если JSON некорректный, показываем как есть
                logger.warning(f"Не удалось распарсить JSON для {name}: {str(e)}")
                logger.debug(f"Позиция ошибки: {getattr(e, 'pos', 'неизвестно')}")
                logger.debug(f"Длина строки: {len(raw)}")
                
                # Пытаемся найти проблемную область
                if hasattr(e, 'pos') and e.pos:
                    start_pos = max(0, e.pos - 50)
                    end_pos = min(len(raw), e.pos + 50)
                    problem_area = raw[start_pos:end_pos]
                    logger.debug(f"Проблемная область вокруг позиции {e.pos}: {repr(problem_area)}")
                
                # Проверяем на наличие скрытых символов
                has_non_printable = any(ord(c) < 32 and c not in '\n\r\t' for c in raw)
                if has_non_printable:
                    logger.warning(f"Обнаружены непечатаемые символы в ответе для {name}")
                
                formatted_results.append(f"### {name.upper()} (Raw output):\n```\n{raw}\n```")
            except Exception as e:
                # Любые другие ошибки
                logger.error(f"Ошибка обработки результата для {name}: {str(e)}")
                formatted_results.append(f"### {name.upper()} (Error):\n```\nОшибка обработки: {str(e)}\n```")
        
        markdown_output = "\n\n".join(formatted_results)

        # Читаем оригинальный код
        with open(file_path, 'r', encoding='utf-8') as f_in:
            orig_code = f_in.read()
        
        # Подготавливаем промпт для исправлений
        orig_name = os.path.basename(file_path)
        fix_prompt = f"""Below is the full source code of '{orig_name}':
```python
{orig_code}
```
Please generate a corrected version of this code, addressing all security vulnerabilities. Return only the full updated source code."""
        
        # Получаем исправленный код
        fixed_code = await run_fix_agent(fix_prompt)
        
        # Очищаем код от блоков <think>
        cleaned_code = re.sub(r"<think>.*?</think>", "", fixed_code, flags=re.DOTALL).strip()
        
        # Генерируем diff
        diff_text = generate_simple_diff(orig_code, cleaned_code, orig_name)
        
        return markdown_output, diff_text, cleaned_code
        
    except Exception as e:
        logger.error(f"Ошибка при обработке файла: {str(e)}")
        return f"❌ Произошла ошибка: {str(e)}", "", ""

async def check_all_servers():
    """Проверяет доступность всех MCP серверов"""
    unavailable_servers = []
    for server_name, config in MCP_SERVERS.items():
        if not check_port(config["port"]):
            unavailable_servers.append(f"{server_name} (порт {config['port']})")
    return unavailable_servers

def process_file_sync(file_obj, custom_checks, selected_servers):
    """Синхронная обертка для process_file"""
    return asyncio.run(process_file(file_obj, custom_checks, selected_servers))

# Создаем интерфейс Gradio
with gr.Blocks(title="Security Tools MCP Agent") as demo:
    gr.Markdown("# 🔒 Security Tools MCP Agent")
    
    with gr.Row():
        with gr.Column(scale=1):
            file_input = gr.File(
                label="Upload a code file",
                file_types=[".py", ".js", ".java", ".go", ".rb"]
            )
            custom_checks = gr.Textbox(
                label="Enter specific checks or tools to use (optional)",
                placeholder="e.g., SQL injection, shell injection, detect secrets"
            )
            server_checkboxes = gr.CheckboxGroup(
                choices=list(MCP_SERVERS.keys()),
                value=list(MCP_SERVERS.keys()),
                label="Select MCP Servers"
            )
            scan_button = gr.Button("Run Scan", variant="primary")
    
    with gr.Row():
        with gr.Column(scale=1):
            analysis_output = gr.Markdown(label="Security Analysis Results")
            diff_output = gr.Textbox(label="Proposed Code Fixes", lines=10)
            fixed_code_output = gr.Code(label="Fixed Code", language="python")
            download_button = gr.File(label="Download corrected file")
    
    def update_download_button(fixed_code):
        if fixed_code:
            temp_dir = tempfile.gettempdir()
            fixed_path = os.path.join(temp_dir, "fixed_code.py")
            with open(fixed_path, "w") as f:
                f.write(fixed_code)
            return fixed_path
        return None
    
    scan_button.click(
        fn=process_file_sync,
        inputs=[file_input, custom_checks, server_checkboxes],
        outputs=[analysis_output, diff_output, fixed_code_output]
    ).then(
        fn=update_download_button,
        inputs=[fixed_code_output],
        outputs=[download_button]
    )

if __name__ == "__main__":
    try:
        # Инициализируем все MCP инструменты при старте
        asyncio.run(init_all_tools())
        
        logger.info("Запуск Security Tools MCP Agent...")
        demo.launch(share=True)
    except Exception as e:
        logger.error(f"Ошибка запуска приложения: {str(e)}")
        sys.exit(1)