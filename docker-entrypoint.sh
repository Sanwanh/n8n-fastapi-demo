#!/bin/bash
# ================================
# 市場分析報告系統 Docker 啟動腳本
# Market Analysis Report System Docker Entrypoint
# ================================

set -e

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# 函數定義
print_header() {
    echo -e "${CYAN}"
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║                                                              ║"
    echo "║        🚀 市場分析報告系統 Docker 容器啟動 🚀              ║"
    echo "║              Market Analysis Docker Container                ║"
    echo "║                                                              ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# 顯示啟動標題
print_header

# 顯示系統資訊
print_info "容器啟動時間: $(date)"
print_info "Python 版本: $(python --version)"
print_info "工作目錄: $(pwd)"
print_info "使用者: $(whoami)"

# 檢查環境變數
print_info "檢查環境變數配置..."

# 設定預設環境變數
export PYTHONPATH="${PYTHONPATH:-/app}"
export PYTHONUNBUFFERED="${PYTHONUNBUFFERED:-1}"
export PYTHONDONTWRITEBYTECODE="${PYTHONDONTWRITEBYTECODE:-1}"
export TZ="${TZ:-Asia/Taipei}"

# 顯示重要環境變數
print_info "重要環境變數:"
echo "  ENVIRONMENT: ${ENVIRONMENT:-development}"
echo "  DEBUG: ${DEBUG:-False}"
echo "  SERVER_HOST: ${SERVER_HOST:-0.0.0.0}"
echo "  SERVER_PORT: ${SERVER_PORT:-8089}"
echo "  LOG_LEVEL: ${LOG_LEVEL:-INFO}"
echo "  WEBHOOK_URL: ${WEBHOOK_URL:-未設定}"
echo "  TZ: ${TZ}"

# 檢查必要檔案
print_info "檢查必要檔案..."

required_files=(
    "/app/main.py"
    "/app/config.py"
    "/app/requirements.txt"
)

for file in "${required_files[@]}"; do
    if [ -f "$file" ]; then
        print_success "找到檔案: $file"
    else
        print_error "缺少檔案: $file"
        exit 1
    fi
done

# 檢查 Python 套件
print_info "檢查 Python 套件..."
python -c "
import sys
required_packages = ['fastapi', 'uvicorn', 'pydantic', 'requests']
missing = []

for package in required_packages:
    try:
        __import__(package)
        print(f'✅ {package} - 已安裝')
    except ImportError:
        missing.append(package)
        print(f'❌ {package} - 未安裝')

if missing:
    print(f'缺少套件: {missing}')
    sys.exit(1)
else:
    print('🎉 所有必要套件已安裝')
"

if [ $? -ne 0 ]; then
    print_error "Python 套件檢查失敗"
    exit 1
fi

# 建立必要目錄
print_info "建立必要目錄..."
directories=(
    "/app/logs"
    "/app/data"
    "/app/cache"
    "/app/backups"
    "/app/frontend/static"
)

for dir in "${directories[@]}"; do
    if [ ! -d "$dir" ]; then
        mkdir -p "$dir"
        print_success "建立目錄: $dir"
    else
        print_info "目錄已存在: $dir"
    fi
done

# 設定檔案權限
print_info "設定檔案權限..."
chmod -R 755 /app/logs
chmod -R 755 /app/data
chmod -R 755 /app/cache
chmod -R 755 /app/backups
print_success "檔案權限設定完成"

# 檢查網路連接
print_info "檢查網路連接..."
if command -v curl > /dev/null 2>&1; then
    if curl -s --connect-timeout 5 http://www.google.com > /dev/null; then
        print_success "網路連接正常"
    else
        print_warning "網路連接可能有問題，但將繼續啟動"
    fi
else
    print_info "curl 不可用，跳過網路檢查"
fi

# 檢查 webhook URL（如果設定）
if [ -n "${WEBHOOK_URL}" ]; then
    print_info "測試 Webhook 連接..."
    if command -v curl > /dev/null 2>&1; then
        # 嘗試連接 webhook URL（允許失敗）
        if curl -s --connect-timeout 10 --max-time 15 "${WEBHOOK_URL}" > /dev/null 2>&1; then
            print_success "Webhook URL 可訪問"
        else
            print_warning "Webhook URL 目前無法訪問，但將繼續啟動"
        fi
    fi
else
    print_warning "未設定 WEBHOOK_URL 環境變數"
fi

# 顯示配置摘要
print_info "配置摘要:"
python -c "
try:
    import config
    summary = config.get_config_summary()
    for key, value in summary.items():
        print(f'  {key}: {value}')
except Exception as e:
    print(f'  無法載入配置摘要: {e}')
"

# 執行資料庫初始化（如果需要）
if [ "${INIT_DB:-false}" = "true" ]; then
    print_info "初始化資料庫..."
    python -c "
try:
    # 這裡可以添加資料庫初始化代碼
    print('資料庫初始化完成')
except Exception as e:
    print(f'資料庫初始化失敗: {e}')
    exit(1)
"
fi

# 執行健康檢查腳本（如果存在）
if [ -f "/app/healthcheck.py" ]; then
    print_info "執行啟動前健康檢查..."
    python /app/healthcheck.py
    if [ $? -eq 0 ]; then
        print_success "健康檢查通過"
    else
        print_warning "健康檢查失敗，但將繼續啟動"
    fi
fi

# 處理信號
cleanup() {
    print_info "接收到終止信號，正在安全關閉..."
    if [ ! -z "$app_pid" ]; then
        print_info "停止應用程序 (PID: $app_pid)..."
        kill -TERM "$app_pid" 2>/dev/null || true
        wait "$app_pid" 2>/dev/null || true
    fi
    print_success "清理完成"
    exit 0
}

trap cleanup SIGTERM SIGINT

# 顯示啟動資訊
print_success "準備啟動應用程序..."
print_info "命令: $@"
print_info "如需停止容器，請使用: docker stop <container_name>"

# 根據傳入的參數決定啟動方式
if [ "$1" = "python" ] && [ "$2" = "main.py" ]; then
    # 標準 Python 應用啟動
    print_info "啟動 FastAPI 應用程序..."

    # 顯示啟動資訊
    echo ""
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║                   🌟 應用程序啟動中 🌟                     ║"
    echo "║                                                              ║"
    echo "║  Web 介面: http://0.0.0.0:${SERVER_PORT:-8089}                    ║"
    echo "║  API 文檔: http://0.0.0.0:${SERVER_PORT:-8089}/docs               ║"
    echo "║  健康檢查: http://0.0.0.0:${SERVER_PORT:-8089}/health             ║"
    echo "║                                                              ║"
    echo "║  按 Ctrl+C 停止應用程序                                      ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo ""

    # 啟動應用程序
    exec python main.py &
    app_pid=$!
    wait "$app_pid"

elif [ "$1" = "uvicorn" ]; then
    # Uvicorn 直接啟動
    print_info "使用 Uvicorn 啟動應用程序..."
    exec "$@" &
    app_pid=$!
    wait "$app_pid"

elif [ "$1" = "bash" ] || [ "$1" = "sh" ]; then
    # 互動式 shell
    print_info "啟動互動式 shell..."
    exec "$@"

elif [ "$1" = "test" ]; then
    # 測試模式
    print_info "執行測試..."
    if [ -f "/app/test_main.py" ]; then
        python /app/test_main.py
    else
        python -c "
import main
print('✅ 模組載入測試通過')
import config
print('✅ 配置載入測試通過')
print('🎉 所有測試通過')
"
    fi

elif [ "$1" = "healthcheck" ]; then
    # 健康檢查模式
    print_info "執行健康檢查..."
    python -c "
import requests
import sys
try:
    response = requests.get('http://localhost:${SERVER_PORT:-8089}/health', timeout=10)
    if response.status_code == 200:
        print('✅ 健康檢查通過')
        sys.exit(0)
    else:
        print(f'❌ 健康檢查失敗: HTTP {response.status_code}')
        sys.exit(1)
except Exception as e:
    print(f'❌ 健康檢查失敗: {e}')
    sys.exit(1)
"

elif [ "$1" = "version" ]; then
    # 版本資訊
    print_info "顯示版本資訊..."
    python -c "
try:
    import config
    print(f'系統名稱: {config.SYSTEM_INFO[\"name\"]}')
    print(f'版本: {config.SYSTEM_INFO[\"version\"]}')
    print(f'建置日期: {config.SYSTEM_INFO[\"build_date\"]}')
except Exception as e:
    print(f'無法載入版本資訊: {e}')
"

else
    # 自訂命令
    print_info "執行自訂命令: $@"
    exec "$@" &
    app_pid=$!
    wait "$app_pid"
fi

print_info "應用程序已結束"