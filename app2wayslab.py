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

    /* ซ่อน Elements ของ Streamlit เวลาสั่ง Print */
    @media print {
        .stAppHeader, .stSidebar, .stToolbar { display: none !important; }
        .no-print { display: none !important; }
        .main-content { margin: 0; padding: 0; }
        @page { margin: 0.5cm; size: A4; }
    }

    /* สไตล์ปุ่ม Print (เลียนแบบ Screenshot สีเขียว) */
    .print-btn-custom {
        background-color: #4CAF50; /* Green */
        border: none;
        color: white !important;
        padding: 10px 24px;
        text-align: center;
        text-decoration: none;
        display: inline-block;
        font-size: 16px;
        margin-bottom: 20px;
        cursor: pointer;
        border-radius: 4px; /* Rounded corners */
        font-family: 'Sarabun', sans-serif;
        font-weight: bold;
        box-shadow: 0 2px 4px rgba(0,0,0,0.2);
        transition: 0.3s;
    }
    .print-btn-custom:hover {
        background-color: #45a049;
        box-shadow: 0 4px 8px rgba(0,0,0,0.3);
    }
    .btn-container {
        text-align: center;
        width: 100%;
        margin-top: 10px;
        margin-bottom: 10px;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. DATABASE & CONSTANTS
# ==========================================
# ACI Method 2 Coefficients (Case 1-9)
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
    # m should be between 0.5 and 1.0
    m = max(0.5, min(1.0, m))
    table = ACI_COEFFICIENTS[case_num]
    if m in table: return table[m]

    # Interpolation
    sorted_keys = sorted(table.keys())
    m1 = 0.5;
    m2 = 1.0
    for k in sorted_keys:
        if k <= m: m1 = k
        if k >= m: m2 = k; break

    if m1 == m2: return table[m1]

    vals1 = table[m1]
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
# 4. PLOTTING FUNCTION
# ==========================================
def plot_twoway_section(h_cm, cover_cm, main_bar, s_main):
    fig, ax = plt.subplots(figsize=(8, 3.5))
    beam_w = 0.30;
    beam_d = 0.50;
    slab_span = 2.5;
    slab_h = h_cm / 100.0

    # Structure
    ax.add_patch(
        patches.Rectangle((-beam_w, -beam_d), beam_w, beam_d, facecolor='white', edgecolor='black', linewidth=1.5))
    ax.add_patch(
        patches.Rectangle((slab_span, -beam_d), beam_w, beam_d, facecolor='white', edgecolor='black', linewidth=1.5))
    ax.add_patch(
        patches.Rectangle((0, -slab_h), slab_span, slab_h, facecolor='#f9f9f9', edgecolor='black', linewidth=1.5))

    # Rebar
    pad = 0.02 + (cover_cm / 100)
    # Top Bars
    top_len = slab_span * 0.25;
    bar_y_top = -pad
    ax.plot([-beam_w + 0.05, -beam_w + 0.05, top_len], [-beam_d / 2, bar_y_top, bar_y_top], color='black',
            linewidth=2.0)
    ax.plot([slab_span + beam_w - 0.05, slab_span + beam_w - 0.05, slab_span - top_len],
            [-beam_d / 2, bar_y_top, bar_y_top], color='black', linewidth=2.0)

    # Bottom Bars
    bar_y_bot = -slab_h + pad
    ax.plot([0.1, slab_span - 0.1], [bar_y_bot, bar_y_bot], color='black', linewidth=2.0)
    ax.plot([0.1, 0.1], [bar_y_bot, bar_y_bot + 0.05], color='black', linewidth=2.0)
    ax.plot([slab_span - 0.1, slab_span - 0.1], [bar_y_bot, bar_y_bot + 0.05], color='black', linewidth=2.0)

    # Dots (Temp/Dist)
    dot_y_top = bar_y_top - 0.02;
    dot_y_bot = bar_y_bot + 0.02
    for x in [0, 0.15, slab_span, slab_span - 0.15]:
        ax.add_patch(patches.Circle((x, dot_y_top), radius=0.015, color='black'))
    for i in range(1, 8):
        ax.add_patch(patches.Circle((slab_span / 8 * i, dot_y_bot), radius=0.015, color='black'))

    # Annotations
    ax.annotate("", xy=(0, -slab_h - 0.2), xytext=(slab_span, -slab_h - 0.2),
                arrowprops=dict(arrowstyle='<->', linewidth=0.8))
    ax.text(slab_span / 2, -slab_h - 0.3, "Span L", ha='center')
    ax.annotate(f"{main_bar}@{s_main:.0f} (Top)", xy=(top_len / 2, bar_y_top), xytext=(top_len, 0.3),
                arrowprops=dict(arrowstyle='->'), fontsize=9)
    ax.annotate(f"{main_bar}@{s_main:.0f} (Bot)", xy=(slab_span / 2, bar_y_bot), xytext=(slab_span / 2, -slab_h - 0.5),
                arrowprops=dict(arrowstyle='->'), fontsize=9)

    ax.axis('off');
    ax.set_ylim(-1.0, 0.5);
    ax.set_xlim(-0.5, slab_span + 0.5)
    plt.tight_layout()
    return fig


# ==========================================
# 5. CALCULATION LOGIC (Detailed)
# ==========================================
def calculate_detailed(inputs):
    rows = []  # [Item, Formula, Substitution, Result, Unit, Status]

    def sec(title):
        rows.append(["SECTION", title, "", "", "", ""])

    def row(item, form, subst, res, unit, stat=""):
        rows.append([item, form, subst, res, unit, stat])

    Lx = inputs['Lx'];
    Ly = inputs['Ly'];
    h = inputs['h'];
    cov = inputs['cover']
    fc = inputs['fc'];
    fy = inputs['fy']

    # 1. Geometry
    sec("1. GEOMETRY & LOADS")
    m = Lx / Ly
    row("Short Span", "Lx", "-", f"{Lx:.2f}", "m")
    row("Long Span", "Ly", "-", f"{Ly:.2f}", "m")
    row("Ratio m", "Lx / Ly", f"{Lx:.2f} / {Ly:.2f}", f"{m:.2f}", "-", "OK" if m >= 0.5 else "WARN")

    # Loads
    w_sw = 2400 * (h / 100)
    w_dl = w_sw + inputs['sdl']
    w_ll = inputs['ll']
    wu = 1.4 * w_dl + 1.7 * w_ll

    row("Dead Load", "SW + SDL", f"{w_sw:.0f} + {inputs['sdl']}", f"{w_dl:.0f}", "kg/m²")
    row("Factored Load (wu)", "1.4DL + 1.7LL", f"1.4({w_dl:.0f}) + 1.7({w_ll})", f"{wu:.0f}", "kg/m²")

    # 2. Moments & Design
    sec(f"2. MOMENT & REINFORCEMENT (CASE {inputs['case']})")
    coefs = get_coefficients(inputs['case'], m)
    # coefs = [Ca_neg, Ca_dl, Ca_ll, Cb_neg, Cb_dl, Cb_ll]

    # Effective Depth
    db = BAR_INFO[inputs['bar']]['d_mm']
    d_short = h - cov - db / 20
    d_long = d_short - db / 10  # Upper layer

    # Helper for As
    def calc_As(Mu_val, d_val):
        Mu_kgcm = Mu_val * 100
        Rn = Mu_kgcm / (0.9 * 100 * d_val ** 2)
        try:
            rho = (0.85 * fc / fy) * (1 - math.sqrt(1 - (2 * Rn) / (0.85 * fc)))
        except:
            rho = 0.002
        As_req = max(rho * 100 * d_val, 0.0018 * 100 * h)
        return As_req

    # Moments (Using Short Span Lx for ALL Method 2 calc as per standard S^2)
    S = Lx

    # -- Short Neg --
    Ma_neg = coefs[0] * wu * S ** 2
    As_a_neg = calc_As(Ma_neg, d_short)
    row("Ma (Neg)", "Ca_neg · wu · Lx²", f"{coefs[0]:.3f}·{wu:.0f}·{S}²", f"{Ma_neg:.2f}", "kg-m")
    row("As (Short-Neg)", "Calc", f"d={d_short:.2f}", f"{As_a_neg:.2f}", "cm²")

    # -- Short Pos --
    Ma_pos = (coefs[1] * 1.4 * w_dl * S ** 2) + (coefs[2] * 1.7 * w_ll * S ** 2)
    As_a_pos = calc_As(Ma_pos, d_short)
    row("Ma (Pos)", "Ca_dl·1.4D + Ca_ll·1.7L", f"Details omitted", f"{Ma_pos:.2f}", "kg-m")
    row("As (Short-Pos)", "Calc", f"d={d_short:.2f}", f"{As_a_pos:.2f}", "cm²")

    # -- Long Neg --
    Mb_neg = coefs[3] * wu * S ** 2
    As_b_neg = calc_As(Mb_neg, d_long)
    row("Mb (Neg)", "Cb_neg · wu · Lx²", f"{coefs[3]:.3f}·{wu:.0f}·{S}²", f"{Mb_neg:.2f}", "kg-m")
    row("As (Long-Neg)", "Calc", f"d={d_long:.2f}", f"{As_b_neg:.2f}", "cm²")

    # -- Long Pos --
    Mb_pos = (coefs[4] * 1.4 * w_dl * S ** 2) + (coefs[5] * 1.7 * w_ll * S ** 2)
    As_b_pos = calc_As(Mb_pos, d_long)
    row("Mb (Pos)", "Cb_dl·1.4D + Cb_ll·1.7L", f"Details omitted", f"{Mb_pos:.2f}", "kg-m")
    row("As (Long-Pos)", "Calc", f"d={d_long:.2f}", f"{As_b_pos:.2f}", "cm²")

    # Spacing
    Ab = BAR_INFO[inputs['bar']]['A_cm2']

    def get_s(As):
        return math.floor(min((Ab * 100) / As, 3 * h, 45) * 2) / 2

    res_sum = {
        's_a_neg': get_s(As_a_neg), 's_a_pos': get_s(As_a_pos),
        's_b_neg': get_s(As_b_neg), 's_b_pos': get_s(As_b_pos)
    }

    sec("3. CHECK SHEAR")
    # Approximate Shear for Two-way (Simplified Conservative: wu * Lx / 3)
    Vu = wu * Lx / 3
    Vc = 0.53 * math.sqrt(fc) * 100 * d_short
    phiVc = 0.85 * Vc
    status = "PASS" if phiVc >= Vu else "FAIL"
    row("Shear Check", "φVc ≥ Vu", f"{fmt(phiVc)} ≥ {fmt(Vu)}", status, "kg", status)

    return rows, res_sum


# ==========================================
# 6. HTML REPORT GENERATOR (Table Format)
# ==========================================
def generate_html_report(inputs, rows, img_base64, res_sum):
    # Table Content
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

            table_rows += f"""
            <tr>
                <td>{r[0]}</td>
                <td>{r[1]}</td>
                <td>{r[2]}</td>
                <td style='color:#D32F2F; font-weight:bold;'>{r[3]}</td>
                <td>{r[4]}</td>
                <td class='{status_class}'>{r[5]}</td>
            </tr>
            """

    html = f"""
    <!DOCTYPE html>
    <html lang="th">
    <head>
        <link href="https://fonts.googleapis.com/css2?family=Sarabun:wght@400;700&display=swap" rel="stylesheet">
        <style>
            body {{ font-family: 'Sarabun', sans-serif; padding: 20px; }}
            .header {{ border-bottom: 2px solid #333; padding-bottom: 10px; margin-bottom: 20px; position: relative; }}
            .id-box {{ position: absolute; top:0; right:0; border: 2px solid #000; padding: 5px 15px; font-weight: bold; font-size: 18px; }}
            .info-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-bottom: 20px; }}
            .info-box {{ border: 1px solid #ddd; padding: 10px; }}
            .report-table {{ width: 100%; border-collapse: collapse; font-size: 14px; margin-top: 20px; }}
            .report-table th, .report-table td {{ border: 1px solid #444; padding: 8px; }}
            .report-table th {{ background-color: #eee; text-align: center; }}
            .pass-ok {{ color: green; font-weight: bold; }}
            .pass-no {{ color: red; font-weight: bold; }}

            /* Footer */
            .footer {{ margin-top: 40px; page-break-inside: avoid; }}
            .sign-box {{ width: 250px; text-align: center; margin-top: 20px; }}
            .line {{ border-bottom: 1px solid #000; margin: 30px 0 5px 0; }}
        </style>
    </head>
    <body>
        <div class="no-print btn-container">
            <button onclick="window.print()" class="print-btn-custom">
                🖨️ Print This Page / พิมพ์หน้านี้
            </button>
        </div>

        <div class="header">
            <div class="id-box">{inputs['slab_id']}</div>
            <h1 style="text-align:center; margin:0;">ENGINEERING DESIGN REPORT</h1>
            <h3 style="text-align:center; margin:5px;">RC Two-Way Slab Design (ACI Method 2)</h3>
        </div>

        <div class="info-grid">
            <div class="info-box">
                <strong>Project:</strong> {inputs['project']}<br>
                <strong>Engineer:</strong> {inputs['engineer']}<br>
                <strong>Date:</strong> 16/12/2568
            </div>
            <div class="info-box">
                <strong>Size:</strong> {inputs['Lx']} x {inputs['Ly']} m (Case {inputs['case']})<br>
                <strong>Thickness:</strong> {inputs['h']} cm (Cover {inputs['cover']} cm)<br>
                <strong>Materials:</strong> fc'={inputs['fc']}, fy={inputs['fy']} ksc
            </div>
        </div>

        <h3 style="text-align:center;">Design Visualization</h3>
        <div style="text-align:center; border:1px solid #eee; padding:10px;">
            <img src="{img_base64}" style="max-width:80%; height:auto;" />
        </div>

        <h3>Calculation Details</h3>
        <table class="report-table">
            <thead>
                <tr>
                    <th width="25%">Item</th><th width="20%">Formula</th><th width="20%">Substitution</th>
                    <th width="15%">Result</th><th width="10%">Unit</th><th width="10%">Status</th>
                </tr>
            </thead>
            <tbody>
                {table_rows}
            </tbody>
        </table>

        <div class="footer">
            <h4>Reinforcement Summary (Use {inputs['bar']})</h4>
            <ul>
                <li><strong>Short Span (Neg/Top):</strong> @ {res_sum['s_a_neg']:.1f} cm</li>
                <li><strong>Short Span (Pos/Bot):</strong> @ {res_sum['s_a_pos']:.1f} cm</li>
                <li><strong>Long Span (Neg/Top):</strong> @ {res_sum['s_b_neg']:.1f} cm</li>
                <li><strong>Long Span (Pos/Bot):</strong> @ {res_sum['s_b_pos']:.1f} cm</li>
            </ul>

            <div class="sign-box">
                <div style="text-align: left; font-weight: bold;">Designed by:</div>
                <div class="line"></div>
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
    case = st.selectbox("Case Type (Edge Conditions)", range(1, 10), index=0)
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

    # Process
    rows, res_sum = calculate_detailed(inputs)
    img_base64 = fig_to_base64(plot_twoway_section(h, cover, bar, res_sum['s_a_pos']))
    html_report = generate_html_report(inputs, rows, img_base64, res_sum)

    st.success("✅ Design Complete! See report below.")
    components.html(html_report, height=1300, scrolling=True)

else:
    st.info("👈 Enter design parameters in the sidebar to generate report.")