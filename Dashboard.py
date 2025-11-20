# ==============================================================================
# IMPORT LIBRARIES
# ==============================================================================
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
import os
import re
from typing import Any

# ==============================================================================
# PAGE CONFIGURATION & HEADER
# ==============================================================================
st.set_page_config(layout="wide", page_title="Patient Experience Program | OPD")

# --- CSS & LOGO ---
LOGO_URL = "https://raw.githubusercontent.com/HOIARRTool/hoiarr/main/logo1.png"
logo_urls = [
    "https://github.com/HOIARRTool/appqtbi/blob/main/messageImage_1763018963411.jpg?raw=true",     
    "https://mfu.ac.th/fileadmin/_processed_/6/7/csm_logo_mfu_3d_colour_15e5a7a50f.png?raw=true"
]

# Sidebar Logo
st.sidebar.markdown(
    f'''
    <div style="display:flex;align-items:center;gap:10px;margin-bottom:1rem;">
        <img src="{LOGO_URL}" style="height:40px;display:block;">
        <h2 style="margin:0;font-size:1.5rem;">
            <span class="gradient-text">Patient Experience [OPD]</span>
        </h2>
    </div>
    ''',
    unsafe_allow_html=True
)

# Top Right Logos
st.markdown(
    f'''
    <div style="display: flex; justify-content: flex-end; align-items: flex-start; gap: 20px; margin-bottom: 10px;">
        <img src="{logo_urls[0]}" style="height: 70px; margin-top: 20px;">
        <img src="{logo_urls[1]}" style="height: 90px;">
    </div>
    ''',
    unsafe_allow_html=True
)

