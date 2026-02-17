import sys
import os
import json
import time
import yfinance as yf
from datetime import datetime, timedelta
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))
from src.engine.alpha_brain import AlphaBrain

def fetch_live_data():
    """Fetches near real-time data for NQ, ES, and YM from Yahoo Finance."""
    assets = {
        'NQ': 'NQ=F',
        'ES': 'ES=F',
        'YM': 'YM=F'
    }
    
    results = {}
    for key, symbol in assets.items():
        try:
            ticker = yf.Ticker(symbol)
            
            # --- MONTHLY LAYER (Fetch 3 Months) ---
            monthly_data = ticker.history(period='3mo', interval='1d')
            if not monthly_data.empty:
                monthly_history = monthly_data
            else:
                monthly_history = None
            
            # --- WEEKLY LAYER (Fetch 5 Days) ---
            weekly_data = ticker.history(period='5d', interval='1d')
            if not weekly_data.empty:
                weekly_history = weekly_data
            else:
                weekly_history = None

            # --- DAILY LIVE LAYER (1D Fetch) ---
            data_1d = ticker.history(period='1d', interval='1m')
            if not data_1d.empty:
                 price = data_1d['Close'].iloc[-1]
                 open_price = data_1d['Open'].iloc[0] # Open of the session
                 o2c = (price - open_price) / open_price
            else:
                 # Fallback to the Daily history
                 data_1d = ticker.history(period='1d')
                 price = data_1d['Close'].iloc[-1]
                 open_price = data_1d['Open'].iloc[0]
                 o2c = (price - open_price) / open_price

            results[key] = {
                'price': round(float(price), 2),
                'live_o2c': o2c,
                'monthly_history': monthly_history,
                'weekly_history': weekly_history
            }
        except Exception as e:
            print(f"Error fetching {key}: {e}")
            
    return results

def run_monitor_loop():
    """Main loop that generates the live_state.json for the dashboard."""
    output_path = Path(__file__).parent / "data" / "alpha_state.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    print("[*] SPEC RESEARCH v4.0 (Layered Alpha Monitor) Started.")
    
    while True:
        try:
            live_data = fetch_live_data()
            states = []
            
            for asset, market_data in live_data.items():
                # Pass the structured data to the Refactored AlphaBrain
                state = AlphaBrain.calculate_state(asset, market_data)
                if state:
                    states.append(state)
            
            final_report = {
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'system_status': 'ACTIVE',
                'assets': states
            }
            
            with open(output_path, 'w') as f:
                json.dump(final_report, f, indent=4, default=str) # Use default=str for DataFrames/Dates
                
            print(f"[{final_report['timestamp']}] Alpha State Updated.")
            
            # Update every 60 seconds
            time.sleep(60)
            
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"Error in monitor loop: {e}")
            time.sleep(30) # Wait and retry

if __name__ == "__main__":
    from datetime import datetime
    run_monitor_loop()
