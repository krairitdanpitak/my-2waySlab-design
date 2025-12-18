import streamlit as st
import matplotlib

matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import math
import io
import base64
import streamlit.components.v1 as components

# ==========================================
# 1. SETUP & CSS
# ==========================================
st.set_page_config(page_title="RC Two-Way Slab Design (Detailed Report)", layout="wide")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Sarabun:wght@400;700&display=swap');

    @media print {
        .no-print, .stAppHeader, .stSidebar, .stToolbar { display: none !important; }
        .main-content { margin: 0; padding: 0; }
        @page { margin: 0.5cm; size: A4; }
        body { -webkit-print-color-adjust: exact; }
    }

    .print-btn-custom {
        background-color: #4CAF50; border: none; color: white !important;
        padding: 10px 24px; text-align: center; text-decoration: none;
        display: inline-flex; align-items: center; gap: 8px;
        font-size: 16px; margin: 0 auto; cursor: pointer; border-radius: 5px; 
        font-family: 'Sarabun', sans-serif; font-weight: bold;
        box-shadow: 0 2px 4px rgba(0,0,0,0.2); transition: 0.3s;
    }
    .print-btn-custom:hover { background-color: #45a049; box-shadow: 0 4px 8px rgba(0,0,0,0.3); }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. DATABASE & CONSTANTS
# ==========================================
CASE_DESC = {
    1: "All Continuous", 2: "Short Discontinuous", 3: "Long Discontinuous",
    4: "2 Short + 1 Long Discont.", 5: "2 Long + 1 Short Discont.", 6: "2 Adjacent Discont.",
    7: "1 Short Discont.", 8: "1 Long Discont.", 9: "All Discontinuous"
}

ACI_COEFFICIENTS = {
    1: {1.00: [0.033, 0.018, 0.027, 0.033, 0.018, 0.027], 0.95: [0.036, 0.020, 0.030, 0.033, 0.017, 0.026],
        0.90: [0.040, 0.023, 0.032, 0.033, 0.016, 0.025], 0.85: [0.045, 0.025, 0.035, 0.033, 0.015, 0.024],
        0.80: [0.050, 0.028, 0.039, 0.033, 0.014, 0.022], 0.75: [0.056, 0.031, 0.043, 0.033, 0.013, 0.021],
        0.70: [0.063, 0.035, 0.047, 0.033, 0.012, 0.019], 0.65: [0.070, 0.038, 0.052, 0.033, 0.011, 0.017],
        0.60: [0.077, 0.042, 0.057, 0.033, 0.010, 0.016], 0.55: [0.084, 0.045, 0.062, 0.033, 0.009, 0.014],
        0.50: [0.091, 0.049, 0.068, 0.033, 0.008, 0.012]},
    2: {1.00: [0.041, 0.021, 0.031, 0.041, 0.021, 0.031], 0.90: [0.048, 0.026, 0.036, 0.037, 0.018, 0.027],
        0.80: [0.058, 0.031, 0.042, 0.032, 0.015, 0.023], 0.70: [0.070, 0.037, 0.050, 0.027, 0.012, 0.019],
        0.60: [0.083, 0.044, 0.059, 0.022, 0.009, 0.015], 0.50: [0.097, 0.051, 0.069, 0.017, 0.007, 0.011]},
    3: {1.00: [0.041, 0.021, 0.031, 0.041, 0.021, 0.031], 0.90: [0.040, 0.021, 0.030, 0.045, 0.023, 0.034],
        0.80: [0.039, 0.020, 0.029, 0.051, 0.025, 0.037], 0.70: [0.036, 0.019, 0.027, 0.057, 0.028, 0.041],
        0.60: [0.033, 0.017, 0.024, 0.065, 0.031, 0.046], 0.50: [0.029, 0.015, 0.022, 0.074, 0.035, 0.052]},
    4: {1.00: [0.049, 0.025, 0.036, 0.048, 0.025, 0.036], 0.90: [0.057, 0.030, 0.041, 0.044, 0.022, 0.032],
        0.80: [0.067, 0.035, 0.048, 0.038, 0.018, 0.027], 0.70: [0.078, 0.041, 0.056, 0.032, 0.015, 0.022],
        0.60: [0.090, 0.048, 0.065, 0.025, 0.011, 0.017], 0.50: [0.103, 0.055, 0.074, 0.019, 0.008, 0.012]},
    5: {1.00: [0.048, 0.025, 0.036, 0.049, 0.025, 0.036], 0.90: [0.048, 0.024, 0.035, 0.055, 0.028, 0.040],
        0.80: [0.046, 0.023, 0.033, 0.062, 0.031, 0.045], 0.70: [0.044, 0.022, 0.031, 0.071, 0.035, 0.051],
        0.60: [0.040, 0.020, 0.028, 0.081, 0.040, 0.058], 0.50: [0.036, 0.018, 0.025, 0.092, 0.045, 0.065]},
    6: {1.00: [0.048, 0.025, 0.036, 0.048, 0.025, 0.036], 0.90: [0.055, 0.029, 0.041, 0.044, 0.022, 0.032],
        0.80: [0.063, 0.033, 0.047, 0.039, 0.019, 0.027], 0.70: [0.074, 0.039, 0.054, 0.033, 0.016, 0.023],
        0.60: [0.086, 0.045, 0.063, 0.027, 0.012, 0.018], 0.50: [0.099, 0.052, 0.072, 0.021, 0.009, 0.013]},
    7: {1.00: [0.041, 0.021, 0.031, 0.041, 0.021, 0.031], 0.90: [0.045, 0.024, 0.034, 0.039, 0.020, 0.028],
        0.80: [0.051, 0.027, 0.038, 0.036, 0.017, 0.025], 0.70: [0.058, 0.031, 0.043, 0.032, 0.015, 0.021],
        0.60: [0.066, 0.036, 0.049, 0.028, 0.012, 0.018], 0.50: [0.074, 0.040, 0.055, 0.024, 0.010, 0.014]},
    8: {1.00: [0.041, 0.021, 0.031, 0.041, 0.021, 0.031], 0.90: [0.043, 0.022, 0.032, 0.044, 0.023, 0.033],
        0.80: [0.045, 0.023, 0.033, 0.048, 0.024, 0.035], 0.70: [0.047, 0.024, 0.035, 0.052, 0.026, 0.038],
        0.60: [0.050, 0.025, 0.037, 0.057, 0.028, 0.042], 0.50: [0.053, 0.027, 0.039, 0.063, 0.031, 0.046]},
    9: {1.00: [0.057, 0.029, 0.041, 0.057, 0.029, 0.041], 0.90: [0.064, 0.033, 0.046, 0.053, 0.027, 0.037],
        0.80: [0.072, 0.037, 0.052, 0.048, 0.024, 0.033], 0.70: [0.082, 0.043, 0.059, 0.042, 0.020, 0.028],
        0.60: [0.093, 0.049, 0.067, 0.036, 0.017, 0.022], 0.50: [0.106, 0.056, 0.076, 0.029, 0.013, 0.017]}
}

BAR_INFO = {
    'RB6': {'A_cm2': 0.283, 'd_mm': 6},
    'RB9': {'A_cm2': 0.636, 'd_mm': 9},
    'DB10': {'A_cm2': 0.785, 'd_mm': 10},
    'DB12': {'A_cm2': 1.131, 'd_mm': 12},
    'DB16': {'A_cm2': 2.011, 'd_mm': 16}
}


# ==========================================
# 3. HELPER FUNCTIONS
# ==========================================
def fmt(n, digits=2):
    try:
        val = float(n)
        if math.isnan(val): return "-"
        return f"{val:,.{digits}f}"
    except:
        return "-"


def get_coefficients(case_num, m):
    m = max(0.5, min(1.0, m))
    table = ACI_COEFFICIENTS[case_num]
    if m in table: return table[m]

    sorted_keys = sorted(table.keys())
    m1 = 0.5;
    m2 = 1.0
    for k in sorted_keys:
        if k <= m: m1 = k
        if k >= m: m2 = k; break
    if m1 == m2: return table[m1]

    vals1 = table[m1];
    vals2 = table[m2]
    interp_vals = []
    ratio = (m - m1) / (m2 - m1)
    for v1, v2 in zip(vals1, vals2):
        interp_vals.append(v1 + (v2 - v1) * ratio)
    return interp_vals


def fig_to_base64(fig):
    buf = io.BytesIO()
    fig.savefig(buf, format='png', bbox_inches='tight')
    buf.seek(0)
    plt.close(fig)
    return f"data:image/png;base64,{base64.b64encode(buf.read()).decode()}"


# ==========================================
# 4. PLOTTING FUNCTION (IMPROVED - FIXED VISUAL THICKNESS)
# ==========================================
def plot_twoway_section_detailed(h_cm, cover_cm, bar_name, res_sum, Lx_val):
    fig, ax = plt.subplots(figsize=(10, 5))
    beam_w = 0.30;
    beam_d = 0.50;
    slab_span = 2.5

    # ---------------------------------------------
    # FIXED VISUAL THICKNESS for Clarity
    # ---------------------------------------------
    # Instead of scaling h_cm directly which might be too thin (e.g. 0.10),
    # we use a fixed schematic height for drawing to ensure bars are separated.
    slab_h_draw = 0.25  # Schematic drawing height (fixed)

    # --- 1. Structure ---
    # Beams
    ax.add_patch(
        patches.Rectangle((-beam_w, -beam_d), beam_w, beam_d, facecolor='white', edgecolor='black', linewidth=1.5))
    ax.add_patch(
        patches.Rectangle((slab_span, -beam_d), beam_w, beam_d, facecolor='white', edgecolor='black', linewidth=1.5))
    # Slab (Using fixed schematic height)
    ax.add_patch(patches.Rectangle((0, -slab_h_draw), slab_span, slab_h_draw, facecolor='#f9f9f9', edgecolor='black',
                                   linewidth=1.5))

    # Padding for schematic
    pad = 0.04

    # --- 2. Short Span Bars (Lines) ---
    bar_y_top = -pad
    bar_y_bot = -slab_h_draw + pad
    top_len = slab_span * 0.25

    # Short Neg (Top Line)
    ax.plot([-beam_w + 0.05, -beam_w + 0.05, top_len], [-beam_d / 2, bar_y_top, bar_y_top], color='blue',
            linewidth=2.5)  # Left
    ax.plot([slab_span + beam_w - 0.05, slab_span + beam_w - 0.05, slab_span - top_len],
            [-beam_d / 2, bar_y_top, bar_y_top], color='blue', linewidth=2.5)  # Right

    # Short Pos (Bot Line)
    ax.plot([0.1, slab_span - 0.1], [bar_y_bot, bar_y_bot], color='blue', linewidth=2.5)
    ax.plot([0.1, 0.1], [bar_y_bot, bar_y_bot + 0.06], color='blue', linewidth=2.5)  # Hook
    ax.plot([slab_span - 0.1, slab_span - 0.1], [bar_y_bot, bar_y_bot + 0.06], color='blue', linewidth=2.5)  # Hook

    # --- 3. Long Span Bars (Dots) ---
    dot_y_top = bar_y_top - 0.025  # Under Short Top
    dot_y_bot = bar_y_bot + 0.025  # Over Short Bot

    # Long Neg (Top Dots)
    for x in [0, 0.15, slab_span, slab_span - 0.15]:
        ax.add_patch(patches.Circle((x, dot_y_top), radius=0.02, color='red'))

    # Long Pos (Bot Dots)
    for i in range(1, 8):
        ax.add_patch(patches.Circle((slab_span / 8 * i, dot_y_bot), radius=0.02, color='red'))

    # --- 4. Dimensions & Annotations ---

    # Dimension: Thickness (h) - Shows ACTUAL value
    ax.annotate("", xy=(slab_span + beam_w + 0.1, -slab_h_draw), xytext=(slab_span + beam_w + 0.1, 0),
                arrowprops=dict(arrowstyle='<->', linewidth=0.8))
    ax.text(slab_span + beam_w + 0.15, -slab_h_draw / 2, f"h = {h_cm / 100:.2f} m", va='center', rotation=90)

    # Dimension: Span (L) - Shows ACTUAL Lx Value
    ax.annotate("", xy=(0, -beam_d - 0.1), xytext=(slab_span, -beam_d - 0.1),
                arrowprops=dict(arrowstyle='<->', linewidth=0.8))
    ax.text(slab_span / 2, -beam_d - 0.2, f"L = {Lx_val:.2f} m", ha='center', fontweight='bold')

    # --- 5. Labels with Leader Lines ---

    # Short Span (Neg/Top)
    txt_short_neg = f"Short(Top): {bar_name}@{res_sum['s_a_neg']:.0f}cm"
    ax.annotate(txt_short_neg, xy=(top_len / 2, bar_y_top), xytext=(top_len, 0.4),
                arrowprops=dict(arrowstyle='->', connectionstyle="angle,angleA=0,angleB=90,rad=10", color='blue'),
                fontsize=9, color='blue', fontweight='bold',
                bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="blue", alpha=0.9))

    # Long Span (Neg/Top) - Pointing to dots
    txt_long_neg = f"Long(Top): {bar_name}@{res_sum['s_b_neg']:.0f}cm"
    ax.annotate(txt_long_neg, xy=(0.15, dot_y_top), xytext=(0.5, 0.2),
                arrowprops=dict(arrowstyle='->', color='red'),
                fontsize=9, color='red', fontweight='bold',
                bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="red", alpha=0.9))

    # Short Span (Pos/Bot)
    txt_short_pos = f"Short(Bot): {bar_name}@{res_sum['s_a_pos']:.0f}cm"
    ax.annotate(txt_short_pos, xy=(slab_span / 2, bar_y_bot), xytext=(slab_span / 2, -0.6),
                arrowprops=dict(arrowstyle='->', color='blue'),
                fontsize=9, ha='center', color='blue', fontweight='bold',
                bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="blue", alpha=0.9))

    # Long Span (Pos/Bot) - Pointing to dots
    txt_long_pos = f"Long(Bot): {bar_name}@{res_sum['s_b_pos']:.0f}cm"
    ax.annotate(txt_long_pos, xy=(slab_span / 2 + 0.3, dot_y_bot), xytext=(slab_span / 2 + 0.6, -0.4),
                arrowprops=dict(arrowstyle='->', color='red'),
                fontsize=9, color='red', fontweight='bold',
                bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="red", alpha=0.9))

    ax.axis('off')
    ax.set_ylim(-1.0, 0.6)
    ax.set_xlim(-0.5, slab_span + 0.8)
    plt.tight_layout()
    return fig


