# 郵件發送系統

基於 FastAPI + n8n 的整合郵件發送系統，提供完整的郵件管理功能。

## 功能特色

- ✅ **直觀的網頁介面** - 簡潔易用的郵件撰寫介面
- ✅ **多種郵件範本** - 內建通知、提醒、會議、報告範本
- ✅ **即時發送狀態** - 顯示郵件發送進度和結果
- ✅ **完整的發送記錄** - 查看所有已發送郵件的詳細資訊
- ✅ **優先級管理** - 支援低、一般、高三種優先級
- ✅ **統計儀表板** - 顯示郵件發送統計資料
- ✅ **響應式設計** - 支援桌面和行動裝置
- ✅ **n8n 整合** - 透過 n8n 工作流程發送郵件
- ✅ **SQLite 資料庫** - 輕量級資料儲存解決方案

## 系統架構

```
Frontend (HTML/CSS/JS) → FastAPI Backend → n8n Webhook → Gmail API
                            ↓
                       SQLite Database
```

## 快速開始

### 1. 環境準備

**系統需求：**
- Python 3.8+
- n8n 實例
- Gmail 帳戶（用於發送郵件）

**安裝步驟：**

```bash
# 1. 克隆專案
git clone <repository-url>
cd mail_sender_project

# 2. 建立虛擬環境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. 安裝依賴
cd backend
pip install -r requirements.txt

# 4. 初始化資料庫
python database.py

# 5. 設定環境變數
cp .env.example .env
# 編輯 .env 檔案，設定您的 n8n webhook URL
```

### 2. n8n 設定

**重要：** 請先設定 n8n 工作流程，然後再啟動 FastAPI 服務。

1. **建立 n8n 工作流程**
   - 參考 [n8n 設定指南](n8n_setup_guide.md)
   - 使用提供的 webhook URL：`https://beloved-swine-sensibly.ngrok-free.app/webhook-test/ef5ac185-f41a-4a2d-9a78-33d329184c2`

2. **Gmail 節點設定**
   - 設定 Google OAuth2 認證
   - 配置郵件發送參數

3. **測試 webhook 連接**
   ```bash
   curl -X POST https://beloved-swine-sensibly.ngrok-free.app/webhook-test/ef5ac185-f41a-4a2d-9a78-33d329184c2 \
     -H "Content-Type: application/json" \
     -d '{"to":"test@example.com","subject":"測試","content":"測試內容"}'
   ```

### 3. 啟動系統

```bash
# 啟動 FastAPI 服務
cd backend
python main.py

# 或使用 uvicorn
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

**訪問系統：**
- 網頁介面：http://localhost:8000
- API 文檔：http://localhost:8000/docs
- 健康檢查：http://localhost:8000/health

## 使用教學

### 1. 發送郵件

1. 打開網頁介面
2. 選擇郵件範本（可選）
3. 填寫郵件資訊：
   - 收件者信箱
   - 寄件者名稱
   - 優先級
   - 主旨
   - 內容
4. 點擊「發送郵件」
5. 系統會顯示發送狀態

### 2. 查看發送記錄

- 右側面板顯示最近的郵件發送記錄
- 點擊「查看」按鈕查看完整郵件內容
- 點擊「展開」按鈕查看完整郵件文字
- 點擊「刪除」按鈕移除記錄

### 3. 統計資料

頂部統計卡片顯示：
- 總發送郵件數
- 今日發送數
- 成功發送數
- 待處理數

## API 文檔

### 發送郵件
```http
POST /api/send-email
Content-Type: application/json

{
  "to": "recipient@example.com",
  "subject": "郵件主旨",
  "content": "郵件內容",
  "sender_name": "寄件者名稱",
  "priority": "normal"
}
```

### 獲取郵件列表
```http
GET /api/emails?limit=20&offset=0
```

### 獲取特定郵件
```http
GET /api/email/{email_id}
```

### 刪除郵件
```http
DELETE /api/email/{email_id}
```

### 獲取統計資料
```http
GET /api/stats
```

## 設定檔案

### config.py 主要設定

```python
# n8n Webhook URL
N8N_WEBHOOK_URL = "https://beloved-swine-sensibly.ngrok-free.app/webhook-test/ef5ac185-f41a-4a2d-9a78-33d329184c2"

# 伺服器設定
HOST = "0.0.0.0"
PORT = 8000

