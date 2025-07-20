#!/bin/bash
# ================================
# Docker 配置檔案建立腳本
# Docker Configuration Files Setup Script
# ================================

set -e

# 顏色定義
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

echo "🔧 建立 Docker 配置檔案..."

# 建立 docker 目錄
mkdir -p docker
print_success "建立 docker 目錄"

# 1. 建立 .env 檔案
print_info "建立 .env 檔案..."
cat > .env << 'EOF'
# ================================
# 市場分析報告系統 - 環境變數設定
# Market Analysis Report System - Environment Variables
# ================================

# 基本配置 Basic Configuration
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO
BUILD_DATE=$(date -u +'%Y-%m-%dT%H:%M:%SZ')

# 伺服器配置 Server Configuration
SERVER_HOST=0.0.0.0
SERVER_PORT=8089

# Webhook 配置 Webhook Configuration
WEBHOOK_URL=https://beloved-swine-sensibly.ngrok-free.app/webhook-test/ef5ac185-f41a-4a2d-9a78-33d329184c2
WEBHOOK_TIMEOUT=30

# ngrok 配置 ngrok Configuration
NGROK_AUTHTOKEN=2zzNP5hnqCVT1EkLieXmLyNEUnX_7RqY7RwqEPheVpbbeRRX6
NGROK_WEB_PORT=4041

# 安全配置 Security Configuration
API_KEY=
CORS_ORIGINS=*

# 功能開關 Feature Flags
ENABLE_METRICS=true
ENABLE_AUTO_BACKUP=false
USE_MOCK_DATA=false

# 快取配置 Cache Configuration
REDIS_PASSWORD=secure_cache_password_456

# 監控配置 Monitoring Configuration
PROMETHEUS_PORT=9090

# 資料庫配置 Database Configuration (Optional)
DB_NAME=market_analysis
DB_USER=market_user
DB_PASSWORD=secure_db_password_789
EOF
print_success "建立 .env 檔案"

# 2. 建立 Prometheus 配置
print_info "建立 Prometheus 配置..."
cat > docker/prometheus.yml << 'EOF'
# ================================
# Prometheus 配置檔案
# Prometheus Configuration File
# ================================

global:
  scrape_interval: 15s
  evaluation_interval: 15s
  external_labels:
    monitor: 'market-analysis-monitor'

rule_files:
  # - "alert_rules.yml"

scrape_configs:
  # 市場分析服務
  - job_name: 'market-analysis'
    static_configs:
      - targets: ['market-analysis:8089']
    metrics_path: '/metrics'
    scrape_interval: 30s
    scrape_timeout: 10s
    honor_labels: true
    params:
      format: ['prometheus']

  # Prometheus 自我監控
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']

  # Redis 監控（如果啟用）
  - job_name: 'redis'
    static_configs:
      - targets: ['market-cache:6379']
    scrape_interval: 30s

  # ngrok 監控
  - job_name: 'ngrok'
    static_configs:
      - targets: ['ngrok-market:4040']
    metrics_path: '/api/tunnels'
    scrape_interval: 60s

# 告警規則（可選）
# alerting:
#   alertmanagers:
#     - static_configs:
#         - targets:
#           - alertmanager:9093
EOF
print_success "建立 Prometheus 配置"

# 3. 建立 Docker ignore 檔案
print_info "建立 .dockerignore 檔案..."
cat > .dockerignore << 'EOF'
# ================================
# Docker Ignore 檔案
# Docker Ignore File
# ================================

# Git 相關
.git
.gitignore
.gitattributes

# IDE 檔案
.vscode/
.idea/
*.swp
*.swo
*~

# Python 相關
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg
MANIFEST

# 虛擬環境
venv/
env/
ENV/
.venv/

# 測試和覆蓋率
.coverage
.pytest_cache/
htmlcov/
.tox/
.nox/

# 日誌檔案
*.log
logs/
*.log.*

# 暫存檔案
*.tmp
*.temp
tmp/
temp/

# 備份檔案
backups/
*.backup
*.bak

# 快取檔案
cache/
.cache/
*.cache

# 資料檔案
data/
*.db
*.sqlite
*.sqlite3

# 環境變數檔案（敏感資訊）
.env.local
.env.production
secrets.env

# 文檔
README.md
CHANGELOG.md
docs/

# Docker 相關
Dockerfile.dev
docker-compose.dev.yml
docker-compose.override.yml

# macOS
.DS_Store

# Windows
Thumbs.db
ehthumbs.db
Desktop.ini

