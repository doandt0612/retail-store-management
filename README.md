# 🛒 Hệ thống Quản lý Cửa hàng Bán lẻ Trực tuyến

Hệ thống giúp quản lý hoạt động của một cửa hàng bán lẻ trực tuyến bao gồm:
- Quản lý sản phẩm
- Quản lý khách hàng
- Quản lý đơn hàng
- Quản lý kho
- Quản lý nhà cung cấp

---

# 📂 Cấu trúc dự án
```
RETAIL_STORE_MANAGEMENT/
│
├── src/ 
│ │
│ ├── database/ 
│ │ ├── db_connection.py 
│ │ └── QUANLYCUAHANG.sql 
│ │
│ └── modules/ 
│ ├── Category.py 
│ ├── Customer.py 
│ ├── Order.py 
│ ├── Overview.py 
│ ├── Product.py 
│ ├── Stock.py 
│ └── Supplier.py 
│
├── ui/ 
│ ├── main.ui
│ └── ... # Các dialog UI khác
│
├── .env 
├── .env.example 
│
└── main.py 
```