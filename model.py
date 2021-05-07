from upbit import Upbitpy
import pandas as pd
from datetime import datetime, timedelta
import time
import random
import telepot
import pickle
import os


class Screening:
    def __init__(self, auto_mode=False):
        access = "CHANGE_HERE"
        secret = "CHANGE_HERE"
        bottoken = "CHANGE_HERE"
        self.chat_id = "CHANGE_HERE"
        self.upbit = Upbitpy(access, secret)
        self.bot = telepot.Bot(bottoken)
        self.auto_mode = auto_mode

        self.output_coin = []
        self.txt = ''
        self.j = 0


    def losscut(self, loss):
        acc = pd.DataFrame(data=self.upbit.get_accounts()).fillna(value=0)
        acc[['balance', 'avg_buy_price']] = acc[['balance', 'avg_buy_price']].apply(pd.to_numeric)
        acc['rtn'] = acc['trade_price'] / acc['avg_buy_price'] * 100 - 100

        drop = list(acc[acc['rtn'] < loss]['currency'])
        if len(drop) >0:
            for nm in drop:
                self.upbit.order(nm, "ask", acc[acc['currency'] == nm]['balance'], acc[acc['currency'] == nm]['trade_price'])
                print(f'losscut --> {nm}, rtn: {round(acc[acc["currency"] == nm]["trade_price"], 1)}')
        else:
            pass

    def clean_output(self):
        self.target_coin = self.get_target_coin()
        self.output_coin = []
        self.txt = ''
        self.j = 0


    def get_basic_info(self, print_mode=False):
        coin_list = pd.DataFrame(data=self.upbit.get_market_all())
        coin_list = coin_list[coin_list['market'].str.contains('KRW-')]

        coin_info = pd.DataFrame(data=self.upbit.get_ticker(list(coin_list['market'].values)))
        coin_info['52_week_ratio'] = coin_info['trade_price'] / coin_info['highest_52_week_price'] * 100
        coin_info['highest_52_week_date'] = [datetime.strptime(x, '%Y-%m-%d') for x in
                                             coin_info['highest_52_week_date']]
        if print_mode:
            txt = '** basic info'
            ## 비트코인 가격 정보 출력 ##
            btc = coin_info[coin_info['market'] == 'KRW-BTC']
            txt = f'비트코인 전고점 날짜: {str(btc["highest_52_week_date"].values[0])[:10]} \n'
            txt += f'비트코인 가격: {btc["trade_price"].values[0]}  / {round(btc["52_week_ratio"].values[0],1)} % \n'
            ## 잡주 코인 비중 출력 ##
            ratio1 = coin_info[coin_info['trade_price'] < 1000].shape[0] / coin_info.shape[0] * 100
            ratio2 = coin_info[coin_info['trade_price'] < 100].shape[0] / coin_info.shape[0] * 100
            txt += f'under 1000: {round(ratio1, 1)}%, under 100: {round(ratio2, 1)}% \n'

            # if not os.path.isdir('ratio_log.pkl'):
            #     df = [{'trade_timestamp': coin_info.iloc[0]['trade_timestamp'], 'under1000': ratio1, 'under100': ratio2}]
            #     with open('ratio_log.pkl', 'wb') as f:
            #         pickle.dump(df, f)
            #
            # else:
            #     with open('ratio_log.pkl', 'rb') as f:
            #         df = pickle.load(f)
            #     df.append({'trade_timestamp': coin_info.iloc[0]['trade_timestamp'], 'under1000': ratio1, 'under100': ratio2})
            #     with open('ratio_log.pkl', 'wb') as f:
            #         pickle.dump(df, f)

        return coin_list, coin_info ### list는 이름 등 기본 정보 info는 수치 데이터도 있음

    def get_target_coin(self, a1=60, a2=10):
        today = datetime.today()
        target_coin = self.coin_info[self.coin_info['52_week_ratio'] > a1]   ## 고점대비 현재 위치(%) - 80, 90 등으로 변경
        target_coin = target_coin[target_coin['highest_52_week_date'] > today - timedelta(days=a2)]  ## 고점 대비 조정 기간(days) - 7일, 10일 등으로 변경
        return target_coin

    def make_txt(self, code, type):
        self.output_coin.append({'type': type, 'code': code})
        ## 결과 출력 ##
        self.j += 1
        nm = self.coin_list[self.coin_list['market'] == code]['korean_name'].values[0]
        rtn2 = self.coin_info[self.coin_info['market'] == code]['signed_change_rate'].values[0]
        self.txt += f"* {type} : {code}({nm}) - 가격: {self.coin_info[self.coin_info['market'] == code]['trade_price'].values[0]} " \
                    f"/ 1day 등락률: {round(rtn2 * 100, 1)}% \n"

    def signal1(self, mkt):
        ### 1) 펌핑코인 2) 아래꼬리 코인 스크리닝 ###
        temp = pd.DataFrame(data=self.upbit.get_minutes_candles(unit=30, market=mkt, count=5))  ## 30분봉, 5개를 살펴봄 (2시간 기준) - 10, 6 등으로 변경
        temp['ratio'] = temp['trade_price'] / temp['low_price'] * 100-100

        ## 펌핑 코인 조건 설정 ##
        if temp.iloc[0]['candle_acc_trade_volume'] > 1.5 * temp.iloc[1:]['candle_acc_trade_volume'].mean():     ## 거래량 조건 - 최근 2시간 평균 거래량 1.5배 돌파
            if temp.iloc[0]['trade_price'] > temp.iloc[1:]['high_price'].max():     ## 가격 조건 - 최근 2시간 고점 돌파
                if temp.iloc[0]['trade_price'] > temp.iloc[0]['high_price']*0.9:
                    code = temp['market'].iloc[0]
                    self.make_txt(code, "pumping")
                # if self.auto_mode:


    def signal2(self, mkt):
        ### 이평선 골든크로스 코인 스크리닝 ###
        temp = pd.DataFrame(
            data=self.upbit.get_minutes_candles(unit=240, market=mkt, count=20))    ## 4시간봉, 5-20로 사용
        temp = temp.set_index("candle_date_time_utc").sort_index(ascending=True)
        price = temp['trade_price']
        ma5 = temp['trade_price'].rolling(5).mean()
        ma20 = temp['trade_price'].rolling(20).mean()

        if price.iloc[-1] > ma5.iloc[-1]:
            if (ma5.iloc[-1] > ma20.iloc[-1]) and (ma5.iloc[-4] < ma20.iloc[-4]):
                code = temp['market'].iloc[0]
                self.make_txt(code, "goldencross")

        if price.iloc[-1] < ma5.iloc[-1]:
            if (ma5.iloc[-1] < ma20.iloc[-1]) and (ma5.iloc[-4] > ma20.iloc[-4]):
                code = temp['market'].iloc[0]
                self.make_txt(code, "deadcross")

    def signal3(self, mkt):
        ### 변동성 돌파 전략 ###
        temp = pd.DataFrame(
            data=self.upbit.get_days_candles(market=mkt, count=2))  ## 일봉
        temp = temp.set_index("candle_date_time_utc").sort_index(ascending=True)
        temp['vol'] = temp['high_price'] - temp['low_price']
        target = temp['vol'].iloc[-2].max()
        if (temp['trade_price'].iloc[-1] - temp['opening_price'].iloc[-1]) > target * 0.5:
            code = temp['market'].iloc[0]
            self.make_txt(code, "vol")


    def send_msg(self):
        self.coin_list, self.coin_info = self.get_basic_info()
        self.target_coin = self.get_target_coin()
        self.clean_output()

        for mkt in self.target_coin['market']:
            time.sleep(random.uniform(1, 5))
            self.signal1(mkt)
            self.signal2(mkt)
            self.signal3(mkt)
        # 스크리닝 코인이 있으면 메세지 발송
        if self.j > 0:
            print(self.txt)
            self.bot.sendMessage(chat_id=self.chat_id, text=self.txt)
            print('--> 메시지 전송 완료!')
        else:
            print('--> 스크리닝 코인 없음!')



if __name__ == "__main__":
    scr = Screening()

    while True:
        now = datetime.now()
        if (now.minute % 30 ==0 and now.second == 0):
            scr.send_msg()