# 預設寄件者名稱
DEFAULT_SENDER_NAME = "系統管理員"

# 郵件內容最大長度
MAX_EMAIL_LENGTH = 10000
```

### 環境變數設定 (.env)

```env
N8N_WEBHOOK_URL=https://your-n8n-instance.com/webhook-test/your-unique-id
DEBUG=true
HOST=0.0.0.0
PORT=8000
SECRET_KEY=your-secret-key-here
DEFAULT_SENDER_NAME=系統管理員
MAX_EMAIL_LENGTH=10000
LOG_LEVEL=INFO
```

## 故障排除

### 常見問題

1. **郵件發送失敗**
   - 檢查 n8n webhook URL 是否正確
   - 確認 n8n 工作流程是否正常運行
   - 檢查 Gmail 認證是否有效

2. **連接 n8n 失敗**
   - 確認 ngrok 服務是否正常
   - 檢查防火牆設定
   - 驗證 webhook 路徑是否正確

3. **資料庫錯誤**
   - 重新初始化資料庫：`python database.py`
   - 檢查檔案權限
   - 確認磁碟空間足夠

### 日誌檢查

```bash
# 查看 FastAPI 日誌
tail -f logs/app.log

# 檢查 n8n 執行記錄
# 在 n8n 介面中查看工作流程執行狀態
```

### 重設系統

```bash
# 重設資料庫
python database.py

# 清除快取
rm -rf __pycache__
rm -rf .pytest_cache
```

## 開發指南

### 目錄結構

```
mail_sender_project/
├── backend/
│   ├── main.py              # FastAPI 主程式
│   ├── models.py            # 資料模型
│   ├── database.py          # 資料庫操作
│   ├── config.py            # 系統設定
│   └── requirements.txt     # Python 依賴
├── frontend/
│   ├── index.html           # 前端介面
│   └── static/
│       ├── css/
│       └── js/
├── logs/                    # 日誌檔案
├── emails.db               # SQLite 資料庫
└── README.md               # 使用說明
```

### 添加新功能

1. **新增 API 端點**
   - 在 `main.py` 中添加新的路由
   - 在 `models.py` 中定義相應的資料模型

2. **擴展前端功能**
   - 修改 `index.html` 添加新的 UI 元素
   - 在 JavaScript 中添加相應的處理邏輯

3. **資料庫變更**
   - 修改 `database.py` 中的資料表結構
   - 執行資料庫遷移

### 測試

```bash
# 執行 API 測試
pytest tests/

# 測試 webhook 連接
curl -X POST http://localhost:8000/api/send-email \
  -H "Content-Type: application/json" \
  -d '{"to":"test@example.com","subject":"測試","content":"測試內容"}'
```

## 部署建議

### 生產環境部署

1. **使用 Docker**
   ```dockerfile
   FROM python:3.9-slim
   WORKDIR /app
   COPY requirements.txt .
   RUN pip install -r requirements.txt
   COPY . .
   CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
   ```

2. **使用 Nginx 反向代理**
   ```nginx
   server {
       listen 80;
       server_name your-domain.com;
       
       location / {
           proxy_pass http://localhost:8000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
       }
   }
   ```

3. **使用 systemd 服務**
   ```ini
   [Unit]
   Description=Mail Sender Service
   After=network.target

   [Service]
   Type=simple
   User=www-data
   WorkingDirectory=/path/to/mail_sender_project/backend
   ExecStart=/path/to/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000
   Restart=always

   [Install]
   WantedBy=multi-user.target
   ```

### 安全建議

1. **設定 HTTPS**
2. **使用環境變數儲存敏感資訊**
3. **實施 API 速率限制**
4. **定期備份資料庫**
5. **監控系統日誌**

## 授權

此專案使用 MIT 授權條款。

## 支援

如有任何問題，請：
1. 查看故障排除章節
2. 檢查 [GitHub Issues](repository-issues-url)
3. 聯繫系統管理員

## 版本歷史

- **v1.0.0** - 初始版本
  - 基本郵件發送功能
  - 網頁介面
  - n8n 整合
  - 郵件記錄管理

## 貢獻指南

歡迎提交 Pull Request 和 Issues。請遵循以下指南：

1. Fork 專案
2. 建立功能分支
3. 提交變更
4. 推送到分支
5. 開啟 Pull Request

---

**注意：** 請確保在使用前正確設定 n8n 工作流程和 Gmail 認證。