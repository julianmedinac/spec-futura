import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import pandas as pd
import numpy as np
import os
from datetime import datetime

class SeasonalityVisualizer:
    def __init__(self, output_dir='output/charts/seasonality'):
        self.output_dir = output_dir
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            
        # VISUAL STYLE GUIDE Constants
        self.bg_color = '#000000'
        self.text_color = '#ffffff'
        self.accent_green = '#00ff44'
        self.accent_red = '#ff0044'
        self.gray_text = '#888888'
        self.line_color = '#333333'
        self.font_family = 'monospace'
        
        # Apply global RC params for terminal style
        plt.rcParams.update({
            'axes.facecolor': self.bg_color,
            'figure.facecolor': self.bg_color,
            'axes.edgecolor': self.line_color,
            'axes.labelcolor': self.text_color,
            'xtick.color': self.gray_text,
            'ytick.color': self.gray_text,
            'text.color': self.text_color,
            'font.family': self.font_family,
            'grid.color': self.line_color,
            'savefig.facecolor': self.bg_color,
            'savefig.edgecolor': self.bg_color
        })

    def plot_monthly_seasonality(self, monthly_stats: pd.DataFrame, asset_name: str, years_range: str):
        """
        Plots the average monthly return bar chart with hit rate and significance labels.
        """
        # (16, 10) for wide table-like format but keeping it slightly smaller for bar charts
        fig, ax = plt.subplots(figsize=(14, 8))
        
        # monthly_stats index is 1-12
        months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        
        # Colors: Style Guide Green and Red
        colors = [self.accent_green if x >= 0 else self.accent_red for x in monthly_stats['mean_return']]
        
        bars = ax.bar(months, monthly_stats['mean_return'] * 100, color=colors, width=0.6, alpha=0.9)
        
        # Add Labels: Hit Rate & Significance
        for i, (bar, row) in enumerate(zip(bars, monthly_stats.itertuples())):
            height = bar.get_height()
            
            # Hit Rate
            hit_rate_label = f'{row.hit_rate:.0%}'
            
            # Significance Stars
            sig_label = ""
            if row.p_value < 0.01:
                sig_label = "***"
            elif row.p_value < 0.05:
                sig_label = "**"
            elif row.p_value < 0.10:
                sig_label = "*"
            
            full_label = f"{hit_rate_label}\n{sig_label}"
            
            # Position label
            label_y_pos = height + (0.3 if height >= 0 else -0.8)
            
            ax.text(bar.get_x() + bar.get_width()/2., label_y_pos,
                    full_label,
                    ha='center', va='bottom' if height >= 0 else 'top',
                    fontsize=10, fontweight='bold', color=self.text_color)

        # Formatting
        ax.axhline(0, color=self.text_color, linewidth=1.0, alpha=0.5)
        ax.yaxis.set_major_formatter(mtick.PercentFormatter())
        
        # Titles
        plt.suptitle(f'{asset_name} MONTHLY SEASONALITY ({years_range})', 
                     fontsize=18, fontweight='bold', color=self.text_color, y=0.95)
        ax.set_title('Average Returns by Month', fontsize=10, color=self.gray_text, pad=10)
        
        # Cleanup
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.grid(axis='y', linestyle=':', alpha=0.3)
        
        # Footer with Statistical Note
        footer_text = f"VAL 2.0 | Seasonality Analysis | {datetime.now().strftime('%d/%m/%Y')} | " \
                     f"Stars indicate statistical significance (Confidence based on T-Stat > 2.0)"
        fig.text(0.1, 0.02, footer_text, fontsize=8, color=self.gray_text)
        
        plt.tight_layout(rect=[0, 0.05, 1, 0.93])
        
        # Save
        asset_dir = os.path.join(self.output_dir, asset_name)
        if not os.path.exists(asset_dir):
            os.makedirs(asset_dir)
            
        filename = f"{asset_dir}/{asset_name}_monthly_seasonality.png"
        plt.savefig(filename, dpi=300, bbox_inches='tight')
        plt.close()
        print(f"  Chart saved: {filename}")

    def plot_quarterly_seasonality(self, stats_df: pd.DataFrame, asset_name: str, years_range: str):
        """
        Creates a bar chart for quarterly performance.
        """
        fig, ax = plt.subplots(figsize=(16, 9))
        
        # Quarter Labels
        quarters = ['Q1', 'Q2', 'Q3', 'Q4']
        stats_df.index = quarters
        
        colors = [self.accent_green if x > 0 else self.accent_red for x in stats_df['mean_return']]
        
        bars = ax.bar(stats_df.index, stats_df['mean_return'], color=colors, alpha=0.9, edgecolor='none')
        
        # Add Horizontal Baseline
        ax.axhline(0, color='white', linewidth=0.8, alpha=0.5)
        
        # Add Data Labels (Returns and Hit Rates)
        for i, bar in enumerate(bars):
            height = bar.get_height()
            hit_rate = stats_df['hit_rate'].iloc[i]
            p_val = stats_df['p_value'].iloc[i]
            
            # Significance stars
            stars = ""
            if p_val < 0.01: stars = "\n***"
            elif p_val < 0.05: stars = "\n**"
            elif p_val < 0.10: stars = "\n*"
            
            # Label on top for positive, below for negative
            va = 'bottom' if height > 0 else 'top'
            offset = 0.001 if height > 0 else -0.001
            
            # Mean Return Label
            ax.text(bar.get_x() + bar.get_width()/2, height + offset, 
                    f"{hit_rate:.0%}{stars}", 
                    ha='center', va=va, color=self.text_color, fontweight='bold', fontsize=12)
            
            # Percentage label on the axis
            label_y = -0.015 if height > 0 else 0.015
            ax.text(bar.get_x() + bar.get_width()/2, label_y, 
                    f"{height:.2%}", 
                    ha='center', va='center', color='white', fontsize=10, fontweight='bold')

        # Formatting
        ax.yaxis.set_major_formatter(mtick.PercentFormatter(1.0))
        plt.xticks(fontsize=12, color=self.gray_text)
        plt.yticks(fontsize=10, color=self.gray_text)
        
        # Titles
        plt.suptitle(f'{asset_name} QUARTERLY SEASONALITY ({years_range})', 
                     fontsize=18, fontweight='bold', color=self.text_color, y=0.95)
        ax.set_title('Average Returns by Quarter', fontsize=10, color=self.gray_text, pad=10)
        
        # Cleanup
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.grid(axis='y', linestyle=':', alpha=0.3)
        
        # Footer
        footer_text = f"VAL 2.0 | Seasonality Analysis | {datetime.now().strftime('%d/%m/%Y')} | " \
                     f"Stars indicate statistical significance (Confidence based on T-Stat > 2.0)"
        fig.text(0.1, 0.02, footer_text, fontsize=8, color=self.gray_text)
        
        plt.tight_layout(rect=[0, 0.05, 1, 0.93])
        
        # Save in asset subdirectory
        asset_dir = os.path.join(self.output_dir, asset_name)
        if not os.path.exists(asset_dir):
            os.makedirs(asset_dir)
            
        filename = f"{asset_dir}/{asset_name}_quarterly_seasonality.png"
        plt.savefig(filename, dpi=300, bbox_inches='tight')
        plt.close()
        print(f"  Chart saved: {filename}")

    def plot_daily_seasonality(self, daily_df: pd.DataFrame, asset_name: str, month: int, years_range: str, 
                               y_lim=None, x_lim=None):
        """
        Plots the cumulative performance by trading day for a specific month.
        daily_df index is Trading Day (1..N), column 'level' (starts ~100)
        """
        month_name = datetime(2000, month, 1).strftime('%B').upper()
        
        fig, ax = plt.subplots(figsize=(14, 8))
        
        # Determine trend (Positive or Negative Month)
        start_val = daily_df['level'].iloc[0]
        end_val = daily_df['level'].iloc[-1]
        is_positive_month = end_val > start_val
        
        month_color = self.accent_green if is_positive_month else self.accent_red
        
        # Plot Line
        ax.plot(daily_df.index, daily_df['level'], linewidth=3, color=month_color)
        
        # Fill area for terminal effect
        ax.fill_between(daily_df.index, daily_df['level'], 100, color=month_color, alpha=0.1)
        
        # Annotation Logic
        # If Positive Month -> Highlight BOTTOM (Best entry opportunity)
        # If Negative Month -> Highlight PEAK (Best shorting opportunity)
        
        if is_positive_month:
            # Find Bottom
            bottom_idx = daily_df['level'].idxmin()
            bottom_val = daily_df['level'].min()
            
            ax.annotate(f'BOTTOM: DAY {bottom_idx}', 
                       xy=(bottom_idx, bottom_val), 
                       xytext=(bottom_idx, bottom_val - (bottom_val * 0.005)),
                       arrowprops=dict(facecolor=self.accent_green, shrink=0.05, width=0, headwidth=7),
                       fontsize=10, color=self.accent_green, fontweight='bold', ha='center', va='top')
        else:
            # Find Peak
            peak_idx = daily_df['level'].idxmax()
            peak_val = daily_df['level'].max()
            
            ax.annotate(f'PEAK: DAY {peak_idx}', 
                       xy=(peak_idx, peak_val), 
                       xytext=(peak_idx, peak_val + (peak_val * 0.005)),
                       arrowprops=dict(facecolor=self.accent_red, shrink=0.05, width=0, headwidth=7),
                       fontsize=10, color=self.accent_red, fontweight='bold', ha='center', va='bottom')

        # Axis Limits (Standardization)
        if y_lim:
            ax.set_ylim(y_lim)
        if x_lim:
            ax.set_xlim(x_lim)

        # Titles
        plt.suptitle(f'{asset_name} {month_name} PERFORMANCE BY TRADING DAY', 
                     fontsize=18, fontweight='bold', color=self.text_color, y=0.95)
        ax.set_title(f'Average Cumulative Return | {years_range}', 
                     fontsize=10, color=self.gray_text, pad=10)
        
        ax.set_xlabel('TRADING DAY OF MONTH', fontsize=10, color=self.gray_text)
        ax.set_ylabel('INDEXED VALUE (START=100)', fontsize=10, color=self.gray_text)
        
        # Formatting
        ax.grid(True, linestyle=':', alpha=0.3)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.axhline(100, color=self.text_color, linewidth=1.0, alpha=0.3)
        
        # Set x ticks to integers only
        ax.xaxis.set_major_locator(mtick.MaxNLocator(integer=True))

        # Footer
        fig.text(0.1, 0.02, f"VAL 2.0 | {asset_name} Seasonality | {datetime.now().strftime('%d/%m/%Y')}", 
                 fontsize=8, color=self.gray_text)

        plt.tight_layout(rect=[0, 0.05, 1, 0.93])
        
        # Save in asset subdirectory
        asset_dir = os.path.join(self.output_dir, asset_name)
        if not os.path.exists(asset_dir):
            os.makedirs(asset_dir)

        filename = f"{asset_dir}/{asset_name}_{month_name.capitalize()}_daily_seasonality.png"
        plt.savefig(filename, dpi=300, bbox_inches='tight')
        plt.close()
        print(f"  Chart saved: {filename}")

    def plot_quarterly_daily_performance(self, daily_df: pd.DataFrame, asset_name: str, quarter: int, years_range: str):
        """
        Plots the cumulative performance for the entire quarter (~63 trading days).
        """
        # Increased height to width ratio to avoid "squashed" look
        fig, ax = plt.subplots(figsize=(12, 9))
        
        # Determine trend
        start_val = daily_df['level'].iloc[0]
        end_val = daily_df['level'].iloc[-1]
        is_positive = end_val > start_val
        curve_color = self.accent_green if is_positive else self.accent_red
        
        # Plot
        ax.plot(daily_df.index, daily_df['level'], linewidth=4, color=curve_color)
        ax.fill_between(daily_df.index, daily_df['level'], 100, color=curve_color, alpha=0.1)

        # Set x-limits explicitly to avoid empty space
        ax.set_xlim(daily_df.index.min(), daily_df.index.max())
        ax.margins(x=0) # IMPORTANT: Removes the whitespace margins

        # Dynamic offset calculation to avoid squashing charts with low volatility
        min_val = daily_df['level'].min()
        max_val = daily_df['level'].max()
        data_range = max_val - min_val
        
        # Use 15% of the range as offset, with a small minimum floor
        offset_magnitude = max(data_range * 0.15, 0.2)

        # Annotate Peak/Bottom
        if is_positive:
            target_idx = daily_df['level'].idxmin()
            target_val = daily_df['level'].min()
            label = f'BOTTOM: DAY {target_idx}'
            va = 'top'
            text_y = target_val - offset_magnitude
        else:
            target_idx = daily_df['level'].idxmax()
            target_val = daily_df['level'].max()
            label = f'PEAK: DAY {target_idx}'
            va = 'bottom'
            text_y = target_val + offset_magnitude

        ax.annotate(label, 
                   xy=(target_idx, target_val), 
                   xytext=(target_idx, text_y),
                   arrowprops=dict(facecolor=curve_color, shrink=0.05, width=0, headwidth=7),
                   fontsize=11, color=curve_color, fontweight='bold', ha='center', va=va)

        # Titles
        plt.suptitle(f'{asset_name} Q{quarter} PERFORMANCE BY TRADING DAY', 
                     fontsize=18, fontweight='bold', color=self.text_color, y=0.95)
        ax.set_title(f'Intra-Quarter Average Cumulative Return | {years_range}', 
                     fontsize=10, color=self.gray_text, pad=10)
        
        ax.set_xlabel('TRADING DAY OF QUARTER', fontsize=10, color=self.gray_text)
        ax.set_ylabel('INDEXED VALUE (START=100)', fontsize=10, color=self.gray_text)
        
        # Formatting
        ax.grid(True, linestyle=':', alpha=0.3)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.axhline(100, color=self.text_color, linewidth=1.0, alpha=0.3)
        
        # Labels for every 5 days
        ax.xaxis.set_major_locator(mtick.MultipleLocator(5))

        # Footer
        footer_text = f"VAL 2.0 | {asset_name} Q{quarter} Seasonality | {datetime.now().strftime('%d/%m/%Y')}"
        fig.text(0.1, 0.02, footer_text, fontsize=8, color=self.gray_text)

        plt.tight_layout(rect=[0, 0.05, 1, 0.93])
        
        # Save
        asset_dir = os.path.join(self.output_dir, asset_name, "quarterly")
        os.makedirs(asset_dir, exist_ok=True)
        filename = f"{asset_dir}/{asset_name}_Q{quarter}_daily_path.png"
        plt.savefig(filename, dpi=300, bbox_inches='tight')
        plt.savefig(filename, dpi=300, bbox_inches='tight')
        plt.close()
        print(f"  Chart saved: {filename}")

    def plot_yearly_extremes(self, df_extremes: pd.DataFrame, asset_name: str, years_range: str):
        """
        Visualizes the distribution of Yearly Highs and Lows.
        """
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10), sharex=True)
        
        bins = np.linspace(1, 252, 26) # ~10 days per bin
        
        # Plot Lows
        ax1.hist(df_extremes['low_day'], bins=bins, color=self.accent_red, alpha=0.6, edgecolor=self.bg_color, label='Yearly Lows')
        low_mean = df_extremes['low_day'].mean()
        ax1.axvline(low_mean, color=self.accent_red, linestyle='--', linewidth=2)
        ax1.annotate(f'AVG LOW: DAY {low_mean:.0f}', xy=(low_mean, ax1.get_ylim()[1]*0.8), 
                    color=self.accent_red, fontweight='bold', ha='right', rotation=90)
        ax1.set_title('YEARLY LOWS DISTRIBUTION', color=self.text_color, loc='left', fontsize=12)
        
        # Plot Highs
        ax2.hist(df_extremes['high_day'], bins=bins, color=self.accent_green, alpha=0.6, edgecolor=self.bg_color, label='Yearly Highs')
        high_mean = df_extremes['high_day'].mean()
        ax2.axvline(high_mean, color=self.accent_green, linestyle='--', linewidth=2)
        ax2.annotate(f'AVG HIGH: DAY {high_mean:.0f}', xy=(high_mean, ax2.get_ylim()[1]*0.8), 
                    color=self.accent_green, fontweight='bold', ha='right', rotation=90)
        ax2.set_title('YEARLY HIGHS DISTRIBUTION', color=self.text_color, loc='left', fontsize=12)
        
        # Formatting
        for ax in [ax1, ax2]:
            ax.grid(True, linestyle=':', alpha=0.2)
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            ax.set_ylabel('FREQUENCY (YEARS)', color=self.gray_text)
            
        ax2.set_xlabel('TRADING DAY OF YEAR (1-252)', color=self.gray_text)
        
        # Add Month Labels on top
        month_days = [0, 21, 42, 63, 84, 105, 126, 147, 168, 189, 210, 231]
        month_names = ['JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN', 'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC']
        ax1.set_xticks(month_days)
        ax1.set_xticklabels(month_names)

        plt.suptitle(f'{asset_name} YEARLY EXTREMES ANALYSIS ({years_range})', 
                     fontsize=18, fontweight='bold', color=self.text_color, y=0.98)
        
        # Footer
        footer_text = f"VAL 2.0 | Statistical Extremes | clustering of Yearly Highs/Lows | {datetime.now().strftime('%d/%m/%Y')}"
        fig.text(0.1, 0.02, footer_text, fontsize=8, color=self.gray_text)
        
        plt.tight_layout(rect=[0, 0.05, 1, 0.95])
        
        # Save
        asset_dir = os.path.join(self.output_dir, asset_name)
        filename = f"{asset_dir}/{asset_name}_yearly_extremes.png"
        plt.savefig(filename, dpi=300, bbox_inches='tight')
        plt.close()
        print(f"  Chart saved: {filename}")

    def plot_monthly_extremes(self, df_extremes: pd.DataFrame, asset_name: str, years_range: str):
        """
        Visualizes the frequency of Yearly Highs and Lows by Month.
        """
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10))
        
        month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        
        # Calculate counts
        low_counts = df_extremes['low_month'].value_counts().reindex(range(1, 13), fill_value=0)
        high_counts = df_extremes['high_month'].value_counts().reindex(range(1, 13), fill_value=0)
        
        # Percentages
        total_years = len(df_extremes)
        low_pct = (low_counts / total_years) * 100
        high_pct = (high_counts / total_years) * 100
        
        # Plot Lows
        bars1 = ax1.bar(month_names, low_pct, color=self.accent_red, alpha=0.7, edgecolor=self.bg_color)
        ax1.set_title('YEARLY LOWS BY MONTH (%)', color=self.text_color, loc='left', fontsize=12, fontweight='bold')
        
        # Plot Highs
        bars2 = ax2.bar(month_names, high_pct, color=self.accent_green, alpha=0.7, edgecolor=self.bg_color)
        ax2.set_title('YEARLY HIGHS BY MONTH (%)', color=self.text_color, loc='left', fontsize=12, fontweight='bold')
        
        # Formatting & Labels
        for ax, bars in zip([ax1, ax2], [bars1, bars2]):
            ax.grid(True, axis='y', linestyle=':', alpha=0.2)
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            ax.set_ylabel('% OF YEARS', color=self.gray_text)
            ax.yaxis.set_major_formatter(mtick.PercentFormatter())
            
            # Add labels on top of bars
            for bar in bars:
                height = bar.get_height()
                if height > 0:
                    ax.text(bar.get_x() + bar.get_width()/2., height + 0.5,
                            f'{height:.1f}%', ha='center', va='bottom', 
                            color=self.text_color, fontsize=10, fontweight='bold')

        plt.suptitle(f'{asset_name} MONTHLY EXTREMES FREQUENCY ({years_range})', 
                     fontsize=18, fontweight='bold', color=self.text_color, y=0.98)
        
        # Footer
        footer_text = f"VAL 2.0 | Monthly Extremes Analysis | Probability of Yearly High/Low | {datetime.now().strftime('%d/%m/%Y')}"
        fig.text(0.1, 0.02, footer_text, fontsize=8, color=self.gray_text)
        
        plt.tight_layout(rect=[0, 0.05, 1, 0.95])
        
        # Save
        asset_dir = os.path.join(self.output_dir, asset_name)
        filename = f"{asset_dir}/{asset_name}_monthly_extremes.png"
        plt.savefig(filename, dpi=300, bbox_inches='tight')
        plt.close()
        print(f"  Chart saved: {filename}")

    def plot_quarterly_extremes(self, df_extremes: pd.DataFrame, asset_name: str, years_range: str):
        """
        Visualizes the frequency of Yearly Highs and Lows by Quarter.
        """
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 7))
        
        q_names = ['Q1', 'Q2', 'Q3', 'Q4']
        
        # Calculate counts
        low_counts = df_extremes['low_quarter'].value_counts().reindex(range(1, 5), fill_value=0)
        high_counts = df_extremes['high_quarter'].value_counts().reindex(range(1, 5), fill_value=0)
        
        # Percentages
        total_years = len(df_extremes)
        low_pct = (low_counts / total_years) * 100
        high_pct = (high_counts / total_years) * 100
        
        # Plot Lows
        bars1 = ax1.bar(q_names, low_pct, color=self.accent_red, alpha=0.7, edgecolor=self.bg_color)
        ax1.set_title('YEARLY LOWS BY QUARTER (%)', color=self.text_color, loc='left', fontsize=12, fontweight='bold')
        
        # Plot Highs
        bars2 = ax2.bar(q_names, high_pct, color=self.accent_green, alpha=0.7, edgecolor=self.bg_color)
        ax2.set_title('YEARLY HIGHS BY QUARTER (%)', color=self.text_color, loc='left', fontsize=12, fontweight='bold')
        
        # Formatting & Labels
        for ax, bars in zip([ax1, ax2], [bars1, bars2]):
            ax.grid(True, axis='y', linestyle=':', alpha=0.2)
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            ax.set_ylabel('% OF YEARS', color=self.gray_text)
            ax.yaxis.set_major_formatter(mtick.PercentFormatter())
            
            # Add labels on top of bars
            for bar in bars:
                height = bar.get_height()
                if height > 0:
                    ax.text(bar.get_x() + bar.get_width()/2., height + 0.5,
                            f'{height:.1f}%', ha='center', va='bottom', 
                            color=self.text_color, fontsize=11, fontweight='bold')

        plt.suptitle(f'{asset_name} QUARTERLY EXTREMES FREQUENCY ({years_range})', 
                     fontsize=18, fontweight='bold', color=self.text_color, y=0.98)
        
        # Footer
        footer_text = f"VAL 2.0 | Quarterly Extremes Analysis | Probability of Yearly High/Low | {datetime.now().strftime('%d/%m/%Y')}"
        fig.text(0.1, 0.02, footer_text, fontsize=8, color=self.gray_text)
        
        plt.tight_layout(rect=[0, 0.05, 1, 0.95])
        
        # Save
        asset_dir = os.path.join(self.output_dir, asset_name)
        filename = f"{asset_dir}/{asset_name}_quarterly_extremes.png"
        plt.savefig(filename, dpi=300, bbox_inches='tight')
        plt.close()
        print(f"  Chart saved: {filename}")

    def plot_conditional_edge(self, results: dict, asset_name: str, years_range: str):
        """
        Visualizes the lift in probability from the conditional signal.
        """
        fig, ax = plt.subplots(figsize=(10, 7))
        
        labels = ['RANDOM BASELINE\n(Any Year)', 'CONDITIONAL SIGNAL\n(If Q2 > Q1 High)']
        probs = [results['prob_benchmark'], results['prob_conditional']]
        colors = [self.line_color, self.accent_green]
        
        bars = ax.bar(labels, probs, color=colors, alpha=0.8, edgecolor=self.bg_color, width=0.6)
        
        # Add labels on top
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height + 2,
                    f'{height:.1f}%', ha='center', va='bottom', 
                    color=self.text_color, fontsize=14, fontweight='bold')
            
        # Draw Arrow for Lift
        lift = results['lift']
        # Arrow from baseline to conditional
        ax.annotate('', 
                    xy=(1, results['prob_conditional']), 
                    xytext=(1, results['prob_benchmark']),
                    arrowprops=dict(arrowstyle="<->", color=self.accent_green, linewidth=2))
        
        ax.text(1.05, (results['prob_benchmark'] + results['prob_conditional'])/2, 
                f'+{lift:.1f}% LIFT', color=self.accent_green, 
                fontsize=12, fontweight='bold', va='center')

        # Formatting
        ax.set_ylim(0, 100)
        ax.grid(True, axis='y', linestyle=':', alpha=0.2)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.set_ylabel('PROBABILITY OF LOW IN Q1', color=self.gray_text, fontsize=10)
        ax.yaxis.set_major_formatter(mtick.PercentFormatter())
        
        plt.suptitle(f'{asset_name} CONDITIONAL EDGE ANALYSIS', 
                     fontsize=18, fontweight='bold', color=self.text_color, y=0.95)
        ax.set_title(f'Signal: Breaking Q1 High in Q2 | Period: {years_range}', 
                     fontsize=10, color=self.gray_text, pad=20)

        # Footer
        footer_text = f"VAL 2.0 | Conditional Probability Logic | P(Low in Q1 | Breakout) | {datetime.now().strftime('%d/%m/%Y')}"
        fig.text(0.1, 0.02, footer_text, fontsize=8, color=self.gray_text)

        plt.tight_layout(rect=[0, 0.05, 1, 0.9])
        
        # Save
        asset_dir = os.path.join(self.output_dir, asset_name)
        filename = f"{asset_dir}/{asset_name}_conditional_edge.png"
        plt.savefig(filename, dpi=300, bbox_inches='tight')
        plt.close()
        print(f"  Chart saved: {filename}")

    def plot_monthly_confidence_progression(self, df_prog: pd.DataFrame, asset_name: str, years_range: str):
        """
        Plots the evolution of confidence that the Yearly Low is in.
        """
        fig, ax = plt.subplots(figsize=(12, 7))
        
        month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        # Filter month names to match df_prog months (which start at 2)
        x_labels = [month_names[m-1] for m in df_prog['month']]
        
        # Plot area
        ax.fill_between(x_labels, df_prog['prob'], color=self.accent_green, alpha=0.1)
        ax.plot(x_labels, df_prog['prob'], color=self.accent_green, marker='o', linewidth=3, markersize=8)
        
        # Add values on points
        for x, y in zip(x_labels, df_prog['prob']):
            ax.text(x, y + 2, f'{y:.1f}%', color=self.text_color, ha='center', fontweight='bold')

        # Formatting
        ax.set_ylim(0, 105)
        ax.grid(True, linestyle=':', alpha=0.2)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.set_ylabel('PROBABILITY THAT YEARLY LOW IS ALREADY IN', color=self.gray_text)
        ax.yaxis.set_major_formatter(mtick.PercentFormatter())
        
        plt.suptitle(f'{asset_name} LOW-LOCK CONFIDENCE CURVE', 
                     fontsize=18, fontweight='bold', color=self.text_color, y=0.98)
        ax.set_title('Condition: If current Month is a New Yearly High | Probability that Low occurred in previous months', 
                     fontsize=10, color=self.gray_text, pad=15)

        # Footer
        footer_text = f"VAL 2.0 | Monthly Progression Analysis | The 'Low is In' Confidence Factor | {datetime.now().strftime('%d/%m/%Y')}"
        fig.text(0.1, 0.02, footer_text, fontsize=8, color=self.gray_text)

        plt.tight_layout(rect=[0, 0.05, 1, 0.95])
        
        # Save
        asset_dir = os.path.join(self.output_dir, asset_name)
        filename = f"{asset_dir}/{asset_name}_confidence_curve.png"
        plt.savefig(filename, dpi=300, bbox_inches='tight')
        plt.close()
        print(f"  Chart saved: {filename}")
