from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import json
import os
from typing import List, Dict, Optional
from pydantic import BaseModel, EmailStr
import uvicorn
import requests
from pathlib import Path
import logging

# 設定日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('market_analysis.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 嘗試載入設定檔，如果沒有就使用預設值
try:
    from config import SERVER_CONFIG, WEBHOOK_CONFIG, EMAIL_TEMPLATES, SENTIMENT_CONFIG, SYSTEM_INFO

    logger.info("✅ 成功載入 config.py 設定檔")
except ImportError:
    logger.warning("⚠️  找不到 config.py，使用預設配置")
    SERVER_CONFIG = {
        'host': '0.0.0.0',
        'port': 8089,
        'debug': True
    }
    WEBHOOK_CONFIG = {
        'send_url': 'https://beloved-swine-sensibly.ngrok-free.app/webhook/Webhook - Preview',
        'timeout': 30
    }
    EMAIL_TEMPLATES = {
        'default_subject': '市場分析報告',
        'report_header': '=== 市場分析報告 ===',
        'report_footer': '--- 報告結束 ---'
    }
    SENTIMENT_CONFIG = {
        'thresholds': {
            'very_positive': 0.5,
            'positive': 0.1,
            'neutral_lower': -0.1,
            'negative': -0.5
        },
        'labels': {
            'very_positive': '極度樂觀',
            'positive': '樂觀',
            'neutral': '中性',
            'negative': '悲觀',
            'very_negative': '極度悲觀'
        }
    }
    SYSTEM_INFO = {
        'name': 'Market Analysis Report System',
        'version': '1.0.0',
        'description': '市場分析報告發送系統'
    }

# 初始化 FastAPI 應用
app = FastAPI(
    title=SYSTEM_INFO['name'],
    description=SYSTEM_INFO['description'],
    version=SYSTEM_INFO['version'],
    docs_url="/docs",
    redoc_url="/redoc"
)

# 添加 CORS 中介軟體
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 確保必要的目錄存在
def ensure_directories():
    """確保必要的目錄存在"""
    directories = [
        "frontend",
        "frontend/static",
        "logs"
    ]

    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        logger.info(f"📁 確保目錄存在: {directory}")


ensure_directories()

# 掛載靜態檔案
static_dir = Path("frontend/static")
if static_dir.exists():
    app.mount("/static", StaticFiles(directory="frontend/static"), name="static")
    logger.info("📂 已掛載靜態檔案目錄")

# 全域變數儲存資料
stored_data = {}
system_stats = {
    "total_reports": 0,
    "today_reports": 0,
    "last_reset": datetime.now().date(),
    "avg_sentiment": 0.0
}


# 資料模型
class N8NData(BaseModel):
    """N8N 傳入的資料模型"""
    average_sentiment_score: float
    message: Dict[str, str]


class EmailRequest(BaseModel):
    """郵件發送請求模型"""
    recipient_email: EmailStr
    subject: str = EMAIL_TEMPLATES['default_subject']


class SystemStatus(BaseModel):
    """系統狀態模型"""
    status: str
    timestamp: str
    has_data: bool
    system_info: Dict
    webhook_url: str


# 路由處理
@app.get("/", response_class=HTMLResponse)
async def home():
    """提供主頁面"""
    try:
        html_file = Path("frontend") / "index.html"

        # 如果存在自訂的 HTML 檔案，就使用它
        if html_file.exists():
            with open(html_file, 'r', encoding='utf-8') as f:
                return HTMLResponse(content=f.read())

        # 否則返回內建的 HTML（從 artifacts 複製）
        return FileResponse("frontend/index.html") if html_file.exists() else HTMLResponse(
            content=get_default_html(),
            status_code=200
        )
    except Exception as e:
        logger.error(f"❌ 載入主頁面失敗: {str(e)}")
        return HTMLResponse(content=get_error_html(str(e)), status_code=500)


