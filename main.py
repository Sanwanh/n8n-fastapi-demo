#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
市場分析報告系統 - API服務 (修正版)
主要修正：
1. 修正市場數據顯示問題
2. 增強錯誤處理和日誌
3. 確保數據正確傳遞到前端
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
    from pydantic import BaseModel, EmailStr, field_validator
    import uvicorn
    import requests
    import yfinance as yf
    import pandas as pd
    import numpy as np
except ImportError as e:
    print(f"❌ 缺少必要的套件: {e}")
    print("請執行: pip install -r requirements.txt")
    sys.exit(1)

# 設定日誌 - 增強版本
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('logs/market_analysis.log', encoding='utf-8')
    ]
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
            'n8n_webhook_url': 'https://beloved-swine-sensibly.ngrok-free.app/webhook/Webhook - Preview',
            'timeout': int(os.getenv('WEBHOOK_TIMEOUT', 30))
        },
        'SYSTEM_INFO': {
            'name': 'Market Analysis API',
            'version': '2.1.4',
            'description': '智能市場分析API服務'
        }
    }


CONFIG = load_config()


# 資料模型
class N8NDataExtended(BaseModel):
    positive: int
    neutral: int
    negative: int
    summary: str
    score: int
    label: str
    emailReportHtml: str

    @field_validator('average_sentiment_score')
    @classmethod
    def validate_score(cls, v):
        if not 0 <= v <= 100:
            raise ValueError('情感分數必須在 0 到 100 之間')
        return v


class MailSenderRequest(BaseModel):
    recipient_email: EmailStr
    sender_name: Optional[str] = "市場分析系統"
    subject: Optional[str] = "市場分析報告"
    priority: Optional[str] = "normal"
    mail_type: Optional[str] = "daily"
    custom_message: Optional[str] = ""
    include_charts: bool = False
    include_recommendations: bool = False
    include_risk_warning: bool = False


# 生命週期管理
from contextlib import asynccontextmanager


@asynccontextmanager
async def lifespan(app: FastAPI):
    """應用生命週期管理"""
    # 啟動時
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

    yield

    # 關閉時
    logger.info("🛑 市場分析系統關閉中...")


