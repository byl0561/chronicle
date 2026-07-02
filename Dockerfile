# ── 阶段 1：构建前端 ─────────────────────────────────────────────────────────
FROM node:20-slim AS frontend-build
WORKDIR /app
COPY frontend/package*.json ./
RUN npm install
COPY frontend/ .
RUN npm run build

# ── 阶段 2：后端 + nginx 运行时 ──────────────────────────────────────────────
FROM python:3.12-slim
LABEL org.opencontainers.image.title="chronicle"
LABEL org.opencontainers.image.description="慢性病指标记录与趋势监控"

RUN apt-get update && \
    apt-get install -y --no-install-recommends nginx && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# 前端构建产物交给 nginx
COPY --from=frontend-build /app/dist /usr/share/nginx/html
COPY nginx/nginx.conf /etc/nginx/conf.d/default.conf
RUN rm -f /etc/nginx/sites-enabled/default && touch /etc/nginx/auth.conf

# 后端
WORKDIR /app
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY backend/ .
RUN mkdir -p /app/data

COPY docker-entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 8080
CMD ["/entrypoint.sh"]
