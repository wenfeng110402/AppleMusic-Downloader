# ── 构建阶段：编译前端 ────────────────────────────────────
FROM node:20-alpine AS frontend-builder

WORKDIR /app
COPY src/fronted/ ./
RUN npm install && npm run build

# ── 运行阶段 ──────────────────────────────────────────────
FROM python:3.11-slim

WORKDIR /app

# 安装运行时依赖
RUN apt-get update && apt-get install -y \
    ffmpeg \
 && rm -rf /var/lib/apt/lists/*

# 复制后端源码并安装
COPY pyproject.toml ./
COPY src/amdl/ ./src/amdl/
RUN pip install --no-cache-dir .

# 复制前端构建产物
COPY --from=frontend-builder /app/out/ ./src/fronted/out/

EXPOSE 8000

CMD ["uvicorn", "src.amdl.server:app", "--host", "0.0.0.0", "--port", "8000"]