get_stock_price_tool = {
    "type": "function",
    "name": "get_stock_price",
    "description": "Get the current stock price",
    "parameters": {
        "type": "object",
        "properties": {
            "symbol": {
                "type": "string",
                "description": "The stock symbol"
            }
        },
        "additionalProperties": False,
        "required": ["symbol"]
    },
    "strict": True
}

TOOLS = [get_stock_price_tool]
