#!/bin/bash

# ================================
# 市場分析報告系統 - 完整部署腳本
# Market Analysis Report System - Complete Deployment Script
# ================================

set -e  # 遇到錯誤時停止執行

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# 系統資訊
SCRIPT_VERSION="1.2.0"
SYSTEM_NAME="Market Analysis Report System"
BUILD_DATE=$(date -u +'%Y-%m-%dT%H:%M:%SZ')

# 預設配置
DEFAULT_NGROK_TOKEN="2zzNP5hnqCVT1EkLieXmLyNEUnX_7RqY7RwqEPheVpbbeRRX6"
DEFAULT_SERVER_PORT="8089"
DEFAULT_NGROK_PORT="4041"
DEFAULT_WEBHOOK_URL="https://beloved-swine-sensibly.ngrok-free.app/webhook-test/ef5ac185-f41a-4a2d-9a78-33d329184c2"

# 讀取環境變數或使用預設值
NGROK_TOKEN="${NGROK_AUTHTOKEN:-$DEFAULT_NGROK_TOKEN}"
SERVER_PORT="${SERVER_PORT:-$DEFAULT_SERVER_PORT}"
NGROK_PORT="${NGROK_WEB_PORT:-$DEFAULT_NGROK_PORT}"
WEBHOOK_URL="${WEBHOOK_URL:-$DEFAULT_WEBHOOK_URL}"
ENVIRONMENT="${ENVIRONMENT:-production}"

# ================================
# 輔助函數 Helper Functions
# ================================

print_banner() {
    echo -e "${CYAN}"
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║                                                              ║"
    echo "║        🚀 市場分析報告系統部署工具 🚀                      ║"
    echo "║              Market Analysis Deployment Tool                 ║"
    echo "║                                                              ║"
    echo "║                    版本: ${SCRIPT_VERSION}                           ║"
    echo "║                 建置日期: ${BUILD_DATE}        ║"
    echo "║                                                              ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

print_section() {
    echo -e "\n${BLUE}════════════════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}🔧 $1${NC}"
    echo -e "${BLUE}════════════════════════════════════════════════════════════════${NC}"
}

print_step() {
    echo -e "\n${YELLOW}📋 $1${NC}"
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

print_info() {
    echo -e "${CYAN}ℹ️  $1${NC}"
}

# 檢查命令是否存在
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# 檢查端口是否被佔用
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        return 0  # 端口被佔用
    else
        return 1  # 端口可用
    fi
}

# 等待服務啟動
wait_for_service() {
    local url=$1
    local max_attempts=${2:-30}
    local attempt=1

    print_step "等待服務啟動: $url"

    while [ $attempt -le $max_attempts ]; do
        if curl -sf "$url" > /dev/null 2>&1; then
            print_success "服務已啟動 ($attempt/$max_attempts)"
            return 0
        else
            echo -n "."
            sleep 2
            ((attempt++))
        fi
    done

    print_error "服務啟動超時"
    return 1
}

# 檢查系統需求
check_system_requirements() {
    print_section "檢查系統需求"

    # 檢查作業系統
    print_step "檢查作業系統..."
    OS=$(uname -s)
    case $OS in
        Linux*)     MACHINE=Linux;;
        Darwin*)    MACHINE=Mac;;
        CYGWIN*)    MACHINE=Cygwin;;
        MINGW*)     MACHINE=MinGw;;
        *)          MACHINE="UNKNOWN:${OS}"
    esac
    print_success "作業系統: $MACHINE"

    # 檢查 Docker
    print_step "檢查 Docker..."
    if command_exists docker; then
        DOCKER_VERSION=$(docker --version | cut -d' ' -f3 | cut -d',' -f1)
        print_success "Docker 已安裝: $DOCKER_VERSION"
    else
        print_error "Docker 未安裝"
        echo "請訪問 https://docs.docker.com/get-docker/ 安裝 Docker"
        exit 1
    fi

    # 檢查 Docker Compose
    print_step "檢查 Docker Compose..."
    if command_exists docker-compose; then
        COMPOSE_VERSION=$(docker-compose --version | cut -d' ' -f3 | cut -d',' -f1)
        print_success "Docker Compose 已安裝: $COMPOSE_VERSION"
    elif docker compose version >/dev/null 2>&1; then
        COMPOSE_VERSION=$(docker compose version --short)
        print_success "Docker Compose (內建) 已安裝: $COMPOSE_VERSION"
        COMPOSE_CMD="docker compose"
    else
        print_error "Docker Compose 未安裝"
        echo "請安裝 Docker Compose 或使用較新版本的 Docker"
        exit 1
    fi

    # 設定 Docker Compose 命令
    COMPOSE_CMD=${COMPOSE_CMD:-"docker-compose"}

    # 檢查系統資源
    print_step "檢查系統資源..."

    # 檢查可用記憶體
    if [ "$MACHINE" = "Linux" ]; then
        TOTAL_MEM=$(free -m | awk 'NR==2{printf "%.0f", $2}')
        AVAIL_MEM=$(free -m | awk 'NR==2{printf "%.0f", $7}')
        print_info "總記憶體: ${TOTAL_MEM}MB, 可用記憶體: ${AVAIL_MEM}MB"

        if [ $AVAIL_MEM -lt 512 ]; then
            print_warning "可用記憶體不足 512MB，可能影響效能"
        fi
    fi

    # 檢查磁碟空間
    DISK_AVAIL=$(df . | tail -1 | awk '{print $4}')
    print_info "可用磁碟空間: $(( DISK_AVAIL / 1024 ))MB"

    if [ $DISK_AVAIL -lt 1048576 ]; then  # 1GB in KB
        print_warning "可用磁碟空間不足 1GB"
    fi
}

