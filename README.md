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
│  ├── Category.py 
│  ├── Customer.py
│  ├── Invoice.py
│  ├── Order.py 
│  ├── Overview.py 
│  ├── Product.py 
│  ├── Promotion.py 
│  └── Supplier.py 
│
├── ui/ 
│  ├── login.ui
│  └── modules_ui/
│     ├── DanhMuc/ ... # Các ui của module Danh Mục 
│     ├── DonHang/ ... # Các ui của module Đơn Hàng 
│     ├── KhachHnag/ ... # Các ui của module Khách Hàng
│     ├── KhuyenMai/ ... # Các ui của module Khuyến Mãi
│     ├── NhaCungCap/ ... # Các ui của module Nhà Cung Cấp 
│     ├── NhanVien/ ... # Các ui của module Nhân Viên 
│     ├── NhapHang/ ... # Các ui của module Nhập Hàng 
│     ├── SanPham/ ... # Các ui của module Sản phẩm
│  ├── NhanVienBanHang/ mainNVBH.ui
│  ├── NhanVienKho/ mainNVK.ui
│  ├── QuanLyCuHang/ main QLCH.ui
│
├── .env 
├── .env.example 
│
└── main.py 
```