import ccxt
import pandas as pd
import numpy as np

class CommodityOrderFlowEngine:
    def __init__(self, symbol='MGC'):
        # Mapping symbol for data feed (e.g., Micro Gold or Crude)
        self.symbol = symbol

    def calculate_futures_microstructure(self, depth_data, trades_data):
        """
        Processes Level 2 Depth and Trades for Commodities (Gold / Oil).
        """
        # 1. Bids & Asks Depth
        bids = pd.DataFrame(depth_data['bids'], columns=['price', 'size'])
        asks = pd.DataFrame(depth_data['asks'], columns=['price', 'size'])

        # CME Liquidity Wall Thresholds (Orders 3.5x larger than average)
        buy_walls = bids[bids['size'] >= (bids['size'].mean() * 3.5)]
        sell_walls = asks[asks['size'] >= (asks['size'].mean() * 3.5)]

        # 2. Cumulative Delta for Commodities
        trades_df = pd.DataFrame(trades_data)
        buy_vol = trades_df[trades_df['side'] == 'buy']['amount'].sum()
        sell_vol = trades_df[trades_df['side'] == 'sell']['amount'].sum()
        delta = round(buy_vol - sell_vol, 2)

        # 3. Volume Point of Control (POC)
        counts, bin_edges = np.histogram(trades_df['price'], bins=15, weights=trades_df['amount'])
        poc_idx = np.argmax(counts)
        poc_price = round((bin_edges[poc_idx] + bin_edges[poc_idx + 1]) / 2.0, 2)

        return {
            "symbol": self.symbol,
            "buy_wall": buy_walls.iloc[0].to_dict() if not buy_walls.empty else None,
            "sell_wall": sell_walls.iloc[0].to_dict() if not sell_walls.empty else None,
            "poc_price": poc_price,
            "delta": delta,
            "imbalance": round(bids['size'].sum() / (asks['size'].sum() + 1e-6), 2)
        }
