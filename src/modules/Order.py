import os
from PyQt6 import uic, QtWidgets
from PyQt6.QtCore import Qt
from src.database.db_connection import DatabaseManager

# Lấy đường dẫn gốc
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(os.path.dirname(CURRENT_DIR))
UI_PATH = os.path.join(ROOT_DIR, "ui", "modules_ui", "DonHang")

# ==========================================
# DIALOG CHI TIẾT ĐƠN HÀNG (KÈM CHUYỂN TRANG KHÁCH HÀNG)
# ==========================================
class ViewOrder(QtWidgets.QDialog):
    def __init__(self, data, switch_to_customer_callback=None):
        super().__init__()
        uic.loadUi(os.path.join(UI_PATH, "viewDonHang.ui"), self)
        
        self.order_id = data['id']
        self.customer_data = data['customer_info'] # Chứa id, tên, sdt của KH
        self.switch_to_customer_callback = switch_to_customer_callback
        
        self.load_general_info(data)
        self.load_product_list()
        self.load_payment_info()
        
        # Nút đóng
        if hasattr(self, 'btnDong'):
            self.btnDong.clicked.connect(self.close)

    def load_general_info(self, data):
        """1. Thông tin chung"""
        if hasattr(self, 'lblHienThiMaDon'): self.lblHienThiMaDon.setText(str(data['id']))
        if hasattr(self, 'lblHienThiNgayMua'): self.lblHienThiNgayMua.setText(data['ngay'])
        if hasattr(self, 'lblHienThiTongTien'): self.lblHienThiTongTien.setText(data['tien'])
        
        # Xử lý màu sắc trạng thái
        if hasattr(self, 'lblHienThiTrangThai'):
            self.lblHienThiTrangThai.setText(data['trang_thai'])
            if "Đã thanh toán" in data['trang_thai']:
                self.lblHienThiTrangThai.setStyleSheet("color: #10b981; font-weight: bold;")
            else:
                self.lblHienThiTrangThai.setStyleSheet("color: #ef4444; font-weight: bold;")
        
        # BIẾN TÊN KHÁCH HÀNG THÀNH LINK CLICK ĐƯỢC
        if hasattr(self, 'lblHienThiKhachHang'):
            ten_kh = self.customer_data['ten']
            link_html = f'<a href="#cus" style="color: #2563eb; text-decoration: none; font-weight: bold;">{ten_kh}</a>'
            self.lblHienThiKhachHang.setText(link_html)
            self.lblHienThiKhachHang.setOpenExternalLinks(False)
            self.lblHienThiKhachHang.linkActivated.connect(self.on_customer_name_clicked)

    def on_customer_name_clicked(self, link):
        """Xử lý khi click vào tên khách hàng"""
        self.close() # 1. Đóng popup chi tiết đơn hàng
        # 2. Gọi hàm callback để main.py xử lý chuyển trang và mở lịch sử
        if self.switch_to_customer_callback:
            self.switch_to_customer_callback(self.customer_data)

    def load_product_list(self):
        """2. Danh sách sản phẩm (JOIN Order_Details và Products)"""
        if not hasattr(self, 'tblDanhSachSanPham'): return
        
        self.tblDanhSachSanPham.verticalHeader().setVisible(False)
        self.tblDanhSachSanPham.setEditTriggers(QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tblDanhSachSanPham.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode.Stretch)
        
        db = DatabaseManager()
        conn = db.get_connection()
        if not conn: return
        
        try:
            cursor = conn.cursor()
            # CẬP NHẬT DB MỚI: Dùng OrderedQuantity và JOIN Products để lấy UnitPrice
            cursor.execute("""
                SELECT p.ProductName, od.OrderedQuantity, p.UnitPrice, od.SubTotal
                FROM Order_Details od
                JOIN Products p ON od.ProductID = p.ProductID
                WHERE od.OrderID = ?
            """, (self.order_id,))
            rows = cursor.fetchall()
            
            self.tblDanhSachSanPham.setRowCount(0)
            for i, row in enumerate(rows):
                self.tblDanhSachSanPham.insertRow(i)
                self.tblDanhSachSanPham.setItem(i, 0, QtWidgets.QTableWidgetItem(row[0])) # Tên
                self.tblDanhSachSanPham.setItem(i, 1, QtWidgets.QTableWidgetItem(str(row[1]))) # Số lượng
                self.tblDanhSachSanPham.setItem(i, 2, QtWidgets.QTableWidgetItem(f"{row[2]:,.0f} VNĐ")) # Đơn giá
                self.tblDanhSachSanPham.setItem(i, 3, QtWidgets.QTableWidgetItem(f"{row[3]:,.0f} VNĐ")) # Thành tiền
        except Exception as e:
            print(f"Lỗi tải chi tiết SP: {e}")
        finally:
            conn.close()

    def load_payment_info(self):
        """3. Thông tin thanh toán (CẬP NHẬT DB MỚI: Lấy từ bảng Bills)"""
        db = DatabaseManager()
        conn = db.get_connection()
        if not conn: return
        
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT BillID, PaymentDate, PaymentAmount, PaymentMethod
                FROM Bills WHERE OrderID = ?
            """, (self.order_id,))
            bill = cursor.fetchone()
            
            if bill:
                if hasattr(self, 'lblHienThiMaHoaDon'): self.lblHienThiMaHoaDon.setText(str(bill[0]))
                if hasattr(self, 'lblHienThiNgayThanhToan'): 
                    date_str = bill[1].strftime('%d/%m/%Y') if bill[1] else ""
                    self.lblHienThiNgayThanhToan.setText(date_str)
                if hasattr(self, 'lblHienThiTongTienThanhToan'): self.lblHienThiTongTienThanhToan.setText(f"{bill[2]:,.0f} VNĐ")
                if hasattr(self, 'lblHienThiPhuongThucThanhToan'): self.lblHienThiPhuongThucThanhToan.setText(bill[3])
            else:
                if hasattr(self, 'lblHienThiMaHoaDon'): self.lblHienThiMaHoaDon.setText("Chưa có dữ liệu")
                if hasattr(self, 'lblHienThiNgayThanhToan'): self.lblHienThiNgayThanhToan.setText("Chưa có dữ liệu")
                if hasattr(self, 'lblHienThiTongTienThanhToan'): self.lblHienThiTongTienThanhToan.setText("0 VNĐ")
                if hasattr(self, 'lblHienThiPhuongThucThanhToan'): self.lblHienThiPhuongThucThanhToan.setText("Chưa có dữ liệu")
                
        except Exception as e:
            print(f"Lỗi tải hóa đơn: {e}")
        finally:
            conn.close()


# ==========================================
# DIALOG TẠO/SỬA ĐƠN HÀNG (Rút gọn cho module này)
# ==========================================
class EditOrder(QtWidgets.QDialog):
    def __init__(self, data):
        super().__init__()
        ui_file = os.path.join(UI_PATH, "editDonHang.ui")
        if os.path.exists(ui_file):
            uic.loadUi(ui_file, self)
        
        self.order_id = data['id']
        
        if hasattr(self, 'cbTrangThai'):
            self.cbTrangThai.setCurrentText(data['trang_thai'])
            
        if hasattr(self, 'btnLuu'): self.btnLuu.clicked.connect(self.save_data)
        if hasattr(self, 'btnHuy'): self.btnHuy.clicked.connect(self.reject)

    def save_data(self):
        QtWidgets.QMessageBox.information(self, "Thông báo", "Chức năng cập nhật đang được hoàn thiện!")
        self.accept()

# ==========================================
# DIALOG XÓA ĐƠN HÀNG
# ==========================================
class DeleteOrder(QtWidgets.QDialog):
    def __init__(self, data):
        super().__init__()
        uic.loadUi(os.path.join(UI_PATH, "deleteDonHang.ui"), self)
        self.order_id = data['id']
        
        if hasattr(self, 'btnXoa'): self.btnXoa.clicked.connect(self.delete_data)
        if hasattr(self, 'btnHuy'): self.btnHuy.clicked.connect(self.reject)

    def delete_data(self):
        db = DatabaseManager()
        conn = db.get_connection()
        if not conn: return
        
        try:
            cursor = conn.cursor()
            # THỨ TỰ XÓA ĐẢM BẢO KHÔNG VI PHẠM KHÓA NGOẠI:
            # 1. Xóa chi tiết đơn hàng
            cursor.execute("DELETE FROM Order_Details WHERE OrderID = ?", (self.order_id,))
            
            # 2. Xóa hóa đơn thanh toán trong bảng Bills
            cursor.execute("DELETE FROM Bills WHERE OrderID = ?", (self.order_id,))
                
            # 3. Xóa đơn hàng chính
            cursor.execute("DELETE FROM Orders WHERE OrderID = ?", (self.order_id,))
            
            conn.commit()
            QtWidgets.QMessageBox.information(self, "Thành công", f"Đã xóa đơn hàng {self.order_id}!")
            self.accept()
        except Exception as e:
            conn.rollback()
            QtWidgets.QMessageBox.critical(self, "Lỗi", f"Không thể xóa đơn hàng:\n{e}")
        finally:
            conn.close()


# ==========================================
# BỘ QUẢN LÝ ĐƠN HÀNG (CONTROLLER)
# ==========================================
class OrderManager:
    def __init__(self, table_widget, btn_prev=None, btn_next=None, lbl_status=None):
        self.table = table_widget
        self.btn_prev = btn_prev
        self.btn_next = btn_next
        self.lbl_status = lbl_status
        
        # Hàm callback sẽ được gán từ main.py
        self.switch_to_customer_callback = None 
        
        self.init_ui()

    def init_ui(self):
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode.Stretch)
        # Cột Thao tác
        header.setSectionResizeMode(5, QtWidgets.QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(5, 200)

    def load_data(self):
        db = DatabaseManager()
        conn = db.get_connection()
        if not conn: return
        
        try:
            cursor = conn.cursor()
            # Lấy thông tin đơn hàng + Tên, SĐT khách hàng
            cursor.execute("""
                SELECT 
                    o.OrderID, 
                    o.OrderDate, 
                    c.CustomerName, 
                    o.TotalAmount, 
                    o.Status,
                    c.CustomerID,
                    c.CustomerPhone
                FROM Orders o
                JOIN Customers c ON o.CustomerID = c.CustomerID
                ORDER BY o.OrderDate DESC
            """)
            rows = cursor.fetchall()
            
            self.table.setRowCount(0)
            for i, row in enumerate(rows):
                self.table.insertRow(i)
                
                order_id = row[0]
                date_str = row[1].strftime('%d/%m/%Y') if row[1] else ""
                cus_name = row[2]
                total_str = f"{row[3]:,.0f} VNĐ" if row[3] else "0 VNĐ"
                status = row[4]
                
                self.table.setItem(i, 0, QtWidgets.QTableWidgetItem(str(order_id)))
                self.table.setItem(i, 1, QtWidgets.QTableWidgetItem(date_str))
                self.table.setItem(i, 2, QtWidgets.QTableWidgetItem(cus_name))
                self.table.setItem(i, 3, QtWidgets.QTableWidgetItem(total_str))
                
                status_item = QtWidgets.QTableWidgetItem(status)
                if status == "Đã thanh toán": status_item.setForeground(Qt.GlobalColor.darkGreen)
                elif status == "Đã hủy": status_item.setForeground(Qt.GlobalColor.darkRed)
                else: status_item.setForeground(Qt.GlobalColor.red)
                self.table.setItem(i, 4, status_item)
                
                item_data = {
                    "id": order_id, "ngay": date_str, "tien": total_str, "trang_thai": status,
                    "customer_info": {"id": row[5], "ten": cus_name, "sdt": row[6]}
                }
                
                self.add_action_buttons(i, item_data)
                
        except Exception as e:
            print(f"Lỗi load Đơn hàng: {e}")
        finally:
            conn.close()

    def add_action_buttons(self, row, item):
        container = QtWidgets.QWidget()
        layout = QtWidgets.QHBoxLayout(container)
        layout.setContentsMargins(5, 2, 5, 2)
        layout.setSpacing(5)

        btn_view = QtWidgets.QPushButton("Xem")
        btn_edit = QtWidgets.QPushButton("Sửa")
        btn_delete = QtWidgets.QPushButton("Xóa")

        style = "padding: 5px; font-weight: bold; border-radius: 4px; color: white; border: none;"
        btn_view.setStyleSheet(f"background-color: #10b981; {style}")
        btn_edit.setStyleSheet(f"background-color: #f59e0b; {style}")
        btn_delete.setStyleSheet(f"background-color: #ef4444; {style}")
        
        btn_view.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_edit.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_delete.setCursor(Qt.CursorShape.PointingHandCursor)

        btn_view.clicked.connect(lambda: self.open_view(item))
        btn_edit.clicked.connect(lambda: self.open_edit(item))
        btn_delete.clicked.connect(lambda: self.open_delete(item))

        layout.addWidget(btn_view)
        layout.addWidget(btn_edit)
        layout.addWidget(btn_delete)
        self.table.setCellWidget(row, 5, container)

    def open_view(self, item):
        dialog = ViewOrder(item, self.switch_to_customer_callback)
        dialog.exec()

    def open_create(self):
        QtWidgets.QMessageBox.information(None, "Thông báo", "Mở giao diện Tạo đơn hàng!")

    def open_edit(self, item):
        if EditOrder(item).exec(): self.load_data()

    def open_delete(self, item):
        if DeleteOrder(item).exec(): self.load_data()

