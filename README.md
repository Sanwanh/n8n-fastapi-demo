# 市場分析郵件系統 - 完整檔案結構

## 📁 專案目錄結構

```
market_analysis_system/
├── 📄 main.py                          # 主程式 (更新版本)
├── 📄 config.py                        # 系統配置檔案
├── 📄 models.py                        # 資料模型定義
├── 📄 requirements.txt                 # Python 依賴套件
├── 📄 Dockerfile                       # Docker 容器配置
├── 📄 docker-compose.yml               # Docker Compose 配置
├── 📄 docker-entrypoint.sh             # Docker 啟動腳本
├── 📄 setup-docker.sh                  # Docker 配置建立腳本
├── 📄 README.md                        # 專案說明文件
├── 📁 frontend/                        # 前端檔案目錄
│   ├── 📄 index.html                   # 主頁面 (更新版本)
│   ├── 📄 mail.html                    # 郵件發送頁面 (新增)
│   └── 📁 static/                      # 靜態資源目錄
│       ├── 📄 style.css                # 主頁面樣式
│       ├── 📄 script.js                # 主頁面腳本
│       ├── 📄 mail-style.css           # 郵件頁面樣式 (新增)
│       └── 📄 mail-script.js           # 郵件頁面腳本 (新增)
├── 📁 docker/                          # Docker 相關配置
│   ├── 📄 prometheus.yml               # Prometheus 監控配置
│   └── 📄 healthcheck.sh               # 健康檢查腳本
├── 📁 logs/                            # 日誌檔案目錄
│   └── 📄 market_analysis.log          # 系統日誌檔案
├── 📁 data/                            # 資料儲存目錄
├── 📁 backups/                         # 備份檔案目錄
└── 📁 cache/                           # 快取檔案目錄
```

## 🔄 主要更新內容

### 1. 新增郵件發送頁面
- **檔案**: `frontend/mail.html`
- **功能**: 獨立的郵件發送介面
- **特色**: 
  - 完整的表單驗證
  - 即時市場數據顯示
  - 郵件預覽功能
  - 多種配置選項

### 2. 郵件頁面樣式
- **檔案**: `frontend/static/mail-style.css`
- **特色**:
  - 現代化設計風格
  - 響應式佈局
  - 豐富的動畫效果
  - 深色主題

### 3. 郵件頁面腳本
- **檔案**: `frontend/static/mail-script.js`
- **功能**:
  - 表單處理與驗證
  - 市場數據載入
  - 郵件內容生成
  - N8N webhook 整合

### 4. 更新主程式
- **檔案**: `main.py`
- **新增功能**:
  - `/mail` 路由 - 郵件發送頁面
  - `/api/send-mail-to-n8n` API - 新的郵件發送接口
  - `/api/test-n8n-connection` API - N8N 連接測試
  - 支援擴展的 N8N 資料格式

### 5. 更新首頁
- **檔案**: `frontend/index.html`
- **改進**:
  - 新增導航列
  - 郵件發送頁面連結
  - 更好的狀態顯示
  - 快速操作區域

## 🔌 API 端點說明

### 現有 API (保持向後相容)
```
POST /api/n8n-data           # 接收 N8N 市場數據
GET  /api/current-data       # 獲取當前市場數據
POST /api/send-email         # 舊版郵件發送 API
GET  /health                 # 系統健康檢查
GET  /api/stats              # 系統統計資料
GET  /api/test-connection    # 測試 webhook 連接
GET  /api/config             # 前端配置資料
```

### 新增 API
```
GET  /mail                   # 郵件發送頁面
POST /api/send-mail-to-n8n   # 新版郵件發送 API
GET  /api/test-n8n-connection # 測試 N8N 連接
```

## 📊 N8N 資料格式

### 輸入資料格式 (從 N8N 接收)
```json
{
  "average_sentiment_score": -0.17,
  "message_content": "今日市場概述：黃金期貨維持在窄幅震盪區間...",
  "market_date": "2025年07月22日",
  "confidence_level": "較低",
  "trend_direction": "溫和看跌",
  "risk_assessment": "低風險"
}
```

### 輸出資料格式 (發送到 N8N)
```json
{
  "average_sentiment_score": -0.17,
  "message_content": "今日市場概述：黃金期貨維持在窄幅震盪區間...",
  "market_date": "2025年07月22日",
  "confidence_level": "較低",
  "trend_direction": "溫和看跌", 
  "risk_assessment": "低風險",
  "received_time": "2025-07-22 00:25:17",
  "mail_config": {
    "recipient_email": "user@example.com",
    "sender_name": "市場分析系統",
    "subject": "市場分析報告 - 2025年07月22日",
    "priority": "normal",
    "mail_type": "daily",
    "custom_message": "自訂內容...",
    "include_charts": true,
    "include_recommendations": true,
    "include_risk_warning": true
  },
  "system_info": {
    "send_timestamp": "2025-07-22T00:30:00.000Z",
    "system_version": "1.3.0",
    "source": "mail-sender-page"
  },
  "sentiment_analysis": {
    "score": -0.17,
    "text": "略為悲觀",
    "emoji": "📉🟡😐"
  }
}
```

## 🚀 部署指南

