import pandas as pd
from datetime import datetime, timedelta

class AlphaBrain:
    """
    The central intelligence unit for SPEC RESEARCH v7.0 (Seasonally Validated).
    Implements a Layered Alpha Architecture with AUDITED PROBABILITIES from AUDITED_W2_STATS.md.
    """
    
    # Audited Alpha Database
    ALPHAS = {
        'NQ': {
            'sigma': {'daily': 0.0135, 'weekly': 0.0276},
            # General Monthly Stats (Fallback)
            'monthly_fractal': {
                'bear': {'prob_red': 0.674, 'prob_low': 0.712},
                'bull': {'prob_green': 0.810, 'prob_high': 0.862}
            },
            # Month-Specific Overrides (The 'Diamond' Signals from AUDITED_W2_STATS.md)
            'seasonal_overrides': {
                2: { # February
                    'bear': {'prob_red': 0.917, 'prob_low': 0.500}, # Audited: 92% Red / 50% Low
                    'bull': {'prob_green': 0.714, 'prob_high': 0.929} # Audited Bull Scenario
                },
                # Can add other months as needed
            },
            'monday_drive': {'prob_bull': 0.823, 'grade': 'GOLD +'},
            'tuesday_reversion': {'trigger': 'PANIC (<-1σ)', 'target': 'WEDNESDAY REBOUND', 'prob': 0.554, 'grade': 'GOLD (T>2.1)'},
            'thursday_reversion': {'trigger': 'DRIVE (>1σ)', 'target': 'FRIDAY REVERSION', 'prob': 0.578, 'grade': 'BRONZE'}
        },
        'ES': {
            'sigma': {'daily': 0.0109, 'weekly': 0.0230},
            # General Monthly Stats
            'monthly_fractal': {
                'bear': {'prob_red': 0.667, 'prob_low': 0.650}, # Conservative defaults or extracted averages
                'bull': {'prob_green': 0.792, 'prob_high': 0.842}
            },
            # Month-Specific Overrides
            'seasonal_overrides': {
                2: { # February
                    'bear': {'prob_red': 0.667, 'prob_low': 0.600}, # Audited: ~67% Red
                    'bull': {'prob_green': 0.800, 'prob_high': 0.800}
                }
            },
            'monday_drive': {'prob_bull': 0.865, 'grade': 'GOLD +'}
        },
        'YM': {
            'sigma': {'daily': 0.0106, 'weekly': 0.0231},
            # General Monthly Stats
            'monthly_fractal': {
                'bear': {'prob_red': 0.667, 'prob_low': 0.650},
                'bull': {'prob_green': 0.776, 'prob_high': 0.876}
            },
            'seasonal_overrides': {
                 2: { # February
                    'bear': {'prob_red': 0.667, 'prob_low': 0.600}, # Audited: ~67% Red
                    'bull': {'prob_green': 0.750, 'prob_high': 0.850} # Estimated
                }
            },
            'monday_drive': {'prob_bull': 0.780, 'grade': 'SILVER'},
            'friday_reversion': {'trigger': 'PANIC (<-1σ)', 'target': 'MONDAY REBOUND', 'prob': 0.679, 'grade': 'SILVER (T>1.5)'}
        }
    }

    @classmethod
    def calculate_state(cls, asset_key, market_data):
        if asset_key not in cls.ALPHAS: return None

        # 1. Monthly Layer (Strategic) - Returns list of signals
        monthly_signals = cls._calculate_monthly_layer(asset_key, market_data['monthly_history'])

        # 2. Weekly Layer (Tactical)
        weekly_bias = cls._calculate_weekly_layer(asset_key, market_data['weekly_history'])

        # 3. Daily Layer (Execution)
        daily_trigger = cls._calculate_daily_layer(asset_key, market_data['live_o2c'])

        return {
            'asset': asset_key,
            'price': market_data['price'],
            'layers': {
                'monthly_signals': monthly_signals, # List of dicts
                'weekly': weekly_bias,
                'daily': daily_trigger
            },
            'last_update': datetime.now().strftime('%H:%M:%S')
        }

    @classmethod
    def _calculate_monthly_layer(cls, asset_key, history_df):
        """
        Evaluates Monthly Structure and returns multiple distinct objectives.
        Checks if objectives (New Low/High) have already been met.
        """
        if history_df is None or history_df.empty:
            return []

        now = datetime.now()
        current_month = now.month
        
        try:
            current_month_df = history_df[history_df.index.month == current_month]
        except AttributeError:
             return []

        if current_month_df.empty or now.day <= 13:
             return [] # Forming...

        # Get data up to Day 13 (Signal Lock)
        w1_w2_df = current_month_df[current_month_df.index.day <= 13]
        if len(w1_w2_df) < 5: return []

        range_high = w1_w2_df['High'].max()
        range_low = w1_w2_df['Low'].min()
        w2_close = w1_w2_df['Close'].iloc[-1]
        rng = range_high - range_low
        if rng == 0: return []
        
        pos = (w2_close - range_low) / rng
        
        # Determine Current Status (Fulfillment Check)
        current_low = current_month_df['Low'].min()
        current_high = current_month_df['High'].max()
        
        # Check if we broke the W1-W2 range
        broke_low = current_low < range_low
        broke_high = current_high > range_high
        
        # Retrieve Probs
        asset_cfg = cls.ALPHAS[asset_key]
        general_probs = asset_cfg['monthly_fractal']
        seasonal_probs = asset_cfg.get('seasonal_overrides', {}).get(current_month, {})
        
        signals = []
        
        if pos < 0.50:
            # BEARISH BIAS
            probs = seasonal_probs.get('bear', general_probs.get('bear', {}))
            
            # 1. RED MONTH OBJECTIVE
            signals.append({
                'name': 'MONTHLY BIAS',
                'condition': 'BEARISH (W2 < 50%)',
                'target': 'RED CLOSE',
                'prob': probs.get('prob_red', 0.60),
                'status': 'ACTIVE', # Always active until month end
                'color': 'RED',
                'grade': 'DIAMOND \ud83d\udc8e' if probs.get('prob_red', 0) > 0.9 else 'GOLD +'
            })
            
            # 2. NEW LOW OBJECTIVE
            signals.append({
                'name': 'EXTENSION BIAS',
                'condition': 'BEARISH (W2 < 50%)',
                'target': 'NEW MONTH LOW',
                'prob': probs.get('prob_low', 0.60),
                'status': 'FULFILLED \u2705' if broke_low else 'PENDING \u23f3',
                'color': 'GREEN' if broke_low else 'RED', # Green check if done, Red target if pending
                'grade': 'GOLD +'
            })
            
        else:
            # BULLISH BIAS
            probs = seasonal_probs.get('bull', general_probs.get('bull', {}))
            
            # 1. GREEN MONTH OBJECTIVE
            signals.append({
                'name': 'MONTHLY BIAS',
                'condition': 'BULLISH (W2 > 50%)',
                'target': 'GREEN CLOSE',
                'prob': probs.get('prob_green', 0.80),
                'status': 'ACTIVE',
                'color': 'GREEN',
                'grade': 'GOLD +'
            })
            
            # 2. NEW HIGH OBJECTIVE
            signals.append({
                'name': 'EXTENSION BIAS',
                'condition': 'BULLISH (W2 > 50%)',
                'target': 'NEW MONTH HIGH',
                'prob': probs.get('prob_high', 0.80),
                'status': 'FULFILLED \u2705' if broke_high else 'PENDING \u23f3',
                'color': 'GREEN' if broke_high else 'GREEN',
                'grade': 'GOLD +'
            })
            
        return signals

    # _calculate_weekly_layer and _calculate_daily_layer remain identical to v5.0
    @classmethod
    def _calculate_weekly_layer(cls, asset_key, history_df):
        # [Same as v5.0]
        if history_df is None or history_df.empty: return {'status': 'NO DATA', 'prob': 0.0, 'color': 'GRAY'}
        mondays = history_df[history_df.index.weekday == 0]
        if mondays.empty: return {'status': 'NO MONDAY', 'prob': 0.0, 'color': 'GRAY'}
        
        last_monday = mondays.iloc[-1]
        last_monday_date = mondays.index[-1]
        current_week = datetime.now().isocalendar()[1]
        monday_week = last_monday_date.isocalendar()[1]
        
        if current_week != monday_week: return {'status': 'WAITING MONDAY', 'prob': 0.0, 'color': 'GRAY'}
        
        mon_o2c = (last_monday['Close'] - last_monday['Open']) / last_monday['Open']
        sigma = cls.ALPHAS[asset_key]['sigma']['daily']
        probs = cls.ALPHAS[asset_key].get('monday_drive', {})
        
        if mon_o2c > sigma:
            return {'status': 'MONDAY DRIVE (>1σ)', 'o2c': mon_o2c, 'prob': probs.get('prob_bull', 0.80), 'color': 'GREEN', 'grade': probs.get('grade', 'GOLD')}
        elif mon_o2c < -sigma:
             return {'status': 'MONDAY PANIC (<-1σ)', 'o2c': mon_o2c, 'prob': 0.80, 'color': 'RED', 'grade': 'GOLD'}
             
        return {'status': 'NEUTRAL', 'o2c': mon_o2c, 'prob': 0.50, 'color': 'GRAY', 'grade': 'NOISE'}

    @classmethod
    def _calculate_daily_layer(cls, asset_key, current_o2c):
        # [Same as v5.0]
        daily_sigma = cls.ALPHAS[asset_key]['sigma']['daily']
        today_weekday = datetime.now().weekday()
        
        status = 'INSIDE NOISE'
        color = 'GRAY'
        prob = 0.0
        target = 'None'
        grade = 'NOISE'
        
        if current_o2c > daily_sigma:
            if today_weekday == 3 and asset_key == 'NQ':
                 stats = cls.ALPHAS['NQ'].get('thursday_reversion')
                 status = f"THU REVERSION {stats['trigger']}"
                 color = 'RED'
                 prob = stats['prob']
                 target = stats['target']
                 grade = stats['grade']
            else:
                 status = 'BULL EXPANSION (>1σ)'
                 color = 'GREEN'
                 prob = 0.82 
                 target = 'WEEKLY BULL EXPANSION'
                 grade = 'GOLD +'
        elif current_o2c < -daily_sigma:
            if today_weekday == 1 and asset_key == 'NQ':
                 stats = cls.ALPHAS['NQ'].get('tuesday_reversion')
                 status = f"TUE REVERSION {stats['trigger']}"
                 color = 'GREEN'
                 prob = stats['prob']
                 target = stats['target']
                 grade = stats['grade']
            elif today_weekday == 4 and asset_key == 'YM':
                 stats = cls.ALPHAS['YM'].get('friday_reversion')
                 status = f"FRI REVERSION {stats['trigger']}"
                 color = 'GREEN'
                 prob = stats['prob']
                 target = stats['target']
                 grade = stats['grade']
            else:
                 status = 'BEAR EXPANSION (<-1σ)'
                 color = 'RED'
                 prob = 0.84
                 target = 'WEEKLY BEAR EXPANSION'
                 grade = 'GOLD +'
            
        return {
            'status': status,
            'o2c': current_o2c,
            'sigma_level': daily_sigma,
            'prob': prob,
            'target': target,
            'color': color,
            'grade': grade
        }

if __name__ == "__main__":
    pass
