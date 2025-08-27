from fastapi import FastAPI, Query
from fastapi.responses import HTMLResponse
import requests
import math

app = FastAPI()

def ema(arr, n):
    if not arr: return []
    k = 2 / (n + 1)
    ema_values = [arr[0]]
    for price in arr[1:]:
        ema_values.append((price - ema_values[-1]) * k + ema_values[-1])
    return ema_values

def rsi(arr, n=14):
    if len(arr) < n+1: return [None] * len(arr)
    gains, losses = [], []
    for i in range(1, len(arr)):
        change = arr[i] - arr[i-1]
        gains.append(max(0, change))
        losses.append(max(0, -change))
    avg_gain = sum(gains[:n]) / n
    avg_loss = sum(losses[:n]) / n
    rs = avg_gain / avg_loss if avg_loss != 0 else math.inf
    rsi_vals = [None]*n + [100 - (100 / (1 + rs))]
    for i in range(n+1, len(arr)):
        avg_gain = (avg_gain * (n - 1) + gains[i-1]) / n
        avg_loss = (avg_loss * (n - 1) + losses[i-1]) / n
        rs = avg_gain / avg_loss if avg_loss != 0 else math.inf
        rsi_vals.append(100 - (100 / (1 + rs)))
    return rsi_vals

def fetch_prices(symbol="BTCUSDT", interval="15m", limit=100):
    url = f"https://fapi.binance.com/fapi/v1/klines?symbol={symbol}&interval={interval}&limit={limit}"
    res = requests.get(url, timeout=10)
    data = res.json()
    closes = [float(k[4]) for k in data]
    return closes

@app.get("/", response_class=HTMLResponse)
def root(symbol: str = "BTCUSDT", interval: str = "15m"):
    closes = fetch_prices(symbol, interval)
    if not closes:
        return "<h2>Klaida: nepavyko gauti duomenų</h2>"

    ema20 = ema(closes, 20)[-1]
    ema50 = ema(closes, 50)[-1]
    rsi_val = rsi(closes, 14)[-1]

    signal = "WATCH"
    if ema20 > ema50 and rsi_val > 55:
        signal = "LONG"
    elif ema20 < ema50 and rsi_val < 45:
        signal = "SHORT"

    html = f'''
    <html>
        <head><title>Kripto Terminalas</title></head>
        <body style='background:#111;color:#eee;font-family:sans-serif;padding:20px'>
            <h2>🔹 Simbolis: {symbol}</h2>
            <p>Intervalas: {interval}</p>
            <p>Kaina: {closes[-1]:.2f}</p>
            <p>EMA 20: {ema20:.2f}</p>
            <p>EMA 50: {ema50:.2f}</p>
            <p>RSI 14: {rsi_val:.2f}</p>
            <h3>📢 Signalas: <span style='color:{"#0f0" if signal=="LONG" else "#f00" if signal=="SHORT" else "#ff0"}'>{signal}</span></h3>
        </body>
    </html>
    '''
    return html

if __name__ == "__main__":
    import uvicorn
    print("Paleidžiama: http://127.0.0.1:8000")
    uvicorn.run(app, host="127.0.0.1
