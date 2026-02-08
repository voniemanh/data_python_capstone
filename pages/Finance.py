import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import date
from models import SessionLocal, Transaction

st.title("💰 Quản lý Chi tiêu")
def get_session():
    return SessionLocal()

session = get_session()

amount = st.number_input("Số tiền", min_value=0.0)
type_ = st.selectbox("Loại", ["Thu nhập", "Chi tiêu"])
cat = st.text_input("Danh mục")
d = st.date_input("Ngày")

if st.button("➕ Ghi nhận"):
    session.add(Transaction(
        amount=amount,
        type=type_,
        category=cat,
        transaction_date=d
    ))
    session.commit()

data = session.query(Transaction).all()
df = pd.DataFrame([{
    "Tháng": t.transaction_date.strftime("%Y-%m"),
    "Số tiền": t.amount if t.type == "Thu nhập" else -t.amount
} for t in data])

if not df.empty:
    balance = df.groupby("Tháng").sum().reset_index()
    fig = px.line(balance, x="Tháng", y="Số tiền", title="Số dư theo tháng")
    st.plotly_chart(fig, use_container_width=True)
session.close()