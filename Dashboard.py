# ==============================================================================
# IMPORT LIBRARIES
# ==============================================================================
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
import os
import io
import hashlib
import re

# ==============================================================================
# PAGE CONFIGURATION & STYLING
# ==============================================================================
st.set_page_config(layout="wide", page_title="Patient Experience Program | OPD")

LOGO_URL = "https://raw.githubusercontent.com/HOIARRTool/hoiarr/refs/heads/main/logo1.png"

st.sidebar.markdown(
    f'<div style="display: flex; align-items: center; margin-bottom: 1rem;"><img src="{LOGO_URL}" style="height: 40px; margin-right: 10px;"><h2 style="margin: 0; font-size: 1.5rem;"><span class="gradient-text">Patient Experience (OPD)</span></h2></div>',
    unsafe_allow_html=True)

st.markdown("""
<style>
  .gauge-head { font-size: 18px; font-weight: 700; color: #111; line-height: 1.25; margin: 2px 4px 6px; white-space: normal; word-break: break-word; }
  .gauge-sub  { font-size: 16px; font-weight: 600; color: #374151; margin: 0 4px 6px; }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<style>
  :root{ --metric-value-size: 2.6rem; --metric-label-size: calc(2.6rem * 2/3); }
  .metric-box{ border: 1px solid #e5e7eb; border-radius: 14px; padding: 16px; text-align: center; color: #4f4f4f;
               box-shadow: 0 2px 6px rgba(0,0,0,.05); display: flex; flex-direction: column; justify-content: center;
               min-height: 120px; background: transparent; margin-bottom: var(--metric-label-size); }
  .metric-box.metric-box-1{ background:#e0f7fa !important; }
  .metric-box.metric-box-2{ background:#e8f5e9 !important; }
  .metric-box.metric-box-3{ background:#fce4ec !important; }
  .metric-box.metric-box-4{ background:#fffde7 !important; }
  .metric-box.metric-box-5{ background:#f3e5f5 !important; }
  .metric-box.metric-box-6{ background:#e3f2fd !important; }
  .metric-box .label{ font-size: var(--metric-label-size) !important; font-weight: 700; line-height: 1.15; margin-bottom: 6px; color: #374151; }
  .metric-box .value{ font-size: var(--metric-value-size) !important; font-weight: 800; line-height: 1.1; }
  @media (max-width: 900px){
    :root{ --metric-value-size: 2.2rem; --metric-label-size: calc(2.2rem * 2/3); }
  }
</style>
""", unsafe_allow_html=True)


# ==============================================================================
# DATA LOADING AND PREPARATION (รองรับอัปโหลด CSV/XLSX)
# ==============================================================================
def _hash_bytes(b: bytes) -> str:
    return hashlib.md5(b).hexdigest() if b else "no-bytes"

