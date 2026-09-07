import requests
import json

class TradeseaExecutionBridge:
    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url

    def execute_order(self, symbol: str, action: str, quantity: int, stop_loss: float, take_profit: float):
        """
        Sends order execution payload directly to Tradesea / Lucid Demo Account.
        """
        payload = {
            "symbol": symbol,           # e.g., "MGC" or "MCL"
            "action": action.lower(),   # "buy" or "sell"
            "size": quantity,           # Contract size (e.g., 1 or 2 contracts)
            "stop_loss": stop_loss,     # Exact Price Level
            "take_profit": take_profit, # Exact Price Level
            "order_type": "market"
        }

        headers = {'Content-Type': 'application/json'}
        
        try:
            response = requests.post(self.webhook_url, data=json.dumps(payload), headers=headers)
            return response.json()
        except Exception as e:
            return {"status": "error", "message": str(e)}

# Example Usage:
# bridge = TradeseaExecutionBridge("YOUR_TRADESEA_WEBHOOK_URL_HERE")
# bridge.execute_order(symbol="MGC", action="buy", quantity=1, stop_loss=2500.0, take_profit=2525.0)
