import ccxt
import pandas as pd
import numpy as np
from supabase import create_client, Client
import os

class OrderFlowEngine:
    def __init__(self, exchange_id='binance', symbol='BTC/USDT'):
        self.exchange = getattr(ccxt, exchange_id)({'enableRateLimit': True})
        self.symbol = symbol

    def analyze_market_depth_and_delta(self, wall_multiplier=3.0, trade_limit=500):
        """
        Fetches Order Book Depth + Trade Ticks and calculates:
        1. Buy/Sell Liquidity Walls
        2. Volume Profile Point of Control (POC)
        3. Order Flow Delta (Aggressive Buying vs Selling)
        """
        # 1. Fetch Order Book Depth
        order_book = self.exchange.fetch_order_book(self.symbol, limit=100)
        bids = pd.DataFrame(order_book['bids'], columns=['price', 'size'])
        asks = pd.DataFrame(order_book['asks'], columns=['price', 'size'])

        # Identify Liquidity Walls (orders > 3x average depth)
        avg_bid_size = bids['size'].mean()
        avg_ask_size = asks['size'].mean()

        buy_walls = bids[bids['size'] >= (avg_bid_size * wall_multiplier)]
        sell_walls = asks[asks['size'] >= (avg_ask_size * wall_multiplier)]

        top_buy_wall = buy_walls.iloc[0].to_dict() if not buy_walls.empty else {"price": 0.0, "size": 0.0}
        top_sell_wall = sell_walls.iloc[0].to_dict() if not sell_walls.empty else {"price": 0.0, "size": 0.0}

        # Order Book Imbalance Ratio
        imbalance = round(bids['size'].sum() / (asks['size'].sum() + 1e-6), 2)

        # 2. Fetch Recent Executed Trades for Delta & POC
        trades = self.exchange.fetch_trades(self.symbol, limit=trade_limit)
        trades_df = pd.DataFrame(trades)

        # Delta Calculation: Buy side volume minus Sell side volume
        buy_vol = trades_df[trades_df['side'] == 'buy']['amount'].sum()
        sell_vol = trades_df[trades_df['side'] == 'sell']['amount'].sum()
        delta = round(buy_vol - sell_vol, 4)

        # Point of Control (POC) Calculation
        counts, bin_edges = np.histogram(trades_df['price'], bins=20, weights=trades_df['amount'])
        poc_idx = np.argmax(counts)
        poc_price = round((bin_edges[poc_idx] + bin_edges[poc_idx + 1]) / 2.0, 2)

        return {
            "symbol": self.symbol,
            "top_buy_wall_price": top_buy_wall['price'],
            "top_buy_wall_size": top_buy_wall['size'],
            "top_sell_wall_price": top_sell_wall['price'],
            "top_sell_wall_size": top_sell_wall['size'],
            "poc_price": poc_price,
            "delta_volume": delta,
            "imbalance": imbalance
        }

    def save_to_supabase(self, metrics, supabase_url: str, supabase_key: str):
        """Saves calculated metrics directly to Supabase."""
        supabase: Client = create_client(supabase_url, supabase_key)
        
        payload = {
            "symbol": metrics["symbol"],
            "buy_wall_price": metrics["top_buy_wall_price"],
            "buy_wall_size": metrics["top_buy_wall_size"],
            "sell_wall_price": metrics["top_sell_wall_price"],
            "sell_wall_size": metrics["top_sell_wall_size"],
            "poc_price": metrics["poc_price"],
            "delta_volume": metrics["delta_volume"],
            "order_book_imbalance": metrics["imbalance"]
        }
        
        supabase.table("order_flow_metrics").insert(payload).execute()


# Example Usage (for testing locally or in background runner):
if __name__ == "__main__":
    engine = OrderFlowEngine(symbol='BTC/USDT')
    data = engine.analyze_market_depth_and_delta()
    print("Market Depth & Delta Metrics:", data)
