#!/bin/bash

# 市場分析報告系統 Docker 部署腳本
# Market Analysis Report System Docker Deployment Script

set -e  # 遇到錯誤時停止執行

# 更新的 ngrok token
NGROK_TOKEN="2zzNP5hnqCVT1EkLieXmLyNEUnX_7RqY7RwqEPheVpbbeRRX6"

echo "🚀 開始部署市場分析報告系統..."
echo "================================================"

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 檢查端口是否被佔用
check_ports() {
    echo -e "${BLUE}🔍 檢查端口使用情況...${NC}"

    # 檢查 8089 端口
    if lsof -Pi :8089 -sTCP:LISTEN -t >/dev/null 2>&1; then
        echo -e "${RED}❌ 端口 8089 已被使用${NC}"
        echo "請停止使用該端口的服務或修改配置"
        lsof -Pi :8089 -sTCP:LISTEN
        exit 1
    fi

    # 檢查 4041 端口 (我們的 ngrok 管理端口)
    if lsof -Pi :4041 -sTCP:LISTEN -t >/dev/null 2>&1; then
        echo -e "${YELLOW}⚠️ 端口 4041 已被使用，嘗試使用其他端口...${NC}"
        # 自動選擇可用端口
        for port in 4042 4043 4044 4045; do
            if ! lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
                echo -e "${GREEN}✅ 使用端口 $port 作為 ngrok 管理端口${NC}"
                # 動態修改 docker-compose.yml
                sed -i.bak "s/4041:4040/$port:4040/g" docker-compose.yml
                NGROK_PORT=$port
                break
            fi
        done

        if [ -z "$NGROK_PORT" ]; then
            echo -e "${RED}❌ 無法找到可用的 ngrok 管理端口${NC}"
            exit 1
        fi
    else
        NGROK_PORT=4041
    fi

    echo -e "${GREEN}✅ 端口檢查完成${NC}"
    echo -e "${BLUE}   - 應用服務端口: 8089${NC}"
    echo -e "${BLUE}   - ngrok 管理端口: $NGROK_PORT${NC}"
}

# 檢查 Docker 是否已安裝
check_docker() {
    if ! command -v docker &> /dev/null; then
        echo -e "${RED}❌ Docker 未安裝，請先安裝 Docker${NC}"
        echo "請訪問 https://docs.docker.com/get-docker/ 安裝 Docker"
        exit 1
    fi
    echo -e "${GREEN}✅ Docker 已安裝${NC}"
}

# 檢查 Docker Compose 是否已安裝
check_docker_compose() {
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        echo -e "${RED}❌ Docker Compose 未安裝${NC}"
        echo "請安裝 Docker Compose 或使用較新版本的 Docker"
        exit 1
    fi
    echo -e "${GREEN}✅ Docker Compose 已安裝${NC}"
}

# 檢查必要檔案
check_files() {
    local required_files=("Dockerfile" "docker-compose.yml" "main.py" "config.py" "requirements.txt")

    for file in "${required_files[@]}"; do
        if [ ! -f "$file" ]; then
            echo -e "${RED}❌ 缺少必要檔案: $file${NC}"
            exit 1
        fi
    done
    echo -e "${GREEN}✅ 所有必要檔案存在${NC}"
}

# 檢查 frontend 目錄
check_frontend() {
    if [ ! -d "frontend/static" ]; then
        echo -e "${YELLOW}⚠️ 建立 frontend/static 目錄${NC}"
        mkdir -p frontend/static
    fi

    if [ ! -f "frontend/static/style.css" ] || [ ! -f "frontend/static/script.js" ]; then
        echo -e "${RED}❌ 缺少前端檔案 (style.css 或 script.js)${NC}"
        echo "請確保 frontend/static/ 目錄包含必要的 CSS 和 JS 檔案"
        exit 1
    fi
    echo -e "${GREEN}✅ 前端檔案檢查完成${NC}"
}

# 檢查 Gmail 配置
check_gmail_config() {
    if grep -q "your_email@gmail.com" config.py || grep -q "your_app_password" config.py; then
        echo -e "${YELLOW}⚠️ 請先設定 Gmail 配置${NC}"
        echo "請編輯 config.py 檔案，填入您的 Gmail 帳號和應用程式密碼"
        read -p "已完成 Gmail 設定？(y/n): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            echo -e "${RED}❌ 請完成 Gmail 設定後再執行此腳本${NC}"
            exit 1
        fi
    fi
    echo -e "${GREEN}✅ Gmail 配置檢查完成${NC}"
}

