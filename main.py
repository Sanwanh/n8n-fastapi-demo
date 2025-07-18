from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from datetime import datetime
import json
from typing import List, Dict
from pydantic import BaseModel
import uvicorn
import requests
from pathlib import Path

# 如果有 config.py 就使用，沒有就用預設值
try:
    from config import SERVER_CONFIG, WEBHOOK_CONFIG, EMAIL_TEMPLATES, SENTIMENT_CONFIG, SYSTEM_INFO
except ImportError:
    print("⚠️  找不到 config.py，使用預設配置")
    SERVER_CONFIG = {'host': '0.0.0.0', 'port': 8089, 'debug': True}
    WEBHOOK_CONFIG = {'send_url': 'https://beloved-swine-sensibly.ngrok-free.app/webhook/Webhook - Preview',
                      'timeout': 30}
    EMAIL_TEMPLATES = {'default_subject': '市場分析報告', 'report_header': '=== 市場分析報告 ===',
                       'report_footer': '--- 報告結束 ---'}
    SENTIMENT_CONFIG = {'thresholds': {'very_positive': 0.5, 'positive': 0.1, 'neutral_lower': -0.1, 'negative': -0.5},
                        'labels': {'very_positive': '正面', 'positive': '中性偏正', 'neutral': '中性',
                                   'negative': '中性偏負', 'very_negative': '負面'}}
    SYSTEM_INFO = {'name': 'Market Analysis Report System', 'version': '1.0.0', 'description': '市場分析報告發送系統'}

app = FastAPI(
    title=SYSTEM_INFO['name'],
    description=SYSTEM_INFO['description'],
    version=SYSTEM_INFO['version']
)

# 確保靜態檔案目錄存在
static_dir = Path("frontend/static")
static_dir.mkdir(parents=True, exist_ok=True)

# 掛載靜態檔案（如果目錄存在）
if static_dir.exists():
    app.mount("/static", StaticFiles(directory="frontend/static"), name="static")

# 全域變數儲存 n8n 資料
stored_data = {}

# 發送目標 URL
SEND_URL = WEBHOOK_CONFIG['send_url']


class N8NData(BaseModel):
    average_sentiment_score: float
    message: Dict[str, str]


class EmailRequest(BaseModel):
    recipient_email: str
    subject: str = EMAIL_TEMPLATES['default_subject']