def get_default_html():
    """返回預設的 HTML 內容"""
    return """
    <!DOCTYPE html>
    <html lang="zh-TW">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>市場分析報告系統</title>
        <style>
            body { font-family: 'Segoe UI', sans-serif; margin: 0; padding: 2rem; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; }
            .container { max-width: 800px; margin: 0 auto; }
            .header { text-align: center; margin-bottom: 2rem; }
            .card { background: rgba(255,255,255,0.1); border-radius: 15px; padding: 2rem; margin-bottom: 2rem; backdrop-filter: blur(10px); }
            .btn { background: #4299e1; color: white; border: none; padding: 1rem 2rem; border-radius: 8px; cursor: pointer; font-size: 1rem; }
            .btn:disabled { opacity: 0.5; cursor: not-allowed; }
            input { width: 100%; padding: 0.75rem; border: none; border-radius: 8px; margin-top: 0.5rem; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🚀 市場分析報告系統</h1>
                <p>系統正在載入中...</p>
            </div>
            <div class="card">
                <h2>📊 系統狀態</h2>
                <p id="status">正在檢查系統狀態...</p>
            </div>
            <div class="card">
                <h2>📧 發送報告</h2>
                <form id="emailForm">
                    <label>收件人郵件地址:</label>
                    <input type="email" id="email" required>
                    <br><br>
                    <button type="submit" class="btn" id="sendBtn" disabled>發送報告</button>
                </form>
            </div>
        </div>

        <script>
            async function checkStatus() {
                try {
                    const response = await fetch('/health');
                    const data = await response.json();
                    document.getElementById('status').innerHTML = 
                        `✅ 系統運行正常<br>時間: ${data.timestamp}<br>版本: ${data.version}`;
                    document.getElementById('sendBtn').disabled = false;
                } catch (error) {
                    document.getElementById('status').innerHTML = '❌ 系統連接失敗';
                }
            }

            document.getElementById('emailForm').addEventListener('submit', async (e) => {
                e.preventDefault();
                const email = document.getElementById('email').value;
                const btn = document.getElementById('sendBtn');
                btn.disabled = true;
                btn.textContent = '發送中...';

                try {
                    const response = await fetch('/api/send-email', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ recipient_email: email, subject: '市場分析報告' })
                    });
                    const result = await response.json();
                    alert(response.ok ? '✅ ' + result.message : '❌ ' + result.detail);
                } catch (error) {
                    alert('❌ 發送失敗: ' + error.message);
                } finally {
                    btn.disabled = false;
                    btn.textContent = '發送報告';
                }
            });

            checkStatus();
            setInterval(checkStatus, 30000);
        </script>
    </body>
    </html>
    """


def get_error_html(error_message):
    """返回錯誤頁面"""
    return f"""
    <!DOCTYPE html>
    <html>
    <head><title>系統錯誤</title></head>
    <body style="font-family: Arial; text-align: center; padding: 2rem; background: #f5f5f5;">
        <h1 style="color: #e53e3e;">系統錯誤</h1>
        <p>載入頁面時發生錯誤：{error_message}</p>
        <button onclick="location.reload()" style="padding: 0.5rem 1rem; background: #3182ce; color: white; border: none; border-radius: 4px; cursor: pointer;">重新載入</button>
    </body>
    </html>
    """


@app.post("/api/n8n-data")
async def receive_n8n_data(data: List[N8NData]):
    """接收來自 N8N 的市場分析資料"""
    try:
        global stored_data, system_stats

        if not data:
            logger.warning("⚠️  收到空的資料列表")
            raise HTTPException(status_code=400, detail="沒有接收到市場分析資料")

        market_data = data[0]

        # 儲存資料
        stored_data = {
            "average_sentiment_score": market_data.average_sentiment_score,
            "message_content": market_data.message.get("content", ""),
            "market_date": datetime.now().strftime("%Y-%m-%d"),
            "received_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "raw_data": market_data.dict()
        }

        # 更新統計
        update_system_stats(market_data.average_sentiment_score)

        logger.info(f"✅ 成功接收 N8N 資料:")
        logger.info(f"   情緒評分: {market_data.average_sentiment_score}")
        logger.info(f"   內容長度: {len(market_data.message.get('content', ''))}")
        logger.info(f"   接收時間: {stored_data['received_time']}")

        return {
            "status": "success",
            "message": "市場分析資料已接收並儲存",
            "data": stored_data,
            "stats": system_stats
        }

    except Exception as e:
        logger.error(f"❌ 接收 N8N 資料失敗: {str(e)}")
        raise HTTPException(status_code=500, detail=f"接收資料失敗: {str(e)}")


