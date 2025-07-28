# 市場分析報告系統 v2.1.4

> 智能市場分析 • 即時黃金價格 • N8N 整合 • 自動化郵件發送 • 情感分析

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com)
[![Docker](https://img.shields.io/badge/Docker-Ready-blue.svg)](https://docker.com)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## 🚀 系統特色

- **📊 即時黃金價格監控** - 使用 yfinance 獲取即時黃金期貨價格 (GC=F)
- **📈 互動式價格圖表** - Chart.js 驅動的專業級價格圖表，支援多種時間週期
- **🧠 智能情感分析** - N8N 工作流程整合的市場情感分析系統
- **📧 獨立郵件發送頁面** - 分離式郵件配置和發送界面
- **🔗 N8N Webhook 整合** - 完整的自動化工作流程支援
- **🌐 現代化 Web 界面** - 響應式設計，支援多設備訪問
- **🐳 Docker 容器化** - 一鍵部署，環境隔離
- **📊 技術指標分析** - RSI、移動平均線、黃金交叉/死亡交叉檢測
- **🔄 生命週期管理** - 應用啟動/關閉事件處理
- **📝 增強日誌系統** - 詳細的錯誤追蹤和系統監控
- **🔍 健康檢查** - 完整的系統健康監控
- **📱 響應式設計** - 支援桌面和移動設備

## 📁 系統架構

```
n8n_web_demo/
├── 🖥️  API 服務 (Port 8089)
│   ├── FastAPI 後端 (main.py)
│   ├── 市場數據處理
│   ├── 黃金價格 API (yfinance)
│   ├── N8N Webhook 整合
│   └── 郵件發送系統
├── 🌐 前端界面
│   ├── index.html (主頁面)
│   ├── mail.html (郵件頁面)
│   └── static/ (靜態資源)
│       ├── style.css
│       ├── mail-style.css
│       ├── script.js
│       └── mail-script.js
├── 📊 數據處理
│   ├── 黃金價格統計
│   ├── 技術指標計算
│   ├── 移動平均線 (MA5, MA20, MA50, MA125)
│   ├── 轉折點
│   └── 情感分析處理
├── 📋 配置與部署
│   ├── requirements.txt
│   ├── Dockerfile
│   ├── docker-compose.yml
│   └── 環境配置
└── 📁 系統目錄
    ├── logs/ (日誌檔案)
    ├── data/ (數據檔案)
    ├── cache/ (快取檔案)
    └── backups/ (備份檔案)
```

## 🛠️ 快速開始

### 方法一：本地開發模式（推薦）

```bash
# 1. 克隆或下載項目檔案
git clone <repository-url>
cd n8n_web_demo

# 2. 建立虛擬環境
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# 或
.venv\Scripts\activate     # Windows

# 3. 安裝依賴
pip install -r requirements.txt

# 4. 啟動服務
python main.py
```

### 方法二：Docker 部署

```bash
# 1. 建立環境變數檔案
cp .env.example .env

# 2. 編輯 .env 檔案設定您的配置
# 設定 N8N Webhook URL 和其他必要參數

# 3. 啟動服務
docker-compose up --build -d

# 4. 查看服務狀態
docker-compose ps
```

### 方法三：直接執行

```bash
# 1. 確保已安裝 Python 3.8+
python --version

# 2. 安裝依賴
pip install fastapi uvicorn yfinance pandas numpy requests pydantic[email]

# 3. 啟動服務
python main.py
```

## 🌐 服務訪問

| 服務 | 本地訪問 | 說明 |
|------|----------|------|
| **主網站** | http://localhost:8089 | 市場數據 + 黃金價格顯示 |
| **郵件頁面** | http://localhost:8089/mail | 獨立的郵件發送頁面 |
| **API 服務** | http://localhost:8089 | RESTful API 接口 |
| **API 文檔** | http://localhost:8089/api/docs | Swagger API 文檔 |
| **健康檢查** | http://localhost:8089/health | 服務健康狀態 |

## 📊 主要功能

### 1. 即時黃金價格監控

- **數據來源**: Yahoo Finance (GC=F 黃金期貨)
- **更新頻率**: 每分鐘自動刷新
- **顯示內容**:
  - 當前價格 (USD/oz)
  - 價格變化和變化百分比
  - 24小時高低點
  - 平均價格和波動率
  - 市場狀態（開市/休市）
  - 最後更新時間
  - 互動式價格圖表
  - 技術指標 (RSI, MA線)
  - 黃金交叉/死亡交叉檢測

### 2. 智能市場情感分析

- **數據來源**: N8N 工作流程
- **分析內容**:
  - 情感分析分數 (0 到 100)
  - 市場情感文字描述
  - 市場日期
  - 情感表情符號

### 3. 技術指標分析

- **移動平均線**: MA5, MA20, MA50, MA125
- **RSI 指標**: 相對強弱指數
- **波動率分析**: 5日波動率
- **價格趨勢**: 價格與移動平均線的關係
- **交叉信號**: 黃金交叉和死亡交叉檢測
- **轉折點**: MA90 概念
- **市場狀態判斷**: 基於時間的市場開放狀態

### 4. 郵件發送系統

- **獨立頁面**: `/mail` 路由
- **功能特色**:
  - 收件人設定
  - 自訂郵件主旨
  - 個人化訊息
  - 多種郵件選項
  - 即時預覽功能
  - N8N webhook 整合
  - 情感分析表情符號
  - 郵件優先級設定

## 🔧 API 接口

### 核心 API

```bash
# 獲取當前市場數據
GET /api/current-data

# 獲取黃金價格
GET /api/gold-price?period=1y&interval=1d

# 接收 N8N 數據
POST /api/n8n-data

# 發送郵件到 N8N
POST /api/send-mail-to-n8n

# 測試 N8N 連接
GET /api/test-n8n-connection

# 調試存儲數據
GET /api/debug-stored-data

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
    "high_24h": 2030.20,
    "low_24h": 2015.80,
    "avg_price": 2025.30,
    "volatility": 15.45,
    "currency": "USD",
    "unit": "per ounce",
    "last_updated": "2025-01-22T08:30:00Z",
    "market_status": "open",
    "chart_data": [...],
    "ma_lines": {
      "ma_5": [...],
      "ma_20": [...]
    },
    "ma_125_line": [...],
    "quarterly_average_line": [...],
    "cross_signal": {
      "golden_cross": false,
      "death_cross": false,
      "status": "normal",
      "message": "⚪ 正常：MA20與MA5無交叉信號"
    },
    "technical_indicators": {
      "ma_20": 2020.50,
      "ma_50": 2015.30,
      "rsi": 65.2,
      "volatility_5d": 12.3,
      "price_vs_ma20": 0.15
    }
  }
}
```

#### N8N 數據格式
```json
{
  "average_sentiment_score": -0.17,
  "message_content": "今日市場概述...",
  "market_date": "2025年01月22日",
  "confidence_level": "較低",
  "trend_direction": "溫和看跌",
  "risk_assessment": "低風險",
  "email_report": "詳細的郵件報告內容..."
}
```

#### 郵件發送請求
```json
{
  "recipient_email": "user@example.com",
  "sender_name": "市場分析系統",
  "subject": "市場分析報告",
  "priority": "normal",
  "mail_type": "daily",
  "custom_message": "請查看附件",
  "include_charts": true,
  "include_recommendations": true,
  "include_risk_warning": false
}
```

## 📋 環境配置

### 必需環境變數

```bash
# 基本配置
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO

# 服務端口
SERVER_HOST=0.0.0.0
SERVER_PORT=8089

# Webhook 配置
WEBHOOK_URL=https://your-n8n-instance.com/webhook/your-webhook-id
WEBHOOK_TIMEOUT=30

# N8N Webhook URL
N8N_WEBHOOK_URL=https://your-n8n-instance.com/webhook/Webhook - Preview
```

### 可選環境變數

```bash
# 日誌配置
LOG_LEVEL=INFO
LOG_FILE=logs/market_analysis.log

# 數據配置
DATA_DIR=data
CACHE_DIR=cache
```

## 🐳 Docker 部署

### 使用 Docker Compose

```bash
# 1. 建立環境變數檔案
cp .env.example .env

# 2. 編輯 .env 檔案
# 設定 N8N Webhook URL 和其他必要參數

# 3. 啟動服務
docker-compose up --build -d

# 4. 查看服務狀態
docker-compose ps

# 5. 查看日誌
docker-compose logs -f
```

### 使用 Dockerfile

```bash
# 1. 建立映像
docker build -t market-analysis-system .

# 2. 執行容器
docker run -d \
  --name market-analysis \
  -p 8089:8089 \
  -e WEBHOOK_URL=your_webhook_url \
  market-analysis-system
```

### Docker Compose 服務

系統包含以下 Docker 服務：

- **market-analysis**: 主要應用服務
- **ngrok**: 隧道服務 (端口 4041)
- **redis**: 快取服務 (可選)
- **prometheus**: 監控服務 (可選)
- **grafana**: 儀表板服務 (可選)

## 📊 監控與日誌

### 查看服務狀態
```bash
# 健康檢查
curl http://localhost:8089/health

# 查看日誌
tail -f logs/market_analysis.log

# Docker 日誌
docker-compose logs -f
```

### 系統統計

系統提供詳細的統計信息：
- 總報告數量
- 今日報告數量
- API 調用次數
- 黃金價格調用次數
- 錯誤計數
- 系統運行時間
- 最後數據接收時間

## 🔧 開發指南

### 本地開發環境

```bash
# 1. 建立虛擬環境
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# 或
.venv\Scripts\activate     # Windows

# 2. 安裝依賴
pip install -r requirements.txt

# 3. 設定環境變數
export DEBUG=true
export LOG_LEVEL=DEBUG

# 4. 啟動開發服務器
python main.py
```

### 檔案結構

```
n8n_web_demo/
├── main.py              # API 服務主程式
├── requirements.txt     # Python 依賴
├── Dockerfile           # Docker 配置
├── docker-compose.yml   # Compose 配置
├── docker-entrypoint.sh # Docker 入口腳本
├── setup-docker.sh      # Docker 設置腳本
├── frontend/           # 前端檔案
│   ├── index.html      # 主頁面
│   ├── mail.html       # 郵件頁面
│   └── static/         # 靜態資源
│       ├── style.css   # 樣式檔案
│       ├── mail-style.css
│       ├── script.js   # 腳本檔案
│       └── mail-script.js
├── data/               # 數據檔案
├── logs/               # 日誌檔案
├── backups/            # 備份檔案
├── cache/              # 快取檔案
└── test/               # 測試檔案
```

### 依賴套件

```txt
# 核心 Web 框架
fastapi>=0.104.0
uvicorn[standard]>=0.24.0

# 資料驗證和序列化
pydantic[email]>=2.5.0
email-validator>=2.0.0

# HTTP 客戶端
requests>=2.31.0
httpx>=0.24.0

# 金融數據
yfinance>=0.2.20

# 資料處理
pandas>=2.0.0
numpy>=1.24.0

# 相容性修正
typing-extensions>=4.5.0
```

## 🛠️ 故障排除

### 常見問題

#### 1. 服務無法啟動
```bash
# 檢查端口是否被占用
netstat -tlnp | grep :8089

# 檢查 Python 版本
python --version

# 檢查依賴安裝
pip list | grep fastapi
```

#### 2. 黃金價格無法獲取
```bash
# 檢查網路連接
curl -s "https://finance.yahoo.com" > /dev/null && echo "網路正常"

# 測試 yfinance
python -c "import yfinance as yf; print(yf.Ticker('GC=F').info['regularMarketPrice'])"
```

#### 3. N8N 連接失敗
```bash
# 測試 webhook 連接
curl -X GET http://localhost:8089/api/test-n8n-connection

# 檢查 webhook URL 設定
echo $WEBHOOK_URL
```

#### 4. 郵件發送失敗
```bash
# 檢查 N8N webhook URL
curl -X POST $N8N_WEBHOOK_URL -H "Content-Type: application/json" -d '{"test": "data"}'

# 查看郵件發送日誌
grep "send-mail" logs/market_analysis.log
```

### 效能優化

#### 1. 記憶體使用優化
```bash
# 限制容器記憶體使用
docker run --memory="512m" market-analysis-system
```

#### 2. 快取配置
```bash
# 啟用數據快取
mkdir -p cache
```

#### 3. 日誌輪轉
```bash
# 設定日誌輪轉
logrotate /etc/logrotate.d/market-analysis
```

## 📞 技術支援

### 日誌位置
- **應用日誌**: `./logs/market_analysis.log`
- **Docker 日誌**: `docker-compose logs`
- **系統日誌**: `/var/log/syslog`

### 健康檢查
```bash
# API 健康檢查
curl http://localhost:8089/health

# 完整服務檢查
curl http://localhost:8089/api/current-data
```

### 備份與恢復
```bash
# 建立備份
tar -czf backup-$(date +%Y%m%d).tar.gz data/ logs/

# 恢復備份
tar -xzf backup-YYYYMMDD.tar.gz
```

## 🔄 版本更新

### 更新到最新版本
```bash
# 1. 停止服務
docker-compose down

# 2. 拉取最新代碼
git pull origin main

# 3. 重建並啟動
docker-compose up --build -d
```

### 版本歷史
- **v2.1.4**: 修正市場數據顯示問題，增強錯誤處理和日誌
- **v2.1.2**: 增強錯誤處理和日誌，修正市場數據顯示問題
- **v2.1.0**: 增強黃金價格 API，新增技術指標
- **v2.0.0**: 分離式架構 + 黃金價格 + N8N 整合
- **v1.3.0**: 郵件發送頁面 + N8N 整合增強
- **v1.2.0**: 基本市場分析功能
- **v1.0.0**: 初始版本

## 🤝 貢獻指南

歡迎提交 Issue 和 Pull Request 來改善本項目。

### 開發流程
1. Fork 本項目
2. 建立功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交變更 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 開啟 Pull Request

### 代碼規範
- 使用 Python 3.8+ 語法
- 遵循 PEP 8 代碼風格
- 添加適當的註釋和文檔
- 確保所有測試通過

## 📄 授權條款

本項目採用 MIT 授權條款。詳見 [LICENSE](LICENSE) 檔案。

## 🙏 致謝

- [FastAPI](https://fastapi.tiangolo.com/) - 現代化的 Python Web 框架
- [yfinance](https://github.com/ranaroussi/yfinance) - Yahoo Finance 數據庫
- [Chart.js](https://www.chartjs.org/) - 互動式圖表庫
- [N8N](https://n8n.io/) - 工作流程自動化平台

---

**市場分析報告系統 v2.1.4** - 智能分析 • 精準決策 🚀

> 讓數據驅動決策，讓智能引領未來