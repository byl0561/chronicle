#!/bin/sh
# 容器启动脚本：
#   1. 根据 APP_PASSWORD 生成 nginx Basic Auth 配置（留空则不启用）
#   2. 后台启动 nginx
#   3. 前台启动 gunicorn（FastAPI）
set -e

: > /etc/nginx/auth.conf
if [ -n "$APP_PASSWORD" ]; then
  python3 -c "
import base64, hashlib, os
u = os.environ.get('APP_USERNAME') or 'chronicle'
p = os.environ['APP_PASSWORD']
h = base64.b64encode(hashlib.sha1(p.encode()).digest()).decode()
open('/etc/nginx/.htpasswd','w').write(u + ':{SHA}' + h + '\n')
"
  printf 'auth_basic "Chronicle";\nauth_basic_user_file /etc/nginx/.htpasswd;\n' > /etc/nginx/auth.conf
  echo "entrypoint: Basic Auth ENABLED for user ${APP_USERNAME:-chronicle}" >&2
else
  echo "entrypoint: APP_PASSWORD empty → Basic Auth DISABLED" >&2
fi

nginx -g 'daemon off;' &

exec gunicorn app.main:app \
  -k uvicorn.workers.UvicornWorker \
  --bind 127.0.0.1:8000 \
  --workers "${GUNICORN_WORKERS:-2}" \
  --timeout "${GUNICORN_TIMEOUT:-120}" \
  --access-logfile - \
  --error-logfile -
