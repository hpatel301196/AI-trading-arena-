import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import time

st.set_page_config(
    page_title="Institutional Order Flow Terminal",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("🔥 Real-Time Order Book Heatmap & Depth Terminal")

# --- SIDEBAR CONTROLS ---
st.sidebar.header("🕹️ Heatmap Settings")
symbol = st.sidebar.selectbox("Asset Symbol", ["MGC (Micro Gold)", "MCL (Micro Crude)", "SIL (Micro Silver)"])
history_length = st.sidebar.slider("Time Buffer (Snapshots)", min_value=10, max_value=50, value=25)
refresh_rate = st.sidebar.slider("Refresh Rate (Seconds)", min_value=1, max_value=10, value=3)
auto_refresh = st.sidebar.toggle("Enable Live Auto-Refresh", value=True)

# --- SIMULATED L2 ORDER BOOK DATA BUFFER ---
@st.cache_data(ttl=300)
def generate_heatmap_buffer(time_steps=25, price_center=2650.0):
    """Generates a 2D matrix of order book depth across time steps."""
    prices = np.round(np.linspace(price_center - 5.0, price_center + 5.0, 21), 2)
    timestamps = [f"T-{time_steps - i}s" for i in range(time_steps)]
    
    # Base liquidity matrix (Prices x Time)
    np.random.seed(42)
    depth_matrix = np.random.randint(10, 80, size=(len(prices), time_steps))
    
    # Inject Bid Liquidity Wall around 2646.0 and Ask Wall around 2653.5
    bid_wall_idx = np.where(prices == 2646.0)[0][0]
    ask_wall_idx = np.where(prices == 2653.5)[0][0]
    
    depth_matrix[bid_wall_idx, :] = np.random.randint(220, 310, size=time_steps) # Heavy Bids
    depth_matrix[ask_wall_idx, :] = np.random.randint(180, 250, size=time_steps) # Heavy Asks
    
    return timestamps, prices, depth_matrix

timestamps, price_levels, matrix = generate_heatmap_buffer(time_steps=history_length)

# --- TOP METRIC DISPLAY ---
m1, m2, m3, m4 = st.columns(4)
m1.metric("Current Price", f"${price_levels[10]:.2f}")
m2.metric("Primary Bid Wall", "$2,646.00", delta="310 Contracts (Strong Support)")
m3.metric("Primary Ask Wall", "$2,653.50", delta="-250 Contracts (Resistance)")
m4.metric("Order Book Imbalance", "2.14", delta="Bullish Bias")

st.markdown("---")

# --- PLOTLY HEATMAP RENDER ---
left_chart, right_summary = st.columns([3, 1])

with left_chart:
    st.subheader(f"📊 Market Depth Heatmap — {symbol}")
    
    fig = go.Figure(data=go.Heatmap(
        z=matrix,
        x=timestamps,
        y=price_levels,
        colorscale='Viridis',
        colorbar=dict(title='Contract Volume'),
        hoverongaps=False
    ))
    
    # Highlight current midpoint line
    fig.add_hline(y=2650.0, line_dash="dash", line_color="white", annotation_text="Mid Price")
    
    fig.update_layout(
        xaxis_title="Time Snapshots",
        yaxis_title="Price Level ($)",
        height=520,
        template="plotly_dark",
        margin=dict(l=20, r=20, t=30, b=20)
    )
    
    st.plotly_chart(fig, use_container_width=True)

with right_summary:
    st.subheader("🛡️ War Room Signals")
    
    st.success("🟢 **BUY ZONE DETECTED**")
    st.caption("Price approaching $2,646.00 bid liquidity wall with positive delta shift.")
    
    st.write("**Wall Proximity:** 4.0 Ticks")
    st.write("**Wall Absorption Score:** 88/100")
    st.write("**Recommended Stop Loss:** $2,644.50")
    st.write("**Recommended Take Profit:** $2,653.00")
    
    if st.button("⚡ Manual Signal Approval", use_container_width=True):
        st.toast("Trade Signal Logged into Local Audit Trail!", icon="✅")

# --- AUTO-REFRESH LOOP ---
if auto_refresh:
    time.sleep(refresh_rate)
    st.rerun()