@app.get("/", response_class=HTMLResponse)
async def home():
    """主頁面"""
    html_content = """
<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>市場分析報告發送系統</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; color: #333; }
        .container { max-width: 800px; margin: 0 auto; padding: 2rem; }
        .header { text-align: center; margin-bottom: 3rem; color: white; }
        .header h1 { font-size: 2.5rem; margin-bottom: 0.5rem; text-shadow: 2px 2px 4px rgba(0,0,0,0.3); }
        .header p { font-size: 1.1rem; opacity: 0.9; }
        .card { background: white; border-radius: 20px; padding: 2rem; margin-bottom: 2rem; box-shadow: 0 10px 30px rgba(0,0,0,0.1); transition: transform 0.3s ease; }
        .card:hover { transform: translateY(-5px); }
        .card-title { font-size: 1.5rem; color: #4a5568; margin-bottom: 1rem; display: flex; align-items: center; gap: 0.5rem; }
        .status-indicator { display: flex; align-items: center; gap: 0.5rem; margin-bottom: 1rem; padding: 1rem; background: #f7fafc; border-radius: 10px; border-left: 4px solid #4299e1; }
        .indicator-dot { width: 10px; height: 10px; border-radius: 50%; background: #48bb78; animation: pulse 2s infinite; }
        @keyframes pulse { 0% { opacity: 1; } 50% { opacity: 0.5; } 100% { opacity: 1; } }
        .form-group { margin-bottom: 1.5rem; }
        .form-group label { display: block; margin-bottom: 0.5rem; font-weight: 600; color: #4a5568; }
        .form-group input { width: 100%; padding: 0.75rem 1rem; border: 2px solid #e2e8f0; border-radius: 10px; font-size: 1rem; transition: border-color 0.3s ease; }
        .form-group input:focus { outline: none; border-color: #4299e1; box-shadow: 0 0 0 3px rgba(66, 153, 225, 0.1); }
        .btn { background: linear-gradient(135deg, #4299e1 0%, #667eea 100%); color: white; border: none; padding: 1rem 2rem; border-radius: 10px; font-size: 1.1rem; font-weight: 600; cursor: pointer; transition: all 0.3s ease; width: 100%; display: flex; align-items: center; justify-content: center; gap: 0.5rem; }
        .btn:hover { transform: translateY(-2px); box-shadow: 0 5px 15px rgba(66, 153, 225, 0.3); }
        .btn:disabled { background: #a0aec0; cursor: not-allowed; transform: none; box-shadow: none; }
        .data-display { background: #f7fafc; border: 1px solid #e2e8f0; border-radius: 10px; padding: 1rem; margin-top: 1rem; }
        .data-item { margin-bottom: 0.5rem; font-family: 'Courier New', monospace; }
        .data-label { font-weight: 600; color: #4a5568; }
        .data-value { color: #2d3748; }
        .loading { display: none; text-align: center; color: #718096; }
        .spinner { border: 3px solid #f3f3f3; border-top: 3px solid #4299e1; border-radius: 50%; width: 30px; height: 30px; animation: spin 1s linear infinite; margin: 0 auto 1rem; }
        @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
        .alert { padding: 1rem; border-radius: 10px; margin-bottom: 1rem; display: none; }
        .alert-success { background: #f0fff4; border: 1px solid #68d391; color: #22543d; }
        .alert-error { background: #fed7d7; border: 1px solid #fc8181; color: #742a2a; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 市場分析報告發送系統</h1>
            <p>智能市場情感分析 • 自動化報告發送 • 無需 Gmail 設定</p>
        </div>

        <div class="card">
            <div class="card-title">📈 市場資料狀態</div>
            <div class="status-indicator" id="status-indicator">
                <div class="indicator-dot"></div>
                <span id="status-text">正在檢查市場資料...</span>
            </div>
            <div id="market-data-display" class="data-display" style="display: none;">
                <div class="data-item"><span class="data-label">情緒評分：</span><span class="data-value" id="sentiment-score">--</span></div>
                <div class="data-item"><span class="data-label">市場內容：</span><span class="data-value" id="market-content">--</span></div>
                <div class="data-item"><span class="data-label">接收時間：</span><span class="data-value" id="received-time">--</span></div>
            </div>
        </div>

        <div class="card">
            <div class="card-title">📧 資料發送設定</div>
            <div class="alert alert-success" id="success-alert"></div>
            <div class="alert alert-error" id="error-alert"></div>
            <form id="email-form">
                <div class="form-group">
                    <label for="recipient_email">📧 收件人郵件地址</label>
                    <input type="email" id="recipient_email" name="recipient_email" placeholder="example@company.com" required>
                </div>
                <div class="form-group">
                    <label for="subject">📋 郵件主題</label>
                    <input type="text" id="subject" name="subject" value="市場分析報告" required>
                </div>
                <div class="loading" id="loading">
                    <div class="spinner"></div>
                    <p>正在發送資料...</p>
                </div>
                <button type="submit" class="btn" id="send-btn" disabled>🚀 發送市場報告</button>
            </form>
        </div>
    </div>

    <script>
        async function checkMarketData() {
            try {
                const response = await fetch('/api/current-data');
                const result = await response.json();
                if (result.data && Object.keys(result.data).length > 0) {
                    const data = result.data;
                    document.getElementById('status-text').textContent = '市場資料已準備就緒';
                    document.getElementById('market-data-display').style.display = 'block';
                    document.getElementById('sentiment-score').textContent = data.average_sentiment_score || '--';
                    document.getElementById('market-content').textContent = (data.message_content || '無內容').substring(0, 100) + '...';
                    document.getElementById('received-time').textContent = data.received_time || '--';
                    document.getElementById('send-btn').disabled = false;
                } else {
                    document.getElementById('status-text').textContent = '等待市場資料...';
                    document.getElementById('send-btn').disabled = true;
                }
            } catch (error) {
                document.getElementById('status-text').textContent = '資料檢查失敗';
                console.error('Error:', error);
            }
        }

        async function sendEmail(event) {
            event.preventDefault();
            const form = event.target;
            const formData = new FormData(form);
            const data = { recipient_email: formData.get('recipient_email'), subject: formData.get('subject') };
            document.getElementById('loading').style.display = 'block';
            document.getElementById('send-btn').disabled = true;
            hideAlerts();
            try {
                const response = await fetch('/api/send-email', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(data)
                });
                const result = await response.json();
                if (response.ok) {
                    showAlert('success', `✅ ${result.message}`);
                } else {
                    showAlert('error', `❌ ${result.detail || '發送失敗'}`);
                }
            } catch (error) {
                showAlert('error', `❌ 網路錯誤: ${error.message}`);
            } finally {
                document.getElementById('loading').style.display = 'none';
                document.getElementById('send-btn').disabled = false;
            }
        }

        function showAlert(type, message) {
            const alertId = type === 'success' ? 'success-alert' : 'error-alert';
            const alertElement = document.getElementById(alertId);
            alertElement.textContent = message;
            alertElement.style.display = 'block';
            setTimeout(() => { alertElement.style.display = 'none'; }, 3000);
        }

        function hideAlerts() {
            document.getElementById('success-alert').style.display = 'none';
            document.getElementById('error-alert').style.display = 'none';
        }

        document.addEventListener('DOMContentLoaded', function() {
            checkMarketData();
            setInterval(checkMarketData, 5000);
            document.getElementById('email-form').addEventListener('submit', sendEmail);
        });
    </script>
</body>
</html>
    """
    return HTMLResponse(content=html_content)