# CSS Styles (รวม Animation ปุ่มเรืองแสง)
st.markdown("""
<style>
  .gradient-text {
    background-image: linear-gradient(45deg, #007bff, #6610f2, #6f42c1, #d63384, #dc3545);
    -webkit-background-clip: text; background-clip: text; -webkit-text-fill-color: transparent;
    font-weight: 700; display: inline-block;
  }
  .gauge-head { font-size: 18px; font-weight: 700; color: #111; line-height: 1.25; margin: 2px 4px 6px; white-space: normal; word-break: break-word; }
  .gauge-sub  { font-size: 16px; font-weight: 600; color: #374151; margin: 0 4px 6px; }
  
  /* Metric Box Styling */
  .metric-box{ border: 1px solid #e5e7eb; border-radius: 14px; padding: 16px; text-align: center; color: #4f4f4f;
               box-shadow: 0 2px 6px rgba(0,0,0,.05); display: flex; flex-direction: column; justify-content: center;
               min-height: 120px; background: transparent; margin-bottom: 1rem; }
  .metric-box-1{ background:#e0f7fa !important; }
  .metric-box-2{ background:#e8f5e9 !important; }
  .metric-box-3{ background:#fce4ec !important; }
  .metric-box-4{ background:#fffde7 !important; }
  .metric-box-5{ background:#f3e5f5 !important; }
  .metric-box-6{ background:#e3f2fd !important; }
  .metric-box .label{ font-size: 1.1rem !important; font-weight: 700; line-height: 1.15; margin-bottom: 6px; color: #374151; }
  .metric-box .value{ font-size: 2.6rem !important; font-weight: 800; line-height: 1.1; }

  /* Real-time Badge Animation */
  @keyframes pulse-green {
      0% { box-shadow: 0 0 0 0 rgba(46, 204, 113, 0.7); }
      70% { box-shadow: 0 0 0 10px rgba(46, 204, 113, 0); }
      100% { box-shadow: 0 0 0 0 rgba(46, 204, 113, 0); }
  }
  .realtime-badge {
      background-color: #e8f5e9;
      color: #2e7d32;
      padding: 6px 12px;
      border-radius: 20px;
      font-size: 0.85rem;
      font-weight: 600;
      display: inline-flex;
      align-items: center;
      gap: 8px;
      margin-top: 10px;
      border: 1px solid #c8e6c9;
  }
  .status-dot {
      width: 10px;
      height: 10px;
      background-color: #2ecc71;
      border-radius: 50%;
      animation: pulse-green 2s infinite;
  }
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# DATA LOADING AND PREPARATION
# ==============================================================================

@st.cache_data(ttl=300) # Cache 5 นาที
def load_and_prepare_data(source: Any) -> pd.DataFrame:
    if source is None:
        return pd.DataFrame()

    try:
        if isinstance(source, str):
            if source.lower().endswith('.xlsx'):
                df = pd.read_excel(source)
            else:
                df = pd.read_csv(source)
        else:
            if source.name.lower().endswith('.xlsx'):
                df = pd.read_excel(source)
            else:
                df = pd.read_csv(source)
    except Exception as e:
        return pd.DataFrame()

    # ----------------- Mapping ชื่อคอลัมน์ (OPD) -----------------
    column_mapping = {
        'หน่วยงานที่ท่านเข้ารับบริการ/ ต้องการประเมิน (เพื่อสะท้อนกลับหน่วยงานโดยตรง)': 'หน่วยงาน',
        '1. ท่านมาใช้บริการ': 'ประเภทการมา',
        '2. ท่านคิดว่าสุขภาพโดยรวมของท่าน (ณ ตอนนี้) เป็นอย่างไร': 'สุขภาพโดยรวม',
        '3. เหตุผลที่เลือกใช้บริการ': 'เหตุผลที่เลือก',
        'ส่วนที่ 1 ข้อมูลทั่วไปของผู้ตอบแบบประเมิน\n1. เพศ': 'เพศ',
        '2. อายุ': 'อายุ',
        '3. ภูมิลำเนา': 'ภูมิลำเนา',
        '4. อาชีพ': 'อาชีพ',
        '5. สิทธิในการรักษา': 'สิทธิการรักษา',
        '6. วันที่มารับบริการ': 'วันที่รับบริการ',
        'ความพึงพอใจต่อบริการของโรงพยาบาลในภาพรวม': 'ความพึงพอใจโดยรวม',
        'แบบประเมิน [1.ขั้นตอนการติดต่อและเข้ารับการรักษาในโรงพยาบาล มีความสะดวกเพียงใด]': 'Q1_ความสะดวกขั้นตอน',
        'แบบประเมิน [2.ขั้นตอนการนัดหมายเพื่อเข้ารับบริการ มีความสะดวกเพียงใด]': 'Q2_ความสะดวกนัดหมาย',
        'แบบประเมิน [3.ท่านรู้สึกว่าระยะเวลารอคอยเพื่อพบแพทย์เหมาะสมเพียงใด]': 'Q3_ระยะเวลารอคอย',
        'แบบประเมิน [4.ในการรับบริการครั้งนี้ ทีมผู้รักษา(แพทย์ พยาบาลและเจ้าหน้าที่) รับฟังและเปิดโอกาสให้ท่านซักถามข้อสงสัยได้มากน้อยเพียงใด]': 'Q4_การรับฟัง',
        'แบบประเมิน [5. ในการรับบริการครั้งนี้ พยาบาลและเจ้าหน้าที่ให้ข้อมูลเกี่ยวกับขั้นตอนการรับบริการได้ชัดเจนเพียงใด]': 'Q5_ความชัดเจนข้อมูล',
        'แบบประเมิน [6. ในการรับบริการครั้งนี้ ท่านรู้สึกว่าบุคลากรทุกคนดูแลท่านอย่างเท่าเทียมและให้เกียรติหรือไม่]': 'Q6_ความเท่าเทียม',
        'แบบประเมิน [7. โรงพยาบาลมีความสะอาด และมีสิ่งอำนวยความ4เพียงพอต่อความต้องการของท่าน]': 'Q7_ความสะอาดและสิ่งอำนวยความสะดวก',
        'แบบประเมิน [8. ก่อนรับบริการหรือการทำหัตถการ ท่านได้รับข้อมูลเกี่ยวกับค่าใช้จ่ายที่อาจเกิดขึ้น ชัดเจนเพียงใด]': 'Q8_ข้อมูลค่าใช้จ่าย',
        'แบบประเมิน [9. ท่านได้รับข้อมูลการรักษา อาการแทรกซ้อนระหว่างการรักษาพยาบาล]': 'Q9_ข้อมูลการรักษา',
        'แบบประเมิน [10. ท่านได้รับคำแนะนำอย่างชัดเจน ถึงอาการผิดปกติ ที่ต้องกลับมาพบแพทย์ และการมาตรวจตามนัด]': 'Q10_คำแนะนำกลับบ้าน',
        '1. หากท่านมีอาการเจ็บป่วย ท่านจะพิจารณากลับมารับบริการที่โรงพยาบาลแห่งนี้หรือไม่': 'กลับมารับบริการหรือไม่',
        '2. หากมีโอกาสท่านจะแนะนำผู้อื่นให้มารับบริการที่โรงพยาบาลแห่งนี้หรือไม่': 'แนะนำผู้อื่นหรือไม่',
        '3. ท่านมีความไม่พึงพอใจในการมาใช้บริการที่โรงพยาบาลนี้หรือไม่': 'มีความไม่พึงพอใจหรือไม่',
        '(หากมี) ความไม่พึงพอใจกรุณาระบุรายละเอียด เพื่อเป็นประโยชน์ในการปรับปรุง': 'รายละเอียดความไม่พึงพอใจ',
        'ความคาดหวังต่อบริการของโรงพยาบาลในภาพรวม': 'ความคาดหวังต่อบริการ'
    }
    df = df.rename(columns=lambda c: column_mapping.get(str(c).strip(), str(c).strip()))

    # ----------------- Time fields -----------------
    if 'ประทับเวลา' in df.columns:
        df['date_col'] = pd.to_datetime(df['ประทับเวลา'], dayfirst=True, errors='coerce')
        df = df.dropna(subset=['date_col'])
        df['เดือน'] = df['date_col'].dt.month
        df['ไตรมาส'] = df['date_col'].dt.quarter
        df['ปี'] = df['date_col'].dt.year
    else:
        df['date_col'] = pd.NaT
        df['เดือน'] = None
        df['ไตรมาส'] = None
        df['ปี'] = None
     
    return df

# ==============================================================================
# MAIN APP LOGIC (Real-time Only)
# ==============================================================================

# --- Data Source Config ---
DATA_FILE = "mpxo.xlsx" # ไฟล์สำรอง
SHEET_ID = '1TYo_SQTHgs97kfmBl9An0wEXdbFT0ofIC4v8TGzWyk8'
SHEET_GID = '1745557312'
GSHEET_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={SHEET_GID}"

df_original = pd.DataFrame()
data_source_info = ""

# --- Loading Logic: Google Sheet First -> Local File Fallback ---
try:
    # พยายามดึง Real-time
    df_original = load_and_prepare_data(GSHEET_URL)
    if df_original.empty:
        raise Exception("Empty data from Google Sheet")
    data_source_info = "Google Sheets (Real-time 🟢)"

except Exception as e:
    # ถ้าดึงไม่ได้ ให้ใช้ไฟล์สำรอง
    if os.path.exists(DATA_FILE):
        df_original = load_and_prepare_data(DATA_FILE)
        data_source_info = f"ไฟล์สำรอง: {DATA_FILE} (Offline)"
        st.sidebar.warning(f"⚠️ เชื่อมต่อ Google Sheet ไม่ได้ ({e}) ระบบจึงแสดงผลข้อมูลจากไฟล์สำรองแทน")
    else:
        st.error(f"⚠️ ไม่สามารถดึงข้อมูลจาก Google Sheets และไม่พบไฟล์สำรอง: {e}")
        st.stop()

if df_original.empty:
    st.warning("ไม่พบข้อมูลในระบบ")
    st.stop()

# --- Sidebar: Status & Date ---
st.sidebar.markdown("---")

min_date_str = "N/A"
max_date_str = "N/A"
if 'date_col' in df_original.columns and not df_original['date_col'].isna().all():
    min_date_str = df_original['date_col'].min().strftime('%d %b %Y')
    max_date_str = df_original['date_col'].max().strftime('%d %b %Y')

# สร้าง HTML ปุ่มเรืองแสง (เขียนบรรทัดเดียวเพื่อป้องกัน Indentation Error)
if "Real-time" in data_source_info:
    source_html = f'<div class="realtime-badge"><div class="status-dot"></div>{data_source_info}</div>'
else:
    source_html = f'<div style="margin-top:8px;font-size:0.8rem;color:#666;">📂 {data_source_info}</div>'

st.sidebar.markdown(f"""
<div class="sidebar-info">
    <div class="label">ช่วงวันที่ของข้อมูล</div>
    <div class="value">{min_date_str} - {max_date_str}</div>
    {source_html}
</div>
""", unsafe_allow_html=True)


# --- Sidebar: Filters ---
st.sidebar.header("ตัวกรองข้อมูล (Filter)")
available_departments = ['ภาพรวมทั้งหมด']
if 'หน่วยงาน' in df_original.columns:
    available_departments += sorted(df_original['หน่วยงาน'].dropna().unique().tolist())

selected_department = st.sidebar.selectbox("เลือกหน่วยงาน:", available_departments)
time_filter_option = st.sidebar.selectbox("เลือกช่วงเวลา:", ["ทั้งหมด", "เลือกตามปี", "เลือกตามไตรมาส", "เลือกตามเดือน"])

# Apply Filters
df_filtered = df_original.copy()
if time_filter_option != "ทั้งหมด" and 'ปี' in df_original.columns:
    year_list = sorted(df_original['ปี'].dropna().unique(), reverse=True)
    if year_list:
        selected_year = st.sidebar.selectbox("เลือกปี:", year_list)
        df_filtered = df_filtered[df_filtered['ปี'] == selected_year]

        if time_filter_option == "เลือกตามไตรมาส":
            quarter_list = sorted(df_filtered['ไตรมาส'].dropna().unique())
            selected_quarter = st.sidebar.selectbox("เลือกไตรมาส:", quarter_list)
            df_filtered = df_filtered[df_filtered['ไตรมาส'] == selected_quarter]
        elif time_filter_option == "เลือกตามเดือน":
            month_map = {1: 'ม.ค.', 2: 'ก.พ.', 3: 'มี.ค.', 4: 'เม.ย.', 5: 'พ.ค.', 6: 'มิ.ย.', 7: 'ก.ค.', 8: 'ส.ค.', 9: 'ก.ย.', 10: 'ต.ค.', 11: 'พ.ย.', 12: 'ธ.ค.'}
            month_list = sorted(df_filtered['เดือน'].dropna().unique())
            selected_month_num = st.sidebar.selectbox("เลือกเดือน:", month_list, format_func=lambda x: month_map.get(x, x))
            df_filtered = df_filtered[df_filtered['เดือน'] == selected_month_num]

if selected_department != 'ภาพรวมทั้งหมด' and 'หน่วยงาน' in df_filtered.columns:
    df_filtered = df_filtered[df_filtered['หน่วยงาน'] == selected_department]

if df_filtered.empty:
    st.warning("ไม่พบข้อมูลตามตัวกรองที่ท่านเลือก")
    st.stop()

# ==============================================================================
# DASHBOARD CONTENT
# ==============================================================================
st.title(f"DASHBOARD: {selected_department}")

# --- Helpers ---
LIKERT_MAP = {'มากที่สุด': 5, 'มาก': 4, 'ปานกลาง': 3, 'น้อย': 2, 'น้อยมาก': 1, ' มากที่สุด': 5, ' มาก': 4, ' ปานกลาง': 3, ' น้อย': 2, ' น้อยมาก': 1}
def normalize_to_1_5(x):
    if pd.isna(x): return pd.NA
    s = str(x).strip()
    if s in LIKERT_MAP: return LIKERT_MAP[s]
    m = re.search(r'([1-5])', s)
    if m: return int(m.group(1))
    for k, v in LIKERT_MAP.items():
        if k.strip() in s: return v
    return pd.NA

def render_average_heart_rating(avg_score, max_score=5, responses=None):
    if pd.isna(avg_score):
        st.info("ยังไม่มีคะแนนเฉลี่ยให้แสดง")
        return
    full = int(avg_score)
    frac = max(0.0, min(1.0, avg_score - full))
    hearts_html = ""
    for i in range(1, max_score + 1):
        if i <= full: hearts_html += '<span class="heart full">♥</span>'
        elif i == full + 1 and frac > 0:
            pct = int(round(frac * 100))
            hearts_html += f'<span class="heart partial" style="background: linear-gradient(90deg, #e02424 {pct}%, #E6E6E6 {pct}%); -webkit-background-clip: text; background-clip: text; -webkit-text-fill-color: transparent; color: transparent;">♥</span>'
        else: hearts_html += '<span class="heart empty">♥</span>'
    labels_html = "".join([f'<span class="heart-label">{i}</span>' for i in range(1, max_score + 1)])
    st.markdown(f"""<style>.heart-wrap {{ width: 100%; border: 1px solid #eee; border-radius: 12px; padding: 16px; background: #fff; }} .heart {{ font-size: 40px; color: #E6E6E6; }} .heart.full {{ color: #e02424; }} .heart-labels {{ display: grid; grid-template-columns: repeat(5, 1fr); margin-top: 6px; color: #6b7280; text-align: center; }}</style><div class="heart-wrap"><div style="font-weight:600;margin-bottom:10px;">Average rating ({avg_score:.2f})</div><div>{hearts_html}</div><div class="heart-labels">{labels_html}</div>{"<div style='color:#6b7280;font-size:0.9rem;margin-top:6px;'>คำตอบ " + f"{responses:,}" + " ข้อ</div>" if responses else ""}</div>""", unsafe_allow_html=True)

def plot_gauge_for_column_numseries(series_num, title, height=200, key=None):
    s = series_num.dropna()
    if s.empty:
        st.info(f"ไม่มีข้อมูลสำหรับ '{title}'")
        return
    avg = float(s.mean()); n = int(s.size)
    st.markdown(f"<div class='gauge-head'>{title}</div><div class='gauge-sub'>n = {n}</div>", unsafe_allow_html=True)
    fig = go.Figure(go.Indicator(mode="gauge+number", value=avg, number={'valueformat': '.2f'}, gauge={'axis': {'range': [1, 5]}, 'bar': {'color': '#111827'}, 'steps': [{'range': [1, 2], 'color': '#DC2626'}, {'range': [2, 3], 'color': '#EA580C'}, {'range': [3, 4], 'color': '#F59E0B'}, {'range': [4, 5], 'color': '#16A34A'}], 'threshold': {'line': {'color': '#111827', 'width': 2}, 'thickness': 0.6, 'value': avg}}))
    fig.update_layout(margin=dict(t=10,b=10,l=10,r=10), height=height)
    st.plotly_chart(fig, use_container_width=True, key=key)

def render_percent_gauge(title, pct, n, height=200, key=None, mode='high_good'):
    st.markdown(f"<div class='gauge-head'>{title}</div><div class='gauge-sub'>n = {n}</div>", unsafe_allow_html=True)
    colors = ['#DC2626', '#EA580C', '#F59E0B', '#16A34A'] if mode == 'high_good' else ['#16A34A', '#F59E0B', '#EA580C', '#DC2626']
    ranges = [[0, 50], [50, 65], [65, 80], [80, 100]] if mode == 'high_good' else [[0, 5], [5, 10], [10, 20], [20, 100]]
    steps = [{'range': r, 'color': c} for r, c in zip(ranges, colors)]
    fig = go.Figure(go.Indicator(mode="gauge+number", value=float(pct), number={'suffix': '%', 'valueformat': '.1f'}, gauge={'axis': {'range': [0, 100]}, 'bar': {'color': '#111827'}, 'steps': steps, 'threshold': {'line': {'color': '#111827', 'width': 2}, 'thickness': 0.6, 'value': float(pct)}}))
    fig.update_layout(margin=dict(t=10,b=10,l=10,r=10), height=height)
    st.plotly_chart(fig, use_container_width=True, key=key)

# --- Metrics Calc ---
if 'ความพึงพอใจโดยรวม' in df_filtered.columns:
    df_filtered['คะแนนความพึงพอใจ'] = df_filtered['ความพึงพอใจโดยรวม'].apply(normalize_to_1_5).astype('Float64')
else:
    df_filtered['คะแนนความพึงพอใจ'] = pd.Series(dtype='Float64')

avg_score = df_filtered['คะแนนความพึงพอใจ'].mean()
display_avg = f"{avg_score:.2f}" if pd.notna(avg_score) else "N/A"
total_resp = len(df_filtered)
health_mode = df_filtered['สุขภาพโดยรวม'].mode()[0] if 'สุขภาพโดยรวม' in df_filtered.columns and not df_filtered['สุขภาพโดยรวม'].dropna().empty else "N/A"

def calc_pct(df, col, val='ใช่'):
    if col not in df.columns: return "N/A"
    c = (df[col].astype(str).str.strip() == val).sum()
    t = df[col].notna().sum()
    return f"{(c/t)*100:.1f}%" if t > 0 else "N/A"

# --- Metric Boxes ---
st.markdown("##### ภาพรวม")
c1, c2, c3 = st.columns(3)
c1.markdown(f'<div class="metric-box metric-box-1"><div class="label">จำนวนผู้ตอบ</div><div class="value">{total_resp:,}</div></div>', unsafe_allow_html=True)
c2.markdown(f'<div class="metric-box metric-box-2"><div class="label">คะแนนพึงพอใจเฉลี่ย</div><div class="value">{display_avg}</div></div>', unsafe_allow_html=True)
c3.markdown(f'<div class="metric-box metric-box-6"><div class="label">สุขภาพผู้ป่วยโดยรวม</div><div class="value" style="font-size:1.8rem">{health_mode}</div></div>', unsafe_allow_html=True)

c4, c5, c6 = st.columns(3)
c4.markdown(f'<div class="metric-box metric-box-3"><div class="label">% กลับมาใช้บริการ</div><div class="value">{calc_pct(df_filtered, "กลับมารับบริการหรือไม่")}</div></div>', unsafe_allow_html=True)
c5.markdown(f'<div class="metric-box metric-box-4"><div class="label">% การบอกต่อ</div><div class="value">{calc_pct(df_filtered, "แนะนำผู้อื่นหรือไม่")}</div></div>', unsafe_allow_html=True)
c6.markdown(f'<div class="metric-box metric-box-5"><div class="label">% ไม่พึงพอใจ</div><div class="value">{calc_pct(df_filtered, "มีความไม่พึงพอใจหรือไม่", "มี")}</div></div>', unsafe_allow_html=True)
st.markdown("---")

if selected_department == 'ภาพรวมทั้งหมด' and 'หน่วยงาน' in df_filtered.columns:
    st.subheader("สรุปจำนวนการประเมินตามหน่วยงาน")
    st.dataframe(df_filtered['หน่วยงาน'].value_counts().reset_index().rename(columns={'index':'หน่วยงาน', 'หน่วยงาน':'จำนวน'}), use_container_width=True, hide_index=True)
    st.markdown("---")

# --- Satisfaction Detail ---
st.subheader("ความพึงพอใจภาพรวม")
cl, cr = st.columns(2)
with cl: render_average_heart_rating(avg_score, responses=total_resp)
with cr:
    rc = df_filtered['คะแนนความพึงพอใจ'].dropna().round().astype(int).value_counts().reindex([1,2,3,4,5], fill_value=0).reset_index()
    rc.columns = ['คะแนน', 'จำนวน']
    fig = px.bar(rc, x='คะแนน', y='จำนวน', title='Distribution (1-5)')
    st.plotly_chart(fig, use_container_width=True)
st.markdown("---")

st.header("ส่วนที่ 2: ความพึงพอใจต่อบริการ (รายหัวข้อ)")
satisfaction_cols = {
    'Q1_ความสะดวกขั้นตอน': '1. ความสะดวกขั้นตอนการติดต่อ',
    'Q2_ความสะดวกนัดหมาย': '2. ความสะดวกขั้นตอนการนัดหมาย',
    'Q3_ระยะเวลารอคอย': '3. ความเหมาะสมระยะเวลารอคอย',
    'Q4_การรับฟัง': '4. การรับฟังและเปิดโอกาสให้ซักถาม',
    'Q5_ความชัดเจนข้อมูล': '5. ความชัดเจนข้อมูลขั้นตอนบริการ',
    'Q6_ความเท่าเทียม': '6. การดูแลอย่างเท่าเทียม',
    'Q7_ความสะอาดและสิ่งอำนวยความสะดวก': '7. ความสะอาดและสิ่งอำนวยความสะดวก',
    'Q8_ข้อมูลค่าใช้จ่าย': '8. ความชัดเจนข้อมูลค่าใช้จ่าย',
    'Q9_ข้อมูลการรักษา': '9. ข้อมูลการรักษา/อาการแทรกซ้อน',
    'Q10_คำแนะนำกลับบ้าน': '10. คำแนะนำเมื่อกลับบ้าน'
}
cols = st.columns(2)
for i, (k, v) in enumerate(satisfaction_cols.items()):
    if k in df_filtered.columns:
        with cols[i % 2]:
            plot_gauge_for_column_numseries(df_filtered[k].apply(normalize_to_1_5).astype('Float64'), v, key=f"g_{k}")

st.markdown("---")
st.header("ส่วนที่ 3: ความตั้งใจในอนาคต")
c1, c2, c3 = st.columns(3)
def get_pct_val(col, val='ใช่'):
    s = df_filtered[col].dropna().astype(str).str.strip()
    return (s == val).sum() / s.size * 100 if s.size > 0 else 0, s.size

p1, n1 = get_pct_val('กลับมารับบริการหรือไม่', 'ใช่')
render_percent_gauge("1. กลับมารับบริการ (ใช่)", p1, n1, key="gp1")
with c2:
    p2, n2 = get_pct_val('แนะนำผู้อื่นหรือไม่', 'ใช่')
    render_percent_gauge("2. แนะนำผู้อื่น (ใช่)", p2, n2, key="gp2")
with c3:
    p3, n3 = get_pct_val('มีความไม่พึงพอใจหรือไม่', 'มี')
    render_percent_gauge("3. ไม่พึงพอใจ (มี)", p3, n3, key="gp3", mode='low_good')

st.markdown("---")
st.subheader("รายละเอียดความไม่พึงพอใจ")
if 'รายละเอียดความไม่พึงพอใจ' in df_filtered.columns:
    det = df_filtered[df_filtered['รายละเอียดความไม่พึงพอใจ'].notna()]
    det = det[~det['รายละเอียดความไม่พึงพอใจ'].astype(str).str.strip().isin(['', 'ไม่มี', '-'])]
    if not det.empty: st.dataframe(det[['หน่วยงาน', 'รายละเอียดความไม่พึงพอใจ']], use_container_width=True, hide_index=True)
    else: st.info("ไม่พบข้อมูล")

st.subheader("ความคาดหวังต่อบริการ")
if 'ความคาดหวังต่อบริการ' in df_filtered.columns:
    sug = df_filtered[df_filtered['ความคาดหวังต่อบริการ'].notna()]
    if not sug.empty: st.dataframe(sug[['หน่วยงาน', 'ความคาดหวังต่อบริการ']], use_container_width=True, hide_index=True)
    else: st.info("ไม่พบข้อมูล")
