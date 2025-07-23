#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
市場分析報告系統 - API服務 (修正版)
Market Analysis Report System - Fixed API Service
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
            'version': '2.1.1',
            'description': '智能市場分析API服務 - 修正版'
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
async def get_gold_price(period: str = "1y", interval: str = "1d"):
    """取得黃金期貨價格 - 整合你的優秀代碼邏輯"""
    try:
        # 驗證參數
        valid_periods = ["1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y"]
        valid_intervals = ["1m", "5m", "15m", "30m", "1h", "1d"]

        if period not in valid_periods:
            logger.warning(f"無效的時間期間: {period}，使用預設值")
            period = "1y"

        if interval not in valid_intervals:
            logger.warning(f"無效的時間間隔: {interval}，使用預設值")
            interval = "1d"

        logger.info(f"🔍 正在獲取黃金期貨數據 - 期間: {period}, 間隔: {interval}")

        # 使用你的代碼邏輯獲取黃金期貨數據
        try:
            hist_data, info, current_price = await get_gold_futures_data_enhanced(period, interval)

            if hist_data is None or hist_data.empty:
                logger.warning("主要數據源無數據，使用備選方案...")
                return create_mock_gold_data(period)

        except Exception as e:
            logger.error(f"yfinance 數據獲取失敗: {str(e)}")
            return create_mock_gold_data(period)

        logger.info(f"✅ 成功獲取 {len(hist_data)} 個數據點")

        # 使用你的統計計算邏輯
        stats = calculate_gold_statistics(hist_data)

        if not stats:
            logger.warning("統計計算失敗，使用備選數據")
            return create_mock_gold_data(period)

        # 準備圖表數據 - 使用完整的數據結構
        chart_data = []
        for idx, row in hist_data.iterrows():
            try:
                data_point = {
                    "time": idx.isoformat(),
                    "price": float(row['Close']) if not pd.isna(row['Close']) else stats['current_price'],
                    "high": float(row['High']) if not pd.isna(row['High']) else stats['current_price'],
                    "low": float(row['Low']) if not pd.isna(row['Low']) else stats['current_price'],
                    "open": float(row['Open']) if not pd.isna(row['Open']) else stats['current_price'],
                    "volume": int(row['Volume']) if not pd.isna(row['Volume']) and row['Volume'] > 0 else 0
                }
                chart_data.append(data_point)
            except Exception as point_error:
                logger.warning(f"處理數據點時出錯: {point_error}")
                continue

        # 計算技術指標 - 使用更穩健的方法
        technical_indicators = calculate_technical_indicators_enhanced(hist_data)

        # 判斷市場狀態 - 改進邏輯
        market_status = determine_market_status()

        # 獲取市場資訊 - 整合你的 info 邏輯
        market_name = get_market_name(info)

        logger.info(
            f"💰 黃金價格: ${stats['current_price']:.2f} (變化: {stats['price_change']:+.2f}, {stats['price_change_pct']:+.2f}%)")

        return {
            "status": "success",
            "data": {
                "symbol": "GC=F",
                "name": market_name,
                "current_price": round(stats['current_price'], 2),
                "change": round(stats['price_change'], 2),
                "change_percent": round(stats['price_change_pct'], 2),
                "high_24h": round(stats['max_price'], 2),
                "low_24h": round(stats['min_price'], 2),
                "avg_price": round(stats['avg_price'], 2),  # 你的代碼特有
                "volatility": round(stats['volatility'], 2),  # 你的代碼特有
                "volume_24h": int(hist_data['Volume'].sum()) if not hist_data['Volume'].isna().all() else 0,
                "currency": "USD",
                "unit": "per ounce",
                "last_updated": stats['latest_date'].isoformat(),
                "chart_data": chart_data,
                "market_status": market_status,
                "technical_indicators": technical_indicators,
                "period": period,
                "interval": interval,
                "data_points": len(chart_data),
                "trading_days": len(hist_data),  # 額外統計
                "data_source_info": {
                    "primary": "Yahoo Finance",
                    "realtime_updated": len(chart_data) > 0 and
                                        chart_data[-1]['time'].split('T')[0] == datetime.now().strftime('%Y-%m-%d')
                }
            },
            "system_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "next_update": (datetime.now() + timedelta(minutes=5)).strftime("%Y-%m-%d %H:%M:%S"),
            "data_source": "Yahoo Finance API (Enhanced)"
        }

    except Exception as e:
        logger.error(f"❌ 獲取黃金價格失敗: {str(e)}")
        return create_mock_gold_data(period)