# 大型檔案
*.iso
*.dmg
*.zip
*.tar.gz
*.rar

# 媒體檔案
*.mp4
*.avi
*.mov
*.mp3
*.wav

# 編輯器備份
*~
*.orig
EOF
print_success "建立 .dockerignore 檔案"

# 4. 建立健康檢查腳本
print_info "建立健康檢查腳本..."
cat > docker/healthcheck.sh << 'EOF'
#!/bin/bash
# ================================
# Docker 健康檢查腳本
# Docker Health Check Script
# ================================

set -e

# 檢查服務是否回應
check_service() {
    local service_url="$1"
    local service_name="$2"

    if curl -f -s --max-time 10 "$service_url" > /dev/null 2>&1; then
        echo "✅ $service_name 服務正常"
        return 0
    else
        echo "❌ $service_name 服務異常"
        return 1
    fi
}

# 主要檢查
main() {
    echo "🔍 開始健康檢查..."

    # 檢查主服務
    check_service "http://localhost:8089/health" "市場分析"

    # 檢查 API 端點
    check_service "http://localhost:8089/api/current-data" "API"

    echo "✅ 所有檢查通過"
}

main "$@"
EOF

chmod +x docker/healthcheck.sh
print_success "建立健康檢查腳本"

# 5. 建立部署腳本
print_info "建立快速部署腳本..."
cat > deploy.sh << 'EOF'
#!/bin/bash
# ================================
# 快速部署腳本
# Quick Deployment Script
# ================================

set -e

# 顏色定義
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

print_info() { echo -e "${BLUE}ℹ️  $1${NC}"; }
print_success() { echo -e "${GREEN}✅ $1${NC}"; }
print_warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }
print_error() { echo -e "${RED}❌ $1${NC}"; }

# 檢查 Docker
check_docker() {
    if ! command -v docker &> /dev/null; then
        print_error "Docker 未安裝"
        exit 1
    fi

    if ! docker info &> /dev/null; then
        print_error "Docker 服務未運行"
        exit 1
    fi

    print_success "Docker 檢查通過"
}

# 檢查 Docker Compose
check_docker_compose() {
    if command -v docker-compose &> /dev/null; then
        COMPOSE_CMD="docker-compose"
    elif docker compose version &> /dev/null; then
        COMPOSE_CMD="docker compose"
    else
        print_error "Docker Compose 未安裝"
        exit 1
    fi

    print_success "Docker Compose 檢查通過"
}

# 顯示選單
show_menu() {
    echo ""
    echo "🚀 市場分析系統部署工具"
    echo "========================"
    echo "1. 完整部署 (建議)"
    echo "2. 僅部署核心服務"
    echo "3. 開發模式部署"
    echo "4. 重建並部署"
    echo "5. 停止所有服務"
    echo "6. 查看服務狀態"
    echo "7. 查看服務日誌"
    echo "8. 清理系統"
    echo "9. 退出"
    echo ""
}

# 完整部署
full_deploy() {
    print_info "開始完整部署..."

    # 設定環境變數
    export BUILD_DATE=$(date -u +'%Y-%m-%dT%H:%M:%SZ')

    # 停止現有服務
    $COMPOSE_CMD down --remove-orphans

    # 建構並啟動
    $COMPOSE_CMD up --build -d

    # 等待服務啟動
    print_info "等待服務啟動..."
    sleep 15

    # 檢查服務狀態
    $COMPOSE_CMD ps

    print_success "完整部署完成"
    show_access_info
}

# 核心服務部署
core_deploy() {
    print_info "部署核心服務..."

    export BUILD_DATE=$(date -u +'%Y-%m-%dT%H:%M:%SZ')

    $COMPOSE_CMD down market-analysis --remove-orphans
    $COMPOSE_CMD up --build -d market-analysis

    print_success "核心服務部署完成"
    show_access_info
}

# 開發模式部署
dev_deploy() {
    print_info "開發模式部署..."

    export ENVIRONMENT=development
    export DEBUG=true
    export BUILD_DATE=$(date -u +'%Y-%m-%dT%H:%M:%SZ')

    $COMPOSE_CMD -f docker-compose.yml up --build -d

    print_success "開發模式部署完成"
    show_access_info
}

# 顯示訪問資訊
show_access_info() {
    local port=${SERVER_PORT:-8089}
    local ngrok_port=${NGROK_WEB_PORT:-4041}

    echo ""
    echo "🌐 服務訪問資訊："
    echo "  主服務: http://localhost:$port"
    echo "  API 文檔: http://localhost:$port/docs"
    echo "  健康檢查: http://localhost:$port/health"
    echo "  ngrok 管理: http://localhost:$ngrok_port"
    echo ""
}

