# 市場分析報告系統 v2.0.0

> 智能市場分析 • 即時黃金價格 • N8N 整合 • 自動化郵件發送

## 🚀 系統特色

- **📊 即時黃金價格顯示** - 使用 yfinance 獲取即時黃金期貨價格
- **📈 互動式價格圖表** - Chart.js 驅動的專業級價格圖表
- **🧠 智能情感分析** - N8N 工作流程整合的市場情感分析
- **📧 獨立郵件發送頁面** - 分離式郵件配置和發送界面
- **🌐 雙服務架構** - API 服務與 Web 服務分離
- **🔗 ngrok 隧道支援** - 輕鬆分享給外部用戶訪問
- **🐳 Docker 容器化** - 一鍵部署，環境隔離

## 📁 系統架構

```
market_analysis_system_v2/
├── 🖥️  API 服務 (Port 8089)
│   ├── FastAPI 後端
│   ├── 市場數據處理
│   ├── 黃金價格 API
│   └── N8N 整合
├── 🌐 Web 服務 (Port 8080)
│   ├── 靜態檔案服務
│   ├── 主頁面 (市場數據 + 黃金價格)
│   └── 郵件發送頁面
├── 🔗 ngrok 隧道 (Port 4040)
│   ├── Web 外部訪問
│   └── API 外部訪問
└── 📊 監控服務 (可選)
    ├── Prometheus (Port 9090)
    └── Grafana (Port 3000)
```

## 🛠️ 快速開始

### 方法一：使用快速啟動腳本（推薦）

```bash
# 1. 克隆或下載項目檔案
git clone <repository-url>
cd market_analysis_system_v2

# 2. 設定 ngrok authtoken（可選）
# 編輯 .env 檔案，設定您的 NGROK_AUTHTOKEN

# 3. 執行快速啟動腳本
chmod +x start.sh
./start.sh

# 或直接啟動
./start.sh start
```

### 方法二：手動 Docker Compose

```bash
# 1. 建立環境變數檔案
cp .env.example .env

# 2. 編輯 .env 檔案設定您的配置

# 3. 啟動服務
docker-compose up --build -d

# 4. 查看服務狀態
docker-compose ps
```

### 方法三：本地開發模式

```bash
# 1. 安裝 Python 依賴
pip install -r requirements.txt

# 2. 啟動 API 服務
python main.py

# 3. 另開終端啟動 Web 服務
python web_server.py
```

## 🌐 服務訪問

| 服務 | 本地訪問 | 說明 |
|------|----------|------|
| **主網站** | http://localhost:8080 | 市場數據 + 黃金價格顯示 |
| **郵件頁面** | http://localhost:8080/mail | 獨立的郵件發送頁面 |
| **API 服務** | http://localhost:8089 | RESTful API 接口 |
| **API 文檔** | http://localhost:8089/api/docs | Swagger API 文檔 |
| **健康檢查** | http://localhost:8089/health | 服務健康狀態 |
| **ngrok 管理** | http://localhost:4040 | ngrok 隧道管理界面 |

## 📊 主要功能

### 1. 即時黃金價格監控

- **數據來源**: Yahoo Finance (GC=F 黃金期貨)
- **更新頻率**: 每分鐘自動刷新
- **顯示內容**:
  - 當前價格 (USD/oz)
  - 價格變化和變化百分比
  - 市場狀態（開市/休市）
  - 最後更新時間
  - 48小時價格走勢圖表

### 2. 智能市場情感分析

- **數據來源**: N8N 工作流程
- **分析內容**:
  - 情感分析分數 (-1.0 到 1.0)
  - 市場情感文字描述
  - 風險評估
  - 趨勢方向
  - 信心水平

### 3. 郵件發送系統

- **獨立頁面**: `/mail` 路由
- **功能特色**:
  - 收件人設定
  - 自訂郵件主旨
  - 個人化訊息
  - 多種郵件選項
  - 即時預覽功能
  - N8N webhook 整合

## 🔧 API 接口

### 核心 API

```bash
# 獲取當前市場數據
GET /api/current-data

# 獲取黃金價格
GET /api/gold-price

# 接收 N8N 數據
POST /api/n8n-data

# 發送郵件到 N8N
POST /api/send-mail-to-n8n

# 測試 N8N 連接
GET /api/test-n8n-connection

# 系統健康檢查
GET /health
```

### 數據格式範例

#### 黃金價格 API 回應
```json
{
  "status": "success",
  "data": {
    "symbol": "GC=F",
    "name": "Gold Futures",
    "current_price": 2023.45,
    "change": 12.30,
    "change_percent": 0.61,
    "currency": "USD",
    "unit": "per ounce",
    "last_updated": "2025-07-22T08:30:00Z",
    "market_status": "open",
    "chart_data": [...]
  }
}
```

#### N8N 數據格式
```json
{
  "average_sentiment_score": -0.17,
  "message_content": "今日市場概述...",
  "market_date": "2025年07月22日",
  "confidence_level": "較低",
  "trend_direction": "溫和看跌",
  "risk_assessment": "低風險"
}
```

## 🔗 ngrok 隧道設定

### 1. 獲取 ngrok Authtoken

```bash
# 1. 註冊 ngrok 帳號
https://ngrok.com/signup

# 2. 獲取您的 authtoken
https://dashboard.ngrok.com/get-started/your-authtoken

# 3. 設定到 .env 檔案
NGROK_AUTHTOKEN=your_token_here
```

### 2. 隧道配置