async def get_gold_futures_data_enhanced(period: str, interval: str):
    """
    整合你的優秀黃金期貨數據獲取邏輯
    """
    try:
        # 計算時間範圍 - 使用你的邏輯
        period_days_map = {
            '1d': 1, '5d': 5, '1mo': 30, '3mo': 90,
            '6mo': 180, '1y': 365, '2y': 730, '5y': 1825
        }
        period_days = period_days_map.get(period, 365)

        end_date = datetime.now()
        start_date = end_date - timedelta(days=period_days)

        logger.info(f"正在獲取黃金期貨數據...")
        logger.info(f"代碼: GC=F")
        logger.info(f"時間範圍: {start_date.strftime('%Y-%m-%d')} 至 {end_date.strftime('%Y-%m-%d')}")

        # 使用yfinance獲取數據 - 你的方法
        gold_ticker = yf.Ticker("GC=F")

        # 先獲取日線數據（指定期間）
        hist_data = gold_ticker.history(
            start=start_date.strftime('%Y-%m-%d'),
            end=end_date.strftime('%Y-%m-%d'),
            interval=interval
        )

        # 嘗試獲取當天的分鐘級數據（最近2天） - 你的邏輯
        try:
            logger.info("正在獲取當天詳細數據...")
            recent_data = gold_ticker.history(
                period='2d',
                interval='1m'
            )

            if not recent_data.empty:
                # 取得今天的數據
                today = datetime.now().date()
                today_data = recent_data[recent_data.index.date >= today]

                if not today_data.empty:
                    # 用今天的最新數據更新收盤價 - 你的邏輯
                    latest_price = today_data['Close'].iloc[-1]
                    latest_time = today_data.index[-1]

                    # 將今天的數據合併到歷史數據中 - 你的邏輯
                    if len(hist_data) > 0:
                        # 更新最後一天的數據
                        last_date = hist_data.index[-1].date()
                        if last_date == today:
                            # 如果今天已有數據，更新它 - 你的邏輯
                            hist_data.loc[hist_data.index[-1], 'Close'] = latest_price
                            hist_data.loc[hist_data.index[-1], 'High'] = max(
                                hist_data.loc[hist_data.index[-1], 'High'], latest_price
                            )
                            hist_data.loc[hist_data.index[-1], 'Low'] = min(
                                hist_data.loc[hist_data.index[-1], 'Low'], latest_price
                            )
                        else:
                            # 添加今天的數據 - 你的邏輯
                            new_row = pd.DataFrame({
                                'Open': [today_data['Open'].iloc[0]],
                                'High': [today_data['High'].max()],
                                'Low': [today_data['Low'].min()],
                                'Close': [latest_price],
                                'Volume': [today_data['Volume'].sum()]
                            }, index=[latest_time.replace(hour=0, minute=0, second=0, microsecond=0)])
                            hist_data = pd.concat([hist_data, new_row])

                    logger.info(f"成功獲取當天數據，最新時間: {latest_time.strftime('%Y-%m-%d %H:%M')}")
                else:
                    logger.info("當天暫無交易數據")
            else:
                logger.info("無法獲取當天詳細數據，使用日線數據")

        except Exception as e:
            logger.warning(f"獲取當天數據時出現問題: {e}，使用日線數據")

        if hist_data.empty:
            raise ValueError("無法獲取數據，請檢查網路連接或API狀態")

        # 獲取最新價格資訊 - 你的邏輯
        info = None
        try:
            info = gold_ticker.info
        except Exception as info_error:
            logger.warning(f"無法獲取市場資訊: {info_error}")

        current_price = hist_data['Close'].iloc[-1] if not hist_data.empty else None

        logger.info(f"成功獲取 {len(hist_data)} 天的數據")
        logger.info(f"最新價格: ${current_price:.2f} USD/oz")
        logger.info(f"數據最後更新: {hist_data.index[-1].strftime('%Y-%m-%d %H:%M')}")

        return hist_data, info, current_price

    except Exception as e:
        logger.error(f"獲取數據時發生錯誤: {e}")
        return None, None, None


def calculate_gold_statistics(data):
    """
    使用你的統計計算邏輯
    """
    if data is None or data.empty:
        return {}

    try:
        close_prices = data['Close']

        stats = {
            'current_price': float(close_prices.iloc[-1]),
            'max_price': float(close_prices.max()),
            'min_price': float(close_prices.min()),
            'avg_price': float(close_prices.mean()),
            'price_change': float(close_prices.iloc[-1] - close_prices.iloc[0]),
            'price_change_pct': float(((close_prices.iloc[-1] - close_prices.iloc[0]) / close_prices.iloc[0]) * 100),
            'volatility': float(close_prices.std()),
            'latest_date': close_prices.index[-1]
        }

        return stats
    except Exception as e:
        logger.error(f"統計計算失敗: {e}")
        return {}