# 初始化 FastAPI
app = FastAPI(
    title=CONFIG['SYSTEM_INFO']['name'],
    description=CONFIG['SYSTEM_INFO']['description'],
    version=CONFIG['SYSTEM_INFO']['version'],
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    lifespan=lifespan
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


# 全域變數 - 增強版本
stored_data = {}
system_stats = {
    "total_reports": 0,
    "today_reports": 0,
    "last_reset": datetime.now().date(),
    "uptime_start": datetime.now(),
    "last_data_received": None,
    "api_calls": 0,
    "gold_price_calls": 0,
    "errors": 0
}


# API 路由
@app.post("/api/n8n-data")
async def receive_n8n_data(request: Request):
    """接收來自 N8N 的市場分析資料 - 增強版本"""
    try:
        global stored_data, system_stats

        raw_data = await request.json()
        logger.info(f"📨 收到 N8N 原始資料大小: {len(json.dumps(raw_data, ensure_ascii=False))} 字元")
        logger.info(f"📨 收到 N8N 資料: {json.dumps(raw_data, ensure_ascii=False)[:500]}...")

        # 增強的數據處理邏輯
        if isinstance(raw_data, list) and len(raw_data) > 0:
            market_data = raw_data[0]
            logger.info("✅ 處理陣列格式數據，取第一個元素")
        elif isinstance(raw_data, dict):
            market_data = raw_data
            logger.info("✅ 處理字典格式數據")
        else:
            logger.error(f"❌ 無效的資料格式: {type(raw_data)}")
            raise HTTPException(status_code=400, detail=f"無效的資料格式: {type(raw_data)}")

        # 詳細記錄接收到的數據欄位
        logger.info(f"📊 數據欄位: {list(market_data.keys())}")

        # 構建儲存的數據
        current_time = datetime.now()

        # 處理emailReport內容
        email_report = ""
        if "data" in market_data and isinstance(market_data["data"], dict):
            email_report = market_data["data"].get("emailReport", "")
            logger.info(f"📧 找到emailReport內容，長度: {len(email_report)} 字元")
        elif "emailReport" in market_data:
            email_report = market_data.get("emailReport", "")
            logger.info(f"📧 直接找到emailReport內容，長度: {len(email_report)} 字元")

        stored_data = {
            "positive": int(market_data.get("positive", 0)),
            "neutral": int(market_data.get("neutral", 0)),
            "negative": int(market_data.get("negative", 0)),
            "summary": str(market_data.get("summary", "")),
            "score": int(market_data.get("score", 0)),
            "label": str(market_data.get("label", "")),
            "emailReportHtml": str(market_data.get("emailReportHtml", "")),
            "received_time": current_time.strftime("%Y-%m-%d %H:%M:%S"),
            "received_timestamp": current_time.isoformat(),
            "raw_data": market_data,
            "email_report": email_report,  # 新增emailReport欄位
            "data_source": "N8N Webhook",
            "processing_time": datetime.now().isoformat()
        }

        # 更新系統統計
        system_stats["total_reports"] += 1
        system_stats["today_reports"] += 1
        system_stats["last_data_received"] = current_time.isoformat()

        # 詳細記錄處理後的數據
        # logger.info(f"✅ 成功處理 N8N 資料:")
        # logger.info(f"   情感分數: {stored_data['average_sentiment_score']}")
        # logger.info(f"   內容長度: {len(stored_data['message_content'])} 字元")
        # logger.info(f"   市場日期: {stored_data['market_date']}")
        # logger.info(f"   信心水平: {stored_data['confidence_level']}")
        # logger.info(f"   趨勢方向: {stored_data['trend_direction']}")
        # logger.info(f"   風險評估: {stored_data['risk_assessment']}")
        # logger.info(f"   接收時間: {stored_data['received_time']}")

        return {
            "status": "success",
            "message": "市場分析資料已接收並儲存",
            "data": stored_data,
            "received_at": current_time.isoformat(),
            "processed_fields": len(stored_data),
            "system_stats": system_stats
        }

    except ValueError as ve:
        logger.error(f"❌ 數據驗證錯誤: {str(ve)}")
        system_stats["errors"] += 1
        raise HTTPException(status_code=400, detail=f"數據驗證錯誤: {str(ve)}")
    except Exception as e:
        logger.error(f"❌ 接收 N8N 資料失敗: {str(e)}")
        system_stats["errors"] += 1
        raise HTTPException(status_code=500, detail=f"接收資料失敗: {str(e)}")


@app.get("/api/current-data")
async def get_current_data():
    """取得目前儲存的市場分析資料 - 增強版本"""
    try:
        system_stats["api_calls"] += 1

        # logger.info(f"📤 API 請求 /api/current-data")
        # logger.info(f"📊 當前儲存數據狀態: {'有數據' if stored_data else '無數據'}")

        # if stored_data:
        # logger.info(f"📊 數據詳情:")
        # logger.info(f"   情感分數: {stored_data.get('average_sentiment_score', 'N/A')}")
        # logger.info(f"   內容長度: {len(stored_data.get('message_content', ''))} 字元")
        # logger.info(f"   接收時間: {stored_data.get('received_time', 'N/A')}")

        # 檢查數據是否過期（超過1小時）
        data_age_minutes = 0
        if stored_data and stored_data.get('received_timestamp'):
            try:
                received_time = datetime.fromisoformat(stored_data['received_timestamp'])
                data_age_minutes = (datetime.now() - received_time).total_seconds() / 60
                # logger.info(f"📅 數據年齡: {data_age_minutes:.1f} 分鐘")
            except Exception as e:
                logger.warning(f"⚠️ 無法計算數據年齡: {e}")

        response_data = {
            "status": "success",
            "data": stored_data,
            "stats": system_stats,
            "timestamp": datetime.now().isoformat(),
            "has_data": len(stored_data) > 0,
            "data_age_minutes": data_age_minutes,
            "data_freshness": "fresh" if data_age_minutes < 60 else "stale" if data_age_minutes < 1440 else "very_old"
        }

        # logger.info(f"✅ 回傳數據: {len(stored_data)} 個欄位")
        return response_data

    except Exception as e:
        logger.error(f"❌ 取得當前數據失敗: {str(e)}")
        system_stats["errors"] += 1
        raise HTTPException(status_code=500, detail=f"取得數據失敗: {str(e)}")


@app.get("/api/gold-price")
async def get_gold_price(period: str = "1y", interval: str = "1d"):
    """取得黃金期貨價格 - 增強版本"""
    try:
        system_stats["gold_price_calls"] += 1

        # 驗證參數
        valid_periods = ["1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y"]
        valid_intervals = ["1m", "5m", "15m", "30m", "1h", "1d"]

        if period not in valid_periods:
            logger.warning(f"無效的時間期間: {period}，使用預設值 1y")
            period = "1y"

        if interval not in valid_intervals:
            logger.warning(f"無效的時間間隔: {interval}，使用預設值 1d")
            interval = "1d"

        # logger.info(f"🔍 開始獲取黃金期貨數據")
        # logger.info(f"   期間: {period}")
        # logger.info(f"   間隔: {interval}")
        # logger.info(f"   請求時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        # 獲取黃金期貨數據
        try:
            hist_data, info, current_price, latest_processing_time = await get_gold_futures_data_enhanced(period,
                                                                                                          interval)

            if hist_data is None or hist_data.empty:
                logger.warning("⚠️ 主要數據源無數據，使用備選方案...")
                return create_mock_gold_data(period)

        except Exception as e:
            logger.error(f"❌ yfinance 數據獲取失敗: {str(e)}")
            return create_mock_gold_data(period)

        # logger.info(f"✅ 成功獲取黃金數據:")
        # logger.info(f"   數據點數量: {len(hist_data)}")
        # logger.info(
        #     f"   日期範圍: {hist_data.index[0].strftime('%Y-%m-%d')} 到 {hist_data.index[-1].strftime('%Y-%m-%d')}")

        # 計算統計數據
        stats = calculate_gold_statistics(hist_data)

        if not stats:
            logger.warning("⚠️ 統計計算失敗，使用備選數據")
            return create_mock_gold_data(period)

        # logger.info(f"💰 價格統計:")
        # logger.info(f"   當前價格: ${stats['current_price']:.2f}")
        # logger.info(f"   價格變化: ${stats['price_change']:+.2f} ({stats['price_change_pct']:+.2f}%)")
        # logger.info(f"   價格範圍: ${stats['min_price']:.2f} - ${stats['max_price']:.2f}")
        # logger.info(f"   平均價格: ${stats['avg_price']:.2f}")
        # logger.info(f"   波動率: {stats['volatility']:.2f}")

        # 準備圖表數據
        chart_data = []
        for idx, row in hist_data.iterrows():
            try:
                # 修正時區問題，轉換為台北時間
                if hasattr(idx, 'tz_localize'):
                    if idx.tz is None:
                        # 假設是UTC時間，轉換為台北時間
                        idx_local = idx + timedelta(hours=8)
                    else:
                        # 轉換為台北時間
                        idx_local = idx.tz_convert('Asia/Taipei')
                else:
                    # 假設是UTC時間，轉換為台北時間
                    idx_local = idx + timedelta(hours=8)

                data_point = {
                    "time": idx_local.strftime('%Y-%m-%d'),
                    "price": float(row['Close']) if not pd.isna(row['Close']) else stats['current_price'],
                    "high": float(row['High']) if not pd.isna(row['High']) else stats['current_price'],
                    "low": float(row['Low']) if not pd.isna(row['Low']) else stats['current_price'],
                    "open": float(row['Open']) if not pd.isna(row['Open']) else stats['current_price'],
                    "volume": int(row['Volume']) if not pd.isna(row['Volume']) and row['Volume'] > 0 else 0
                }
                logger.debug(f"數據點: {data_point['time']} - ${data_point['price']:.2f}")
                chart_data.append(data_point)
            except Exception as point_error:
                logger.warning(f"⚠️ 處理數據點時出錯: {point_error}")
                continue

        # logger.info(f"📊 圖表數據:")
        # logger.info(f"   有效數據點: {len(chart_data)}")
        if chart_data:
            prices = [d['price'] for d in chart_data]
            valid_prices = [p for p in prices if not pd.isna(p) and p > 0]
            # logger.info(f"   有效價格數量: {len(valid_prices)}")
            # if valid_prices:
            #     logger.info(f"   價格範圍: ${min(valid_prices):.2f} - ${max(valid_prices):.2f}")
            # logger.info(f"   前3個數據點: {chart_data[:3]}")

        # 計算技術指標
        technical_indicators = calculate_technical_indicators_enhanced(hist_data)
        # logger.info(f"📈 技術指標: {list(technical_indicators.keys())}")

        # 計算移動平均線數據
        ma_lines = {}
        if len(hist_data) >= 5:
            ma_5_data = hist_data['Close'].rolling(window=5).mean().dropna()
            ma_5_line_data = []
            for idx, val in ma_5_data.items():
                # 確保時間格式與圖表數據一致，並正確處理時區
                if hasattr(idx, 'tz_localize'):
                    if idx.tz is None:
                        # 假設是UTC時間，轉換為台北時間
                        idx_local = idx + timedelta(hours=8)
                    else:
                        # 轉換為台北時間
                        idx_local = idx.tz_convert('Asia/Taipei')
                else:
                    # 假設是UTC時間，轉換為台北時間
                    idx_local = idx + timedelta(hours=8)

                ma_5_line_data.append({
                    'time': idx_local.strftime('%Y-%m-%d'),
                    'price': float(val)
                })
            ma_lines["ma_5"] = ma_5_line_data

        if len(hist_data) >= 20:
            ma_20_data = hist_data['Close'].rolling(window=20).mean().dropna()
            ma_20_line_data = []
            for idx, val in ma_20_data.items():
                # 確保時間格式與圖表數據一致，並正確處理時區
                if hasattr(idx, 'tz_localize'):
                    if idx.tz is None:
                        # 假設是UTC時間，轉換為台北時間
                        idx_local = idx + timedelta(hours=8)
                    else:
                        # 轉換為台北時間
                        idx_local = idx.tz_convert('Asia/Taipei')
                else:
                    # 假設是UTC時間，轉換為台北時間
                    idx_local = idx + timedelta(hours=8)

                ma_20_line_data.append({
                    'time': idx_local.strftime('%Y-%m-%d'),
                    'price': float(val)
                })
            ma_lines["ma_20"] = ma_20_line_data

        # 計算MA125線（替代月平均線）
        ma_125_line = calculate_ma125_line(hist_data)

        # 計算季平均價格線（替代年平均線）
        quarterly_average_line = calculate_quarterly_average_line(hist_data)

        # 檢測黃金交叉和死亡交叉
        cross_signal = detect_golden_death_cross(hist_data)

        # 判斷市場狀態
        market_status = determine_market_status()
        # logger.info(f"🏪 市場狀態: {market_status}")

        # 獲取市場資訊
        market_name = get_market_name(info)

        # 計算當日高和當日低
        today_high = None
        today_low = None
        try:
            # 獲取當天的數據
            today = datetime.now().date()
            today_data = hist_data[hist_data.index.date == today]
            if not today_data.empty:
                today_high = float(today_data['High'].max())
                today_low = float(today_data['Low'].min())
                logger.info(f"📊 當日數據: 高=${today_high:.2f}, 低=${today_low:.2f}")
            else:
                # 如果沒有當天數據，使用最近一天的數據
                if len(hist_data) > 0:
                    latest_data = hist_data.iloc[-1]
                    today_high = float(latest_data['High'])
                    today_low = float(latest_data['Low'])
                    logger.info(f"📊 使用最近數據: 高=${today_high:.2f}, 低=${today_low:.2f}")
        except Exception as e:
            logger.warning(f"⚠️ 計算當日高低價失敗: {e}")
            today_high = stats['current_price']
            today_low = stats['current_price']

        # 準備回應數據
        response_data = {
            "status": "success",
            "data": {
                "symbol": "GC=F",
                "name": market_name,
                "current_price": round(stats['current_price'], 2),
                "change": round(stats['price_change'], 2),
                "change_percent": round(stats['price_change_pct'], 2),
                "high_24h": round(stats['max_price'], 2),
                "low_24h": round(stats['min_price'], 2),
                "today_high": round(today_high, 2) if today_high else None,
                "today_low": round(today_low, 2) if today_low else None,
                "avg_price": round(stats['avg_price'], 2),
                "volatility": round(stats['volatility'], 2),
                "volume_24h": 0,  # 移除交易量顯示
                "currency": "USD",
                "unit": "per ounce",
                "last_updated": stats['latest_date'].isoformat(),
                "last_updated_formatted": latest_processing_time,
                "chart_data": chart_data,
                "ma_lines": ma_lines,
                "ma_125_line": ma_125_line,
                "pivot_points": quarterly_average_line,  # 轉折點數據
                "cross_signal": cross_signal,
                "market_status": market_status,
                "technical_indicators": technical_indicators,
                "period": period,
                "interval": interval,
                "data_points": len(chart_data),
                "trading_days": len(hist_data),
                "data_source_info": {
                    "primary": "Yahoo Finance",
                    "realtime_updated": len(chart_data) > 0 and
                                        chart_data[-1]['time'].split('T')[0] == datetime.now().strftime('%Y-%m-%d')
                }
            },
            "system_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "next_update": (datetime.now() + timedelta(minutes=5)).strftime("%Y-%m-%d %H:%M:%S"),
            "data_source": "Yahoo Finance API (Enhanced)",
            "processing_stats": {
                "raw_data_points": len(hist_data),
                "processed_chart_points": len(chart_data),
                "technical_indicators_count": len(technical_indicators),
                "processing_time": datetime.now().isoformat()
            }
        }

        # logger.info(f"✅ 成功回傳黃金價格數據:")
        # logger.info(f"   回應大小: {len(json.dumps(response_data))} 字元")
        # logger.info(f"   圖表數據點: {len(chart_data)}")

        return response_data

    except Exception as e:
        logger.error(f"❌ 獲取黃金價格失敗: {str(e)}")
        system_stats["errors"] += 1
        return create_mock_gold_data(period)


async def get_gold_futures_data_enhanced(period: str, interval: str):
    """獲取黃金期貨數據 - 增強版本"""
    try:
        # 計算時間範圍
        period_days_map = {
            '1d': 1, '5d': 5, '1mo': 30, '3mo': 90,
            '6mo': 180, '1y': 365, '2y': 730, '5y': 1825
        }
        period_days = period_days_map.get(period, 365)

        end_date = datetime.now()
        start_date = end_date - timedelta(days=period_days)

        # logger.info(f"🕐 時間範圍: {start_date.strftime('%Y-%m-%d')} 至 {end_date.strftime('%Y-%m-%d')}")

        # 使用yfinance獲取數據
        gold_ticker = yf.Ticker("GC=F")

        # 獲取歷史數據
        # logger.info(f"📊 正在獲取歷史數據...")
        hist_data = gold_ticker.history(
            start=start_date.strftime('%Y-%m-%d'),
            end=end_date.strftime('%Y-%m-%d'),
            interval=interval
        )

        # logger.info(f"📊 獲取到 {len(hist_data)} 筆歷史數據")

        # 嘗試獲取當天的分鐘級數據
        try:
            # logger.info("🔄 正在獲取當天詳細數據...")
            recent_data = gold_ticker.history(
                period='2d',
                interval='1m'
            )

            if not recent_data.empty:
                today = datetime.now().date()
                today_data = recent_data[recent_data.index.date >= today]

                if not today_data.empty:
                    latest_price = today_data['Close'].iloc[-1]
                    latest_time = today_data.index[-1]

                    # logger.info(f"📊 今日數據: {len(today_data)} 筆，最新價格: ${latest_price:.2f}")
                    # logger.info(f"📅 原始時間: {latest_time}")

                    # 更新歷史數據中的最新價格
                    if len(hist_data) > 0:
                        last_date = hist_data.index[-1].date()
                        if last_date == today:
                            # 更新今天的數據
                            hist_data.loc[hist_data.index[-1], 'Close'] = latest_price
                            hist_data.loc[hist_data.index[-1], 'High'] = max(
                                hist_data.loc[hist_data.index[-1], 'High'], latest_price
                            )
                            hist_data.loc[hist_data.index[-1], 'Low'] = min(
                                hist_data.loc[hist_data.index[-1], 'Low'], latest_price
                            )
                            # logger.info("✅ 已更新今日數據")
                        else:
                            # 添加今天的數據
                            new_row = pd.DataFrame({
                                'Open': [today_data['Open'].iloc[0]],
                                'High': [today_data['High'].max()],
                                'Low': [today_data['Low'].min()],
                                'Close': [latest_price],
                                'Volume': [today_data['Volume'].sum()]
                            }, index=[latest_time.replace(hour=0, minute=0, second=0, microsecond=0)])
                            hist_data = pd.concat([hist_data, new_row])
                            # logger.info("✅ 已添加今日數據")

                    # 修正時區問題，轉換為台北時間 (+8)
                    if hasattr(latest_time, 'tz_localize'):
                        # 如果是時區感知的時間，轉換為台北時間
                        if latest_time.tz is None:
                            # 假設是UTC時間，轉換為台北時間
                            latest_time_local = latest_time + timedelta(hours=8)
                        else:
                            # 轉換為台北時間
                            latest_time_local = latest_time.tz_convert('Asia/Taipei')
                    else:
                        # 假設是UTC時間，轉換為台北時間
                        latest_time_local = latest_time + timedelta(hours=8)

                    latest_time_formatted = latest_time_local.strftime('%Y-%m-%d %H:%M')
                    # logger.info(f"✅ 當天數據處理完成，最新時間: {latest_time_formatted}")
                else:
                    logger.info("ℹ️ 當天暫無交易數據")
            else:
                logger.info("ℹ️ 無法獲取當天詳細數據")

        except Exception as e:
            logger.warning(f"⚠️ 獲取當天數據時出現問題: {e}")

        if hist_data.empty:
            raise ValueError("無法獲取數據，請檢查網路連接或API狀態")

        # 獲取市場資訊
        info = None
        try:
            info = gold_ticker.info
            # logger.info(f"📋 獲取市場資訊: {info.get('longName', 'N/A') if info else 'N/A'}")
        except Exception as info_error:
            logger.warning(f"⚠️ 無法獲取市場資訊: {info_error}")

        current_price = hist_data['Close'].iloc[-1] if not hist_data.empty else None

        # logger.info(f"✅ 數據獲取完成:")
        # logger.info(f"   最終數據點數: {len(hist_data)}")
        # logger.info(f"   最新價格: ${current_price:.2f}")
        # logger.info(f"   最後更新: {hist_data.index[-1].strftime('%Y-%m-%d %H:%M')}")

        # 獲取最新的處理時間
        latest_processing_time = None
        if 'latest_time_formatted' in locals():
            latest_processing_time = latest_time_formatted
        else:
            # 修正時區問題，轉換為台北時間 (+8)
            last_time = hist_data.index[-1]
            if hasattr(last_time, 'tz_localize'):
                if last_time.tz is None:
                    # 假設是UTC時間，轉換為台北時間
                    last_time_local = last_time + timedelta(hours=8)
                else:
                    # 轉換為台北時間
                    last_time_local = last_time.tz_convert('Asia/Taipei')
            else:
                # 假設是UTC時間，轉換為台北時間
                last_time_local = last_time + timedelta(hours=8)
            latest_processing_time = last_time_local.strftime('%Y-%m-%d %H:%M')

        return hist_data, info, current_price, latest_processing_time

    except Exception as e:
        logger.error(f"❌ 獲取數據時發生錯誤: {e}")
        return None, None, None


def calculate_gold_statistics(data):
    """計算黃金統計數據"""
    if data is None or data.empty:
        return {}

    try:
        close_prices = data['Close']

        # 計算日變化（當前價格與昨天收盤價格的差額）
        current_price = float(close_prices.iloc[-1])
        yesterday_price = float(close_prices.iloc[-2]) if len(close_prices) > 1 else current_price

        daily_change = current_price - yesterday_price
        daily_change_pct = ((daily_change / yesterday_price) * 100) if yesterday_price != 0 else 0

        # 計算年度標準差（使用整個數據集）
        # 使用 ddof=1 來計算樣本標準差，與前端的計算方法保持一致
        annual_volatility = float(close_prices.std(ddof=1))

        stats = {
            'current_price': current_price,
            'max_price': float(close_prices.max()),
            'min_price': float(close_prices.min()),
            'avg_price': float(close_prices.mean()),
            'price_change': daily_change,  # 日變化
            'price_change_pct': daily_change_pct,  # 日變化百分比
            'volatility': annual_volatility,  # 年度標準差
            'latest_date': close_prices.index[-1],
            'yesterday_price': yesterday_price  # 添加昨天價格用於調試
        }

        # logger.info(f"📊 統計計算完成: 當前=${stats['current_price']:.2f}, 日變化={stats['price_change']:+.2f}")
        return stats
    except Exception as e:
        logger.error(f"❌ 統計計算失敗: {e}")
        return {}


def calculate_technical_indicators_enhanced(hist_data):
    """計算技術指標 - 增強版本"""
    technical_indicators = {}

    try:
        close_prices = hist_data['Close'].dropna()

        # MA5 計算
        if len(close_prices) >= 5:
            ma_5 = close_prices.rolling(window=5).mean().iloc[-1]
            if not pd.isna(ma_5):
                technical_indicators["ma_5"] = float(ma_5)

        # MA20 計算
        if len(close_prices) >= 20:
            ma_20 = close_prices.rolling(window=20).mean().iloc[-1]
            if not pd.isna(ma_20):
                technical_indicators["ma_20"] = float(ma_20)

        # MA50 計算
        if len(close_prices) >= 50:
            ma_50 = close_prices.rolling(window=50).mean().iloc[-1]
            if not pd.isna(ma_50):
                technical_indicators["ma_50"] = float(ma_50)

        # RSI 計算
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

        # logger.info(f"📈 技術指標計算完成: {len(technical_indicators)} 個指標")

    except Exception as e:
        logger.warning(f"⚠️ 技術指標計算錯誤: {e}")

    return technical_indicators


def calculate_rsi(prices, periods=14):
    """計算 RSI 技術指標"""
    try:
        if len(prices) < periods + 1:
            return None

        prices = np.array(prices, dtype=float)
        prices = prices[~np.isnan(prices)]

        if len(prices) < periods + 1:
            return None

        deltas = np.diff(prices)

        if len(deltas) < periods:
            return None

        up_moves = np.where(deltas > 0, deltas, 0)
        down_moves = np.where(deltas < 0, -deltas, 0)

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
        logger.warning(f"⚠️ RSI 計算錯誤: {e}")
        return None


def calculate_monthly_average_line(hist_data):
    """計算每月最高最低價格平均值的線 - 每個月一個點"""
    try:
        # 確保數據有日期索引
        if not isinstance(hist_data.index, pd.DatetimeIndex):
            hist_data.index = pd.to_datetime(hist_data.index)

        # 統一時區處理 - 轉換為無時區的日期
        hist_data.index = hist_data.index.tz_localize(None)

        # 按月份分組並計算每月的最高和最低價格
        monthly_data = hist_data.groupby(hist_data.index.to_period('M')).agg({
            'High': 'max',
            'Low': 'min'
        })

        # 計算每月最高最低價格的平均值
        monthly_averages = (monthly_data['High'] + monthly_data['Low']) / 2

        # 取最近12個月的數據
        monthly_averages = monthly_averages.tail(12)

        # 轉換為圖表數據格式 - 每個月只創建一個數據點
        monthly_line_data = []
        for period, avg_price in monthly_averages.items():
            try:
                # 使用該月的最後一個交易日作為代表日期
                try:
                    month_end = period.to_timestamp() + pd.offsets.MonthEnd(0)
                except Exception as e:
                    logger.warning(f"⚠️ 轉換月份 {period} 時出錯: {e}")
                    continue

                # 找到該月的最後一個交易日
                month_trading_days = [date for date in hist_data.index if date <= month_end]
                if month_trading_days:
                    last_trading_day = max(month_trading_days)
                    monthly_line_data.append({
                        'time': str(last_trading_day)[:10],  # 取前10個字符作為日期
                        'price': float(avg_price)
                    })
            except Exception as e:
                logger.warning(f"⚠️ 處理月份 {period} 時出錯: {e}")
                continue

        logger.info(f"📊 月平均線計算完成，共 {len(monthly_line_data)} 個數據點")
        logger.info(f"    月平均價格範圍: ${monthly_averages.min():.2f} - ${monthly_averages.max():.2f}")

        return monthly_line_data

    except Exception as e:
        logger.warning(f"⚠️ 每月平均線計算錯誤: {e}")
        return []


def calculate_quarterly_average_line(hist_data):
    """
    計算轉折點（Pivot Point）- 每月初計算一次，該點為前三個月最高價與最低價的平均值，每月只產生一個點，並可連成折線圖。
    """
    try:
        # 確保索引為 DatetimeIndex
        if not isinstance(hist_data.index, pd.DatetimeIndex):
            hist_data.index = pd.to_datetime(hist_data.index)

        # 統一處理時區問題，轉換為台北時間 (+8)
        if hist_data.index.tz is None:
            # 假設是UTC時間，轉換為台北時間
            hist_data.index = hist_data.index + timedelta(hours=8)
        else:
            # 轉換為台北時間
            hist_data.index = hist_data.index.tz_convert('Asia/Taipei')

        # 移除時區信息，統一為本地時間
        hist_data.index = hist_data.index.tz_localize(None)

        # 確保數據按時間排序
        hist_data = hist_data.sort_index()

        # 獲取數據的時間範圍
        start_date = hist_data.index.min()
        end_date = hist_data.index.max()

        logger.info(f"📊 數據時間範圍: {start_date.strftime('%Y-%m-%d')} 到 {end_date.strftime('%Y-%m-%d')}")

        if len(hist_data) < 90:
            logger.warning("⚠️ 數據不足90天，無法計算轉折點")
            return []

        points = []

        # 修正：使用更精確的月份計算方法
        # 將數據按月份分組
        hist_data['year_month'] = hist_data.index.to_period('M')
        monthly_groups = hist_data.groupby('year_month')

        # 獲取所有月份
        all_months = sorted(monthly_groups.groups.keys())

        logger.info(f"📊 可用月份: {[str(m) for m in all_months]}")

        # 從第4個月開始計算（需要前3個月的數據）
        for i in range(3, len(all_months)):
            current_month = all_months[i]

            # 獲取前三個月的數據
            prev3_months = all_months[i - 3:i]
            prev3_data = hist_data[hist_data['year_month'].isin(prev3_months)]

            if len(prev3_data) == 0:
                logger.warning(f"⚠️ 月份 {current_month} 的前三個月數據不足")
                continue

            # 計算前三個月的最高價和最低價
            high = prev3_data['High'].max()
            low = prev3_data['Low'].min()
            pivot = (high + low) / 2

            # 獲取當前月份的數據
            current_month_data = hist_data[hist_data['year_month'] == current_month]

            # 修正：確保每個月都有一個轉折點，使用當月第一個交易日
            if len(current_month_data) > 0:
                # 使用當月第一個交易日
                first_trading_day = current_month_data.index.min()
                point_date = first_trading_day.strftime('%Y-%m-%d')
                logger.info(f"📊 轉折點: {point_date} (月份: {current_month}) = ${pivot:.2f}")
            else:
                # 如果當月沒有交易數據，使用月初日期
                point_date = current_month.to_timestamp().strftime('%Y-%m-%d')
                logger.warning(f"⚠️ 當月無交易數據，使用月初: {point_date}")

            points.append({
                'time': point_date,
                'price': float(pivot),
                'high': float(high),
                'low': float(low),
                'range': f"{prev3_months[0]}~{prev3_months[-1]}"
            })

        # 按時間排序確保折線圖正確連接
        points.sort(key=lambda x: x['time'])

        logger.info(f"📊 轉折點計算完成，共 {len(points)} 個數據點")
        if points:
            prices = [p['price'] for p in points]
            logger.info(f"    轉折點價格範圍: ${min(prices):.2f} - ${max(prices):.2f}")
            logger.info(f"    轉折點時間範圍: {points[0]['time']} 到 {points[-1]['time']}")

            # 檢查每個月的點數
            monthly_counts = {}
            for point in points:
                month = point['time'][:7]  # 取YYYY-MM部分
                monthly_counts[month] = monthly_counts.get(month, 0) + 1

            logger.info(f"    每月點數統計:")
            for month, count in sorted(monthly_counts.items()):
                logger.info(f"      {month}: {count} 個點")

            # 檢查轉折點的連續性
            logger.info(f"    轉折點詳細信息:")
            for i, point in enumerate(points):
                logger.info(f"      {i + 1}. {point['time']} - ${point['price']:.2f} (基於{point['range']})")
        else:
            logger.info("    無轉折點數據")

        return points

    except Exception as e:
        logger.warning(f"⚠️ 轉折點計算錯誤: {e}")
        return []


def calculate_ma125_line(hist_data):
    """計算MA125移動平均線"""
    try:
        # 確保數據有日期索引
        if not isinstance(hist_data.index, pd.DatetimeIndex):
            hist_data.index = pd.to_datetime(hist_data.index)

        if len(hist_data) < 125:
            logger.warning("⚠️ 數據不足125天，無法計算MA125")
            return []

        # 計算MA125
        ma_125_data = hist_data['Close'].rolling(window=125).mean().dropna()

        # 轉換為圖表數據格式，確保時間格式與圖表數據一致
        ma_125_line_data = []
        for idx, val in ma_125_data.items():
            # 確保時間格式與圖表數據一致，並正確處理時區
            if hasattr(idx, 'tz_localize'):
                if idx.tz is None:
                    # 假設是UTC時間，轉換為台北時間
                    idx_local = idx + timedelta(hours=8)
                else:
                    # 轉換為台北時間
                    idx_local = idx.tz_convert('Asia/Taipei')
            else:
                # 假設是UTC時間，轉換為台北時間
                idx_local = idx + timedelta(hours=8)

            ma_125_line_data.append({
                'time': idx_local.strftime('%Y-%m-%d'),
                'price': float(val)
            })

        logger.info(f"📊 MA125計算完成，共 {len(ma_125_line_data)} 個數據點")
        logger.info(f"    最新MA125值: ${ma_125_data.iloc[-1]:.2f}")

        return ma_125_line_data

    except Exception as e:
        logger.warning(f"⚠️ MA125計算錯誤: {e}")
        return []


def detect_golden_death_cross(hist_data):
    """檢測黃金交叉和死亡交叉 - 使用MA20穿越MA5"""
    try:
        if len(hist_data) < 20:
            return {"golden_cross": False, "death_cross": False, "message": "", "status": "normal"}

        # 計算MA20和MA5
        ma_20 = hist_data['Close'].rolling(window=20).mean()
        ma_5 = hist_data['Close'].rolling(window=5).mean()

        # 獲取最近幾個數據點進行比較
        recent_data = hist_data.tail(10)
        recent_ma20 = ma_20.tail(10)
        recent_ma5 = ma_5.tail(10)

        # 檢查是否有足夠的數據
        if recent_ma20.isna().all() or recent_ma5.isna().all():
            return {"golden_cross": False, "death_cross": False, "message": "", "status": "normal"}

        # 獲取最新的MA值，確保轉換為Python原生類型
        current_ma20 = float(recent_ma20.iloc[-1])
        current_ma5 = float(recent_ma5.iloc[-1])
        prev_ma20 = float(recent_ma20.iloc[-2]) if len(recent_ma20) > 1 else current_ma20
        prev_ma5 = float(recent_ma5.iloc[-2]) if len(recent_ma5) > 1 else current_ma5

        # 檢測黃金交叉（MA20從下方穿越MA5）
        golden_cross = bool((prev_ma20 < prev_ma5) and (current_ma20 > current_ma5))

        # 檢測死亡交叉（MA20從上方穿越MA5）
        death_cross = bool((prev_ma20 > prev_ma5) and (current_ma20 < current_ma5))

        message = ""
        status = "normal"
        if golden_cross:
            message = "🟢 黃金交叉：MA20穿越MA5向上，看漲信號"
            status = "golden_cross"
            logger.info(f"🟢 檢測到黃金交叉: MA20=${current_ma20:.2f}, MA5=${current_ma5:.2f}")
        elif death_cross:
            message = "🔴 死亡交叉：MA20穿越MA5向下，看跌信號"
            status = "death_cross"
            logger.info(f"🔴 檢測到死亡交叉: MA20=${current_ma20:.2f}, MA5=${current_ma5:.2f}")
        else:
            message = "⚪ 正常：MA20與MA5無交叉信號"
            status = "normal"
            logger.info(f"⚪ 無交叉信號: MA20=${current_ma20:.2f}, MA5=${current_ma5:.2f}")

        return {
            "golden_cross": golden_cross,
            "death_cross": death_cross,
            "status": status,
            "message": message,
            "current_ma20": current_ma20,
            "current_ma5": current_ma5
        }

    except Exception as e:
        logger.warning(f"⚠️ 交叉檢測錯誤: {e}")
        return {"golden_cross": False, "death_cross": False, "message": "", "status": "normal"}


def calculate_yearly_average_line(hist_data):
    """計算年平均價格線 - 修正為真正的水平線"""
    try:
        # 確保數據有日期索引
        if not isinstance(hist_data.index, pd.DatetimeIndex):
            hist_data.index = pd.to_datetime(hist_data.index)

        # 計算過去一年的平均價格
        one_year_ago = hist_data.index.max() - pd.DateOffset(years=1)
        yearly_data = hist_data[hist_data.index >= one_year_ago]

        if len(yearly_data) == 0:
            logger.warning("⚠️ 沒有足夠的數據計算年平均價格")
            return []

        # 計算年平均價格
        yearly_avg_price = yearly_data['Close'].mean()

        # 創建一條水平線，覆蓋整個時間範圍
        yearly_line_data = []
        for date in hist_data.index:
            yearly_line_data.append({
                'time': str(date)[:10],  # 取前10個字符作為日期
                'price': float(yearly_avg_price)
            })

        logger.info(f"📊 年平均價格計算完成: ${yearly_avg_price:.2f}")
        logger.info(f"    數據範圍: {str(yearly_data.index.min())[:10]} 至 {str(yearly_data.index.max())[:10]}")
        logger.info(f"    數據點數: {len(yearly_data)}")

        return yearly_line_data

    except Exception as e:
        logger.warning(f"⚠️ 年平均價格計算錯誤: {e}")
        return []


def determine_market_status():
    """判斷市場狀態 - 黃金期貨市場時間 (美東時間)"""
    try:
        from datetime import timezone, timedelta

        # 獲取美東時間
        # 注意：這裡簡化處理，實際應該考慮夏令時間
        # 美東時間 = UTC - 5小時 (標準時間) 或 UTC - 4小時 (夏令時間)
        utc_now = datetime.now(timezone.utc)

        # 簡化：假設是標準時間 (UTC - 5)
        # 實際應用中應該使用 pytz 或 zoneinfo 來正確處理時區
        est_offset = timedelta(hours=5)
        est_now = utc_now - est_offset

        weekday = est_now.weekday()  # 0=Monday, 6=Sunday
        hour = est_now.hour
        minute = est_now.minute

        # 黃金期貨市場時間 (美東時間 EST)
        # 週日 6:00 PM - 週五 5:00 PM (美東時間)
        # 週五 5:00 PM - 週日 6:00 PM 休市

        # 調試信息
        logger.info(f"🔍 市場狀態判斷: UTC={utc_now.strftime('%Y-%m-%d %H:%M')}, "
                    f"EST={est_now.strftime('%Y-%m-%d %H:%M')}, "
                    f"週{weekday + 1}, {hour:02d}:{minute:02d}")

        if weekday < 5:  # Monday to Friday
            logger.info("✅ 週一到週五 - 開市")
            return "open"  # 週一到週五都是開市
        elif weekday == 5:  # Saturday
            logger.info("❌ 週六 - 休市")
            return "closed"  # 週六休市
        elif weekday == 6:  # Sunday
            # 週日 6:00 PM (18:00) 後開市
            if hour >= 18:
                logger.info("✅ 週日 18:00後 - 開市")
                return "open"
            else:
                logger.info("❌ 週日 18:00前 - 休市")
                return "closed"
        else:
            logger.info("❌ 未知週期 - 休市")
            return "closed"

    except Exception as e:
        logger.error(f"❌ 市場狀態判斷失敗: {e}")
        return "unknown"


def get_market_name(info):
    """獲取市場名稱"""
    try:
        if isinstance(info, dict) and info:
            return info.get('longName', 'Gold Futures (GC=F)')
        return 'Gold Futures (GC=F)'
    except Exception as e:
        logger.error(f"❌ 獲取市場名稱失敗: {e}")
        return 'Gold Futures (GC=F)'


def create_mock_gold_data(period: str):
    """創建模擬黃金價格數據作為備選方案"""
    logger.info("🔧 使用模擬數據作為備選方案")

    base_price = 2025.50
    current_price = base_price + np.random.uniform(-10, 10)
    change = np.random.uniform(-20, 20)
    change_percent = (change / base_price) * 100

    # 根據時間期間生成模擬圖表數據
    period_days = {
        '1d': 1, '5d': 5, '1mo': 30, '3mo': 90,
        '6mo': 180, '1y': 365
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

    logger.info(f"🔧 生成模擬數據: {len(chart_data)} 個數據點")

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
            "today_high": round(current_price * 1.008, 2),
            "today_low": round(current_price * 0.992, 2),
            "avg_price": round(base_price, 2),
            "volatility": round(np.random.uniform(10, 50), 2),
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
            "data_points": len(chart_data),
            "trading_days": len(chart_data)
        },
        "system_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "next_update": (datetime.now() + timedelta(minutes=5)).strftime("%Y-%m-%d %H:%M:%S"),
        "data_source": "Mock Data (Yahoo Finance 不可用)"
    }


