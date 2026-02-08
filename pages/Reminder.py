import streamlit as st
import pandas as pd
from datetime import date
from models import SessionLocal, Document

st.title("⏰ Reminder Văn kiện")
def get_session():
    return SessionLocal()

session = get_session()

name = st.text_input("Tên văn kiện")
dept = st.text_input("Phòng ban")
deadline = st.date_input("Deadline")
status = st.selectbox("Trạng thái", ["Đang xử lý", "Hoàn thành", "Tạm dừng"])

if st.button("➕ Thêm"):
    session.add(Document(
        document_name=name,
        department=dept,
        deadline=deadline,
        status=status
    ))
    session.commit()
    st.success("Đã thêm")

docs = session.query(Document).all()

# ALERT
late = [d for d in docs if d.deadline < date.today() and d.status != "Hoàn thành"]
if late:
    st.error("⚠️ Có văn kiện trễ hạn!")

df = pd.DataFrame([{
    "Tên": d.document_name,
    "Phòng ban": d.department,
    "Deadline": d.deadline,
    "Trạng thái": d.status
} for d in docs])

st.dataframe(df)
session.close()