# 檢查端口可用性
check_ports() {
    print_section "檢查端口可用性"

    # 檢查主要服務端口
    print_step "檢查服務端口 $SERVER_PORT..."
    if check_port $SERVER_PORT; then
        print_error "端口 $SERVER_PORT 已被使用"
        print_info "請停止使用該端口的服務或修改 SERVER_PORT 環境變數"
        lsof -Pi :$SERVER_PORT -sTCP:LISTEN

        read -p "是否要嘗試停止現有服務？(y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            print_step "嘗試停止現有服務..."
            $COMPOSE_CMD down 2>/dev/null || true
            sleep 3

            if check_port $SERVER_PORT; then
                print_error "無法釋放端口 $SERVER_PORT"
                exit 1
            else
                print_success "端口 $SERVER_PORT 已釋放"
            fi
        else
            exit 1
        fi
    else
        print_success "端口 $SERVER_PORT 可用"
    fi

    # 檢查 ngrok 管理端口
    print_step "檢查 ngrok 管理端口 $NGROK_PORT..."
    if check_port $NGROK_PORT; then
        print_warning "端口 $NGROK_PORT 已被使用，將嘗試使用其他端口"

        # 尋找可用端口
        for port in 4042 4043 4044 4045; do
            if ! check_port $port; then
                print_success "使用端口 $port 作為 ngrok 管理端口"
                NGROK_PORT=$port
                export NGROK_WEB_PORT=$port
                break
            fi
        done

        if check_port $NGROK_PORT; then
            print_error "無法找到可用的 ngrok 管理端口"
            exit 1
        fi
    else
        print_success "ngrok 管理端口 $NGROK_PORT 可用"
    fi
}