@st.cache_data
def load_and_prepare_data_from_bytes(file_bytes: bytes, filename: str) -> pd.DataFrame:
    """
    อ่านไฟล์จาก bytes (xlsx/xls/csv) แล้วเตรียมคอลัมน์ที่ใช้ในแดชบอร์ด
    ผูก cache ตามอาร์กิวเมนต์ file_bytes + filename อัตโนมัติ
    """
    if not file_bytes:
        return pd.DataFrame()

    try:
        if filename.lower().endswith(".csv"):
            df = pd.read_csv(io.BytesIO(file_bytes))
        else:
            df = pd.read_excel(io.BytesIO(file_bytes), sheet_name=0, engine="openpyxl")
    except Exception as e:
        st.error(f"เกิดข้อผิดพลาดในการอ่านไฟล์ข้อมูล: {e}")
        return pd.DataFrame()

    # ----------------- Mapping ชื่อคอลัมน์ (OPD) -----------------
    column_mapping = {
        'หน่วยงานที่ท่านเข้ารับบริการ/ ต้องการประเมิน (เพื่อสะท้อนกลับหน่วยงานโดยตรง)': 'หน่วยงาน',
        '1. ท่านมาใช้บริการ': 'ประเภทการมา',
        '2. ท่านคิดว่าสุขภาพโดยรวมของท่านเป็นอย่างไร': 'สุขภาพโดยรวม',
        '3. เหตุผลที่เลือกใช้บริการ': 'เหตุผลที่เลือก',
        'ส่วนที่ 1 ข้อมูลทั่วไปของผู้ตอบแบบประเมิน\n1. เพศ': 'เพศ',
        '2. อายุ': 'อายุ',
        '3. ภูมิลำเนา': 'ภูมิลำเนา',
        '4. อาชีพ': 'อาชีพ',
        '5. สิทธิในการรักษา': 'สิทธิการรักษา',
        '6. วันที่มารับบริการ': 'วันที่รับบริการ',
        'ความพึงพอใจต่อบริการของโรงพยาบาลในภาพรวม': 'ความพึงพอใจโดยรวม',
        '1. ขั้นตอนการติดต่อและเข้ารับการรักษาในโรงพยาบาล มีความสะดวกเพียงใด': 'Q1_ความสะดวกขั้นตอน',
        '2. ขั้นตอนการนัดหมายเพื่อเข้ารับบริการ มีความสะดวกเพียงใด': 'Q2_ความสะดวกนัดหมาย',
        '3. ท่านรู้สึกว่าระยะเวลารอคอยเพื่อพบแพทย์เหมาะสมเพียงใด': 'Q3_ระยะเวลารอคอย',
        '4. ในการรับบริการครั้งนี้ ทีมผู้รักษา(แพทย์ พยาบาลและเจ้าหน้าที่) รับฟังและเปิดโอกาสให้ท่านซักถามข้อสงสัยได้มากน้อยเพียงใด': 'Q4_การรับฟัง',
        '5. ในการรับบริการครั้งนี้ พยาบาลและเจ้าหน้าที่ให้ข้อมูลเกี่ยวกับขั้นตอนการรับบริการได้ชัดเจนเพียงใด': 'Q5_ความชัดเจนข้อมูล',
        '6. ในการรับบริการครั้งนี้ ท่านรู้สึกว่าบุคลากรทุกคนดูแลท่านอย่างเท่าเทียมและให้เกียรติหรือไม่': 'Q6_ความเท่าเทียม',
        '5. โรงพยาบาลมีความสะอาด และมีสิ่งอำนวยความสะดวกเพียงพอต่อความต้องการของท่าน': 'Q7_ความสะอาดและสิ่งอำนวยความสะดวก',
        '8. ก่อนรับบริการหรือการทำหัตถการ ท่านได้รับข้อมูลเกี่ยวกับค่าใช้จ่ายที่อาจเกิดขึ้น ชัดเจนเพียงใด': 'Q8_ข้อมูลค่าใช้จ่าย',
        '9. ท่านได้รับข้อมูลการรักษา อาการแทรกซ้อนระหว่างการรักษาพยาบาล': 'Q9_ข้อมูลการรักษา',
        '10. ท่านได้รับคำแนะนำอย่างชัดเจน ถึงอาการผิดปกติ ที่ต้องกลับมาพบแพทย์ และการมาตรวจตามนัด': 'Q10_คำแนะนำกลับบ้าน',
        '1. หากท่านมีอาการเจ็บป่วย ท่านจะพิจารณากลับมารับบริการที่โรงพยาบาลแห่งนี้หรือไม่': 'กลับมารับบริการหรือไม่',
        '2. หากมีโอกาสท่านจะแนะนำผู้อื่นให้มารับบริการที่โรงพยาบาลแห่งนี้หรือไม่': 'แนะนำผู้อื่นหรือไม่',
        '3. ท่านมีความไม่พึงพอใจในการมาใช้บริการที่โรงพยาบาลนี้หรือไม่': 'มีความไม่พึงพอใจหรือไม่',
        '(หากมี) ความไม่พึงพอใจกรุณาระบุรายละเอียด เพื่อเป็นประโยชน์ในการปรับปรุง': 'รายละเอียดความไม่พึงพอใจ',
        'ความคาดหวังต่อบริการของโรงพยาบาลในภาพรวม': 'ความคาดหวังต่อบริการ'
    }
    df = df.rename(columns=lambda c: column_mapping.get(str(c).strip(), str(c).strip()))

    # ----------------- Time fields -----------------
    time_col = None
    for cand in ['ประทับเวลา', 'Timestamp', 'เวลา', 'วันที่รับบริการ']:
        if cand in df.columns:
            time_col = cand
            break
    if not time_col:
        st.error("ไม่พบคอลัมน์เวลาสำหรับอ้างอิง (เช่น 'ประทับเวลา' หรือ 'Timestamp')")
        return pd.DataFrame()

    df['date_col'] = pd.to_datetime(df[time_col], errors='coerce')
    df = df.dropna(subset=['date_col'])
    df['เดือน'] = df['date_col'].dt.month
    df['ไตรมาส'] = df['date_col'].dt.quarter
    df['ปี'] = df['date_col'].dt.year
    return df


