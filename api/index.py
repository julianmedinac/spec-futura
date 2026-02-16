from http.server import BaseHTTPRequestHandler
import json
import yfinance as yf
from datetime import datetime, timedelta

# ============================================================
# AUDITED PROBABILITY TABLES
# Source: AUDITED_W2_STATS.md + Research Files
# ============================================================
W2_MONTHLY = {
    'NQ': {
        1:  {'bear': {'prob_red': 75.0, 'prob_low': 87.5, 'n': 8},  'bull': {'prob_green': 77.8, 'prob_high': 88.9, 'n': 18}},
        2:  {'bear': {'prob_red': 91.7, 'prob_low': 50.0, 'n': 12}, 'bull': {'prob_green': 71.4, 'prob_high': 92.9, 'n': 14}},
        3:  {'bear': {'prob_red': 57.1, 'prob_low': 85.7, 'n': 14}, 'bull': {'prob_green': 90.9, 'prob_high': 81.8, 'n': 11}},
        5:  {'bear': {'prob_red': 61.5, 'prob_low': 61.5, 'n': 13}, 'bull': {'prob_green': 91.7, 'prob_high': 91.7, 'n': 12}},
        6:  {'bear': {'prob_red': 69.2, 'prob_low': 84.6, 'n': 13}, 'bull': {'prob_green': 91.7, 'prob_high': 83.3, 'n': 12}},
        10: {'bear': {'prob_red': 60.0, 'prob_low': 50.0, 'n': 10}, 'bull': {'prob_green': 75.0, 'prob_high': 93.8, 'n': 16}},
        11: {'bear': {'prob_red': 60.0, 'prob_low': 90.0, 'n': 10}, 'bull': {'prob_green': 93.8, 'prob_high': 87.5, 'n': 16}},
    },
    'ES': {
        1:  {'bear': {'prob_red': 70.0, 'prob_low': 90.0, 'n': 10}, 'bull': {'prob_green': 75.0, 'prob_high': 85.0, 'n': 16}},
        2:  {'bear': {'prob_red': 66.7, 'prob_low': 60.0, 'n': 12}, 'bull': {'prob_green': 80.0, 'prob_high': 80.0, 'n': 15}},
        3:  {'bear': {'prob_red': 60.0, 'prob_low': 75.0, 'n': 12}, 'bull': {'prob_green': 83.3, 'prob_high': 91.7, 'n': 12}},
        7:  {'bear': {'prob_red': 60.0, 'prob_low': 65.0, 'n': 6},  'bull': {'prob_green': 85.0, 'prob_high': 95.0, 'n': 20}},
        9:  {'bear': {'prob_red': 83.3, 'prob_low': 83.3, 'n': 12}, 'bull': {'prob_green': 75.0, 'prob_high': 80.0, 'n': 14}},
        11: {'bear': {'prob_red': 60.0, 'prob_low': 70.0, 'n': 10}, 'bull': {'prob_green': 100.0,'prob_high': 86.7, 'n': 15}},
        12: {'bear': {'prob_red': 80.0, 'prob_low': 80.0, 'n': 10}, 'bull': {'prob_green': 93.8, 'prob_high': 87.5, 'n': 16}},
    },
    'YM': {
        1:  {'bear': {'prob_red': 70.0, 'prob_low': 90.0, 'n': 10}, 'bull': {'prob_green': 75.0, 'prob_high': 85.0, 'n': 16}},
        2:  {'bear': {'prob_red': 66.7, 'prob_low': 65.0, 'n': 8},  'bull': {'prob_green': 75.0, 'prob_high': 85.0, 'n': 14}},
        5:  {'bear': {'prob_red': 60.0, 'prob_low': 65.0, 'n': 10}, 'bull': {'prob_green': 84.6, 'prob_high': 84.6, 'n': 13}},
        6:  {'bear': {'prob_red': 73.3, 'prob_low': 73.3, 'n': 15}, 'bull': {'prob_green': 80.0, 'prob_high': 80.0, 'n': 10}},
        9:  {'bear': {'prob_red': 83.3, 'prob_low': 83.3, 'n': 12}, 'bull': {'prob_green': 75.0, 'prob_high': 80.0, 'n': 14}},
        10: {'bear': {'prob_red': 60.0, 'prob_low': 60.0, 'n': 8},  'bull': {'prob_green': 82.4, 'prob_high': 94.1, 'n': 17}},
        11: {'bear': {'prob_red': 60.0, 'prob_low': 70.0, 'n': 10}, 'bull': {'prob_green': 100.0,'prob_high': 86.7, 'n': 15}},
        12: {'bear': {'prob_red': 75.0, 'prob_low': 75.0, 'n': 10}, 'bull': {'prob_green': 93.8, 'prob_high': 87.5, 'n': 16}},
    },
    'GC': {
        1:  {'bear': {'prob_red': 65.0, 'prob_low': 70.0, 'n': 7},  'bull': {'prob_green': 78.9, 'prob_high': 84.2, 'n': 19}},
        2:  {'bear': {'prob_red': 80.0, 'prob_low': 90.0, 'n': 10}, 'bull': {'prob_green': 81.2, 'prob_high': 75.0, 'n': 16}},
        8:  {'bear': {'prob_red': 100.0,'prob_low': 85.7, 'n': 7},  'bull': {'prob_green': 94.4, 'prob_high': 66.7, 'n': 18}},
        12: {'bear': {'prob_red': 65.0, 'prob_low': 65.0, 'n': 8},  'bull': {'prob_green': 92.3, 'prob_high': 92.3, 'n': 13}},
    }
}

