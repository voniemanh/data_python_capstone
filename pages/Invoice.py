import streamlit as st
import pandas as pd
from models import (
    SessionLocal, init_db,
    Supplier, Product, Invoice
)

# CONFIG
st.set_page_config(page_title="Hoá đơn NCC", layout="wide")
st.title("📄 Quản lý Hoá đơn Nhà cung cấp")

init_db()
session = SessionLocal()

# IMPORT EXCEL
st.subheader("📥 Import Excel")

file = st.file_uploader(
    "File Excel (Nhà cung cấp | Sản phẩm | Tháng | Giá | Số lượng | Đã trả | Nợ)",
    type=["xlsx"]
)

# HELPERS
def get_or_create_supplier_product(session, supplier_name, product_name):
    supplier = session.query(Supplier).filter_by(
        supplier_name=supplier_name
    ).first()

    if not supplier:
        supplier = Supplier(supplier_name=supplier_name)
        session.add(supplier)
        session.commit()

    product = session.query(Product).filter_by(
        product_name=product_name,
        supplier_id=supplier.supplier_id
    ).first()

    if not product:
        product = Product(
            product_name=product_name,
            supplier_id=supplier.supplier_id
        )
        session.add(product)
        session.commit()

    return supplier, product

# HANDLE IMPORT
if file:
    df = pd.read_excel(file)
    st.dataframe(df, use_container_width=True)

    if st.button("⚙️ Xử lý hoá đơn"):
        for _, row in df.iterrows():
            supplier, product = get_or_create_supplier_product(
                session,
                row["Nhà cung cấp"],
                row["Sản phẩm"]
            )

            total = row["Giá"] * row["Số lượng"]
            debt = total - row["Đã trả"]

            session.add(Invoice(
                supplier_id=supplier.supplier_id,
                product_id=product.product_id,
                invoice_month=row["Tháng"],
                price=row["Giá"],
                quantity=row["Số lượng"],
                total_amount=total,
                total_paid=row["Đã trả"],
                total_debt=debt
            ))

        session.commit()
        st.success("✅ Import thành công")

# INPUT TAY
st.subheader("➕ Nhập hoá đơn thủ công")

with st.form("add_invoice", clear_on_submit=True):
    col1, col2, col3 = st.columns(3)

    with col1:
        supplier_name = st.text_input("Nhà cung cấp")
        product_name = st.text_input("Sản phẩm")

    with col2:
        month = st.text_input("Tháng (YYYY-MM)")
        price = st.number_input(
            "Giá",
            value=0.0,
            min_value=0.0,
            step=1000.0,
            format="%.0f"
        )

    with col3:
        quantity = st.number_input(
            "Số lượng",
            value=1,
            min_value=1,
            step=1
        )
        paid = st.number_input(
            "Đã trả",
            value=0.0,
            min_value=0.0,
            step=1000.0,
            format="%.0f"
        )

    # AUTO CALC
    total = price * quantity
    debt = total - paid
    submit = st.form_submit_button("💾 Lưu")

if submit:
    supplier, product = get_or_create_supplier_product(
        session,
        supplier_name,
        product_name
    )

    session.add(Invoice(
        supplier_id=supplier.supplier_id,
        product_id=product.product_id,
        invoice_month=month,
        price=price,
        quantity=quantity,
        total_amount=total,
        total_paid=paid,
        total_debt=debt
    ))
    session.commit()

    st.success("✅ Đã thêm hoá đơn")

# LIST + CRUD
st.subheader("📋 Danh sách hoá đơn")

data = (
    session.query(Invoice, Supplier, Product)
    .select_from(Invoice)
    .join(Supplier)
    .join(Product)
    .order_by(Invoice.invoice_id.desc())
    .all()
)

for i, s, p in data:
    title = f"🏷️ {s.supplier_name} | {p.product_name} | {i.invoice_month}"
    if i.total_debt > 0:
        title = "🔴 " + title

    with st.expander(title):
        col1, col2, col3 = st.columns(3)

        with col1:
            new_price = st.number_input(
                "Giá",
                value=float(i.price),
                step=1000.0,
                format="%.0f",
                key=f"amount_{i.invoice_id}"
            )
            new_quantity = st.number_input(
                "Số lượng",
                value=int(i.quantity),
                step=1,
                format="%d",
                key=f"quantity_{i.invoice_id}"  
            )

        with col2:
            new_paid = st.number_input(
                "Đã trả",
                value=float(i.total_paid),
                step=1000.0,
                format="%.0f",
                key=f"paid_{i.invoice_id}"
            )
            new_month = st.text_input(
                "Tháng (YYYY-MM)",
                value=i.invoice_month,
                key=f"month_{i.invoice_id}"
            )

        with col3:
            if st.button("💾 Sửa", key=f"edit_{i.invoice_id}"):
                i.quantity = new_quantity
                i.price = new_price    
                i.total_amount = new_price * new_quantity
                i.total_paid = new_paid
                i.total_debt = i.total_amount - new_paid
                i.invoice_month = new_month
                session.commit()
                st.success("✅ Đã cập nhật")

            if st.button("🗑️ Xoá", key=f"delete_{i.invoice_id}"):
                session.delete(i)
                session.commit()
                st.warning("🗑️ Đã xoá")
                st.rerun()

# SUMMARY TABLE
st.subheader("📊 Tổng hợp hoá đơn")

summary = [
    {
        "Nhà cung cấp": s.supplier_name,
        "Sản phẩm": p.product_name,
        "Tháng": i.invoice_month,
        "Giá": f"{i.price:,.0f}",
        "Số lượng": f"{i.quantity:,}",
        "Tổng tiền": f"{i.total_amount:,.0f}",
        "Đã trả": f"{i.total_paid:,.0f}",
        "Còn nợ": f"{i.total_debt:,.0f}",
    }
    for i, s, p in data
]

if summary:
    df_summary = pd.DataFrame(summary)
    df_summary.index = range(1, len(df_summary) + 1)
    st.dataframe(df_summary, use_container_width=True)
else:
    st.info("Chưa có hoá đơn nào.")

session.close()
