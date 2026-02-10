import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import date
from models import SessionLocal, Personal_Spending
import io

# Helpers
def fetch_data(session):
    data = session.query(Personal_Spending).order_by(Personal_Spending.transaction_date.desc()).all()
    if not data:
        return pd.DataFrame()
    
    df = pd.DataFrame([{
        "Ngày": t.transaction_date,
        "Loại": t.type,
        "Danh mục": t.category,
        "Số tiền": t.amount,
        "Thu": t.amount if t.type == "Thu nhập" else 0,
        "Chi": t.amount if t.type == "Chi tiêu" else 0
    } for t in data])
    
    return df

def plot_monthly(df):
    monthly = df.groupby("Tháng")[["Thu", "Chi"]].sum().reset_index()
    monthly["Tổng"] = monthly["Thu"] - monthly["Chi"]
    
    fig = px.bar(
        monthly,
        x="Tháng",
        y=["Thu", "Chi"],
        title="💹 Thu/Chi theo tháng",
        barmode='group',
        color_discrete_map={"Thu":"blue", "Chi":"orange"},
        text_auto=".0f"  
    )
    fig.update_layout(yaxis_title="Số tiền (VND)")
    return fig, monthly

def plot_yearly(df):
    yearly = df.groupby("Năm")[["Thu", "Chi"]].sum().reset_index()
    yearly["Tổng"] = yearly["Thu"] - yearly["Chi"]
    
    fig = px.bar(
        yearly,
        x="Năm",
        y=["Thu", "Chi"],
        title="💹 Thu/Chi theo năm",
        barmode='group',
        color_discrete_map={"Thu":"blue", "Chi":"orange"},
        text_auto=".0f" 
    )
    fig.update_layout(yaxis_title="Số tiền (VND)", xaxis=dict(tickformat="d"))
    return fig, yearly

def render_edit_transaction(session, t):
    sign = "+" if t.type == "Thu nhập" else "-"

    with st.expander(
        f"{sign}{t.amount:,.0f} 👉 {t.category} 🗓️ {t.transaction_date:%d-%m-%Y}"
    ):
        with st.form(key=f"form_{t.transaction_id}"):

            col1, col2, col3 = st.columns(3)

            with col1:
                amount = st.number_input(
                    "Số tiền",
                    value=t.amount,
                    min_value=0.0,
                    step=1000.0,
                    format="%0.0f"
                )
                type_ = st.selectbox(
                    "Loại",
                    ["Thu nhập", "Chi tiêu"],
                    index=0 if t.type == "Thu nhập" else 1
                )

            with col2:
                cat = st.text_input("Danh mục", value=t.category)
                d = st.date_input("Ngày", value=t.transaction_date)

            with col3:
                save = st.form_submit_button("💾 Sửa")
                delete = st.form_submit_button("🗑️ Xoá")

            if save:
                t.amount = amount
                t.type = type_
                t.category = cat
                t.transaction_date = d
                session.commit()
                st.success("✅ Đã cập nhật")
                st.rerun()

            if delete:
                session.delete(t)
                session.commit()
                st.warning("🗑️ Đã xoá")
                st.rerun()

# Streamlit App
st.set_page_config(page_title="💰 Quản lý Chi tiêu", layout="wide")
st.title("💰 Quản lý Chi tiêu")

session = SessionLocal()

# Set view limit
if "edit_limit" not in st.session_state:
    st.session_state.edit_limit = 10

# Input chi tiêu 
amount = st.number_input("Số tiền", min_value=0.0, step=1000.0, format="%0.0f")
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

# Chỉnh sửa / Xoá chi tiêu
st.subheader("✏️ Chỉnh sửa / Xoá chi tiêu")

total_count = session.query(Personal_Spending).count()

data = session.query(Personal_Spending).order_by(Personal_Spending.transaction_date.desc()).limit(st.session_state.edit_limit).all()
if data:
    for t in data:
        render_edit_transaction(session, t)
    if st.session_state.edit_limit < total_count:
        if st.button("➕ Xem thêm"):
            st.session_state.edit_limit += 10
            st.rerun()
else:
    st.info("Chưa có chi tiêu nào được ghi nhận.")

# DataFrame và hiển thị
st.subheader("📋 Danh sách chi tiêu")
df = fetch_data(session)
if not df.empty:
    df["Ngày"] = pd.to_datetime(df["Ngày"])
    df["Ngày hiển thị"] = df["Ngày"].dt.strftime("%d-%m-%Y")
    df.index = range(1, len(df) + 1)
    st.dataframe(df[["Danh mục","Số tiền","Thu","Chi","Ngày hiển thị"]], width='stretch')

    # Biểu đồ tổng hợp
    st.subheader("📊 Dashboard tổng hợp")
    df["Tháng"] = df["Ngày"].dt.strftime("%b-%Y") 
    df["Năm"] = df["Ngày"].dt.year
    fig_month, monthly_summary = plot_monthly(df)
    st.plotly_chart(fig_month, use_container_width=True, config={"displayModeBar": False, "responsive": True})
    
    fig_year, yearly_summary = plot_yearly(df)
    st.plotly_chart(fig_year, use_container_width=True, config={"displayModeBar": False, "responsive": True})

# Xuất Excel
st.subheader("📥 Xuất dữ liệu chi tiêu")
export_df = df.drop(columns=["Ngày", "Tháng", "Năm"], errors="ignore")
output = io.BytesIO()
export_df.to_excel(output, index=False)
output.seek(0)
st.download_button("📤 Xuất toàn bộ chi tiêu", data=output, file_name="chi_tieu.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

session.close()
