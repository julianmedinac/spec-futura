from http.server import BaseHTTPRequestHandler
import json
import yfinance as yf
from datetime import datetime, timedelta

# ============================================================
# AUDITED PROBABILITY TABLES
# EVERY number here MUST have a source in the repo
# ============================================================

# Source: output/charts/strategy/W2/ (complete 12-month matrices)
# Based on 2000-2026 History | * = >80% Win Rate
W2_MONTHLY = {
    'NQ': {
        1:  {'bull': {'prob_green': 78, 'prob_high': 89}, 'bear': {'prob_red': 75, 'prob_low': 88}},
        2:  {'bull': {'prob_green': 67, 'prob_high': 87}, 'bear': {'prob_red': 91, 'prob_low': 55}},
        3:  {'bull': {'prob_green': 91, 'prob_high': 82}, 'bear': {'prob_red': 57, 'prob_low': 86}},
        4:  {'bull': {'prob_green': 86, 'prob_high': 71}, 'bear': {'prob_red': 64, 'prob_low': 73}},
        5:  {'bull': {'prob_green': 92, 'prob_high': 92}, 'bear': {'prob_red': 62, 'prob_low': 62}},
        6:  {'bull': {'prob_green': 92, 'prob_high': 83}, 'bear': {'prob_red': 69, 'prob_low': 85}},
        7:  {'bull': {'prob_green': 84, 'prob_high': 89}, 'bear': {'prob_red': 50, 'prob_low': 67}},
        8:  {'bull': {'prob_green': 71, 'prob_high': 86}, 'bear': {'prob_red': 64, 'prob_low': 64}},
        9:  {'bull': {'prob_green': 77, 'prob_high': 85}, 'bear': {'prob_red': 85, 'prob_low': 85}},
        10: {'bull': {'prob_green': 75, 'prob_high': 94}, 'bear': {'prob_red': 60, 'prob_low': 50}},
        11: {'bull': {'prob_green': 94, 'prob_high': 88}, 'bear': {'prob_red': 60, 'prob_low': 90}},
        12: {'bull': {'prob_green': 85, 'prob_high': 85}, 'bear': {'prob_red': 77, 'prob_low': 85}},
    },
    'ES': {
        1:  {'bull': {'prob_green': 67, 'prob_high': 83}, 'bear': {'prob_red': 75, 'prob_low': 88}},
        2:  {'bull': {'prob_green': 80, 'prob_high': 80}, 'bear': {'prob_red': 82, 'prob_low': 55}},
        3:  {'bull': {'prob_green': 91, 'prob_high': 100}, 'bear': {'prob_red': 64, 'prob_low': 79}},
        4:  {'bull': {'prob_green': 79, 'prob_high': 79}, 'bear': {'prob_red': 36, 'prob_low': 64}},
        5:  {'bull': {'prob_green': 92, 'prob_high': 77}, 'bear': {'prob_red': 50, 'prob_low': 67}},
        6:  {'bull': {'prob_green': 73, 'prob_high': 87}, 'bear': {'prob_red': 70, 'prob_low': 80}},
        7:  {'bull': {'prob_green': 80, 'prob_high': 90}, 'bear': {'prob_red': 80, 'prob_low': 80}},
        8:  {'bull': {'prob_green': 73, 'prob_high': 87}, 'bear': {'prob_red': 60, 'prob_low': 70}},
        9:  {'bull': {'prob_green': 85, 'prob_high': 85}, 'bear': {'prob_red': 85, 'prob_low': 85}},
        10: {'bull': {'prob_green': 75, 'prob_high': 88}, 'bear': {'prob_red': 60, 'prob_low': 60}},
        11: {'bull': {'prob_green': 88, 'prob_high': 82}, 'bear': {'prob_red': 56, 'prob_low': 100}},
        12: {'bull': {'prob_green': 100, 'prob_high': 85}, 'bear': {'prob_red': 54, 'prob_low': 85}},
    },
    'YM': {
        1:  {'bull': {'prob_green': 59, 'prob_high': 76}, 'bear': {'prob_red': 70, 'prob_low': 90}},
        2:  {'bull': {'prob_green': 81, 'prob_high': 75}, 'bear': {'prob_red': 73, 'prob_low': 64}},
        3:  {'bull': {'prob_green': 83, 'prob_high': 92}, 'bear': {'prob_red': 57, 'prob_low': 57}},
        4:  {'bull': {'prob_green': 85, 'prob_high': 85}, 'bear': {'prob_red': 38, 'prob_low': 54}},
        5:  {'bull': {'prob_green': 85, 'prob_high': 85}, 'bear': {'prob_red': 62, 'prob_low': 77}},
        6:  {'bull': {'prob_green': 64, 'prob_high': 82}, 'bear': {'prob_red': 73, 'prob_low': 73}},
        7:  {'bull': {'prob_green': 85, 'prob_high': 95}, 'bear': {'prob_red': 33, 'prob_low': 83}},
        8:  {'bull': {'prob_green': 64, 'prob_high': 86}, 'bear': {'prob_red': 58, 'prob_low': 67}},
        9:  {'bull': {'prob_green': 71, 'prob_high': 71}, 'bear': {'prob_red': 83, 'prob_low': 83}},
        10: {'bull': {'prob_green': 82, 'prob_high': 94}, 'bear': {'prob_red': 67, 'prob_low': 67}},
        11: {'bull': {'prob_green': 100, 'prob_high': 87}, 'bear': {'prob_red': 64, 'prob_low': 100}},
        12: {'bull': {'prob_green': 94, 'prob_high': 88}, 'bear': {'prob_red': 80, 'prob_low': 80}},
    },
    'GC': {
        1:  {'bull': {'prob_green': 79, 'prob_high': 84}, 'bear': {'prob_red': 71, 'prob_low': 71}},
        2:  {'bull': {'prob_green': 81, 'prob_high': 75}, 'bear': {'prob_red': 80, 'prob_low': 90}},
        3:  {'bull': {'prob_green': 36, 'prob_high': 71}, 'bear': {'prob_red': 55, 'prob_low': 64}},
        4:  {'bull': {'prob_green': 74, 'prob_high': 74}, 'bear': {'prob_red': 67, 'prob_low': 83}},
        5:  {'bull': {'prob_green': 80, 'prob_high': 67}, 'bear': {'prob_red': 80, 'prob_low': 80}},
        6:  {'bull': {'prob_green': 64, 'prob_high': 73}, 'bear': {'prob_red': 79, 'prob_low': 64}},
        7:  {'bull': {'prob_green': 67, 'prob_high': 89}, 'bear': {'prob_red': 57, 'prob_low': 86}},
        8:  {'bull': {'prob_green': 94, 'prob_high': 67}, 'bear': {'prob_red': 100, 'prob_low': 86}},
        9:  {'bull': {'prob_green': 73, 'prob_high': 73}, 'bear': {'prob_red': 67, 'prob_low': 60}},
        10: {'bull': {'prob_green': 79, 'prob_high': 93}, 'bear': {'prob_red': 83, 'prob_low': 67}},
        11: {'bull': {'prob_green': 71, 'prob_high': 79}, 'bear': {'prob_red': 58, 'prob_low': 67}},
        12: {'bull': {'prob_green': 92, 'prob_high': 92}, 'bear': {'prob_red': 62, 'prob_low': 85}},
    }
}

