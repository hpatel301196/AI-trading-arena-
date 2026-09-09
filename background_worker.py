import time
import requests
import random
from datetime import datetime, date
import yfinance as yf
from supabase import create_client, Client
import os

# -------------------------------------------------------------
# 1. SETUP ENVIRONMENT & SUPABASE CONNECTION
# -------------------------------------------------------------
# Use environmental variables or replace strings with your Supabase credentials
SUPABASE_URL = os.environ.get("SUPABASE_URL", "YOUR_SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "YOUR_SUPABASE_KEY")
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "YOUR_TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "YOUR_CHAT_ID")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def send_telegram_alert(message):
    try:
        if TELEGRAM_TOKEN and TELEGRAM_CHAT_ID:
            url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
            payload = {"chat_id": TELEGRAM_CHAT_ID, "text": f"🤖 **HP 24/7 Autonomous Worker**\n\n{message}", "parse_mode": "Markdown"}
            requests.post(url, json=payload, timeout=5)
    except Exception as e:
        print(f"Telegram alert error: {e}")

def fetch_market_data():
    market_data = {}
    tickers = {"Bitcoin": "BTC-USD", "Ethereum": "ETH-USD", "Gold": "GC=F", "Silver": "SI=F"}
    
    for name, symbol in tickers.items():
        try:
            t = yf.Ticker(symbol)
            hist = t.history(period="5d", interval="15m")
            if not hist.empty:
                raw_p = float(hist['Close'].iloc[-1])
                high_low = hist['High'] - hist['Low']
                atr = float(high_low.rolling(14).mean().iloc[-1])
                if pd.isna(atr): atr = raw_p * 0.008
                vol_baseline = float(high_low.rolling(50).mean().iloc[-1]) if len(high_low) >= 50 else atr
                vol_ratio = atr / vol_baseline if vol_baseline > 0 else 1.0
                est_poc = raw_p - (atr * 0.1)
            else:
                raw_p, atr, vol_ratio, est_poc = 65000.0, 500.0, 1.0, 64500.0
                
            market_data[name] = {"price": round(raw_p, 2), "atr": round(atr, 4), "vol_ratio": round(vol_ratio, 2), "poc": round(est_poc, 2)}
        except Exception as e:
            print(f"Error fetching {name}: {e}")
    return market_data

def get_reinforcement_adjustment():
    try:
        res = supabase.table("system_memory_ledger").select("*").order("id", desc=True).limit(5).execute()
        lessons = res.data
        if not lessons: return 0.0
        recent_pnl = sum([float(l.get("pnl", 0)) for l in lessons])
        if recent_pnl > 0: return 4.0
        elif recent_pnl < 0: return -6.0
    except:
        pass
    return 0.0

def run_autonomous_loop():
    print("⚡ HP 24/7 Autonomous Worker Started...")
    send_telegram_alert("⚡ Autonomous Trading Worker Online & Scanning Markets.")
    
    while True:
        try:
            market_snapshot = fetch_market_data()
            reinforcement_bias = get_reinforcement_adjustment()
            
            # Fetch Portfolio State from Supabase
            res = supabase.table("agent_portfolio").select("*").eq("agent_id", "HP_Advanced_Fund").execute()
            if len(res.data) == 0:
                supabase.table("agent_portfolio").insert({
                    "agent_id": "HP_Advanced_Fund", "cash": 100000.0,
                    "current_position": None, "trades_today": 0, "total_pnl": 0.0, "last_trade_date": str(date.today())
                }).execute()
                continue
                
            fund = res.data[0]
            cash = float(fund.get("cash", 100000.0))
            pos = fund.get("current_position")
            trades_today = fund.get("trades_today", 0)

            # 1. Manage Active Positions (Check Stops & Targets)
            if pos is not None:
                held_asset = pos["asset"]
                entry_price = float(pos["entry_price"])
                pos_type = pos.get("type", "LONG")
                units = float(pos["units"])
                current_p = market_snapshot.get(held_asset, {"price": entry_price})["price"]
                target_p = float(pos["target_price"])
                stop_p = float(pos["stop_price"])

                pnl_pct = ((current_p - entry_price) / entry_price) * 100.0 if pos_type == "LONG" else ((entry_price - current_p) / entry_price) * 100.0
                exit_triggered, exit_reason = False, ""

                if pos_type == "LONG":
                    if current_p >= target_p: exit_triggered, exit_reason = True, f"Target Reached (${target_p})"
                    elif current_p <= stop_p: exit_triggered, exit_reason = True, f"Stop Loss Triggered (${stop_p})"
                else:
                    if current_p <= target_p: exit_triggered, exit_reason = True, f"Short Target Reached (${target_p})"
                    elif current_p >= stop_p: exit_triggered, exit_reason = True, f"Short Stop Loss Triggered (${stop_p})"

                if exit_triggered:
                    realized_pnl = round((pnl_pct / 100.0) * (units * entry_price), 2)
                    net_cash = round(cash + (units * current_p) if pos_type == "LONG" else cash + (units * entry_price) + (units * (entry_price - current_p)), 2)

                    # Store memory reflection
                    reward = 100 if realized_pnl > 0 else -50
                    supabase.table("system_memory_ledger").insert({
                        "asset": held_asset, "trade_type": pos_type, "pnl": realized_pnl,
                        "reflection_notes": f"Autonomous close: {exit_reason}", "lesson_learned": "24/7 worker rule validated", "reward_score": reward
                    }).execute()

                    # Update portfolio
                    supabase.table("agent_portfolio").update({
                        "cash": net_cash, "current_position": None, "trades_today": trades_today + 1, "total_pnl": fund.get("total_pnl", 0) + realized_pnl
                    }).eq("agent_id", "HP_Advanced_Fund").execute()

                    supabase.table("trade_ledger_history").insert({
                        "agent_id": "HP_Advanced_Fund", "asset": held_asset, "action": f"AUTO_CLOSE_{pos_type}",
                        "size": units, "price": current_p, "pnl": realized_pnl, "trade_num": trades_today + 1
                    }).execute()

                    send_telegram_alert(f"🔴 *Autonomous Position Closed: {pos_type} {held_asset}*\nRealized PnL: `${realized_pnl:,.2f}` ({pnl_pct:+.2f}%)\nReason: {exit_reason}")

            # 2. Look for New Entries if Flat
            elif pos is None and trades_today < 12:
                for asset, data in market_snapshot.items():
                    price = data["price"]
                    atr = data["atr"]
                    vol_ratio = data["vol_ratio"]
                    
                    # Simulated swarm intelligence check
                    score = int(50 + (vol_ratio * 10) + reinforcement_bias)
                    score = max(5, min(95, score))
                    
                    if score >= 68: # BUY SIGNAL
                        limit_entry = round(price - (atr * 0.2), 2)
                        target_price = round(limit_entry + (atr * 2.2), 2)
                        stop_price = round(limit_entry - (atr * 1.1), 2)
                        
                        kelly_fraction = 0.25
                        allocated_capital = cash * kelly_fraction
                        units = round(allocated_capital / limit_entry, 4)
                        
                        new_pos = {
                            "asset": asset, "entry_price": limit_entry, "units": units,
                            "type": "LONG", "persona": "AUTONOMOUS_SWARM",
                            "target_price": target_price, "stop_price": stop_price,
                            "entry_timestamp": time.time()
                        }
                        
                        supabase.table("agent_portfolio").update({
                            "cash": round(cash - allocated_capital, 2), "current_position": new_pos, "trades_today": trades_today + 1
                        }).eq("agent_id", "HP_Advanced_Fund").execute()
                        
                        supabase.table("trade_ledger_history").insert({
                            "agent_id": "HP_Advanced_Fund", "asset": asset, "action": f"AUTO_KELLY_LONG_{asset}",
                            "size": units, "price": limit_entry, "pnl": 0.0, "trade_num": trades_today + 1
                        }).execute()

                        send_telegram_alert(f"🟢 *Autonomous Kelly Long: {asset}*\nLimit Entry: `${limit_entry:,.2f}`\nTarget: `${target_price:,.2f}` | Stop: `${stop_price:,.2f}`")
                        break
                        
        except Exception as e:
            print(f"Worker loop error: {e}")
            
        time.sleep(60) # Runs every 60 seconds

if __name__ == "__main__":
    run_autonomous_loop()