# 停止並移除現有容器
cleanup_containers() {
    echo -e "${BLUE}🧹 清理現有容器...${NC}"

    # 停止可能運行的相關容器
    if docker ps -q --filter "name=market-analysis" | grep -q .; then
        echo "停止現有 market-analysis 容器..."
        docker stop $(docker ps -q --filter "name=market-analysis") 2>/dev/null || true
        docker rm $(docker ps -aq --filter "name=market-analysis") 2>/dev/null || true
    fi

    if docker ps -q --filter "name=ngrok-market" | grep -q .; then
        echo "停止現有 ngrok-market 容器..."
        docker stop $(docker ps -q --filter "name=ngrok-market") 2>/dev/null || true
        docker rm $(docker ps -aq --filter "name=ngrok-market") 2>/dev/null || true
    fi

    # 使用 docker-compose 清理
    if docker-compose ps -q 2>/dev/null | grep -q .; then
        echo "停止 docker-compose 服務..."
        docker-compose down 2>/dev/null || true
    fi

    # 移除舊的映像（可選）
    if docker images | grep -q "n8n_web_demo.*market-analysis"; then
        echo "移除舊的映像..."
        docker rmi $(docker images | grep "n8n_web_demo.*market-analysis" | awk '{print $3}') 2>/dev/null || true
    fi

    echo -e "${GREEN}✅ 清理完成${NC}"
}

# 建構和啟動服務
build_and_start() {
    echo -e "${BLUE}🔨 建構 Docker 映像...${NC}"
    docker-compose build --no-cache

    echo -e "${BLUE}🚀 啟動服務...${NC}"
    docker-compose up -d

    echo -e "${BLUE}⏳ 等待服務啟動...${NC}"
    sleep 20
}

