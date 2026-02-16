import pandas as pd
import numpy as np

class ConditionalAnalyzer:
    """
    Calculates conditional probabilities based on price action regimes.
    Example: 'If price in Q2 crosses Q1 High, what is the probability that 
    the Yearly Low was already set in Q1?'
    """
    def __init__(self, data: pd.DataFrame):
        self.data = data.copy()
        self.data['year'] = self.data.index.year
        self.data['quarter'] = self.data.index.quarter
        
    def analyze_q2_breakout(self):
        """
        Calculates: P(Yearly Low is in Q1 | Q2 price > Q1 High)
        """
        years = self.data['year'].unique()
        stats = []
        
        for year in years:
            y_data = self.data[self.data['year'] == year].copy()
            if len(y_data) < 200: continue
            
            q1_data = y_data[y_data['quarter'] == 1]
            q2_data = y_data[y_data['quarter'] == 2]
            
            if q1_data.empty or q2_data.empty: continue
            
            h_q1 = q1_data['close'].max()
            l_year = y_data['close'].min()
            low_date = y_data['close'].idxmin()
            
            # Condition: Did Q2 cross Q1 High?
            condition_met = (q2_data['close'] > h_q1).any()
            
            # Outcome: Was the yearly low in Q1?
            outcome_met = (low_date.quarter == 1)
            
            stats.append({
                'year': year,
                'condition': condition_met,
                'outcome': outcome_met,
                'q1_high': h_q1,
                'yearly_low': l_year
            })
            
        df = pd.DataFrame(stats)
        
        # Calculations
        total_years = len(df)
        years_with_condition = df[df['condition'] == True]
        count_condition = len(years_with_condition)
        
        if count_condition == 0:
            return "No years met the condition.", df
            
        success_given_condition = len(years_with_condition[years_with_condition['outcome'] == True])
        prob_conditional = (success_given_condition / count_condition) * 100
        
        # Benchmark: Probability of Low in Q1 regardless of condition
        prob_benchmark = (len(df[df['outcome'] == True]) / total_years) * 100
        
        return {
            'prob_conditional': prob_conditional,
            'prob_benchmark': prob_benchmark,
            'sample_size': count_condition,
            'total_sample': total_years,
            'lift': prob_conditional - prob_benchmark
        }, df

    def analyze_monthly_progression(self):
        """
        Calculates: P(Yearly Low is already set | Month M makes a New Yearly High)
        Returns a progression of confidence month by month.
        """
        years = self.data['year'].unique()
        monthly_stats = []
        
        for m in range(2, 13): # From Feb to Dec
            hits = 0
            total_signals = 0
            
            for year in years:
                y_data = self.data[self.data['year'] == year]
                if len(y_data) < 200: continue
                
                # Data up to previous month
                prior_data = y_data[y_data['quarter'].isin([1,2,3,4]) & (y_data.index.month < m)]
                current_month_data = y_data[y_data.index.month == m]
                
                if prior_data.empty or current_month_data.empty: continue
                
                h_prior = prior_data['close'].max()
                yearly_low_date = y_data['close'].idxmin()
                
                # Condition: Current month makes a new high for the year
                if current_month_data['close'].max() > h_prior:
                    total_signals += 1
                    # Outcome: Was the yearly low before this month?
                    if yearly_low_date < current_month_data.index[0]:
                        hits += 1
            
            if total_signals > 0:
                monthly_stats.append({
                    'month': m,
                    'prob': (hits / total_signals) * 100,
                    'sample': total_signals
                })
                
        return pd.DataFrame(monthly_stats)

    def analyze_q2_reversal_pattern(self):
        """
        Condition: Q2 makes a Lower Low than Q1 AND a Higher High than Q1.
        Question: Does Q2 become the Yearly Low? Does Q4 become the Yearly High?
        """
        years = self.data['year'].unique()
        stats = []
        
        for year in years:
            y_data = self.data[self.data['year'] == year]
            if len(y_data) < 200: continue
            
            q1 = y_data[y_data['quarter'] == 1]
            q2 = y_data[y_data['quarter'] == 2]
            
            if q1.empty or q2.empty: continue
            
            low_q1 = q1['close'].min()
            high_q1 = q1['close'].max()
            
            low_q2 = q2['close'].min()
            high_q2 = q2['close'].max()
            
            # Condition: Q2 Lower Low AND Q2 Higher High (Quarterly Outside Expansion)
            condition_met = (low_q2 < low_q1) and (high_q2 > high_q1)
            
            if condition_met:
                yearly_low_date = y_data['close'].idxmin()
                yearly_high_date = y_data['close'].idxmax()
                
                stats.append({
                    'year': year,
                    'is_q2_low': (yearly_low_date.quarter == 2),
                    'is_q4_high': (yearly_high_date.quarter == 4)
                })
        
        df_results = pd.DataFrame(stats)
        
        if df_results.empty:
            return None
            
        prob_q2_is_low = (df_results['is_q2_low'].sum() / len(df_results)) * 100
        prob_q4_is_high = (df_results['is_q4_high'].sum() / len(df_results)) * 100
        
        return {
            'sample_size': len(df_results),
            'prob_q2_is_low': prob_q2_is_low,
            'prob_q4_is_high': prob_q4_is_high,
            'years': df_results['year'].tolist()
        }
