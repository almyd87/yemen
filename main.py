import telebot
import pandas as pd
import requests
import time
import datetime
import ta
import io
from telebot import types

TOKEN = "7869769364:AAGWDK4orRgxQDcjfEHScbfExgIt_Ti8ARs"
CHAT_ID = "6964741705"
bot = telebot.TeleBot(TOKEN)

SYMBOL = "EURUSD=X"

def fetch_data():
    url = f"https://query1.finance.yahoo.com/v7/finance/download/{SYMBOL}?interval=1m&range=1d"
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers)
    df = pd.read_csv(io.StringIO(response.text))  # ✅ تم التعديل هنا
    df.dropna(inplace=True)
    return df

def analyze():
    df = fetch_data()
    df['EMA20'] = ta.trend.ema_indicator(df['Close'], window=20).ema_indicator()
    df['EMA50'] = ta.trend.ema_indicator(df['Close'], window=50).ema_indicator()
    df['RSI'] = ta.momentum.RSIIndicator(df['Close'], window=14).rsi()
    boll = ta.volatility.BollingerBands(df['Close'])
    df['BB_High'] = boll.bollinger_hband()
    df['BB_Low'] = boll.bollinger_lband()
    df['Supertrend'] = ta.trend.stc(df['Close'])

    last = df.iloc[-1]

    ema_buy = last['Close'] > last['EMA20'] and last['Close'] > last['EMA50']
    rsi_buy = 50 < last['RSI'] < 70
    boll_buy = last['Close'] > last['BB_High']
    supertrend_buy = last['Supertrend'] > 0.5

    score = sum([ema_buy, rsi_buy, boll_buy, supertrend_buy])

    if score >= 3:
        action = "شراء ✅"
        emoji = "🚀"
    elif score <= 1:
        action = "بيع 🔻"
        emoji = "🔥"
    else:
        action = "انتظار ⚠️"
        emoji = "⏳"

    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    message = f"""📉 توصية لحظية لزوج EUR/USD
🕒 الوقت: {now}

📈 الحالة: {action} {emoji}

🔍 تحليل المؤشرات:
• EMA20: {"✅ فوق المتوسط" if last['Close'] > last['EMA20'] else "❌ تحت المتوسط"}
• EMA50: {"✅ فوق المتوسط" if last['Close'] > last['EMA50'] else "❌ تحت المتوسط"}
• RSI(14): {round(last['RSI'], 2)} {"🟢 جيد" if rsi_buy else "🔴 مرتفع أو منخفض"}
• Bollinger: {"✅ كسر الحد العلوي" if boll_buy else "📉 داخل النطاق"}
• SuperTrend: {"📈 صاعد" if supertrend_buy else "📉 هابط"}

📊 التوصية النهائية: {action}
    """
    return message

def send_recommendations():
    while True:
        try:
            msg = analyze()
            bot.send_message(CHAT_ID, msg)
        except Exception as e:
            bot.send_message(CHAT_ID, f"❗ حدث خطأ أثناء التحليل:\n{e}")
        time.sleep(60)

import threading
threading.Thread(target=send_recommendations).start()
bot.polling()