import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import numpy as np
from datetime import datetime
import os

class DailyAlphaMatrixGenerator:
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
        
    def generate(self, filename="daily_alpha_matrix_weekdays.png"):
        # Setup Figure
        fig, ax = plt.subplots(figsize=(16, 12), dpi=300)
        fig.patch.set_facecolor(self.bg_color)
        ax.set_facecolor(self.bg_color)
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.axis('off')

        # 1. Main Title Area (Aligned with 0.92/0.88 Guide)
        plt.text(0.5, 0.92, "DAILY ALPHA MATRIX: WEEK_DAY SIGMA EDGE", 
                 color=self.text_color, fontsize=self.title_size, fontweight='bold', 
                 ha='center', family=self.font_family)
        plt.text(0.5, 0.88, "Analisis 2015-2025 | D+1 Probability based on Daily Sigma | NQ, ES, YM", 
                 color=self.gray_text, fontsize=self.subtitle_size, 
                 ha='center', family=self.font_family)

        # 2. Top Separator (Aligned with 0.84 Guide)
        ax.axhline(0.84, xmin=0.1, xmax=0.9, color=self.text_color, linewidth=0.5)

        # 3. Table Headers (Aligned with 0.78 Guide)
        headers = ["Trigger Day", "Asset Condition", "D+1 Signal", "Prob(Signal)", "Avg Ret D+1", "Confidence"]
        # Balanced 6-column positions between 0.12 and 0.88
        col_positions = [0.14, 0.29, 0.44, 0.59, 0.74, 0.87]
        
        for head, pos in zip(headers, col_positions):
            plt.text(pos, 0.78, head, color=self.text_color, fontsize=self.header_size, ha='center', family=self.font_family)

        # 4. Alpha Data Rows (Start at 0.68, Spacing 0.10 Guide)
        data = [
            ["Tuesday",   "NQ < -1.28% (Panic)", "REBOUND (Wed)",   "55.4%", "+0.543%", "GOLD (T>2.1)"],
            ["Friday",    "YM < -1.02% (Panic)", "REBOUND (Mon)",   "67.9%", "+0.444%", "SILVER (T>1.5)"],
            ["Thursday",  "NQ > +1.43% (Drive)", "REVERSION (Fri)", "57.8%", "-0.271%", "BRONZE (T>1.4)"],
            ["Friday",    "NQ > +1.43% (Drive)", "CONTINUE (Mon)",  "64.5%", "+0.108%", "NOISE (T<0.5)"],
            ["Wednesday", "YM < -1.02% (Panic)", "REBOUND (Thu)",   "63.3%", "-0.115%", "NOISE (T<0.4)"]
        ]

        start_y = 0.68
        row_spacing = 0.08 # Adjusted for content density
        
        for i, row in enumerate(data):
            curr_y = start_y - (i * row_spacing)
            for j, val in enumerate(row):
                color = self.text_color
                
                # Highlight Signal Probabilities and Returns
                if "67.9%" in val or "64.5%" in val or "63.3%" in val or "+0.543%" in val:
                    color = self.accent_green
                
                # Confidence-based Coloring (Institutional Hierarchy)
                if "GOLD" in val:
                    color = self.accent_green
                elif "SILVER" in val:
                    color = '#ffee00' # Bright Yellow/Silver
                elif "BRONZE" in val:
                    color = '#cd7f32' # Bronze/Amber
                elif "NOISE" in val:
                    color = self.accent_red
                
                plt.text(col_positions[j], curr_y, val, color=color, 
                         fontsize=self.data_size, ha='center', family=self.font_family)

        # 5. Bottom Area Separator (Aligned with 0.32 Guide)
        ax.axhline(0.32, xmin=0.1, xmax=0.9, color=self.text_color, linewidth=0.5)

        # 6. Summary / Footnote
        version_text = f"VAL 2.8   Periodo 2005-2025   TRADING GRADE   {datetime.now().strftime('%d/%m/%Y')}"
        plt.text(0.1, 0.28, version_text, color=self.gray_text, fontsize=self.footer_size, family=self.font_family)

        method_lines = [
            "GOLD (T > 2.0): >95% Confidence. Institutional Grade. (NQ Tuesday)",
            "SILVER (T > 1.5): ~90% Confidence. Significant Alpha. (YM Friday)",
            "BRONZE (T > 1.3): ~80% Confidence. Moderate skew, tradable with tight stops."
        ]
        for i, line in enumerate(method_lines):
            plt.text(0.5, 0.22 - (i * 0.04), line, color=self.gray_text, 
                     fontsize=self.footer_size, ha='center', family=self.font_family)

        # 7. Bottom Highlight
        highlight = "WEEKEND ALPHA: 67.9% YM REBOUND | 64.5% NQ CONTINUATION | NEXT MONDAY TARGETS"
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
    gen = DailyAlphaMatrixGenerator()
    gen.generate()
