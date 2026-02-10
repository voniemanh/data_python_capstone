import streamlit as st
import pandas as pd
from datetime import datetime
from models import (
    SessionLocal, init_db,
    Supplier, Product, Invoice
)

# CONFIG
st.set_page_config(page_title="Hoá đơn NCC", layout="wide")
st.title("📄 Quản lý Hoá đơn Nhà cung cấp")

init_db()
session = SessionLocal()

# HELPERS
def calculate(price, quantity, paid):
    total = price * quantity
    debt = total - paid
    return total, debt


def validate_invoice(price, quantity, paid):
    if price < 0:
        return False, "Giá không hợp lệ"
    if quantity <= 0:
        return False, "Số lượng phải > 0"
    if paid < 0:
        return False, "Đã trả không hợp lệ"
    if paid > price * quantity:
        return False, "Đã trả > Tổng tiền"
    return True, ""


def get_or_create_supplier_product(session, supplier_name, product_name):
    supplier_name = supplier_name.strip()
    product_name = product_name.strip()

    if not supplier_name or not product_name:
        raise ValueError("Nhà cung cấp / Sản phẩm không được để trống")

    supplier = session.query(Supplier).filter_by(
        supplier_name=supplier_name
    ).first()

    if not supplier:
        supplier = Supplier(supplier_name=supplier_name)
        session.add(supplier)
        session.flush()

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
        session.flush()

    return supplier, product

# IMPORT EXCEL
st.subheader("📥 Import Excel")

file = st.file_uploader(
    "File Excel (Nhà cung cấp | Sản phẩm | Tháng | Giá | Số lượng | Đã trả | Nợ)",
    type=["xlsx"]
)
if file:
    df_import = pd.read_excel(file)
    st.dataframe(df_import, use_container_width=True)

    if st.button("⚙️ Xử lý hoá đơn"):
        errors = []

        try:
            for idx, row in df_import.iterrows():
                valid, msg = validate_invoice(
                    row["Giá"],
                    row["Số lượng"],
                    row["Đã trả"]
                )
                if not valid:
                    errors.append(f"Dòng {idx + 1}: {msg}")
                    continue

                supplier, product = get_or_create_supplier_product(
                    session,
                    row["Nhà cung cấp"],
                    row["Sản phẩm"]
                )

                total, debt = calculate(
                    row["Giá"],
                    row["Số lượng"],
                    row["Đã trả"]
                )

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

            if errors:
                session.rollback()
                for e in errors:
                    st.error(e)
                st.error("❌ Import thất bại – không có dữ liệu nào được lưu")
            else:
                session.commit()
                st.success("✅ Import thành công")

        except Exception as e:
            session.rollback()
            st.error("❌ Lỗi hệ thống")
            st.exception(e)

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
            min_value=0.0,
            step=1000.0,
            format="%.0f"
        )

    with col3:
        quantity = st.number_input(
            "Số lượng",
            min_value=1,
            step=1
        )
        paid = st.number_input(
            "Đã trả",
            min_value=0.0,
            step=1000.0,
            format="%.0f"
        )

    submit = st.form_submit_button("💾 Lưu")

if submit:
    valid, msg = validate_invoice(price, quantity, paid)
    if not valid:
        st.error(msg)
    else:
        try:
            supplier, product = get_or_create_supplier_product(
                session,
                supplier_name,
                product_name
            )

            total, debt = calculate(price, quantity, paid)

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

        except Exception as e:
            session.rollback()
            st.error("❌ Lỗi khi lưu")
            st.exception(e)


# LOAD DATA
data = (
    session.query(Invoice, Supplier, Product)
    .select_from(Invoice)
    .join(Supplier)
    .join(Product)
    .order_by(Invoice.invoice_id.desc())
    .all()
)
# DASHBOARD
st.subheader("📋 Danh sách hoá đơn")
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
    st.dataframe(df_summary, width='stretch')
else:
    st.info("Chưa có hoá đơn nào.")

# SUMMARY + CHART 
st.subheader("📊 Phân tích") 

if data:
    df = pd.DataFrame([{
        "Nhà cung cấp": s.supplier_name,
        "Sản phẩm": p.product_name,
        "Tháng": i.invoice_month,
        "Tổng tiền": i.total_amount,
        "Đã trả": i.total_paid,
        "Còn nợ": i.total_debt
    } for i, s, p in data])

    # KPI
    c1, c2, c3 = st.columns(3)
    c1.metric("💰 Tổng phải chi", f"{df['Tổng tiền'].sum():,.0f}")
    c2.metric("💸 Đã trả", f"{df['Đã trả'].sum():,.0f}")
    c3.metric("🔴 Còn nợ", f"{df['Còn nợ'].sum():,.0f}")


    # Charts
    st.markdown("### 🔥 Top Nhà cung cấp còn nợ")
    debt_by_supplier = (
        df.groupby("Nhà cung cấp")["Còn nợ"]
        .sum()
        .sort_values(ascending=False)
    )
    st.bar_chart(debt_by_supplier)

    st.markdown("### 📈 Công nợ theo tháng")
    monthly = (
        df.groupby("Tháng")[["Tổng tiền", "Còn nợ"]]
        .sum()
        .sort_index()
    )
    st.line_chart(monthly)

else:
    st.info("Chưa có dữ liệu")

session.close()
