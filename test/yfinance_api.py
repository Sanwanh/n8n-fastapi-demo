import pandas as pd
import matplotlib.pyplot as plt
import yfinance as yf
from datetime import datetime, timedelta
import os

# 設定中文字型（避免顯示問題）
plt.rcParams['font.sans-serif'] = ['SimHei', 'Arial Unicode MS', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

# 配置設定
CONFIG = {
    'symbol': 'GC=F',  # 黃金期貨，替代 GDF1!
    'period': '1y',  # 一年期間
    'interval': '1h'  # 一小時間隔
}


def get_trading_data(symbol, period='1y', interval='1h'):
    """
    使用 yfinance 獲取交易資料

    Parameters:
    symbol (str): 交易商品代碼
    period (str): 時間週期
    interval (str): 資料間隔

    Returns:
    pd.DataFrame: 交易資料
    """
    try:
        print(f"正在獲取 {symbol} 的資料...")

        # 創建 yfinance Ticker 物件
        ticker = yf.Ticker(symbol)

        # 獲取歷史資料
        data = ticker.history(period=period, interval=interval)

        if data.empty:
            print(f"警告：無法獲取 {symbol} 的資料")
            return None

        print(f"成功獲取 {len(data)} 筆資料")
        return data

    except Exception as e:
        print(f"獲取資料時發生錯誤：{e}")
        return None


def plot_price_chart(data, symbol):
    """
    繪製價格圖表

    Parameters:
    data (pd.DataFrame): 交易資料
    symbol (str): 商品代碼
    """
    if data is None or data.empty:
        print("無資料可繪製")
        return

    # 創建圖表
    plt.figure(figsize=(14, 8))

    # 主圖 - 收盤價
    plt.subplot(2, 1, 1)
    plt.plot(data.index, data['Close'], label='Close Price', linewidth=1.5, color='blue')
    plt.title(f'{symbol} Hourly Close Price (Past Year)', fontsize=16)
    plt.ylabel('Price', fontsize=12)
    plt.grid(True, alpha=0.3)
    plt.legend()

    # 子圖 - 交易量
    plt.subplot(2, 1, 2)
    plt.bar(data.index, data['Volume'], alpha=0.7, color='orange', width=0.02)
    plt.title('Trading Volume', fontsize=14)
    plt.xlabel('Date', fontsize=12)
    plt.ylabel('Volume', fontsize=12)
    plt.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.show()


def save_data_to_csv(data, filename='trading_data.csv'):
    """
    將資料保存到 CSV 檔案

    Parameters:
    data (pd.DataFrame): 交易資料
    filename (str): 檔案名稱
    """
    if data is not None:
        data.to_csv(filename)
        print(f"資料已保存至 {filename}")


def main():
    """主程式"""
    print("=== 交易資料獲取程式 ===")
    print(f"目標商品：{CONFIG['symbol']}")
    print(f"時間週期：{CONFIG['period']}")
    print(f"資料間隔：{CONFIG['interval']}")
    print("=" * 30)

    # 獲取資料
    data = get_trading_data(
        symbol=CONFIG['symbol'],
        period=CONFIG['period'],
        interval=CONFIG['interval']
    )

    if data is not None:
        # 顯示資料摘要
        print("\n資料摘要：")
        print(f"資料期間：{data.index[0]} 至 {data.index[-1]}")
        print(f"總筆數：{len(data)}")
        print(f"最高價：{data['High'].max():.2f}")
        print(f"最低價：{data['Low'].min():.2f}")
        print(f"最新收盤價：{data['Close'].iloc[-1]:.2f}")

        # 繪製圖表
        plot_price_chart(data, CONFIG['symbol'])

        # 保存資料（可選）
        save_choice = input("\n是否要將資料保存為 CSV 檔案？(y/n): ")
        if save_choice.lower() == 'y':
            save_data_to_csv(data)

    else:
        print("程式執行失敗：無法獲取資料")
        print("\n可能的解決方案：")
        print("1. 檢查網路連線")
        print("2. 確認商品代碼是否正確")
        print("3. 嘗試使用其他商品代碼，如：")
        print("   - GC=F (黃金期貨)")
        print("   - SI=F (白銀期貨)")
        print("   - CL=F (原油期貨)")


if __name__ == "__main__":
    main()