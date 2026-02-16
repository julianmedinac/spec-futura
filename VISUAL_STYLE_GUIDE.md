# VISUAL STYLE GUIDE: TRADING ANALYSIS TABLES
## Professional Terminal-Style Statistical Presentations

---

## 🎨 **COLOR PALETTE**

### **Core Colors**
```python
# Background
bg_color = '#000000'          # Pure black (terminal background)

# Text Colors  
text_color = '#ffffff'        # Pure white (primary text)
gray_text = '#888888'         # Gray for metadata/footnotes

# Accent Colors
accent_green = '#00ff44'      # Bright green (positive values, highlights)
accent_red = '#ff0044'        # Bright red (negative values, warnings)

# Lines
line_color = '#333333'        # Subtle gray for separators
```

### **Color Usage Rules**
- **Green (#00ff44)**: Positive edges, high probabilities (>60%), breakouts, highlights
- **Red (#ff0044)**: Negative edges, poor performance, warnings
- **White (#ffffff)**: Standard data, headers, neutral values
- **Gray (#888888)**: Metadata, version info, explanatory text, watermarks

---

## 📝 **TYPOGRAPHY**

### **Font Settings**
```python
font_family = 'monospace'     # Terminal-style monospace font

# Font Sizes (matching reference proportions)
title_size = 20              # Main title
subtitle_size = 12           # Subtitle/metadata 
header_size = 11             # Table headers
data_size = 11               # Table data
footer_size = 9              # Footer text/explanations
watermark_size = 9           # Branding/Watermark size
```

### **Typography Rules**
- **All text**: Monospace font family for terminal consistency
- **Title**: Bold, white, centered
- **Headers**: Normal weight, white, centered
- **Data**: Normal weight, color-coded by value type
- **Footer**: Small size, gray color for secondary info

---

## 📐 **LAYOUT STRUCTURE**

### **Canvas Setup**
```python
fig_size = (16, 10)          # Wide format for tables
dpi = 300                    # High resolution for crisp text
bg_color = '#000000'         # Pure black background
```

### **Positioning System** (transform coordinates 0-1)
```python
# Title Area
title_y = 0.92              # Main title position
subtitle_y = 0.88           # Subtitle position

# Table Area  
separator_top = 0.84        # Top separator line
headers_y = 0.78            # Table headers
data_start_y = 0.68         # First data row
row_spacing = 0.10          # Space between rows

# Footer Area
separator_bottom = 0.32     # Bottom separator line
version_y = 0.28            # Version/metadata info
explanation_start = 0.22    # Methodology explanation
highlight_y = 0.08          # Bottom highlight line

# Branding Area (MANDATORY)
watermark_y = 0.04          # "SPEC RESEARCH ®" position

# Horizontal Positioning (5-column table)
col_positions = [0.15, 0.35, 0.55, 0.7, 0.85]  # Center-aligned columns
```

### **Visual Elements**
```python
# Separator Lines
line_width = 0.001          # Thin lines
line_length = 0.8           # 80% of canvas width
line_x_start = 0.1          # 10% margin from left

# Spacing Rules
vertical_margin = 0.08      # Space around main content
horizontal_margin = 0.1     # Side margins
```

---

## ⚖️ **BRANDING (MANDATORY)**

Every visualization generated MUST include the following watermark at the bottom center:
**"SPEC RESEARCH ®"**

- **Color**: `gray_text` (#888888)
- **Alpha**: 0.5 (for subtle blending)
- **Font**: Monospace, size 9
- **Position**: `x=0.5` (centered), `y=0.04`

---

## 📊 **TABLE STRUCTURE**

### **Standard 5-Column Layout**
```python
headers = [
    "Condition",      # Setup classification (CLOSE>75, etc.)
    "P(breakout)",    # Breakout probability  
    "P(continuation)", # Continuation probability
    "Sigma",          # Edge vs 50% (statistical significance)
    "P(combined)"     # Combined probability
]

# Column Alignment: All center-aligned
# Column Widths: Evenly distributed with slight condition column bias
```

### **Data Formatting Rules**
```python
# Percentage Format
"XX.X%"                     # Always 1 decimal place

# Condition Format  
"CLOSE>XX"                  # Clear threshold indicators
"CLOSE<XX" 
"CLOSE>XX" / "CLOSE<XX"     # For comparative analysis

# Sigma Format
"+XX.X%" / "-XX.X%"         # Always include sign for edge indication
```

---

## 🎯 **COLOR CODING LOGIC**

### **Probability Values**
```python
def get_probability_color(value, threshold=60.0):
    """Color code probabilities based on performance."""
    if float(value.replace('%', '')) >= threshold:
        return accent_green      # Green for strong performance
    else:
        return text_color        # White for neutral/weak

def get_breakout_color(value, threshold=70.0):
    """Color code breakout probabilities.""" 
    if float(value.replace('%', '')) >= threshold:
        return accent_green      # Green for high breakout probability
    else:
        return text_color        # White for moderate
```

### **Edge/Sigma Values**
```python
def get_edge_color(value):
    """Color code edge values."""
    if value.startswith('+'):
        return accent_green      # Green for positive edge
    elif value.startswith('-'):
        return accent_red        # Red for negative edge
    else:
        return text_color        # White for neutral
```

---

## 📋 **CONTENT STRUCTURE**

### **Title Format**
```
MAIN_ANALYSIS_TYPE NQ (TIMEFRAME)
```
Examples:
- "CONTINUATION STRENGTH NQ (6AM→10AM)"
- "CONTINUATION STRENGTH NQ (10AM→2PM)" 
- "COMPARATIVE ANALYSIS NQ (6AM→10AM vs 10AM→2PM)"

### **Subtitle Format**
```
Analisis YEAR-YEAR | X,XXX casos | Bloque HH:MM-HH:MM EST
```
Example:
- "Analisis 2008-2025 | 4,232 casos | Bloque 06:00-10:00 EST"

### **Version Info Format**
```
VAL X.X   Periodo  YEAR-YEAR   OK   DD/MM/YYYY
```
Example:
- "VAL 2.0   Periodo  2008-2025   OK   15/08/2025"

### **Methodology Footer**
```python
method_lines = [
    "P(breakout) = Probabilidad nuevo high/low durante [TIMEFRAME]",
    "P(continuation) = Probabilidad continuation strength DADO breakout", 
    "Sigma = Margen error 95% confianza | Edge [POSITIVO/NEGATIVO] sistematico YEAR-YEAR"
]
```

### **Bottom Highlight Format**
```
KEY_METRIC: XX.X% edge PERFORMANCE_TYPE | KEY_METRIC: XX.X% edge PERFORMANCE_TYPE
```
Examples:
- "CLOSE>75: 90.3% edge breakout | CLOSE<25: 89.0% edge breakout"
- "CLOSE>50: 78.0% edge continuation | CLOSE<50: 74.4% edge continuation"

---

## 🛠️ **IMPLEMENTATION TEMPLATE**

### **Base Class Structure**
```python
class TradingTableGenerator:
    def __init__(self):
        # Colors
        self.bg_color = '#000000'
        self.text_color = '#ffffff' 
        self.accent_green = '#00ff44'
        self.accent_red = '#ff0044'
        self.gray_text = '#888888'
        self.line_color = '#333333'
        
        # Typography
        self.font_family = 'monospace'
        self.title_size = 20
        self.subtitle_size = 12
        self.header_size = 11
        self.data_size = 11
        self.footer_size = 9
        
    def add_branding(self, plt):
        """Mandatory watermark implementation."""
        plt.text(0.5, 0.04, "SPEC RESEARCH ®", color='#888888', 
                 fontsize=9, ha='center', family='monospace', alpha=0.5)

    def create_table(self, title, subtitle, data, filename):
        fig, ax = plt.subplots(figsize=(16, 10))
        fig.patch.set_facecolor(self.bg_color)
        ax.set_facecolor(self.bg_color)
        
        # Apply standard layout...
        # [Implementation follows structure above]

    def save_report(self, plt, filename):
        self.add_branding(plt) # Always call before saving
        plt.savefig(filename, facecolor='#000000', bbox_inches='tight')
```

### **Standard Workflow**
1. **Setup Canvas**: Black background, correct size
2. **Add Title**: Centered, white, bold
3. **Add Subtitle**: Centered, gray, metadata
4. **Top Separator**: Thin white line
5. **Table Headers**: Centered, white
6. **Data Rows**: Color-coded by value type
7. **Bottom Separator**: Thin white line
8. **Version Info**: Left-aligned, gray
9. **Methodology**: Centered, gray, multi-line
10. **Highlight**: Centered, green, key metrics
11. **Save**: High DPI, black background

---

## ✅ **QUALITY CHECKLIST**

### **Visual Consistency**
- [ ] Pure black background (#000000)
- [ ] Exact green (#00ff44) for positive values
- [ ] Monospace font throughout
- [ ] Centered alignment for all table content

### **Branding & Integrity** 
- [ ] **MANDATORY**: "SPEC RESEARCH ®" watermark included at y=0.04
- [ ] Version info correctly formatted (VAL X.X format)
- [ ] "GOLD +" used instead of "ULTRA GOLD" for top-tier signals

### **Color Logic** 
- [ ] Green for positive edges/high probabilities
- [ ] Red for negative edges/warnings
- [ ] White for neutral data
- [ ] Gray for metadata/explanations

### **Content Standards**
- [ ] Consistent percentage formatting (XX.X%)
- [ ] Clear condition labels (CLOSE>XX format)
- [ ] Proper version/date information
- [ ] Meaningful bottom highlight
- [ ] Professional terminology

### **Technical Quality**
- [ ] High resolution (300 DPI)
- [ ] Clean text rendering
- [ ] Proper file naming convention
- [ ] Correct canvas proportions

---

## 📁 **FILE NAMING CONVENTION**

```
[analysis_type]_[timeframe]_results.png
```

Examples:
- `continuation_6am_10am_results.png`
- `continuation_10am_2pm_results.png`
- `continuation_comparative_results.png`
- `probability_intraday_2020_2025.png`

---

## 🎯 **USAGE NOTES**

### **When to Use This Style**
- Statistical trading analysis presentations
- Probability tables for quantitative research
- Professional quant trading reports
- Terminal-style data visualization
- High-contrast statistical displays

### **Style Inspiration**
- Terminal/console interfaces
- Professional trading platforms  
- Quantitative research papers
- Financial data terminals
- Monospace statistical outputs

### **Key Principles**
1. **Clarity**: Information hierarchy through color and typography
2. **Professionalism**: Clean, terminal-inspired aesthetic
3. **Readability**: High contrast, monospace consistency
4. **Consistency**: Standardized layout and color logic
5. **Impact**: Strategic use of green/red for key insights

---

**Style Guide Version:** 2.1  
**Created:** 15 August 2025  
**Last Updated:** 15 February 2026  
**Compatible with:** Matplotlib, Professional Trading Analysis
**Status**: ACTIVE - MANDATORY BRANDING ENFORCED  

---

*"Consistency in visual presentation reflects precision in quantitative analysis."*