# ==========================================
# 5. CALCULATION LOGIC
# ==========================================
def calculate_detailed(inputs):
    rows = []

    def sec(title):
        rows.append(["SECTION", title, "", "", "", ""])

    def row(item, form, subst, res, unit, stat=""):
        rows.append([item, form, subst, res, unit, stat])

    Lx = inputs['Lx'];
    Ly = inputs['Ly'];
    h = inputs['h'];
    cov = inputs['cover']
    fc = inputs['fc'];
    fy = inputs['fy'];
    bar_name = inputs['bar']
    Ab = BAR_INFO[bar_name]['A_cm2']

    # 1. Geometry
    sec("1. GEOMETRY & LOADS")
    m = Lx / Ly
    row("Short Span", "Lx", "-", f"{Lx:.2f}", "m")
    row("Long Span", "Ly", "-", f"{Ly:.2f}", "m")
    row("Ratio m", "Lx / Ly", f"{Lx:.2f} / {Ly:.2f}", f"{m:.2f}", "-", "OK" if m >= 0.5 else "WARN")

    w_sw = 2400 * (h / 100);
    w_dl = w_sw + inputs['sdl'];
    w_ll = inputs['ll']
    wu = 1.4 * w_dl + 1.7 * w_ll
    row("Dead Load", "SW + SDL", f"{w_sw:.0f} + {inputs['sdl']}", f"{w_dl:.0f}", "kg/m²")
    row("Factored Load", "1.4DL + 1.7LL", f"1.4({w_dl:.0f}) + 1.7({w_ll})", f"{wu:.0f}", "kg/m²")

    # 2. Moments & Design
    case_id = inputs['case']
    sec(f"2. MOMENT & REINF. (CASE {case_id}: {CASE_DESC[case_id]})")
    coefs = get_coefficients(case_id, m)

    db = BAR_INFO[bar_name]['d_mm']
    d_short = h - cov - db / 20
    d_long = d_short - db / 10
    S = Lx

    def calc_As_Spacing(Mu_val, d_val):
        Mu_kgcm = Mu_val * 100
        Rn = Mu_kgcm / (0.9 * 100 * d_val ** 2)
        try:
            rho = (0.85 * fc / fy) * (1 - math.sqrt(1 - (2 * Rn) / (0.85 * fc)))
        except:
            rho = 0.002
        As_req = max(rho * 100 * d_val, 0.0018 * 100 * h)
        s = (Ab * 100) / As_req
        s_final = math.floor(min(s, 3 * h, 45) * 2) / 2
        return As_req, s, s_final

    # --- Short Neg ---
    Ma_neg = coefs[0] * wu * S ** 2
    As_a_neg, _, s_a_neg = calc_As_Spacing(Ma_neg, d_short)
    row("Ma (Neg)", "Ca_neg · wu · Lx²", f"{coefs[0]:.3f}·{wu:.0f}·{S}²", f"{Ma_neg:.2f}", "kg-m")
    row("As (Short-Neg)", "Calc", f"d={d_short:.2f}", f"{As_a_neg:.2f}", "cm²")
    row("• Spacing", f"Use {bar_name}", f"Max {3 * h:.0f} cm", f"@{s_a_neg:.1f}", "cm", "OK")

    # --- Short Pos ---
    Ma_pos = (coefs[1] * 1.4 * w_dl * S ** 2) + (coefs[2] * 1.7 * w_ll * S ** 2)
    As_a_pos, _, s_a_pos = calc_As_Spacing(Ma_pos, d_short)
    row("Ma (Pos)", "Ca_dl·D + Ca_ll·L", "-", f"{Ma_pos:.2f}", "kg-m")
    row("As (Short-Pos)", "Calc", f"d={d_short:.2f}", f"{As_a_pos:.2f}", "cm²")
    row("• Spacing", f"Use {bar_name}", f"Max {3 * h:.0f} cm", f"@{s_a_pos:.1f}", "cm", "OK")

    # --- Long Neg ---
    Mb_neg = coefs[3] * wu * S ** 2
    As_b_neg, _, s_b_neg = calc_As_Spacing(Mb_neg, d_long)
    row("Mb (Neg)", "Cb_neg · wu · Lx²", f"{coefs[3]:.3f}·{wu:.0f}·{S}²", f"{Mb_neg:.2f}", "kg-m")
    row("As (Long-Neg)", "Calc", f"d={d_long:.2f}", f"{As_b_neg:.2f}", "cm²")
    row("• Spacing", f"Use {bar_name}", f"Max {3 * h:.0f} cm", f"@{s_b_neg:.1f}", "cm", "OK")

    # --- Long Pos ---
    Mb_pos = (coefs[4] * 1.4 * w_dl * S ** 2) + (coefs[5] * 1.7 * w_ll * S ** 2)
    As_b_pos, _, s_b_pos = calc_As_Spacing(Mb_pos, d_long)
    row("Mb (Pos)", "Cb_dl·D + Cb_ll·L", "-", f"{Mb_pos:.2f}", "kg-m")
    row("As (Long-Pos)", "Calc", f"d={d_long:.2f}", f"{As_b_pos:.2f}", "cm²")
    row("• Spacing", f"Use {bar_name}", f"Max {3 * h:.0f} cm", f"@{s_b_pos:.1f}", "cm", "OK")

    res_sum = {'s_a_neg': s_a_neg, 's_a_pos': s_a_pos, 's_b_neg': s_b_neg, 's_b_pos': s_b_pos}

    sec("3. CHECK SHEAR")
    Vu = wu * Lx / 3
    Vc = 0.53 * math.sqrt(fc) * 100 * d_short
    phiVc = 0.85 * Vc
    status = "PASS" if phiVc >= Vu else "FAIL"
    row("Shear Check", "φVc ≥ Vu", f"{fmt(phiVc)} ≥ {fmt(Vu)}", status, "kg", status)

    return rows, res_sum