@app.post("/api/n8n-data")
async def receive_n8n_data(data: List[N8NData]):
    """接收來自 N8N 的市場分析資料"""
    try:
        global stored_data
        if not data:
            raise HTTPException(status_code=400, detail="沒有接收到市場分析資料")

        market_data = data[0]
        stored_data = {
            "average_sentiment_score": market_data.average_sentiment_score,
            "message_content": market_data.message.get("content", ""),
            "received_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "raw_data": market_data.dict()
        }

        print(f"✅ 成功接收 N8N 資料:")
        print(f"   情緒評分: {market_data.average_sentiment_score}")
        print(f"   內容長度: {len(market_data.message.get('content', ''))}")

        return {"status": "success", "message": "市場分析資料已接收並儲存", "data": stored_data}

    except Exception as e:
        print(f"❌ 接收 N8N 資料失敗: {str(e)}")
        raise HTTPException(status_code=500, detail=f"接收資料失敗: {str(e)}")


@app.get("/api/current-data")
async def get_current_data():
    """取得目前儲存的市場分析資料"""
    return {"data": stored_data}


@app.post("/api/send-email")
async def send_email(email_data: EmailRequest):
    """發送市場分析報告 - 只發送資料，不使用 Gmail"""
    try:
        print(f"🚀 開始發送程序...")
        print(f"   收件人: {email_data.recipient_email}")
        print(f"   主題: {email_data.subject}")

        # 檢查是否有市場資料
        if not stored_data:
            print("❌ 沒有市場資料")
            raise HTTPException(status_code=400, detail="沒有可用的市場分析資料，請先從 N8N 傳送資料")

        if "raw_data" not in stored_data:
            print("❌ 市場資料格式不完整")
            raise HTTPException(status_code=400, detail="市場資料格式不完整")

        # 建立郵件內容
        email_content = create_email_content()
        print(f"   郵件內容長度: {len(email_content)}")

        # 準備要發送的資料結構
        send_data = [{
            "headers": {
                "host": "beloved-swine-sensibly.ngrok-free.app",
                "user-agent": "email-sender-client",
                "accept": "application/json",
                "accept-encoding": "gzip, deflate",
                "x-forwarded-for": "172.19.0.4",
                "x-forwarded-host": "beloved-swine-sensibly.ngrok-free.app",
                "x-forwarded-port": "80",
                "x-forwarded-proto": "http",
                "x-forwarded-server": "system",
                "x-real-ip": "172.19.0.4"
            },
            "params": {},
            "query": {
                "to": email_data.recipient_email,
                "subject": email_data.subject,
                "content": email_content,
                "data": json.dumps([stored_data["raw_data"]], ensure_ascii=False),
                "timestamp": datetime.now().isoformat(),
                "sentiment_score": str(stored_data.get("average_sentiment_score", 0))
            },
            "body": {},
            "webhookUrl": SEND_URL,
            "executionMode": "production"
        }]

        print(f"📤 發送資料到: {SEND_URL}")

        # 發送資料到指定的 URL
        response = requests.post(
            SEND_URL,
            json=send_data,
            headers={"Content-Type": "application/json"},
            timeout=WEBHOOK_CONFIG['timeout']
        )

        print(f"📨 回應狀態碼: {response.status_code}")
        if response.text:
            print(f"📄 回應內容: {response.text[:200]}...")

        if response.status_code == 200:
            print("✅ 發送成功!")
            return {
                "status": "success",
                "message": f"市場分析報告已成功發送至 {email_data.recipient_email}",
                "sent_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "target_url": SEND_URL,
                "sent_data": send_data[0]["query"]
            }
        else:
            print(f"❌ 發送失敗，HTTP 狀態碼: {response.status_code}")
            raise HTTPException(status_code=500, detail=f"發送失敗，HTTP 狀態碼: {response.status_code}")

    except requests.exceptions.Timeout:
        print("❌ 請求超時")
        raise HTTPException(status_code=500, detail="請求超時，請檢查網路連接")
    except requests.exceptions.ConnectionError:
        print("❌ 連接錯誤")
        raise HTTPException(status_code=500, detail=f"無法連接到 {SEND_URL}，請檢查 URL 是否正確")
    except Exception as e:
        print(f"❌ 發送失敗: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"發送失敗: {str(e)}")


def create_email_content() -> str:
    """建立郵件內容"""
    try:
        content_parts = []
        content_parts.append(EMAIL_TEMPLATES['report_header'])
        content_parts.append(f"生成時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        content_parts.append("")

        sentiment_score = stored_data.get("average_sentiment_score", 0)
        sentiment_text = get_sentiment_text(sentiment_score)
        content_parts.append(f"市場情緒評分: {sentiment_score} ({sentiment_text})")
        content_parts.append("")

        content_parts.append("市場分析:")
        content_parts.append(stored_data.get("message_content", "無分析內容"))
        content_parts.append("")
        content_parts.append(EMAIL_TEMPLATES['report_footer'])

        return "\\n".join(content_parts)
    except Exception as e:
        print(f"❌ 建立郵件內容失敗: {str(e)}")
        return f"郵件內容建立失敗: {str(e)}"


def get_sentiment_text(score: float) -> str:
    """根據情感分數返回文字描述"""
    try:
        thresholds = SENTIMENT_CONFIG['thresholds']
        labels = SENTIMENT_CONFIG['labels']

        if score > thresholds['very_positive']:
            return labels['very_positive']
        elif score > thresholds['positive']:
            return labels['positive']
        elif score > thresholds['neutral_lower']:
            return labels['neutral']
        elif score > thresholds['negative']:
            return labels['negative']
        else:
            return labels['very_negative']
    except Exception as e:
        print(f"❌ 取得情感文字失敗: {str(e)}")
        return f"未知"


@app.get("/health")
async def health_check():
    """系統健康檢查"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "system": SYSTEM_INFO['name'],
        "version": SYSTEM_INFO['version'],
        "send_url": SEND_URL,
        "has_data": len(stored_data) > 0,
        "note": "此系統不使用 Gmail，只發送資料到 webhook"
    }


@app.get("/api/test")
async def test_connection():
    """測試連接到目標 URL"""
    try:
        response = requests.get(SEND_URL, timeout=10)
        return {
            "status": "success",
            "target_url": SEND_URL,
            "response_code": response.status_code,
            "message": "連接測試成功"
        }
    except Exception as e:
        return {
            "status": "error",
            "target_url": SEND_URL,
            "error": str(e),
            "message": "連接測試失敗"
        }


if __name__ == "__main__":
    print("🚀 啟動市場分析報告系統...")
    print(f"📡 目標 URL: {SEND_URL}")
    print(f"🌐 伺服器: http://{SERVER_CONFIG['host']}:{SERVER_CONFIG['port']}")
    print("⚠️  注意: 此系統不使用 Gmail 發送郵件")

    uvicorn.run(
        app,
        host=SERVER_CONFIG['host'],
        port=SERVER_CONFIG['port'],
        log_level="info",
        reload=SERVER_CONFIG.get('debug', False)
    )