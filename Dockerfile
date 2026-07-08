FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    ffmpeg \
    wget \
 && rm -rf /var/lib/apt/lists/*

# 安装 nodejs 构建前端
RUN apt-get update && apt-get install -y curl && \
    curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && \
    apt-get install -y nodejs && \
    rm -rf /var/lib/apt/lists/*

COPY pyproject.toml ./
RUN pip install --no-cache-dir .

COPY src/ ./src/

# 构建前端
WORKDIR /app/src/fronted
RUN npm install && npm run build

WORKDIR /app

EXPOSE 8000

CMD ["uvicorn", "src.amdl.server:app", "--host", "0.0.0.0", "--port", "8000"]