# ==========================================
# 6. HTML REPORT
# ==========================================
def generate_html_report(inputs, rows, img_base64, res_sum):
    table_rows = ""
    for r in rows:
        if r[0] == "SECTION":
            table_rows += f"<tr style='background-color:#ddd; font-weight:bold;'><td colspan='6'>{r[1]}</td></tr>"
        else:
            status_class = "pass-ok"
            if r[5] == "FAIL":
                status_class = "pass-no"
            elif "WARN" in r[5]:
                status_class = "pass-warn"
            bg = "background-color:#f9fbe7;" if "Spacing" in r[0] else ""
            table_rows += f"<tr style='{bg}'><td>{r[0]}</td><td>{r[1]}</td><td>{r[2]}</td><td style='color:#D32F2F; font-weight:bold;'>{r[3]}</td><td>{r[4]}</td><td class='{status_class}'>{r[5]}</td></tr>"

    html = f"""
    <!DOCTYPE html>
    <html lang="th">
    <head>
        <link href="https://fonts.googleapis.com/css2?family=Sarabun:wght@400;700&display=swap" rel="stylesheet">
        <style>
            body {{ font-family: 'Sarabun', sans-serif; padding: 20px; }}
            .report-table {{ width: 100%; border-collapse: collapse; font-size: 14px; margin-top: 20px; }}
            .report-table th, .report-table td {{ border: 1px solid #444; padding: 8px; }}
            .report-table th {{ background-color: #eee; text-align: center; }}
            .pass-ok {{ color: green; font-weight: bold; }}
            .pass-no {{ color: red; font-weight: bold; }}
            @media print {{ .no-print {{ display: none !important; }} }}
        </style>
    </head>
    <body>
        <div class="no-print" style="text-align: center; margin-bottom: 20px;">
            <button onclick="window.print()" style="background-color: #4CAF50; border: none; color: white; padding: 12px 24px; display: inline-flex; align-items: center; gap: 8px; font-size: 16px; cursor: pointer; border-radius: 5px; font-family: 'Sarabun'; font-weight: bold;">
                🖨️ Print This Page / พิมพ์หน้านี้
            </button>
        </div>

        <div style="border-bottom: 2px solid #333; padding-bottom: 10px; margin-bottom: 20px; position: relative;">
            <div style="position: absolute; top:0; right:0; border: 2px solid #000; padding: 5px 15px; font-weight: bold;">{inputs['slab_id']}</div>
            <h1 style="text-align:center; margin:0;">ENGINEERING DESIGN REPORT</h1>
            <h3 style="text-align:center; margin:5px;">RC Two-Way Slab Design (ACI Method 2)</h3>
        </div>

        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-bottom: 20px;">
            <div style="border: 1px solid #ddd; padding: 10px;">
                <strong>Project:</strong> {inputs['project']}<br>
                <strong>Engineer:</strong> {inputs['engineer']}<br>
                <strong>Date:</strong> 16/12/2568
            </div>
            <div style="border: 1px solid #ddd; padding: 10px;">
                <strong>Size:</strong> {inputs['Lx']} x {inputs['Ly']} m (Case {inputs['case']})<br>
                <strong>Thickness:</strong> {inputs['h']} cm (Cover {inputs['cover']} cm)<br>
                <strong>Materials:</strong> fc'={inputs['fc']}, fy={inputs['fy']} ksc
            </div>
        </div>

        <h3 style="text-align:center;">Design Visualization</h3>
        <div style="text-align:center; border:1px solid #eee; padding:10px;">
            <img src="{img_base64}" style="max-width:90%; height:auto;" />
        </div>

        <h3>Calculation Details</h3>
        <table class="report-table">
            <thead>
                <tr><th width="25%">Item</th><th width="20%">Formula</th><th width="20%">Substitution</th><th width="15%">Result</th><th width="10%">Unit</th><th width="10%">Status</th></tr>
            </thead>
            <tbody>{table_rows}</tbody>
        </table>

        <div style="margin-top: 40px; page-break-inside: avoid;">
            <h4>Reinforcement Summary (Use {inputs['bar']})</h4>
            <ul>
                <li><strong>Short Span (Neg/Top):</strong> @ {res_sum['s_a_neg']:.1f} cm</li>
                <li><strong>Short Span (Pos/Bot):</strong> @ {res_sum['s_a_pos']:.1f} cm</li>
                <li><strong>Long Span (Neg/Top):</strong> @ {res_sum['s_b_neg']:.1f} cm</li>
                <li><strong>Long Span (Pos/Bot):</strong> @ {res_sum['s_b_pos']:.1f} cm</li>
            </ul>
            <div style="width: 250px; text-align: center; margin-top: 20px;">
                <div style="text-align: left; font-weight: bold;">Designed by:</div>
                <div style="border-bottom: 1px solid #000; margin: 30px 0 5px 0;"></div>
                <div>({inputs['engineer']})</div>
                <div>Civil Engineer</div>
            </div>
        </div>
    </body>
    </html>
    """
    return html