# Source: SKILL_WEEKLY_FRACTAL_STRATEGY.md lines 46-49
# ONLY bull_high is audited. No bear stats or bull_green available.
D2_WEEKLY_GENERAL = {
    'NQ':  {'bull_high': 80.0},
    'ES':  {'bull_high': 82.4},
    'YM':  {'bull_high': 77.6},
    'GC':  {'bull_high': 75.5},
}

# Source: DOR output charts (output/charts/*/daily/DOR_O2C_D_*_2020-2025_*.png)
# Desviacion estandar from each chart's statistics table
SIGMA = {'NQ': 0.01560, 'ES': 0.01266, 'YM': 0.01219, 'GC': 0.00932}

# --- DAILY SPECIFIC TRIGGERS (Validated T-stats from Daily Alpha Matrix) ---
# Key: (asset, weekday) where weekday: 0=Mon 1=Tue 2=Wed 3=Thu 4=Fri
# Only includes combos with real statistical significance
DAILY_TRIGGERS = {
    # NQ Tuesday Panic → Wednesday Rebound | T>2.1 GOLD
    ('NQ', 1, 'panic'):  {'target': 'WED REBOUND', 'prob': 55.4, 'grade': 'GOLD (T>2.1)', 'avg_ret': '+0.54%'},
    # YM Friday Panic → Monday Rebound | T>1.5 SILVER
    ('YM', 4, 'panic'):  {'target': 'MON REBOUND', 'prob': 67.9, 'grade': 'SILVER (T>1.5)', 'avg_ret': '+0.44%'},
    # NQ Thursday Drive → Friday Reversion | T>1.4 BRONZE
    ('NQ', 3, 'drive'):  {'target': 'FRI REVERSION', 'prob': 57.8, 'grade': 'BRONZE (T>1.4)', 'avg_ret': '-0.27%'},
    # NQ Friday Drive → Monday Continuation
    ('NQ', 4, 'drive'):  {'target': 'MON CONTINUATION', 'prob': 64.5, 'grade': 'SILVER', 'avg_ret': '+0.11%'},
    # YM Wednesday Panic → Thursday Rebound
    ('YM', 2, 'panic'):  {'target': 'THU REBOUND', 'prob': 63.3, 'grade': 'BRONZE', 'avg_ret': '-0.12%'},
}

