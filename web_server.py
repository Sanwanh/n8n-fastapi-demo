#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
市場分析報告系統 - 網頁服務器
Market Analysis Report System - Web Server
"""

import os
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# 初始化 FastAPI
app = FastAPI(
    title="Market Analysis Web",
    description="市場分析網頁界面",
    version="2.0.0"
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


@app.get("/favicon.ico")
async def favicon():
    favicon_path = Path("frontend/static/favicon.ico")
    if favicon_path.exists():
        return FileResponse(favicon_path)
    return Response(content="", media_type="image/x-icon")


def main():
    web_port = int(os.getenv('WEB_PORT', 8080))
    print(f"🌐 啟動網頁服務器: http://0.0.0.0:{web_port}")
    print(f"📧 郵件頁面: http://0.0.0.0:{web_port}/mail")

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=web_port,
        log_level="info"
    )


if __name__ == "__main__":
    main()