# 準備環境配置
setup_environment() {
    print_section "準備環境配置"

    # 建立必要目錄
    print_step "建立必要目錄..."
    mkdir -p logs data backups docker
    print_success "目錄建立完成"

    # 檢查必要檔案
    print_step "檢查必要檔案..."
    local required_files=("Dockerfile" "docker-compose.yml" "main.py" "config.py")

    for file in "${required_files[@]}"; do
        if [ ! -f "$file" ]; then
            print_error "缺少必要檔案: $file"
            exit 1
        fi
    done
    print_success "所有必要檔案存在"

    # 檢查前端檔案
    print_step "檢查前端檔案..."
    if [ ! -d "frontend" ]; then
        print_warning "frontend 目錄不存在，建立中..."
        mkdir -p frontend/static
    fi

    # 建立環境變數檔案
    print_step "建立環境變數檔案..."
    cat > .env << EOF
# 系統配置
ENVIRONMENT=$ENVIRONMENT
BUILD_DATE=$BUILD_DATE
DEBUG=false

# 伺服器配置
SERVER_HOST=0.0.0.0
SERVER_PORT=$SERVER_PORT
LOG_LEVEL=INFO

# Webhook 配置
WEBHOOK_URL=$WEBHOOK_URL
WEBHOOK_TIMEOUT=30

# ngrok 配置
NGROK_AUTHTOKEN=$NGROK_TOKEN
NGROK_WEB_PORT=$NGROK_PORT

# 安全配置
API_KEY=
CORS_ORIGINS=*

# 功能開關
ENABLE_METRICS=true
ENABLE_AUTO_BACKUP=false
USE_MOCK_DATA=false
EOF
    print_success "環境變數檔案已建立"

    # 建立 Docker 配置檔案
    setup_docker_configs
}