# ---- อัปโหลดไฟล์ (แถบซ้าย) + Fallback เป็น mpxo.xlsx ----
st.sidebar.markdown("### อัปโหลดไฟล์ข้อมูล")
uploaded = st.sidebar.file_uploader("อัปโหลด .xlsx / .xls / .csv", type=["xlsx", "xls", "csv"])

DATA_FILE = "mpxo.xlsx"  # default

if uploaded is not None:
    # ใช้ไฟล์ที่อัปโหลดเป็นแหล่งข้อมูลทันที
    file_bytes = uploaded.getbuffer().tobytes()
    df_original = load_and_prepare_data_from_bytes(file_bytes, uploaded.name)

    # (ตัวเลือก) บันทึกสำเนาไฟล์อัปโหลดลงดิสก์
    SAVE_DIR = "data_uploads"
    os.makedirs(SAVE_DIR, exist_ok=True)
    save_path = os.path.join(SAVE_DIR, f"opd_latest{Path(uploaded.name).suffix.lower()}")
    try:
        with open(save_path, "wb") as w:
            w.write(file_bytes)
    except Exception as e:
        st.info(f"บันทึกไฟล์อัปโหลดไม่สำเร็จ: {e}")

    # เขียนทับ DATA_FILE ให้เป็น .xlsx เสมอ (ถ้าต้องการแชร์ให้หน้าอื่น ๆ)
    try:
        if uploaded.name.lower().endswith((".xlsx", ".xls")):
            with open(DATA_FILE, "wb") as w:
                w.write(file_bytes)
        elif uploaded.name.lower().endswith(".csv"):
            tmp_df = pd.read_csv(io.BytesIO(file_bytes))
            with pd.ExcelWriter(DATA_FILE, engine="openpyxl") as writer:
                tmp_df.to_excel(writer, index=False, sheet_name="Sheet1")
    except Exception as e:
        st.info(f"บันทึกเป็น .xlsx ไม่สำเร็จ: {e}")

else:
    # fallback: โหลด mpxo.xlsx ถ้ามี
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "rb") as f:
            file_bytes = f.read()
        df_original = load_and_prepare_data_from_bytes(file_bytes, DATA_FILE)
    else:
        df_original = pd.DataFrame()

# ถ้าไม่มีข้อมูลเลย ให้แจ้งเตือนและหยุด (ไม่มีหน้าอื่นแล้ว Landing คือ Dashboard)
if df_original.empty:
    st.warning("ยังไม่มีข้อมูล ให้ลองอัปโหลดไฟล์ทางแถบด้านซ้าย (.xlsx/.xls/.csv) หรือเพิ่มไฟล์ mpxo.xlsx ในโฟลเดอร์โปรเจกต์")
    st.stop()


