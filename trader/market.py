import json
import urllib.request

URL = "https://indodax.com/api/summaries"

def get_btc_price():
    try:
        request = urllib.request.Request(
            URL,
            headers={
                "User-Agent": "Mozilla/5.0"
            }
        )

        with urllib.request.urlopen(request, timeout=10) as response:
            data = json.loads(response.read().decode())

        ticker = data["tickers"]["btc_idr"]

        return {
            "last": float(ticker["last"]),
            "buy": float(ticker["buy"]),
            "sell": float(ticker["sell"]),
            "high": float(ticker["high"]),
            "low": float(ticker["low"]),
            "volume_btc": float(ticker["vol_btc"]),
            "volume_idr": float(ticker["vol_idr"])
        }

    except Exception as e:
        print("Gagal mengambil data:", e)
        return None


if __name__ == "__main__":
    market = get_btc_price()

    if market:
        print()
        print("===== INDODAX MARKET =====")
        print(f"Harga       : Rp{market['last']:,.0f}")
        print(f"Buy         : Rp{market['buy']:,.0f}")
        print(f"Sell        : Rp{market['sell']:,.0f}")
        print(f"High        : Rp{market['high']:,.0f}")
        print(f"Low         : Rp{market['low']:,.0f}")
        print(f"Volume BTC  : {market['volume_btc']:,.8f}")
        print(f"Volume IDR  : Rp{market['volume_idr']:,.0f}")
        print()
