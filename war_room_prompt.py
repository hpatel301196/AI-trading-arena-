import time
from order_flow_engine import CommodityOrderFlowEngine
from tradesea_account_bridge import TradeseaAccountBridge

# 1. Configuration Settings
TRADESEA_ACCOUNT_ID = "YOUR_TRADESEA_ACCOUNT_ID_HERE"
SYMBOL = "MGC"  # Micro Gold
CONTRACTS = 1

# 2. Initialize Engine and Execution Bridge
order_flow = CommodityOrderFlowEngine(symbol=SYMBOL)
bridge = TradeseaAccountBridge(account_id=TRADESEA_ACCOUNT_ID, environment="simulation")

def evaluate_trade_setup(metrics: dict):
    """
    Evaluates real-time microstructure data to determine high-probability trades.
    """
    delta = metrics.get("delta", 0)
    buy_wall = metrics.get("buy_wall")
    sell_wall = metrics.get("sell_wall")
    imbalance = metrics.get("imbalance", 1.0)

    print(f"[{SYMBOL}] Delta: {delta} | Imbalance Ratio: {imbalance}")

    # BUY CONDITION: Positive Delta Shift + Order Book Bid Imbalance >= 1.8
    if delta > 150 and imbalance >= 1.8:
        return {
            "action": "BUY",
            "reason": f"Strong positive delta (+{delta}) & bid imbalance ({imbalance})",
            "stop_loss_pts": 4.0,   # $4.00 stop distance on Gold
            "take_profit_pts": 10.0  # $10.00 target distance on Gold
        }

    # SELL CONDITION: Negative Delta Shift + Order Book Ask Imbalance <= 0.5
    elif delta < -150 and imbalance <= 0.5:
        return {
            "action": "SELL",
            "reason": f"Strong negative delta ({delta}) & ask imbalance ({imbalance})",
            "stop_loss_pts": 4.0,
            "take_profit_pts": 10.0
        }

    return None

def run_war_room_loop():
    """
    Main loop running continuously to scan the order flow and execute trades.
    """
    print(f"🚀 AI War Room Active. Monitoring {SYMBOL} on Account: {TRADESEA_ACCOUNT_ID}...")
    
    # Mock order flow data for demonstration (replace with live CCXT / Broker feed data)
    mock_depth = {
        'bids': [[2650.0, 120], [2649.5, 45], [2649.0, 30]],
        'asks': [[2651.0, 35], [2651.5, 20], [2652.0, 15]]
    }
    mock_trades = [
        {'side': 'buy', 'amount': 15, 'price': 2650.5},
        {'side': 'buy', 'amount': 25, 'price': 2650.6},
        {'side': 'sell', 'amount': 5, 'price': 2650.4}
    ]

    try:
        while True:
            # Step A: Fetch Microstructure Metrics from Order Flow Engine
            metrics = order_flow.calculate_futures_microstructure(mock_depth, mock_trades)

            # Step B: Evaluate Trading Strategy
            trade_signal = evaluate_trade_setup(metrics)

            # Step C: Execute Trade if Setup is Approved
            if trade_signal:
                print(f"⚡ HIGH-PROBABILITY SIGNAL DETECTED: {trade_signal['reason']}")
                
                execution = bridge.place_commodity_order(
                    symbol=SYMBOL,
                    action=trade_signal["action"],
                    contracts=CONTRACTS,
                    stop_loss_pts=trade_signal["stop_loss_pts"],
                    take_profit_pts=trade_signal["take_profit_pts"]
                )
                print("Execution Status:", execution)
                
                # Pause execution loop after trade placement to prevent duplicate orders
                time.sleep(60)

            # Wait 5 seconds between scans
            time.sleep(5)

    except KeyboardInterrupt:
        print("\n⏹️ War Room Loop Stopped.")

if __name__ == "__main__":
    run_war_room_loop()