系統會自動建立兩個隧道：
- **Web 隧道**: 供用戶訪問網站
- **API 隧道**: 供 N8N 回調使用

## 📋 環境配置

### 必需環境變數

```bash
# 基本配置
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO

# 服務端口
API_PORT=8089
WEB_PORT=8080

# Webhook 配置
WEBHOOK_URL=your_n8n_webhook_url

# ngrok 配置
NGROK_AUTHTOKEN=your_ngrok_token
```

### 可選環境變數

```bash
# Redis 配置
REDIS_PASSWORD=secure_password

# 監控配置
GRAFANA_PASSWORD=admin123

# 建置配置
BUILD_DATE=auto_generated
```

## 🐳 Docker 部署

### 單服務部署
```bash
# 僅啟動主要服務
docker-compose up -d market-analysis
```

### 完整部署
```bash
# 啟動所有服務包括 ngrok
docker-compose up -d
```

### 監控部署
```bash
# 啟動監控服務
docker-compose --profile monitoring up -d
```

### 快取部署
```bash
# 啟動 Redis 快取
docker-compose --profile redis up -d
```

## 📊 監控與日誌

### 查看服務狀態
```bash
# 使用腳本
./start.sh status

# 或直接使用 docker-compose
docker-compose ps
```

### 查看日誌
```bash
# 即時日誌
./start.sh logs

# 或指定服務
docker-compose logs -f market-analysis
```

### Prometheus 指標
```bash
# 訪問 Prometheus
http://localhost:9090

# 常用指標
- http_requests_total
- response_time_seconds
- system_cpu_usage
- memory_usage_bytes
```

## 🔧 開發指南

### 本地開發環境

```bash
# 1. 建立虛擬環境
python -m venv venv
source venv/bin/activate  # Linux/macOS
# 或
venv\Scripts\activate     # Windows

# 2. 安裝依賴
pip install -r requirements.txt

# 3. 設定環境變數
export DEBUG=true
export LOG_LEVEL=DEBUG

# 4. 啟動開發服務器
python main.py  # API 服務
python web_server.py  # Web 服務
```

### 檔案結構

```
├── main.py              # API 服務主程式
├── web_server.py        # Web 服務主程式
├── config.py            # 系統配置
├── models.py            # 資料模型
├── requirements.txt     # Python 依賴
├── Dockerfile           # Docker 配置
├── docker-compose.yml   # Compose 配置
├── ngrok.yml           # ngrok 配置
├── start.sh            # 快速啟動腳本
├── frontend/           # 前端檔案
│   ├── index.html      # 主頁面
│   ├── mail.html       # 郵件頁面
│   └── static/         # 靜態資源
│       ├── style.css   # 樣式檔案
│       ├── mail-style.css
│       ├── script.js   # 腳本檔案
│       └── mail-script.js
└── logs/               # 日誌檔案
```

## 🛠️ 故障排除

### 常見問題

#### 1. 服務無法啟動
```bash
# 檢查端口是否被占用
sudo netstat -tlnp | grep :8089
sudo netstat -tlnp | grep :8080

# 強制停止並重啟
./start.sh stop
./start.sh start
```

#### 2. 黃金價格無法獲取
```bash
# 檢查網路連接
curl -s "https://finance.yahoo.com" > /dev/null && echo "網路正常"

# 查看 API 日誌
docker-compose logs market-analysis | grep gold
```

#### 3. N8N 連接失敗
```bash
# 測試 webhook 連接
curl -X GET http://localhost:8089/api/test-n8n-connection

# 檢查 webhook URL 設定
grep WEBHOOK_URL .env
```

#### 4. ngrok 隧道無法建立
```bash
# 檢查 authtoken
grep NGROK_AUTHTOKEN .env

# 查看 ngrok 日誌
docker-compose logs ngrok
```

### 效能優化

#### 1. 記憶體使用優化
```bash
# 限制容器記憶體使用
docker-compose up -d --memory="512m"
```

#### 2. 快取配置
```bash
# 啟用 Redis 快取
./start.sh cache
```

#### 3. 監控設定
```bash
# 啟用完整監控
./start.sh monitoring
```

## 📞 技術支援

### 日誌位置
- **容器日誌**: `docker-compose logs`
- **應用日誌**: `./logs/market_analysis.log`
- **系統日誌**: `/var/log/syslog`

### 健康檢查
```bash
# API 健康檢查
curl http://localhost:8089/health

# Web 服務檢查
curl http://localhost:8080/

# 完整服務檢查
./start.sh status
```

### 備份與恢復
```bash
# 建立備份
docker-compose exec market-analysis tar -czf /app/backups/backup-$(date +%Y%m%d).tar.gz /app/data

# 恢復備份
docker-compose exec market-analysis tar -xzf /app/backups/backup-YYYYMMDD.tar.gz -C /
```

## 🔄 版本更新

### 更新到最新版本
```bash
# 1. 停止服務
./start.sh stop

# 2. 拉取最新代碼
git pull origin main

# 3. 重建並啟動
./start.sh start
```

### 版本歷史
- **v2.0.0**: 分離式架構 + 黃金價格 + ngrok 支援
- **v1.3.0**: 郵件發送頁面 + N8N 整合增強
- **v1.2.0**: 基本市場分析功能
- **v1.0.0**: 初始版本

---

## 📄 授權條款

本項目採用 MIT 授權條款。

## 🤝 貢獻指南

歡迎提交 Issue 和 Pull Request 來改善本項目。

---

**市場分析報告系統 v2.0.0** - 智能分析 • 精準決策 🚀