ASSET_TICKERS = {'NQ': 'NQ=F', 'ES': 'ES=F', 'YM': 'YM=F', 'GC': 'GC=F'}
ASSET_NAMES = {'NQ': 'NASDAQ 100', 'ES': 'S&P 500', 'YM': 'DOW JONES', 'GC': 'GOLD'}
DAY_NAMES = ['MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT', 'SUN']

def get_grade(p):
    if p >= 90: return 'DIAMOND'
    if p >= 82: return 'GOLD+'
    if p >= 75: return 'GOLD'
    return 'SILVER'

def calc_layers(asset, df):
    # Use the LAST DATA BAR's date as reference, not the server clock.
    # This avoids timezone drift (e.g., 7pm CST = Tues UTC but data is still Mon)
    last_date = df.index[-1]
    day = last_date.day
    month = last_date.month
    year = last_date.year
    
    # 1. Monthly — Only show if W2 signal is LOCKED (day > 13)
    month_df = df[(df.index.month == month) & (df.index.year == year)]
    m_signals = []
    m_bias = None
    if day > 13 and len(month_df) >= 5:
        w1w2 = month_df[month_df.index.day <= 13]
        if not w1w2.empty:
            hi, lo = float(w1w2['High'].max()), float(w1w2['Low'].min())
            w2c = float(w1w2['Close'].iloc[-1])
            pos = (w2c - lo) / (hi - lo) if (hi - lo) != 0 else 0.5
            is_bear = pos < 0.5
            m_bias = "BEAR" if is_bear else "BULL"
            
            curr_lo, curr_hi = float(month_df['Low'].min()), float(month_df['High'].max())
            probs = W2_MONTHLY.get(asset, {}).get(month, None)
            if probs:
                p_set = probs.get('bear') if is_bear else probs.get('bull')
                if p_set and is_bear:
                    m_signals.append({'target': 'RED CLOSE', 'prob': p_set['prob_red'], 'status': 'ACTIVE', 'grade': get_grade(p_set['prob_red']), 'color': 'red'})
                    s = 'FULFILLED' if curr_lo < lo else 'PENDING'
                    m_signals.append({'target': 'NEW LOW', 'prob': p_set['prob_low'], 'status': s, 'grade': get_grade(p_set['prob_low']), 'color': 'red' if s=='PENDING' else 'green'})
                elif p_set and not is_bear:
                    m_signals.append({'target': 'GREEN CLOSE', 'prob': p_set['prob_green'], 'status': 'ACTIVE', 'grade': get_grade(p_set['prob_green']), 'color': 'green'})
                    s = 'FULFILLED' if curr_hi > hi else 'PENDING'
                    m_signals.append({'target': 'NEW HIGH', 'prob': p_set['prob_high'], 'status': s, 'grade': get_grade(p_set['prob_high']), 'color': 'green'})
                # If p_set is None → this month/direction has no audited data → m_signals stays empty

    # 2. Weekly — Only show after Tuesday close (>= 2 trading days this week)
    current_week = last_date.isocalendar()[1]
    week_df = df[(df.index.isocalendar().week == current_week) & (df.index.isocalendar().year == year)]
    w_signals = []
    w_bias = None
    if len(week_df) >= 2:
        d1, d2 = week_df.iloc[0], week_df.iloc[1]
        hi, lo = max(float(d1['High']), float(d2['High'])), min(float(d1['Low']), float(d2['Low']))
        pos = (float(d2['Close']) - lo) / (hi - lo) if (hi - lo) != 0 else 0.5
        is_bull = pos > 0.5
        w_bias = "BULL" if is_bull else "BEAR"
        curr_lo, curr_hi = float(week_df['Low'].min()), float(week_df['High'].max())
        gen = D2_WEEKLY_GENERAL.get(asset, {})
        if is_bull:
            # Only bull_high is audited (SKILL_WEEKLY_FRACTAL_STRATEGY.md)
            w_signals.append({'target': 'NEW HIGH', 'prob': gen.get('bull_high', 75), 'status': 'FULFILLED' if curr_hi > hi else 'PENDING', 'grade': get_grade(gen.get('bull_high', 75)), 'color': 'green'})
        # BEAR: no audited weekly bear probabilities exist → w_signals stays empty → column hidden

    # 3. Daily — Check YESTERDAY's O2C for specific triggers (they predict TODAY)
    #         + Check TODAY's O2C for general expansion bias
    #    NOTE: Day references come from the DATA (df index), not the server clock,
    #          because after 5pm CT the "trading day" shifts but Yahoo data hasn't yet.
    d_signals = []
    sigma = SIGMA.get(asset, 0.013)

    # --- YESTERDAY'S TRIGGERS (predict today) ---
    if len(df) >= 2:
        yesterday = df.iloc[-2]
        y_o, y_c = float(yesterday['Open']), float(yesterday['Close'])
        y_o2c = (y_c - y_o) / y_o if y_o != 0 else 0
        y_weekday = yesterday.name.weekday()  # from the data, not the clock
        y_day_name = DAY_NAMES[y_weekday] if y_weekday < 7 else '?'

        if y_o2c > sigma:
            trigger = DAILY_TRIGGERS.get((asset, y_weekday, 'drive'), None)
            if trigger:
                d_signals.append({
                    'target': trigger['target'],
                    'prob': trigger['prob'],
                    'status': 'ACTIVE',
                    'grade': trigger['grade'],
                    'color': 'red' if 'REVERSION' in trigger['target'] else 'green',
                    'val': f'{y_day_name} closed {y_o2c*100:+.2f}% (>{sigma*100:.1f}%)',
                    'avg_ret': trigger['avg_ret']
                })
        elif y_o2c < -sigma:
            trigger = DAILY_TRIGGERS.get((asset, y_weekday, 'panic'), None)
            if trigger:
                d_signals.append({
                    'target': trigger['target'],
                    'prob': trigger['prob'],
                    'status': 'ACTIVE',
                    'grade': trigger['grade'],
                    'color': 'green',
                    'val': f'{y_day_name} closed {y_o2c*100:+.2f}% (<-{sigma*100:.1f}%)',
                    'avg_ret': trigger['avg_ret']
                })

    # General expansion bias REMOVED — probabilities were not audited
    # If neither yesterday triggered nor today broke σ → d_signals stays empty → column hidden

    return {'monthly': {'bias': m_bias, 'signals': m_signals}, 'weekly': {'bias': w_bias, 'signals': w_signals}, 'daily': {'signals': d_signals}}

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        res = []
        for k, ticker in ASSET_TICKERS.items():
            try:
                t = yf.Ticker(ticker); df = t.history(period='60d', interval='1d')
                if df.empty: res.append({'asset': k, 'error': 'Empty'}); continue
                res.append({'asset': k, 'name': ASSET_NAMES[k], 'price': round(float(df['Close'].iloc[-1]), 2), 'layers': calc_layers(k, df)})
            except Exception as e: res.append({'asset': k, 'error': str(e)})
        self.wfile.write(json.dumps({'timestamp': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC'), 'data': res}).encode())
