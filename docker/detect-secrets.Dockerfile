FROM python:3.10-slim
WORKDIR /app

# Install build tools
RUN apt-get update && apt-get install -y build-essential

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY detect_secrets_mcp.py .
EXPOSE 7861
CMD ["python", "detect_secrets_mcp.py"] 