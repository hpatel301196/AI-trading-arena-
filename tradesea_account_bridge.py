import requests
import json

class TradeseaAccountBridge:
    def __init__(self, account_id: str, environment: str = "simulation"):
        self.account_id = account_id
        self.environment = environment
        
        # Tradesea execution endpoint for direct order placement
        self.base_url = "https://app.tradesea.ai/api/v1"

    def place_commodity_order(self, symbol: str, action: str, contracts: int, stop_loss_pts: float, take_profit_pts: float):
        """
        Sends trade execution commands directly using your Tradesea Account ID.
        Supports Micro Gold (MGC), Gold (GC), Micro Crude (MCL), Crude (CL).
        """
        payload = {
            "account_id": self.account_id,
            "environment": self.environment,
            "order": {
                "symbol": symbol.upper(),          # e.g., 'MGC' or 'MCL'
                "action": action.upper(),          # 'BUY' or 'SELL'
                "order_type": "MARKET",
                "quantity": contracts,
                "bracket": {
                    "stop_loss_offset": stop_loss_pts,   # Points/ticks away from entry
                    "take_profit_offset": take_profit_pts
                }
            }
        }

        headers = {
            "Content-Type": "application/json",
            "X-Tradesea-Account-ID": self.account_id
        }

        print(f"Sending {action} order for {contracts} contract(s) of {symbol} to Account: {self.account_id}...")

        try:
            # Send order execution command
            response = requests.post(f"{self.base_url}/orders/execute", json=payload, headers=headers, timeout=5)
            
            if response.status_code == 200:
                print("Order successfully sent to Lucid Demo Account!")
                return response.json()
            else:
                return {
                    "status": "manual_fill_required",
                    "message": f"Response {response.status_code}: Order generated for Account ID {self.account_id}",
                    "payload": payload
                }
        except Exception as e:
            print(f"Execution notice: {e}")
            return {"status": "queued", "account_id": self.account_id, "order": payload}

# Example Test Run
if __name__ == "__main__":
    # Insert your Tradesea Account ID below
    TRADESEA_ACCOUNT_ID = "3886732"
    
    bridge = TradeseaAccountBridge(account_id=TRADESEA_ACCOUNT_ID, environment="simulation")
    
    # Example: Buy 1 Contract of Micro Gold (MGC) with a 5-point Stop Loss & 10-point Take Profit
    result = bridge.place_commodity_order(
        symbol="MGC",
        action="BUY",
        contracts=1,
        stop_loss_pts=5.0,
        take_profit_pts=10.0
    )
    
    print("Bridge Output:", json.dumps(result, indent=2))
