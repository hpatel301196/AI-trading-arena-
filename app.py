from flask import Flask, jsonify
import requests
import pandas as pd
from datetime import datetime, date
import yfinance as yf
from supabase import create_client, Client
import os
import time

app = Flask(__name__)

# -------------------------------------------------------------
# SUPABASE & TELEGRAM CREDENTIALS
# -------------------------------------------------------------
SUPABASE_URL = os.environ.get("SUPABASE_URL", "YOUR_SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "YOUR_SUPABASE_KEY")
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "YOUR_TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "YOUR_CHAT_ID")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def send_telegram_alert(message):
    try:
        if TELEGRAM_TOKEN and TELEGRAM_CHAT_ID:
            url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
            payload = {"chat_id": TELEGRAM_CHAT_ID, "text": f"⚡ **HP 24/7 Scalper Bot**\n\n{message}", "parse_mode": "Markdown"}
            requests.post(url, json=payload, timeout=5)
    except Exception as e:
        print(f"Telegram alert error: {e}")

def store_advanced_self_reflection(asset, trade_type, pnl, reflection, lesson, reward_score):
    try:
        supabase.table("system_memory_ledger").insert({
            "asset": asset, "trade_type": trade_type, "pnl": pnl,
            "reflection_notes": reflection, "lesson_learned": lesson,
            "reward_score": reward_score
        }).execute()
        send_telegram_alert(f"🧠 *Reinforcement Learning Updated*\nAsset: {asset} ({trade_type}) | PnL: `${pnl:,.2f}`\nReward Score: `{reward_score}`\nLesson: {lesson}")
    except Exception as e:
        print(f"Memory logging error: {e}")

@app.route("/run-cycle", methods=["GET"])
def run_cycle():
    try:
        # 1. Fetch live market data snapshot (BTC, ETH, Gold, Silver)
        market_data = {}
        tickers = {
            "Bitcoin": "BTC-USD",
            "Ethereum": "ETH-USD",
            "Gold": "GC=F",
            "Silver": "SI=F"
        }
        
        for name, symbol in tickers.items():
            try:
                t = yf.Ticker(symbol)
                hist_15m = t.history(period="5d", interval="15m")
                if not hist_15m.empty:
                    raw_p = float(hist_15m['Close'].iloc[-1])
                    high_low = hist_15m['High'] - hist_15m['Low']
                    atr = float(high_low.rolling(14).mean().iloc[-1])
                    if pd.isna(atr): atr = raw_p * 0.008
                    market_data[name] = {"price": round(raw_p, 2), "atr": round(atr, 4)}
                else:
                    market_data[name] = {"price": 65000.0, "atr": 500.0}
            except Exception as e:
                print(f"Error fetching {name}: {e}")
                market_data[name] = {"price": 65000.0, "atr": 500.0}

        # 2. Pull portfolio details from Supabase
        res = supabase.table("agent_portfolio").select("*").eq("agent_id", "HP_Advanced_Fund").execute()
        
        if len(res.data) == 0:
            supabase.table("agent_portfolio").insert({
                "agent_id": "HP_Advanced_Fund", "cash": 100000.0,
                "current_position": None, "trades_today": 0, "total_pnl": 0.0, "last_trade_date": str(date.today())
            }).execute()
            fund = {"cash": 100000.0, "current_position": None, "trades_today": 0, "total_pnl": 0.0}
        else:
            fund = res.data[0]

        cash = float(fund.get("cash", 100000.0))
        pos = fund.get("current_position")
        trades_today = fund.get("trades_today", 0)

        # 3. Process active position evaluation (Target / Stop-Loss check)
        if pos is not None:
            held_asset = pos["asset"]
            entry_price = float(pos["entry_price"])
            pos_type = pos.get("type", "LONG")
            units = float(pos["units"])
            current_p = market_data.get(held_asset, {"price": entry_price})["price"]
            target_p = float(pos["target_price"])
            stop_p = float(pos["stop_price"])
            
            entry_timestamp = float(pos.get("entry_timestamp", time.time()))
            trade_duration_minutes = (time.time() - entry_timestamp) / 60.0

            pnl_pct = ((current_p - entry_price) / entry_price) * 100.0 if pos_type == "LONG" else ((entry_price - current_p) / entry_price) * 100.0
            exit_triggered, exit_reason = False, ""

            if pos_type == "LONG":
                if current_p >= target_p:
                    exit_triggered, exit_reason = True, f"Dynamic Profit Target Reached (${target_p})"
                elif current_p <= stop_p:
                    exit_triggered, exit_reason = True, f"Dynamic Stop Loss Triggered (${stop_p})"
            else:
                if current_p <= target_p:
                    exit_triggered, exit_reason = True, f"Dynamic Short Target Reached (${target_p})"
                elif current_p >= stop_p:
                    exit_triggered, exit_reason = True, f"Dynamic Short Stop Loss Triggered (${stop_p})"

            if trade_duration_minutes >= 30.0 and -0.4 < pnl_pct < 0.6:
                exit_triggered, exit_reason = True, f"Time-Horizon Stagnation Release ({trade_duration_minutes:.1f}m)"

            if exit_triggered:
                realized_pnl = round((pnl_pct / 100.0) * (units * entry_price), 2)
                net_cash = round(cash + (units * current_p) if pos_type == "LONG" else cash + (units * entry_price) + (units * (entry_price - current_p)), 2)

                reward_score = 100 if realized_pnl > 0 else -50
                reflection = f"REINFORCEMENT: {pos_type} trade on {held_asset} closed at {pnl_pct:+.2f}%. Reason: {exit_reason}."
                lesson = f"24/7 autonomous worker execution validated."

                store_advanced_self_reflection(held_asset, pos_type, realized_pnl, reflection, lesson, reward_score)

                supabase.table("agent_portfolio").update({
                    "cash": net_cash, "current_position": None, "trades_today": trades_today + 1, "total_pnl": fund.get("total_pnl", 0) + realized_pnl
                }).eq("agent_id", "HP_Advanced_Fund").execute()

                supabase.table("trade_ledger_history").insert({
                    "agent_id": "HP_Advanced_Fund", "asset": held_asset, "action": f"AUTO_CLOSE_{pos_type}",
                    "size": units, "price": current_p, "pnl": realized_pnl, "trade_num": trades_today + 1
                }).execute()

                send_telegram_alert(f"🔴 *Autonomous Position Terminated: {pos_type} {held_asset}*\nRealized PnL: `${realized_pnl:,.2f}` ({pnl_pct:+.2f}%)\nReason: {exit_reason}")

        return jsonify({"status": "success", "message": "24/7 scalper cycle evaluated cleanly."}), 200

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
