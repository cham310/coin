from upbit import Upbitpy
import pandas as pd
from datetime import datetime, timedelta
import time
import random
import telepot
import pickle

def get_basic_info():
    coin_list = pd.DataFrame(data=upbit.get_market_all())
    coin_list = coin_list[coin_list['market'].str.contains('KRW-')]

    coin_info = pd.DataFrame(data=upbit.get_ticker(list(coin_list['market'].values)))
    coin_info['52_week_ratio'] = coin_info['trade_price'] / coin_info['highest_52_week_price'] * 100
    coin_info['highest_52_week_date'] = [datetime.strptime(x, '%Y-%m-%d') for x in
                                         coin_info['highest_52_week_date']]

    txt = '** basic info'
    ## 비트코인 가격 정보 출력 ##
    btc = coin_info[coin_info['market'] == 'KRW-BTC']
    txt = f'비트코인 전고점 날짜: {str(btc["highest_52_week_date"].values[0])[:10]} / 오늘: {str(today)[:10]}\n'
    txt += f'비트코인 가격: {btc["trade_price"].values[0]}  / {btc["52_week_ratio"].values[0]} % \n'
    ## 잡주 코인 비중 출력 ##
    ratio1 = coin_info[coin_info['trade_price'] < 1000].shape[0] / coin_info.shape[0] * 100
    ratio2 = coin_info[coin_info['trade_price'] < 100].shape[0] / coin_info.shape[0] * 100
    txt += f'under 1000: {round(ratio1, 1)}%, under 100: {round(ratio2, 1)}% \n'

    with open('ratio_log.pkl', 'rb') as f:
        df = pickle.load(f)
    df.append({'trade_timestamp': coin_info.iloc[0]['trade_timestamp'], 'under1000': ratio1, 'under100': ratio2})

    with open('ratio_log.pkl', 'wb') as f:
        pickle.dump(df, f)

    return coin_info, coin_list, txt

def send_msg(bot, chat_id):
    coin_info, coin_list, txt = get_basic_info()

    target_coin = coin_info[coin_info['52_week_ratio'] > 85]
    target_coin = target_coin[target_coin['highest_52_week_date'] > today - timedelta(days=5)]

    txt += '** alert!'
    for mkt in target_coin['market']:
        time.sleep(random.uniform(1,5))
        temp = pd.DataFrame(data=upbit.get_minutes_candles(unit=30, market=mkt, count=4))
        ## 조건 설정 ##
        if temp.iloc[0]['candle_acc_trade_volume'] > 1.5 * temp.iloc[1:]['candle_acc_trade_volume'].mean():
            if temp.iloc[0]['trade_price'] > temp.iloc[1:]['high_price'].mean():
                code = temp['market'].iloc[0]
                ## 결과 출력 ##
                nm = coin_list[coin_list['market'] == code]['korean_name'].values[0]
                rtn1 = temp['trade_price'].iloc[0].values[0]/temp['opening_price'].iloc[0].values[0]*100-100
                rtn2 = coin_info[coin_info['market'] == code]['change_rate'].values[0]
                txt += f"{code}({nm}) - 현재가: {temp.iloc[0]['trade_price']} / 30분 등락률: {round(rtn1, 1)}% " \
                       f"/ 등락률: {round(rtn2 * 100, 1)}% \n"

    bot.sendMessage(chat_id=chat_id, text=txt)
    print('--> 메시지 전송 완료!')


token = "aa""
bot = telepot.Bot(token)
chat_id = "aa""

access = "aa""
secret = "aa""
upbit = Upbitpy(access, secret)


while True:
    today = datetime.today()
    now = datetime.now()
    if now.minute == 0 or now.minute == 30:
        send_msg(bot, chat_id)