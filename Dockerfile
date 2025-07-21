# ================================
# 市場分析報告系統 - 更新版 Dockerfile
# Market Analysis Report System - Updated Dockerfile
# ================================

# 多階段建構 - 基礎映像
FROM python:3.11-slim as base

# 設定建構參數
ARG PYTHON_VERSION=3.11
ARG BUILD_DATE
ARG VCS_REF

# 設定標籤
LABEL maintainer="Market Analysis Team" \
      version="1.3.0" \
      description="Market Analysis Report System with Mail Sender" \
      python.version="${PYTHON_VERSION}" \
      build.date="${BUILD_DATE}" \
      vcs.ref="${VCS_REF}"

# 設定環境變數
ENV PYTHONPATH=/app \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    TZ=Asia/Taipei \
    DEBIAN_FRONTEND=noninteractive

# ================================
# 系統依賴安裝階段
# ================================
RUN apt-get update && apt-get install -y --no-install-recommends \
    # 基本工具
    curl \
    wget \
    ca-certificates \
    # 網路工具
    netcat-traditional \
    # 建構工具（編譯某些 Python 套件需要）
    gcc \
    g++ \
    libc6-dev \
    libffi-dev \
    # 時區設定
    tzdata \
    # 清理
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    && rm -rf /tmp/* \
    && rm -rf /var/tmp/*

# 設定時區
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# ================================
# 使用者建立階段
# ================================
# 建立應用程式使用者（安全考量）
RUN groupadd --gid 1000 appuser \
    && useradd --uid 1000 --gid 1000 --create-home --shell /bin/bash appuser

# ================================
# Python 依賴安裝階段
# ================================
# 設定工作目錄
WORKDIR /app

# 複製 requirements.txt 並安裝 Python 依賴
COPY requirements.txt .

# 升級 pip 並安裝依賴
RUN pip install --upgrade pip setuptools wheel \
    && pip install --no-cache-dir -r requirements.txt \
    && pip cache purge

# ================================
# 應用程式檔案複製階段
# ================================
# 複製主要應用程式檔案
COPY --chown=appuser:appuser main.py .
COPY --chown=appuser:appuser config.py .
COPY --chown=appuser:appuser models.py .

# 複製前端檔案
COPY --chown=appuser:appuser frontend/ ./frontend/

# 複製 Docker 相關檔案
COPY --chown=appuser:appuser docker-entrypoint.sh /usr/local/bin/
COPY --chown=appuser:appuser docker/ ./docker/

# 確保腳本有執行權限
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

# ================================
# 目錄建立階段
# ================================
# 建立必要的目錄
RUN mkdir -p /app/logs /app/data /app/cache /app/backups \
    && chown -R appuser:appuser /app/logs /app/data /app/cache /app/backups

# ================================
# 健康檢查腳本
# ================================
# 建立簡單的健康檢查腳本
RUN echo '#!/bin/bash\n\
import requests\n\
import sys\n\
try:\n\
    response = requests.get("http://localhost:8089/health", timeout=10)\n\
    if response.status_code == 200:\n\
        print("✅ 健康檢查通過")\n\
        sys.exit(0)\n\
    else:\n\
        print(f"❌ 健康檢查失敗: HTTP {response.status_code}")\n\
        sys.exit(1)\n\
except Exception as e:\n\
    print(f"❌ 健康檢查失敗: {e}")\n\
    sys.exit(1)' > /app/healthcheck.py && \
    chmod +x /app/healthcheck.py && \
    chown appuser:appuser /app/healthcheck.py

# ================================
# 安全性設定
# ================================
# 切換到非 root 使用者
USER appuser

# 設定預設環境變數
ENV SERVER_HOST=0.0.0.0 \
    SERVER_PORT=8089 \
    DEBUG=false \
    LOG_LEVEL=INFO \
    ENVIRONMENT=production

# ================================
# 暴露端口
# ================================
EXPOSE 8089

# ================================
# 健康檢查
# ================================
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python /app/healthcheck.py

# ================================
# 容器標籤
# ================================
LABEL org.opencontainers.image.title="Market Analysis System" \
      org.opencontainers.image.description="智能市場分析報告發送系統" \
      org.opencontainers.image.version="1.3.0" \
      org.opencontainers.image.created="${BUILD_DATE}" \
      org.opencontainers.image.source="https://github.com/your-org/market-analysis" \
      org.opencontainers.image.vendor="AI Development Team"

# ================================
# 啟動命令
# ================================
ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]
CMD ["python", "main.py"]

# ================================
# 建構說明
# ================================
# 建構命令範例:
# docker build --build-arg BUILD_DATE=$(date -u +'%Y-%m-%dT%H:%M:%SZ') -t market-analysis:latest .
#
# 運行命令範例:
# docker run -d --name market-analysis -p 8089:8089 \
#   -e WEBHOOK_URL=your_webhook_url \
#   -v $(pwd)/logs:/app/logs \
#   market-analysis:latest
#
# 除錯模式運行:
# docker run -it --rm --name market-analysis-debug -p 8089:8089 \
#   -e DEBUG=true \
#   -e LOG_LEVEL=DEBUG \
#   market-analysis:latest bash