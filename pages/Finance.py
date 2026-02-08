import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import date
from models import SessionLocal, Personal_Spending

st.set_page_config(page_title="💰 Quản lý Chi tiêu", layout="wide")
st.title("💰 Quản lý Chi tiêu")

session = SessionLocal()

# INPUT CHI TIÊU
amount = st.number_input("Số tiền", min_value=0.0)
type_ = st.selectbox("Loại", ["Thu nhập", "Chi tiêu"])
cat = st.text_input("Danh mục")
d = st.date_input("Ngày")

if st.button("➕ Ghi nhận"):
    session.add(Personal_Spending(
        amount=amount,
        type=type_,
        category=cat,
        transaction_date=d
    ))
    session.commit()
    st.success("✅ Đã ghi nhận")

st.divider()

# DỮ LIỆU + CRUD
st.subheader("📋 Danh sách chi tiêu")

data = session.query(Personal_Spending).order_by(Personal_Spending.transaction_date.desc()).all()

for t in data:
    sign = "+" if t.type == "Thu nhập" else "-"
    with st.expander(f"{sign}{t.amount:,.0f} | {t.category} | {t.transaction_date}"):
        col1, col2, col3 = st.columns(3)

        with col1:
            new_amount = st.number_input(
                "Số tiền",
                value=t.amount,
                min_value=0.0,
                key=f"amount_{t.transaction_id}"
            )
            new_type = st.selectbox(
                "Loại",
                ["Thu nhập", "Chi tiêu"],
                index=["Thu nhập", "Chi tiêu"].index(t.type),
                key=f"type_{t.transaction_id}"
            )

        with col2:
            new_category = st.text_input(
                "Danh mục",
                value=t.category,
                key=f"cat_{t.transaction_id}"
            )
            new_date = st.date_input(
                "Ngày",
                value=t.transaction_date,
                key=f"date_{t.transaction_id}"
            )

        with col3:
            if st.button("💾 Sửa", key=f"edit_{t.transaction_id}"):
                t.amount = new_amount
                t.type = new_type
                t.category = new_category
                t.transaction_date = new_date
                session.commit()
                st.success("✅ Đã cập nhật")

            if st.button("🗑️ Xoá", key=f"delete_{t.transaction_id}"):
                session.delete(t)
                session.commit()
                st.warning("🗑️ Đã xoá")
                st.experimental_rerun()

# DATAFRAME TỔNG HỢP
df = pd.DataFrame([{
    "Tháng": t.transaction_date.strftime("%Y-%m"),
    "Năm": t.transaction_date.year,
    "Số tiền": t.amount if t.type == "Thu nhập" else -t.amount,
    "Loại": t.type,
    "Danh mục": t.category,
    "Ngày": t.transaction_date
} for t in session.query(Personal_Spending).all()])

# EXPORT EXCEL
st.subheader("📥 Export Excel")
if st.button("📤 Xuất toàn bộ chi tiêu"):
    df.to_excel("chi_tieu.xlsx", index=False)
    st.success("✅ Đã xuất Excel: chi_tieu.xlsx")

# DASHBOARD TỔNG
st.subheader("📊 Dashboard tổng")

if not df.empty:
    # --- Theo tháng ---
    monthly = df.groupby("Tháng")["Số tiền"].sum().reset_index()
    fig_month = px.bar(
        monthly,
        x="Tháng",
        y="Số tiền",
        color="Số tiền",
        color_continuous_scale="Viridis",
        title="💹 Tổng thu/chi theo tháng"
    )
    st.plotly_chart(fig_month, use_container_width=True)

    # --- Theo năm ---
    yearly = df.groupby("Năm")["Số tiền"].sum().reset_index()
    fig_year = px.bar(
        yearly,
        x="Năm",
        y="Số tiền",
        color="Số tiền",
        color_continuous_scale="Cividis",
        title="💹 Tổng thu/chi theo năm"
    )
    st.plotly_chart(fig_year, use_container_width=True)

session.close()
