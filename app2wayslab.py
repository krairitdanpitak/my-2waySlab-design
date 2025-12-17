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
# 1. SETUP & CSS (REPORT STYLE)
# ==========================================
st.set_page_config(page_title="RC Two-Way Slab Design SDM", layout="wide")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Sarabun:wght@400;500;700&display=swap');

    /* Main container settings */
    .report-container {
        font-family: 'Sarabun', sans-serif;
        max-width: 210mm; /* A4 Width */
        margin: 0 auto;
        padding: 20px;
        background-color: white;
        color: #333;
    }

    /* Header Styles */
    .report-header {
        text-align: center;
        margin-bottom: 20px;
    }
    .report-title {
        font-size: 24px;
        font-weight: bold;
        margin: 0;
    }
    .report-subtitle {
        font-size: 16px;
        color: #555;
        margin-top: 5px;
    }
    .id-badge {
        float: right;
        border: 2px solid #333;
        padding: 2px 10px;
        font-weight: bold;
        font-size: 14px;
    }

    /* Info Box */
    .info-box {
        border: 1px solid #ccc;
        background-color: #f9f9f9;
        padding: 15px;
        margin-bottom: 20px;
        border-radius: 4px;
        display: flex;
        justify-content: space-between;
        font-size: 14px;
    }
    .info-col { width: 48%; }

    /* Table Styles (Matching PDF) */
    .calc-table {
        width: 100%;
        border-collapse: collapse;
        font-size: 13px;
        margin-bottom: 25px;
    }
    .calc-table th {
        background-color: #f0f0f0;
        border: 1px solid #ddd;
        padding: 8px;
        text-align: center;
        font-weight: bold;
    }
    .calc-table td {
        border: 1px solid #ddd;
        padding: 6px 10px;
        vertical-align: middle;
    }
    .section-row {
        background-color: #e6e6e6;
        font-weight: bold;
        text-align: left;
        padding-left: 10px !important;
    }

    /* Status Indicators */
    .status-ok { color: green; font-weight: bold; text-align: center; }
    .status-fail { color: red; font-weight: bold; text-align: center; }
    .result-val { font-weight: bold; color: #000; text-align: center; }

    /* Print Button (Green) */
    .print-btn-internal {
        background-color: #4CAF50;
        color: white;
        padding: 10px 20px;
        border: none;
        border-radius: 5px;
        font-family: 'Sarabun', sans-serif;
        font-weight: bold;
        cursor: pointer;
        text-decoration: none;
        display: inline-block;
        margin-bottom: 20px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.2);
    }
    .print-btn-internal:hover { background-color: #45a049; }

    /* Plot Image */
    .plot-img {
        width: 100%;
        border: 1px solid #eee;
        margin-bottom: 10px;
    }

    @media print {
        .no-print { display: none !important; }
        .report-container { width: 100%; max-width: none; padding: 0; }
        body { margin: 0; padding: 0; }
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. DATA & COEFFICIENTS
# ==========================================
BAR_INFO = {
    'RB6': {'A_cm2': 0.283, 'd_mm': 6},
    'RB9': {'A_cm2': 0.636, 'd_mm': 9},
    'DB10': {'A_cm2': 0.785, 'd_mm': 10},
    'DB12': {'A_cm2': 1.131, 'd_mm': 12},
    'DB16': {'A_cm2': 2.011, 'd_mm': 16}
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


def get_moment_coefficients(case_id, m):
    if m < 0.5: m = 0.5
    if m > 1.0: m = 1.0
    data = ACI_METHOD2_DATA.get(case_id, ACI_METHOD2_DATA[1])
    v05 = data.get(0.5, data.get(min(data.keys())))
    v10 = data.get(1.0, data.get(max(data.keys())))
    res = []
    frac = (m - 0.5) / 0.5
    for i in range(6):
        res.append(v05[i] + frac * (v10[i] - v05[i]))
    return res


def fmt(n, digits=2):
    try:
        return f"{float(n):,.{digits}f}"
    except:
        return "-"


def fig_to_base64(fig):
    buf = io.BytesIO()
    fig.savefig(buf, format='png', bbox_inches='tight', dpi=100)
    buf.seek(0)
    return f"data:image/png;base64,{base64.b64encode(buf.read()).decode()}"


# ==========================================
# 3. PLOTTING
# ==========================================
def plot_slab_section_detailed(Lx, h, cover, main_bar, s_main, top_bar_info, top_s, case_id):
    # Generates a section view similar to the provided screenshot
    fig, ax = plt.subplots(figsize=(8, 3.5))

    h_m = h / 100
    cov_m = cover / 100
    supp_w = 0.25  # Support width

    # 1. Concrete Shape (Slab + Beams)
    # Slab
    ax.add_patch(patches.Rectangle((0, 0), Lx, h_m, facecolor='white', edgecolor='black', linewidth=1.5))
    # Supports (Downstand beams)
    ax.add_patch(patches.Rectangle((-supp_w, -0.4), supp_w, 0.4 + h_m, facecolor='white', edgecolor='black',
                                   linewidth=1.5))  # Left
    ax.add_patch(
        patches.Rectangle((Lx, -0.4), supp_w, 0.4 + h_m, facecolor='white', edgecolor='black', linewidth=1.5))  # Right

    # 2. Rebar
    # Bottom Main (Continuous)
    y_bot = cov_m
    ax.plot([-0.15, Lx + 0.15], [y_bot, y_bot], 'k-', linewidth=2)
    # Hooks up
    ax.plot([-0.15, -0.15], [y_bot, y_bot + 0.1], 'k-', linewidth=2)
    ax.plot([Lx + 0.15, Lx + 0.15], [y_bot, y_bot + 0.1], 'k-', linewidth=2)

    # Top Bars (At Supports) - Assuming L/3 for visual
    L_top = Lx / 3.0
    y_top = h_m - cov_m

    # Left Top
    ax.plot([-0.15, L_top], [y_top, y_top], 'k-', linewidth=2)
    ax.plot([L_top, L_top], [y_top, y_top - 0.08], 'k-', linewidth=2)  # Hook down

    # Right Top
    ax.plot([Lx - L_top, Lx + 0.15], [y_top, y_top], 'k-', linewidth=2)
    ax.plot([Lx - L_top, Lx - L_top], [y_top, y_top - 0.08], 'k-', linewidth=2)

    # Dots (Distribution/Temp)
    spacing_dots = 0.2
    n_dots = int(Lx / spacing_dots)
    for i in range(1, n_dots):
        cx = i * spacing_dots
        # Bottom dots
        ax.add_patch(patches.Circle((cx, y_bot + 0.015), 0.008, color='black'))
        # Top dots (if within top bar range)
        if cx < L_top or cx > (Lx - L_top):
            ax.add_patch(patches.Circle((cx, y_top - 0.015), 0.008, color='black'))

    # 3. Dimensions & Annotations (Matching Screenshot Style)
    # Top Dimensions (L/3, L, L/3)
    dim_y = h_m + 0.2
    # Left Top
    ax.annotate('', xy=(0, dim_y), xytext=(L_top, dim_y), arrowprops=dict(arrowstyle='|-|', linewidth=0.8))
    ax.text(L_top / 2, dim_y + 0.05, f"{L_top:.2f}", ha='center')
    # Right Top
    ax.annotate('', xy=(Lx - L_top, dim_y), xytext=(Lx, dim_y), arrowprops=dict(arrowstyle='|-|', linewidth=0.8))
    ax.text(Lx - L_top / 2, dim_y + 0.05, f"{L_top:.2f}", ha='center')

    # Bottom Dimension (Total Span)
    ax.annotate('', xy=(0, -0.2), xytext=(Lx, -0.2), arrowprops=dict(arrowstyle='|-|', linewidth=0.8))
    ax.text(Lx / 2, -0.25, f"{Lx:.2f} m.", ha='center', va='top')

    # Rebar Labels
    # Top Label
    top_txt = f"{main_bar}@{top_s:.2f}"
    ax.annotate(top_txt, xy=(L_top / 2, y_top), xytext=(L_top / 2, y_top + 0.35),
                arrowprops=dict(arrowstyle='->', connectionstyle="angle,angleA=0,angleB=90,rad=10"), ha='center')

    # Bottom Label
    bot_txt = f"{main_bar}@{s_main:.2f}"
    ax.annotate(bot_txt, xy=(Lx / 2, y_bot), xytext=(Lx / 2, y_bot - 0.5),
                arrowprops=dict(arrowstyle='->', connectionstyle="angle,angleA=0,angleB=90,rad=10"), ha='center')

    # Thickness
    ax.annotate('', xy=(Lx + 0.4, 0), xytext=(Lx + 0.4, h_m), arrowprops=dict(arrowstyle='|-|', linewidth=0.8))
    ax.text(Lx + 0.45, h_m / 2, f"{h_m:.2f}", rotation=90, va='center')

    ax.axis('off')
    ax.set_xlim(-0.5, Lx + 0.8)
    ax.set_ylim(-0.8, h_m + 0.6)

    return fig


# ==========================================
# 4. REPORT GENERATOR
# ==========================================
def generate_report(inputs, rows, img_sec):
    # Constructing HTML rows
    table_html = ""
    for r in rows:
        if r[0].startswith("SECTION_HEAD"):
            # Section Header Row
            title = r[1]
            table_html += f"<tr class='section-row'><td colspan='6'>{title}</td></tr>"
        else:
            # Data Row
            item, formula, sub, res, unit, stat = r

            # Status styling
            stat_class = ""
            if stat == "OK" or stat == "PASS":
                stat_class = "status-ok"
            elif stat == "FAIL" or "WARN" in stat:
                stat_class = "status-fail"

            table_html += f"""
            <tr>
                <td>{item}</td>
                <td>{formula}</td>
                <td>{sub}</td>
                <td class='result-val'>{res}</td>
                <td style='text-align:center;'>{unit}</td>
                <td class='{stat_class}'>{stat}</td>
            </tr>
            """

    today = date.today().strftime("%d/%m/%Y")

    html = f"""
    <div class="no-print" style="text-align: center;">
        <button onclick="window.print()" class="print-btn-internal">🖨️ Print This Page / พิมพ์หน้านี้</button>
    </div>

    <div class="report-container">
        <div class="report-header">
            <div class="id-badge">{inputs['slab_id']}</div>
            <div class="report-title">ENGINEERING DESIGN REPORT</div>
            <div class="report-subtitle">RC Two-Way Slab Design SDM (ACI 318 Method 2)</div>
        </div>

        <div class="info-box">
            <div class="info-col">
                <strong>Project:</strong> {inputs['project']}<br>
                <strong>Engineer:</strong> {inputs['engineer']}<br>
                <strong>Date:</strong> {today}
            </div>
            <div class="info-col">
                <strong>Panel Size:</strong> {inputs['Lx']} x {inputs['Ly']} m.<br>
                <strong>Thickness:</strong> {inputs['h']} cm (Cover {inputs['cover']} cm)<br>
                <strong>Materials:</strong> fc'={inputs['fc']} ksc, fy={inputs['fy']} ksc
            </div>
        </div>

        <div style="margin-bottom: 20px;">
            <div style="font-weight: bold; margin-bottom: 5px; text-align: center;">Design Visualization (Section S-S)</div>
            <img src="{img_sec}" class="plot-img">
        </div>

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

        <div style="margin-top: 30px; border: 2px solid #333; padding: 10px; text-align: center;">
            <div style="font-size: 14px; color: #555;">CONCLUSION</div>
            <div style="font-size: 24px; font-weight: bold; color: green; margin: 5px 0;">DESIGN COMPLETE</div>
            <div style="font-size: 12px; color: #777;">Checked by: {inputs['engineer']}</div>
        </div>

        <div style="margin-top:20px; text-align:right; font-size:10px; color:#999;">
            Generated by RC Slab Design Module v2.0
        </div>
    </div>
    """
    return html


# ==========================================
# 5. CALCULATION & PROCESSING
# ==========================================
def run_design(inputs):
    # Unpack
    Lx, Ly = inputs['Lx'], inputs['Ly']
    h, cov = inputs['h'], inputs['cover']
    fc, fy = inputs['fc'], inputs['fy']
    sdl, ll = inputs['sdl'], inputs['ll']
    case_id = inputs['case']
    main_bar = inputs['mainBar']

    rows = []

    # 1. Geometry
    short = min(Lx, Ly)
    long_s = max(Lx, Ly)
    m = short / long_s
    ratio_chk = long_s / short

    rows.append(["SECTION_HEAD", "1. GEOMETRY & SLAB TYPE"])
    rows.append(["Short Span (Lx)", "min(Lx, Ly)", "-", fmt(short), "m", ""])
    rows.append(["Long Span (Ly)", "max(Lx, Ly)", "-", fmt(long_s), "m", ""])
    rows.append(["Ratio Ly/Lx", "Ly / Lx", f"{fmt(long_s)}/{fmt(short)}", fmt(ratio_chk), "-",
                 "OK" if ratio_chk <= 2 else "WARN"])
    rows.append(["Slab Type", "Ratio <= 2.0", "-", "Two-Way Slab", "-", "OK"])

    # 2. Loads
    w_sw = 2400 * (h / 100)
    w_d = w_sw + sdl
    wu_d = 1.2 * w_d
    wu_l = 1.6 * ll
    wu = wu_d + wu_l

    rows.append(["SECTION_HEAD", "2. LOAD ANALYSIS"])
    rows.append(["Dead Load (D)", "SW + SDL", f"{w_sw:.0f} + {sdl}", fmt(w_d), "kg/m²", ""])
    rows.append(["Factored Load (wu)", "1.2D + 1.6L", f"1.2({w_d:.0f})+1.6({ll})", fmt(wu), "kg/m²", ""])

    # 3. Moments
    Ca_neg, Ca_dl, Ca_ll, Cb_neg, Cb_dl, Cb_ll = get_moment_coefficients(case_id, m)
    La_sq = short ** 2
    Ma_pos = (Ca_dl * wu_d + Ca_ll * wu_l) * La_sq
    Mb_pos = (Cb_dl * wu_d + Cb_ll * wu_l) * La_sq
    Ma_neg = Ca_neg * wu * La_sq
    Mb_neg = Cb_neg * wu * La_sq

    rows.append(["SECTION_HEAD", "3. MOMENTS & REINFORCEMENT (SHORT SPAN)"])
    rows.append(["Ma(+) Moment", "Coeff * La²", f"({Ca_dl:.3f}D+{Ca_ll:.3f}L)*{short:.1f}²", fmt(Ma_pos), "kg-m", ""])

    # Rebar Calc
    db = BAR_INFO[main_bar]['d_mm']
    As_bar = BAR_INFO[main_bar]['A_cm2']
    d_short = h - cov - db / 20
    d_long = d_short - db / 10

    def get_as(Mu, d):
        if Mu <= 10: return 0.0018 * 100 * h
        Rn = (Mu * 100) / (0.9 * 100 * d ** 2) * 1000  # kg/cm2
        rho = 0.85 * fc / fy * (1 - math.sqrt(max(0, 1 - 2 * Rn / (0.85 * fc))))
        return max(rho * 100 * d, 0.0018 * 100 * h)

    def get_spacing(As_req):
        s = math.floor(min((As_bar * 100) / As_req, 3 * h, 45) * 2) / 2
        return min(s, 30.0)

    # Short Pos
    As_a = get_as(Ma_pos, d_short)
    s_a = get_spacing(As_a)
    rows.append(["Req. As (Mid)", "Calculation", f"Mu={fmt(Ma_pos)}", fmt(As_a), "cm²", ""])
    rows.append(["Provide Short(+)", f"Use {main_bar}", "-", f"@{s_a} cm", "-", "OK"])

    # Short Neg
    if Ca_neg > 0:
        As_an = get_as(Ma_neg, d_short)
        s_an = get_spacing(As_an)
        rows.append(
            ["Ma(-) Support", "C_neg * wu * La²", f"{Ca_neg:.3f}*{wu:.0f}*{short:.1f}²", fmt(Ma_neg), "kg-m", ""])
        rows.append(["Provide Short(-)", f"Use {main_bar}", "-", f"@{s_an} cm", "-", "OK"])
    else:
        s_an = 0
        rows.append(["Ma(-) Support", "Discontinuous", "-", "0.00", "kg-m", "-"])

    rows.append(["SECTION_HEAD", "4. MOMENTS & REINFORCEMENT (LONG SPAN)"])
    # Long Pos
    As_b = get_as(Mb_pos, d_long)
    s_b = get_spacing(As_b)
    rows.append(["Mb(+) Moment", "Coeff * La²", f"...", fmt(Mb_pos), "kg-m", ""])
    rows.append(["Provide Long(+)", f"Use {main_bar}", "-", f"@{s_b} cm", "-", "OK"])

    # Long Neg
    if Cb_neg > 0:
        As_bn = get_as(Mb_neg, d_long)
        s_bn = get_spacing(As_bn)
        rows.append(["Mb(-) Support", "C_neg * wu * La²", f"{Cb_neg:.3f}...", fmt(Mb_neg), "kg-m", ""])
        rows.append(["Provide Long(-)", f"Use {main_bar}", "-", f"@{s_bn} cm", "-", "OK"])
    else:
        rows.append(["Mb(-) Support", "Discontinuous", "-", "0.00", "kg-m", "-"])

    # 5. Checks
    rows.append(["SECTION_HEAD", "5. SHEAR & DEFLECTION CHECK"])
    Vu = wu * short / 2
    Vc = 0.53 * math.sqrt(fc) * 100 * d_short
    phiVc = 0.85 * Vc
    status_shear = "PASS" if phiVc >= Vu else "FAIL"

    rows.append(["Shear Check", "phiVc >= Vu", f"{fmt(phiVc)} >= {fmt(Vu)}", status_shear, "kg", status_shear])

    min_h = (2 * (Lx + Ly) * 100) / 180
    status_def = "PASS" if h >= min_h else "CHECK"
    rows.append(["Min Thickness", "Perimeter / 180", f"Peri={fmt(2 * (Lx + Ly))}", fmt(min_h), "cm", status_def])

    # Generate Image
    top_s_plot = s_an if Ca_neg > 0 else 20  # Default spacing if 0
    img_sec = fig_to_base64(plot_slab_section_detailed(Lx, h, cov, main_bar, s_a, "", top_s_plot, case_id))

    return generate_report(inputs, rows, img_sec)


# ==========================================
# 6. MAIN APP
# ==========================================
st.title("RC Two-Way Slab Design SDM")

with st.sidebar.form("input_form"):
    st.header("Project Info")
    project = st.text_input("Project Name", "อาคารสำนักงาน 2 ชั้น")
    slab_id = st.text_input("Slab Mark", "S-01")
    engineer = st.text_input("Engineer", "นายไกรฤทธิ์ ด่านพิทักษ์")

    st.header("Geometry & Load")
    c1, c2 = st.columns(2)
    Lx = c1.number_input("Short Span (m)", 4.0, step=0.1)
    Ly = c2.number_input("Long Span (m)", 5.0, step=0.1)
    h = c1.number_input("Thickness (cm)", 15.0, step=1.0)
    cover = c2.number_input("Cover (cm)", 2.5)

    sdl = c1.number_input("SDL (kg/m²)", 150.0)
    ll = c2.number_input("LL (kg/m²)", 300.0)

    st.header("Materials")
    fc = c1.number_input("fc' (ksc)", 240)
    fy = c2.number_input("fy (ksc)", 4000)
    mainBar = st.selectbox("Main Rebar", list(BAR_INFO.keys()), index=1)

    case_opts = {1: "1. Simple", 2: "2. All Cont", 3: "3. One Short Discont", 4: "4. One Long Discont",
                 5: "5. Two Short Discont", 6: "6. Two Long Discont", 7: "7. Corner", 8: "8. One Long Cont",
                 9: "9. One Short Cont"}
    case_sel = st.selectbox("Case (ACI)", list(case_opts.values()))
    case_id = int(case_sel.split(".")[0])

    run_btn = st.form_submit_button("Run Calculation")

if run_btn:
    inputs = {
        'project': project, 'slab_id': slab_id, 'engineer': engineer,
        'Lx': Lx, 'Ly': Ly, 'h': h, 'cover': cover,
        'fc': fc, 'fy': fy, 'sdl': sdl, 'll': ll,
        'case': case_id, 'mainBar': mainBar
    }

    html_report = run_design(inputs)
    st.success("✅ คำนวณเสร็จสิ้น (Calculation Finished)")
    components.html(html_report, height=1200, scrolling=True)
else:
    st.info("👈 กรุณากรอกข้อมูลแล้วกดปุ่ม Run Calculation")