import yfinance as yf
import matplotlib.pyplot as plt
import pandas as pd
from datetime import datetime, timedelta
import numpy as np
from matplotlib.widgets import Cursor
import mplcursors


# 配置設定
class Config:
    # 黃金期貨代碼 (COMEX Gold Futures)
    SYMBOL = "GC=F"
    # 資料期間（天數）
    PERIOD_DAYS = 365
    # 圖表設定
    FIGURE_SIZE = (15, 8)
    CHART_STYLE = 'seaborn-v0_8'
    GRID_ALPHA = 0.3


def get_gold_futures_data():
    """
    獲取黃金期貨數據 - 包含當天數據
    返回: pandas DataFrame with 價格數據
    """
    try:
        # 計算起始日期（一年前）
        end_date = datetime.now()
        start_date = end_date - timedelta(days=Config.PERIOD_DAYS)

        print(f"正在獲取黃金期貨數據...")
        print(f"代碼: {Config.SYMBOL}")
        print(f"時間範圍: {start_date.strftime('%Y-%m-%d')} 至 {end_date.strftime('%Y-%m-%d')}")

        # 使用yfinance獲取數據
        gold_ticker = yf.Ticker(Config.SYMBOL)

        # 先獲取日線數據（一年）
        hist_data = gold_ticker.history(
            start=start_date.strftime('%Y-%m-%d'),
            end=end_date.strftime('%Y-%m-%d'),
            interval='1d'
        )

        # 嘗試獲取當天的分鐘級數據（最近2天）
        try:
            print("正在獲取當天詳細數據...")
            recent_data = gold_ticker.history(
                period='2d',
                interval='1m'
            )

            if not recent_data.empty:
                # 取得今天的數據
                today = datetime.now().date()
                today_data = recent_data[recent_data.index.date >= today]

                if not today_data.empty:
                    # 用今天的最新數據更新收盤價
                    latest_price = today_data['Close'].iloc[-1]
                    latest_time = today_data.index[-1]

                    # 將今天的數據合併到歷史數據中
                    if len(hist_data) > 0:
                        # 更新最後一天的數據
                        last_date = hist_data.index[-1].date()
                        if last_date == today:
                            # 如果今天已有數據，更新它
                            hist_data.loc[hist_data.index[-1], 'Close'] = latest_price
                            hist_data.loc[hist_data.index[-1], 'High'] = max(hist_data.loc[hist_data.index[-1], 'High'],
                                                                             latest_price)
                            hist_data.loc[hist_data.index[-1], 'Low'] = min(hist_data.loc[hist_data.index[-1], 'Low'],
                                                                            latest_price)
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

                    print(f"成功獲取當天數據，最新時間: {latest_time.strftime('%Y-%m-%d %H:%M')}")
                else:
                    print("當天暫無交易數據")
            else:
                print("無法獲取當天詳細數據，使用日線數據")

        except Exception as e:
            print(f"獲取當天數據時出現問題: {e}，使用日線數據")

        if hist_data.empty:
            raise ValueError("無法獲取數據，請檢查網路連接或API狀態")

        # 獲取最新價格資訊
        info = gold_ticker.info
        current_price = hist_data['Close'].iloc[-1] if not hist_data.empty else None

        print(f"成功獲取 {len(hist_data)} 天的數據")
        print(f"最新價格: ${current_price:.2f} USD/oz")
        print(f"數據最後更新: {hist_data.index[-1].strftime('%Y-%m-%d %H:%M')}")

        return hist_data, info, current_price

    except Exception as e:
        print(f"獲取數據時發生錯誤: {e}")
        return None, None, None


def calculate_monthly_high_low_avg(data):
    """
    計算每個月最高和最低價格的平均值
    返回: DataFrame with 月度數據和對應的平均日期
    """
    if data is None or data.empty:
        return None

    print("正在計算月度高低平均值...")
    
    # 創建一個包含年月信息的副本
    monthly_data = data.copy()
    monthly_data['YearMonth'] = monthly_data.index.to_period('M')
    
    # 按月份分組並計算每月的最高和最低價
    monthly_stats = monthly_data.groupby('YearMonth').agg({
        'High': 'max',
        'Low': 'min',
        'Close': 'last'  # 用於獲取月末日期
    })
    
    # 計算每月高低平均值
    monthly_stats['High_Low_Avg'] = (monthly_stats['High'] + monthly_stats['Low']) / 2
    
    # 創建對應的日期（使用每月最後一個交易日的日期）
    monthly_dates = []
    for period in monthly_stats.index:
        # 獲取該月份的最後一個交易日
        month_data = monthly_data[monthly_data['YearMonth'] == period]
        if not month_data.empty:
            monthly_dates.append(month_data.index[-1])
    
    # 只取最近12個月的數據
    if len(monthly_stats) > 12:
        monthly_stats = monthly_stats.tail(12)
        monthly_dates = monthly_dates[-12:]
    
    print(f"計算完成，共 {len(monthly_stats)} 個月的數據")
    
    # 為方便繪圖，返回日期和對應的平均值
    return pd.Series(monthly_stats['High_Low_Avg'].values, index=monthly_dates)


