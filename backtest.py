from backtesting.backtesting import Backtest, Strategy
from backtesting.lib import crossover, barssince
from backtesting.test import SMA, RSI

import FinanceDataReader as fdr
from model import Screening as scr
import numpy as np
import pandas as pd
from datetime import datetime
import time
import random

def load_price(mkt, count=200):
    data = pd.DataFrame(data=scr.upbit.get_days_candles(market=mkt, count = count))
    data = data[['candle_date_time_kst', 'opening_price', 'high_price', 'low_price', 'trade_price']]
    data = data.rename(
        {'candle_date_time_kst': 'Date', 'opening_price': 'Open', 'high_price': 'High', 'low_price': 'Low',
         'trade_price': 'Close'}, axis=1)
    data['Date'] = [datetime.strptime(x, '%Y-%m-%dT%H:%M:%S') for x in data['Date']]
    return data.set_index('Date')


class Vol(Strategy):
    def init(self):
        self.k = 0.5
        self.vol = self.data.High-self.data.Low

    def next(self):
        price = self.data.Close[-1]
        if (not self.position and
        price > self.data.Open[-1]+self.vol[-2]*self.k):
            self.buy(s1=.9*price)
        elif price < 100:
            self.position.close()

class SmaRsi(Strategy):
    def init(self):
        self.level = 30
        self.ma10 = self.I(SMA, self.data.Close, 5)
        self.ma20 = self.I(SMA, self.data.Close, 20)
        self.rsi = self.I(RSI, self.data.Close, 14)

    def next(self):
        price = self.data.Close[-1]
        if (not self.position and
                self.rsi[-1] > self.level and
                price > self.ma10):
            self.buy(sl=.9*price)
        elif price < .98 * self.ma10[-1]:
            self.position.close()


scr = scr()
coin_list, coin_info = scr.get_basic_info()


data = fdr.DataReader('BTC/KRW', '2018-01-01')  ## 비트코인 일봉 불러오기
# data = load_price("KRW-ETH")  ## 업빗api로 알트코인포함, 240분봉 불러오기

bt = Backtest(data, SmaRsi, commission=.002, cash=100000000, exclusive_orders=True)
res = bt.run()
bt.plot()
print(res)