### 方法一：Docker 部署 (推薦)
```bash
# 1. 使用提供的 Docker 配置腳本
./setup-docker.sh

# 2. 啟動系統
./deploy.sh

# 或使用 docker-compose
docker-compose up -d
```

### 方法二：直接運行
```bash
# 1. 安裝依賴
pip install -r requirements.txt

# 2. 啟動系統
python main.py

# 或使用 uvicorn
uvicorn main:app --host 0.0.0.0 --port 8089
```

## 🔧 配置說明

### 環境變數設定
```bash
# 基本配置
SERVER_HOST=0.0.0.0
SERVER_PORT=8089
DEBUG=false
LOG_LEVEL=INFO

# Webhook 配置
WEBHOOK_URL=https://beloved-swine-sensibly.ngrok-free.app/webhook-test/ef5ac185-f41a-4a2d-9a78-33d329184c2
WEBHOOK_TIMEOUT=30

# N8N Webhook (新增)
N8N_WEBHOOK_URL=https://beloved-swine-sensibly.ngrok-free.app/webhook/Webhook%20-%20Preview

# 安全配置
API_KEY=your_api_key_here
CORS_ORIGINS=*
```

### 重要配置項目
- **WEBHOOK_URL**: 舊版 webhook 端點 (保持向後相容)
- **N8N_WEBHOOK_URL**: 新版 N8N webhook 端點 (郵件發送頁面使用)
- **SERVER_PORT**: 系統運行端口 (預設: 8089)
- **DEBUG**: 除錯模式開關

## 📱 使用說明

### 1. 首頁功能
- 訪問 `http://localhost:8089/`
- 查看系統狀態和當前市場數據
- 快速導航到各功能頁面

### 2. 郵件發送頁面
- 訪問 `http://localhost:8089/mail`
- 配置郵件相關設定
- 預覽郵件內容
- 發送到 N8N webhook

### 3. API 使用
```bash
# 查看 API 文檔
curl http://localhost:8089/docs

# 獲取當前數據
curl http://localhost:8089/api/current-data

# 測試 N8N 連接
curl http://localhost:8089/api/test-n8n-connection

# 健康檢查
curl http://localhost:8089/health
```

## 🔄 資料流程

```
N8N 工作流程 
    ↓ (POST /api/n8n-data)
系統接收並儲存市場數據
    ↓
使用者在郵件頁面配置郵件
    ↓ (POST /api/send-mail-to-n8n)
系統整合數據並發送到 N8N
    ↓ (POST webhook/Webhook - Preview)
N8N 處理郵件發送
    ↓
郵件發送到收件人
```

## 🛠️ 開發指南

### 新增功能步驟
1. **後端 API**: 在 `main.py` 中新增路由
2. **前端頁面**: 在 `frontend/` 目錄建立 HTML
3. **樣式設計**: 在 `frontend/static/` 建立 CSS
4. **互動功能**: 在 `frontend/static/` 建立 JS
5. **配置更新**: 更新 `config.py` 相關設定

### 程式碼結構
- **main.py**: FastAPI 應用主體
- **config.py**: 系統配置管理
- **models.py**: 資料模型定義
- **frontend/**: 前端檔案
- **static/**: 靜態資源

## 🐛 故障排除

### 常見問題
1. **郵件發送失敗**
   - 檢查 N8N webhook URL 是否正確
   - 確認網路連接正常
   - 查看系統日誌 `logs/market_analysis.log`

2. **市場數據未顯示**
   - 確認 N8N 工作流程正常運行
   - 檢查資料格式是否符合預期
   - 使用 `/api/current-data` 檢查原始數據

3. **系統無法啟動**
   - 檢查端口 8089 是否被佔用
   - 確認 Python 依賴已正確安裝
   - 查看啟動日誌

### 日誌檢查
```bash
# 查看系統日誌
tail -f logs/market_analysis.log

# 查看 Docker 日誌
docker-compose logs -f market-analysis
```

## 📋 檢查清單

### 部署前檢查
- [ ] 已安裝所有依賴套件
- [ ] 配置檔案設定正確
- [ ] N8N webhook URL 可訪問
- [ ] 端口 8089 未被佔用
- [ ] 日誌目錄有寫入權限

### 功能測試檢查
- [ ] 首頁正常載入並顯示狀態
- [ ] 郵件頁面可正常訪問
- [ ] 可以接收 N8N 市場數據
- [ ] 郵件發送功能正常
- [ ] API 文檔可正常訪問
- [ ] 健康檢查回應正常

## 🔮 未來擴展

### 計畫功能
- [ ] 使用者帳戶管理
- [ ] 郵件範本自定義
- [ ] 歷史數據查詢
- [ ] 進階分析圖表
- [ ] 排程郵件發送
- [ ] 多語言支援

### 技術改進
- [ ] 資料庫整合 (PostgreSQL/MongoDB)
- [ ] Redis 快取層
- [ ] 訊息佇列 (Celery)
- [ ] 監控儀表板 (Grafana)
- [ ] 單元測試覆蓋
- [ ] CI/CD 流程

## 📞 聯絡資訊

如有任何問題或建議，請：
1. 查看系統日誌檔案
2. 檢查 GitHub Issues (如果有的話)
3. 聯繫系統管理員

---

**版本**: 1.3.0  
**最後更新**: 2025-07-22