FROM python:3.10-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY semgrep_mcp.py .
EXPOSE 7864
CMD ["python", "semgrep_mcp.py"] 