D2_WEEKLY_GENERAL = {
    'NQ':  {'bull_high': 80.0, 'bull_green': 75.0, 'bear_low': 72.0, 'bear_red': 67.0},
    'ES':  {'bull_high': 82.4, 'bull_green': 77.0, 'bear_low': 70.0, 'bear_red': 65.0},
    'YM':  {'bull_high': 77.6, 'bull_green': 74.0, 'bear_low': 68.0, 'bear_red': 64.0},
    'GC':  {'bull_high': 75.5, 'bull_green': 70.0, 'bear_low': 65.0, 'bear_red': 60.0},
}

SIGMA = {'NQ': 0.0135, 'ES': 0.0109, 'YM': 0.0106, 'GC': 0.0085}

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
    now = datetime.utcnow()
    month = now.month
    year = now.year
    
    # 1. Monthly
    month_df = df[(df.index.month == month) & (df.index.year == year)]
    m_signals = []
    m_bias = "FORMING"
    if len(month_df) >= 3:
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
                p_set = probs['bear'] if is_bear else probs['bull']
                if is_bear:
                    m_signals.append({'target': 'RED CLOSE', 'prob': p_set['prob_red'], 'status': 'ACTIVE', 'grade': get_grade(p_set['prob_red']), 'color': 'red'})
                    s = 'FULFILLED' if curr_lo < lo else 'PENDING'
                    m_signals.append({'target': 'NEW LOW', 'prob': p_set['prob_low'], 'status': s, 'grade': get_grade(p_set['prob_low']), 'color': 'red' if s=='PENDING' else 'green'})
                else:
                    m_signals.append({'target': 'GREEN CLOSE', 'prob': p_set['prob_green'], 'status': 'ACTIVE', 'grade': get_grade(p_set['prob_green']), 'color': 'green'})
                    s = 'FULFILLED' if curr_hi > hi else 'PENDING'
                    m_signals.append({'target': 'NEW HIGH', 'prob': p_set['prob_high'], 'status': s, 'grade': get_grade(p_set['prob_high']), 'color': 'green'})
            else:
                m_signals.append({'target': 'MONTHLY TARGET', 'prob': 65, 'status': 'AUDITING', 'grade': 'SILVER', 'color': 'gray'})

    # 2. Weekly
    current_week = now.isocalendar()[1]
    week_df = df[(df.index.isocalendar().week == current_week) & (df.index.isocalendar().year == year)]
    w_signals = []
    w_bias = "FORMING"
    if len(week_df) >= 2:
        d1, d2 = week_df.iloc[0], week_df.iloc[1]
        hi, lo = max(float(d1['High']), float(d2['High'])), min(float(d1['Low']), float(d2['Low']))
        pos = (float(d2['Close']) - lo) / (hi - lo) if (hi - lo) != 0 else 0.5
        is_bull = pos > 0.5
        w_bias = "BULL" if is_bull else "BEAR"
        curr_lo, curr_hi = float(week_df['Low'].min()), float(week_df['High'].max())
        gen = D2_WEEKLY_GENERAL.get(asset, {})
        if is_bull:
            w_signals.append({'target': 'NEW HIGH', 'prob': gen.get('bull_high', 75), 'status': 'FULFILLED' if curr_hi > hi else 'PENDING', 'grade': 'GOLD', 'color': 'green'})
            w_signals.append({'target': 'GREEN WEEK', 'prob': gen.get('bull_green', 70), 'status': 'ACTIVE', 'grade': 'SILVER', 'color': 'green'})
        else:
            w_signals.append({'target': 'NEW LOW', 'prob': gen.get('bear_low', 70), 'status': 'FULFILLED' if curr_lo < lo else 'PENDING', 'grade': 'GOLD', 'color': 'red'})
            w_signals.append({'target': 'RED WEEK', 'prob': gen.get('bear_red', 65), 'status': 'ACTIVE', 'grade': 'SILVER', 'color': 'red'})
    else:
        w_signals.append({'target': 'WAITING TUE CLOSE', 'prob': 0, 'status': 'FORMING', 'grade': 'WAITING', 'color': 'gray'})

    # 3. Daily — Specific Triggers + General Expansion Bias
    d_signals = []
    today = df.iloc[-1]
    o, c = float(today['Open']), float(today['Close'])
    o2c = (c - o) / o if o != 0 else 0
    sigma = SIGMA.get(asset, 0.013)
    weekday = now.weekday()  # 0=Mon ... 4=Fri
    day_name = DAY_NAMES[weekday] if weekday < 7 else '?'

    if o2c > sigma:
        # Check for specific DRIVE trigger
        trigger = DAILY_TRIGGERS.get((asset, weekday, 'drive'), None)
        if trigger:
            d_signals.append({
                'target': trigger['target'],
                'prob': trigger['prob'],
                'status': 'ACTIVE',
                'grade': trigger['grade'],
                'color': 'red' if 'REVERSION' in trigger['target'] else 'green',
                'val': f'{day_name} O2C: {o2c*100:+.2f}% (>{sigma*100:.1f}%)',
                'avg_ret': trigger['avg_ret']
            })
        # Always also show general expansion bias
        d_signals.append({
            'target': 'WEEKLY BULL EXPANSION',
            'prob': 82,
            'status': 'ACTIVE',
            'grade': 'GOLD+',
            'color': 'green',
            'val': f'{day_name} DRIVE: {o2c*100:+.2f}% (broke +1σ)'
        })
    elif o2c < -sigma:
        # Check for specific PANIC trigger
        trigger = DAILY_TRIGGERS.get((asset, weekday, 'panic'), None)
        if trigger:
            d_signals.append({
                'target': trigger['target'],
                'prob': trigger['prob'],
                'status': 'ACTIVE',
                'grade': trigger['grade'],
                'color': 'green',
                'val': f'{day_name} O2C: {o2c*100:+.2f}% (<-{sigma*100:.1f}%)',
                'avg_ret': trigger['avg_ret']
            })
        # Always also show general expansion bias
        d_signals.append({
            'target': 'WEEKLY BEAR EXPANSION',
            'prob': 84,
            'status': 'ACTIVE',
            'grade': 'GOLD+',
            'color': 'red',
            'val': f'{day_name} PANIC: {o2c*100:+.2f}% (broke -1σ)'
        })
    else:
        d_signals.append({
            'target': 'INSIDE RANGE',
            'prob': 50,
            'status': 'NO SIGNAL',
            'grade': 'NOISE',
            'color': 'gray'
        })

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
