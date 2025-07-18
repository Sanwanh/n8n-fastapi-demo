# ================================
# 市場分析報告系統 Dockerfile
# Market Analysis Report System Dockerfile
# ================================

# 使用 Python 3.11 官方 slim 映像作為基礎
FROM python:3.11-slim

# 設定建構參數
ARG PYTHON_VERSION=3.11
ARG BUILD_DATE
ARG VCS_REF

# 設定標籤
LABEL maintainer="Market Analysis Team" \
      version="1.2.0" \
      description="Market Analysis Report System" \
      python.version="${PYTHON_VERSION}" \
      build.date="${BUILD_DATE}" \
      vcs.ref="${VCS_REF}"

# 設定工作目錄
WORKDIR /app

# 設定環境變數
ENV PYTHONPATH=/app \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    TZ=Asia/Taipei \
    DEBIAN_FRONTEND=noninteractive

# 更新套件列表並安裝系統依賴
RUN apt-get update && apt-get install -y --no-install-recommends \
    # 基本工具
    curl \
    wget \
    ca-certificates \
    # 網路工具
    netcat-traditional \
    # 清理工具
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    && rm -rf /tmp/* \
    && rm -rf /var/tmp/*

# 建立應用程式使用者（安全考量）
RUN groupadd --gid 1000 appuser \
    && useradd --uid 1000 --gid 1000 --create-home --shell /bin/bash appuser

# 複製 requirements.txt 並安裝 Python 依賴
COPY requirements.txt .

# 升級 pip 並安裝依賴
RUN pip install --upgrade pip setuptools wheel \
    && pip install --no-cache-dir -r requirements.txt \
    && pip cache purge

# 複製應用程式檔案
COPY --chown=appuser:appuser main.py .
COPY --chown=appuser:appuser config.py .

# 複製前端檔案（如果存在）
COPY --chown=appuser:appuser frontend/ ./frontend/

# 建立必要的目錄並設定權限
RUN mkdir -p \
    frontend/static \
    logs \
    data \
    cache \
    backups \
    && chown -R appuser:appuser /app \
    && chmod -R 755 /app

# 建立日誌目錄的符號連結（方便容器外訪問）
RUN ln -sf /dev/stdout /app/logs/access.log \
    && ln -sf /dev/stderr /app/logs/error.log

# 切換到非特權使用者
USER appuser

# 暴露端口
EXPOSE 8089

# 設定健康檢查
HEALTHCHECK --interval=30s \
            --timeout=10s \
            --start-period=40s \
            --retries=3 \
            CMD curl -f http://localhost:8089/health || exit 1

# 設定啟動腳本
COPY --chown=appuser:appuser docker-entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

# 預設啟動命令
ENTRYPOINT ["docker-entrypoint.sh"]
CMD ["python", "main.py"]

# ================================
# 建構說明
# ================================
# 建構命令：
# docker build -t market-analysis:latest .
#
# 執行命令：
# docker run -d -p 8089:8089 --name market-analysis market-analysis:latest
#
# 開發模式：
# docker run -it -p 8089:8089 -v $(pwd):/app market-analysis:latest bash