FROM python:3.10-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY detect_secrets_mcp.py .
EXPOSE 7861
CMD ["python", "detect_secrets_mcp.py"] 