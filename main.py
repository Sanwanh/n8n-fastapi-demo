#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
市場分析報告系統 - 主程式 (完整版本)
Market Analysis Report System - Main Application (Complete Version)

新增郵件發送頁面和功能
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
            'n8n_webhook_url': 'https://beloved-swine-sensibly.ngrok-free.app/webhook/Webhook%20-%20Preview',
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
            'version': '1.3.0',
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
            'enable_sentiment_analysis': True,
            'enable_mail_sender_page': True
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


class N8NDataExtended(BaseModel):
    """擴展的 N8N 資料模型，包含更多字段"""
    average_sentiment_score: float
    message_content: str
    market_date: Optional[str] = None
    confidence_level: Optional[str] = None
    trend_direction: Optional[str] = None
    risk_assessment: Optional[str] = None

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


class MailSenderRequest(BaseModel):
    """郵件發送頁面請求模型"""
    recipient_email: EmailStr
    sender_name: Optional[str] = "市場分析系統"
    subject: str
    priority: Optional[str] = "normal"
    mail_type: Optional[str] = "daily"
    custom_message: Optional[str] = ""
    include_charts: bool = False
    include_recommendations: bool = False
    include_risk_warning: bool = False


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


@app.get("/mail", response_class=HTMLResponse)
async def mail_sender_page():
    """提供郵件發送頁面"""
    try:
        mail_html_file = Path("frontend") / "mail.html"

        if mail_html_file.exists():
            with open(mail_html_file, 'r', encoding='utf-8') as f:
                content = f.read()
            return HTMLResponse(content=content)
        else:
            # 如果檔案不存在，建立一個基本的郵件發送頁面
            mail_html = get_default_mail_html()
            mail_html_file.parent.mkdir(parents=True, exist_ok=True)
            with open(mail_html_file, 'w', encoding='utf-8') as f:
                f.write(mail_html)
            logger.info("📝 已建立郵件發送頁面")
            return HTMLResponse(content=mail_html)

    except Exception as e:
        logger.error(f"❌ 載入郵件頁面失敗: {str(e)}")
        return HTMLResponse(content=get_error_html(str(e)), status_code=500)


# API 路由處理
@app.post("/api/n8n-data")
async def receive_n8n_data(request: Request):
    """接收來自 N8N 的市場分析資料（更新版本）"""
    try:
        global stored_data, system_stats

        # 獲取原始 JSON 數據
        raw_data = await request.json()
        logger.info(f"🔄 收到 N8N 原始資料: {json.dumps(raw_data, indent=2, ensure_ascii=False)}")

        # 處理不同格式的數據
        if isinstance(raw_data, list) and len(raw_data) > 0:
            market_data = raw_data[0]
        elif isinstance(raw_data, dict):
            market_data = raw_data
        else:
            raise HTTPException(status_code=400, detail="無效的資料格式")

        # 儲存資料
        stored_data = {
            "average_sentiment_score": market_data.get("average_sentiment_score", 0),
            "message_content": market_data.get("message_content", ""),
            "market_date": market_data.get("market_date", datetime.now().strftime("%Y年%m月%d日")),
            "confidence_level": market_data.get("confidence_level", "未知"),
            "trend_direction": market_data.get("trend_direction", "未知"),
            "risk_assessment": market_data.get("risk_assessment", "未知"),
            "received_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "raw_data": market_data
        }

        # 更新統計
        update_system_stats(market_data.get("average_sentiment_score", 0))

        logger.info(f"✅ 成功接收並儲存 N8N 資料:")
        logger.info(f"   情緒評分: {market_data.get('average_sentiment_score')}")
        logger.info(f"   內容長度: {len(market_data.get('message_content', ''))}")
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
    """發送市場分析報告到指定的 webhook（舊版 API，保持向後相容）"""
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


