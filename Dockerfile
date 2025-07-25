# 多階段建構 - 基礎映像
FROM python:3.11-slim AS base

# 設定建構參數
ARG BUILD_DATE
ARG VCS_REF

# 設定標籤
LABEL maintainer="Market Analysis Team" \
    version="2.1.0" \
    description="Market Analysis System with Gold Price & Mail Sender" \
    python.version="3.11" \
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

# 系統依賴安裝
RUN apt-get update && apt-get install -y --no-install-recommends \
    # 基本工具
    curl \
    wget \
    ca-certificates \
    # 網路工具
    netcat-traditional \
    # 建構工具（編譯 numpy, pandas 等需要）
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

# 建立應用程式使用者
RUN groupadd --gid 1000 appuser \
    && useradd --uid 1000 --gid 1000 --create-home --shell /bin/bash appuser

# 設定工作目錄
WORKDIR /app

# 複製 requirements.txt 並安裝 Python 依賴
COPY requirements.txt .

# 升級 pip 並安裝依賴
RUN pip install --upgrade pip setuptools wheel \
    && pip install --no-cache-dir -r requirements.txt

# 複製應用程式檔案
COPY --chown=appuser:appuser main.py .

# 複製前端檔案（如果存在）
COPY --chown=appuser:appuser frontend/ ./frontend/

# 建立 docker-entrypoint.sh
RUN echo '#!/bin/bash\n\
    set -e\n\
    \n\
    # 顏色定義\n\
    GREEN="\\033[0;32m"\n\
    BLUE="\\033[0;34m"\n\
    NC="\\033[0m"\n\
    \n\
    print_info() {\n\
    echo -e "${BLUE}ℹ️  $1${NC}"\n\
    }\n\
    \n\
    print_success() {\n\
    echo -e "${GREEN}✅ $1${NC}"\n\
    }\n\
    \n\
    echo "🚀 市場分析系統啟動中..."\n\
    print_info "容器啟動時間: $(date)"\n\
    print_info "Python 版本: $(python --version)"\n\
    print_info "工作目錄: $(pwd)"\n\
    \n\
    # 檢查環境變數\n\
    print_info "環境配置:"\n\
    echo "  ENVIRONMENT: ${ENVIRONMENT:-development}"\n\
    echo "  DEBUG: ${DEBUG:-False}"\n\
    echo "  SERVER_HOST: ${SERVER_HOST:-0.0.0.0}"\n\
    echo "  SERVER_PORT: ${SERVER_PORT:-8089}"\n\
    echo "  LOG_LEVEL: ${LOG_LEVEL:-INFO}"\n\
    \n\
    # 檢查必要檔案\n\
    if [ ! -f "/app/main.py" ]; then\n\
    echo "❌ 找不到 main.py 檔案"\n\
    exit 1\n\
    fi\n\
    \n\
    print_success "檔案檢查完成"\n\
    \n\
    # 建立必要目錄\n\
    mkdir -p /app/logs /app/data /app/cache /app/backups\n\
    \n\
    print_success "目錄建立完成"\n\
    \n\
    # 顯示啟動資訊\n\
    echo ""\n\
    echo "╔══════════════════════════════════════════════════════════════╗"\n\
    echo "║                   🌟 應用程序啟動中 🌟                     ║"\n\
    echo "║                                                              ║"\n\
    echo "║  Web 介面: http://0.0.0.0:${SERVER_PORT:-8089}                    ║"\n\
    echo "║  API 文檔: http://0.0.0.0:${SERVER_PORT:-8089}/api/docs           ║"\n\
    echo "║  健康檢查: http://0.0.0.0:${SERVER_PORT:-8089}/health             ║"\n\
    echo "║                                                              ║"\n\
    echo "║  按 Ctrl+C 停止應用程序                                      ║"\n\
    echo "╚══════════════════════════════════════════════════════════════╝"\n\
    echo ""\n\
    \n\
    # 執行傳入的命令\n\
    exec "$@"\n\
    ' > /usr/local/bin/docker-entrypoint.sh && \
    chmod +x /usr/local/bin/docker-entrypoint.sh

# 確保腳本有執行權限（已在上面設定）

# 建立必要目錄
RUN mkdir -p /app/logs /app/data /app/cache /app/backups \
    && chown -R appuser:appuser /app/logs /app/data /app/cache /app/backups

# 建立健康檢查腳本
RUN echo '#!/usr/bin/env python3\n\
    import requests\n\
    import sys\n\
    \n\
    def check_service():\n\
    try:\n\
    # 檢查 API 健康\n\
    response = requests.get("http://localhost:8089/health", timeout=10)\n\
    if response.status_code != 200:\n\
    return False\n\
    # 檢查主頁\n\
    response = requests.get("http://localhost:8089/", timeout=10)\n\
    if response.status_code != 200:\n\
    return False\n\
    return True\n\
    except:\n\
    return False\n\
    \n\
    if __name__ == "__main__":\n\
    if check_service():\n\
    print("✅ 服務健康")\n\
    sys.exit(0)\n\
    else:\n\
    print("❌ 服務異常")\n\
    sys.exit(1)\n\
    ' > /app/healthcheck.py && \
    chmod +x /app/healthcheck.py && \
    chown appuser:appuser /app/healthcheck.py

# 設定預設環境變數
ENV SERVER_HOST=0.0.0.0 \
    SERVER_PORT=8089 \
    DEBUG=false \
    LOG_LEVEL=INFO \
    ENVIRONMENT=production

# 切換到非 root 使用者
USER appuser

# 暴露端口
EXPOSE 8089

# 健康檢查
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD python /app/healthcheck.py

# 容器標籤
LABEL org.opencontainers.image.title="Market Analysis System" \
    org.opencontainers.image.description="智能市場分析報告發送系統 with Gold Price" \
    org.opencontainers.image.version="2.1.0" \
    org.opencontainers.image.created="${BUILD_DATE}" \
    org.opencontainers.image.vendor="AI Development Team"

# 啟動命令
ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]
CMD ["python", "main.py"]