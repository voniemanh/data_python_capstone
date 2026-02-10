import streamlit as st
from datetime import date
from models import SessionLocal, Todo

st.set_page_config(page_title="✅ Todo List", layout="wide")
st.title("✅ Todo List")

session = SessionLocal()

# CSS để căn giữa checkbox
st.markdown(
    """
    <style>
    .stHorizontalBlock {
        align-items: center !important;
    }
    .stHorizontalBlock div[data-testid="stCheckbox"] {
        align-self: center !important;
        margin-top: 0 !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# validate task
def validate_task(task: str):
    if not task:
        st.error("❌ Vui lòng nhập task")
        return False
    return True

# Thêm task mới
st.subheader("➕ Thêm việc cần làm")
with st.form("add_todo"):
    task_input = st.text_input("Việc cần làm")
    due_input = st.date_input("Ngày")
    submit = st.form_submit_button("💾 Thêm task")

    if submit and validate_task(task_input):
        session.add(Todo(task=task_input, due_date=due_input))
        session.commit()
        st.success("✅ Đã thêm task")

# Filter
st.subheader("📅 Lọc theo ngày")

filter_date = st.date_input(
    "Chọn ngày",
    value=date.today()
)

# Query task 
todos = (
    session.query(Todo)
    .filter(Todo.due_date == filter_date)
    .order_by(Todo.due_date)
    .all()
)

# Hiển thị danh sách task
st.subheader("📋 Danh sách task")

if not todos:
    st.info("😴 Không có task nào cho ngày này")
else:
    for t in todos:
        cols = st.columns([0.5, 5, 2])

        # Checkbox hoàn thành
        with cols[0]:
            done = st.checkbox(
                "Hoàn thành task",
                value=t.is_done,
                key=f"check_{t.todo_id}",
                label_visibility="collapsed"
            )

        # Nội dung task
        with cols[1]:
            if done:
                st.markdown(f"~~{t.task}~~")
            else:
                st.markdown(t.task)

        # Ngày
        with cols[2]:            
            st.caption(f"📅 {t.due_date}")

        # Update khi check/uncheck
        if done != t.is_done:
            t.is_done = done
            session.commit()
            st.rerun()

# Xoá/sửa task
st.subheader("🤖 Quản lý task")
todo_ids = [t.todo_id for t in todos]
todo_dict = {t.todo_id: t.task for t in todos}  
selected_todo_id = st.selectbox(
    "Chọn task để xoá/sửa",
    todo_ids,
    format_func=lambda x: todo_dict[x]
)
if selected_todo_id:
    selected_todo = session.get(Todo, selected_todo_id)

    # Xoá task
    if st.button("🗑️ Xoá task"):
        session.delete(selected_todo)
        session.commit()
        st.rerun()
    # Sửa task
    st.write("✏️ Sửa task")
    new_task_input = st.text_input(
        "Việc cần làm",
        value=selected_todo.task
    )
    new_due_input = st.date_input(
        "Ngày",
        value=selected_todo.due_date
    )
    edit_submit = st.button("💾 Lưu thay đổi")

    if edit_submit and validate_task(new_task_input):
        selected_todo.task = new_task_input
        selected_todo.due_date = new_due_input
        session.commit()
        st.rerun()

session.close()