# ==========================================
# 7. MAIN APP UI
# ==========================================
st.title("RC Two-Way Slab Design (Report Mode)")

with st.sidebar.form("input_form"):
    st.header("Project Info")
    project = st.text_input("Project Name", "อาคารพักอาศัย")
    slab_id = st.text_input("Slab Mark", "S-02")
    engineer = st.text_input("Engineer", "นายไกรฤทธิ์ ด่านพิทักษ์")

    st.header("1. Geometry (m)")
    c1, c2 = st.columns(2)
    Lx = c1.number_input("Short Span (Lx)", value=4.0, min_value=0.0, step=0.1)
    Ly = c2.number_input("Long Span (Ly)", value=5.0, min_value=0.0, step=0.1)
    h = st.number_input("Thickness (cm)", value=12.0, min_value=0.0, step=1.0)
    cover = st.number_input("Cover (cm)", value=2.5, min_value=0.0, step=0.5)

    st.header("2. Loads & Mat.")
    sdl = st.number_input("SDL (kg/m²)", value=150.0, min_value=0.0)
    ll = st.number_input("LL (kg/m²)", value=200.0, min_value=0.0)
    fc = st.number_input("fc' (ksc)", value=240.0, min_value=0.0)
    fy = st.number_input("fy (ksc)", value=4000.0, min_value=0.0)

    st.header("3. Design Parameters")
    case = st.selectbox("Case Type (Edge Conditions)", range(1, 10), index=0,
                        format_func=lambda x: f"{x}: {CASE_DESC[x]}")
    bar = st.selectbox("Rebar Size", list(BAR_INFO.keys()), index=1)

    run_btn = st.form_submit_button("Calculate & Preview")

if run_btn:
    if Lx > Ly and Ly > 0:
        Lx, Ly = Ly, Lx
        st.sidebar.warning(f"Auto-swapped: Lx={Lx}, Ly={Ly}")

    inputs = {
        'project': project, 'slab_id': slab_id, 'engineer': engineer,
        'Lx': Lx, 'Ly': Ly, 'h': h, 'cover': cover,
        'sdl': sdl, 'll': ll, 'fc': fc, 'fy': fy,
        'case': case, 'bar': bar
    }

    rows, res_sum = calculate_detailed(inputs)
    # Pass Lx to plot function for Dimension Label
    img_base64 = fig_to_base64(plot_twoway_section_detailed(h, cover, bar, res_sum, Lx))
    html_report = generate_html_report(inputs, rows, img_base64, res_sum)

    st.success("✅ Design Complete! See report below.")
    components.html(html_report, height=1300, scrolling=True)
else:
    st.info("👈 Enter design parameters in the sidebar to generate report.")