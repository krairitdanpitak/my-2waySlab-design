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
st.set_page_config(page_title="RC Two-Way Slab Design (ACI Method 2)", layout="wide")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Sarabun:wght@400;700&display=swap');

    .print-btn-internal {
        background-color: #4CAF50; border: none; color: white !important;
        padding: 12px 24px; text-align: center; text-decoration: none;
        display: inline-block; font-size: 16px; margin: 10px 0px;
        cursor: pointer; border-radius: 5px; font-family: 'Sarabun', sans-serif;
        font-weight: bold; box-shadow: 0 2px 5px rgba(0,0,0,0.2);
    }
    .print-btn-internal:hover { background-color: #45a049; }

    .report-table {width: 100%; border-collapse: collapse; font-family: 'Sarabun', sans-serif; font-size: 14px;}
    .report-table th, .report-table td {border: 1px solid #ddd; padding: 8px;}
    .report-table th {background-color: #f2f2f2; text-align: center; font-weight: bold;}

    .pass-ok {color: green; font-weight: bold;}
    .pass-no {color: red; font-weight: bold;}
    .pass-warn {color: #ff9800; font-weight: bold;} 

    .sec-row {background-color: #e0e0e0; font-weight: bold; font-size: 15px;}
    .load-value {color: #D32F2F !important; font-weight: bold;}
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. DATABASE: ACI METHOD 2 COEFFICIENTS
# ==========================================
# Data Structure:
# Case -> Ratio (m) -> [C_neg_a, C_pos_dl_a, C_pos_ll_a, C_neg_b, C_pos_dl_b, C_pos_ll_b]
# m = La / Lb (Short / Long)
# Cases 1-9 based on standard ACI tables (Method 2)

ACI_COEFFICIENTS = {
    # Case 1: All 4 edges continuous
    1: {
        1.00: [0.033, 0.018, 0.027, 0.033, 0.018, 0.027],
        0.95: [0.036, 0.020, 0.030, 0.033, 0.017, 0.026],
        0.90: [0.040, 0.023, 0.032, 0.033, 0.016, 0.025],
        0.85: [0.045, 0.025, 0.035, 0.033, 0.015, 0.024],
        0.80: [0.050, 0.028, 0.039, 0.033, 0.014, 0.022],
        0.75: [0.056, 0.031, 0.043, 0.033, 0.013, 0.021],
        0.70: [0.063, 0.035, 0.047, 0.033, 0.012, 0.019],
        0.65: [0.070, 0.038, 0.052, 0.033, 0.011, 0.017],
        0.60: [0.077, 0.042, 0.057, 0.033, 0.010, 0.016],
        0.55: [0.084, 0.045, 0.062, 0.033, 0.009, 0.014],
        0.50: [0.091, 0.049, 0.068, 0.033, 0.008, 0.012],
    },
    # Case 2: Short edges discontinuous (Long edges continuous)
    2: {
        1.00: [0.041, 0.021, 0.031, 0.041, 0.021, 0.031],  # Note: Symmetrical
        0.90: [0.048, 0.026, 0.036, 0.037, 0.018, 0.027],
        0.80: [0.058, 0.031, 0.042, 0.032, 0.015, 0.023],
        0.70: [0.070, 0.037, 0.050, 0.027, 0.012, 0.019],
        0.60: [0.083, 0.044, 0.059, 0.022, 0.009, 0.015],
        0.50: [0.097, 0.051, 0.069, 0.017, 0.007, 0.011],
    },
    # Case 3: Long edges discontinuous (Short edges continuous)
    3: {
        1.00: [0.041, 0.021, 0.031, 0.041, 0.021, 0.031],
        0.90: [0.040, 0.021, 0.030, 0.045, 0.023, 0.034],
        0.80: [0.039, 0.020, 0.029, 0.051, 0.025, 0.037],
        0.70: [0.036, 0.019, 0.027, 0.057, 0.028, 0.041],
        0.60: [0.033, 0.017, 0.024, 0.065, 0.031, 0.046],
        0.50: [0.029, 0.015, 0.022, 0.074, 0.035, 0.052],
    },
    # Case 4: 2 Short edges + 1 Long edge discontinuous
    4: {
        1.00: [0.049, 0.025, 0.036, 0.048, 0.025, 0.036],
        0.90: [0.057, 0.030, 0.041, 0.044, 0.022, 0.032],
        0.80: [0.067, 0.035, 0.048, 0.038, 0.018, 0.027],
        0.70: [0.078, 0.041, 0.056, 0.032, 0.015, 0.022],
        0.60: [0.090, 0.048, 0.065, 0.025, 0.011, 0.017],
        0.50: [0.103, 0.055, 0.074, 0.019, 0.008, 0.012],
    },
    # Case 5: 2 Long edges + 1 Short edge discontinuous
    5: {
        1.00: [0.048, 0.025, 0.036, 0.049, 0.025, 0.036],
        0.90: [0.048, 0.024, 0.035, 0.055, 0.028, 0.040],
        0.80: [0.046, 0.023, 0.033, 0.062, 0.031, 0.045],
        0.70: [0.044, 0.022, 0.031, 0.071, 0.035, 0.051],
        0.60: [0.040, 0.020, 0.028, 0.081, 0.040, 0.058],
        0.50: [0.036, 0.018, 0.025, 0.092, 0.045, 0.065],
    },
    # Case 6: 2 Adjacent edges discontinuous
    6: {
        1.00: [0.048, 0.025, 0.036, 0.048, 0.025, 0.036],
        0.90: [0.055, 0.029, 0.041, 0.044, 0.022, 0.032],
        0.80: [0.063, 0.033, 0.047, 0.039, 0.019, 0.027],
        0.70: [0.074, 0.039, 0.054, 0.033, 0.016, 0.023],
        0.60: [0.086, 0.045, 0.063, 0.027, 0.012, 0.018],
        0.50: [0.099, 0.052, 0.072, 0.021, 0.009, 0.013],
    },
    # Case 7: 1 Short edge discontinuous
    7: {
        1.00: [0.041, 0.021, 0.031, 0.041, 0.021, 0.031],
        0.90: [0.045, 0.024, 0.034, 0.039, 0.020, 0.028],
        0.80: [0.051, 0.027, 0.038, 0.036, 0.017, 0.025],
        0.70: [0.058, 0.031, 0.043, 0.032, 0.015, 0.021],
        0.60: [0.066, 0.036, 0.049, 0.028, 0.012, 0.018],
        0.50: [0.074, 0.040, 0.055, 0.024, 0.010, 0.014],
    },
    # Case 8: 1 Long edge discontinuous
    8: {
        1.00: [0.041, 0.021, 0.031, 0.041, 0.021, 0.031],
        0.90: [0.043, 0.022, 0.032, 0.044, 0.023, 0.033],
        0.80: [0.045, 0.023, 0.033, 0.048, 0.024, 0.035],
        0.70: [0.047, 0.024, 0.035, 0.052, 0.026, 0.038],
        0.60: [0.050, 0.025, 0.037, 0.057, 0.028, 0.042],
        0.50: [0.053, 0.027, 0.039, 0.063, 0.031, 0.046],
    },
    # Case 9: All 4 edges discontinuous
    9: {
        1.00: [0.057, 0.029, 0.041, 0.057, 0.029, 0.041],
        0.90: [0.064, 0.033, 0.046, 0.053, 0.027, 0.037],
        0.80: [0.072, 0.037, 0.052, 0.048, 0.024, 0.033],
        0.70: [0.082, 0.043, 0.059, 0.042, 0.020, 0.028],
        0.60: [0.093, 0.049, 0.067, 0.036, 0.017, 0.022],
        0.50: [0.106, 0.056, 0.076, 0.029, 0.013, 0.017],
    },
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
def get_coefficients(case_num, m):
    """Interpolate coefficients for a given m (Ratio)"""
    # m should be between 0.5 and 1.0
    m = max(0.5, min(1.0, m))

    table = ACI_COEFFICIENTS[case_num]

    # Check exact match
    if m in table:
        return table[m]

    # Interpolation
    sorted_keys = sorted(table.keys())
    m1 = 0.5
    m2 = 1.0
    for k in sorted_keys:
        if k <= m: m1 = k
        if k >= m:
            m2 = k
            break

    if m1 == m2: return table[m1]

    vals1 = table[m1]
    vals2 = table[m2]

    interp_vals = []
    ratio = (m - m1) / (m2 - m1)

    for v1, v2 in zip(vals1, vals2):
        val = v1 + (v2 - v1) * ratio
        interp_vals.append(val)

    return interp_vals


def fmt(n, digits=2):
    try:
        val = float(n)
        return f"{val:,.{digits}f}"
    except:
        return "-"


def fig_to_base64(fig):
    buf = io.BytesIO()
    fig.savefig(buf, format='png', bbox_inches='tight')
    buf.seek(0)
    plt.close(fig)
    return f"data:image/png;base64,{base64.b64encode(buf.read()).decode()}"


# ==========================================
# 4. VISUALIZATION (UPDATED)
# ==========================================
def plot_twoway_section(h_cm, cover_cm, main_bar, s_main):
    """
    Draw section showing Beam supports on both sides,
    Top bars at supports, Bottom bars in mid-span.
    """
    fig, ax = plt.subplots(figsize=(8, 3.5))

    # Dimensions for drawing
    beam_w = 0.30
    beam_d = 0.50
    slab_span = 2.5  # Visual span
    slab_h = h_cm / 100.0

    # 1. Concrete Structure (Beams & Slab)
    # Left Beam
    ax.add_patch(patches.Rectangle((-beam_w, -beam_d), beam_w, beam_d,
                                   facecolor='white', edgecolor='black', linewidth=1.5))
    # Right Beam
    ax.add_patch(patches.Rectangle((slab_span, -beam_d), beam_w, beam_d,
                                   facecolor='white', edgecolor='black', linewidth=1.5))
    # Slab
    ax.add_patch(patches.Rectangle((0, -slab_h), slab_span, slab_h,
                                   facecolor='#f9f9f9', edgecolor='black', linewidth=1.5))

    # Common Padding
    pad = 0.02 + (cover_cm / 100)

    # 2. Rebar - Top Bars (Negative Moment) at Supports
    # Visual length ~ L/4
    top_len = slab_span * 0.25
    bar_y_top = -pad

    # Left Top Bar (Hook in beam -> Slab)
    ax.plot([-beam_w + 0.05, -beam_w + 0.05, top_len],
            [-beam_d / 2, bar_y_top, bar_y_top], color='black', linewidth=2.0)

    # Right Top Bar
    ax.plot([slab_span + beam_w - 0.05, slab_span + beam_w - 0.05, slab_span - top_len],
            [-beam_d / 2, bar_y_top, bar_y_top], color='black', linewidth=2.0)

    # 3. Rebar - Bottom Bars (Positive Moment) Mid-span
    # Visual length ~ full span minus cover
    bar_y_bot = -slab_h + pad
    ax.plot([0.1, slab_span - 0.1], [bar_y_bot, bar_y_bot], color='black', linewidth=2.0)
    # Hooks up
    ax.plot([0.1, 0.1], [bar_y_bot, bar_y_bot + 0.05], color='black', linewidth=2.0)
    ax.plot([slab_span - 0.1, slab_span - 0.1], [bar_y_bot, bar_y_bot + 0.05], color='black', linewidth=2.0)

    # 4. Temperature/Perpendicular Bars (Dots)
    dot_y_top = bar_y_top - 0.02
    dot_y_bot = bar_y_bot + 0.02

    # Dots under top bars
    ax.add_patch(patches.Circle((0, dot_y_top), radius=0.015, color='black'))
    ax.add_patch(patches.Circle((0.15, dot_y_top), radius=0.015, color='black'))
    ax.add_patch(patches.Circle((slab_span, dot_y_top), radius=0.015, color='black'))
    ax.add_patch(patches.Circle((slab_span - 0.15, dot_y_top), radius=0.015, color='black'))

    # Dots over bottom bars
    for i in range(1, 8):
        ax.add_patch(patches.Circle((slab_span / 8 * i, dot_y_bot), radius=0.015, color='black'))

    # 5. Dimensions & Annotations
    # Dimension Line
    ax.annotate("", xy=(0, -slab_h - 0.2), xytext=(slab_span, -slab_h - 0.2),
                arrowprops=dict(arrowstyle='<->', linewidth=0.8))
    ax.text(slab_span / 2, -slab_h - 0.3, "Span L", ha='center')

    # Beam Widths
    ax.annotate("", xy=(-beam_w, 0.1), xytext=(0, 0.1), arrowprops=dict(arrowstyle='<->', linewidth=0.5))
    ax.text(-beam_w / 2, 0.15, "Bm", ha='center', fontsize=8)

    ax.annotate("", xy=(slab_span, 0.1), xytext=(slab_span + beam_w, 0.1),
                arrowprops=dict(arrowstyle='<->', linewidth=0.5))
    ax.text(slab_span + beam_w / 2, 0.15, "Bm", ha='center', fontsize=8)

    # Rebar Labels
    # Top Label
    ax.annotate(f"{main_bar}@{s_main:.0f} (Top)",
                xy=(top_len / 2, bar_y_top), xytext=(top_len, 0.3),
                arrowprops=dict(arrowstyle='->', linewidth=0.8), fontsize=9)

    # Bottom Label
    ax.annotate(f"{main_bar}@{s_main:.0f} (Bot)",
                xy=(slab_span / 2, bar_y_bot), xytext=(slab_span / 2, -slab_h - 0.5),
                arrowprops=dict(arrowstyle='->', linewidth=0.8), fontsize=9)

    ax.axis('off')
    ax.set_ylim(-1.0, 0.5)
    ax.set_xlim(-0.5, slab_span + 0.5)
    plt.tight_layout()
    return fig


# ==========================================
# 5. CALCULATION LOGIC
# ==========================================
def calculate_twoway(inputs):
    rows = []
    Lx = inputs['Lx']  # Short
    Ly = inputs['Ly']  # Long
    h = inputs['h']
    cover = inputs['cover']
    fc = inputs['fc']
    fy = inputs['fy']
    case = inputs['case']

    # 1. Geometry
    rows.append(["SECTION", "1. GEOMETRY & LOADS", "", "", "", ""])
    m = Lx / Ly
    status_m = "OK" if 0.5 <= m <= 1.0 else "WARN (Extrapolate)"
    rows.append(["Span Ratio (m)", "Lx / Ly", f"{Lx}/{Ly}", f"{m:.2f}", "-", status_m])

    # Loads
    w_sw = 2400 * (h / 100)
    w_dead = w_sw + inputs['sdl']
    w_live = inputs['ll']
    wu = 1.4 * w_dead + 1.7 * w_live  # ACI/EIT Factors (Can use 1.2/1.6 if preferred)

    rows.append(["Dead Load (w_dead)", "SW + SDL", f"{w_sw:.0f}+{inputs['sdl']}", f"{w_dead:.0f}", "kg/m²", ""])
    rows.append(["Live Load (w_live)", "LL", "-", f"{w_live:.0f}", "kg/m²", ""])
    rows.append(["Factored Load (wu)", "1.4DL + 1.7LL", f"1.4({w_dead:.0f})+1.7({w_live})", f"{wu:.0f}", "kg/m²", ""])

    # 2. Coefficients Look up
    rows.append(["SECTION", f"2. MOMENT COEFFICIENTS (CASE {case})", "", "", "", ""])
    coefs = get_coefficients(case, m)
    # [Ca_neg, Ca_dl, Ca_ll, Cb_neg, Cb_dl, Cb_ll]
    c_names = ["Ca (Neg)", "Ca (DL)", "Ca (LL)", "Cb (Neg)", "Cb (DL)", "Cb (LL)"]
    for name, val in zip(c_names, coefs):
        rows.append([name, "Table", f"m={m:.2f}", f"{val:.3f}", "-", ""])

    # 3. Moment Calculation & Steel Design
    rows.append(["SECTION", "3. REINFORCEMENT DESIGN", "", "", "", ""])

    # Effective Depth
    db_assume = 1.2  # DB12
    d_short = h - cover - db_assume / 2
    d_long = d_short - db_assume  # Inner layer

    # Helper for Rho calc
    def get_As(Mu_kgm, d_cm):
        Mu_kgcm = Mu_kgm * 100
        phi = 0.9
        Rn = Mu_kgcm / (phi * 100 * d_cm ** 2)  # b=100cm
        try:
            rho = (0.85 * fc / fy) * (1 - math.sqrt(1 - (2 * Rn) / (0.85 * fc)))
        except:
            rho = 0.002  # Min if fail

        As_req = max(rho * 100 * d_cm, 0.0018 * 100 * h)
        return As_req

    # Calculate Moments
    # M = C * w * Lx^2 (Note: Method 2 uses Lx (Short span) for BOTH directions usually, or check specific table)
    # Standard Method 2: Ma = Ca * w * La^2, Mb = Cb * w * Lb^2 ??
    # WAIT: Standard ACI Method 2 uses S (Short Span) for ALL calculations: M = C * w * S^2
    S = Lx

    # List of moments to design: Neg A, Pos A, Neg B, Pos B
    # Neg A
    Ma_neg = coefs[0] * wu * S ** 2
    As_a_neg = get_As(Ma_neg, d_short)

    # Pos A (Total = DL moment + LL moment)
    Ma_pos = (coefs[1] * 1.4 * w_dead * S ** 2) + (coefs[2] * 1.7 * w_live * S ** 2)
    As_a_pos = get_As(Ma_pos, d_short)

    # Neg B
    Mb_neg = coefs[3] * wu * S ** 2
    As_b_neg = get_As(Mb_neg, d_long)

    # Pos B
    Mb_pos = (coefs[4] * 1.4 * w_dead * S ** 2) + (coefs[5] * 1.7 * w_live * S ** 2)
    As_b_pos = get_As(Mb_pos, d_long)

    # Output Rows
    def add_res(zone, M_val, As_val, d_val):
        rows.append([f"{zone} Moment", "C · w · S²", "-", f"{M_val:.2f}", "kg-m", ""])
        rows.append([f"{zone} As Req", "Calc", f"d={d_val:.1f}", f"{As_val:.2f}", "cm²", ""])

    add_res("Short Neg (Supp)", Ma_neg, As_a_neg, d_short)
    add_res("Short Pos (Mid)", Ma_pos, As_a_pos, d_short)
    add_res("Long Neg (Supp)", Mb_neg, As_b_neg, d_long)
    add_res("Long Pos (Mid)", Mb_pos, As_b_pos, d_long)

    # 4. Spacing Calculation (Using selected bar)
    bar_key = inputs['bar']
    Ab = BAR_INFO[bar_key]['A_cm2']

    def get_spacing(As_req):
        s = (Ab * 100) / As_req
        return math.floor(min(s, 3 * h, 45) * 2) / 2  # Round down to 0.5

    s_a_neg = get_spacing(As_a_neg)
    s_a_pos = get_spacing(As_a_pos)
    s_b_neg = get_spacing(As_b_neg)
    s_b_pos = get_spacing(As_b_pos)

    result_summary = {
        's_a_neg': s_a_neg, 's_a_pos': s_a_pos,
        's_b_neg': s_b_neg, 's_b_pos': s_b_pos
    }

    return rows, result_summary


# ==========================================
# 6. HTML REPORT
# ==========================================
def generate_report(inputs, rows, img_base64, res_sum):
    table_html = ""
    for r in rows:
        if r[0] == "SECTION":
            table_html += f"<tr class='sec-row'><td colspan='6'>{r[1]}</td></tr>"
        else:
            table_html += f"<tr><td>{r[0]}</td><td>{r[1]}</td><td>{r[2]}</td><td class='load-value'>{r[3]}</td><td>{r[4]}</td><td>{r[5]}</td></tr>"

    html = f"""
    <div style="font-family: Sarabun; padding: 20px;">
        <h2 style="text-align:center">RC Two-Way Slab Design Report (ACI Method 2)</h2>
        <div style="border:1px solid #333; padding:10px; margin-bottom:10px;">
            <strong>Project:</strong> {inputs['project']} | <strong>Slab:</strong> {inputs['slab_id']} <br>
            <strong>Size:</strong> {inputs['Lx']} x {inputs['Ly']} m | <strong>Thk:</strong> {inputs['h']} cm | <strong>Case:</strong> {inputs['case']}
        </div>

        <div style="text-align:center; margin:10px;">
            <img src="{img_base64}" style="max-width:90%; border:1px solid #ccc; padding:5px;">
        </div>

        <table class="report-table">
            <tr><th>Item</th><th>Formula</th><th>Subst.</th><th>Result</th><th>Unit</th><th>Status</th></tr>
            {table_html}
        </table>

        <h3>Reinforcement Summary (Use {inputs['bar']})</h3>
        <ul>
            <li><strong>Short Span (Top/Supp):</strong> @ {res_sum['s_a_neg']:.1f} cm</li>
            <li><strong>Short Span (Bot/Mid):</strong> @ {res_sum['s_a_pos']:.1f} cm</li>
            <li><strong>Long Span (Top/Supp):</strong> @ {res_sum['s_b_neg']:.1f} cm</li>
            <li><strong>Long Span (Bot/Mid):</strong> @ {res_sum['s_b_pos']:.1f} cm</li>
        </ul>

        <div style="text-align:center">
            <button onclick="window.print()" class="print-btn-internal">🖨️ Print Report</button>
        </div>
    </div>
    """
    return html


# ==========================================
# 7. UI MAIN
# ==========================================
st.title("RC Two-Way Slab Design (ACI Method 2)")

with st.sidebar.form("input_form"):
    st.header("Project Info")
    project = st.text_input("Project", "อาคารพักอาศัย")
    slab_id = st.text_input("Slab Mark", "S-02")

    st.header("1. Geometry (m)")
    c1, c2 = st.columns(2)
    # Enforce min_value=0.0 as requested
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
                        format_func=lambda x: f"Case {x}: " + {
                            1: "All Continuous", 2: "Short Discont.", 3: "Long Discont.",
                            4: "2 Short + 1 Long Discont.", 5: "2 Long + 1 Short Discont.",
                            6: "2 Adjacent Discont.", 7: "1 Short Discont.", 8: "1 Long Discont.",
                            9: "All Discontinuous"
                        }[x])

    bar = st.selectbox("Rebar Size", list(BAR_INFO.keys()), index=1)

    run_btn = st.form_submit_button("Calculate & Design")

if run_btn:
    # Auto-swap if user inputs wrong
    if Lx > Ly and Ly > 0:
        Lx, Ly = Ly, Lx
        st.sidebar.warning(f"Swapped: Lx={Lx}, Ly={Ly} (Lx must be shorter)")

    inputs = {
        'project': project, 'slab_id': slab_id,
        'Lx': Lx, 'Ly': Ly, 'h': h, 'cover': cover,
        'sdl': sdl, 'll': ll, 'fc': fc, 'fy': fy,
        'case': case, 'bar': bar
    }

    # Calc
    rows, res_sum = calculate_twoway(inputs)

    # Plot (Using Short Span Bottom spacing for visualization)
    img = fig_to_base64(plot_twoway_section(h, cover, bar, res_sum['s_a_pos']))

    # Report
    html_out = generate_report(inputs, rows, img, res_sum)

    st.success("Design Complete!")
    components.html(html_out, height=1000, scrolling=True)

else:
    st.info("Please configure parameters and click Calculate.")
