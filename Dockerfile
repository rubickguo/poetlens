# 使用轻量级 Python 3.9 基础镜像
FROM python:3.9-slim

# 设置环境变量，防止 Python 生成 .pyc 文件，并让日志直接输出到终端
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# 设置工作目录
WORKDIR /app

# 安装系统依赖
# libjpeg-dev zlib1g-dev 用于 Pillow 图片处理
# default-libmysqlclient-dev build-essentialpkg-config 用于编译 mysqlclient/cryptography (虽然我们用 PyMySQL，但有时 Pillow 需要基础库)
# 既然用 PyMySQL，通常不需要 mysql client libs，但为了稳妥安装 Pillow 依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    libjpeg-dev \
    zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件并安装
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制项目所有文件
COPY . .

# 设置环境变量：照片根目录（NAS挂载点）
# 默认指向容器内的 /app/static/photos，你需要在与 docker run 时挂载 -v /your/nas/photos:/app/static/photos
ENV PHOTOS_ROOT=/app/static/photos

# 暴露端口
EXPOSE 5000

# 启动命令
CMD ["python", "server.py"]
