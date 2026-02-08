import streamlit as st
from datetime import date
from models import SessionLocal, Todo

st.set_page_config(page_title="✅ Todo List", layout="wide")
st.title("✅ Todo List")

session = SessionLocal()

# Thêm task mới
st.subheader("➕ Thêm việc cần làm")
with st.form("add_todo"):
    task_input = st.text_input("Việc cần làm")
    due_input = st.date_input("Ngày")
    submit = st.form_submit_button("💾 Thêm task")

    if submit:
        if not task_input:
            st.error("❌ Vui lòng nhập task")
        else:
            session.add(Todo(task=task_input, due_date=due_input))
            session.commit()
            st.success("✅ Đã thêm task")

st.divider()

# Hiển thị tất cả task
st.subheader("📋 Danh sách task")

todos = session.query(Todo).order_by(Todo.due_date).all()

for t in todos:
    with st.expander(f"📅 {t.due_date} | 📝 {t.task}"):
        col1, col2, col3 = st.columns([4, 2, 1])

        # --- Sửa task ---
        with col1:
            new_task = st.text_input(
                "Task",
                value=t.task,
                key=f"task_{t.todo_id}"
            )
            new_due = st.date_input(
                "Ngày",
                value=t.due_date,
                key=f"due_{t.todo_id}"
            )
            new_done = st.checkbox(
                "Hoàn thành",
                value=t.is_done,
                key=f"done_{t.todo_id}"
            )

        # --- Cập nhật ---
        with col2:
            if st.button("💾 Sửa", key=f"edit_{t.todo_id}"):
                t.task = new_task
                t.due_date = new_due
                t.is_done = new_done
                session.commit()
                st.success("✅ Đã cập nhật")

        # --- Xoá task ---
        with col3:
            if st.button("🗑️ Xoá", key=f"delete_{t.todo_id}"):
                session.delete(t)
                session.commit()
                st.warning("🗑️ Đã xoá")
                st.experimental_rerun()  # reload UI

session.close()