def calculate_statistics(data):
    """
    計算價格統計資訊
    """
    if data is None or data.empty:
        return {}

    close_prices = data['Close']
    
    # 獲取當日數據（最新一天）
    latest_date = close_prices.index[-1].date()
    today_data = data[data.index.date == latest_date]
    
    # 計算當日統計
    if not today_data.empty:
        today_high = today_data['High'].max()
        today_low = today_data['Low'].min()
        today_open = today_data['Open'].iloc[0]
        today_close = today_data['Close'].iloc[-1]
        today_change = today_close - today_open
        today_change_pct = (today_change / today_open) * 100 if today_open > 0 else 0
    else:
        # 如果沒有當日詳細數據，使用最後一天的數據
        today_high = data['High'].iloc[-1]
        today_low = data['Low'].iloc[-1]
        today_open = data['Open'].iloc[-1]
        today_close = close_prices.iloc[-1]
        today_change = 0
        today_change_pct = 0

    stats = {
        'current_price': close_prices.iloc[-1],
        'today_high': today_high,
        'today_low': today_low,
        'today_open': today_open,
        'today_close': today_close,
        'today_change': today_change,
        'today_change_pct': today_change_pct,
        'yearly_max': close_prices.max(),
        'yearly_min': close_prices.min(),
        'avg_price': close_prices.mean(),
        'price_change': close_prices.iloc[-1] - close_prices.iloc[0],
        'price_change_pct': ((close_prices.iloc[-1] - close_prices.iloc[0]) / close_prices.iloc[0]) * 100,
        'volatility': close_prices.std(),
        'latest_date': close_prices.index[-1],
        'yearly_average': close_prices.mean()  # 年均線值
    }

    return stats


