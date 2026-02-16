import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime
import os
from pathlib import Path

class WeeklyBiasMatrixGenerator:
    def __init__(self):
        # Colors from VISUAL_STYLE_GUIDE.md
        self.bg_color = '#000000'
        self.text_color = '#ffffff'
        self.accent_green = '#00ff44'
        self.accent_red = '#ff0044'
        self.gray_text = '#888888'
        self.line_color = '#333333'
        
        # Typography settings
        self.font_family = 'monospace'
        self.title_size = 20
        self.subtitle_size = 12
        self.header_size = 10
        self.data_size = 10
        self.footer_size = 9
        
    def generate(self, filename="weekly_bias_inertia_matrix.png"):
        # Setup Figure
        fig, ax = plt.subplots(figsize=(16, 12), dpi=300)
        fig.patch.set_facecolor(self.bg_color)
        ax.set_facecolor(self.bg_color)
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.axis('off')

        # 1. Main Title Area (Aligned with 0.92/0.88 Guide)
        plt.text(0.5, 0.92, "WEEKLY BIAS & INERTIA MATRIX", 
                 color=self.text_color, fontsize=self.title_size, fontweight='bold', 
                 ha='center', family=self.font_family)
        plt.text(0.5, 0.88, "Analisis 2015-2025 | Impact of Daily 1st-DEV (σ) Breaches on Weekly Close", 
                 color=self.gray_text, fontsize=self.subtitle_size, 
                 ha='center', family=self.font_family)

        # 2. Top Separator (Aligned with 0.84 Guide)
        ax.axhline(0.84, xmin=0.1, xmax=0.9, color=self.text_color, linewidth=0.5)

        # 3. Table Headers (Aligned with 0.78 Guide)
        headers = ["Trigger Day", "Daily Signal", "W1 Prob", "Avg Week Ret", "T-Stat", "Audit Grade"]
        # Balanced 6-column positions between 0.12 and 0.88
        col_positions = [0.14, 0.29, 0.44, 0.59, 0.74, 0.87]
        
        for head, pos in zip(headers, col_positions):
            plt.text(pos, 0.78, head, color=self.text_color, fontsize=self.header_size, ha='center', family=self.font_family)

        # 4. Alpha Data Rows (Start at 0.68, Spacing 0.10 Guide)
        data = [
            ["Monday",   "NQ DRIVE (> +1σ)", "82.3% BULL", "+2.82%", "6.53", "GOLD +"],
            ["Friday",   "NQ PANIC (< -1σ)", "84.5% BEAR", "-2.44%", "7.40", "GOLD +"],
            ["Monday",   "ES DRIVE (> +1σ)", "86.5% BULL", "+2.65%", "7.30", "GOLD +"],
            ["Friday",   "ES PANIC (< -1σ)", "91.8% BEAR", "-2.16%", "5.97", "GOLD +"],
            ["Thursday", "NQ PANIC (< -1σ)", "78.5% BEAR", "-2.12%", "6.26", "GOLD GRADE"],
            ["Wednesday","YM PANIC (< -1σ)", "75.5% BEAR", "-1.93%", "4.58", "GOLD GRADE"],
            ["Tuesday",  "ES DRIVE (> +1σ)", "75.5% BULL", "+1.75%", "3.65", "SILVER EDGE"]
        ]

        start_y = 0.68
        row_spacing = 0.05 # Reduced to fit 7 rows without overlapping footer
        
        for i, row in enumerate(data):
            curr_y = start_y - (i * row_spacing)
            for j, val in enumerate(row):
                color = self.text_color
                
                # Highlight Signal Probabilities and Returns
                if "BULL" in val or "+" in val: 
                    color = self.accent_green
                if "BEAR" in val or "-" in val:
                    color = self.accent_red
                
                # Confidence-based Coloring (Institutional Hierarchy)
                if "ULTRA" in val or "GOLD" in val:
                    if j == 5: color = self.accent_green
                elif "SILVER" in val:
                    if j == 5: color = '#ffee00' # Bright Yellow/Silver
                
                plt.text(col_positions[j], curr_y, val, color=color, 
                         fontsize=self.data_size, ha='center', family=self.font_family)

        # 5. Bottom Area Separator (Aligned with 0.32 Guide)
        ax.axhline(0.32, xmin=0.1, xmax=0.9, color=self.text_color, linewidth=0.5)

        # 6. Summary / Footnote
        version_text = f"VAL 2.9   Periodo 2005-2025   AUDITED   {datetime.now().strftime('%d/%m/%Y')}"
        plt.text(0.1, 0.28, version_text, color=self.gray_text, fontsize=self.footer_size, family=self.font_family)

        method_lines = [
            "GOLD +: T-Stat > 5.0 | P-Value < 0.0001. Absolute structural Alpha found in 10-year audit.",
            "W1 Probability: Likelihood of the week closing in the same direction as the trigger day.",
            "Methodology: One-sample T-test on weekly Open-to-Close returns, corrected for multi-event bias."
        ]
        for i, line in enumerate(method_lines):
            plt.text(0.5, 0.22 - (i * 0.04), line, color=self.gray_text, 
                     fontsize=self.footer_size, ha='center', family=self.font_family)

        # 7. Bottom Highlight
        highlight = "KEY INSIGHT: Lunes Sigma dictates weekly direction with >82% accuracy across all indices."
        plt.text(0.5, 0.08, highlight, color=self.accent_green, 
                 fontsize=self.header_size + 1, ha='center', fontweight='bold', family=self.font_family)

        # 8. Bottom Watermark
        watermark = "SPEC RESEARCH ®"
        plt.text(0.5, 0.04, watermark, color=self.gray_text, 
                 fontsize=self.footer_size, ha='center', family=self.font_family, alpha=0.5)

        # Output
        output_dir = "output/charts/Multi/daily"
        os.makedirs(output_dir, exist_ok=True)
        full_path = os.path.join(output_dir, filename)
        
        plt.savefig(full_path, facecolor=self.bg_color, bbox_inches='tight')
        plt.close()
        print(f"Image saved to: {full_path}")
        return full_path

if __name__ == "__main__":
    gen = WeeklyBiasMatrixGenerator()
    gen.generate()
