import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import numpy as np
from datetime import datetime
import os

class MultiAssetAlphaGenerator:
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
        self.title_size = 18
        self.subtitle_size = 10
        self.header_size = 9
        self.data_size = 10
        self.footer_size = 8
        
    def generate(self, filename="alpha_matrix_indices_weekly.png"):
        # Setup Figure - Increased height for 3 assets
        fig, ax = plt.subplots(figsize=(16, 14), dpi=300)
        fig.patch.set_facecolor(self.bg_color)
        ax.set_facecolor(self.bg_color)
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.axis('off')

        # 1. Main Title Area (Centering logic applied)
        plt.text(0.5, 0.96, "ALPHA MATRIX: NQ, ES & YM (WEEKLY)", 
                 color=self.text_color, fontsize=self.title_size, fontweight='bold', 
                 ha='center', va='center', family=self.font_family)
        plt.text(0.5, 0.92, "Analisis 2015-2025 | Bloque Semanal | Metodologia DOR 1-Sigma", 
                 color=self.gray_text, fontsize=self.subtitle_size, 
                 ha='center', va='center', family=self.font_family)

        headers = ["Alpha Source", "Threshold", "Statistical Edge", "Tactical Expectation", "Confidence"]
        col_positions = [0.15, 0.32, 0.50, 0.72, 0.88]

        # ----------------------------------------------------------------------
        # SECTION: NQ (NASDAQ 100)
        # ----------------------------------------------------------------------
        y_offset_nq = 0.87
        plt.text(0.1, y_offset_nq, ">> ASSET: NQ (NASDAQ 100 FUTURES)", 
                 color=self.accent_green, fontsize=12, fontweight='bold', ha='left', va='center', family=self.font_family)
        ax.axhline(y_offset_nq - 0.02, xmin=0.1, xmax=0.9, color=self.text_color, linewidth=0.5)
        
        for head, pos in zip(headers, col_positions):
            plt.text(pos, y_offset_nq - 0.05, head, color=self.text_color, fontsize=self.header_size, ha='center', va='center', family=self.font_family)

        nq_data = [
            ["BULL MOMENTUM", "CLOSE > +3.55%", "61.0% P(cont)", "STRONG CONTINUATION", "GOLD +"],
            ["MEAN REVERSION", "CLOSE < -2.73%", "55.8% P(rev)", "MODERATE REBOUND", "MEDIUM"],
            ["RANGE CEILING", "2-WEEK BLOCK", "9.39% LIMIT", "TP NEAR LIMIT", "STRUCTURAL"]
        ]

        row_y = y_offset_nq - 0.09
        for i, row in enumerate(nq_data):
            curr_y = row_y - (i * 0.04)
            for j, val in enumerate(row):
                color = self.accent_green if "61.0%" in val or "GOLD +" in val and j == 4 and i == 0 else self.text_color
                plt.text(col_positions[j], curr_y, val, color=color, fontsize=self.data_size, ha='center', va='center', family=self.font_family)

        # ----------------------------------------------------------------------
        # SECTION: ES (S&P 500)
        # ----------------------------------------------------------------------
        y_offset_es = 0.65
        plt.text(0.1, y_offset_es, ">> ASSET: ES (S&P 500 FUTURES)", 
                 color=self.accent_green, fontsize=12, fontweight='bold', ha='left', va='center', family=self.font_family)
        ax.axhline(y_offset_es - 0.02, xmin=0.1, xmax=0.9, color=self.text_color, linewidth=0.5)
        
        for head, pos in zip(headers, col_positions):
            plt.text(pos, y_offset_es - 0.05, head, color=self.text_color, fontsize=self.header_size, ha='center', va='center', family=self.font_family)

        es_data = [
            ["BULL MOMENTUM", "CLOSE > +2.98%", "54.3% P(cont)", "CONTINUATION IN W+1", "MEDIUM"],
            ["MEAN REVERSION", "CLOSE < -2.33%", "65.8% P(rev)", "HIGH PROB REBOUND", "GOLD +"],
            ["RANGE CEILING", "2-WEEK BLOCK", "8.10% LIMIT", "TP NEAR LIMIT", "STRUCTURAL"]
        ]

        row_y = y_offset_es - 0.09
        for i, row in enumerate(es_data):
            curr_y = row_y - (i * 0.04)
            for j, val in enumerate(row):
                color = self.accent_green if "65.8%" in val or "GOLD +" in val and j == 4 and i == 1 else self.text_color
                plt.text(col_positions[j], curr_y, val, color=color, fontsize=self.data_size, ha='center', va='center', family=self.font_family)

        # ----------------------------------------------------------------------
        # SECTION: YM (DOW JONES)
        # ----------------------------------------------------------------------
        y_offset_ym = 0.43
        plt.text(0.1, y_offset_ym, ">> ASSET: YM (DOW JONES FUTURES)", 
                 color=self.accent_green, fontsize=12, fontweight='bold', ha='left', va='center', family=self.font_family)
        ax.axhline(y_offset_ym - 0.02, xmin=0.1, xmax=0.9, color=self.text_color, linewidth=0.5)
        
        for head, pos in zip(headers, col_positions):
            plt.text(pos, y_offset_ym - 0.05, head, color=self.text_color, fontsize=self.header_size, ha='center', va='center', family=self.font_family)

        ym_data = [
            ["BULL MOMENTUM", "CLOSE > +2.90%", "56.2% P(cont)", "CONTINUATION IN W+1", "MEDIUM"],
            ["MEAN REVERSION", "CLOSE < -2.41%", "67.7% P(rev)", "CAPITULATION REBOUND", "GOLD +"],
            ["RANGE CEILING", "2-WEEK BLOCK", "7.92% LIMIT", "TP NEAR LIMIT", "STRUCTURAL"]
        ]

        row_y = y_offset_ym - 0.09
        for i, row in enumerate(ym_data):
            curr_y = row_y - (i * 0.04)
            for j, val in enumerate(row):
                color = self.accent_green if "67.7%" in val or "GOLD +" in val and j == 4 and i == 1 else self.text_color
                plt.text(col_positions[j], curr_y, val, color=color, fontsize=self.data_size, ha='center', va='center', family=self.font_family)

        # ----------------------------------------------------------------------
        # SECTION: Footer (Symmetrical alignment)
        # ----------------------------------------------------------------------
        ax.axhline(0.24, xmin=0.1, xmax=0.9, color=self.text_color, linewidth=0.5)
        
        version_text = f"VAL 2.9   Periodo 2015-2025   AUDITED   {datetime.now().strftime('%d/%m/%Y')}"
        plt.text(0.1, 0.20, version_text, color=self.gray_text, fontsize=self.footer_size, ha='left', va='center', family=self.font_family)
        
        method_note = "Metodologia: Analisis de persistencia 1-sigma basado en cierres semanales independientes."
        plt.text(0.5, 0.15, method_note, color=self.gray_text, fontsize=self.footer_size, ha='center', va='center', family=self.font_family)

        footer_note = "KEY_INSIGHT: NQ LEADS MOMENTUM (61%) | YM LEADS REVERSION (67.7%) | MAX RANGE CEILING: NQ (9.39%)"
        plt.text(0.5, 0.09, footer_note, color=self.accent_green, 
                 fontsize=self.header_size, ha='center', va='center', fontweight='bold', family=self.font_family)

        watermark = "SPEC RESEARCH ®"
        plt.text(0.5, 0.04, watermark, color=self.gray_text, 
                 fontsize=self.footer_size, ha='center', va='center', family=self.font_family, alpha=0.5)

        # Save
        output_dir = "output/charts/Multi/weekly"
        os.makedirs(output_dir, exist_ok=True)
        filename = "alpha_matrix_all_indices_weekly.png"
        full_path = os.path.join(output_dir, filename)
        
        plt.savefig(full_path, facecolor=self.bg_color, bbox_inches='tight')
        plt.close()
        print(f"Image saved to: {full_path}")
        return full_path

if __name__ == "__main__":
    gen = MultiAssetAlphaGenerator()
    gen.generate()
