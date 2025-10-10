# pages/Admin_Upload.py

import streamlit as st
import pandas as pd
import os

# --- ชื่อไฟล์กลางที่จะใช้ทั้งระบบ ---
# เราจะใช้ไฟล์ .xlsx เป็นไฟล์กลางในการเก็บข้อมูล
TARGET_FILENAME = "patient_satisfaction_data.xlsx"

st.set_page_config(layout="wide", page_title="Admin Upload")

st.title("อัปโหลดไฟล์ Patient Satisfaction (XLSX)")

# 1. สร้างตัวอัปโหลดไฟล์ ให้รับเฉพาะ .xlsx
uploaded_file = st.file_uploader(
    "เลือกไฟล์ Excel (.xlsx)",
    type=["xlsx"],
    help="อัปโหลดไฟล์ข้อมูล Excel ที่ดาวน์โหลดจาก Google Forms หรือไฟล์ที่คุณเตรียมไว้"
)

# 2. เมื่อมีการอัปโหลดไฟล์เข้ามา
if uploaded_file is not None:
    try:
        st.info(f"กำลังประมวลผลไฟล์: `{uploaded_file.name}`")

        # อ่านข้อมูลจากไฟล์ Excel ที่อัปโหลดเข้ามา
        df = pd.read_excel(uploaded_file)

        # 3. บันทึก DataFrame ลงเป็นไฟล์ Excel ใหม่ (สำคัญ!)
        # ใช้ df.to_excel() เพื่อบันทึกเป็น .xlsx
        # index=False คือการไม่เอ столбец index ของ pandas ไปใส่ในไฟล์
        df.to_excel(TARGET_FILENAME, index=False, engine='openpyxl')

        st.success(f"ไฟล์ '{uploaded_file.name}' ได้รับการประมวลผลและบันทึกเป็น '{TARGET_FILENAME}' เรียบร้อยแล้ว!")

        # (Optional) แสดงตัวอย่างข้อมูล
        st.markdown("---")
        st.subheader(f"ข้อมูลทั้งหมด {len(df)} แถว")
        st.dataframe(df.head())

    except Exception as e:
        st.error(f"เกิดข้อผิดพลาดในการประมวลผลไฟล์: {e}")

# เพิ่มคำแนะนำการใช้งาน
st.markdown("---")
st.warning("หลังจากอัปโหลดไฟล์สำเร็จ กรุณาไปที่หน้า 'Dashboard' เพื่อดูผลลัพธ์")