# ==============================================================================
# PLOTTING HELPERS
# ==============================================================================
def render_average_heart_rating(avg_score: float, max_score: int = 5, responses: int | None = None):
    """แสดงหัวใจ 5 ดวง (เต็ม/บางส่วน/ว่าง) จากค่าเฉลี่ย พร้อมหัวข้อและ n"""
    if pd.isna(avg_score):
        st.info("ยังไม่มีคะแนนเฉลี่ยให้แสดง")
        return

    full = int(avg_score)
    frac = max(0.0, min(1.0, avg_score - full))
    hearts_html = ""
    for i in range(1, max_score + 1):
        if i <= full:
            hearts_html += '<span class="heart full">♥</span>'
        elif i == full + 1 and frac > 0:
            pct = int(round(frac * 100))
            hearts_html += f'''
            <span class="heart partial" style="
                background: linear-gradient(90deg, #e02424 {pct}%, #E6E6E6 {pct}%);
                -webkit-background-clip: text; background-clip: text;
                -webkit-text-fill-color: transparent; color: transparent;">♥</span>'''
        else:
            hearts_html += '<span class="heart empty">♥</span>'

    labels_html = "".join([f'<span class="heart-label">{i}</span>' for i in range(1, max_score + 1)])

    component_html = f"""
    <style>
      .heart-wrap {{ width: 100%; border: 1px solid #eee; border-radius: 12px; padding: 16px 18px; background: #fff; }}
      .heart-title {{ font-weight: 600; font-size: 1.05rem; color: #333; margin-bottom: 10px; }}
      .heart-row {{ display: flex; align-items: center; justify-content: space-between; gap: 8px; margin: 6px 4px 2px 4px; }}
      .heart {{ font-size: 40px; line-height: 1; display: inline-block; text-shadow: 0 1px 0 rgba(0,0,0,0.06); user-select: none; }}
      .heart.full {{ color: #e02424; }}
      .heart.empty {{ color: #E6E6E6; }}
      .heart.partial {{ }}
      .heart-labels {{ display: grid; grid-template-columns: repeat({5}, 1fr); margin-top: 6px; }}
      .heart-label {{ text-align: center; color: #6b7280; font-size: 0.9rem; }}
      .heart-sub {{ color: #6b7280; font-size: 0.9rem; margin-top: 6px; }}
    </style>
    <div class="heart-wrap">
      <div class="heart-title">Average rating ({avg_score:.2f})</div>
      <div class="heart-row">{hearts_html}</div>
      <div class="heart-labels">{labels_html}</div>
      {"<div class='heart-sub'>คำตอบ " + f"{responses:,}" + " ข้อ</div>" if responses is not None else ""}
    </div>
    """
    st.markdown(component_html, unsafe_allow_html=True)


def plot_generic_pie_chart(df, column_name, title):
    if column_name not in df.columns or df[column_name].dropna().empty:
        st.info(f"ไม่มีข้อมูลสำหรับ '{title}'")
        return
    counts = df[column_name].value_counts().reset_index()
    counts.columns = [column_name, 'จำนวน']
    fig = px.pie(counts, names=column_name, values='จำนวน', title=title)
    fig.update_traces(textposition='inside', textinfo='percent+label', showlegend=True)
    st.plotly_chart(fig, use_container_width=True)


LIKERT_MAP = {
    'มากที่สุด': 5, 'มาก': 4, 'ปานกลาง': 3, 'น้อย': 2, 'น้อยมาก': 1,
    ' มากที่สุด': 5, ' มาก': 4, ' ปานกลาง': 3, ' น้อย': 2, ' น้อยมาก': 1
}
def normalize_to_1_5(x):
    if pd.isna(x):
        return pd.NA
    s = str(x).strip()
    if s in LIKERT_MAP:
        return LIKERT_MAP[s]
    m = re.search(r'([1-5])', s)
    if m:
        return int(m.group(1))
    for k, v in LIKERT_MAP.items():
        base = k.strip()
        if base and base in s:
            return v
    return pd.NA


def plot_gauge_for_column_numseries(
    series_num, title: str,
    min_v: int = 1, max_v: int = 5,
    height: int = 190, number_font_size: int = 34,
    key: str | None = None
):
    series_num = series_num.dropna()
    if series_num.empty:
        st.info(f"ไม่มีข้อมูลสำหรับ '{title}'")
        return

    avg = float(series_num.mean()); n = int(series_num.size)

    st.markdown(f"<div class='gauge-head'>{title}</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='gauge-sub'>n = {n}</div>", unsafe_allow_html=True)

    steps_4 = [
        {'range': [1, 2], 'color': '#DC2626'},
        {'range': [2, 3], 'color': '#EA580C'},
        {'range': [3, 4], 'color': '#F59E0B'},
        {'range': [4, 5], 'color': '#16A34A'},
    ]

    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=avg,
        number={'valueformat': '.2f', 'font': {'size': number_font_size}},
        title={'text': ''},
        gauge={
            'axis': {'range': [min_v, max_v], 'tickmode': 'array', 'tickvals': [1,2,3,4,5]},
            'bar': {'color': '#111827', 'thickness': 0.25},
            'steps': steps_4,
            'threshold': {'line': {'color': '#111827', 'width': 2}, 'thickness': 0.6, 'value': avg}
        }
    ))
    fig.update_layout(margin=dict(t=8, r=6, b=6, l=6), height=height)
    st.plotly_chart(fig, use_container_width=True, key=key or f"gauge_{hash(title)}")


