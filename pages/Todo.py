import streamlit as st
from datetime import date
from models import SessionLocal, Todo

st.title("✅ Todo List")
def get_session():
    return SessionLocal()

session = get_session()

task = st.text_input("Việc cần làm")
due = st.date_input("Ngày")

if st.button("➕ Thêm task"):
    session.add(Todo(task=task, due_date=due))
    session.commit()

todos = session.query(Todo).filter_by(due_date=due).all()

for t in todos:
    checked = st.checkbox(
        t.task,
        value=t.is_done,
        key=t.todo_id
    )
    if checked != t.is_done:
        t.is_done = checked
        session.commit()
session.close()