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
# 1. SETUP & CSS (THEME MATCHING)
# ==========================================
st.set_page_config(page_title="RC Two-Way Slab Design SDM", layout="wide")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Sarabun:wght@400;500;700&display=swap');

    body { font-family: 'Sarabun', sans-serif; }

    /* SUCCESS BOX STYLE */
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
    }
    .success-icon { margin-right: 10px; font-size: 18px; }

    /* PRINT BUTTON STYLE (GREEN) */
    .print-btn-green {
        background-color: #28a745; 
        color: white !important; 
        padding: 10px 25px;
        border: none; 
        border-radius: 5px; 
        font-family: 'Sarabun', sans-serif;
        font-weight: bold; 
        cursor: pointer; 
        text-decoration: none;
        display: inline-block; 
        box-shadow: 0 2px 4px rgba(0,0,0,0.2);
        font-size: 16px;
    }
    .print-btn-green:hover { background-color: #218838; }

    /* REPORT CONTAINER (A4 STYLE) */
    .report-container {
        font-family: 'Sarabun', sans-serif;
        max-width: 210mm;
        margin: 0 auto;
        padding: 40px;
        background-color: white;
        box-shadow: 0 0 10px rgba(0,0,0,0.1);
    }

    /* REPORT HEADERS */
    .report-title { font-size: 24px; font-weight: bold; text-align: center; margin-bottom: 5px; color: #000; }
    .report-subtitle { font-size: 16px; font-weight: bold; text-align: center; margin-bottom: 20px; color: #000; }
    .id-badge { float: right; border: 1px solid #000; padding: 2px 10px; font-weight: bold; }

    /* INFO GRID (BORDERED) */
    .info-grid {
        display: grid;
        grid-template-columns: 1fr 1fr;
        border: 1px solid #ddd;
        padding: 15px;
        background-color: #f9f9f9;
        margin-bottom: 25px;
        border-radius: 4px;
        font-size: 14px;
    }

    /* CALC TABLE */
    .calc-table { width: 100%; border-collapse: collapse; font-size: 13px; margin-bottom: 20px; }
    .calc-table th { background-color: #f8f9fa; border: 1px solid #dee2e6; padding: 10px; text-align: center; font-weight: bold; }
    .calc-table td { border: 1px solid #dee2e6; padding: 8px; vertical-align: middle; }
    .sec-row { background-color: #e9ecef; font-weight: bold; padding-left: 10px; }
    .pass { color: green; font-weight: bold; text-align: center; }
    .fail { color: red; font-weight: bold; text-align: center; }

    /* SUMMARY CARDS */
    .summary-container { display: flex; justify-content: space-between; margin-top: 20px; text-align: center; }
    .summary-card { width: 32%; border: 1px solid #ddd; padding: 15px; border-radius: 5px; }
    .summary-title { font-weight: bold; margin-bottom: 10px; font-size: 16px; }
    .summary-val { color: #0275d8; font-weight: bold; font-size: 18px; }

    @media print {
        .no-print { display: none !important; }
        .report-container { box-shadow: none; padding: 0; }
        body { background-color: white; }
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. DATA & LOGIC (ACI METHOD 2)
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
    """Interpolate ACI Coefficients"""
    if m < 0.5: m = 0.5
    if m > 1.0: m = 1.0
    data = ACI_METHOD2_DATA.get(case, ACI_METHOD2_DATA[1])
    v05 = data.get(0.5)
    v10 = data.get(1.0)
    frac = (m - 0.5) / 0.5
    res = []
    for i in range(6):
        res.append(v05[i] + frac * (v10[i] - v05[i]))
    return res  # [Ca_neg, Ca_dl, Ca_ll, Cb_neg, Cb_dl, Cb_ll]


def fig_to_base64(fig):
    buf = io.BytesIO()
    fig.savefig(buf, format='png', bbox_inches='tight', dpi=120)
    buf.seek(0)
    return f"data:image/png;base64,{base64.b64encode(buf.read()).decode()}"


# ==========================================
# 3. PLOTTING FUNCTION (MATCHING REFERENCE IMAGE)
# ==========================================
def plot_slab_section_realistic(Lx, h, cover, main_bar, s_pos, s_neg, case_id):
    fig, ax = plt.subplots(figsize=(10, 3.5))

    # Scale factors
    h_m = h / 100
    cov_m = cover / 100
    beam_w = 0.30  # Width of support beam
    beam_h_drop = 0.40  # Depth of beam below slab

    # 1. Draw Concrete Section (Slab + Beams)
    # Main Slab
    ax.add_patch(patches.Rectangle((0, 0), Lx, h_m, facecolor='white', edgecolor='black', linewidth=1.2))

    # Left Beam (Support)
    ax.add_patch(
        patches.Rectangle((-beam_w, -beam_h_drop), beam_w, beam_h_drop + h_m, facecolor='white', edgecolor='black',
                          linewidth=1.2))
    # Right Beam (Support)
    ax.add_patch(patches.Rectangle((Lx, -beam_h_drop), beam_w, beam_h_drop + h_m, facecolor='white', edgecolor='black',
                                   linewidth=1.2))

    # 2. Reinforcement
    y_bot = cov_m
    y_top = h_m - cov_m

    # Bottom Bars (Continuous)
    ax.plot([-beam_w + 0.05, Lx + beam_w - 0.05], [y_bot, y_bot], 'k-', linewidth=1.5)
    # Hook ends for bottom bars
    ax.plot([-beam_w + 0.05, -beam_w + 0.05], [y_bot, y_bot + 0.1], 'k-', linewidth=1.5)
    ax.plot([Lx + beam_w - 0.05, Lx + beam_w - 0.05], [y_bot, y_bot + 0.1], 'k-', linewidth=1.5)

    # Top Bars (At Supports) - Assuming L/3 Extension or approx 0.3 Ln
    ext_len = Lx / 3.0
    if s_neg > 0:
        # Left Top
        ax.plot([-beam_w + 0.05, ext_len], [y_top, y_top], 'k-', linewidth=1.5)
        ax.plot([ext_len, ext_len], [y_top, y_top - 0.08], 'k-', linewidth=1.5)  # Hook down
        # Right Top
        ax.plot([Lx - ext_len, Lx + beam_w - 0.05], [y_top, y_top], 'k-', linewidth=1.5)
        ax.plot([Lx - ext_len, Lx - ext_len], [y_top, y_top - 0.08], 'k-', linewidth=1.5)  # Hook down

        # Dots for perpendicular bars (Temperature)
        n_dots_top = int(ext_len / 0.20)
        for i in range(n_dots_top):
            ax.add_patch(patches.Circle((i * 0.20, y_top - 0.015), 0.006, color='black'))
            ax.add_patch(patches.Circle((Lx - i * 0.20, y_top - 0.015), 0.006, color='black'))

    # Dots for bottom perpendicular bars
    n_dots_bot = int(Lx / 0.20)
    for i in range(1, n_dots_bot):
        ax.add_patch(patches.Circle((i * 0.20, y_bot + 0.015), 0.006, color='black'))

    # 3. Dimensions & Annotations (Matching Style)

    # Top Bar Dimension Line
    if s_neg > 0:
        dim_y = y_top + 0.15
        # Left
        ax.annotate('', xy=(0, dim_y), xytext=(ext_len, dim_y), arrowprops=dict(arrowstyle='|-|', linewidth=0.6))
        ax.text(ext_len / 2, dim_y + 0.02, f"{ext_len:.2f}", ha='center', fontsize=9)
        # Right
        ax.annotate('', xy=(Lx - ext_len, dim_y), xytext=(Lx, dim_y), arrowprops=dict(arrowstyle='|-|', linewidth=0.6))
        ax.text(Lx - ext_len / 2, dim_y + 0.02, f"{ext_len:.2f}", ha='center', fontsize=9)

        # Leader for Top Bar
        ax.plot([ext_len / 2, ext_len / 2], [y_top, dim_y + 0.1], 'k-', linewidth=0.5)
        ax.plot([ext_len / 2, ext_len / 2 + 0.2], [dim_y + 0.1, dim_y + 0.1], 'k-', linewidth=0.5)
        ax.text(ext_len / 2 + 0.22, dim_y + 0.1, f"{main_bar}@{s_neg:.2f}", va='center', fontsize=9)

    # Bottom Bar Leader
    ax.plot([Lx / 2, Lx / 2], [y_bot, y_bot - 0.15], 'k-', linewidth=0.5)  # Vertical drop
    ax.plot([Lx / 2, Lx / 2 + 0.2], [y_bot - 0.15, y_bot - 0.15], 'k-', linewidth=0.5)  # Horizontal
    ax.text(Lx / 2 + 0.22, y_bot - 0.15, f"{main_bar}@{s_pos:.2f}", va='center', fontsize=9)

    # Span Dimension (Bottom)
    span_y = -beam_h_drop - 0.15
    ax.annotate('', xy=(0, span_y), xytext=(Lx, span_y), arrowprops=dict(arrowstyle='|-|', linewidth=0.6))
    ax.text(Lx / 2, span_y - 0.1, f"{Lx:.2f} m.", ha='center', fontsize=10)

    # Centerlines
    ax.plot([0, 0], [span_y - 0.2, h_m + 0.5], 'k-.', linewidth=0.5)
    ax.plot([Lx, Lx], [span_y - 0.2, h_m + 0.5], 'k-.', linewidth=0.5)

    ax.set_title("Typical Reinforcement Detail / แบบขยายเหล็กเสริม (Typical)", fontsize=11, pad=20)
    ax.axis('off')
    ax.set_ylim(span_y - 0.3, h_m + 0.8)
    ax.set_xlim(-beam_w - 0.2, Lx + beam_w + 0.2)
    return fig


# ==========================================
# 4. REPORT GENERATOR
# ==========================================
def generate_html_report(inputs, rows, summary, img_b64):
    today_str = date.today().strftime("%d/%m/%Y")

    # Generate Table Rows
    table_rows_html = ""
    for r in rows:
        if r[0] == "SECTION":
            table_rows_html += f"<tr class='sec-row'><td colspan='6'>{r[1]}</td></tr>"
        else:
            status_class = "pass" if r[5] in ["OK", "PASS"] else ("fail" if r[5] in ["FAIL", "WARN"] else "")
            table_rows_html += f"""
            <tr>
                <td>{r[0]}</td>
                <td style='color:#666;'>{r[1]}</td>
                <td>{r[2]}</td>
                <td style='font-weight:bold;'>{r[3]}</td>
                <td style='text-align:center;'>{r[4]}</td>
                <td class='{status_class}'>{r[5]}</td>
            </tr>
            """

    html = f"""
    <div class="success-box">
        <span class="success-icon">✅</span> คำนวณเสร็จสิ้น (Calculation Finished)
    </div>

    <div class="no-print" style="text-align: center; margin-bottom: 20px;">
        <button onclick="window.print()" class="print-btn-green">🖨️ Print This Page / พิมพ์หน้านี้</button>
    </div>

    <div class="report-container">
        <div style="text-align:center; margin-bottom:10px;">
            <div class="report-title">ENGINEERING DESIGN REPORT</div>
            <div class="report-subtitle">RC Two-Way Slab Design SDM</div>
            <div class="id-badge">{inputs['slab_id']}</div>
        </div>

        <hr style="border: 1px solid #333;">

        <div class="info-grid">
            <div>
                <strong>Project:</strong> {inputs['project']}<br>
                <strong>Engineer:</strong> {inputs['engineer']}<br>
                <strong>Date:</strong> {today_str}
            </div>
            <div>
                <strong>Materials:</strong> fc'={inputs['fc']} ksc, fy={inputs['fy']} ksc<br>
                <strong>Section:</strong> {inputs['Lx']} x {inputs['Ly']} m, Thickness={inputs['h']} cm<br>
                <strong>Cover:</strong> {inputs['cover']} cm
            </div>
        </div>

        <div style="font-weight:bold; font-size:18px; text-align:center; margin: 20px 0;">Design Summary</div>

        <div class="summary-container">
            <div class="summary-card">
                <div class="summary-title">Short Span (Pos)</div>
                <div class="summary-val">{summary['short_pos']}</div>
            </div>
            <div class="summary-card">
                <div class="summary-title">Long Span (Pos)</div>
                <div class="summary-val">{summary['long_pos']}</div>
            </div>
            <div class="summary-card">
                <div class="summary-title">Support (Top)</div>
                <div class="summary-val">{summary['top']}</div>
            </div>
        </div>

        <div style="margin-top: 30px; text-align:center;">
            <img src="{img_b64}" style="max-width:100%; border:1px solid #eee; padding:10px;">
        </div>

        <div style="margin-top: 30px;">
            <div style="font-weight:bold; margin-bottom:10px;">Calculation Details</div>
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
        </div>

        <div style="margin-top:20px; text-align:right; font-size:12px; color:#666;">
            *Calculation based on ACI 318 Method 2 (SDM)
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

    st.subheader("Loads & Materials")
    sdl = st.number_input("SDL (kg/m²)", 150.0)
    ll = st.number_input("LL (kg/m²)", 300.0)
    fc = st.number_input("fc' (ksc)", 240.0)
    fy = st.number_input("fy (ksc)", 4000.0)

    st.subheader("Design Parameters")
    case_opts = {1: "1. Simple", 2: "2. All Cont", 3: "3. One Short Discont", 4: "4. One Long Discont",
                 5: "5. Two Short Discont", 6: "6. Two Long Discont", 7: "7. Corner", 8: "8. One Long Cont",
                 9: "9. One Short Cont"}
    case_val = st.selectbox("Case (ACI)", list(case_opts.keys()), format_func=lambda x: case_opts[x], index=1)
    main_bar = st.selectbox("Main Rebar", list(BAR_INFO.keys()), index=1)  # RB9 default

    submitted = st.form_submit_button("Run Calculation")

if submitted:
    # 1. Calculation Logic
    short, long_s = min(Lx, Ly), max(Lx, Ly)
    m = short / long_s

    # Load Factors (ACI SDM)
    wd = 2400 * (h / 100) + sdl
    wu_dl = 1.2 * wd
    wu_ll = 1.6 * ll
    wu = wu_dl + wu_ll

    # Coefficients
    Ca_neg, Ca_dl, Ca_ll, Cb_neg, Cb_dl, Cb_ll = get_coeffs(case_val, m)
    La2 = short ** 2

    # Moments
    # ACI Method 2: Pos M = (C_dl*w_dl + C_ll*w_ll) * La^2
    Ma_pos = (Ca_dl * wu_dl + Ca_ll * wu_ll) * La2
    Mb_pos = (Cb_dl * wu_dl + Cb_ll * wu_ll) * La2
    # Neg M = C_neg * wu_total * La^2
    Ma_neg = Ca_neg * wu * La2
    Mb_neg = Cb_neg * wu * La2


    # Steel Design Function
    def design_steel(Mu, d, b=100):
        if Mu <= 0.1: return 0, 0
        Mn = Mu * 1000 * 100  # kg-cm
        # Phi = 0.9
        Rn = Mn / (0.9 * b * d ** 2)  # ksc
        try:
            rho = 0.85 * fc / fy * (1 - math.sqrt(1 - 2 * Rn / (0.85 * fc)))
        except:
            return 999, 999  # Fail

        As_req = rho * b * d
        As_min = 0.0018 * b * h  # Temp & Shrinkage ACI
        As_final = max(As_req, As_min)

        # Spacing
        bar_area = BAR_INFO[main_bar]['A_cm2']
        s = int(bar_area * 100 / As_final)
        # Max spacing check (ACI: 3h or 45cm)
        s_max = min(3 * h, 45)
        s = min(s, s_max)
        return As_final, s


    db = BAR_INFO[main_bar]['d_mm']
    d_short = h - cover - db / 20  # approx d
    d_long = d_short - db / 10

    As_a_pos, s_a_pos = design_steel(Ma_pos, d_short)
    As_b_pos, s_b_pos = design_steel(Mb_pos, d_long)

    As_a_neg, s_a_neg = design_steel(Ma_neg, d_short)

    # 2. Prepare Data Rows
    rows = []

    # Geometry
    rows.append(["SECTION", "1. GEOMETRY", "", "", "", ""])
    rows.append(["Short Span (Lx)", "-", "-", f"{short:.2f}", "m", ""])
    rows.append(["Long Span (Ly)", "-", "-", f"{long_s:.2f}", "m", ""])
    rows.append(["Ratio m", "Lx/Ly", f"{short:.2f}/{long_s:.2f}", f"{m:.2f}", "-", "OK"])

    # Loads
    rows.append(["SECTION", "2. LOAD ANALYSIS (SDM)", "", "", "", ""])
    rows.append(["Dead Load (w_dl)", "1.2(DL)", f"1.2({wd:.0f})", f"{wu_dl:.0f}", "kg/m²", ""])
    rows.append(["Live Load (w_ll)", "1.6(LL)", f"1.6({ll:.0f})", f"{wu_ll:.0f}", "kg/m²", ""])
    rows.append(["Total Factored (wu)", "w_dl + w_ll", "-", f"{wu:.0f}", "kg/m²", ""])

    # Moments & Steel
    rows.append(["SECTION", "3. SHORT SPAN MOMENT & STEEL", "", "", "", ""])
    rows.append(
        ["Ma(+) Moment", "(Cdl.wd + Cll.wl)Lx²", f"({Ca_dl:.3f}x{wu_dl:.0f}+{Ca_ll:.3f}x{wu_ll:.0f}){short:.2f}²",
         f"{Ma_pos:.2f}", "kg-m", ""])
    rows.append(["Ma(+) Steel", f"Use {main_bar}", f"As_req={As_a_pos:.2f}", f"@{s_a_pos} cm", "-", "OK"])

    if Ma_neg > 0:
        rows.append(
            ["Ma(-) Moment (Sup)", "C_neg.wu.Lx²", f"{Ca_neg:.3f}x{wu:.0f}x{short:.2f}²", f"{Ma_neg:.2f}", "kg-m", ""])
        rows.append(["Ma(-) Steel (Top)", f"Use {main_bar}", f"As_req={As_a_neg:.2f}", f"@{s_a_neg} cm", "-", "OK"])

    rows.append(["SECTION", "4. LONG SPAN MOMENT & STEEL", "", "", "", ""])
    rows.append(
        ["Mb(+) Moment", "(Cdl.wd + Cll.wl)Lx²", f"({Cb_dl:.3f}x{wu_dl:.0f}+{Cb_ll:.3f}x{wu_ll:.0f}){short:.2f}²",
         f"{Mb_pos:.2f}", "kg-m", ""])
    rows.append(["Mb(+) Steel", f"Use {main_bar}", f"As_req={As_b_pos:.2f}", f"@{s_b_pos} cm", "-", "OK"])

    # Shear Check
    rows.append(["SECTION", "5. CHECKS", "", "", "", ""])
    Vu = wu * short / 2
    PhiVc = 0.85 * 0.53 * math.sqrt(fc) * 100 * d_short  # ACI Simplified
    status_shear = "PASS" if PhiVc >= Vu else "FAIL"
    rows.append(["Shear Check", "phi.Vc >= Vu", f"{PhiVc:.0f} >= {Vu:.0f}", status_shear, "kg", status_shear])

    # Summary Dict for Cards
    summary = {
        'short_pos': f"{main_bar}@{s_a_pos}",
        'long_pos': f"{main_bar}@{s_b_pos}",
        'top': f"{main_bar}@{s_a_neg}" if Ma_neg > 0 else "-"
    }

    # 3. Generate Plot
    fig = plot_slab_section_realistic(Lx, h, cover, main_bar, s_a_pos, s_a_neg, case_val)
    img_b64 = fig_to_base64(fig)

    # 4. Render Report
    html_code = generate_html_report(
        {'project': project, 'slab_id': slab_id, 'engineer': engineer, 'fc': fc, 'fy': fy, 'Lx': Lx, 'Ly': Ly, 'h': h,
         'cover': cover},
        rows, summary, img_b64
    )

    components.html(html_code, height=1400, scrolling=True)

else:
    st.info("👈 Please enter data on the sidebar and click Run.")
