import yfinance as yf
import pandas as pd
import requests
from datetime import datetime, timedelta
import os

# ======================
# ПОСТАВКИ
# ======================
SYMBOLS = ["BTC-USD", "ETH-USD", "SOL-USD"]   # Можеш да додаваш повеќе
FAST_MA = 20
SLOW_MA = 50
STOP_LOSS_PCT = 0.05
TAKE_PROFIT_PCT = 0.10

# Telegram (се читаат од GitHub Secrets)
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def send_telegram(message: str):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("Telegram не е конфигуриран")
        print(message)
        return

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "HTML"
    }
    try:
        r = requests.post(url, json=payload, timeout=10)
        if r.status_code == 200:
            print("✅ Telegram порака испратена")
        else:
            print(f"❌ Грешка: {r.text}")
    except Exception as e:
        print(f"❌ Грешка при испраќање: {e}")

def check_symbol(symbol: str):
    print(f"\nПроверувам {symbol}...")
    
    # Земаме последни 100 дена
    end = datetime.now()
    start = end - timedelta(days=100)
    
    data = yf.download(symbol, start=start.strftime("%Y-%m-%d"), end=end.strftime("%Y-%m-%d"), progress=False)
    
    if data.empty or len(data) < SLOW_MA + 5:
        print(f"Нема доволно податоци за {symbol}")
        return
    
    data['Fast_MA'] = data['Close'].rolling(window=FAST_MA).mean()
    data['Slow_MA'] = data['Close'].rolling(window=SLOW_MA).mean()
    
    # Последните две вредности
    last = data.iloc[-1]
    prev = data.iloc[-2]
    
    current_price = float(last['Close'])
    fast = float(last['Fast_MA'])
    slow = float(last['Slow_MA'])
    
    # --- Сигнал за КУПУВАЊЕ ---
    if prev['Fast_MA'] < prev['Slow_MA'] and last['Fast_MA'] > last['Slow_MA']:
        stop_loss = current_price * (1 - STOP_LOSS_PCT)
        take_profit = current_price * (1 + TAKE_PROFIT_PCT)
        
        message = (
            f"🟢 <b>КУПИ СИГНАЛ</b>\n\n"
            f"Симбол: <b>{symbol}</b>\n"
            f"Цена: <b>{current_price:.2f}</b>\n"
            f"Fast MA ({FAST_MA}): {fast:.2f}\n"
            f"Slow MA ({SLOW_MA}): {slow:.2f}\n\n"
            f"Stop-Loss: {stop_loss:.2f} ({STOP_LOSS_PCT*100}%)\n"
            f"Take-Profit: {take_profit:.2f} ({TAKE_PROFIT_PCT*100}%)\n\n"
            f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        )
        send_telegram(message)
        print(f"→ КУПИ сигнал за {symbol}")
    
    # --- Сигнал за ПРОДАВАЊЕ ---
    elif prev['Fast_MA'] > prev['Slow_MA'] and last['Fast_MA'] < last['Slow_MA']:
        message = (
            f"🔴 <b>ПРОДАЈ СИГНАЛ</b>\n\n"
            f"Симбол: <b>{symbol}</b>\n"
            f"Цена: <b>{current_price:.2f}</b>\n"
            f"Fast MA ({FAST_MA}): {fast:.2f}\n"
            f"Slow MA ({SLOW_MA}): {slow:.2f}\n\n"
            f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        )
        send_telegram(message)
        print(f"→ ПРОДАЈ сигнал за {symbol}")
    
    else:
        print(f"Нема нов сигнал за {symbol} (цена: {current_price:.2f})")

# ======================
# ГЛАВНА ФУНКЦИЈА
# ======================
if __name__ == "__main__":
    print(f"Старт на проверка: {datetime.now()}")
    
    for symbol in SYMBOLS:
        try:
            check_symbol(symbol)
        except Exception as e:
            print(f"Грешка кај {symbol}: {e}")
    
    print("\nГотово.")