def calculate_technical_indicators_enhanced(hist_data):
    """
    計算技術指標 - 增強版本
    """
    technical_indicators = {}

    try:
        close_prices = hist_data['Close'].dropna()

        if len(close_prices) >= 20:
            ma_20 = close_prices.rolling(window=20).mean().iloc[-1]
            if not pd.isna(ma_20):
                technical_indicators["ma_20"] = float(ma_20)

        if len(close_prices) >= 50:
            ma_50 = close_prices.rolling(window=50).mean().iloc[-1]
            if not pd.isna(ma_50):
                technical_indicators["ma_50"] = float(ma_50)

        if len(close_prices) >= 14:
            rsi = calculate_rsi(close_prices.values)
            if rsi is not None:
                technical_indicators["rsi"] = rsi

        # 額外技術指標
        if len(close_prices) >= 5:
            technical_indicators["volatility_5d"] = float(close_prices.tail(5).std())

        if len(close_prices) >= 20 and "ma_20" in technical_indicators:
            technical_indicators["price_vs_ma20"] = float(
                (close_prices.iloc[-1] / technical_indicators["ma_20"] - 1) * 100)

    except Exception as e:
        logger.warning(f"技術指標計算錯誤: {e}")

    return technical_indicators


def determine_market_status():
    """
    判斷市場狀態 - 改進版本
    """
    try:
        now = datetime.now()
        # 美國市場時間考慮 (EST/EDT)
        # 黃金期貨交易時間: 週日晚上到週五下午
        weekday = now.weekday()  # 0=Monday, 6=Sunday
        hour = now.hour

        # 簡化的市場開放邏輯
        if weekday < 5:  # Monday to Friday
            if 18 <= hour or hour <= 17:  # 大部分時間開市
                return "open"
            else:
                return "closed"
        elif weekday == 6:  # Sunday
            if hour >= 18:  # Sunday evening
                return "open"

        return "closed"
    except Exception:
        return "unknown"


def get_market_name(info):
    """
    獲取市場名稱
    返回 info['longName'] 或默認 'Gold Futures (GC=F)'
    """
    try:
        if isinstance(info, dict) and info:
            return info.get('longName', 'Gold Futures (GC=F)')
        return 'Gold Futures (GC=F)'
    except Exception as e:
        logger.error(f"獲取市場名稱失敗: {e}")
        return 'Gold Futures (GC=F)'


def get_gold_data(period):
    """
    根據給定的時間週期 period，從 Yahoo Finance 獲取並處理黃金價格數據。
    如果發生任何錯誤，將返回模擬數據。
    """
    try:
        # TODO: 在此添加實際的數據抓取和處理邏輯
        # 例如：調用 Yahoo Finance API，生成 chart_data、market_status、technical_indicators 等

        # 範例佔位數據 (請替換為真實邏輯)
        chart_data = []  # 實際的圖表數據列表
        market_status = 'open'  # 或 'closed'
        technical_indicators = {}  # 計算得到的技術指標
        interval = period  # 或其他邏輯

        data = {
            "currency": "USD",
            "unit": "per ounce",
            "last_updated": datetime.now().isoformat(),
            "chart_data": chart_data,
            "market_status": market_status,
            "technical_indicators": technical_indicators,
            "period": period,
            "interval": interval,
            "data_points": len(chart_data)
        }
        result = {
            "data": data,
            "system_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "next_update": (datetime.now() + timedelta(minutes=5)).strftime("%Y-%m-%d %H:%M:%S"),
            "data_source": "Yahoo Finance API"
        }
        return result

    except Exception as e:
        logger.error(f"❌ 獲取或處理黃金價格失敗: {str(e)}")
        # 返回模擬數據而不是拋出異常，確保前端能正常顯示
        return create_mock_gold_data(period)


def create_mock_gold_data(period: str):
    """創建模擬黃金價格數據作為備選方案"""
    logger.info("🔧 使用模擬數據作為備選方案")

    base_price = 2025.50
    current_price = base_price + np.random.uniform(-10, 10)
    change = np.random.uniform(-20, 20)
    change_percent = (change / base_price) * 100

    # 根據時間期間生成模擬圖表數據
    period_days = {
        '1d': 1,
        '5d': 5,
        '1mo': 30,
        '3mo': 90,
        '6mo': 180,
        '1y': 365
    }

    days = period_days.get(period, 365)
    chart_data = []

    for i in range(min(days, 100)):  # 最多100個數據點
        date = datetime.now() - timedelta(days=days - i - 1)
        price_variation = np.random.uniform(-0.02, 0.02)  # 2%的波動
        price = base_price * (1 + price_variation)

        chart_data.append({
            "time": date.isoformat(),
            "price": round(price, 2),
            "high": round(price * 1.005, 2),
            "low": round(price * 0.995, 2),
            "open": round(price * (1 + np.random.uniform(-0.001, 0.001)), 2),
            "volume": np.random.randint(1000, 10000)
        })

    return {
        "status": "success",
        "data": {
            "symbol": "GC=F",
            "name": "Gold Futures (模擬數據)",
            "current_price": round(current_price, 2),
            "change": round(change, 2),
            "change_percent": round(change_percent, 2),
            "high_24h": round(current_price * 1.015, 2),
            "low_24h": round(current_price * 0.985, 2),
            "volume_24h": np.random.randint(50000, 200000),
            "currency": "USD",
            "unit": "per ounce",
            "last_updated": datetime.now().isoformat(),
            "chart_data": chart_data,
            "market_status": "open",
            "technical_indicators": {
                "ma_20": round(current_price * 0.998, 2),
                "ma_50": round(current_price * 1.002, 2),
                "rsi": round(np.random.uniform(30, 70), 1)
            },
            "period": period,
            "interval": "1d",
            "data_points": len(chart_data)
        },
        "system_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "next_update": (datetime.now() + timedelta(minutes=5)).strftime("%Y-%m-%d %H:%M:%S"),
        "data_source": "Mock Data (Yahoo Finance 不可用)"
    }


