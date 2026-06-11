import requests
from django.conf import settings


class StockAPI:
    BASE_URL = "https://www.alphavantage.co/query"

    @staticmethod
    def get_stock_price(symbol):
        api_key = settings.ALPHA_VANTAGE_API_KEY
        if not api_key:
            raise ValueError("Missing API key for Alpha Vantage")

        params = {
            "function": "GLOBAL_QUOTE",
            "symbol": symbol,
            "apikey": api_key,
        }
        response = requests.get(StockAPI.BASE_URL, params=params)
        if response.status_code != 200:
            raise ConnectionError(f"API error: {response.status_code}")

        data = response.json()
        price = data.get("Global Quote", {}).get("05. price", "Unknown")
        return {"symbol": symbol, "price": price}