# 主函數
main() {
    print_info "檢查系統需求..."
    check_docker
    check_docker_compose

    while true; do
        show_menu
        read -p "請選擇操作 (1-9): " choice

        case $choice in
            1) full_deploy ;;
            2) core_deploy ;;
            3) dev_deploy ;;
            4)
                print_info "重建並部署..."
                $COMPOSE_CMD down
                $COMPOSE_CMD build --no-cache
                $COMPOSE_CMD up -d
                show_access_info
                ;;
            5)
                print_info "停止所有服務..."
                $COMPOSE_CMD down
                print_success "所有服務已停止"
                ;;
            6)
                print_info "服務狀態："
                $COMPOSE_CMD ps
                ;;
            7)
                print_info "服務日誌："
                $COMPOSE_CMD logs -f --tail=50
                ;;
            8)
                print_warning "清理系統..."
                $COMPOSE_CMD down --volumes --remove-orphans
                docker system prune -f
                print_success "系統清理完成"
                ;;
            9)
                print_info "退出部署工具"
                exit 0
                ;;
            *)
                print_error "無效選項，請重新選擇"
                ;;
        esac

        echo ""
        read -p "按 Enter 繼續..."
    done
}

main "$@"
EOF

chmod +x deploy.sh
print_success "建立快速部署腳本"

# 6. 建立開發環境檔案
print_info "建立開發環境檔案..."
cat > .env.development << 'EOF'
# ================================
# 開發環境配置
# Development Environment Configuration
# ================================

# 基本配置
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=DEBUG

# 伺服器配置
SERVER_HOST=0.0.0.0
SERVER_PORT=8089

# Webhook 配置
WEBHOOK_URL=https://beloved-swine-sensibly.ngrok-free.app/webhook-test/ef5ac185-f41a-4a2d-9a78-33d329184c2
WEBHOOK_TIMEOUT=30

# ngrok 配置
NGROK_AUTHTOKEN=2zzNP5hnqCVT1EkLieXmLyNEUnX_7RqY7RwqEPheVpbbeRRX6
NGROK_WEB_PORT=4041

# 開發功能
USE_MOCK_DATA=true
ENABLE_AUTO_RELOAD=true
ENABLE_DEBUG_TOOLBAR=true

# 安全配置（開發環境較寬鬆）
CORS_ORIGINS=*
API_KEY=dev_api_key_123

# 功能開關
ENABLE_METRICS=true
ENABLE_AUTO_BACKUP=false
EOF
print_success "建立開發環境檔案"

# 7. 建立生產環境檔案範例
print_info "建立生產環境檔案範例..."
cat > .env.production.example << 'EOF'
# ================================
# 生產環境配置範例
# Production Environment Configuration Example
# ================================

# 基本配置
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=WARNING

# 伺服器配置
SERVER_HOST=0.0.0.0
SERVER_PORT=8089

# Webhook 配置（請替換為實際的 URL）
WEBHOOK_URL=https://your-production-webhook.example.com/webhook
WEBHOOK_TIMEOUT=30

# ngrok 配置（生產環境可能不需要）
# NGROK_AUTHTOKEN=your_production_ngrok_token
# NGROK_WEB_PORT=4041

# 安全配置
API_KEY=your_secure_api_key_here
CORS_ORIGINS=https://your-domain.com,https://api.your-domain.com

# 功能開關
ENABLE_METRICS=true
ENABLE_AUTO_BACKUP=true
USE_MOCK_DATA=false

# 資料庫配置（如果使用）
DB_NAME=market_analysis_prod
DB_USER=market_user_prod
DB_PASSWORD=very_secure_password_here

# 快取配置
REDIS_PASSWORD=very_secure_cache_password_here

# SSL 配置（如果使用）
# SSL_CERT_PATH=/app/certs/fullchain.pem
# SSL_KEY_PATH=/app/certs/privkey.pem
EOF
print_success "建立生產環境檔案範例"

# 8. 建立 Makefile
print_info "建立 Makefile..."
cat > Makefile << 'EOF'
# ================================
# 市場分析報告系統 Makefile
# Market Analysis Report System Makefile
# ================================

.PHONY: help build up down restart logs ps clean dev prod test lint format

# 預設目標
.DEFAULT_GOAL := help

# 變數定義
COMPOSE_CMD := $(shell which docker-compose 2>/dev/null || echo "docker compose")
PROJECT_NAME := market-analysis
BUILD_DATE := $(shell date -u +'%Y-%m-%dT%H:%M:%SZ')

