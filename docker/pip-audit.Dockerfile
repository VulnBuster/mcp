FROM python:3.10-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY pip_audit_mcp.py .
EXPOSE 7862
CMD ["python", "pip_audit_mcp.py"] 