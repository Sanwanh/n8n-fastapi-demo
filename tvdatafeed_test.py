from tvDatafeed import TvDatafeed, Interval
import matplotlib.pyplot as plt
import pandas as pd

# 初始化 TradingView 登入（第一次會跳瀏覽器登入）
tv = TvDatafeed(username='ncu.ec310a@gmail.com', password='ncu45002931!')

# 抓取 GDF1! 在 SGX 交易所的 1小時歷史資料
data = tv.get_hist(
    symbol='GDF1!',
    exchange='SGX',
    interval=Interval.in_1_hour,
    n_bars=2000  # 約一年（交易日 × 每日小時數）
)

# 確保 index 是時間戳記
data.index = pd.to_datetime(data.index)

# 畫出收盤價折線圖
plt.figure(figsize=(14, 6))
plt.plot(data.index, data['close'], label='Close Price', linewidth=1)
plt.title('GDF1! Hourly Close Price (Past Year)')
plt.xlabel('Date')
plt.ylabel('Price')
plt.grid(True)
plt.legend()
plt.tight_layout()
plt.show()