# 顯示幫助資訊
help: ## 顯示此幫助訊息
	@echo "🚀 市場分析報告系統 - 開發工具"
	@echo "================================"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "\033[36m%-15s\033[0m %s\n", $1, $2}' $(MAKEFILE_LIST)

# 建構相關
build: ## 建構 Docker 映像
	@echo "🔨 建構 Docker 映像..."
	BUILD_DATE=$(BUILD_DATE) $(COMPOSE_CMD) build

build-no-cache: ## 重新建構 Docker 映像（不使用快取）
	@echo "🔨 重新建構 Docker 映像..."
	BUILD_DATE=$(BUILD_DATE) $(COMPOSE_CMD) build --no-cache

# 服務管理
up: ## 啟動所有服務
	@echo "🚀 啟動所有服務..."
	BUILD_DATE=$(BUILD_DATE) $(COMPOSE_CMD) up -d

up-build: ## 建構並啟動所有服務
	@echo "🚀 建構並啟動所有服務..."
	BUILD_DATE=$(BUILD_DATE) $(COMPOSE_CMD) up --build -d

down: ## 停止所有服務
	@echo "🛑 停止所有服務..."
	$(COMPOSE_CMD) down

restart: ## 重啟所有服務
	@echo "🔄 重啟所有服務..."
	$(COMPOSE_CMD) restart

# 開發模式
dev: ## 啟動開發模式
	@echo "🔧 啟動開發模式..."
	ENVIRONMENT=development DEBUG=true BUILD_DATE=$(BUILD_DATE) $(COMPOSE_CMD) up --build -d

dev-logs: ## 查看開發模式日誌
	@echo "📋 開發模式日誌..."
	$(COMPOSE_CMD) logs -f market-analysis

# 生產模式
prod: ## 啟動生產模式
	@echo "🏭 啟動生產模式..."
	ENVIRONMENT=production DEBUG=false BUILD_DATE=$(BUILD_DATE) $(COMPOSE_CMD) up --build -d

# 監控和日誌
logs: ## 查看服務日誌
	@echo "📋 查看服務日誌..."
	$(COMPOSE_CMD) logs -f

logs-app: ## 查看應用程式日誌
	@echo "📋 查看應用程式日誌..."
	$(COMPOSE_CMD) logs -f market-analysis

ps: ## 查看服務狀態
	@echo "📊 服務狀態..."
	$(COMPOSE_CMD) ps

# 測試和檢查
test: ## 執行測試
	@echo "🧪 執行測試..."
	$(COMPOSE_CMD) exec market-analysis python -m pytest

health: ## 檢查服務健康狀態
	@echo "🔍 檢查服務健康狀態..."
	$(COMPOSE_CMD) exec market-analysis python /app/healthcheck.py

# 進入容器
shell: ## 進入主容器的 shell
	@echo "🐚 進入主容器..."
	$(COMPOSE_CMD) exec market-analysis bash

shell-root: ## 以 root 身份進入主容器
	@echo "🐚 以 root 身份進入主容器..."
	$(COMPOSE_CMD) exec --user root market-analysis bash

# 清理和維護
clean: ## 清理停止的容器和未使用的映像
	@echo "🧹 清理系統..."
	docker system prune -f

clean-all: ## 徹底清理（包括資料卷）
	@echo "🧹 徹底清理系統..."
	$(COMPOSE_CMD) down --volumes --remove-orphans
	docker system prune -a -f --volumes

# 資料管理
backup: ## 建立資料備份
	@echo "💾 建立資料備份..."
	mkdir -p backups
	tar -czf backups/backup-$(shell date +%Y%m%d_%H%M%S).tar.gz data/ logs/

restore: ## 還原資料（需要指定 BACKUP_FILE）
	@echo "📥 還原資料..."
	@if [ -z "$(BACKUP_FILE)" ]; then \
		echo "❌ 請指定備份檔案: make restore BACKUP_FILE=backup-xxx.tar.gz"; \
		exit 1; \
	fi
	tar -xzf backups/$(BACKUP_FILE)

# 程式碼品質
lint: ## 檢查程式碼品質
	@echo "🔍 檢查程式碼品質..."
	$(COMPOSE_CMD) exec market-analysis python -m flake8 /app
	$(COMPOSE_CMD) exec market-analysis python -m black --check /app

format: ## 格式化程式碼
	@echo "✨ 格式化程式碼..."
	$(COMPOSE_CMD) exec market-analysis python -m black /app
	$(COMPOSE_CMD) exec market-analysis python -m isort /app