# ==============================================================================
# DASHBOARD (Landing Page)
# ==============================================================================
st.title("DASHBOARD (OPD)")

# --- Sidebar: ช่วงวันที่และตัวกรอง ---
st.sidebar.markdown("---")
min_date = df_original['date_col'].min().strftime('%d %b %Y')
max_date = df_original['date_col'].max().strftime('%d %b %Y')
st.sidebar.markdown(f"""
<div class="sidebar-info">
    <div class="label">ช่วงวันที่ของข้อมูล</div>
    <div class="value">{min_date} - {max_date}</div>
</div>
""", unsafe_allow_html=True)

st.sidebar.header("ตัวกรองข้อมูล (Filter)")
available_departments = ['ภาพรวมทั้งหมด'] + sorted(df_original['หน่วยงาน'].dropna().unique().tolist()) if 'หน่วยงาน' in df_original.columns else ['ภาพรวมทั้งหมด']
selected_department = st.sidebar.selectbox("เลือกหน่วยงาน:", available_departments)
time_filter_option = st.sidebar.selectbox("เลือกช่วงเวลา:", ["ทั้งหมด", "เลือกตามปี", "เลือกตามไตรมาส", "เลือกตามเดือน"])

df_filtered = df_original.copy()
if time_filter_option != "ทั้งหมด":
    year_list = sorted(df_original['ปี'].unique(), reverse=True)
    selected_year = st.sidebar.selectbox("เลือกปี:", year_list)
    df_filtered = df_original[df_original['ปี'] == selected_year]
    if time_filter_option in ["เลือกตามไตรมาส", "เลือกตามเดือน"]:
        if time_filter_option == "เลือกตามไตรมาส":
            quarter_list = sorted(df_filtered['ไตรมาส'].unique())
            selected_quarter = st.sidebar.selectbox("เลือกไตรมาส:", quarter_list)
            df_filtered = df_filtered[df_filtered['ไตรมาส'] == selected_quarter]
        else:
            month_map = {1: 'ม.ค.', 2: 'ก.พ.', 3: 'มี.ค.', 4: 'เม.ย.', 5: 'พ.ค.', 6: 'มิ.ย.', 7: 'ก.ค.', 8: 'ส.ค.',
                         9: 'ก.ย.', 10: 'ต.ค.', 11: 'พ.ย.', 12: 'ธ.ค.'}
            month_list = sorted(df_filtered['เดือน'].unique())
            selected_month_num = st.sidebar.selectbox("เลือกเดือน:", month_list,
                                                      format_func=lambda x: month_map.get(x, x))
            df_filtered = df_filtered[df_filtered['เดือน'] == selected_month_num]

if selected_department != 'ภาพรวมทั้งหมด' and 'หน่วยงาน' in df_filtered.columns:
    df_filtered = df_filtered[df_filtered['หน่วยงาน'] == selected_department]

if df_filtered.empty:
    st.warning("ไม่พบข้อมูลตามตัวกรองที่ท่านเลือก")
    st.stop()

# --- Metrics ---
satisfaction_score_map = {'มากที่สุด': 5, 'มาก': 4, 'ปานกลาง': 3, 'น้อย': 2, 'น้อยมาก': 1}
if 'ความพึงพอใจโดยรวม' in df_filtered.columns:
    df_filtered['คะแนนความพึงพอใจ'] = df_filtered['ความพึงพอใจโดยรวม'].map(satisfaction_score_map)
else:
    df_filtered['คะแนนความพึงพอใจ'] = pd.NA

