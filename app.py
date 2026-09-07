import streamlit as st
import plotly.graph_objects as go
from order_flow_engine import OrderFlowEngine

# 1. Fetch live order flow metrics
engine = OrderFlowEngine(symbol='BTC/USDT')
metrics = engine.analyze_market_depth_and_delta()

st.title("Market Microstructure & Order Flow")

# 2. Display the Order Flow Imbalance Badge
col1, col2, col3, col4 = st.columns(4)

imbalance_color = "normal" if metrics['imbalance'] >= 1.0 else "inverse"
col1.metric("Order Book Imbalance", f"{metrics['imbalance']}x", delta="Bullish Bias" if metrics['imbalance'] >= 1.0 else "Bearish Bias")
col2.metric("Point of Control (POC)", f"${metrics['poc_price']}")
col3.metric("Buy Wall (Support)", f"${metrics['top_buy_wall_price']}", delta=f"{metrics['top_buy_wall_size']} Vol")
col4.metric("Sell Wall (Resistance)", f"${metrics['top_sell_wall_price']}", delta=f"{metrics['top_sell_wall_size']} Vol")

# 3. Draw Chart with Depth Walls and Point of Control (POC)
fig = go.Figure()

# Add Point of Control Line
fig.add_hline(
    y=metrics['poc_price'], 
    line_dash="dash", 
    line_color="gold", 
    annotation_text=f"POC: ${metrics['poc_price']}", 
    annotation_position="bottom right"
)

# Add Buy Wall Line (Support)
if metrics['top_buy_wall_price'] > 0:
    fig.add_hline(
        y=metrics['top_buy_wall_price'], 
        line_color="#00E676", 
        line_width=3,
        annotation_text=f"BUY WALL: ${metrics['top_buy_wall_price']}", 
        annotation_position="top left"
    )

# Add Sell Wall Line (Resistance)
if metrics['top_sell_wall_price'] > 0:
    fig.add_hline(
        y=metrics['top_sell_wall_price'], 
        line_color="#FF5252", 
        line_width=3,
        annotation_text=f"SELL WALL: ${metrics['top_sell_wall_price']}", 
        annotation_position="bottom left"
    )

fig.update_layout(
    title="Price Chart with Institutional Walls & POC",
    template="plotly_dark",
    height=500
)

st.plotly_chart(fig, use_container_width=True)
