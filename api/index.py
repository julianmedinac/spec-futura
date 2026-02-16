from http.server import BaseHTTPRequestHandler
import json
import sys
import os

# Add the current directory to sys.path so we can import src
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.engine.alpha_brain import AlphaBrain
from src.data.data_loader import DataLoader
import pandas as pd
from datetime import datetime

# Vercel Handler
class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()

        # Simulate Live Monitor Logic for a single request
        loader = DataLoader()
        assets = ['NQ', 'ES', 'YM']
        results = []

        for asset in assets:
            # 1. Fetch History (Optimized for Serverless - No caching if possible or small range)
            # We need enough history for Weekly/Monthly (e.g. 1 year)
            # In Vercel, this might take a few seconds.
            try:
                # Override cache in DataLoader if needed by not saving, but DataLoader saves by default.
                # Vercel filesystem is read-only except /tmp. 
                # DataLoader likely tries to save to 'data/raw/'. We should handle this.
                # For now, let's assume yfinance works and we catch errors.
                
                # Custom download logic to bypass file saving in DataLoader if it's strictly local
                # Or just use yfinance direct. 
                # Actually, DataLoader as is might fail if 'data/raw' doesn't exist and can't be created.
                # Let's import yfinance directly here for safety.
                import yfinance as yf
                
                ticker_map = {'NQ': 'NQ=F', 'ES': 'ES=F', 'YM': 'YM=F', 'GC': 'GC=F'}
                data = yf.download(ticker_map[asset], period="2y", interval="1d", progress=False)
                
                if data.empty:
                     results.append({'asset': asset, 'error': 'No Data'})
                     continue
                
                # Standardize columns (lowercase)
                data.columns = [c.lower() for c in data.columns]
                
                # Prepare Inputs for AlphaBrain
                monthly_history = data.copy()
                # Rename columns for Brain: 'High', 'Low', 'Close', 'Open' (case sensitive in Brain?)
                # AlphaBrain uses 'High', 'Low' (Title Case) in _calculate_monthly_layer lines.
                monthly_history.columns = [c.capitalize() for c in monthly_history.columns]
                
                weekly_history = monthly_history.copy() # Same daily data used for weekly layer aggregation?
                # Actually _calculate_weekly_layer uses daily data to find Mondays.
                
                # Live O2C (Latest Candle)
                latest = data.iloc[-1]
                current_price = latest['close']
                o2c = (latest['close'] - latest['open']) / latest['open']
                
                context = {
                    'monthly_history': monthly_history,
                    'weekly_history': weekly_history,
                    'live_o2c': o2c,
                    'price': current_price
                }
                
                state = AlphaBrain.calculate_state(asset, context)
                if state:
                    results.append(state)
                    
            except Exception as e:
                results.append({'asset': asset, 'error': str(e)})

        response = {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'system_status': 'ACTIVE (VERCEL)',
            'assets': results
        }
        
        self.wfile.write(json.dumps(response).encode('utf-8'))
        return