@app.post("/api/send-mail-to-n8n")
async def send_mail_to_n8n(mail_data: MailSenderRequest):
    """新的郵件發送 API - 將市場資料和郵件資訊發送到 N8N webhook"""
    try:
        logger.info(f"📧 開始新版郵件發送程序...")
        logger.info(f"   收件人: {mail_data.recipient_email}")
        logger.info(f"   主題: {mail_data.subject}")
        logger.info(f"   優先級: {mail_data.priority}")

        # 檢查是否有市場資料
        if not stored_data:
            logger.warning("❌ 沒有市場資料")
            raise HTTPException(
                status_code=400,
                detail="沒有可用的市場分析資料，請先從 N8N 傳送資料"
            )

        # 構建要發送到 N8N 的完整數據結構
        n8n_payload = {
            # 原始市場數據
            "average_sentiment_score": stored_data.get("average_sentiment_score"),
            "message_content": stored_data.get("message_content"),
            "market_date": stored_data.get("market_date"),
            "confidence_level": stored_data.get("confidence_level"),
            "trend_direction": stored_data.get("trend_direction"),
            "risk_assessment": stored_data.get("risk_assessment"),
            "received_time": stored_data.get("received_time"),

            # 郵件配置資訊
            "mail_config": {
                "recipient_email": str(mail_data.recipient_email),
                "sender_name": mail_data.sender_name,
                "subject": mail_data.subject,
                "priority": mail_data.priority,
                "mail_type": mail_data.mail_type,
                "custom_message": mail_data.custom_message,
                "include_charts": mail_data.include_charts,
                "include_recommendations": mail_data.include_recommendations,
                "include_risk_warning": mail_data.include_risk_warning
            },

            # 系統資訊
            "system_info": {
                "send_timestamp": datetime.now().isoformat(),
                "system_version": CONFIG['SYSTEM_INFO']['version'],
                "source": "mail-sender-page"
            },

            # 情感分析資訊
            "sentiment_analysis": {
                "score": stored_data.get("average_sentiment_score"),
                "text": get_sentiment_text(stored_data.get("average_sentiment_score", 0)),
                "emoji": get_market_emoji(stored_data.get("average_sentiment_score", 0))
            }
        }

        logger.info(f"📤 發送資料到 N8N: {CONFIG['WEBHOOK_CONFIG']['n8n_webhook_url']}")
        logger.info(f"📊 資料大小: {len(json.dumps(n8n_payload))} bytes")

        # 發送到 N8N webhook
        response = requests.post(
            CONFIG['WEBHOOK_CONFIG']['n8n_webhook_url'],
            json=n8n_payload,
            headers={
                'Content-Type': 'application/json',
                'Accept': 'application/json',
                'User-Agent': f"{CONFIG['SYSTEM_INFO']['name']}/{CONFIG['SYSTEM_INFO']['version']}"
            },
            timeout=CONFIG['WEBHOOK_CONFIG']['timeout']
        )

        logger.info(f"📨 N8N 回應狀態: {response.status_code}")

        if response.status_code == 200:
            # 更新統計
            update_send_statistics()

            logger.info("✅ 郵件資料成功發送到 N8N!")
            return {
                "status": "success",
                "message": f"郵件資料已成功發送到 N8N，將發送到 {mail_data.recipient_email}",
                "sent_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "target_url": CONFIG['WEBHOOK_CONFIG']['n8n_webhook_url'],
                "recipient": str(mail_data.recipient_email),
                "subject": mail_data.subject,
                "priority": mail_data.priority,
                "stats": system_stats,
                "payload_size": len(json.dumps(n8n_payload))
            }
        else:
            error_text = response.text if response.text else "無回應內容"
            logger.error(f"❌ N8N 回應錯誤: {response.status_code} - {error_text}")
            raise HTTPException(
                status_code=500,
                detail=f"N8N webhook 回應錯誤: {response.status_code}"
            )

    except requests.exceptions.Timeout:
        logger.error("❌ N8N webhook 請求超時")
        raise HTTPException(status_code=500, detail="N8N webhook 請求超時，請檢查網路連接")
    except requests.exceptions.ConnectionError:
        logger.error("❌ 無法連接到 N8N webhook")
        raise HTTPException(
            status_code=500,
            detail=f"無法連接到 N8N webhook: {CONFIG['WEBHOOK_CONFIG']['n8n_webhook_url']}"
        )
    except Exception as e:
        logger.error(f"❌ 發送郵件資料到 N8N 失敗: {str(e)}")
        raise HTTPException(status_code=500, detail=f"發送失敗: {str(e)}")


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
        "n8n_webhook_url": CONFIG['WEBHOOK_CONFIG']['n8n_webhook_url'],
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


