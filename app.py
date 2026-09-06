import streamlit as st
import pandas as pd
import yfinance as yf
import requests
import json
import random

# Streamlit Page Config
st.set_page_config(page_title="AI Trading Arena", layout="wide")

st.title("🤖 Autonomous AI Multi-Agent Trading Arena")
st.caption("Live asset tracking, simulated brokerage, and evolutionary agent competition ($0 Cloud Hosted)")

# -------------------------------------------------------------
# 1. LIVE MARKET DATA ENGINE ($0 Fee)
# -------------------------------------------------------------
@st.cache_data(ttl=15)
def fetch_live_prices():
    tickers = {
        "BTC-USD": "Bitcoin",
        "ETH-USD": "Ethereum",
        "GC=F": "Gold",
        "SI=F": "Silver"
    }
    data = {}
    for symbol, name in tickers.items():
        try:
            ticker = yf.Ticker(symbol)
            price = ticker.fast_info['lastPrice']
            data[name] = round(price, 2)
        except:
            data[name] = 0.0
    return data

live_prices = fetch_live_prices()

# Display Live Price Header
cols = st.columns(4)
for i, (asset, price) in enumerate(live_prices.items()):
    cols[i].metric(label=f"Live {asset}", value=f"${price:,.2f}")

st.divider()

# -------------------------------------------------------------
# 2. VIRTUAL BROKERAGE & SLIPPAGE SIMULATOR
# -------------------------------------------------------------
class VirtualBrokerage:
    def __init__(self, agent_id, cash=100000.0, fee_rate=0.001):
        self.agent_id = agent_id
        self.cash = cash
        self.fee_rate = fee_rate

    def execute_order(self, ticker, action, amount, market_price):
        # Simulated slippage factor (0.05% base + random depth variance)
        slippage = market_price * (0.0005 + random.uniform(0, 0.001))
        effective_price = market_price + slippage if action == "BUY" else market_price - slippage
        
        gross = amount * effective_price
        fee = gross * self.fee_rate
        
        return {
            "agent": self.agent_id,
            "action": action,
            "ticker": ticker,
            "effective_price": round(effective_price, 2),
            "fee": round(fee, 2),
            "status": "EXECUTED"
        }

# -------------------------------------------------------------
# 3. DUMMY AGENT EVALUATION ENGINE
# -------------------------------------------------------------
agents = ["Agent_Alpha_Quant", "Agent_Beta_Sentiment", "Agent_Gamma_Risk", "Agent_Delta_Hybrid"]

if st.button("⚡ Trigger Hourly AI Market Scan & Agent Decisions"):
    st.subheader("Latest Agent Trade Executions")
    trade_results = []
    votes = {"BUY": 0, "SELL": 0, "HOLD": 0}

    for agent_id in agents:
        broker = VirtualBrokerage(agent_id)
        # Simulate decision logic
        decision = random.choice(["BUY", "SELL", "HOLD"])
        votes[decision] += 1
        
        if decision in ["BUY", "SELL"]:
            asset = random.choice(["Bitcoin", "Gold"])
            price = live_prices.get(asset, 1000.0)
            result = broker.execute_order(asset, decision, 0.1, price)
            trade_results.append(result)

    # Display Trade Logs
    st.dataframe(pd.DataFrame(trade_results), use_container_width=True)

    # -------------------------------------------------------------
    # 4. ENSEMBLE VOTING CONSENSUS
    # -------------------------------------------------------------
    consensus = max(votes, key=votes.get)
    st.subheader("🎯 Ensemble Consensus Signal")
    st.info(f"Consensus Direction: **{consensus}** (Votes: {votes})")

st.divider()

# -------------------------------------------------------------
# 5. LEADERBOARD & PERFORMANCE TRACKING
# -------------------------------------------------------------
st.subheader("🏆 Daily Leaderboard (30-Day Simulated Net Worth)")

# Simulated agent portfolios
leaderboard_data = {
    "Agent ID": agents,
    "Strategy Profile": ["Technical / EMA", "News Sentiment", "Mean Reversion", "Hybrid LLM"],
    "Starting Cash": ["$100,000"] * 4,
    "Current Portfolio Value": [
        f"${100000 + random.randint(-2000, 5000):,.2f}" for _ in agents
    ],
    "Sharpe Ratio": [1.82, 1.15, 0.94, 2.05]
}

st.table(pd.DataFrame(leaderboard_data))
