import streamlit as st
import pandas as pd
from models import (
    SessionLocal, init_db,
    Supplier, Product, Invoice
)

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

# HELPER
def get_or_create_supplier_product(
    session,
    supplier_name: str,
    product_name: str
):
    # ---- SUPPLIER ----
    supplier = session.query(Supplier).filter_by(
        supplier_name=supplier_name
    ).first()

    if not supplier:
        supplier = Supplier(supplier_name=supplier_name)
        session.add(supplier)
        session.commit()

    # ---- PRODUCT ----
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

if file:
    df = pd.read_excel(file)
    st.dataframe(df)

    if st.button("⚙️ Xử lý hoá đơn"):
        for _, row in df.iterrows():
            # Supplier
            supplier, product = get_or_create_supplier_product(
                session,
                row["Nhà cung cấp"],
                row["Sản phẩm"]
            )

            total = row["Giá"] * row["Số lượng"]

            invoice = Invoice(
                supplier_id=supplier.supplier_id,
                product_id=product.product_id,
                invoice_month=row["Tháng"],
                price=row["Giá"],
                quantity=row["Số lượng"],
                total_amount=total,
                total_paid=row["Đã trả"],
                total_debt=row["Nợ"]
            )
            session.add(invoice)

        session.commit()
        st.success("✅ Import thành công")

st.divider()

# INPUT TAY
st.subheader("➕ Nhập hoá đơn thủ công")

with st.form("add_invoice"):
    col1, col2, col3 = st.columns(3)

    with col1:
        supplier_name = st.text_input("Nhà cung cấp")
        product_name = st.text_input("Sản phẩm")

    with col2:
        month = st.text_input("Tháng (YYYY-MM)")
        price = st.number_input("Giá", min_value=0.0)

    with col3:
        quantity = st.number_input("Số lượng", min_value=1, step=1)
        paid = st.number_input("Đã trả", min_value=0.0)
        debt = st.number_input("Nợ", min_value=0.0)

    submit = st.form_submit_button("💾 Lưu")

    if submit:
        supplier, product = get_or_create_supplier_product(
            session,
            supplier_name,
            product_name
        )

        total = price * quantity

        invoice = Invoice(
            supplier_id=supplier.supplier_id,
            product_id=product.product_id,
            invoice_month=month,
            price=price,
            quantity=quantity,
            total_amount=total,
            total_paid=paid,
            total_debt=debt
        )
        session.add(invoice)
        session.commit()

        st.success("✅ Đã thêm hoá đơn")

st.divider()

# TỔNG HỢP + CRUD
st.subheader("📋 Danh sách hoá đơn")

data = (
    session.query(Invoice, Supplier, Product)
    .select_from(Invoice)
    .join(Supplier, Invoice.supplier_id == Supplier.supplier_id)
    .join(Product, Invoice.product_id == Product.product_id)
    .order_by(Invoice.invoice_id.desc())
    .all()
)

for i, s, p in data:
    with st.expander(
        f"🏷️ {s.supplier_name} | {p.product_name} | {i.invoice_month}"
    ):
        col1, col2, col3 = st.columns(3)

        with col1:
            st.write(f"💰 Tổng: **{i.total_amount:,.0f}**")
            st.write(f"📦 SL: {i.quantity}")

        with col2:
            new_paid = st.number_input(
                "Đã trả",
                value=i.total_paid,
                key=f"paid_{i.invoice_id}"
            )
            new_debt = st.number_input(
                "Nợ",
                value=i.total_debt,
                key=f"debt_{i.invoice_id}"
            )

        with col3:
            if st.button("💾 Sửa", key=f"edit_{i.invoice_id}"):
                i.total_paid = new_paid
                i.total_debt = new_debt
                session.commit()
                st.success("✅ Đã cập nhật")

            if st.button("🗑️ Xoá", key=f"delete_{i.invoice_id}"):
                session.delete(i)
                session.commit()
                st.warning("🗑️ Đã xoá")
                st.experimental_rerun()

session.close()