@app.post("/api/send-mail-to-n8n")
async def send_mail_to_n8n(mail_data: MailSenderRequest):
    """發送郵件數據到 N8N webhook"""
    try:
        # logger.info(f"📧 收到郵件發送請求:")
        # logger.info(f"   收件人: {mail_data.recipient_email}")
        # logger.info(f"   自訂訊息: {mail_data.custom_message[:50] if mail_data.custom_message else '無'}...")
        # logger.info(f"   主題: {mail_data.subject}")

        if not stored_data:
            logger.error("❌ 沒有可用的市場分析資料")
            raise HTTPException(status_code=400, detail="沒有可用的市場分析資料")

        # logger.info(f"📊 當前儲存數據: {len(stored_data)} 個欄位")
        # logger.info(f"   情感分數: {stored_data.get('average_sentiment_score', 'N/A')}")
        # logger.info(f"   內容長度: {len(stored_data.get('message_content', ''))} 字元")

        # 構建發送到 N8N 的數據結構
        send_data = {
            **stored_data,
            "mail_config": {
                "recipient_email": str(mail_data.recipient_email),
                "sender_name": mail_data.sender_name or "市場分析系統",
                "subject": mail_data.subject or "市場分析報告",
                "priority": mail_data.priority or "normal",
                "mail_type": mail_data.mail_type or "daily",
                "custom_message": mail_data.custom_message or "",
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

        # logger.info(f"📤 準備發送數據到 N8N:")
        # logger.info(f"   Webhook URL: {CONFIG['WEBHOOK_CONFIG']['n8n_webhook_url']}")
        # logger.info(f"   數據大小: {len(json.dumps(send_data, ensure_ascii=False))} 字元")
        #
        # # 輸出完整的 JSON 數據
        # logger.info("📋 發送到 N8N 的完整 JSON 數據:")
        # logger.info(json.dumps(send_data, ensure_ascii=False, indent=2))
        #
        # logger.info("📤 開始發送數據到 N8N...")

        response = requests.post(
            CONFIG['WEBHOOK_CONFIG']['n8n_webhook_url'],
            json=send_data,
            headers={'Content-Type': 'application/json'},
            timeout=CONFIG['WEBHOOK_CONFIG']['timeout']
        )

        # logger.info(f"📡 N8N 回應狀態: {response.status_code}")
        # logger.info(f"📡 N8N 回應內容: {response.text[:200]}...")

        if response.status_code == 200:
            # logger.info("✅ 郵件數據已成功發送到 N8N")
            return {
                "status": "success",
                "message": f"郵件數據已成功發送到 N8N",
                "sent_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "recipient": str(mail_data.recipient_email),
                "n8n_response": response.text[:100] if response.text else "無回應內容"
            }
        else:
            logger.error(f"❌ N8N webhook 回應錯誤: {response.status_code} - {response.text}")
            raise HTTPException(status_code=response.status_code, detail=f"N8N webhook 回應錯誤: {response.text}")

    except requests.exceptions.Timeout:
        logger.error("❌ 請求超時")
        raise HTTPException(status_code=500, detail="請求超時")
    except requests.exceptions.ConnectionError:
        logger.error("❌ 無法連接到 N8N webhook")
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


@app.get("/api/debug-stored-data")
async def debug_stored_data():
    """調試端點 - 查看當前存儲的數據結構"""
    try:
        if not stored_data:
            return {
                "status": "warning",
                "message": "沒有存儲的數據",
                "data": None,
                "timestamp": datetime.now().isoformat()
            }

        # 構建示例郵件數據（不實際發送）
        sample_mail_data = {
            "recipient_email": "test@example.com",
            "custom_message": "這是一個測試訊息"
        }

        # 模擬郵件發送時的數據結構
        sample_send_data = {
            **stored_data,
            "mail_config": {
                "recipient_email": sample_mail_data["recipient_email"],
                "sender_name": "市場分析系統",
                "subject": "市場分析報告",
                "priority": "normal",
                "mail_type": "daily",
                "custom_message": sample_mail_data["custom_message"],
                "include_charts": False,
                "include_recommendations": False,
                "include_risk_warning": False
            },
            "system_info": {
                "send_timestamp": datetime.now().isoformat(),
                "system_version": CONFIG['SYSTEM_INFO']['version'],
                "source": "debug-endpoint"
            },
            "sentiment_analysis": {
                "score": stored_data.get("average_sentiment_score", 0),
                "text": get_sentiment_text(stored_data.get("average_sentiment_score", 0)),
                "emoji": get_market_emoji(stored_data.get("average_sentiment_score", 0))
            }
        }

        return {
            "status": "success",
            "message": "當前存儲的數據結構",
            "json_data": sample_send_data,
            "timestamp": datetime.now().isoformat(),
            "webhook_url": CONFIG['WEBHOOK_CONFIG']['n8n_webhook_url']
        }

    except Exception as e:
        logger.error(f"❌ 調試數據端點錯誤: {str(e)}")
        return {
            "status": "error",
            "message": f"調試數據失敗: {str(e)}",
            "timestamp": datetime.now().isoformat()
        }


@app.get("/health")
async def health_check():
    """系統健康檢查 - 增強版本"""
    uptime = datetime.now() - system_stats["uptime_start"]

    # 測試黃金價格 API
    gold_api_status = "healthy"
    try:
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
        "stats": system_stats,
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


# 錯誤處理
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    logger.error(f"HTTP異常: {exc.status_code} - {exc.detail}")
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
    system_stats["errors"] += 1
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
    uvicorn.run(
        app,
        host=CONFIG['SERVER_CONFIG']['host'],
        port=CONFIG['SERVER_CONFIG']['port'],
        log_level="info",
        reload=CONFIG['SERVER_CONFIG'].get('debug', False)
    )


if __name__ == "__main__":
    main()