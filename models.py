import os
from sqlalchemy import (
    Column, Integer, String, Float, Date, Boolean,
    ForeignKey, create_engine
)
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from sqlalchemy import create_engine
from datetime import date

Base = declarative_base()

# ---------- PAGE 1 ----------
class Supplier(Base):
    __tablename__ = "suppliers"
    supplier_id = Column(Integer, primary_key=True)
    supplier_name = Column(String, unique=True)

    invoices = relationship("Invoice", back_populates="supplier")
    products = relationship("Product", back_populates="supplier")

class Product(Base):
    __tablename__ = "products"
    product_id = Column(Integer, primary_key=True)
    product_name = Column(String)
    supplier_id = Column(Integer, ForeignKey("suppliers.supplier_id"))

    supplier = relationship("Supplier", back_populates="products")
    invoices = relationship("Invoice", back_populates="product")

class Invoice(Base):
    __tablename__ = "invoices"
    invoice_id = Column(Integer, primary_key=True)

    supplier_id = Column(Integer, ForeignKey("suppliers.supplier_id"))
    product_id = Column(Integer, ForeignKey("products.product_id"))

    invoice_month = Column(String)

    price = Column(Float)
    quantity = Column(Integer)

    total_amount = Column(Float)
    total_paid = Column(Float)
    total_debt = Column(Float)

    supplier = relationship("Supplier")
    product = relationship("Product")


# ---------- PAGE 2 ----------
class Department(Base):
    __tablename__ = "departments"
    department_id = Column(Integer, primary_key=True)
    department_name = Column(String, unique=True)

    documents = relationship("Document", back_populates="department")
    
class Document(Base):
    __tablename__ = "documents"
    document_id = Column(Integer, primary_key=True)
    document_name = Column(String)
    department_id = Column(Integer, ForeignKey("departments.department_id"))
    deadline = Column(Date)
    status = Column(String)

    department = relationship("Department", back_populates="documents")
# ---------- PAGE 3 ----------
class Todo(Base):
    __tablename__ = "todos"
    todo_id = Column(Integer, primary_key=True)
    task = Column(String)
    due_date = Column(Date)
    is_done = Column(Boolean, default=False)

# ---------- PAGE 4 ----------
class Personal_Spending(Base):
    __tablename__ = "transactions"
    transaction_id = Column(Integer, primary_key=True)
    amount = Column(Float)
    type = Column(String)  
    category = Column(String)
    transaction_date = Column(Date)
    monthly_summary = Column(String)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "database", "app.db")

engine = create_engine(
    f"sqlite:///{DB_PATH}",
    connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(bind=engine)

def init_db():
    Base.metadata.create_all(engine)
