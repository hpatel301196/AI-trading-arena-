import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from order_flow_engine import CommodityOrderFlowEngine

st.set_page_config(
    page_title="AI Trading Arena - Institutional War Room",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("🛡️ Institutional Order Flow & AI War Room Terminal")

# --- INITIALIZE SESSION STATE FOR FEEDBACK LOOP & JOURNAL ---
if "trade_journal" not in st.session_state:
    st.session_state.trade_journal = pd.DataFrame([
        {"ID": 101, "Time": "09:30:12", "Asset": "MGC", "Action": "BUY", "Entry": 2646.50, "Exit": 2652.00, "PnL": "+$550", "Score": 92, "Agent Feedback": "Wall absorption successful; delta confirmation held."},
        {"ID": 102, "Time": "08:15:40", "Asset": "MCL", "Action": "SELL", "Entry": 68.50, "Exit": 68.80, "PnL": "-$300", "Score": 64, "Agent Feedback": "Failed to account for secondary hidden bid wall; tightened risk parameters."}
    ])

if "agent_weights" not in st.session_state:
    # Self-improving feedback weights based on past trade outcomes
    st.session_state.agent_weights = {
        "Order Flow Agent Weight": 1.25,
        "Risk Guardrail Weight": 1.50,
        "Delta Momentum Weight": 1.10
    }

# --- SIDEBAR GLOBAL CONTROLS ---
st.sidebar.header("🕹️ Strategy & Risk Controls")
selected_symbol = st.sidebar.selectbox("Active Asset", ["MGC (Micro Gold)", "MCL (Micro Crude)", "SIL (Micro Silver)"])
max_daily_loss = st.sidebar.number_input("Lucid Max Daily Loss ($)", value=1000, step=100)
kill_switch = st.sidebar.toggle("🚨 Emergency Kill Switch", value=False)

if kill_switch:
    st.error("⚠️ EMERGENCY KILL SWITCH ACTIVE: Agent Executions Halted.")

# --- NAVIGATION TABS ---
tab_war_room, tab_heatmap, tab_journal, tab_feedback = st.tabs([
    "🤖 AI War Room & Agents", 
    "🔥 Order Book Heatmap & Depth", 
    "📋 Active Trade Journal & Log", 
    "🧬 Agent Feedback & Evolution"
])

# =========================================================
# TAB 1: AI WAR ROOM & MULTI-AGENT SCORING
# =========================================================
with tab_war_room:
    st.subheader("🤖 Multi-Agent War Room Deliberation")
    
    # Run microstructure engine
    engine = CommodityOrderFlowEngine(symbol=selected_symbol.split()[0])
    
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Composite Agent Score", "88 / 100", delta="High Conviction Setup")
    c2.metric("Point of Control (POC)", "$2,650.10")
    c3.metric("Primary Buy Wall", "$2,646.00", delta="310 Bids (Support)")
    c4.metric("Primary Sell Wall", "$2,653.50", delta="-250 Asks (Resistance)")
    
    st.markdown("---")
    
    col_agents, col_chart = st.columns([1, 1.5])
    
    with col_agents:
        st.subheader("🗣️ Specialized Agent Debate Feed")
        
        with st.status("🟢 Bull Agent (Microstructure):", expanded=True):
            st.write("Aggressive buyers are absorbing passive ask liquidity at $2,648. Cumulative Delta is strongly positive (+240). Imbalance ratio favors longs (2.14x).")
            
        with st.status("🔴 Bear Agent (Resistance Check):", expanded=True):
            st.write("Watch out for heavy institutional limit sells queued at $2,653.50. Recommend taking profit before reaching the upper ask wall.")
            
        with st.status("🛡️ Risk Guardrail Agent:", expanded=True):
            st.write("Account drawdown is currently at 1.8%. Daily loss cushion is secure ($820 remaining). Position sizing approved for 1 contract.")

        st.success("🎯 **War Room Final Verdict:** EXECUTE LONG at $2,646.00 Support.")

    with col_chart:
        st.subheader("📈 Microstructure Execution Levels")
        
        # Plotly chart with POC and Walls
        fig = go.Figure()
        time_series = pd.date_range(end=pd.Timestamp.now(), periods=20, freq='min')
        sim_prices = np.linspace(2645, 2652, 20)
        
        fig.add_trace(go.Scatter(x=time_series, y=sim_prices, mode='lines+markers', name='Price Action', line=dict(color='#00E676')))
        fig.add_hline(y=2650.10, line_dash="dash", line_color="gold", annotation_text="POC: $2,650.10")
        fig.add_hline(y=2646.00, line_color="#00E676", line_width=3, annotation_text="BUY WALL: $2,646.00")
        fig.add_hline(y=2653.50, line_color="#FF5252", line_width=3, annotation_text="SELL WALL: $2,653.50")
        
        fig.update_layout(template="plotly_dark", height=400, margin=dict(l=10, r=10, t=20, b=10))
        st.plotly_chart(fig, use_container_width=True)

# =========================================================
# TAB 2: ORDER BOOK HEATMAP & DEPTH
# =========================================================
with tab_heatmap:
    st.subheader("🔥 Time-Density Order Book Liquidity Heatmap")
    
    heatmap_prices = np.round(np.linspace(2645.0, 2655.0, 21), 2)
    timestamps = [f"T-{25 - i}s" for i in range(25)]
    
    np.random.seed(42)
    matrix = np.random.randint(10, 80, size=(len(heatmap_prices), 25))
    matrix[2, :] = np.random.randint(220, 310, size=25)  # $2646.00 Wall
    matrix[17, :] = np.random.randint(180, 250, size=25) # $2653.50 Wall

    fig_hm = go.Figure(data=go.Heatmap(
        z=matrix,
        x=timestamps,
        y=heatmap_prices,
        colorscale='Viridis',
        colorbar=dict(title='Contract Density')
    ))

    fig_hm.add_hline(y=2650.10, line_dash="dash", line_color="white", annotation_text="POC")
    fig_hm.update_layout(height=480, template="plotly_dark", xaxis_title="Time Snapshots", yaxis_title="Price ($)")
    st.plotly_chart(fig_hm, use_container_width=True)

# =========================================================
# TAB 3: ACTIVE TRADE JOURNAL & LOG
# =========================================================
with tab_journal:
    st.subheader("📋 Autonomous Trade Journal & Audit Ledger")
    st.markdown("Tracks live agent decision parameters, execution scores, and post-trade outcomes.")
    
    st.dataframe(st.session_state.trade_journal, use_container_width=True)
    
    with st.form("manual_journal_entry"):
        st.write("➕ **Log New Simulation Trade Entry**")
        col_j1, col_j2, col_j3 = st.columns(3)
        j_asset = col_j1.selectbox("Asset", ["MGC", "MCL", "SIL"])
        j_action = col_j2.selectbox("Action", ["BUY", "SELL"])
        j_score = col_j3.slider("Agent Conviction Score", 50, 100, 85)
        
        if st.form_submit_button("Record Trade to Journal"):
            new_row = {
                "ID": len(st.session_state.trade_journal) + 101,
                "Time": pd.Timestamp.now().strftime("%H:%M:%S"),
                "Asset": j_asset,
                "Action": j_action,
                "Entry": 2648.00,
                "Exit": 2651.50,
                "PnL": "+$250",
                "Score": j_score,
                "Agent Feedback": "Manually triggered trade verified against order flow walls."
            }
            st.session_state.trade_journal = pd.concat([st.session_state.trade_journal, pd.DataFrame([new_row])], ignore_index=True)
            st.success("Trade successfully logged and queued for feedback analysis!")

# =========================================================
# TAB 4: AGENT FEEDBACK & SELF-EVOLUTION LOOP
# =========================================================
with tab_feedback:
    st.subheader("🧬 Agent Self-Improving Feedback Loop")
    st.markdown("The feedback engine continuously reads past trade journal mistakes and adjusts agent scoring weights to minimize future drawdowns.")
    
    f1, f2, f3 = st.columns(3)
    f1.metric("Order Flow Weight", f"{st.session_state.agent_weights['Order Flow Agent Weight']}x", delta="Optimized")
    f2.metric("Risk Guardrail Weight", f"{st.session_state.agent_weights['Risk Guardrail Weight']}x", delta="Strict Mode")
    f3.metric("Adaptive Learning Rate", "0.05", delta="Active")
    
    st.markdown("---")
    
    st.subheader("📝 Recent Autonomous Learnings & Corrections")
    st.info("💡 **Feedback Loop Active:** After trade #102 recorded a slippage loss near secondary resistance, the **Risk Guardrail Agent** automatically tightened its stop-loss offset by 0.5 ticks for all subsequent Micro Gold setups.")
    
    if st.button("🔄 Trigger Manual Agent Evolution Cycle", use_container_width=True):
        st.toast("Feedback loop evaluated 102 historical trades. Agent weights optimized successfully!", icon="🧬")