# 部署
deploy-staging: ## 部署到測試環境
	@echo "🚀 部署到測試環境..."
	ENVIRONMENT=staging $(MAKE) up-build

deploy-prod: ## 部署到生產環境
	@echo "🏭 部署到生產環境..."
	ENVIRONMENT=production $(MAKE) up-build

# 監控
stats: ## 查看 Docker 統計資訊
	@echo "📊 Docker 統計資訊..."
	docker stats --no-stream

top: ## 查看容器中的進程
	@echo "📊 容器進程..."
	$(COMPOSE_CMD) top

# 網路和連接測試
test-webhook: ## 測試 Webhook 連接
	@echo "🔗 測試 Webhook 連接..."
	$(COMPOSE_CMD) exec market-analysis curl -f http://localhost:8089/api/test-connection

test-health: ## 測試健康檢查端點
	@echo "🔍 測試健康檢查..."
	$(COMPOSE_CMD) exec market-analysis curl -f http://localhost:8089/health

# 配置管理
show-config: ## 顯示當前配置
	@echo "⚙️  當前配置..."
	$(COMPOSE_CMD) exec market-analysis python -c "import config; print(config.get_config_summary())"

show-env: ## 顯示環境變數
	@echo "🌍 環境變數..."
	$(COMPOSE_CMD) exec market-analysis env | grep -E "(WEBHOOK|SERVER|DEBUG|ENVIRONMENT)" | sort

# 快速操作
quick-start: ## 快速啟動（建構 + 啟動 + 查看日誌）
	@echo "⚡ 快速啟動..."
	$(MAKE) up-build
	@echo "⏳ 等待服務啟動..."
	@sleep 10
	$(MAKE) health
	$(MAKE) logs-app

quick-restart: ## 快速重啟主服務
	@echo "⚡ 快速重啟主服務..."
	$(COMPOSE_CMD) restart market-analysis
	@sleep 5
	$(MAKE) health

# 開發工具
install-dev: ## 安裝開發依賴
	@echo "📦 安裝開發依賴..."
	$(COMPOSE_CMD) exec market-analysis pip install -r requirements-dev.txt

update-deps: ## 更新依賴套件
	@echo "📦 更新依賴套件..."
	$(COMPOSE_CMD) exec market-analysis pip install --upgrade -r requirements.txt

# 說明文件
docs: ## 生成 API 文檔
	@echo "📚 API 文檔位置..."
	@echo "  Swagger UI: http://localhost:8089/docs"
	@echo "  ReDoc: http://localhost:8089/redoc"

# 安全檢查
security-scan: ## 執行安全掃描
	@echo "🔒 執行安全掃描..."
	$(COMPOSE_CMD) exec market-analysis python -m safety check
	$(COMPOSE_CMD) exec market-analysis python -m bandit -r /app

# 效能測試
load-test: ## 執行負載測試（需要安裝 locust）
	@echo "⚡ 執行負載測試..."
	@echo "請確保已安裝 locust: pip install locust"
	@echo "然後執行: locust -f tests/load_test.py --host=http://localhost:8089"
EOF
print_success "建立 Makefile"

# 顯示完成資訊
echo ""
echo "🎉 Docker 配置檔案建立完成！"
echo ""
echo "📁 建立的檔案："
echo "  ├── .env                    # 環境變數設定"
echo "  ├── .env.development        # 開發環境設定"
echo "  ├── .env.production.example # 生產環境設定範例"
echo "  ├── .dockerignore           # Docker 忽略檔案"
echo "  ├── deploy.sh              # 快速部署腳本"
echo "  ├── Makefile               # 開發工具"
echo "  └── docker/"
echo "      ├── prometheus.yml      # Prometheus 配置"
echo "      └── healthcheck.sh      # 健康檢查腳本"
echo ""
echo "🚀 快速開始："
echo "  1. 檢查配置: cat .env"
echo "  2. 快速部署: ./deploy.sh"
echo "  3. 或使用 Make: make quick-start"
echo "  4. 查看狀態: make ps"
echo "  5. 查看日誌: make logs"
echo ""
echo "🔧 自訂配置："
echo "  • 編輯 .env 檔案來修改設定"
echo "  • 複製 .env.production.example 到 .env.production 用於生產環境"
echo "  • 修改 docker/prometheus.yml 來自訂監控設定"
echo ""
print_warning "注意：請記得修改 .env 檔案中的敏感資訊（如 API 金鑰、密碼等）"