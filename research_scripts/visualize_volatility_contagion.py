import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime
import os
from pathlib import Path

class VolatilityContagionGenerator:
    def __init__(self):
        # Core Colors (Strictly from VISUAL_STYLE_GUIDE.md v2.1)
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
        
    def generate(self, filename="volatility_contagion_matrix.png"):
        # Setup Figure (16x10 format)
        fig, ax = plt.subplots(figsize=(16, 10), dpi=300)
        fig.patch.set_facecolor(self.bg_color)
        ax.set_facecolor(self.bg_color)
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.axis('off')

        # 1. Main Title Area (At 0.92/0.88)
        plt.text(0.5, 0.92, "VOLATILITY CONTAGIO MATRIX (Σ)", 
                 color=self.text_color, fontsize=self.title_size, fontweight='bold', 
                 ha='center', va='center', family=self.font_family)
        
        plt.text(0.5, 0.88, "Daily 1-Sigma Breaches as Predictors of Weekly Expansion | NQ, ES, YM", 
                 color=self.gray_text, fontsize=self.subtitle_size, 
                 ha='center', va='center', family=self.font_family)

        # 2. Top Separator (At 0.84)
        ax.axhline(0.84, xmin=0.1, xmax=0.9, color=self.text_color, linewidth=0.5)

        # 3. Table Headers (At 0.78)
        headers = ["Asset", "Trigger", "P(W-Sigma)", "Base", "Edge", "T-Stat", "Grade"]
        col_positions = [0.12, 0.25, 0.40, 0.53, 0.65, 0.78, 0.90]
        
        for head, pos in zip(headers, col_positions):
            plt.text(pos, 0.78, head, color=self.text_color, fontsize=self.header_size - 1, 
                     ha='center', va='center', fontweight='bold', family=self.font_family)

        # 4. Contagion Data Rows (Audited T-Stats)
        data = [
            ["NQ", "BULL (+1.35%)", "32.9% BULL", "16.4%", "+16.5%", "7.44", "GOLD +"],
            ["NQ", "BEAR (-1.35%)", "31.5% BEAR", "12.5%", "+19.0%", "7.15", "GOLD +"],
            ["YM", "BULL (+1.06%)", "29.6% BULL", "11.8%", "+17.8%", "6.45", "GOLD +"],
            ["ES", "BULL (+1.09%)", "28.3% BULL", "12.0%", "+16.3%", "6.11", "GOLD +"],
            ["ES", "BEAR (-1.09%)", "29.5% BEAR", "10.1%", "+19.4%", "5.97", "GOLD +"],
            ["YM", "BEAR (-1.06%)", "29.7% BEAR", "9.6%",  "+20.1%", "5.60", "GOLD +"]
        ]

        start_y = 0.68
        row_spacing = 0.06 
        
        for i, row in enumerate(data):
            curr_y = start_y - (i * row_spacing)
            for j, val in enumerate(row):
                color = self.text_color
                
                # Highlight Signal Probabilities and Edges
                if "BULL" in val or "+" in val: color = self.accent_green
                if "BEAR" in val or "-" in val:
                    if j > 0: color = self.accent_red # Only color trigger/signal red, not the asset name
                
                # Conviction (GOLD +)
                if j == 6 and "GOLD +" in val: color = self.accent_green
                
                # Special row formatting for NQ/ES text color safety
                if j == 0 and val in ["NQ", "ES", "YM"]: color = self.text_color
                if j == 0 and "S&P" in val: color = self.text_color
                if j == 0 and "Dow" in val: color = self.text_color

                plt.text(col_positions[j], curr_y, val, color=color, 
                         fontsize=self.data_size, ha='center', va='center', family=self.font_family)

        # 5. Bottom Area Separator (At 0.32)
        ax.axhline(0.32, xmin=0.1, xmax=0.9, color=self.text_color, linewidth=0.5)

        # 6. Version & Methodology
        version_text = f"VAL 2.9   Periodo 2015-2025   AUDITED   {datetime.now().strftime('%d/%m/%Y')}"
        plt.text(0.1, 0.28, version_text, color=self.gray_text, fontsize=self.footer_size, 
                 ha='left', va='center', family=self.font_family)

        method_lines = [
            "P(W-Sigma): Probabilidad cierre semanal > 1-Sigma semanal DADO un dia 1-sigma diario.",
            "T-Stat: Significancia estadistica (Audit Pass > 2.0). Calidad de señal absoluta.",
            "Edge: Incremento sistematico en la probabilidad de expansion de Target."
        ]
        for i, line in enumerate(method_lines):
            plt.text(0.5, 0.22 - (i * 0.04), line, color=self.gray_text, 
                     fontsize=self.footer_size, ha='center', va='center', family=self.font_family)

        # 7. Bottom Highlight (At 0.08)
        highlight = "VOLATILITY SPILLOVER: Un dia Sigma duplica las probabilidades de Expansion Semanal."
        plt.text(0.5, 0.08, highlight, color=self.accent_green, 
                 fontsize=self.header_size, ha='center', va='center', fontweight='bold', family=self.font_family)

        # 8. MANDATORY BRANDING (At 0.04)
        watermark = "SPEC RESEARCH ®"
        plt.text(0.5, 0.04, watermark, color=self.gray_text, 
                 fontsize=self.footer_size, ha='center', va='center', family=self.font_family, alpha=0.5)

        # Output Management
        output_dir = Path("output/charts/Multi/weekly")
        output_dir.mkdir(parents=True, exist_ok=True)
        full_path = output_dir / filename
        
        plt.savefig(full_path, facecolor=self.bg_color, bbox_inches='tight')
        plt.close()
        print(f"Image saved to: {full_path}")

if __name__ == "__main__":
    generator = VolatilityContagionGenerator()
    generator.generate()