def create_visualization(data, stats, monthly_hl_avg=None):
    """
    創建價格視覺化圖表
    """
    if data is None or data.empty:
        print("無數據可供繪圖")
        return

    # 設定圖表樣式
    plt.style.use(Config.CHART_STYLE)
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=Config.FIGURE_SIZE, height_ratios=[3, 1])

    # 主圖：價格走勢
    dates = data.index
    prices = data['Close']

    # 繪製價格線
    ax1.plot(dates, prices, linewidth=2, color='gold', label='Gold Futures Price')

    # 標記最新價格點
    ax1.scatter(dates[-1], prices.iloc[-1], color='red', s=100, zorder=5,
                label=f'Latest: ${stats["current_price"]:.2f}')

    # 添加移動平均線
    ma_20 = prices.rolling(window=20).mean()
    ma_50 = prices.rolling(window=50).mean()

    ax1.plot(dates, ma_20, linewidth=1, alpha=0.7, color='blue', label='MA20')
    ax1.plot(dates, ma_50, linewidth=1, alpha=0.7, color='red', label='MA50')

    # 新增：繪製月度高低平均線
    if monthly_hl_avg is not None and not monthly_hl_avg.empty:
        ax1.plot(monthly_hl_avg.index, monthly_hl_avg.values, 
                linewidth=2, alpha=0.8, color='purple', 
                marker='o', markersize=6, 
                label=f'Monthly H/L Avg ({len(monthly_hl_avg)} months)')
        
        print(f"月度高低平均線已添加，包含 {len(monthly_hl_avg)} 個數據點")

    # 新增：繪製年均線（水平線）
    yearly_avg = stats['yearly_average']
    ax1.axhline(y=yearly_avg, color='orange', linestyle='--', 
                linewidth=2, alpha=0.8, 
                label=f'Yearly Average: ${yearly_avg:.2f}')
    
    print(f"年均線已添加：${yearly_avg:.2f} USD/oz")

    # 設定主圖標題 - 包含最新更新時間
    latest_time = stats["latest_date"]
    ax1.set_title(f'Gold Futures (GC=F) - 1 Year Chart | Current: ${stats["current_price"]:.2f} USD/oz ({latest_time.strftime("%Y-%m-%d %H:%M")})',
                  fontsize=14, fontweight='bold', pad=20)
    ax1.set_ylabel('Price (USD/oz)', fontsize=12)
    ax1.grid(True, alpha=Config.GRID_ALPHA)
    # 調整圖例位置，避免與統計框重疊
    ax1.legend(loc='upper right', framealpha=0.9)

    # 添加統計資訊文字框 - 更新以包含當日統計資訊
    info_text = f'''Today's Statistics:
High: ${stats["today_high"]:.2f}
Low: ${stats["today_low"]:.2f}
Open: ${stats["today_open"]:.2f}
Close: ${stats["today_close"]:.2f}
Change: ${stats["today_change"]:+.2f} ({stats["today_change_pct"]:+.1f}%)

Year Statistics:
Max: ${stats["yearly_max"]:.2f}
Min: ${stats["yearly_min"]:.2f}
Avg: ${stats["avg_price"]:.2f}
Volatility: ${stats["volatility"]:.2f}'''

    if monthly_hl_avg is not None and not monthly_hl_avg.empty:
        monthly_avg_value = monthly_hl_avg.mean()
        info_text += f'\nMonthly H/L Avg: ${monthly_avg_value:.2f}'

    # 調整文字框位置和樣式，避免重疊
    ax1.text(0.02, 0.95, info_text, transform=ax1.transAxes,
             verticalalignment='top', horizontalalignment='left',
             bbox=dict(boxstyle="round,pad=0.5", facecolor="white", alpha=0.9, edgecolor='gray'),
             fontsize=9, fontfamily='monospace')

    # 副圖：成交量
    if 'Volume' in data.columns:
        ax2.bar(dates, data['Volume'], alpha=0.6, color='skyblue', width=1)
        ax2.set_ylabel('Volume', fontsize=10)
        ax2.set_xlabel('Date', fontsize=12)
        ax2.grid(True, alpha=Config.GRID_ALPHA)

    # 調整佈局
    plt.tight_layout()

    # 顯示最後更新時間
    plt.figtext(0.99, 0.01, f'Last Updated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}',
                ha='right', va='bottom', fontsize=8, alpha=0.7)

    return fig


def main():
    """
    主程式
    """
    print("=" * 50)
    print("黃金期貨即時價格追蹤器")
    print("=" * 50)

    # 獲取數據
    data, info, current_price = get_gold_futures_data()

    if data is None:
        print("程式執行失敗：無法獲取數據")
        return

    # 計算統計資訊
    stats = calculate_statistics(data)
    
    # 計算月度高低平均值
    monthly_hl_avg = calculate_monthly_high_low_avg(data)

    # 顯示基本資訊
    print("\n" + "=" * 30)
    print("價格統計摘要")
    print("=" * 30)
    print(f"當前價格: ${stats['current_price']:.2f} USD/oz")
    print(f"當日最高: ${stats['today_high']:.2f} USD/oz")
    print(f"當日最低: ${stats['today_low']:.2f} USD/oz")
    print(f"當日開盤: ${stats['today_open']:.2f} USD/oz")
    print(f"當日收盤: ${stats['today_close']:.2f} USD/oz")
    print(f"當日變化: ${stats['today_change']:+.2f} USD ({stats['today_change_pct']:+.1f}%)")
    print(f"年度最高: ${stats['yearly_max']:.2f} USD/oz")
    print(f"年度最低: ${stats['yearly_min']:.2f} USD/oz")
    print(f"年度變化: ${stats['price_change']:+.2f} USD ({stats['price_change_pct']:+.1f}%)")
    print(f"最後更新: {stats['latest_date'].strftime('%Y-%m-%d %H:%M:%S')}")
    
    if monthly_hl_avg is not None and not monthly_hl_avg.empty:
        monthly_avg_value = monthly_hl_avg.mean()
        print(f"月度高低平均: ${monthly_avg_value:.2f} USD/oz ({len(monthly_hl_avg)} 個月)")

    # 創建視覺化
    print(f"\n正在生成圖表...")
    fig = create_visualization(data, stats, monthly_hl_avg)

    if fig:
        plt.show()
        print("圖表已顯示！")

    print("\n程式執行完成。")


if __name__ == "__main__":
    main()