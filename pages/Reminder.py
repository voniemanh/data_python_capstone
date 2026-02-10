import streamlit as st
import pandas as pd
from datetime import date, timedelta
from models import SessionLocal, init_db, Document, Department

# CONFIG
st.set_page_config(page_title="Reminder Văn bản", layout="wide")
st.title("⏰ Reminder Văn bản")

init_db()
session = SessionLocal()

# set session state
if "edit_limit" not in st.session_state:
    st.session_state.edit_limit = 10

#  HELPERS 
def get_or_create_department(session, name: str):
    name = name.strip()
    dept = session.query(Department).filter_by(department_name=name).first()
    if not dept:
        dept = Department(department_name=name)
        session.add(dept)
        session.commit()
    return dept

def deadline_label(deadline):
    today = date.today()
    if deadline < today:
        return "Quá hạn"
    if deadline <= today + timedelta(days=3):
        return "Sắp tới"
    return "Đúng hạn"

def style_deadline_row(row):
    color_map = {
        "Quá hạn": "background-color:#ffdddd",
        "Sắp tới": "background-color:#fff4cc",
        "Đúng hạn": "background-color:#ddffdd",
    }
    bg = color_map[row["Nhãn trạng thái"]]
    return [bg] * len(row)

#  ADD DOCUMENT 
st.subheader("➕ Thêm văn bản")

with st.form("add_doc"):
    c1, c2 = st.columns(2)
    with c1:
        name = st.text_input("Tên văn bản")
        dept = st.text_input("Phòng ban")
    with c2:
        deadline = st.date_input("Deadline")
        status = st.selectbox("Trạng thái", ["Đang xử lý", "Hoàn thành", "Tạm dừng"])

    if st.form_submit_button("💾 Thêm"):
        if not name or not dept:
            st.error("❌ Thiếu thông tin")
            st.stop()

        department = get_or_create_department(session, dept)
        session.add(Document(
            document_name=name,
            department_id=department.department_id,
            deadline=deadline,
            status=status
        ))
        session.commit()
        st.success("✅ Đã thêm")
        st.rerun()

#  LIST & EDIT 
st.subheader("📋 Danh sách văn bản")

docs = (
    session.query(Document, Department)
    .join(Department)
    .order_by(Document.deadline)
    .limit(st.session_state.edit_limit)
    .all()
)

total = session.query(Document).count()

late_exist = any(
    d.deadline < date.today() and d.status != "Hoàn thành"
    for d, _ in docs
)

if late_exist:
    st.error("⚠️ Có văn bản quá hạn chưa xử lý!")

def render_editor(d, dept):
    with st.expander(f"📄 {d.document_name} | 🏢 {dept.department_name}"):
        with st.form(f"edit_{d.document_id}"):
            c1, c2 = st.columns(2)

            with c1:
                name = st.text_input("Tên văn bản", d.document_name)
                deadline = st.date_input("Deadline", d.deadline)

            with c2:
                dept_name = st.text_input("Phòng ban", dept.department_name)
                status = st.selectbox(
                    "Trạng thái",
                    ["Đang xử lý", "Hoàn thành", "Tạm dừng"],
                    index=["Đang xử lý", "Hoàn thành", "Tạm dừng"].index(d.status)
                )

            col_save, col_del = st.columns(2)

            if col_save.form_submit_button("💾 Lưu"):
                department = get_or_create_department(session, dept_name)
                d.document_name = name
                d.deadline = deadline
                d.status = status
                d.department_id = department.department_id
                session.commit()
                st.success("✅ Đã cập nhật")
                st.rerun()

            if col_del.form_submit_button("🗑️ Xoá"):
                session.delete(d)
                session.commit()
                st.warning("🗑️ Đã xoá")
                st.rerun()

for d, dept in docs:
    render_editor(d, dept)

if st.session_state.edit_limit < total:
    if st.button("➕ Xem thêm"):
        st.session_state.edit_limit += 10
        st.rerun()

#  SUMMARY TABLE 
st.subheader("📊 Tổng hợp tình trạng văn bản")

data = session.query(Document, Department).join(Department).all()

if not data:
    st.info("Chưa có văn bản.")
else:
    df = pd.DataFrame([
        {
            "Tên văn bản": d.document_name,
            "Phòng ban": dept.department_name,
            "Deadline": d.deadline,
            "Trạng thái": d.status,
            "Nhãn trạng thái": deadline_label(d.deadline)
        }
        for d, dept in data
    ])

    df.index = range(1, len(df) + 1)

    styled = df.style.apply(style_deadline_row, axis=1)

    st.dataframe(styled, use_container_width=True)

session.close()