average_satisfaction_score = df_filtered['คะแนนความพึงพอใจ'].mean()
display_avg_satisfaction = f"{average_satisfaction_score:.2f}" if pd.notna(average_satisfaction_score) else "N/A"
total_responses = len(df_filtered)

def calculate_percentage(df, col_name, positive_value='ใช่', decimals=1):
    if col_name in df.columns and not df[col_name].dropna().empty:
        count = (df[col_name].astype(str).str.strip() == positive_value).sum()
        total_count = df[col_name].notna().sum()
        if total_count > 0:
            return f"{(count / total_count) * 100:.{decimals}f}%"
    return "N/A"

return_service_pct = calculate_percentage(df_filtered, 'กลับมารับบริการหรือไม่', decimals=1)
recommend_pct     = calculate_percentage(df_filtered, 'แนะนำผู้อื่นหรือไม่', decimals=1)
dissatisfied_pct  = calculate_percentage(df_filtered, 'มีความไม่พึงพอใจหรือไม่', positive_value='มี', decimals=2)

most_common_health_status = (
    df_filtered['สุขภาพโดยรวม'].mode()[0]
    if 'สุขภาพโดยรวม' in df_filtered.columns and not df_filtered['สุขภาพโดยรวม'].dropna().empty
    else "N/A"
)

st.markdown("##### ภาพรวม")
row1 = st.columns(3); row2 = st.columns(3)
with row1[0]:
    st.markdown(f'<div class="metric-box metric-box-1"><div class="label">จำนวนผู้ตอบ</div><div class="value">{total_responses:,}</div></div>', unsafe_allow_html=True)
with row1[1]:
    st.markdown(f'<div class="metric-box metric-box-2"><div class="label">คะแนนพึงพอใจเฉลี่ย</div><div class="value">{display_avg_satisfaction}</div></div>', unsafe_allow_html=True)
with row1[2]:
    st.markdown(f'<div class="metric-box metric-box-6"><div class="label">สุขภาพผู้ป่วยโดยรวม</div><div class="value" style="font-size: 1.8rem;">{most_common_health_status}</div></div>', unsafe_allow_html=True)
with row2[0]:
    st.markdown(f'<div class="metric-box metric-box-3"><div class="label">% กลับมาใช้บริการ</div><div class="value">{return_service_pct}</div></div>', unsafe_allow_html=True)
with row2[1]:
    st.markdown(f'<div class="metric-box metric-box-4"><div class="label">% การบอกต่อ</div><div class="value">{recommend_pct}</div></div>', unsafe_allow_html=True)
with row2[2]:
    st.markdown(f'<div class="metric-box metric-box-5"><div class="label">% ไม่พึงพอใจ</div><div class="value">{dissatisfied_pct}</div></div>', unsafe_allow_html=True)

st.markdown("---")

# --- ถ้าเลือกภาพรวมทั้งหมด แสดงจำนวนการประเมินตามหน่วยงาน ---
if selected_department == 'ภาพรวมทั้งหมด' and 'หน่วยงาน' in df_filtered.columns:
    st.subheader("สรุปจำนวนการประเมินตามหน่วยงาน")
    evaluation_counts = df_filtered['หน่วยงาน'].value_counts().reset_index()
    evaluation_counts.columns = ['หน่วยงาน', 'จำนวนการประเมิน']
    st.dataframe(evaluation_counts, use_container_width=True, hide_index=True)
    st.markdown("---")

# ==============================================================================
# ความพึงพอใจภาพรวม: หัวใจ + สัดส่วนคะแนน 1–5
# ==============================================================================
st.subheader("ความพึงพอใจภาพรวม")
col_left, col_right = st.columns(2)

with col_left:
    render_average_heart_rating(average_satisfaction_score, max_score=5, responses=total_responses)

with col_right:
    rating_counts = (
        df_filtered['คะแนนความพึงพอใจ']
        .value_counts()
        .reindex([1, 2, 3, 4, 5])
        .fillna(0).astype(int)
        .reset_index()
    )
    rating_counts.columns = ['คะแนน', 'จำนวน']
    fig = px.bar(rating_counts, x='คะแนน', y='จำนวน', title='Distribution of Ratings (1–5)')
    fig.update_layout(yaxis_title='จำนวน', xaxis_title='คะแนน', margin=dict(t=60, r=10, l=10, b=10), height=350)
    st.plotly_chart(fig, use_container_width=True)

