import streamlit as st
import matplotlib

matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import math
import io
import base64
import streamlit.components.v1 as components
from datetime import date

# ==========================================
# 1. CSS & UI STYLING (MATCHING SCREENSHOTS)
# ==========================================
st.set_page_config(page_title="RC Slab Design SDM", layout="wide")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Sarabun:wght@400;500;700&display=swap');

    body { font-family: 'Sarabun', sans-serif; }

    /* 1. SUCCESS MESSAGE BOX (Green Background) */
    .stAlert { display: none; } /* Hide default streamlit alerts if used */

    .custom-success-box {
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

    /* 2. PRINT BUTTON (Green Solid) */
    .print-btn-green {
        background-color: #28a745; 
        color: white !important; 
        padding: 12px 24px;
        border: none; 
        border-radius: 5px; 
        font-family: 'Sarabun', sans-serif;
        font-weight: bold; 
        cursor: pointer; 
        text-decoration: none;
        display: inline-block; 
        box-shadow: 0 2px 5px rgba(0,0,0,0.2);
        font-size: 16px;
        margin-top: 10px;
    }
    .print-btn-green:hover { background-color: #218838; }
    .print-icon { margin-right: 8px; }

    /* 3. REPORT CONTAINER (A4 Paper Style) */
    .report-container {
        font-family: 'Sarabun', sans-serif;
        max-width: 210mm;
        margin: 0 auto;
        padding: 40px;
        background-color: white;
        color: black;
    }

    /* HEADERS */
    .report-title { font-size: 24px; font-weight: bold; text-align: center; margin-bottom: 5px; text-transform: uppercase; }
    .report-subtitle { font-size: 18px; font-weight: bold; text-align: center; margin-bottom: 30px; }
    .id-box { 
        float: right; 
        border: 2px solid #000; 
        padding: 5px 15px; 
        font-weight: bold; 
        font-size: 16px;
        margin-top: -50px;
    }

    /* INFO SECTION */
    .info-box {
        border: 1px solid #ccc;
        background-color: #f8f9fa;
        padding: 20px;
        border-radius: 4px;
        font-size: 14px;
        margin-bottom: 25px;
        display: flex;
        justify-content: space-between;
    }
    .info-col { width: 48%; line-height: 1.6; }

    /* SUMMARY CARDS */
    .summary-grid { display: flex; justify-content: space-between; margin-bottom: 30px; text-align: center; }
    .summary-card { 
        width: 30%; 
        border: 1px solid #ddd; 
        padding: 15px; 
        border-radius: 5px;
    }
    .card-head { font-weight: bold; font-size: 16px; margin-bottom: 5px; }
    .card-val { color: #0d6efd; font-weight: bold; font-size: 18px; }

    /* CALC TABLE (Clean & Fixed Widths) */
    .calc-table { width: 100%; border-collapse: collapse; font-size: 13px; margin-top: 10px; }
    .calc-table th { 
        background-color: #f1f3f5; 
        border: 1px solid #dee2e6; 
        padding: 10px; 
        text-align: center; 
        font-weight: bold; 
        color: #333;
    }
    .calc-table td { border: 1px solid #dee2e6; padding: 8px 10px; vertical-align: middle; }
    .sec-row { background-color: #e9ecef; font-weight: bold; text-align: left; padding-left: 15px; color: #000; text-transform: uppercase; }

    /* UTILS */
    .status-pass { color: green; font-weight: bold; text-align: center; }
    .status-fail { color: red; font-weight: bold; text-align: center; }
    .center { text-align: center; }
    .bold { font-weight: bold; }

    @media print {
        .no-print { display: none !important; }
        .report-container { width: 100%; max-width: none; padding: 0; box-shadow: none; }
        body { margin: 0; background-color: white; }
        @page { size: A4; margin: 10mm; }
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. CALCULATION LOGIC (ACI METHOD 2)
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
    if Mu_kgm < 1: Mu_kgm = 0
    Mn = Mu_kgm * 100
    phi = 0.90

    # Min Steel (Temp & Shrinkage)
    rho_min = 0.0018 if fy >= 4000 else 0.0020
    As_min = rho_min * b_cm * h_cm

    status = "OK"
    if Mu_kgm == 0:
        As_final = As_min
        status = "Min Steel"
    else:
        Rn = Mn / (phi * b_cm * d_cm ** 2)
        try:
            rho_calc = (0.85 * fc / fy) * (1 - math.sqrt(max(0, 1 - 2 * Rn / (0.85 * fc))))
            As_req = rho_calc * b_cm * d_cm
            As_final = max(As_req, As_min)
        except:
            As_final = As_min
            status = "Calc Error"

    # Spacing
    bar_area = BAR_INFO[bar_key]['A_cm2']
    if As_final > 0:
        s_calc = (bar_area * 100) / As_final
        s_max = min(3 * h_cm, 45.0)
        s_final = min(s_calc, s_max)
        s_final = math.floor(s_final * 2) / 2  # Round 0.5
        return As_final, s_final, status
    return 0, 0, "Error"


def fig_to_base64(fig):
    buf = io.BytesIO()
    fig.savefig(buf, format='png', bbox_inches='tight', dpi=150)
    buf.seek(0)
    return f"data:image/png;base64,{base64.b64encode(buf.read()).decode()}"


# ==========================================
# 3. PLOTTING (CAD STYLE - MATCHING REFERENCE IMAGE)
# ==========================================
def plot_slab_cad_style(Lx, h, cover, main_bar, s_pos, s_neg):
    fig, ax = plt.subplots(figsize=(10, 4))

    # Parameters
    h_m = h / 100
    cov_m = cover / 100
    beam_w = 0.25
    drop = 0.40

    # --- DRAWING HELPERS ---
    def draw_line(x1, y1, x2, y2, lw=1.0, ls='-'):
        ax.plot([x1, x2], [y1, y2], color='black', linewidth=lw, linestyle=ls)

    def draw_tick_diagonal(x, y, size=0.03):
        ax.plot([x - size, x + size], [y - size, y + size], color='black', linewidth=0.8)

    def draw_dim_line(x1, x2, y, text):
        draw_line(x1, y, x2, y, lw=0.5)  # Main line
        draw_tick_diagonal(x1, y)  # Ticks
        draw_tick_diagonal(x2, y)
        # Vertical Extension lines
        draw_line(x1, y - 0.05, x1, y + 0.05, lw=0.3)
        draw_line(x2, y - 0.05, x2, y + 0.05, lw=0.3)
        # Text
        ax.text((x1 + x2) / 2, y + 0.05, text, ha='center', va='bottom', fontsize=9)

    def draw_leader_elbow(x_target, y_target, text, direction='up'):
        # Target circle
        ax.add_patch(patches.Circle((x_target, y_target), 0.012, color='black', fill=True))

        elbow_y = y_target + 0.25 if direction == 'up' else y_target - 0.25
        text_offset = 0.25

        # Line up/down
        draw_line(x_target, y_target, x_target, elbow_y, lw=0.6)
        # Line horizontal
        draw_line(x_target, elbow_y, x_target + text_offset, elbow_y, lw=0.6)

        # Text
        ax.text(x_target + text_offset + 0.05, elbow_y, text, va='center', ha='left', fontsize=9)

    # --- 1. CONCRETE OUTLINE ---
    # Top Slab
    draw_line(0, h_m, Lx, h_m)
    # Bottom Slab (Span)
    draw_line(0, 0, Lx, 0)
    # Left Beam
    draw_line(0, 0, 0, -drop)
    draw_line(0, -drop, -beam_w, -drop)
    draw_line(-beam_w, -drop, -beam_w, h_m)
    draw_line(-beam_w, h_m, 0, h_m)
    # Right Beam
    draw_line(Lx, 0, Lx, -drop)
    draw_line(Lx, -drop, Lx + beam_w, -drop)
    draw_line(Lx + beam_w, -drop, Lx + beam_w, h_m)
    draw_line(Lx + beam_w, h_m, Lx, h_m)

    # Centerlines (Dash Dot)
    draw_line(-beam_w / 2, -drop - 0.15, -beam_w / 2, h_m + 0.4, lw=0.5, ls='-.')
    draw_line(Lx + beam_w / 2, -drop - 0.15, Lx + beam_w / 2, h_m + 0.4, lw=0.5, ls='-.')

    # --- 2. REINFORCEMENT ---
    y_bot = cov_m
    y_top = h_m - cov_m
    ext_L = Lx / 3.5

    # Bottom Bars (Continuous)
    draw_line(-beam_w + 0.05, y_bot, Lx + beam_w - 0.05, y_bot, lw=1.5)
    # Hooks Bottom
    draw_line(-beam_w + 0.05, y_bot, -beam_w + 0.05, y_bot + 0.08, lw=1.5)
    draw_line(Lx + beam_w - 0.05, y_bot, Lx + beam_w - 0.05, y_bot + 0.08, lw=1.5)

    # Top Bars (Supports)
    if s_neg > 0:
        # Left Top
        draw_line(-beam_w + 0.05, y_top, ext_L, y_top, lw=1.5)
        draw_line(ext_L, y_top, ext_L, y_top - 0.08, lw=1.5)  # Hook
        # Right Top
        draw_line(Lx - ext_L, y_top, Lx + beam_w - 0.05, y_top, lw=1.5)
        draw_line(Lx - ext_L, y_top, Lx - ext_L, y_top - 0.08, lw=1.5)  # Hook

        # Temp Bars (Dots) Top
        spacing_temp = 0.20
        n_temp = int(ext_L / spacing_temp)
        for i in range(n_temp + 1):
            ax.add_patch(patches.Circle((i * spacing_temp, y_top - 0.015), 0.008, color='black'))
            ax.add_patch(patches.Circle((Lx - i * spacing_temp, y_top - 0.015), 0.008, color='black'))

    # Temp Bars (Dots) Bottom
    n_bot = int(Lx / 0.20)
    for i in range(1, n_bot):
        ax.add_patch(patches.Circle((i * 0.20, y_bot + 0.015), 0.008, color='black'))

    # --- 3. ANNOTATIONS (CAD Style) ---

    # Span Dimension
    dim_y = -drop - 0.1
    draw_dim_line(0, Lx, dim_y, f"{Lx:.2f} m.")

    # Top Bar Extension Dimension
    if s_neg > 0:
        top_dim_y = h_m + 0.15
        draw_dim_line(0, ext_L, top_dim_y, f"{ext_L:.2f}")
        draw_dim_line(Lx - ext_L, Lx, top_dim_y, f"{ext_L:.2f}")

        # Top Leaders
        draw_leader_elbow(ext_L / 2, y_top, f"{main_bar}@{s_neg:.2f}", direction='up')
        draw_leader_elbow(Lx - ext_L / 2, y_top, f"{main_bar}@{s_neg:.2f}", direction='up')

    # Bottom Leader
    draw_leader_elbow(Lx / 2, y_bot, f"{main_bar}@{s_pos:.2f}", direction='down')

    # Title inside plot (optional)
    ax.text(Lx / 2, h_m + 0.5, "TYPICAL REINFORCEMENT DETAIL", ha='center', fontsize=12, fontweight='bold')

    ax.axis('off')
    ax.set_ylim(-0.8, h_m + 0.8)
    ax.set_xlim(-0.5, Lx + 0.5)
    return fig


# ==========================================
# 4. REPORT GENERATOR (HTML/PDF FRIENDLY)
# ==========================================
def generate_html(inputs, rows, img_b64, summary):
    today_str = date.today().strftime("%d/%m/%Y")

    table_rows_html = ""
    for r in rows:
        if r[0] == "SECTION":
            table_rows_html += f"<tr class='sec-row'><td colspan='6'>{r[1]}</td></tr>"
        else:
            cls = "status-pass" if r[5] in ["OK", "PASS"] else ("status-fail" if r[5] in ["FAIL", "WARN"] else "")
            table_rows_html += f"""
            <tr>
                <td>{r[0]}</td>
                <td style='color:#666;'>{r[1]}</td>
                <td>{r[2]}</td>
                <td class='bold'>{r[3]}</td>
                <td class='center'>{r[4]}</td>
                <td class='{cls}'>{r[5]}</td>
            </tr>
            """

    html = f"""
    <div class="custom-success-box no-print">
        <span style="margin-right:10px;">✅</span> คำนวณเสร็จสิ้น (Calculation Finished)
    </div>

    <div class="no-print" style="text-align: center; margin-bottom: 20px;">
        <button onclick="window.print()" class="print-btn-green">
            <span class="print-icon">🖨️</span> Print This Page / พิมพ์หน้านี้
        </button>
    </div>

    <div class="report-container">
        <div class="report-header">
            <div class="id-box">{inputs['slab_id']}</div>
            <div class="report-title">ENGINEERING DESIGN REPORT</div>
            <div class="report-subtitle">RC Slab Design SDM</div>
        </div>

        <div class="info-box">
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

        <div class="summary-grid">
            <div class="summary-card">
                <div class="card-head">Short Span (+)</div>
                <div class="card-val">{summary['short']}</div>
            </div>
            <div class="summary-card">
                <div class="card-head">Long Span (+)</div>
                <div class="card-val">{summary['long']}</div>
            </div>
            <div class="summary-card">
                <div class="card-head">Support (-)</div>
                <div class="card-val">{summary['supp']}</div>
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
                {table_rows_html}
            </tbody>
        </table>

        <div style="margin-top:30px; border-top:1px solid #ddd; padding-top:10px; font-size:12px; color:#666; display:flex; justify-content:space-between;">
            <div>RC Slab Design SDM - Streamlit App</div>
            <div>Designed by: {inputs['engineer']}</div>
        </div>
    </div>
    """
    return html


# ==========================================
# 5. MAIN APPLICATION
# ==========================================
st.title("RC Slab Design SDM")

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

    st.subheader("Design Params")
    case_opts = {1: "1. Simple", 2: "2. All Cont", 3: "3. One Short Discont", 4: "4. One Long Discont",
                 5: "5. Two Short Discont", 6: "6. Two Long Discont", 7: "7. Corner", 8: "8. One Long Cont",
                 9: "9. One Short Cont"}
    case_val = st.selectbox("Support Case", list(case_opts.keys()), format_func=lambda x: case_opts[x], index=1)
    main_bar = st.selectbox("Main Rebar", list(BAR_INFO.keys()), index=3)  # Default DB12

    run = st.form_submit_button("Run Calculation")

if run:
    # 1. Calc
    short, long_s = min(Lx, Ly), max(Lx, Ly)
    m = short / long_s
    wd = 2400 * (h / 100) + sdl
    wu = 1.2 * wd + 1.6 * ll

    Ca_neg, Ca_dl, Ca_ll, Cb_neg, Cb_dl, Cb_ll = get_coeffs(case_val, m)
    La2 = short ** 2

    Ma_pos = (Ca_dl * 1.2 * wd + Ca_ll * 1.6 * ll) * La2
    Ma_neg = Ca_neg * wu * La2
    Mb_pos = (Cb_dl * 1.2 * wd + Cb_ll * 1.6 * ll) * La2

    d = h - cover - BAR_INFO[main_bar]['d_mm'] / 10 / 2

    As_pos, s_pos, st_pos = design_steel(Ma_pos, d, 100, fc, fy, h, main_bar)

    s_neg = 0
    st_neg = "-"
    if Ma_neg > 0:
        As_neg, s_neg, st_neg = design_steel(Ma_neg, d, 100, fc, fy, h, main_bar)

    As_long, s_long, st_long = design_steel(Mb_pos, d, 100, fc, fy, h, main_bar)

    # 2. Rows
    rows = []
    rows.append(["SECTION", "1. GEOMETRY & LOADS", "", "", "", ""])
    rows.append(["Dimensions", "Lx x Ly", f"{short:.2f} x {long_s:.2f}", "-", "m", ""])
    rows.append(["Factored Load", "1.2DL + 1.6LL", f"1.2({wd:.0f})+1.6({ll:.0f})", f"{wu:.0f}", "kg/m²", ""])

    rows.append(["SECTION", "2. SHORT SPAN DESIGN", "", "", "", ""])
    rows.append(
        ["Ma(+) Moment", "C_pos * wu * Lx²", f"({Ca_dl:.3f}..+{Ca_ll:.3f}..){short:.2f}²", f"{Ma_pos:.2f}", "kg-m", ""])
    rows.append(["Ma(+) Steel", f"Use {main_bar}", f"As_req={As_pos:.2f}", f"@{s_pos:.2f} cm", "-", st_pos])

    if Ma_neg > 0:
        rows.append(
            ["Ma(-) Moment", "C_neg * wu * Lx²", f"{Ca_neg:.3f} * {wu:.0f} * {short:.2f}²", f"{Ma_neg:.2f}", "kg-m",
             ""])
        rows.append(["Ma(-) Steel", f"Use {main_bar}", f"As_req={As_neg:.2f}", f"@{s_neg:.2f} cm", "-", st_neg])

    rows.append(["SECTION", "3. LONG SPAN DESIGN", "", "", "", ""])
    rows.append(["Mb(+) Steel", f"Use {main_bar}", f"As_req={As_long:.2f}", f"@{s_long:.2f} cm", "-", st_long])

    rows.append(["SECTION", "4. CHECKS", "", "", "", ""])
    Vu = wu * short / 2
    phiVc = 0.85 * 0.53 * math.sqrt(fc) * 100 * d
    chk_s = "PASS" if phiVc >= Vu else "FAIL"
    rows.append(["Shear Check", "phiVc >= Vu", f"{phiVc:.0f} >= {Vu:.0f}", chk_s, "kg", chk_s])

    # 3. Output
    summary_data = {
        'short': f"{main_bar}@{s_pos:.2f}",
        'long': f"{main_bar}@{s_long:.2f}",
        'supp': f"{main_bar}@{s_neg:.2f}" if s_neg > 0 else "-"
    }

    fig = plot_slab_cad_style(Lx, h, cover, main_bar, s_pos, s_neg)
    img = fig_to_base64(fig)

    html = generate_html(
        {'project': project, 'slab_id': slab_id, 'engineer': engineer, 'Lx': Lx, 'Ly': Ly, 'fc': fc, 'fy': fy, 'h': h,
         'cover': cover}, rows, img, summary_data)

    components.html(html, height=1400, scrolling=True)
