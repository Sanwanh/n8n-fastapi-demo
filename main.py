#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
市場分析報告系統 - 主程式
Market Analysis Report System - Main Application

修正版本，解決配置載入和錯誤處理問題
Fixed version with configuration loading and error handling improvements
"""

import os
import sys
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Any

# 第三方套件
try:
    from fastapi import FastAPI, Request, HTTPException, Response
    from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
    from fastapi.staticfiles import StaticFiles
    from fastapi.middleware.cors import CORSMiddleware
    from pydantic import BaseModel, EmailStr, validator
    import uvicorn
    import requests
except ImportError as e:
    print(f"❌ 缺少必要的套件: {e}")
    print("請執行: pip install -r requirements.txt")
    sys.exit(1)

# 設定基本日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


# 確保日誌目錄存在
def ensure_directories():
    """確保必要的目錄存在"""
    directories = [
        "frontend",
        "frontend/static",
        "logs",
        "data",
        "backups",
        "cache"
    ]

    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)

    # 設定檔案日誌
    try:
        log_file = Path("logs") / "market_analysis.log"
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setFormatter(
            logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        )
        logger.addHandler(file_handler)
        logger.info(f"📁 日誌檔案: {log_file}")
    except Exception as e:
        logger.warning(f"⚠️  無法設定檔案日誌: {e}")


ensure_directories()


# 載入配置檔案
def load_config():
    """載入配置檔案"""
    try:
        # 嘗試載入 config.py
        sys.path.insert(0, os.getcwd())
        import config

        logger.info("✅ 成功載入 config.py")

        # 驗證配置
        validation_result = config.validate_config()
        if not validation_result['valid']:
            logger.error("❌ 配置驗證失敗:")
            for error in validation_result['errors']:
                logger.error(f"   {error}")
            sys.exit(1)

        for warning in validation_result['warnings']:
            logger.warning(f"⚠️  {warning}")

        return {
            'SERVER_CONFIG': config.SERVER_CONFIG,
            'WEBHOOK_CONFIG': config.WEBHOOK_CONFIG,
            'EMAIL_TEMPLATES': config.EMAIL_TEMPLATES,
            'SENTIMENT_CONFIG': config.SENTIMENT_CONFIG,
            'SYSTEM_INFO': config.SYSTEM_INFO,
            'SECURITY_CONFIG': getattr(config, 'SECURITY_CONFIG', {}),
            'FEATURE_FLAGS': getattr(config, 'FEATURE_FLAGS', {}),
            'UI_CONFIG': getattr(config, 'UI_CONFIG', {})
        }

    except ImportError as e:
        logger.warning(f"⚠️  找不到 config.py，使用預設配置: {e}")
        return get_default_config()
    except Exception as e:
        logger.error(f"❌ 載入配置失敗: {e}")
        return get_default_config()


def get_default_config():
    """取得預設配置"""
    return {
        'SERVER_CONFIG': {
            'host': os.getenv('SERVER_HOST', '0.0.0.0'),
            'port': int(os.getenv('SERVER_PORT', 8089)),
            'debug': os.getenv('DEBUG', 'False').lower() == 'true',
            'reload': False,
            'log_level': os.getenv('LOG_LEVEL', 'info')
        },
        'WEBHOOK_CONFIG': {
            'send_url': os.getenv(
                'WEBHOOK_URL',
                'https://beloved-swine-sensibly.ngrok-free.app/webhook-test/ef5ac185-f41a-4a2d-9a78-33d329184c2'
            ),
            'timeout': int(os.getenv('WEBHOOK_TIMEOUT', 30)),
            'retry_attempts': 3,
            'retry_delay': 2,
            'headers': {
                'User-Agent': 'Market-Analysis-System/1.0',
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            }
        },
        'EMAIL_TEMPLATES': {
            'default_subject': '市場分析報告',
            'report_header': '╔══════════════════════════════════════════╗\n║          📊 市場分析報告 📊          ║\n╚══════════════════════════════════════════╝',
            'report_footer': '╔══════════════════════════════════════════╗\n║     本報告由智能分析系統自動生成     ║\n║        感謝您使用我們的服務！        ║\n╚══════════════════════════════════════════╝'
        },
        'SENTIMENT_CONFIG': {
            'thresholds': {
                'very_positive': 0.6,
                'positive': 0.2,
                'neutral_upper': 0.1,
                'neutral_lower': -0.1,
                'negative': -0.2,
                'very_negative': -0.6
            },
            'labels': {
                'very_positive': '極度樂觀',
                'positive': '樂觀',
                'neutral_positive': '中性偏樂觀',
                'neutral': '中性',
                'neutral_negative': '中性偏悲觀',
                'negative': '悲觀',
                'very_negative': '極度悲觀'
            },
            'emojis': {
                'very_positive': '🚀📈💚',
                'positive': '📈🟢😊',
                'neutral_positive': '📊🟡😐',
                'neutral': '➡️⚪😑',
                'neutral_negative': '📊🟡😐',
                'negative': '📉🔴😟',
                'very_negative': '💥📉😱'
            }
        },
        'SYSTEM_INFO': {
            'name': 'Market Analysis Report System',
            'version': '1.2.0',
            'description': '智能市場分析報告發送系統',
            'author': 'AI Development Team',
            'build_date': datetime.now().strftime('%Y-%m-%d')
        },
        'SECURITY_CONFIG': {
            'cors_origins': ['*'],
            'cors_methods': ['GET', 'POST', 'PUT', 'DELETE'],
            'cors_headers': ['*']
        },
        'FEATURE_FLAGS': {
            'enable_n8n_integration': True,
            'enable_webhook_forwarding': True,
            'enable_sentiment_analysis': True
        },
        'UI_CONFIG': {
            'theme': {
                'primary_color': '#2563eb',
                'success_color': '#10b981',
                'error_color': '#ef4444'
            }
        }
    }


# 載入配置
CONFIG = load_config()


# 資料模型
class N8NData(BaseModel):
    """N8N 傳入的資料模型"""
    average_sentiment_score: float
    message: Dict[str, str]

    @validator('average_sentiment_score')
    def validate_sentiment_score(cls, v):
        if not -1.0 <= v <= 1.0:
            raise ValueError('情感分數必須在 -1.0 到 1.0 之間')
        return v


class EmailRequest(BaseModel):
    """郵件發送請求模型"""
    recipient_email: EmailStr
    subject: str = CONFIG['EMAIL_TEMPLATES']['default_subject']
    custom_content: Optional[str] = ""
    include_sentiment: bool = True
    include_message: bool = True


class SystemStatus(BaseModel):
    """系統狀態模型"""
    status: str
    timestamp: str
    has_data: bool
    system_info: Dict[str, Any]
    webhook_url: str


# 初始化 FastAPI 應用
app = FastAPI(
    title=CONFIG['SYSTEM_INFO']['name'],
    description=CONFIG['SYSTEM_INFO']['description'],
    version=CONFIG['SYSTEM_INFO']['version'],
    docs_url="/docs",
    redoc_url="/redoc"
)

# 添加 CORS 中介軟體
app.add_middleware(
    CORSMiddleware,
    allow_origins=CONFIG['SECURITY_CONFIG']['cors_origins'],
    allow_credentials=True,
    allow_methods=CONFIG['SECURITY_CONFIG']['cors_methods'],
    allow_headers=CONFIG['SECURITY_CONFIG']['cors_headers'],
)

# 掛載靜態檔案
static_dir = Path("frontend/static")
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
    logger.info("📂 已掛載靜態檔案目錄")

# 全域變數儲存資料
stored_data = {}
system_stats = {
    "total_reports": 0,
    "today_reports": 0,
    "last_reset": datetime.now().date(),
    "avg_sentiment": 0.0,
    "uptime_start": datetime.now()
}


# 路由處理
@app.get("/", response_class=HTMLResponse)
async def home():
    """提供主頁面"""
    try:
        html_file = Path("frontend") / "index.html"

        if html_file.exists():
            with open(html_file, 'r', encoding='utf-8') as f:
                content = f.read()
            return HTMLResponse(content=content)
        else:
            # 建立預設 HTML 檔案
            default_html = get_default_html()
            html_file.parent.mkdir(parents=True, exist_ok=True)
            with open(html_file, 'w', encoding='utf-8') as f:
                f.write(default_html)
            logger.info("📝 已建立預設 HTML 檔案")
            return HTMLResponse(content=default_html)

    except Exception as e:
        logger.error(f"❌ 載入主頁面失敗: {str(e)}")
        return HTMLResponse(content=get_error_html(str(e)), status_code=500)


def get_default_html():
    """返回預設的 HTML 內容"""
    return f"""<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{CONFIG['SYSTEM_INFO']['name']}</title>
    <style>
        :root {{
            --primary: #2563eb;
            --success: #10b981;
            --error: #ef4444;
            --bg: #0f172a;
            --card: rgba(30, 41, 59, 0.8);
            --text: #f8fafc;
            --text-muted: #64748b;
        }}

        * {{ margin: 0; padding: 0; box-sizing: border-box; }}

        body {{
            font-family: 'Segoe UI', sans-serif;
            background: linear-gradient(135deg, var(--bg) 0%, #1e293b 100%);
            color: var(--text);
            min-height: 100vh;
            padding: 2rem;
        }}

        .container {{
            max-width: 800px;
            margin: 0 auto;
        }}

        .header {{
            text-align: center;
            margin-bottom: 2rem;
            padding: 2rem;
            background: var(--card);
            border-radius: 15px;
            backdrop-filter: blur(10px);
        }}

        .card {{
            background: var(--card);
            border-radius: 15px;
            padding: 2rem;
            margin-bottom: 2rem;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255,255,255,0.1);
        }}

        .btn {{
            background: var(--primary);
            color: white;
            border: none;
            padding: 1rem 2rem;
            border-radius: 8px;
            cursor: pointer;
            font-size: 1rem;
            transition: all 0.3s ease;
        }}

        .btn:hover {{ 
            background: #1d4ed8; 
            transform: translateY(-2px);
        }}

        .btn:disabled {{ 
            opacity: 0.5; 
            cursor: not-allowed; 
            transform: none;
        }}

        input, textarea {{
            width: 100%;
            padding: 0.75rem;
            border: 2px solid rgba(255,255,255,0.1);
            border-radius: 8px;
            margin-top: 0.5rem;
            background: rgba(255,255,255,0.05);
            color: var(--text);
            font-family: inherit;
        }}

        input:focus, textarea:focus {{
            outline: none;
            border-color: var(--primary);
        }}

        .status {{
            padding: 1rem;
            border-radius: 8px;
            margin: 1rem 0;
        }}

        .status.success {{ background: rgba(16, 185, 129, 0.2); }}
        .status.error {{ background: rgba(239, 68, 68, 0.2); }}
        .status.loading {{ background: rgba(245, 158, 11, 0.2); }}

        .form-group {{
            margin-bottom: 1.5rem;
        }}

        label {{
            display: block;
            margin-bottom: 0.5rem;
            font-weight: 600;
        }}

        .loading {{
            display: inline-block;
            width: 20px;
            height: 20px;
            border: 3px solid rgba(255,255,255,0.3);
            border-radius: 50%;
            border-top-color: var(--primary);
            animation: spin 1s ease-in-out infinite;
        }}

        @keyframes spin {{
            to {{ transform: rotate(360deg); }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 {CONFIG['SYSTEM_INFO']['name']}</h1>
            <p>{CONFIG['SYSTEM_INFO']['description']}</p>
            <p>版本: {CONFIG['SYSTEM_INFO']['version']}</p>
        </div>

        <div class="card">
            <h2>📊 系統狀態</h2>
            <div id="status" class="status loading">
                <div class="loading"></div> 正在檢查系統狀態...
            </div>
            <div id="data-info"></div>
        </div>

        <div class="card">
            <h2>📧 發送報告</h2>
            <form id="emailForm">
                <div class="form-group">
                    <label for="email">收件人郵件地址:</label>
                    <input type="email" id="email" required placeholder="example@gmail.com">
                </div>

                <div class="form-group">
                    <label for="subject">郵件主題:</label>
                    <input type="text" id="subject" value="{CONFIG['EMAIL_TEMPLATES']['default_subject']}">
                </div>

                <div class="form-group">
                    <label for="custom_content">自訂內容 (選填):</label>
                    <textarea id="custom_content" rows="3" placeholder="輸入您想要在郵件開頭加入的自訂內容..."></textarea>
                </div>

                <button type="submit" class="btn" id="sendBtn" disabled>
                    <span id="btnText">發送報告</span>
                </button>
            </form>
        </div>
    </div>

    <script>
        let currentData = null;

        async function checkStatus() {{
            try {{
                const response = await fetch('/health');
                const data = await response.json();

                document.getElementById('status').className = 'status success';
                document.getElementById('status').innerHTML = 
                    '✅ 系統運行正常<br>時間: ' + data.timestamp + '<br>版本: ' + data.version;

                // 檢查是否有資料
                const dataResponse = await fetch('/api/current-data');
                const dataResult = await dataResponse.json();

                if (dataResult.data && Object.keys(dataResult.data).length > 0) {{
                    currentData = dataResult.data;
                    document.getElementById('data-info').innerHTML = 
                        '<h3>📈 當前市場資料</h3>' +
                        '<p>情感分數: ' + dataResult.data.average_sentiment_score + '</p>' +
                        '<p>接收時間: ' + dataResult.data.received_time + '</p>';
                    document.getElementById('sendBtn').disabled = false;
                }} else {{
                    document.getElementById('data-info').innerHTML = 
                        '<h3>⏳ 等待市場資料</h3><p>請確認 N8N 工作流程已正確運行</p>';
                }}

            }} catch (error) {{
                document.getElementById('status').className = 'status error';
                document.getElementById('status').innerHTML = '❌ 系統連接失敗: ' + error.message;
            }}
        }}

        document.getElementById('emailForm').addEventListener('submit', async (e) => {{
            e.preventDefault();

            const email = document.getElementById('email').value;
            const subject = document.getElementById('subject').value;
            const custom_content = document.getElementById('custom_content').value;
            const btn = document.getElementById('sendBtn');
            const btnText = document.getElementById('btnText');

            btn.disabled = true;
            btnText.innerHTML = '<div class="loading"></div> 發送中...';

            try {{
                const response = await fetch('/api/send-email', {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json' }},
                    body: JSON.stringify({{
                        recipient_email: email,
                        subject: subject,
                        custom_content: custom_content
                    }})
                }});

                const result = await response.json();

                if (response.ok) {{
                    alert('✅ ' + result.message);
                }} else {{
                    alert('❌ ' + result.detail);
                }}

            }} catch (error) {{
                alert('❌ 發送失敗: ' + error.message);
            }} finally {{
                btn.disabled = !currentData;
                btnText.textContent = '發送報告';
            }}
        }});

        // 初始化檢查
        checkStatus();

        // 每30秒檢查一次
        setInterval(checkStatus, 30000);
    </script>
</body>
</html>"""


def get_error_html(error_message):
    """返回錯誤頁面"""
    return f"""<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <title>系統錯誤</title>
    <style>
        body {{ 
            font-family: Arial, sans-serif; 
            text-align: center; 
            padding: 2rem; 
            background: #f5f5f5; 
            color: #333;
        }}
        .error-container {{
            max-width: 600px;
            margin: 0 auto;
            background: white;
            padding: 2rem;
            border-radius: 15px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}
        .btn {{
            padding: 0.75rem 1.5rem;
            background: #3182ce;
            color: white;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            font-size: 1rem;
            margin-top: 1rem;
        }}
    </style>
</head>
<body>
    <div class="error-container">
        <h1 style="color: #e53e3e;">❌ 系統錯誤</h1>
        <p>載入頁面時發生錯誤：</p>
        <pre style="background: #f7fafc; padding: 1rem; border-radius: 8px; text-align: left;">{error_message}</pre>
        <button onclick="location.reload()" class="btn">🔄 重新載入</button>
        <button onclick="location.href='/health'" class="btn" style="background: #38a169;">📊 檢查狀態</button>
    </div>
</body>
</html>"""


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

        # 建立郵件內容
        email_content = create_email_content(email_data)
        logger.info(f"   郵件內容長度: {len(email_content)} 字元")

        # 準備要發送的資料結構
        send_data = create_webhook_payload(email_data, email_content)

        logger.info(f"📤 發送資料到: {CONFIG['WEBHOOK_CONFIG']['send_url']}")

        # 發送資料到指定的 webhook URL
        response = await send_webhook_request(send_data)

        if response.status_code == 200:
            # 更新統計
            update_send_statistics()

            logger.info("✅ 發送成功!")
            return {
                "status": "success",
                "message": f"市場分析報告已成功發送至 {email_data.recipient_email}",
                "sent_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "target_url": CONFIG['WEBHOOK_CONFIG']['send_url'],
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
                detail=f"發送失敗，HTTP 狀態碼: {response.status_code}"
            )

    except requests.exceptions.Timeout:
        logger.error("❌ 請求超時")
        raise HTTPException(status_code=500, detail="請求超時，請檢查網路連接")
    except requests.exceptions.ConnectionError:
        logger.error("❌ 連接錯誤")
        raise HTTPException(
            status_code=500,
            detail=f"無法連接到 {CONFIG['WEBHOOK_CONFIG']['send_url']}，請檢查 URL 是否正確"
        )
    except Exception as e:
        logger.error(f"❌ 發送失敗: {str(e)}")
        raise HTTPException(status_code=500, detail=f"發送失敗: {str(e)}")


async def send_webhook_request(send_data):
    """發送 webhook 請求"""
    return requests.post(
        CONFIG['WEBHOOK_CONFIG']['send_url'],
        json=send_data,
        headers=CONFIG['WEBHOOK_CONFIG']['headers'],
        timeout=CONFIG['WEBHOOK_CONFIG']['timeout']
    )


def create_webhook_payload(email_data: EmailRequest, email_content: str):
    """建立 webhook 負載"""
    return [{
        "headers": {
            "host": "beloved-swine-sensibly.ngrok-free.app",
            "user-agent": f"{CONFIG['SYSTEM_INFO']['name']}/{CONFIG['SYSTEM_INFO']['version']}",
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
            "system_version": CONFIG['SYSTEM_INFO']['version']
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
        "webhookUrl": CONFIG['WEBHOOK_CONFIG']['send_url'],
        "executionMode": "production"
    }]


@app.get("/health")
async def health_check():
    """系統健康檢查"""
    uptime = datetime.now() - system_stats["uptime_start"]

    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "system": CONFIG['SYSTEM_INFO']['name'],
        "version": CONFIG['SYSTEM_INFO']['version'],
        "webhook_url": CONFIG['WEBHOOK_CONFIG']['send_url'],
        "has_data": len(stored_data) > 0,
        "stats": system_stats,
        "uptime": str(uptime).split('.')[0],
        "environment": os.getenv('ENVIRONMENT', 'development'),
        "features": CONFIG['FEATURE_FLAGS']
    }


@app.get("/api/stats")
async def get_system_stats():
    """取得系統統計資料"""
    try:
        return {
            "status": "success",
            "stats": system_stats,
            "has_current_data": len(stored_data) > 0,
            "last_data_time": stored_data.get("received_time") if stored_data else None,
            "system_info": CONFIG['SYSTEM_INFO']
        }
    except Exception as e:
        logger.error(f"❌ 取得統計資料失敗: {str(e)}")
        raise HTTPException(status_code=500, detail=f"取得統計資料失敗: {str(e)}")


@app.get("/api/test-connection")
async def test_webhook_connection():
    """測試 webhook 連接"""
    try:
        logger.info(f"🔍 測試連接到: {CONFIG['WEBHOOK_CONFIG']['send_url']}")

        # 發送測試請求
        test_response = requests.get(
            CONFIG['WEBHOOK_CONFIG']['send_url'],
            timeout=10,
            headers={"User-Agent": f"{CONFIG['SYSTEM_INFO']['name']}/test"}
        )

        logger.info(f"✅ 測試連接成功，狀態碼: {test_response.status_code}")

        return {
            "status": "success",
            "target_url": CONFIG['WEBHOOK_CONFIG']['send_url'],
            "response_code": test_response.status_code,
            "response_time": "< 10s",
            "message": "Webhook 連接測試成功",
            "timestamp": datetime.now().isoformat()
        }
    except requests.exceptions.Timeout:
        logger.warning("⚠️  測試連接超時")
        return {
            "status": "timeout",
            "target_url": CONFIG['WEBHOOK_CONFIG']['send_url'],
            "error": "連接超時",
            "message": "Webhook 連接測試超時，但這不一定表示服務不可用"
        }
    except requests.exceptions.ConnectionError as e:
        logger.error(f"❌ 測試連接失敗: {str(e)}")
        return {
            "status": "error",
            "target_url": CONFIG['WEBHOOK_CONFIG']['send_url'],
            "error": str(e),
            "message": "無法連接到 webhook，請檢查 URL 和網路連接"
        }
    except Exception as e:
        logger.error(f"❌ 測試連接發生未知錯誤: {str(e)}")
        return {
            "status": "error",
            "target_url": CONFIG['WEBHOOK_CONFIG']['send_url'],
            "error": str(e),
            "message": "測試連接失敗"
        }


@app.get("/api/config")
async def get_frontend_config():
    """提供前端配置資料"""
    try:
        return {
            "status": "success",
            "config": {
                "system_info": CONFIG['SYSTEM_INFO'],
                "ui_config": CONFIG['UI_CONFIG'],
                "feature_flags": CONFIG['FEATURE_FLAGS'],
                "sentiment_config": {
                    "labels": CONFIG['SENTIMENT_CONFIG']['labels'],
                    "emojis": CONFIG['SENTIMENT_CONFIG']['emojis']
                }
            }
        }
    except Exception as e:
        logger.error(f"❌ 取得前端配置失敗: {str(e)}")
        raise HTTPException(status_code=500, detail=f"取得配置失敗: {str(e)}")


# 輔助函數
def create_email_content(email_data: EmailRequest) -> str:
    """建立郵件內容"""
    try:
        content_parts = []

        # 自訂開頭內容
        if email_data.custom_content:
            content_parts.append(email_data.custom_content)
            content_parts.append("")

        # 郵件標題
        content_parts.append(CONFIG['EMAIL_TEMPLATES']['report_header'])
        content_parts.append(f"生成時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        content_parts.append("")

        # 情感分析
        if email_data.include_sentiment:
            sentiment_score = stored_data.get("average_sentiment_score", 0)
            sentiment_text = get_sentiment_text(sentiment_score)
            market_emoji = get_market_emoji(sentiment_score)

            content_parts.append(f"📊 市場情緒評分: {sentiment_score:.3f}")
            content_parts.append(f"📈 市場情緒: {sentiment_text} {market_emoji}")
            content_parts.append(f"📅 市場日期: {stored_data.get('market_date', '今日')}")
            content_parts.append("")

        # 市場分析內容
        if email_data.include_message:
            content_parts.append("🏛️ 市場分析詳情:")
            content_parts.append("-" * 40)
            market_content = stored_data.get("message_content", "無分析內容")
            content_parts.append(market_content)
            content_parts.append("-" * 40)
            content_parts.append("")

        # 系統資訊
        content_parts.append(f"🤖 報告系統: {CONFIG['SYSTEM_INFO']['name']} v{CONFIG['SYSTEM_INFO']['version']}")
        content_parts.append(f"⏰ 資料接收時間: {stored_data.get('received_time', '未知')}")
        content_parts.append("")

        content_parts.append(CONFIG['EMAIL_TEMPLATES']['report_footer'])

        return "\\n".join(content_parts)

    except Exception as e:
        logger.error(f"❌ 建立郵件內容失敗: {str(e)}")
        return f"❌ 郵件內容建立失敗: {str(e)}"


def get_sentiment_text(score: float) -> str:
    """根據情感分數返回文字描述"""
    try:
        thresholds = CONFIG['SENTIMENT_CONFIG']['thresholds']
        labels = CONFIG['SENTIMENT_CONFIG']['labels']

        if score > thresholds['very_positive']:
            return labels['very_positive']
        elif score > thresholds['positive']:
            return labels['positive']
        elif score > thresholds['neutral_upper']:
            return labels['neutral_positive']
        elif score > thresholds['neutral_lower']:
            return labels['neutral']
        elif score > thresholds['negative']:
            return labels['neutral_negative']
        else:
            return labels['very_negative']
    except Exception as e:
        logger.error(f"❌ 取得情感文字失敗: {str(e)}")
        return "未知"


def get_market_emoji(score: float) -> str:
    """根據情感分數返回對應的表情符號"""
    try:
        emojis = CONFIG['SENTIMENT_CONFIG']['emojis']
        thresholds = CONFIG['SENTIMENT_CONFIG']['thresholds']

        if score > thresholds['very_positive']:
            return emojis['very_positive']
        elif score > thresholds['positive']:
            return emojis['positive']
        elif score > thresholds['neutral_upper']:
            return emojis['neutral_positive']
        elif score > thresholds['neutral_lower']:
            return emojis['neutral']
        elif score > thresholds['negative']:
            return emojis['neutral_negative']
        else:
            return emojis['very_negative']
    except Exception as e:
        logger.error(f"❌ 取得表情符號失敗: {str(e)}")
        return "📊"


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


def update_send_statistics():
    """更新發送統計"""
    try:
        global system_stats

        system_stats["total_reports"] += 1
        today = datetime.now().date()

        if system_stats["last_reset"] != today:
            system_stats["today_reports"] = 1
            system_stats["last_reset"] = today
        else:
            system_stats["today_reports"] += 1

        logger.info(f"📊 發送統計已更新: 總計 {system_stats['total_reports']}, 今日 {system_stats['today_reports']}")

    except Exception as e:
        logger.error(f"❌ 更新發送統計失敗: {str(e)}")


# 啟動和關閉事件
@app.on_event("startup")
async def startup_event():
    """應用啟動時的初始化"""
    logger.info("🚀 市場分析報告系統啟動中...")
    logger.info(f"📡 目標 Webhook URL: {CONFIG['WEBHOOK_CONFIG']['send_url']}")
    logger.info(f"🌐 伺服器位置: http://{CONFIG['SERVER_CONFIG']['host']}:{CONFIG['SERVER_CONFIG']['port']}")
    logger.info(f"📖 API 文檔: http://{CONFIG['SERVER_CONFIG']['host']}:{CONFIG['SERVER_CONFIG']['port']}/docs")
    logger.info(f"🔧 環境模式: {os.getenv('ENVIRONMENT', 'development')}")
    logger.info(
        f"🎯 功能標誌: {sum(1 for v in CONFIG['FEATURE_FLAGS'].values() if v)}/{len(CONFIG['FEATURE_FLAGS'])} 已啟用")
    logger.info("✅ 系統啟動完成")


@app.on_event("shutdown")
async def shutdown_event():
    """應用關閉時的清理"""
    logger.info("🛑 市場分析報告系統正在關閉...")
    logger.info(f"📊 最終統計: {system_stats}")
    logger.info("👋 系統已安全關閉")


# 錯誤處理
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """HTTP 異常處理器"""
    logger.warning(f"⚠️  HTTP 異常: {exc.status_code} - {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "status": "error",
            "message": exc.detail,
            "status_code": exc.status_code,
            "timestamp": datetime.now().isoformat(),
            "path": str(request.url)
        }
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """全域異常處理器"""
    logger.error(f"❌ 全域異常: {str(exc)}")
    logger.error(f"   請求路徑: {request.url}")

    import traceback
    logger.error(f"   錯誤詳情: {traceback.format_exc()}")

    return JSONResponse(
        status_code=500,
        content={
            "status": "error",
            "message": "系統發生內部錯誤",
            "detail": str(exc) if CONFIG['SERVER_CONFIG'].get('debug', False) else "請聯繫系統管理員",
            "timestamp": datetime.now().isoformat(),
            "path": str(request.url)
        }
    )


# 主程式入口點
def main():
    """主程式函數"""
    print("🚀 啟動市場分析報告系統...")
    print(f"📡 目標 Webhook URL: {CONFIG['WEBHOOK_CONFIG']['send_url']}")
    print(f"🌐 伺服器位置: http://{CONFIG['SERVER_CONFIG']['host']}:{CONFIG['SERVER_CONFIG']['port']}")
    print(f"📖 API 文檔: http://{CONFIG['SERVER_CONFIG']['host']}:{CONFIG['SERVER_CONFIG']['port']}/docs")
    print(f"🔧 環境模式: {os.getenv('ENVIRONMENT', 'development')}")
    print("⚠️  注意: 此系統不使用 Gmail 發送郵件，而是透過 webhook 轉發資料")
    print("-" * 80)

    try:
        uvicorn.run(
            app,
            host=CONFIG['SERVER_CONFIG']['host'],
            port=CONFIG['SERVER_CONFIG']['port'],
            log_level=CONFIG['SERVER_CONFIG']['log_level'],
            reload=CONFIG['SERVER_CONFIG'].get('reload', False),
            access_log=True
        )
    except KeyboardInterrupt:
        print("\n👋 使用者中斷，系統正在安全關閉...")
    except Exception as e:
        print(f"❌ 系統啟動失敗: {str(e)}")
        logger.error(f"系統啟動失敗: {str(e)}")
    finally:
        print("🛑 系統已關閉")


if __name__ == "__main__":
    main()