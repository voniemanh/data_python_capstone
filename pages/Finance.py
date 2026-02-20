import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
from models import SessionLocal, Personal_Spending, ChatHistory
import io
from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(page_title="💰 Quản lý Chi tiêu", layout="wide")
st.title("💰 Quản lý Chi tiêu")

session = SessionLocal()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

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

def build_financial_context(df):
    monthly = df.groupby("Tháng")[["Thu", "Chi"]].sum()
    yearly = df.groupby("Năm")[["Thu", "Chi"]].sum()
    category = df.groupby("Danh mục")[["Thu", "Chi"]].sum()

    total_income = df["Thu"].sum()
    total_expense = df["Chi"].sum()

    saving_rate = 0
    if total_income > 0:
        saving_rate = (total_income - total_expense) / total_income * 100

    return f"""
Tổng thu: {total_income:,.0f}
Tổng chi: {total_expense:,.0f}
Tỉ lệ tiết kiệm: {saving_rate:.2f}%

Theo tháng:
{monthly.to_string()}

Theo năm:
{yearly.to_string()}

Theo danh mục:
{category.to_string()}
"""

# Set view limit
if "edit_limit" not in st.session_state:
    st.session_state.edit_limit = 10

# Nhập chi tiêu mới
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
    st.plotly_chart(fig_month, use_container_width=True)
    
    fig_year, yearly_summary = plot_yearly(df)
    st.plotly_chart(fig_year, use_container_width=True)

# Xuất Excel
st.subheader("📥 Xuất dữ liệu chi tiêu")
export_df = df.drop(columns=["Ngày", "Tháng", "Năm", "Thu", "Chi"], errors="ignore")
output = io.BytesIO()
export_df.to_excel(output, index=False)
output.seek(0)
st.download_button("📤 Xuất toàn bộ chi tiêu", data=output, file_name="chi_tieu.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

# Chatbot AI
st.subheader("🤖 Trợ lý tài chính AI")
question = st.text_input("Hỏi về chi tiêu của bạn")

if st.button("💬 Hỏi AI"):
    if not df.empty and question:

        context = build_financial_context(df)

        messages = [
            {
                "role": "system",
                "content": """
Bạn là chuyên gia tư vấn tài chính cá nhân 10 năm kinh nghiệm.
Phân tích dữ liệu logic.
Chỉ ra điểm mạnh, điểm yếu.
Đưa ra lời khuyên cụ thể.
Không nói chung chung.
"""
            },
            {
                "role": "user",
                "content": f"""
Dữ liệu tài chính:
{context}

Câu hỏi:
{question}
"""
            }
        ]

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages
        )

        answer = response.choices[0].message.content
        st.success(answer)

        session.add(ChatHistory(
            question=question,
            answer=answer
        ))
        session.commit()

# CHAT HISTORY
st.subheader("📜 Lịch sử hỏi đáp")

history = session.query(ChatHistory)\
    .order_by(ChatHistory.created_at.desc())\
    .limit(10)\
    .all()

for h in history:
    st.markdown(f"**🧑 Bạn:** {h.question}")
    st.markdown(f"**🤖 AI:** {h.answer}")
    st.divider()

session.close()
