import streamlit as st
import matplotlib

matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import matplotlib.lines as mlines
import math
import io
import base64
import streamlit.components.v1 as components
from datetime import date

# ==========================================
# 1. SETUP & CSS (MATCHING UI)
# ==========================================
st.set_page_config(page_title="RC Two-Way Slab Design SDM", layout="wide")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Sarabun:wght@400;500;700&display=swap');

    body { font-family: 'Sarabun', sans-serif; }

    /* SUCCESS BOX STYLE (Green like screenshot) */
    .success-box {
        background-color: #d1e7dd;
        color: #0f5132;
        padding: 15px;
        border-radius: 5px;
        border: 1px solid #badbcc;
        font-family: 'Sarabun', sans-serif;
        font-weight: bold;
        display: flex;
        align-items: center;
        margin-bottom: 20px;
        font-size: 16px;
    }
    .success-icon { margin-right: 10px; font-size: 20px; }

    /* PRINT BUTTON STYLE (Green Gradient/Solid) */
    .print-btn-green {
        background-color: #28a745; 
        color: white !important; 
        padding: 12px 30px;
        border: none; 
        border-radius: 4px; 
        font-family: 'Sarabun', sans-serif;
        font-weight: bold; 
        cursor: pointer; 
        text-decoration: none;
        display: inline-block; 
        box-shadow: 0 2px 5px rgba(0,0,0,0.2);
        font-size: 16px;
    }
    .print-btn-green:hover { background-color: #218838; }

    /* REPORT CONTAINER */
    .report-container {
        font-family: 'Sarabun', sans-serif;
        max-width: 210mm;
        margin: 0 auto;
        padding: 40px;
        background-color: white;
    }

    /* HEADERS */
    .report-title { font-size: 26px; font-weight: bold; text-align: center; margin-bottom: 5px; color: #000; }
    .report-subtitle { font-size: 18px; font-weight: bold; text-align: center; margin-bottom: 25px; color: #333; }
    .id-box { 
        float: right; 
        border: 2px solid #000; 
        padding: 5px 15px; 
        font-weight: bold; 
        font-size: 18px;
    }

    /* INFO SECTION */
    .info-grid {
        display: flex;
        justify-content: space-between;
        border: 1px solid #ccc;
        background-color: #f8f9fa;
        padding: 20px;
        margin-bottom: 30px;
        border-radius: 4px;
        font-size: 14px;
    }
    .info-col { width: 48%; line-height: 1.8; }

    /* TABLE STYLES */
    .calc-table { width: 100%; border-collapse: collapse; font-size: 14px; margin-bottom: 20px; }
    .calc-table th { 
        background-color: #f1f3f5; 
        border: 1px solid #ced4da; 
        padding: 12px; 
        text-align: center; 
        font-weight: bold; 
        color: #333;
    }
    .calc-table td { border: 1px solid #ced4da; padding: 10px; vertical-align: middle; }
    .sec-row { background-color: #e9ecef; font-weight: bold; padding-left: 15px; text-transform: uppercase; color: #333; }

    /* STATUS COLORS */
    .status-pass { color: #198754; font-weight: bold; text-align: center; }
    .status-fail { color: #dc3545; font-weight: bold; text-align: center; }

    @media print {
        .no-print { display: none !important; }
        .report-container { width: 100%; max-width: none; padding: 0; }
        body { background-color: white; margin: 0; }
        @page { size: A4; margin: 1cm; }
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. DATA & LOGIC (Robust ACI Calc)
# ==========================================
BAR_INFO = {
    'RB6': {'A_cm2': 0.283, 'd_mm': 6},
    'RB9': {'A_cm2': 0.636, 'd_mm': 9},
    'DB10': {'A_cm2': 0.785, 'd_mm': 10},
    'DB12': {'A_cm2': 1.131, 'd_mm': 12},
    'DB16': {'A_cm2': 2.011, 'd_mm': 16},
    'DB20': {'A_cm2': 3.142, 'd_mm': 20}
}

ACI_METHOD2_DATA = {
    1: {1.0: [0., 0., .036, .036, .036, .036], 0.5: [0., 0., .095, .006, .095, .006]},
    2: {1.0: [.033, .033, .018, .018, .027, .027], 0.5: [.090, .004, .048, .003, .066, .005]},
    3: {1.0: [.033, .033, .018, .023, .027, .027], 0.5: [.090, .003, .048, .004, .066, .005]},
    4: {1.0: [.033, .033, .022, .018, .027, .027], 0.5: [.098, .003, .062, .003, .072, .005]},
    5: {1.0: [.033, .033, .018, .026, .027, .027], 0.5: [.090, .000, .048, .005, .066, .005]},
    6: {1.0: [.033, .033, .027, .018, .027, .027], 0.5: [.000, .003, .078, .003, .076, .005]},
    7: {1.0: [.033, .033, .022, .022, .028, .028], 0.5: [.098, .004, .062, .004, .074, .005]},
    8: {1.0: [.033, .000, .026, .022, .028, .028], 0.5: [.098, .000, .073, .004, .074, .005]},
    9: {1.0: [.000, .033, .022, .026, .028, .028], 0.5: [.000, .004, .062, .005, .074, .005]}
}


def get_coeffs(case, m):
    if m < 0.5: m = 0.5
    if m > 1.0: m = 1.0
    data = ACI_METHOD2_DATA.get(case, ACI_METHOD2_DATA[1])
    v05 = data.get(0.5)
    v10 = data.get(1.0)
    frac = (m - 0.5) / 0.5
    res = []
    for i in range(6):
        res.append(v05[i] + frac * (v10[i] - v05[i]))
    return res


def design_steel(Mu_kgm, d_cm, b_cm, fc, fy, h_cm, bar_key):
    # Safeguard for very small moments
    if Mu_kgm < 10:
        Mu_kgm = 0  # Assume min steel

    Mn = Mu_kgm * 100  # kg-cm
    phi = 0.90
    Rn = Mn / (phi * b_cm * d_cm ** 2)  # ksc

    # Check Max Reinforcement to avoid compression failure
    rho_max = 0.75 * (0.85 * 0.85 * fc / fy * (6120 / (6120 + fy)))
    # Check Min Reinforcement (Temp & Shrinkage)
    rho_min = 0.0018  # For fy=4000 (0.0020 for fy=2400)

    # Calculate rho required
    try:
        # standard quadratic formula from ACI
        term = 1 - 2 * Rn / (0.85 * fc)
        if term < 0:
            return 0, 0, "Fail (Thick.)"  # Section too small
        rho_calc = (0.85 * fc / fy) * (1 - math.sqrt(term))
    except:
        return 0, 0, "Calc Error"

    As_req = rho_calc * b_cm * d_cm
    As_min = rho_min * b_cm * h_cm

    As_final = max(As_req, As_min)

    # Bar spacing
    bar_area = BAR_INFO[bar_key]['A_cm2']
    if As_final > 0:
        s_calc = (bar_area * 100) / As_final
        # Max spacing ACI: 3h or 45cm
        s_max = min(3 * h_cm, 45.0)
        s_final = min(s_calc, s_max)

        # Round down to nearest 0.5 cm for practical spacing (or 1 cm)
        s_final = math.floor(s_final * 2) / 2
        return As_final, s_final, "OK"
    else:
        return 0, 0, "Error"


def fig_to_base64(fig):
    buf = io.BytesIO()
    fig.savefig(buf, format='png', bbox_inches='tight', dpi=150)
    buf.seek(0)
    return f"data:image/png;base64,{base64.b64encode(buf.read()).decode()}"


# ==========================================
# 3. PLOTTING FUNCTION (CAD STYLE)
# ==========================================
def plot_slab_cad_style(Lx, h, cover, main_bar, s_pos, s_neg):
    fig, ax = plt.subplots(figsize=(10, 4))

    h_m = h / 100
    cov_m = cover / 100
    beam_w = 0.25
    beam_h = 0.40

    # --- 1. CONCRETE OUTLINE ---
    # Slab Top
    ax.plot([-beam_w, Lx + beam_w], [h_m, h_m], 'k-', linewidth=1.0)
    # Slab Bottom (between beams)
    ax.plot([0, Lx], [0, 0], 'k-', linewidth=1.0)
    # Left Beam
    ax.plot([-beam_w, -beam_w], [h_m, -beam_h], 'k-', linewidth=1.0)
    ax.plot([0, 0], [0, -beam_h], 'k-', linewidth=1.0)
    ax.plot([-beam_w, 0], [-beam_h, -beam_h], 'k-', linewidth=1.0)
    # Right Beam
    ax.plot([Lx, Lx], [0, -beam_h], 'k-', linewidth=1.0)
    ax.plot([Lx + beam_w, Lx + beam_w], [h_m, -beam_h], 'k-', linewidth=1.0)
    ax.plot([Lx, Lx + beam_w], [-beam_h, -beam_h], 'k-', linewidth=1.0)

    # Centerlines (Dash-Dot)
    ax.plot([-beam_w / 2, -beam_w / 2], [-beam_h - 0.2, h_m + 0.5], 'k-.', linewidth=0.5)
    ax.plot([Lx + beam_w / 2, Lx + beam_w / 2], [-beam_h - 0.2, h_m + 0.5], 'k-.', linewidth=0.5)

    # --- 2. REINFORCEMENT ---
    y_bot = cov_m
    y_top = h_m - cov_m
    ext_L = Lx / 3.5  # Top bar extension approx L/3 or L/4

    # Bottom Bars
    ax.plot([-beam_w + 0.05, Lx + beam_w - 0.05], [y_bot, y_bot], 'k-', linewidth=1.2)
    # Hooks Bottom
    ax.plot([-beam_w + 0.05, -beam_w + 0.05], [y_bot, y_bot + 0.1], 'k-', linewidth=1.2)  # Left Hook
    ax.plot([Lx + beam_w - 0.05, Lx + beam_w - 0.05], [y_bot, y_bot + 0.1], 'k-', linewidth=1.2)  # Right Hook

    # Top Bars (Supports)
    if s_neg > 0:
        # Left Top
        ax.plot([-beam_w + 0.05, ext_L], [y_top, y_top], 'k-', linewidth=1.2)
        ax.plot([ext_L, ext_L], [y_top, y_top - 0.08], 'k-', linewidth=1.2)  # Hook down
        # Right Top
        ax.plot([Lx - ext_L, Lx + beam_w - 0.05], [y_top, y_top], 'k-', linewidth=1.2)
        ax.plot([Lx - ext_L, Lx - ext_L], [y_top, y_top - 0.08], 'k-', linewidth=1.2)  # Hook down

        # Temp bars (Dots) Top
        spacing_temp = 0.2
        n_temp = int(ext_L / spacing_temp)
        for i in range(n_temp + 1):
            ax.add_patch(patches.Circle((i * spacing_temp, y_top - 0.015), 0.008, color='black'))
            ax.add_patch(patches.Circle((Lx - i * spacing_temp, y_top - 0.015), 0.008, color='black'))

    # Temp bars (Dots) Bottom
    n_temp_bot = int(Lx / 0.2)
    for i in range(1, n_temp_bot):
        ax.add_patch(patches.Circle((i * 0.2, y_bot + 0.015), 0.008, color='black'))

    # --- 3. DIMENSIONS & LABELS (Engineering Style) ---
    def draw_dim_line(x1, x2, y, text):
        ax.plot([x1, x2], [y, y], 'k-', linewidth=0.5)
        # Ticks (Diagonal)
        tick_h = 0.05
        ax.plot([x1 - 0.02, x1 + 0.02], [y - tick_h, y + tick_h], 'k-', linewidth=0.8)  # Left tick
        ax.plot([x2 - 0.02, x2 + 0.02], [y - tick_h, y + tick_h], 'k-', linewidth=0.8)  # Right tick
        # Vertical leaders
        ax.plot([x1, x1], [y - 0.1, y], 'k-', linewidth=0.3)
        ax.plot([x2, x2], [y - 0.1, y], 'k-', linewidth=0.3)
        # Text
        ax.text((x1 + x2) / 2, y + 0.05, text, ha='center', va='bottom', fontsize=9)

    # Span Dimension
    span_y = -beam_h - 0.2
    draw_dim_line(0, Lx, span_y, f"{Lx:.2f} m.")

    # Top Bar Extension Dimension
    if s_neg > 0:
        ext_y = y_top + 0.2
        draw_dim_line(0, ext_L, ext_y, f"{ext_L:.2f}")
        draw_dim_line(Lx - ext_L, Lx, ext_y, f"{ext_L:.2f}")

        # Label Top Bar
        ax.annotate(f"{main_bar}@{s_neg:.2f}", xy=(ext_L / 2, y_top), xytext=(ext_L / 2, y_top + 0.4),
                    arrowprops=dict(arrowstyle='->', lw=0.8), ha='center', fontsize=9)
        ax.annotate(f"{main_bar}@{s_neg:.2f}", xy=(Lx - ext_L / 2, y_top), xytext=(Lx - ext_L / 2, y_top + 0.4),
                    arrowprops=dict(arrowstyle='->', lw=0.8), ha='center', fontsize=9)

    # Label Bottom Bar
    ax.annotate(f"{main_bar}@{s_pos:.2f}", xy=(Lx / 2, y_bot), xytext=(Lx / 2, y_bot - 0.3),
                arrowprops=dict(arrowstyle='->', lw=0.8), ha='center', fontsize=9)

    # Title
    ax.text(Lx / 2, h_m + 0.6, "TYPICAL REINFORCEMENT DETAIL", ha='center', fontsize=11, fontweight='bold')

    ax.set_ylim(-1.0, h_m + 0.8)
    ax.set_xlim(-0.5, Lx + 0.5)
    ax.axis('off')
    return fig


# ==========================================
# 4. REPORT GENERATOR
# ==========================================
def generate_html_report(inputs, rows, img_b64):
    today_str = date.today().strftime("%d/%m/%Y")

    table_html = ""
    for r in rows:
        if r[0] == "SECTION":
            table_html += f"<tr class='sec-row'><td colspan='6'>{r[1]}</td></tr>"
        else:
            cls = "status-pass" if r[5] in ["OK", "PASS"] else ("status-fail" if r[5] in ["FAIL"] else "")
            table_html += f"""
            <tr>
                <td>{r[0]}</td>
                <td style='color:#555;'>{r[1]}</td>
                <td>{r[2]}</td>
                <td style='font-weight:bold;'>{r[3]}</td>
                <td style='text-align:center;'>{r[4]}</td>
                <td class='{cls}'>{r[5]}</td>
            </tr>
            """

    html = f"""
    <div class="success-box no-print">
        <span class="success-icon">✅</span> คำนวณเสร็จสิ้น (Calculation Finished)
    </div>

    <div class="no-print" style="text-align: center; margin-bottom: 30px;">
        <button onclick="window.print()" class="print-btn-green">🖨️ Print This Page / พิมพ์หน้านี้</button>
    </div>

    <div class="report-container">
        <div class="id-box">{inputs['slab_id']}</div>
        <div class="report-title">ENGINEERING DESIGN REPORT</div>
        <div class="report-subtitle">RC Two-Way Slab Design SDM</div>

        <div class="info-grid">
            <div class="info-col">
                <strong>Project:</strong> {inputs['project']}<br>
                <strong>Engineer:</strong> {inputs['engineer']}<br>
                <strong>Date:</strong> {today_str}
            </div>
            <div class="info-col">
                <strong>Materials:</strong> fc'={inputs['fc']} ksc, fy={inputs['fy']} ksc<br>
                <strong>Section:</strong> {inputs['Lx']} x {inputs['Ly']} m.<br>
                <strong>Thickness:</strong> {inputs['h']} cm (Cover {inputs['cover']} cm)
            </div>
        </div>

        <div style="font-weight:bold; font-size:16px; margin-bottom:10px;">Design Visualization</div>
        <div style="text-align:center; border:1px solid #ddd; padding:10px; margin-bottom:20px;">
            <img src="{img_b64}" style="max-width:100%;">
        </div>

        <div style="font-weight:bold; font-size:16px; margin-bottom:10px;">Calculation Details</div>
        <table class="calc-table">
            <thead>
                <tr>
                    <th width="20%">Item</th>
                    <th width="20%">Formula</th>
                    <th width="25%">Substitution</th>
                    <th width="15%">Result</th>
                    <th width="10%">Unit</th>
                    <th width="10%">Status</th>
                </tr>
            </thead>
            <tbody>
                {table_html}
            </tbody>
        </table>

        <div style="margin-top:30px; border-top:1px solid #aaa; padding-top:10px; display:flex; justify-content:space-between; font-size:12px; color:#555;">
            <div>RC Two-Way Slab Design SDM - Streamlit App</div>
            <div>*Calculation based on ACI 318 Method 2 coefficients.</div>
        </div>
    </div>
    """
    return html


# ==========================================
# 5. MAIN APP
# ==========================================
st.title("RC Two-Way Slab Design SDM")

with st.sidebar.form("input_form"):
    st.header("Project Input")
    project = st.text_input("Project Name", "อาคารสำนักงาน 2 ชั้น")
    slab_id = st.text_input("Slab Mark", "S-01")
    engineer = st.text_input("Engineer", "นายไกรฤทธิ์ ด่านพิทักษ์")

    st.subheader("Geometry")
    c1, c2 = st.columns(2)
    Lx = c1.number_input("Short Span (m)", 4.0, step=0.1)
    Ly = c2.number_input("Long Span (m)", 5.0, step=0.1)
    h = st.number_input("Thickness (cm)", 12.0, step=1.0)
    cover = st.number_input("Cover (cm)", 2.0, step=0.5)

    st.subheader("Loads & Material")
    sdl = st.number_input("SDL (kg/m²)", 150.0)
    ll = st.number_input("LL (kg/m²)", 300.0)
    fc = st.number_input("fc' (ksc)", 240.0)
    fy = st.number_input("fy (ksc)", 4000.0)

    st.subheader("Design Parameters")
    case_opts = {1: "1. Simple", 2: "2. All Cont", 3: "3. One Short Discont", 4: "4. One Long Discont",
                 5: "5. Two Short Discont", 6: "6. Two Long Discont", 7: "7. Corner", 8: "8. One Long Cont",
                 9: "9. One Short Cont"}
    case_val = st.selectbox("Support Case", list(case_opts.keys()), format_func=lambda x: case_opts[x], index=1)
    main_bar = st.selectbox("Main Rebar", list(BAR_INFO.keys()), index=3)  # Default DB12

    run = st.form_submit_button("Run Calculation")

if run:
    # 1. Logic
    short, long_s = min(Lx, Ly), max(Lx, Ly)
    m = short / long_s

    # Loads
    wd = 2400 * (h / 100) + sdl
    wu = 1.2 * wd + 1.6 * ll

    # Coefficients & Moments
    Ca_neg, Ca_dl, Ca_ll, Cb_neg, Cb_dl, Cb_ll = get_coeffs(case_val, m)
    La2 = short ** 2

    Ma_pos = (Ca_dl * 1.2 * wd + Ca_ll * 1.6 * ll) * La2
    Ma_neg = Ca_neg * wu * La2
    Mb_pos = (Cb_dl * 1.2 * wd + Cb_ll * 1.6 * ll) * La2
    Mb_neg = Cb_neg * wu * La2

    # Design Steel
    d = h - cover - BAR_INFO[main_bar]['d_mm'] / 10 / 2  # approx d

    As_pos, s_pos, st_pos = design_steel(Ma_pos, d, 100, fc, fy, h, main_bar)

    s_neg = 0
    st_neg = ""
    if Ma_neg > 0:
        As_neg, s_neg, st_neg = design_steel(Ma_neg, d, 100, fc, fy, h, main_bar)

    As_long, s_long, st_long = design_steel(Mb_pos, d, 100, fc, fy, h, main_bar)

    # 2. Prepare Rows
    rows = []
    # Geometry
    rows.append(["SECTION", "1. GEOMETRY", "", "", "", ""])
    rows.append(["Dimensions", "Lx x Ly", f"{short:.2f} x {long_s:.2f}", "-", "m", ""])
    rows.append(["Ratio m", "Lx/Ly", f"{short:.2f}/{long_s:.2f}", f"{m:.2f}", "-", "OK"])

    # Loads
    rows.append(["SECTION", "2. LOAD ANALYSIS", "", "", "", ""])
    rows.append(["Total Factored (wu)", "1.2(DL)+1.6(LL)", f"1.2({wd:.0f})+1.6({ll:.0f})", f"{wu:.0f}", "kg/m²", ""])

    # Short Span
    rows.append(["SECTION", "3. SHORT SPAN DESIGN", "", "", "", ""])
    rows.append(
        ["Ma(+) Moment", "Coeff Method 2", f"({Ca_dl:.3f}..+{Ca_ll:.3f}..){short:.2f}²", f"{Ma_pos:.2f}", "kg-m", ""])
    rows.append(["Ma(+) Steel", f"Use {main_bar}", f"As_req={As_pos:.2f}", f"@{s_pos:.2f} cm", "-", st_pos])

    if Ma_neg > 0:
        rows.append(
            ["Ma(-) Moment (Sup)", "C_neg.wu.Lx²", f"{Ca_neg:.3f}x{wu:.0f}x{short:.2f}²", f"{Ma_neg:.2f}", "kg-m", ""])
        rows.append(["Ma(-) Steel (Top)", f"Use {main_bar}", f"As_req={As_neg:.2f}", f"@{s_neg:.2f} cm", "-", st_neg])

    # Long Span
    rows.append(["SECTION", "4. LONG SPAN DESIGN", "", "", "", ""])
    rows.append(
        ["Mb(+) Moment", "Coeff Method 2", f"({Cb_dl:.3f}..+{Cb_ll:.3f}..){short:.2f}²", f"{Mb_pos:.2f}", "kg-m", ""])
    rows.append(["Mb(+) Steel", f"Use {main_bar}", f"As_req={As_long:.2f}", f"@{s_long:.2f} cm", "-", st_long])

    # Check
    rows.append(["SECTION", "5. CHECKS", "", "", "", ""])
    Vu = wu * short / 2
    phiVc = 0.85 * 0.53 * math.sqrt(fc) * 100 * d
    chk_s = "PASS" if phiVc >= Vu else "FAIL"
    rows.append(["Shear Check", "phiVc >= Vu", f"{phiVc:.0f} >= {Vu:.0f}", chk_s, "kg", chk_s])

    # 3. Generate Plot & HTML
    fig = plot_slab_cad_style(Lx, h, cover, main_bar, s_pos, s_neg)
    img_b64 = fig_to_base64(fig)
    html = generate_html_report(
        {'project': project, 'slab_id': slab_id, 'engineer': engineer, 'Lx': Lx, 'Ly': Ly, 'fc': fc, 'fy': fy, 'h': h,
         'cover': cover}, rows, img_b64)

    components.html(html, height=1300, scrolling=True)
