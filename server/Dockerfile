# 后端镜像（在 server 目录构建；线上部署见 ../deploy/）
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
# 国内服务器走清华镜像加速
RUN pip install --no-cache-dir -r requirements.txt \
    -i https://pypi.tuna.tsinghua.edu.cn/simple

COPY . .

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