@app.get("/api/current-data")
async def get_current_data():
    """取得目前儲存的市場分析資料"""
    try:
        logger.info(f"📊 取得當前資料，資料存在: {len(stored_data) > 0}")
        return {
            "status": "success",
            "data": stored_data,
            "stats": system_stats,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"❌ 取得當前資料失敗: {str(e)}")
        return {
            "status": "error",
            "data": {},
            "stats": system_stats,
            "error": str(e)
        }


@app.post("/api/send-email")
async def send_email(email_data: EmailRequest):
    """發送市場分析報告到指定的 webhook"""
    try:
        logger.info(f"🚀 開始發送程序...")
        logger.info(f"   收件人: {email_data.recipient_email}")
        logger.info(f"   主題: {email_data.subject}")

        # 檢查是否有市場資料
        if not stored_data:
            logger.warning("❌ 沒有市場資料")
            raise HTTPException(
                status_code=400,
                detail="沒有可用的市場分析資料，請先從 N8N 傳送資料"
            )

        if "raw_data" not in stored_data:
            logger.warning("❌ 市場資料格式不完整")
            raise HTTPException(
                status_code=400,
                detail="市場資料格式不完整"
            )

        # 建立郵件內容
        email_content = create_email_content()
        logger.info(f"   郵件內容長度: {len(email_content)} 字元")

        # 準備要發送的資料結構
        send_data = [{
            "headers": {
                "host": "beloved-swine-sensibly.ngrok-free.app",
                "user-agent": "market-analysis-system/1.0",
                "accept": "application/json",
                "content-type": "application/json",
                "x-forwarded-for": "system",
                "x-real-ip": "system"
            },
            "params": {},
            "query": {
                "to": str(email_data.recipient_email),
                "subject": email_data.subject,
                "content": email_content,
                "data": json.dumps([stored_data["raw_data"]], ensure_ascii=False),
                "timestamp": datetime.now().isoformat(),
                "sentiment_score": str(stored_data.get("average_sentiment_score", 0)),
                "market_date": stored_data.get("market_date", ""),
                "system_version": SYSTEM_INFO['version']
            },
            "body": {
                "email_data": email_data.dict(),
                "market_summary": {
                    "sentiment_score": stored_data.get("average_sentiment_score"),
                    "sentiment_text": get_sentiment_text(stored_data.get("average_sentiment_score", 0)),
                    "content_preview": stored_data.get("message_content", "")[:100] + "..." if stored_data.get(
                        "message_content") else "",
                    "generated_time": stored_data.get("received_time")
                }
            },
            "webhookUrl": WEBHOOK_CONFIG['send_url'],
            "executionMode": "production"
        }]

        logger.info(f"📤 發送資料到: {WEBHOOK_CONFIG['send_url']}")

        # 發送資料到指定的 webhook URL
        response = requests.post(
            WEBHOOK_CONFIG['send_url'],
            json=send_data,
            headers={
                "Content-Type": "application/json",
                "User-Agent": f"{SYSTEM_INFO['name']}/{SYSTEM_INFO['version']}"
            },
            timeout=WEBHOOK_CONFIG['timeout']
        )

        logger.info(f"📨 回應狀態碼: {response.status_code}")
        if response.text:
            logger.info(f"📄 回應內容: {response.text[:200]}...")

        if response.status_code == 200:
            # 更新統計
            system_stats["total_reports"] += 1
            today = datetime.now().date()
            if system_stats["last_reset"] != today:
                system_stats["today_reports"] = 1
                system_stats["last_reset"] = today
            else:
                system_stats["today_reports"] += 1

            logger.info("✅ 發送成功!")
            return {
                "status": "success",
                "message": f"市場分析報告已成功發送至 {email_data.recipient_email}",
                "sent_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "target_url": WEBHOOK_CONFIG['send_url'],
                "stats": system_stats,
                "sentiment_info": {
                    "score": stored_data.get("average_sentiment_score"),
                    "text": get_sentiment_text(stored_data.get("average_sentiment_score", 0))
                }
            }
        else:
            logger.error(f"❌ 發送失敗，HTTP 狀態碼: {response.status_code}")
            raise HTTPException(
                status_code=500,
                detail=f"發送失敗，HTTP 狀態碼: {response.status_code}，回應: {response.text[:100]}"
            )

    except requests.exceptions.Timeout:
        logger.error("❌ 請求超時")
        raise HTTPException(status_code=500, detail="請求超時，請檢查網路連接")
    except requests.exceptions.ConnectionError:
        logger.error("❌ 連接錯誤")
        raise HTTPException(
            status_code=500,
            detail=f"無法連接到 {WEBHOOK_CONFIG['send_url']}，請檢查 URL 是否正確"
        )
    except Exception as e:
        logger.error(f"❌ 發送失敗: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"發送失敗: {str(e)}")


@app.get("/api/stats")
async def get_system_stats():
    """取得系統統計資料"""
    try:
        return {
            "status": "success",
            "stats": system_stats,
            "has_current_data": len(stored_data) > 0,
            "last_data_time": stored_data.get("received_time") if stored_data else None,
            "system_info": SYSTEM_INFO
        }
    except Exception as e:
        logger.error(f"❌ 取得統計資料失敗: {str(e)}")
        raise HTTPException(status_code=500, detail=f"取得統計資料失敗: {str(e)}")


@app.get("/health")
async def health_check():
    """系統健康檢查"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "system": SYSTEM_INFO['name'],
        "version": SYSTEM_INFO['version'],
        "webhook_url": WEBHOOK_CONFIG['send_url'],
        "has_data": len(stored_data) > 0,
        "stats": system_stats,
        "uptime": "系統運行中",
        "note": "此系統透過 webhook 發送資料，不直接使用 Gmail"
    }


@app.get("/api/test-connection")
async def test_webhook_connection():
    """測試 webhook 連接"""
    try:
        logger.info(f"🔍 測試連接到: {WEBHOOK_CONFIG['send_url']}")

        # 發送測試請求
        test_response = requests.get(
            WEBHOOK_CONFIG['send_url'],
            timeout=10,
            headers={"User-Agent": f"{SYSTEM_INFO['name']}/test"}
        )

        logger.info(f"✅ 測試連接成功，狀態碼: {test_response.status_code}")

        return {
            "status": "success",
            "target_url": WEBHOOK_CONFIG['send_url'],
            "response_code": test_response.status_code,
            "response_time": "< 10s",
            "message": "Webhook 連接測試成功",
            "timestamp": datetime.now().isoformat()
        }
    except requests.exceptions.Timeout:
        logger.warning("⚠️  測試連接超時")
        return {
            "status": "timeout",
            "target_url": WEBHOOK_CONFIG['send_url'],
            "error": "連接超時",
            "message": "Webhook 連接測試超時，但這不一定表示服務不可用"
        }
    except requests.exceptions.ConnectionError as e:
        logger.error(f"❌ 測試連接失敗: {str(e)}")
        return {
            "status": "error",
            "target_url": WEBHOOK_CONFIG['send_url'],
            "error": str(e),
            "message": "無法連接到 webhook，請檢查 URL 和網路連接"
        }
    except Exception as e:
        logger.error(f"❌ 測試連接發生未知錯誤: {str(e)}")
        return {
            "status": "error",
            "target_url": WEBHOOK_CONFIG['send_url'],
            "error": str(e),
            "message": "測試連接失敗"
        }


# 輔助函數
def create_email_content() -> str:
    """建立郵件內容"""
    try:
        content_parts = []

        # 郵件標題
        content_parts.append(EMAIL_TEMPLATES['report_header'])
        content_parts.append(f"生成時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        content_parts.append("")

        # 情感分析
        sentiment_score = stored_data.get("average_sentiment_score", 0)
        sentiment_text = get_sentiment_text(sentiment_score)
        market_emoji = get_market_emoji(sentiment_score)

        content_parts.append(f"📊 市場情緒評分: {sentiment_score:.3f}")
        content_parts.append(f"📈 市場情緒: {sentiment_text} {market_emoji}")
        content_parts.append(f"📅 市場日期: {stored_data.get('market_date', '今日')}")
        content_parts.append("")

        # 市場分析內容
        content_parts.append("🏛️ 市場分析詳情:")
        content_parts.append("-" * 40)
        market_content = stored_data.get("message_content", "無分析內容")
        content_parts.append(market_content)
        content_parts.append("-" * 40)
        content_parts.append("")

        # 系統資訊
        content_parts.append(f"🤖 報告系統: {SYSTEM_INFO['name']} v{SYSTEM_INFO['version']}")
        content_parts.append(f"⏰ 資料接收時間: {stored_data.get('received_time', '未知')}")
        content_parts.append("")

        content_parts.append(EMAIL_TEMPLATES['report_footer'])

        return "\\n".join(content_parts)

    except Exception as e:
        logger.error(f"❌ 建立郵件內容失敗: {str(e)}")
        return f"❌ 郵件內容建立失敗: {str(e)}"


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
        logger.error(f"❌ 取得情感文字失敗: {str(e)}")
        return "未知"


def get_market_emoji(score: float) -> str:
    """根據情感分數返回對應的表情符號"""
    if score > 0.5:
        return "🚀📈"
    elif score > 0.1:
        return "📈🟢"
    elif score > -0.1:
        return "➡️🟡"
    elif score > -0.5:
        return "📉🟠"
    else:
        return "📉🔴"


def update_system_stats(sentiment_score: float):
    """更新系統統計資料"""
    try:
        global system_stats

        # 檢查是否需要重置每日統計
        today = datetime.now().date()
        if system_stats["last_reset"] != today:
            system_stats["today_reports"] = 0
            system_stats["last_reset"] = today
            logger.info(f"📅 重置每日統計 - 新的一天: {today}")

        # 更新平均情緒（簡化版本，實際應該維護歷史資料）
        system_stats["avg_sentiment"] = sentiment_score

        logger.info(f"📊 統計已更新: {system_stats}")

    except Exception as e:
        logger.error(f"❌ 更新統計失敗: {str(e)}")


# 啟動事件
@app.on_event("startup")
async def startup_event():
    """應用啟動時的初始化"""
    logger.info("🚀 市場分析報告系統啟動中...")
    logger.info(f"📡 目標 Webhook URL: {WEBHOOK_CONFIG['send_url']}")
    logger.info(f"🌐 伺服器位置: http://{SERVER_CONFIG['host']}:{SERVER_CONFIG['port']}")
    logger.info(f"📖 API 文檔: http://{SERVER_CONFIG['host']}:{SERVER_CONFIG['port']}/docs")
    logger.info("⚠️  注意: 此系統透過 webhook 發送資料，不直接使用 Gmail")
    logger.info("✅ 系統啟動完成")


@app.on_event("shutdown")
async def shutdown_event():
    """應用關閉時的清理"""
    logger.info("🛑 市場分析報告系統正在關閉...")
    logger.info(f"📊 最終統計: {system_stats}")
    logger.info("👋 系統已安全關閉")


# 錯誤處理
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """全域異常處理器"""
    logger.error(f"❌ 全域異常: {str(exc)}")
    logger.error(f"   請求路徑: {request.url}")
    import traceback
    logger.error(f"   錯誤詳情: {traceback.format_exc()}")

    return {
        "status": "error",
        "message": "系統發生內部錯誤",
        "detail": str(exc) if SERVER_CONFIG.get('debug', False) else "請聯繫系統管理員",
        "timestamp": datetime.now().isoformat()
    }


# 主程式入口點
if __name__ == "__main__":
    print("🚀 啟動市場分析報告系統...")
    print(f"📡 目標 Webhook URL: {WEBHOOK_CONFIG['send_url']}")
    print(f"🌐 伺服器位置: http://{SERVER_CONFIG['host']}:{SERVER_CONFIG['port']}")
    print(f"📖 API 文檔: http://{SERVER_CONFIG['host']}:{SERVER_CONFIG['port']}/docs")
    print("⚠️  注意: 此系統不使用 Gmail 發送郵件，而是透過 webhook 轉發資料")
    print("-" * 60)

    try:
        uvicorn.run(
            app,
            host=SERVER_CONFIG['host'],
            port=SERVER_CONFIG['port'],
            log_level="info",
            reload=SERVER_CONFIG.get('debug', False),
            access_log=True
        )
    except KeyboardInterrupt:
        print("\n👋 使用者中斷，系統正在安全關閉...")
    except Exception as e:
        print(f"❌ 系統啟動失敗: {str(e)}")
        logger.error(f"系統啟動失敗: {str(e)}")
    finally:
        print("🛑 系統已關閉")