st.markdown("---")

# ==============================================================================
# ส่วนที่ 2: ความพึงพอใจต่อบริการ (รายหัวข้อ) -> เกจ
# ==============================================================================
st.header("ส่วนที่ 2: ความพึงพอใจต่อบริการ (รายหัวข้อ)")

satisfaction_cols = {
    'Q1_ความสะดวกขั้นตอน': '1. ความสะดวกขั้นตอนการติดต่อและเข้ารับบริการ',
    'Q2_ความสะดวกนัดหมาย': '2. ความสะดวกขั้นตอนการนัดหมาย',
    'Q3_ระยะเวลารอคอย': '3. ความเหมาะสมของระยะเวลารอคอยพบแพทย์',
    'Q4_การรับฟัง': '4. การรับฟังและเปิดโอกาสให้ซักถามโดยทีมผู้รักษา',
    'Q5_ความชัดเจนข้อมูล': '5. ความชัดเจนของข้อมูลขั้นตอนบริการ',
    'Q6_ความเท่าเทียม': '6. การดูแลอย่างเท่าเทียมและให้เกียรติ',
    'Q7_ความสะอาดและสิ่งอำนวยความสะดวก': '7. ความสะอาดและสิ่งอำนวยความสะดวก',
    'Q8_ข้อมูลค่าใช้จ่าย': '8. ความชัดเจนของข้อมูลค่าใช้จ่าย',
    'Q9_ข้อมูลการรักษา': '9. การได้รับข้อมูลการรักษาและอาการแทรกซ้อน',
    'Q10_คำแนะนำกลับบ้าน': '10. ความชัดเจนของคำแนะนำเมื่อกลับบ้าน'
}

# แปลงทุกหัวข้อเป็นคะแนน 1–5
for col in satisfaction_cols.keys():
    if col in df_filtered.columns:
        df_filtered[f'{col}__score'] = df_filtered[col].apply(normalize_to_1_5).astype('Float64')

cols_per_row = 2
items = list(satisfaction_cols.items())
for i in range(0, len(items), cols_per_row):
    cols = st.columns(cols_per_row)
    for j in range(cols_per_row):
        if i + j < len(items):
            col_name, title = items[i + j]
            with cols[j]:
                score_col = f'{col_name}__score'
                if score_col in df_filtered.columns:
                    plot_gauge_for_column_numseries(
                        df_filtered[score_col],
                        title,
                        height=200,
                        key=f"gauge_{col_name}"
                    )

st.markdown("---")

# ==============================================================================
# ส่วนที่ 3: ความตั้งใจในอนาคตและข้อเสนอแนะ
# ==============================================================================
st.header("ส่วนที่ 3: ความตั้งใจในอนาคตและข้อเสนอแนะ")

def percent_positive(series, positives=("ใช่",)):
    s = series.dropna().astype(str).str.strip()
    n = s.size
    if n == 0:
        return 0.0, 0
    pct = (s.isin(positives).sum() / n) * 100.0
    return pct, n

def render_percent_gauge(title, pct, n, height=190, key=None, number_font_size=34, mode='high_good'):
    st.markdown(f"<div class='gauge-head'>{title}</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='gauge-sub'>n = {n}</div>", unsafe_allow_html=True)

    if mode == 'high_good':
        steps_4 = [
            {'range': [0, 50],  'color': '#DC2626'},
            {'range': [50, 65], 'color': '#EA580C'},
            {'range': [65, 80], 'color': '#F59E0B'},
            {'range': [80, 100],'color': '#16A34A'},
        ]
    else:  # 'low_good' เช่น % ไม่พึงพอใจ (ต่ำดี)
        steps_4 = [
            {'range': [0, 5],   'color': '#16A34A'},
            {'range': [5, 10],  'color': '#F59E0B'},
            {'range': [10, 20], 'color': '#EA580C'},
            {'range': [20, 100],'color': '#DC2626'},
        ]

    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=float(pct),
        number={'suffix': '%', 'valueformat': '.1f', 'font': {'size': number_font_size}},
        title={'text': ''},
        gauge={
            'axis': {'range': [0, 100], 'tickmode': 'array', 'tickvals': [0,20,40,60,80,100]},
            'bar': {'color': '#111827', 'thickness': 0.25},
            'steps': steps_4,
            'threshold': {'line': {'color': '#111827', 'width': 2}, 'thickness': 0.6, 'value': float(pct)}
        }
    ))
    fig.update_layout(margin=dict(t=8, r=6, b=6, l=6), height=height)
    st.plotly_chart(fig, use_container_width=True, key=key or f"gauge_pct_{hash(title)}")


