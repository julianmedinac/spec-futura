import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import numpy as np
from datetime import datetime
import os

class AlphaMatrixGenerator:
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
        self.header_size = 11
        self.data_size = 11
        self.footer_size = 9
        
    def generate(self, filename="alpha_matrix_weekly_nq.png"):
        # Setup Figure
        fig, ax = plt.subplots(figsize=(16, 10), dpi=300)
        fig.patch.set_facecolor(self.bg_color)
        ax.set_facecolor(self.bg_color)
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.axis('off')

        # 1. Title Area
        plt.text(0.5, 0.92, "ALPHA MATRIX NQ (WEEKLY)", 
                 color=self.text_color, fontsize=self.title_size, fontweight='bold', 
                 ha='center', family=self.font_family)
        plt.text(0.5, 0.88, "Analisis 2015-2025 | 520+ semanas | Bloque Semanal (Mon Open → Fri Close)", 
                 color=self.gray_text, fontsize=self.subtitle_size, 
                 ha='center', family=self.font_family)

        # 2. Top Separator
        ax.axhline(0.84, xmin=0.1, xmax=0.9, color=self.text_color, linewidth=0.5)

        # 3. Table Headers
        headers = ["Alpha Source", "Threshold", "Statistical Edge", "Tactical Expectation", "Confidence"]
        col_positions = [0.15, 0.35, 0.55, 0.75, 0.90]
        
        for head, pos in zip(headers, col_positions):
            plt.text(pos, 0.78, head, color=self.text_color, fontsize=self.header_size, ha='center', family=self.font_family)

        # 4. Data Rows
        data = [
            ["BULL MOMENTUM", "CLOSE > +3.5%", "60.0% P(cont)", "CONTINUATION IN W+1", "HIGH"],
            ["MEAN REVERSION", "CLOSE < -2.7%", "55.4% P(rev)", "REBOUND +1.06% AVG", "MEDIUM"],
            ["VOL CLUSTERING", "EXTREME VOL", "4 WEEK MEDIAN", "RACHAS EVERY 1-3 WKS", "HIGH"],
            ["RANGE CEILING", "2-WEEK BLOCK", "9.4% LIMIT", "TP NEAR RANGE LIMIT", "STRUCTURAL"]
        ]

        start_y = 0.68
        spacing = 0.08
        
        for i, row in enumerate(data):
            curr_y = start_y - (i * spacing)
            for j, val in enumerate(row):
                # Color logic
                color = self.text_color
                if "60.0%" in val or "HIGH" in val or "LIMIT" in val:
                    color = self.accent_green
                if "REBOUND" in val and i == 1: # Highlight Mean Reversion result
                    color = self.accent_green
                
                plt.text(col_positions[j], curr_y, val, color=color, 
                         fontsize=self.data_size, ha='center', family=self.font_family)

        # 5. Bottom Separator
        ax.axhline(0.35, xmin=0.1, xmax=0.9, color=self.text_color, linewidth=0.5)

        # 6. Version Info
        version_text = f"VAL 2.1   Periodo 2015-2025   OK   {datetime.now().strftime('%d/%m/%Y')}"
        plt.text(0.1, 0.30, version_text, color=self.gray_text, fontsize=self.footer_size, family=self.font_family)

        # 7. Methodology
        method_lines = [
            "P(cont) = Probabilidad de cierre positivo en W+1 tras cierre extremo alcista",
            "P(rev) = Probabilidad de rebote alcista en W+1 tras cierre extremo bajista",
            "Range Ceiling = Expansion maxima esperada de la estructura en un bloque de 10 dias de trading"
        ]
        for i, line in enumerate(method_lines):
            plt.text(0.5, 0.24 - (i * 0.03), line, color=self.gray_text, 
                     fontsize=self.footer_size, ha='center', family=self.font_family)

        # 8. Bottom Highlight
        highlight = "MOMENTUM > 3.5%: 60.0% edge continuation | REVERSION < -2.7%: +1.06% edge performance"
        plt.text(0.5, 0.10, highlight, color=self.accent_green, 
                 fontsize=self.header_size, ha='center', fontweight='bold', family=self.font_family)

        # Output dir
        output_dir = "output/charts/NQ/weekly"
        os.makedirs(output_dir, exist_ok=True)
        full_path = os.path.join(output_dir, filename)
        
        plt.savefig(full_path, facecolor=self.bg_color, bbox_inches='tight')
        plt.close()
        print(f"Image saved to: {full_path}")
        return full_path

if __name__ == "__main__":
    gen = AlphaMatrixGenerator()
    gen.generate()
