import streamlit as st
import pandas as pd
from datetime import date
from models import SessionLocal, init_db, Document, Department
from datetime import timedelta

st.set_page_config(page_title="Reminder Văn kiện", layout="wide")
st.title("⏰ Reminder Văn kiện")

init_db()
session = SessionLocal()

# HELPER
def get_or_create_department(session, dept_name: str):
    dept_name = dept_name.strip()

    department = session.query(Department).filter_by(
        department_name=dept_name
    ).first()

    if not department:
        department = Department(department_name=dept_name)
        session.add(department)
        session.commit()

    return department

def deadline_color(deadline):
    today = date.today()

    if deadline < today:
        return "🔴 QUÁ HẠN"
    elif deadline <= today + timedelta(days=3):
        return "🟠 SẮP TỚI"
    else:
        return "🟢 OK"

# ➕ ADD DOCUMENT
st.subheader("➕ Thêm văn kiện")

with st.form("add_doc"):
    col1, col2 = st.columns(2)

    with col1:
        name = st.text_input("Tên văn kiện")
        dept = st.text_input("Phòng ban")

    with col2:
        deadline = st.date_input("Deadline")
        status = st.selectbox(
            "Trạng thái",
            ["Đang xử lý", "Hoàn thành", "Tạm dừng"]
        )

    submit = st.form_submit_button("💾 Thêm")

    if submit:
        if not name or not dept:
            st.error("❌ Vui lòng nhập đủ thông tin")
            st.stop()

        department = get_or_create_department(session, dept)

        session.add(Document(
            document_name=name,
            department_id=department.department_id,
            deadline=deadline,
            status=status
        ))
        session.commit()

        st.success("✅ Đã thêm văn kiện")

st.divider()

# 📋 LIST + CRUD

st.subheader("📋 Danh sách văn kiện")

docs = (
    session.query(Document, Department)
    .join(Department)
    .order_by(Document.deadline)
    .all()
)

# ALERT
late_docs = [
    d for d, dept in docs
    if d.deadline < date.today() and d.status != "Hoàn thành"
]

if late_docs:
    st.error("⚠️ Có văn kiện trễ hạn!")

for d, dept in docs:
    with st.expander(f"📄 {d.document_name} | 🏢 {dept.department_name}"):

        col1, col2, col3 = st.columns(3)

        with col1:
            new_name = st.text_input(
                "Tên văn kiện",
                value=d.document_name,
                key=f"name_{d.document_id}"
            )
            new_deadline = st.date_input(
                "Deadline",
                value=d.deadline,
                key=f"deadline_{d.document_id}"
            )

        with col2:
            new_dept = st.text_input(
                "Phòng ban",
                value=dept.department_name,
                key=f"dept_{d.document_id}"
            )
            new_status = st.selectbox(
                "Trạng thái",
                ["Đang xử lý", "Hoàn thành", "Tạm dừng"],
                index=["Đang xử lý", "Hoàn thành", "Tạm dừng"].index(d.status),
                key=f"status_{d.document_id}"
            )

        with col3:
            if st.button("💾 Sửa", key=f"edit_{d.document_id}"):
                department = get_or_create_department(session, new_dept)

                d.document_name = new_name
                d.deadline = new_deadline
                d.status = new_status
                d.department_id = department.department_id

                session.commit()
                st.success("✅ Đã cập nhật")

            if st.button("🗑️ Xoá", key=f"delete_{d.document_id}"):
                session.delete(d)
                session.commit()
                st.warning("🗑️ Đã xoá")
                st.experimental_rerun()

session.close()