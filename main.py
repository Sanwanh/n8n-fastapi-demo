#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
市場分析報告系統 - API服務 (優化版)
Market Analysis Report System - Enhanced API Service
"""

import os
import sys
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Optional, Any
import asyncio

# 第三方套件
try:
    from fastapi import FastAPI, Request, HTTPException
    from fastapi.responses import JSONResponse, HTMLResponse
    from fastapi.staticfiles import StaticFiles
    from fastapi.middleware.cors import CORSMiddleware
    from pydantic import BaseModel, EmailStr, validator
    import uvicorn
    import requests
    import yfinance as yf
    import pandas as pd
    import numpy as np
except ImportError as e:
    print(f"❌ 缺少必要的套件: {e}")
    print("請執行: pip install -r requirements.txt")
    sys.exit(1)

# 設定日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 確保目錄存在
Path("logs").mkdir(exist_ok=True)
Path("data").mkdir(exist_ok=True)
Path("frontend/static").mkdir(parents=True, exist_ok=True)


# 載入配置
def load_config():
    return {
        'SERVER_CONFIG': {
            'host': os.getenv('SERVER_HOST', '0.0.0.0'),
            'port': int(os.getenv('SERVER_PORT', 8089)),
            'debug': os.getenv('DEBUG', 'False').lower() == 'true'
        },
        'WEBHOOK_CONFIG': {
            'send_url': os.getenv(
                'WEBHOOK_URL',
                'https://beloved-swine-sensibly.ngrok-free.app/webhook-test/ef5ac185-f41a-4a2d-9a78-33d329184c2'
            ),
            'n8n_webhook_url': 'https://beloved-swine-sensibly.ngrok-free.app/webhook/Webhook%20-%20Preview',
            'timeout': int(os.getenv('WEBHOOK_TIMEOUT', 30))
        },
        'SYSTEM_INFO': {
            'name': 'Market Analysis API',
            'version': '2.1.0',
            'description': '智能市場分析API服務 - 增強版'
        }
    }


CONFIG = load_config()


# 資料模型
class N8NDataExtended(BaseModel):
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


class MailSenderRequest(BaseModel):
    recipient_email: EmailStr
    sender_name: Optional[str] = "市場分析系統"
    subject: str
    priority: Optional[str] = "normal"
    mail_type: Optional[str] = "daily"
    custom_message: Optional[str] = ""
    include_charts: bool = False
    include_recommendations: bool = False
    include_risk_warning: bool = False


# 初始化 FastAPI
app = FastAPI(
    title=CONFIG['SYSTEM_INFO']['name'],
    description=CONFIG['SYSTEM_INFO']['description'],
    version=CONFIG['SYSTEM_INFO']['version'],
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# CORS 設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 掛載靜態檔案
app.mount("/static", StaticFiles(directory="frontend/static"), name="static")


# Web 路由
@app.get("/", response_class=HTMLResponse)
async def home():
    """主頁面 - 顯示市場數據和黃金價格"""
    html_file = Path("frontend") / "index.html"
    if html_file.exists():
        with open(html_file, 'r', encoding='utf-8') as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse(content="<h1>首頁檔案不存在</h1>", status_code=404)


@app.get("/mail", response_class=HTMLResponse)
async def mail_page():
    """郵件發送頁面"""
    html_file = Path("frontend") / "mail.html"
    if html_file.exists():
        with open(html_file, 'r', encoding='utf-8') as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse(content="<h1>郵件頁面檔案不存在</h1>", status_code=404)


# 全域變數
stored_data = {}
system_stats = {
    "total_reports": 0,
    "today_reports": 0,
    "last_reset": datetime.now().date(),
    "uptime_start": datetime.now()
}


# API 路由
@app.post("/api/n8n-data")
async def receive_n8n_data(request: Request):
    """接收來自 N8N 的市場分析資料"""
    try:
        global stored_data, system_stats

        raw_data = await request.json()
        logger.info(f"收到 N8N 資料: {json.dumps(raw_data, ensure_ascii=False)[:200]}...")

        if isinstance(raw_data, list) and len(raw_data) > 0:
            market_data = raw_data[0]
        elif isinstance(raw_data, dict):
            market_data = raw_data
        else:
            raise HTTPException(status_code=400, detail="無效的資料格式")

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

        system_stats["total_reports"] += 1
        system_stats["today_reports"] += 1

        logger.info(f"✅ 成功儲存 N8N 資料")

        return {
            "status": "success",
            "message": "市場分析資料已接收並儲存",
            "data": stored_data
        }

    except Exception as e:
        logger.error(f"❌ 接收 N8N 資料失敗: {str(e)}")
        raise HTTPException(status_code=500, detail=f"接收資料失敗: {str(e)}")


@app.get("/api/current-data")
async def get_current_data():
    """取得目前儲存的市場分析資料"""
    return {
        "status": "success",
        "data": stored_data,
        "stats": system_stats,
        "timestamp": datetime.now().isoformat()
    }


@app.get("/api/gold-price")
async def get_gold_price(period: str = "1d", interval: str = "1h"):
    """取得黃金期貨價格 - 增強版支援多時間範圍"""
    try:
        # 驗證參數
        valid_periods = ["1d", "5d", "1mo", "3mo", "6mo", "1y"]
        valid_intervals = ["1m", "5m", "15m", "30m", "1h", "1d"]

        if period not in valid_periods:
            period = "1d"
        if interval not in valid_intervals:
            interval = "1h"

        logger.info(f"🔍 正在獲取黃金期貨數據 - 期間: {period}, 間隔: {interval}")

        # 使用 yfinance 獲取黃金期貨數據
        gold_ticker = yf.Ticker("GC=F")

        # 獲取歷史數據
        hist = gold_ticker.history(period=period, interval=interval)

        if hist.empty:
            logger.error("❌ yfinance 返回空數據")
            raise HTTPException(status_code=500, detail="無法獲取黃金價格數據")

        logger.info(f"✅ 成功獲取 {len(hist)} 個數據點")

        # 嘗試獲取即時數據
        try:
            recent_data = gold_ticker.history(period="2d", interval="1m")
            if not recent_data.empty:
                today = datetime.now().date()
                today_data = recent_data[recent_data.index.date >= today]

                if not today_data.empty:
                    # 更新最新價格
                    latest_price = float(today_data['Close'].iloc[-1])
                    latest_time = today_data.index[-1]

                    # 更新歷史數據中的最後一天
                    if len(hist) > 0:
                        last_date = hist.index[-1].date()
                        if last_date == today:
                            hist.iloc[-1, hist.columns.get_loc('Close')] = latest_price
                            hist.iloc[-1, hist.columns.get_loc('High')] = max(hist.iloc[-1]['High'], latest_price)
                            hist.iloc[-1, hist.columns.get_loc('Low')] = min(hist.iloc[-1]['Low'], latest_price)

                    logger.info(f"📊 已更新即時價格: ${latest_price:.2f}")

        except Exception as e:
            logger.warning(f"⚠️ 無法獲取即時數據: {str(e)}")

        # 計算價格變化
        current_price = float(hist['Close'].iloc[-1])
        previous_close = float(hist['Close'].iloc[-2]) if len(hist) > 1 else current_price
        change = current_price - previous_close
        change_percent = (change / previous_close) * 100 if previous_close != 0 else 0

        # 計算統計數據
        high_24h = float(hist['High'].max())
        low_24h = float(hist['Low'].min())
        volume_24h = int(hist['Volume'].sum()) if hist['Volume'].sum() > 0 else 0

        # 準備圖表數據
        chart_data = []
        for idx, row in hist.iterrows():
            chart_data.append({
                "time": idx.isoformat(),
                "price": float(row['Close']),
                "high": float(row['High']),
                "low": float(row['Low']),
                "open": float(row['Open']),
                "volume": int(row['Volume']) if row['Volume'] > 0 else 0
            })

        # 計算技術指標
        ma_20_series = hist['Close'].rolling(window=min(20, len(hist))).mean()
        ma_50_series = hist['Close'].rolling(window=min(50, len(hist))).mean()

        technical_indicators = {
            "ma_20": float(ma_20_series.iloc[-1]) if not ma_20_series.empty and not pd.isna(
                ma_20_series.iloc[-1]) else None,
            "ma_50": float(ma_50_series.iloc[-1]) if not ma_50_series.empty and not pd.isna(
                ma_50_series.iloc[-1]) else None,
            "rsi": calculate_rsi(hist['Close'].values) if len(hist) >= 14 else None
        }

        # 判斷市場狀態
        current_hour = datetime.now().hour
        market_status = "open" if 18 <= current_hour or current_hour <= 17 else "closed"

        # 獲取市場資訊
        try:
            info = gold_ticker.info
            market_name = info.get('longName', 'Gold Futures')
        except:
            market_name = 'Gold Futures'

        logger.info(f"💰 黃金價格: ${current_price:.2f} (變化: {change:+.2f}, {change_percent:+.2f}%)")

        return {
            "status": "success",
            "data": {
                "symbol": "GC=F",
                "name": market_name,
                "current_price": current_price,
                "change": change,
                "change_percent": change_percent,
                "high_24h": high_24h,
                "low_24h": low_24h,
                "volume_24h": volume_24h,
                "currency": "USD",
                "unit": "per ounce",
                "last_updated": datetime.now().isoformat(),
                "chart_data": chart_data,
                "market_status": market_status,
                "technical_indicators": technical_indicators,
                "period": period,
                "interval": interval,
                "data_points": len(chart_data)
            },
            "system_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "next_update": (datetime.now() + timedelta(minutes=1)).strftime("%Y-%m-%d %H:%M:%S"),
            "data_source": "Yahoo Finance API"
        }

    except Exception as e:
        logger.error(f"❌ 獲取黃金價格失敗: {str(e)}")
        raise HTTPException(status_code=500, detail=f"獲取黃金價格失敗: {str(e)}")


def calculate_rsi(prices, periods=14):
    """計算 RSI 技術指標"""
    try:
        if len(prices) < periods + 1:
            return None

        # 轉換為 numpy 數組並確保是浮點數
        prices = np.array(prices, dtype=float)
        deltas = np.diff(prices)

        if len(deltas) < periods:
            return None

        up_moves = np.where(deltas > 0, deltas, 0)
        down_moves = np.where(deltas < 0, -deltas, 0)

        # 計算初始平均值
        avg_up = np.mean(up_moves[:periods])
        avg_down = np.mean(down_moves[:periods])

        if avg_down == 0:
            return 100

        rs = avg_up / avg_down
        rsi = 100 - (100 / (1 + rs))
        return round(float(rsi), 2)
    except Exception as e:
        logger.warning(f"RSI 計算錯誤: {e}")
        return None


@app.post("/api/send-mail-to-n8n")
async def send_mail_to_n8n(mail_data: MailSenderRequest):
    """發送郵件數據到 N8N webhook"""
    try:
        if not stored_data:
            raise HTTPException(status_code=400, detail="沒有可用的市場分析資料")

        # 構建發送到 N8N 的數據結構
        send_data = {
            **stored_data,
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
            "system_info": {
                "send_timestamp": datetime.now().isoformat(),
                "system_version": CONFIG['SYSTEM_INFO']['version'],
                "source": "mail-sender-page"
            },
            "sentiment_analysis": {
                "score": stored_data.get("average_sentiment_score", 0),
                "text": get_sentiment_text(stored_data.get("average_sentiment_score", 0)),
                "emoji": get_market_emoji(stored_data.get("average_sentiment_score", 0))
            }
        }

        response = requests.post(
            CONFIG['WEBHOOK_CONFIG']['n8n_webhook_url'],
            json=send_data,
            headers={'Content-Type': 'application/json'},
            timeout=CONFIG['WEBHOOK_CONFIG']['timeout']
        )

        if response.status_code == 200:
            logger.info("✅ 郵件數據已成功發送到 N8N")
            return {
                "status": "success",
                "message": f"郵件數據已成功發送到 N8N",
                "sent_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "recipient": str(mail_data.recipient_email)
            }
        else:
            raise HTTPException(status_code=500, detail=f"N8N webhook 回應錯誤: {response.status_code}")

    except requests.exceptions.Timeout:
        raise HTTPException(status_code=500, detail="請求超時")
    except requests.exceptions.ConnectionError:
        raise HTTPException(status_code=500, detail="無法連接到 N8N webhook")
    except Exception as e:
        logger.error(f"❌ 發送郵件到 N8N 失敗: {str(e)}")
        raise HTTPException(status_code=500, detail=f"發送失敗: {str(e)}")


@app.get("/api/test-n8n-connection")
async def test_n8n_connection():
    """測試 N8N 連接"""
    try:
        response = requests.get(
            CONFIG['WEBHOOK_CONFIG']['n8n_webhook_url'],
            timeout=10
        )
        return {
            "status": "success",
            "message": "N8N 連接正常",
            "status_code": response.status_code,
            "url": CONFIG['WEBHOOK_CONFIG']['n8n_webhook_url']
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"N8N 連接失敗: {str(e)}",
            "url": CONFIG['WEBHOOK_CONFIG']['n8n_webhook_url']
        }


@app.get("/health")
async def health_check():
    """系統健康檢查"""
    uptime = datetime.now() - system_stats["uptime_start"]

    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "system": CONFIG['SYSTEM_INFO']['name'],
        "version": CONFIG['SYSTEM_INFO']['version'],
        "has_data": len(stored_data) > 0,
        "uptime": str(uptime).split('.')[0],
        "environment": os.getenv('ENVIRONMENT', 'development'),
        "features": {
            "gold_price_api": True,
            "market_analysis": True,
            "mail_sender": True,
            "real_time_updates": True
        }
    }


# 輔助函數
def get_sentiment_text(score: float) -> str:
    """根據情感分數返回文字描述"""
    if score > 0.6:
        return "極度樂觀"
    elif score > 0.2:
        return "樂觀"
    elif score > 0.1:
        return "中性偏樂觀"
    elif score > -0.1:
        return "中性"
    elif score > -0.2:
        return "中性偏悲觀"
    elif score > -0.6:
        return "悲觀"
    else:
        return "極度悲觀"


def get_market_emoji(score: float) -> str:
    """根據情感分數返回表情符號"""
    if score > 0.6:
        return "🚀📈💚"
    elif score > 0.2:
        return "📈🟢😊"
    elif score > 0.1:
        return "📊🟡😐"
    elif score > -0.1:
        return "➡️⚪😑"
    elif score > -0.2:
        return "📊🟡😐"
    elif score > -0.6:
        return "📉🔴😟"
    else:
        return "💥📉😱"


# 啟動事件
@app.on_event("startup")
async def startup_event():
    logger.info("🚀 市場分析系統啟動 - 增強版")
    logger.info(f"📡 N8N Webhook: {CONFIG['WEBHOOK_CONFIG']['n8n_webhook_url']}")
    logger.info(f"🌐 主網站: http://{CONFIG['SERVER_CONFIG']['host']}:{CONFIG['SERVER_CONFIG']['port']}")
    logger.info(f"📧 郵件頁面: http://{CONFIG['SERVER_CONFIG']['host']}:{CONFIG['SERVER_CONFIG']['port']}/mail")
    logger.info(f"📖 API文檔: http://{CONFIG['SERVER_CONFIG']['host']}:{CONFIG['SERVER_CONFIG']['port']}/api/docs")


# 錯誤處理
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "status": "error",
            "message": exc.detail,
            "timestamp": datetime.now().isoformat()
        }
    )


def main():
    print("🚀 啟動市場分析系統 - 增強版...")
    print(f"🌐 主網站: http://{CONFIG['SERVER_CONFIG']['host']}:{CONFIG['SERVER_CONFIG']['port']}")
    print(f"📧 郵件頁面: http://{CONFIG['SERVER_CONFIG']['host']}:{CONFIG['SERVER_CONFIG']['port']}/mail")
    print(f"📖 API文檔: http://{CONFIG['SERVER_CONFIG']['host']}:{CONFIG['SERVER_CONFIG']['port']}/api/docs")

    uvicorn.run(
        app,
        host=CONFIG['SERVER_CONFIG']['host'],
        port=CONFIG['SERVER_CONFIG']['port'],
        log_level="info",
        reload=CONFIG['SERVER_CONFIG'].get('debug', False)
    )


if __name__ == "__main__":
    main()