# 使用 Python 3.11 官方映像作為基礎
FROM python:3.11-slim

# 設定工作目錄
WORKDIR /app

# 設定環境變數
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV TZ=Asia/Taipei

# 安裝系統依賴
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 複製 requirements.txt 並安裝 Python 依賴
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 複製專案檔案
COPY main.py .
COPY config.py .
COPY frontend/ ./frontend/

# 建立必要的目錄
RUN mkdir -p frontend/static

# 設定正確的檔案權限
RUN chmod -R 755 /app

# 暴露端口
EXPOSE 8089

# 健康檢查
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8089/health || exit 1

# 啟動命令
CMD ["python", "main.py"]