# 檢查服務狀態
check_services() {
    echo -e "${BLUE}🔍 檢查服務狀態...${NC}"

    # 檢查市場分析服務
    local max_attempts=30
    local attempt=1

    while [ $attempt -le $max_attempts ]; do
        if curl -sf http://localhost:8089/health > /dev/null 2>&1; then
            echo -e "${GREEN}✅ 市場分析服務運行正常${NC}"
            echo -e "${GREEN}   網址: http://localhost:8089${NC}"
            break
        else
            if [ $attempt -eq $max_attempts ]; then
                echo -e "${RED}❌ 市場分析服務啟動失敗${NC}"
                echo "檢查日誌："
                docker-compose logs market-analysis
                return 1
            fi
            echo -e "${YELLOW}⏳ 等待服務啟動... ($attempt/$max_attempts)${NC}"
            sleep 2
            ((attempt++))
        fi
    done

    # 等待 ngrok 啟動
    echo -e "${BLUE}⏳ 等待 ngrok 隧道建立...${NC}"
    sleep 10

    # 檢查 ngrok 服務
    attempt=1
    max_attempts=20

    while [ $attempt -le $max_attempts ]; do
        if curl -sf http://localhost:${NGROK_PORT}/api/tunnels > /dev/null 2>&1; then
            echo -e "${GREEN}✅ ngrok 隧道服務運行正常${NC}"
            echo -e "${GREEN}   管理介面: http://localhost:${NGROK_PORT}${NC}"

            # 獲取公開 URL
            sleep 3
            NGROK_URL=$(curl -s http://localhost:${NGROK_PORT}/api/tunnels 2>/dev/null | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    for tunnel in data.get('tunnels', []):
        if tunnel.get('proto') == 'https':
            print(tunnel.get('public_url', ''))
            break
except Exception as e:
    pass
" 2>/dev/null)

            if [ -n "$NGROK_URL" ]; then
                echo -e "${GREEN}🌐 公開網址: ${NGROK_URL}${NC}"
                echo -e "${YELLOW}📌 N8N API 端點: ${NGROK_URL}/api/n8n-data${NC}"

                # 將 URL 寫入檔案供後續使用
                echo "$NGROK_URL" > .ngrok_url
            else
                echo -e "${YELLOW}⚠️ 無法獲取 ngrok 公開網址，請稍後訪問 http://localhost:${NGROK_PORT} 查看${NC}"
            fi
            break
        else
            if [ $attempt -eq $max_attempts ]; then
                echo -e "${YELLOW}⚠️ ngrok 服務啟動較慢，請稍後檢查 http://localhost:${NGROK_PORT}${NC}"
                echo "ngrok 日誌："
                docker-compose logs ngrok-market | tail -10
            else
                echo -e "${YELLOW}⏳ 等待 ngrok 啟動... ($attempt/$max_attempts)${NC}"
                sleep 3
                ((attempt++))
            fi
        fi
    done
}

# 測試 API 連接
test_api() {
    if [ -f ".ngrok_url" ]; then
        NGROK_URL=$(cat .ngrok_url)
        echo -e "${BLUE}🧪 測試 API 連接...${NC}"

        # 測試健康檢查
        if curl -sf "${NGROK_URL}/health" > /dev/null 2>&1; then
            echo -e "${GREEN}✅ 外部 API 訪問正常${NC}"
        else
            echo -e "${YELLOW}⚠️ 外部 API 可能需要更多時間初始化${NC}"
        fi
    fi
}

# 顯示使用說明
show_usage() {
    echo -e "${BLUE}================================================${NC}"
    echo -e "${GREEN}🎉 部署完成！${NC}"
    echo
    echo -e "${YELLOW}📋 服務資訊：${NC}"
    echo "  • 市場分析系統: http://localhost:8089"
    echo "  • ngrok 管理介面: http://localhost:${NGROK_PORT}"
    echo
    if [ -f ".ngrok_url" ]; then
        NGROK_URL=$(cat .ngrok_url)
        echo -e "${YELLOW}🌐 公開網址：${NC}"
        echo "  • 網站: ${NGROK_URL}"
        echo -e "${GREEN}  • N8N API: ${NGROK_URL}/api/n8n-data${NC}"
        echo
    fi
    echo -e "${YELLOW}🔧 常用指令：${NC}"
    echo "  • 查看日誌: docker-compose logs -f"
    echo "  • 停止服務: docker-compose down"
    echo "  • 重啟服務: docker-compose restart"
    echo "  • 查看狀態: docker-compose ps"
    echo "  • 獲取 ngrok URL: curl -s http://localhost:${NGROK_PORT}/api/tunnels"
    echo
    echo -e "${YELLOW}🌐 N8N 連接設定：${NC}"
    echo "  1. 訪問 http://localhost:${NGROK_PORT} 獲取最新的 ngrok 公開網址"
    echo "  2. 在 N8N HTTP Request 節點中使用："
    echo "     Method: POST"
    echo "     Content-Type: application/json"
    if [ -f ".ngrok_url" ]; then
        NGROK_URL=$(cat .ngrok_url)
        echo -e "     ${GREEN}URL: ${NGROK_URL}/api/n8n-data${NC}"
    else
        echo "     URL: [從 ngrok 管理介面獲取]/api/n8n-data"
    fi
    echo
    echo -e "${YELLOW}⚠️  注意事項：${NC}"
    echo "  • 如果您有其他 ngrok 服務，它們會使用不同的端口"
    echo "  • 當前 ngrok 管理端口: ${NGROK_PORT}"
    echo "  • 各服務間不會互相影響"
    echo
    echo -e "${GREEN}✨ 系統已準備就緒！${NC}"
}

# 主執行流程
main() {
    echo -e "${BLUE}檢查系統環境...${NC}"
    check_docker
    check_docker_compose
    check_ports
    check_files
    check_frontend
    check_gmail_config

    echo
    echo -e "${BLUE}部署應用程式...${NC}"
    cleanup_containers
    build_and_start
    check_services
    test_api

    echo
    show_usage
}

# 錯誤處理
trap 'echo -e "${RED}❌ 部署過程中發生錯誤${NC}"; exit 1' ERR

# 執行主函數
main "$@"
    echo -e "${YELLOW}🌐 N8N 連接設定：${NC}"
    echo "  1. 訪問 http://localhost:4040 獲取最新的 ngrok 公開網址"
    echo "  2. 在 N8N HTTP Request 節點中使用："
    echo "     Method: POST"
    echo "     Content-Type: application/json"
    if [ -f ".ngrok_url" ]; then
        NGROK_URL=$(cat .ngrok_url)
        echo -e "     ${GREEN}URL: ${NGROK_URL}/api/n8n-data${NC}"
    else
        echo "     URL: [從 ngrok 管理介面獲取]/api/n8n-data"
    fi
    echo
    echo -e "${GREEN}✨ 系統已準備就緒！${NC}"
}

# 主執行流程
main() {
    echo -e "${BLUE}檢查系統環境...${NC}"
    check_docker
    check_docker_compose
    check_files
    check_frontend
    check_gmail_config

    echo
    echo -e "${BLUE}部署應用程式...${NC}"
    cleanup_containers
    build_and_start
    check_services
    test_api

    echo
    show_usage
}

# 錯誤處理
trap 'echo -e "${RED}❌ 部署過程中發生錯誤${NC}"; exit 1' ERR

# 執行主函數
main "$@"