# 建立 Docker 配置檔案
setup_docker_configs() {
    print_step "建立 Docker 配置檔案..."

    # ngrok 配置
    cat > docker/ngrok.yml << EOF
version: "2"
authtoken: $NGROK_TOKEN
tunnels:
  market-analysis:
    proto: http
    addr: market-analysis:8089
    region: ap
    bind_tls: true
    inspect: false
    metadata: "Market Analysis System"
log_level: info
log_format: term
EOF

    # Redis 配置
    cat > docker/redis.conf << EOF
# Redis 配置
maxmemory 128mb
maxmemory-policy allkeys-lru
save 900 1
save 300 10
save 60 10000
appendonly yes
appendfsync everysec
EOF

    # Fluent Bit 配置
    cat > docker/fluent-bit.conf << EOF
[SERVICE]
    Flush        1
    Log_Level    info
    Daemon       off
    Parsers_File parsers.conf

[INPUT]
    Name              tail
    Path              /var/log/market-analysis/*.log
    Parser            json
    Tag               market.logs
    Refresh_Interval  5

[OUTPUT]
    Name  stdout
    Match *
EOF

    # Prometheus 配置
    cat > docker/prometheus.yml << EOF
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'market-analysis'
    static_configs:
      - targets: ['market-analysis:8089']
    metrics_path: '/metrics'
    scrape_interval: 30s
EOF

    # 資料庫初始化腳本
    cat > docker/init-db.sql << EOF
-- 市場分析系統資料庫初始化
CREATE DATABASE IF NOT EXISTS market_analysis;

-- 建立使用者
CREATE USER IF NOT EXISTS 'market_user'@'%' IDENTIFIED BY 'secure_password_123';
GRANT ALL PRIVILEGES ON market_analysis.* TO 'market_user'@'%';
FLUSH PRIVILEGES;

-- 建立基本表格（如果需要）
USE market_analysis;

CREATE TABLE IF NOT EXISTS market_reports (
    id SERIAL PRIMARY KEY,
    sentiment_score DECIMAL(10,6),
    message_content TEXT,
    received_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_market_reports_received_time ON market_reports(received_time);
EOF

    print_success "Docker 配置檔案已建立"
}

# 建構和啟動服務
build_and_deploy() {
    print_section "建構和部署服務"

    # 停止現有服務
    print_step "停止現有服務..."
    $COMPOSE_CMD down --remove-orphans 2>/dev/null || true
    print_success "現有服務已停止"

    # 清理舊的映像（可選）
    if [ "${CLEAN_BUILD:-false}" = "true" ]; then
        print_step "清理舊的 Docker 映像..."
        docker system prune -f --volumes
        print_success "Docker 系統清理完成"
    fi

    # 建構映像
    print_step "建構 Docker 映像..."
    export BUILD_DATE
    $COMPOSE_CMD build --no-cache --pull
    print_success "Docker 映像建構完成"

    # 啟動服務
    print_step "啟動服務..."
    $COMPOSE_CMD up -d
    print_success "服務啟動命令已執行"

    # 等待服務啟動
    print_step "等待服務初始化..."
    sleep 15

    # 檢查服務狀態
    check_service_health
}

# 檢查服務健康狀態
check_service_health() {
    print_section "檢查服務健康狀態"

    # 檢查主要服務
    print_step "檢查市場分析服務..."
    if wait_for_service "http://localhost:$SERVER_PORT/health" 30; then
        print_success "市場分析服務運行正常"

        # 顯示服務資訊
        SERVICE_INFO=$(curl -s "http://localhost:$SERVER_PORT/health" | jq -r '.system + " v" + .version' 2>/dev/null || echo "服務已啟動")
        print_info "服務資訊: $SERVICE_INFO"
    else
        print_error "市場分析服務啟動失敗"
        print_info "檢查日誌："
        $COMPOSE_CMD logs market-analysis | tail -20
        return 1
    fi

    # 檢查 ngrok 服務
    print_step "檢查 ngrok 隧道服務..."
    if wait_for_service "http://localhost:$NGROK_PORT/api/tunnels" 20; then
        print_success "ngrok 隧道服務運行正常"

        # 獲取公開 URL
        sleep 5
        get_ngrok_url
    else
        print_warning "ngrok 服務啟動較慢，請稍後檢查"
        print_info "ngrok 管理介面: http://localhost:$NGROK_PORT"
    fi

    # 檢查所有容器狀態
    print_step "檢查容器狀態..."
    $COMPOSE_CMD ps
}

# 獲取 ngrok 公開 URL
get_ngrok_url() {
    print_step "獲取 ngrok 公開網址..."

    local max_attempts=10
    local attempt=1

    while [ $attempt -le $max_attempts ]; do
        NGROK_URL=$(curl -s "http://localhost:$NGROK_PORT/api/tunnels" 2>/dev/null | \
                   python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    for tunnel in data.get('tunnels', []):
        if tunnel.get('proto') == 'https':
            print(tunnel.get('public_url', ''))
            break
except:
    pass
" 2>/dev/null)

        if [ -n "$NGROK_URL" ]; then
            print_success "ngrok 公開網址: $NGROK_URL"
            echo "$NGROK_URL" > .ngrok_url
            return 0
        else
            print_info "嘗試獲取 ngrok URL... ($attempt/$max_attempts)"
            sleep 3
            ((attempt++))
        fi
    done

    print_warning "無法自動獲取 ngrok 公開網址"
    print_info "請稍後訪問 http://localhost:$NGROK_PORT 手動查看"
}

# 執行測試
run_tests() {
    print_section "執行系統測試"

    # 測試健康檢查端點
    print_step "測試健康檢查..."
    if curl -sf "http://localhost:$SERVER_PORT/health" > /dev/null; then
        print_success "健康檢查測試通過"
    else
        print_error "健康檢查測試失敗"
        return 1
    fi

    # 測試 API 端點
    print_step "測試 API 端點..."
    if curl -sf "http://localhost:$SERVER_PORT/api/current-data" > /dev/null; then
        print_success "API 端點測試通過"
    else
        print_error "API 端點測試失敗"
        return 1
    fi

    # 測試 Webhook 連接
    print_step "測試 Webhook 連接..."
    WEBHOOK_TEST=$(curl -s "http://localhost:$SERVER_PORT/api/test-connection" | jq -r '.status' 2>/dev/null || echo "error")

    if [ "$WEBHOOK_TEST" = "success" ]; then
        print_success "Webhook 連接測試通過"
    else
        print_warning "Webhook 連接測試失敗（這不一定表示問題）"
        print_info "請確認目標 Webhook URL 正確且可訪問"
    fi

    print_success "系統測試完成"
}

# 顯示部署摘要
show_deployment_summary() {
    print_section "部署摘要"

    echo -e "${GREEN}"
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║                                                              ║"
    echo "║                 🎉 部署成功完成！ 🎉                       ║"
    echo "║                                                              ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"

    print_info "📋 服務資訊："
    echo "  • 市場分析系統: http://localhost:$SERVER_PORT"
    echo "  • API 文檔: http://localhost:$SERVER_PORT/docs"
    echo "  • 系統健康: http://localhost:$SERVER_PORT/health"
    echo "  • ngrok 管理: http://localhost:$NGROK_PORT"

    if [ -f ".ngrok_url" ]; then
        NGROK_URL=$(cat .ngrok_url)
        print_info "🌐 公開網址："
        echo "  • 外部訪問: $NGROK_URL"
        echo "  • N8N 端點: $NGROK_URL/api/n8n-data"
        echo "  • Webhook 測試: $NGROK_URL/api/test-connection"
    fi

    print_info "🔧 常用指令："
    echo "  • 查看日誌: $COMPOSE_CMD logs -f"
    echo "  • 停止服務: $COMPOSE_CMD down"
    echo "  • 重啟服務: $COMPOSE_CMD restart"
    echo "  • 查看狀態: $COMPOSE_CMD ps"
    echo "  • 服務擴縮: $COMPOSE_CMD up --scale market-analysis=2"
    echo "  • 進入容器: $COMPOSE_CMD exec market-analysis bash"

    print_info "📁 重要檔案："
    echo "  • 配置檔案: config.py"
    echo "  • 環境變數: .env"
    echo "  • 日誌檔案: logs/"
    echo "  • 資料備份: backups/"

    print_info "🔍 監控和除錯："
    echo "  • 容器狀態: docker ps"
    echo "  • 系統資源: docker stats"
    echo "  • 網路檢查: docker network ls"
    echo "  • 卷狀態: docker volume ls"

    print_info "⚠️  注意事項："
    echo "  • ngrok URL 可能會變更，請定期檢查"
    echo "  • 生產環境建議使用固定域名"
    echo "  • 定期檢查日誌檔案大小"
    echo "  • 建議設定自動備份"

    if [ "$ENVIRONMENT" = "development" ]; then
        print_warning "當前運行在開發模式，生產環境請設定 ENVIRONMENT=production"
    fi
}

# 清理和回滾
cleanup_and_rollback() {
    print_section "清理和回滾"

    print_step "停止所有服務..."
    $COMPOSE_CMD down --remove-orphans --volumes

    print_step "清理 Docker 資源..."
    docker system prune -f

    print_success "清理完成"
}

# 設定備份
setup_backup() {
    print_section "設定自動備份"

    # 建立備份腳本
    cat > backup.sh << 'EOF'
#!/bin/bash
# 市場分析系統備份腳本

BACKUP_DIR="backups"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="market_analysis_backup_$DATE.tar.gz"

echo "🔄 開始備份..."

# 建立備份目錄
mkdir -p $BACKUP_DIR

# 備份配置和資料
tar -czf "$BACKUP_DIR/$BACKUP_FILE" \
    --exclude='logs/*' \
    --exclude='backups/*' \
    --exclude='.git/*' \
    --exclude='__pycache__/*' \
    config.py .env docker/ data/ 2>/dev/null

if [ $? -eq 0 ]; then
    echo "✅ 備份完成: $BACKUP_FILE"

    # 清理舊備份（保留最近7個）
    ls -t "$BACKUP_DIR"/market_analysis_backup_*.tar.gz | tail -n +8 | xargs -r rm
    echo "🧹 已清理舊備份檔案"
else
    echo "❌ 備份失敗"
    exit 1
fi
EOF

    chmod +x backup.sh
    print_success "備份腳本已建立: ./backup.sh"

    # 建立 crontab 條目（可選）
    print_info "如需自動備份，請將以下行加入 crontab："
    echo "0 2 * * * $(pwd)/backup.sh"
}

# 效能調優
performance_tuning() {
    print_section "效能調優建議"

    print_info "🚀 效能最佳化建議："
    echo "  1. 調整 Docker 資源限制"
    echo "  2. 啟用 Redis 快取"
    echo "  3. 使用 nginx 反向代理"
    echo "  4. 設定 CDN 加速靜態資源"
    echo "  5. 監控系統資源使用"

    # 檢查系統資源
    if command_exists free; then
        echo ""
        print_info "📊 當前系統資源："
        free -h
        echo ""
        df -h . | head -2
    fi
}

# 安全強化
security_hardening() {
    print_section "安全強化"

    print_info "🔒 安全強化建議："
    echo "  1. 更改預設密碼和金鑰"
    echo "  2. 啟用 HTTPS"
    echo "  3. 設定防火牆規則"
    echo "  4. 定期更新依賴套件"
    echo "  5. 監控異常訪問"

    # 生成隨機 API 金鑰
    if command_exists openssl; then
        API_KEY=$(openssl rand -hex 32)
        print_info "🔑 建議使用的 API 金鑰："
        echo "  API_KEY=$API_KEY"
        echo ""
        print_warning "請將此金鑰加入 .env 檔案中"
    fi
}

# 故障排除
troubleshooting_guide() {
    print_section "故障排除指南"

    print_info "🔧 常見問題解決方案："
    echo ""
    echo "1. 端口被佔用："
    echo "   解決：$COMPOSE_CMD down && sudo lsof -ti:$SERVER_PORT | xargs sudo kill -9"
    echo ""
    echo "2. Docker 映像建構失敗："
    echo "   解決：docker system prune -f && $COMPOSE_CMD build --no-cache"
    echo ""
    echo "3. 服務無法啟動："
    echo "   檢查：$COMPOSE_CMD logs market-analysis"
    echo ""
    echo "4. ngrok 連接失敗："
    echo "   檢查：ngrok token 是否正確，網路是否正常"
    echo ""
    echo "5. Webhook 測試失敗："
    echo "   檢查：目標 URL 是否可訪問，防火牆設定"
}

# 顯示幫助資訊
show_help() {
    echo -e "${CYAN}市場分析報告系統部署腳本${NC}"
    echo ""
    echo "用法: $0 [選項]"
    echo ""
    echo "選項："
    echo "  -h, --help              顯示此幫助資訊"
    echo "  -v, --version           顯示版本資訊"
    echo "  -c, --check-only        僅檢查系統需求，不進行部署"
    echo "  -f, --full-deploy       完整部署（包含所有服務）"
    echo "  -m, --minimal           最小部署（僅核心服務）"
    echo "  -d, --dev               開發模式部署"
    echo "  -p, --production        生產模式部署"
    echo "  -b, --backup            執行備份"
    echo "  -r, --rollback          回滾和清理"
    echo "  -t, --test              執行系統測試"
    echo "  -s, --status            查看服務狀態"
    echo "  --clean                 清理重建"
    echo "  --no-ngrok              不啟動 ngrok 服務"
    echo ""
    echo "環境變數："
    echo "  NGROK_AUTHTOKEN         ngrok 認證 token"
    echo "  SERVER_PORT             伺服器端口 (預設: $DEFAULT_SERVER_PORT)"
    echo "  NGROK_WEB_PORT          ngrok 管理端口 (預設: $DEFAULT_NGROK_PORT)"
    echo "  WEBHOOK_URL             目標 webhook URL"
    echo "  ENVIRONMENT             運行環境 (development/production)"
    echo ""
    echo "範例："
    echo "  $0                      # 標準部署"
    echo "  $0 -d                   # 開發模式部署"
    echo "  $0 -p --clean           # 生產模式清理重建"
    echo "  $0 -c                   # 僅檢查系統需求"
    echo "  $0 -b                   # 執行備份"
}

# 顯示版本資訊
show_version() {
    echo "$SYSTEM_NAME"
    echo "部署腳本版本: $SCRIPT_VERSION"
    echo "建置日期: $BUILD_DATE"
}

# 查看服務狀態
show_status() {
    print_section "服務狀態"

    if ! command_exists docker-compose && ! docker compose version >/dev/null 2>&1; then
        print_error "Docker Compose 未安裝"
        return 1
    fi

    echo "📊 容器狀態："
    $COMPOSE_CMD ps 2>/dev/null || echo "沒有運行中的服務"

    echo ""
    echo "🌐 服務可用性："

    # 檢查主服務
    if curl -sf "http://localhost:$SERVER_PORT/health" >/dev/null 2>&1; then
        print_success "市場分析服務: 運行中"
        SERVICE_INFO=$(curl -s "http://localhost:$SERVER_PORT/health" | jq -r '.timestamp' 2>/dev/null || echo "")
        [ -n "$SERVICE_INFO" ] && echo "  最後檢查: $SERVICE_INFO"
    else
        print_error "市場分析服務: 離線"
    fi

    # 檢查 ngrok
    if curl -sf "http://localhost:$NGROK_PORT/api/tunnels" >/dev/null 2>&1; then
        print_success "ngrok 隧道: 運行中"
        if [ -f ".ngrok_url" ]; then
            NGROK_URL=$(cat .ngrok_url)
            echo "  公開網址: $NGROK_URL"
        fi
    else
        print_error "ngrok 隧道: 離線"
    fi

    echo ""
    echo "💾 資源使用："
    if command_exists docker; then
        docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}" 2>/dev/null | grep market || echo "沒有相關容器"
    fi
}

# 主函數
main() {
    # 解析命令列參數
    while [[ $# -gt 0 ]]; do
        case $1 in
            -h|--help)
                show_help
                exit 0
                ;;
            -v|--version)
                show_version
                exit 0
                ;;
            -c|--check-only)
                CHECK_ONLY=true
                shift
                ;;
            -f|--full-deploy)
                FULL_DEPLOY=true
                shift
                ;;
            -m|--minimal)
                MINIMAL_DEPLOY=true
                shift
                ;;
            -d|--dev)
                ENVIRONMENT="development"
                shift
                ;;
            -p|--production)
                ENVIRONMENT="production"
                shift
                ;;
            -b|--backup)
                BACKUP_ONLY=true
                shift
                ;;
            -r|--rollback)
                ROLLBACK_ONLY=true
                shift
                ;;
            -t|--test)
                TEST_ONLY=true
                shift
                ;;
            -s|--status)
                STATUS_ONLY=true
                shift
                ;;
            --clean)
                CLEAN_BUILD=true
                shift
                ;;
            --no-ngrok)
                NO_NGROK=true
                shift
                ;;
            *)
                print_error "未知選項: $1"
                show_help
                exit 1
                ;;
        esac
    done

    # 顯示標題
    print_banner

    # 根據選項執行對應操作
    if [ "${STATUS_ONLY:-false}" = "true" ]; then
        show_status
        exit 0
    fi

    if [ "${BACKUP_ONLY:-false}" = "true" ]; then
        setup_backup
        if [ -x "./backup.sh" ]; then
            ./backup.sh
        fi
        exit 0
    fi

    if [ "${ROLLBACK_ONLY:-false}" = "true" ]; then
        cleanup_and_rollback
        exit 0
    fi

    if [ "${TEST_ONLY:-false}" = "true" ]; then
        run_tests
        exit 0
    fi

    # 系統需求檢查
    check_system_requirements

    if [ "${CHECK_ONLY:-false}" = "true" ]; then
        print_success "系統需求檢查完成"
        exit 0
    fi

    # 檢查端口
    check_ports

    # 設定環境
    setup_environment

    # 建構和部署
    if build_and_deploy; then
        # 執行測試
        run_tests

        # 顯示部署摘要
        show_deployment_summary

        # 設定備份
        setup_backup

        # 效能調優建議
        performance_tuning

        # 安全強化建議
        security_hardening

        print_success "🎉 部署流程完成！"
    else
        print_error "部署失敗"
        troubleshooting_guide
        exit 1
    fi
}

# 錯誤處理
trap 'echo -e "\n${RED}❌ 部署過程中發生錯誤${NC}"; troubleshooting_guide; exit 1' ERR

# 中斷處理
trap 'echo -e "\n${YELLOW}⚠️  部署被中斷${NC}"; exit 130' INT

# 執行主函數
main "$@"