# คำนวณ % ตัวชี้วัด
pct_return, n_return = percent_positive(df_filtered.get('กลับมารับบริการหรือไม่', pd.Series(dtype=str)), positives=("ใช่",))
pct_reco,   n_reco   = percent_positive(df_filtered.get('แนะนำผู้อื่นหรือไม่', pd.Series(dtype=str)), positives=("ใช่",))
pct_dissat, n_dissat = percent_positive(df_filtered.get('มีความไม่พึงพอใจหรือไม่', pd.Series(dtype=str)), positives=("มี",))

# จัดวาง 3 เกจ
c1, c2, c3 = st.columns(3)
with c1:
    render_percent_gauge("1. หากเจ็บป่วยจะกลับมารับบริการหรือไม่ (ตอบ 'ใช่')",
                         pct_return, n_return, height=200, key="g_future_return", mode='high_good')
with c2:
    render_percent_gauge("2. จะแนะนำผู้อื่นให้มารับบริการหรือไม่ (ตอบ 'ใช่')",
                         pct_reco, n_reco, height=200, key="g_future_reco", mode='high_good')
with c3:
    render_percent_gauge("3. ไม่พึงพอใจ (ตอบ 'มี')",
                         pct_dissat, n_dissat, height=200, key="g_future_dissat", mode='low_good')

st.markdown("---")

# ตารางรายละเอียด/ความคาดหวัง
st.subheader("รายละเอียดความไม่พึงพอใจ (หากมี)")
if 'รายละเอียดความไม่พึงพอใจ' in df_filtered.columns:
    temp_df = df_filtered[['หน่วยงาน', 'รายละเอียดความไม่พึงพอใจ']].copy() if 'หน่วยงาน' in df_filtered.columns else df_filtered[['รายละเอียดความไม่พึงพอใจ']].copy()
    temp_df.dropna(subset=['รายละเอียดความไม่พึงพอใจ'], inplace=True)
    temp_df['details_stripped'] = temp_df['รายละเอียดความไม่พึงพอใจ'].astype(str).str.strip()
    dissatisfaction_df = temp_df[(temp_df['details_stripped'] != '') & (temp_df['details_stripped'] != 'ไม่มี')]
    show_cols = ['หน่วยงาน', 'รายละเอียดความไม่พึงพอใจ'] if 'หน่วยงาน' in temp_df.columns else ['รายละเอียดความไม่พึงพอใจ']
    if not dissatisfaction_df.empty:
        st.dataframe(dissatisfaction_df[show_cols], use_container_width=True, hide_index=True)
    else:
        st.info("ไม่พบรายละเอียดความไม่พึงพอใจในช่วงข้อมูลที่เลือก")

st.subheader("ความคาดหวังต่อบริการของโรงพยาบาลในภาพรวม")
if 'ความคาดหวังต่อบริการ' in df_filtered.columns:
    show_cols = ['หน่วยงาน', 'ความคาดหวังต่อบริการ'] if 'หน่วยงาน' in df_filtered.columns else ['ความคาดหวังต่อบริการ']
    suggestions_df = df_filtered[df_filtered['ความคาดหวังต่อบริการ'].notna()][show_cols]
    if not suggestions_df.empty:
        st.dataframe(suggestions_df, use_container_width=True, hide_index=True)
    else:
        st.info("ไม่พบข้อมูลความคาดหวังในช่วงข้อมูลที่เลือก")

