import streamlit as st
from models import init_db

st.set_page_config(page_title="Management App", layout="wide")
init_db()

st.title("📊 Internal Management App")
st.header("Điều hướng đến các trang")
st.page_link("pages/Invoice.py", label="Quản lý hoá đơn")
st.page_link("pages/Reminder.py", label="Quản lý văn kiện")
st.page_link("pages/Todo.py", label="Quản lý công việc")
st.page_link("pages/Finance.py", label="Quản lý chi tiêu")
