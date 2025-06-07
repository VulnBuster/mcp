FROM python:3.10-slim
WORKDIR /app

# Install build tools
RUN apt-get update && apt-get install -y build-essential

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY circle_test_mcp.py .
EXPOSE 7863
CMD ["python", "circle_test_mcp.py"] 