def calculate_rsi(prices, periods=14):
    """計算 RSI 技術指標 - 增強版本"""
    try:
        if len(prices) < periods + 1:
            return None

        # 轉換為 numpy 數組並確保是浮點數
        prices = np.array(prices, dtype=float)

        # 移除 NaN 值
        prices = prices[~np.isnan(prices)]

        if len(prices) < periods + 1:
            return None

        deltas = np.diff(prices)

        if len(deltas) < periods:
            return None

        up_moves = np.where(deltas > 0, deltas, 0)
        down_moves = np.where(deltas < 0, -deltas, 0)

        # 計算移動平均
        if len(up_moves) >= periods and len(down_moves) >= periods:
            avg_up = np.mean(up_moves[-periods:])
            avg_down = np.mean(down_moves[-periods:])

            if avg_down == 0:
                return 100.0

            rs = avg_up / avg_down
            rsi = 100 - (100 / (1 + rs))
            return round(float(rsi), 1)

        return None

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
    """系統健康檢查 - 增強版本"""
    uptime = datetime.now() - system_stats["uptime_start"]

    # 測試黃金價格 API
    gold_api_status = "healthy"
    try:
        # 快速測試 yfinance 連接
        import yfinance as yf
        test_ticker = yf.Ticker("GC=F")
        test_data = test_ticker.history(period="1d", interval="1d")
        if test_data.empty:
            gold_api_status = "degraded"
    except Exception:
        gold_api_status = "unhealthy"

    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "system": CONFIG['SYSTEM_INFO']['name'],
        "version": CONFIG['SYSTEM_INFO']['version'],
        "has_market_data": len(stored_data) > 0,
        "uptime": str(uptime).split('.')[0],
        "environment": os.getenv('ENVIRONMENT', 'development'),
        "features": {
            "gold_price_api": gold_api_status,
            "market_analysis": "healthy",
            "mail_sender": "healthy",
            "real_time_updates": "healthy"
        },
        "services": {
            "yfinance": gold_api_status,
            "n8n_webhook": "unknown",
            "static_files": "healthy"
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
    logger.info("🚀 市場分析系統啟動 - 修正版")
    logger.info(f"📡 N8N Webhook: {CONFIG['WEBHOOK_CONFIG']['n8n_webhook_url']}")
    logger.info(f"🌐 主網站: http://{CONFIG['SERVER_CONFIG']['host']}:{CONFIG['SERVER_CONFIG']['port']}")
    logger.info(f"📧 郵件頁面: http://{CONFIG['SERVER_CONFIG']['host']}:{CONFIG['SERVER_CONFIG']['port']}/mail")
    logger.info(f"📖 API文檔: http://{CONFIG['SERVER_CONFIG']['host']}:{CONFIG['SERVER_CONFIG']['port']}/api/docs")

    # 測試黃金價格 API
    try:
        logger.info("🔍 測試黃金價格 API...")
        import yfinance as yf
        test_ticker = yf.Ticker("GC=F")
        test_data = test_ticker.history(period="1d")
        if not test_data.empty:
            logger.info("✅ 黃金價格 API 連接正常")
        else:
            logger.warning("⚠️ 黃金價格 API 可能有問題，將使用模擬數據")
    except Exception as e:
        logger.warning(f"⚠️ 黃金價格 API 測試失敗: {str(e)}，將使用模擬數據")


# 錯誤處理
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "status": "error",
            "message": exc.detail,
            "timestamp": datetime.now().isoformat(),
            "path": str(request.url)
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.error(f"未處理的異常: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={
            "status": "error",
            "message": "內部服務器錯誤",
            "timestamp": datetime.now().isoformat(),
            "path": str(request.url)
        }
    )


def main():
    print("🚀 啟動市場分析系統 - 修正版...")
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