@app.get("/api/test-n8n-connection")
async def test_n8n_connection():
    """測試 N8N webhook 連接"""
    try:
        logger.info(f"🔍 測試 N8N 連接到: {CONFIG['WEBHOOK_CONFIG']['n8n_webhook_url']}")

        # 發送測試資料
        test_data = {
            "test": True,
            "message": "系統連接測試",
            "timestamp": datetime.now().isoformat(),
            "source": "connection-test"
        }

        test_response = requests.post(
            CONFIG['WEBHOOK_CONFIG']['n8n_webhook_url'],
            json=test_data,
            timeout=10,
            headers={
                'Content-Type': 'application/json',
                'User-Agent': f"{CONFIG['SYSTEM_INFO']['name']}/test"
            }
        )

        logger.info(f"✅ N8N 測試連接成功，狀態碼: {test_response.status_code}")

        return {
            "status": "success",
            "target_url": CONFIG['WEBHOOK_CONFIG']['n8n_webhook_url'],
            "response_code": test_response.status_code,
            "response_time": "< 10s",
            "message": "N8N Webhook 連接測試成功",
            "timestamp": datetime.now().isoformat()
        }
    except requests.exceptions.Timeout:
        logger.warning("⚠️  N8N 測試連接超時")
        return {
            "status": "timeout",
            "target_url": CONFIG['WEBHOOK_CONFIG']['n8n_webhook_url'],
            "error": "連接超時",
            "message": "N8N Webhook 連接測試超時"
        }
    except Exception as e:
        logger.error(f"❌ N8N 測試連接失敗: {str(e)}")
        return {
            "status": "error",
            "target_url": CONFIG['WEBHOOK_CONFIG']['n8n_webhook_url'],
            "error": str(e),
            "message": "N8N Webhook 連接測試失敗"
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
            text-decoration: none;
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
            margin: 0.5rem;
        }}

        .btn:hover {{ 
            background: #1d4ed8; 
            transform: translateY(-2px);
        }}

        .btn.success {{
            background: var(--success);
        }}

        .navigation {{
            display: flex;
            gap: 1rem;
            justify-content: center;
            margin-bottom: 2rem;
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

        <div class="navigation">
            <a href="/" class="btn">
                🏠 首頁
            </a>
            <a href="/mail" class="btn success">
                📧 郵件發送
            </a>
            <a href="/docs" class="btn">
                📚 API 文檔
            </a>
        </div>

        <div class="card">
            <h2>📊 系統狀態</h2>
            <div id="status" style="padding: 1rem; border-radius: 8px; margin: 1rem 0; background: rgba(245, 158, 11, 0.2);">
                🔄 正在檢查系統狀態...
            </div>
            <div id="data-info"></div>
        </div>

        <div class="card">
            <h2>🛠️ 系統功能</h2>
            <ul style="list-style: none; padding: 0;">
                <li style="padding: 0.5rem 0; border-bottom: 1px solid rgba(255,255,255,0.1);">
                    📡 接收 N8N 市場分析數據
                </li>
                <li style="padding: 0.5rem 0; border-bottom: 1px solid rgba(255,255,255,0.1);">
                    📈 即時情感分析顯示
                </li>
                <li style="padding: 0.5rem 0; border-bottom: 1px solid rgba(255,255,255,0.1);">
                    📧 智能郵件發送系統
                </li>
                <li style="padding: 0.5rem 0; border-bottom: 1px solid rgba(255,255,255,0.1);">
                    🔄 Webhook 數據轉發
                </li>
                <li style="padding: 0.5rem 0;">
                    📊 系統健康監控
                </li>
            </ul>
        </div>

        <div class="card">
            <h2>🚀 快速開始</h2>
            <p style="margin-bottom: 1rem;">選擇您需要的功能：</p>
            <div style="display: flex; gap: 1rem; flex-wrap: wrap;">
                <a href="/mail" class="btn success">
                    📧 發送市場報告
                </a>
                <a href="/api/current-data" class="btn">
                    📊 查看當前數據
                </a>
                <a href="/health" class="btn">
                    🔍 系統健康檢查
                </a>
            </div>
        </div>
    </div>

    <script>
        async function checkStatus() {{
            try {{
                const response = await fetch('/health');
                const data = await response.json();

                document.getElementById('status').style.background = 'rgba(16, 185, 129, 0.2)';
                document.getElementById('status').innerHTML = 
                    '✅ 系統運行正常<br>時間: ' + data.timestamp + '<br>版本: ' + data.version;

                const dataResponse = await fetch('/api/current-data');
                const dataResult = await dataResponse.json();

                if (dataResult.data && Object.keys(dataResult.data).length > 0) {{
                    document.getElementById('data-info').innerHTML = 
                        '<h3 style="color: var(--success); margin-top: 1rem;">📈 當前市場資料</h3>' +
                        '<p>情感分數: <strong>' + dataResult.data.average_sentiment_score + '</strong></p>' +
                        '<p>接收時間: ' + dataResult.data.received_time + '</p>' +
                        '<p style="margin-top: 1rem;"><a href="/mail" class="btn success">📧 立即發送報告</a></p>';
                }} else {{
                    document.getElementById('data-info').innerHTML = 
                        '<h3 style="color: var(--text-muted); margin-top: 1rem;">⏳ 等待市場資料</h3>' +
                        '<p>請確認 N8N 工作流程已正確運行</p>';
                }}

            }} catch (error) {{
                document.getElementById('status').style.background = 'rgba(239, 68, 68, 0.2)';
                document.getElementById('status').innerHTML = '❌ 系統連接失敗: ' + error.message;
            }}
        }}

        checkStatus();
        setInterval(checkStatus, 30000);
    </script>
</body>
</html>"""


def get_default_mail_html():
    """返回預設的郵件發送頁面 HTML"""
    return """<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>市場分析郵件發送</title>
    <style>
        /* 基本樣式，實際應該使用外部 CSS 檔案 */
        body { font-family: Arial, sans-serif; margin: 2rem; background: #f5f5f5; }
        .container { max-width: 800px; margin: 0 auto; }
        .card { background: white; padding: 2rem; margin: 1rem 0; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .btn { background: #2563eb; color: white; padding: 1rem 2rem; border: none; border-radius: 8px; cursor: pointer; }
        input, textarea, select { width: 100%; padding: 0.75rem; margin: 0.5rem 0; border: 1px solid #ddd; border-radius: 5px; }
        .form-group { margin: 1rem 0; }
        label { display: block; margin-bottom: 0.5rem; font-weight: bold; }
    </style>
</head>
<body>
    <div class="container">
        <div class="card">
            <h1>📧 市場分析郵件發送</h1>
            <p><a href="/">← 返回首頁</a></p>

            <div id="market-data">
                <h3>📊 當前市場數據</h3>
                <div id="data-display">載入中...</div>
            </div>
        </div>

        <div class="card">
            <h2>郵件設定</h2>
            <form id="mail-form">
                <div class="form-group">
                    <label>收件人郵件地址:</label>
                    <input type="email" id="recipient" required>
                </div>
                <div class="form-group">
                    <label>郵件主旨:</label>
                    <input type="text" id="subject" value="市場分析報告">
                </div>
                <div class="form-group">
                    <label>自訂訊息 (選填):</label>
                    <textarea id="custom_message" rows="4"></textarea>
                </div>
                <button type="submit" class="btn">發送郵件</button>
            </form>
        </div>
    </div>

    <script>
        // 載入市場數據
        fetch('/api/current-data')
            .then(response => response.json())
            .then(data => {
                if (data.data && Object.keys(data.data).length > 0) {
                    document.getElementById('data-display').innerHTML = 
                        '<p>情感分數: ' + data.data.average_sentiment_score + '</p>' +
                        '<p>接收時間: ' + data.data.received_time + '</p>';
                } else {
                    document.getElementById('data-display').innerHTML = '等待市場資料...';
                }
            });

        // 表單提交處理
        document.getElementById('mail-form').addEventListener('submit', async (e) => {
            e.preventDefault();

            const formData = {
                recipient_email: document.getElementById('recipient').value,
                subject: document.getElementById('subject').value,
                custom_message: document.getElementById('custom_message').value
            };

            try {
                const response = await fetch('/api/send-mail-to-n8n', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(formData)
                });

                const result = await response.json();

                if (response.ok) {
                    alert('✅ ' + result.message);
                } else {
                    alert('❌ ' + result.detail);
                }
            } catch (error) {
                alert('❌ 發送失敗: ' + error.message);
            }
        });
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
            margin: 0.5rem;
            text-decoration: none;
            display: inline-block;
        }}
    </style>
</head>
<body>
    <div class="error-container">
        <h1 style="color: #e53e3e;">❌ 系統錯誤</h1>
        <p>載入頁面時發生錯誤：</p>
        <pre style="background: #f7fafc; padding: 1rem; border-radius: 8px; text-align: left;">{error_message}</pre>
        <a href="/" class="btn">🏠 返回首頁</a>
        <button onclick="location.reload()" class="btn">🔄 重新載入</button>
        <a href="/health" class="btn" style="background: #38a169;">📊 檢查狀態</a>
    </div>
</body>
</html>"""


# 啟動和關閉事件
@app.on_event("startup")
async def startup_event():
    """應用啟動時的初始化"""
    logger.info("🚀 市場分析報告系統啟動中...")
    logger.info(f"📡 目標 Webhook URL: {CONFIG['WEBHOOK_CONFIG']['send_url']}")
    logger.info(f"📧 N8N Webhook URL: {CONFIG['WEBHOOK_CONFIG']['n8n_webhook_url']}")
    logger.info(f"🌐 伺服器位置: http://{CONFIG['SERVER_CONFIG']['host']}:{CONFIG['SERVER_CONFIG']['port']}")
    logger.info(f"📖 API 文檔: http://{CONFIG['SERVER_CONFIG']['host']}:{CONFIG['SERVER_CONFIG']['port']}/docs")
    logger.info(f"📧 郵件發送頁面: http://{CONFIG['SERVER_CONFIG']['host']}:{CONFIG['SERVER_CONFIG']['port']}/mail")
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
    print(f"📧 N8N Webhook URL: {CONFIG['WEBHOOK_CONFIG']['n8n_webhook_url']}")
    print(f"🌐 伺服器位置: http://{CONFIG['SERVER_CONFIG']['host']}:{CONFIG['SERVER_CONFIG']['port']}")
    print(f"📖 API 文檔: http://{CONFIG['SERVER_CONFIG']['host']}:{CONFIG['SERVER_CONFIG']['port']}/docs")
    print(f"📧 郵件發送頁面: http://{CONFIG['SERVER_CONFIG']['host']}:{CONFIG['SERVER_CONFIG']['port']}/mail")
    print(f"🔧 環境模式: {os.getenv('ENVIRONMENT', 'development')}")
    print("⚠️  注意: 此系統不使用 Gmail 發送郵件，而是透過 N8N webhook 轉發資料")
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