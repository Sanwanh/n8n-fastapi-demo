# ================================
# 市場分析報告系統 - 修正版 Dockerfile
# Market Analysis Report System - Fixed Dockerfile
# ================================

# 多階段建構 - 基礎映像
FROM python:3.11-slim as base

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
    # 建構工具（編譯某些 Python 套件需要）
    gcc \
    g++ \
    libc6-dev \
    libffi-dev \
    # 清理
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    && rm -rf /tmp/* \
    && rm -rf /var/tmp/*

# 建立應用程式使用者（安全考量）
RUN groupadd --gid 1000 appuser \
    && useradd --uid 1000 --gid 1000 --create-home --shell /bin/bash appuser

# 設定工作目錄
WORKDIR /app

# 複製 requirements.txt 並安裝 Python 依賴
COPY requirements.txt .

# 升級 pip 並安裝依賴
RUN pip install --upgrade pip setuptools wheel \
    && pip install --no-cache-dir -r requirements.txt \
    && pip cache purge

# 複製應用程式檔案
COPY --chown=appuser:appuser main.py .
COPY --chown=appuser:appuser config.py .
COPY --chown=appuser:appuser models.py .

# 複製前端檔案
COPY --chown=app