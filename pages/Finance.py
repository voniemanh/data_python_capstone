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

def format_currency(x):
    return f"{x:,.0f}"

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

# Streamlit App
st.set_page_config(page_title="💰 Quản lý Chi tiêu", layout="wide")
st.title("💰 Quản lý Chi tiêu")

session = SessionLocal()

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
data = session.query(Personal_Spending).order_by(Personal_Spending.transaction_date.desc()).all()
if data:
    for t in data:
        sign = "+" if t.type == "Thu nhập" else "-"
        with st.expander(f"{sign}{t.amount:,.0f} 👉{t.category} 🗓️{t.transaction_date.strftime('%d-%m-%Y')}"):
            col1, col2, col3 = st.columns(3)
            with col1:
                new_amount = st.number_input("Số tiền", value=t.amount, min_value=0.0, format="%0.0f", key=f"amount_{t.transaction_id}")
                new_type = st.selectbox("Loại", ["Thu nhập", "Chi tiêu"], index=["Thu nhập", "Chi tiêu"].index(t.type), key=f"type_{t.transaction_id}")
            with col2:
                new_category = st.text_input("Danh mục", value=t.category, key=f"cat_{t.transaction_id}")
                new_date = st.date_input("Ngày", value=t.transaction_date, key=f"date_{t.transaction_id}")
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

# DataFrame và hiển thị
st.subheader("📋 Danh sách chi tiêu")
df = fetch_data(session)
if not df.empty:
    df["Ngày"] = pd.to_datetime(df["Ngày"])
    df["Ngày hiển thị"] = df["Ngày"].dt.strftime("%d-%m-%Y")
    st.dataframe(df[["Danh mục","Số tiền","Thu","Chi","Ngày hiển thị"]], width='stretch')

    # Thêm cột Tháng / Năm
    df["Tháng"] = df["Ngày"].dt.strftime("%b-%Y") 
    df["Năm"] = df["Ngày"].dt.year

    # Biểu đồ tổng hợp
    st.subheader("📊 Dashboard tổng hợp")
    fig_month, monthly_summary = plot_monthly(df)
    st.plotly_chart(fig_month, use_container_width=True, config={"displayModeBar": False, "responsive": True})
    
    fig_year, yearly_summary = plot_yearly(df)
    st.plotly_chart(fig_year, use_container_width=True, config={"displayModeBar": False, "responsive": True})

# Xuất Excel
st.subheader("📥 Xuất dữ liệu chi tiêu")
output = io.BytesIO()
df.to_excel(output, index=False)
output.seek(0)
st.download_button("📤 Xuất toàn bộ chi tiêu", data=output, file_name="chi_tieu.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

session.close()
