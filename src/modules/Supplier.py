import os
from PyQt6 import uic, QtWidgets
from PyQt6.QtCore import Qt
from src.database.db_connection import DatabaseManager

# Lấy đường dẫn gốc
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(os.path.dirname(CURRENT_DIR))
UI_PATH = os.path.join(ROOT_DIR, "ui", "modules_ui", "NhaCungCap")


# ==========================================
# DIALOG THÊM NHÀ CUNG CẤP
# ==========================================
class AddSupplier(QtWidgets.QDialog):
    def __init__(self):
        super().__init__()
        uic.loadUi(os.path.join(UI_PATH, "addNCC.ui"), self)
        
        if hasattr(self, 'btnLuu'): self.btnLuu.clicked.connect(self.save_data)
        if hasattr(self, 'btnHuy'): self.btnHuy.clicked.connect(self.reject)

    def save_data(self):
        ten = self.txtTenNCC.text().strip()
        sdt = self.txtSDT.text().strip() if hasattr(self, 'txtSDT') else self.txtSDTNCC.text().strip()
        email = self.txtEmail.text().strip()
        dia_chi = self.txtDiaChi.text().strip()
        
        if not ten or not sdt:
            QtWidgets.QMessageBox.warning(self, "Lỗi", "Vui lòng nhập Tên và Số điện thoại!")
            return
            
        db = DatabaseManager()
        conn = db.get_connection()
        if not conn: return
        
        try:
            cursor = conn.cursor()
            
            # Kiểm tra trùng SĐT
            cursor.execute("SELECT COUNT(*) FROM Suppliers WHERE SupplierPhone = ?", (sdt,))
            if cursor.fetchone()[0] > 0:
                QtWidgets.QMessageBox.warning(self, "Từ chối", "Số điện thoại này đã tồn tại!")
                return
            
            # Tự động tăng ID
            cursor.execute("SELECT ISNULL(MAX(SupplierID), 0) FROM Suppliers")
            new_id = cursor.fetchone()[0] + 1
            
            cursor.execute("""
                INSERT INTO Suppliers (SupplierID, SupplierName, SupplierPhone, SupplierEmail, SupplierAddress)
                VALUES (?, ?, ?, ?, ?)
            """, (new_id, ten, sdt, email, dia_chi))
            
            conn.commit()
            QtWidgets.QMessageBox.information(self, "Thành công", "Đã thêm Nhà cung cấp mới!")
            self.accept()
        except Exception as e:
            conn.rollback()
            QtWidgets.QMessageBox.critical(self, "Lỗi", f"Lỗi hệ thống:\n{e}")
        finally:
            conn.close()


# ==========================================
# DIALOG SỬA NHÀ CUNG CẤP
# ==========================================
class EditSupplier(QtWidgets.QDialog):
    def __init__(self, data):
        super().__init__()
        uic.loadUi(os.path.join(UI_PATH, "editNCC.ui"), self)
        
        self.supplier_id = data['id']
        self.load_old_data(data)
        
        if hasattr(self, 'btnLuu'): self.btnLuu.clicked.connect(self.update_data)
        if hasattr(self, 'btnHuy'): self.btnHuy.clicked.connect(self.reject)

    def load_old_data(self, data):
        if hasattr(self, 'txtReadOnlyMaNCC'): self.txtReadOnlyMaNCC.setText(str(data['id']))
        self.txtTenNCC.setText(data['ten'])
        
        if hasattr(self, 'txtSDT'): self.txtSDT.setText(data['sdt'])
        elif hasattr(self, 'txtSDTNCC'): self.txtSDTNCC.setText(data['sdt'])
            
        self.txtEmail.setText(data['email'])
        self.txtDiaChi.setText(data['dia_chi'])

    def update_data(self):
        ten = self.txtTenNCC.text().strip()
        sdt = self.txtSDT.text().strip() if hasattr(self, 'txtSDT') else self.txtSDTNCC.text().strip()
        email = self.txtEmail.text().strip()
        dia_chi = self.txtDiaChi.text().strip()
        
        if not ten or not sdt:
            QtWidgets.QMessageBox.warning(self, "Lỗi", "Vui lòng nhập Tên và Số điện thoại!")
            return
            
        db = DatabaseManager()
        conn = db.get_connection()
        if not conn: return
        
        try:
            cursor = conn.cursor()
            
            # Kiểm tra trùng SĐT (trừ chính nó)
            cursor.execute("SELECT COUNT(*) FROM Suppliers WHERE SupplierPhone = ? AND SupplierID != ?", (sdt, self.supplier_id))
            if cursor.fetchone()[0] > 0:
                QtWidgets.QMessageBox.warning(self, "Từ chối", "Số điện thoại này đã được sử dụng!")
                return
                
            cursor.execute("""
                UPDATE Suppliers 
                SET SupplierName=?, SupplierPhone=?, SupplierEmail=?, SupplierAddress=?
                WHERE SupplierID=?
            """, (ten, sdt, email, dia_chi, self.supplier_id))
            
            conn.commit()
            QtWidgets.QMessageBox.information(self, "Thành công", "Đã cập nhật thông tin!")
            self.accept()
        except Exception as e:
            conn.rollback()
            QtWidgets.QMessageBox.critical(self, "Lỗi", f"Lỗi hệ thống:\n{e}")
        finally:
            conn.close()


# ==========================================
# DIALOG XÓA NHÀ CUNG CẤP
# ==========================================
class DeleteSupplier(QtWidgets.QDialog):
    def __init__(self, data):
        super().__init__()
        uic.loadUi(os.path.join(UI_PATH, "deleteNCC.ui"), self)
        
        self.supplier_id = data['id']
        self.supplier_name = data['ten']
        
        if hasattr(self, 'btnXoa'): self.btnXoa.clicked.connect(self.delete_data)
        if hasattr(self, 'btnHuy'): self.btnHuy.clicked.connect(self.reject)

    def delete_data(self):
        db = DatabaseManager()
        conn = db.get_connection()
        if not conn: return
        
        try:
            cursor = conn.cursor()
            
            # KIỂM TRA RÀNG BUỘC
            cursor.execute("SELECT COUNT(*) FROM Products WHERE SupplierID = ?", (self.supplier_id,))
            if cursor.fetchone()[0] > 0:
                QtWidgets.QMessageBox.warning(self, "Từ chối", f"'{self.supplier_name}' đang cung cấp sản phẩm. Không thể xóa!")
                return
                
            cursor.execute("SELECT COUNT(*) FROM Purchase_Orders WHERE SupplierID = ?", (self.supplier_id,))
            if cursor.fetchone()[0] > 0:
                QtWidgets.QMessageBox.warning(self, "Từ chối", f"'{self.supplier_name}' đã có lịch sử đơn nhập hàng. Không thể xóa!")
                return

            # Xóa
            cursor.execute("DELETE FROM Suppliers WHERE SupplierID = ?", (self.supplier_id,))
            conn.commit()
            QtWidgets.QMessageBox.information(self, "Thành công", "Đã xóa nhà cung cấp!")
            self.accept()
        except Exception as e:
            conn.rollback()
            QtWidgets.QMessageBox.critical(self, "Lỗi", f"Lỗi hệ thống:\n{e}")
        finally:
            conn.close()


# ==========================================
# DIALOG CHI TIẾT NHÀ CUNG CẤP
# ==========================================
class ViewSupplier(QtWidgets.QDialog):
    def __init__(self, data, open_purchase_order_callback=None, edit_callback=None):
        super().__init__()
        uic.loadUi(os.path.join(UI_PATH, "viewNCC.ui"), self)
        
        self.data = data
        self.open_purchase_order_callback = open_purchase_order_callback
        self.edit_callback = edit_callback
        self.latest_po_id = None # Lưu ID đơn nhập mới nhất
        
        self.load_contact_info()
        self.load_products()
        self.load_latest_purchase_order()
        
        if hasattr(self, 'btnSua'): 
            self.btnSua.clicked.connect(self.on_edit_clicked)
        if hasattr(self, 'btnDong'): 
            self.btnDong.clicked.connect(self.close)
        if hasattr(self, 'btnXemDonNhap'): 
            self.btnXemDonNhap.clicked.connect(self.on_view_po_clicked)

    def load_contact_info(self):
        if hasattr(self, 'lblHienThiMaNCC'): self.lblHienThiMaNCC.setText(str(self.data['id']))
        if hasattr(self, 'lblHienThiTenNCC'): self.lblHienThiTenNCC.setText(self.data['ten'])
        if hasattr(self, 'lblHienThiSDT'): self.lblHienThiSDT.setText(self.data['sdt'])
        if hasattr(self, 'lblHienThiEmail'): self.lblHienThiEmail.setText(self.data['email'])
        if hasattr(self, 'lblHienThiDiaChi'): self.lblHienThiDiaChi.setText(self.data['dia_chi'])

    def load_products(self):
        """Tải danh sách sản phẩm do NCC này cung cấp"""
        tbl = getattr(self, 'tblDanhSachSanPham', None)
        if not tbl: return
        
        tbl.verticalHeader().setVisible(False)
        tbl.setEditTriggers(QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)
        tbl.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode.Stretch)
        
        db = DatabaseManager()
        conn = db.get_connection()
        if not conn: return
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT ProductID, ProductName, UnitsInStock, UnitPrice
                FROM Products WHERE SupplierID = ?
            """, (self.data['id'],))
            
            rows = cursor.fetchall()
            tbl.setRowCount(0)
            for i, row in enumerate(rows):
                tbl.insertRow(i)
                tbl.setItem(i, 0, QtWidgets.QTableWidgetItem(str(row[0])))
                tbl.setItem(i, 1, QtWidgets.QTableWidgetItem(row[1]))
                tbl.setItem(i, 2, QtWidgets.QTableWidgetItem(str(row[2])))
                tbl.setItem(i, 3, QtWidgets.QTableWidgetItem(f"{row[3]:,.0f} VNĐ"))
        finally:
            conn.close()

    def load_latest_purchase_order(self):
        """Lấy đơn nhập hàng MỚI NHẤT để hiển thị lên panel"""
        db = DatabaseManager()
        conn = db.get_connection()
        if not conn: return
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT TOP 1 PurchaseOrderID, PurchasedDate, TotalAmount
                FROM Purchase_Orders
                WHERE SupplierID = ?
                ORDER BY PurchasedDate DESC
            """, (self.data['id'],))
            
            po = cursor.fetchone()
            if po:
                self.latest_po_id = po[0]
                if hasattr(self, 'lblHienThiMaDonNhap'): self.lblHienThiMaDonNhap.setText(str(po[0]))
                if hasattr(self, 'lblHienThiNgayNhap'): 
                    date_str = po[1].strftime('%d/%m/%Y') if po[1] else ""
                    self.lblHienThiNgayNhap.setText(date_str)
                if hasattr(self, 'lblHienThiTongTien'): self.lblHienThiTongTien.setText(f"{po[2]:,.0f} VNĐ")
                if hasattr(self, 'btnXemDonNhap'): self.btnXemDonNhap.setEnabled(True)
            else:
                if hasattr(self, 'lblHienThiMaDonNhap'): self.lblHienThiMaDonNhap.setText("Chưa có")
                if hasattr(self, 'lblHienThiNgayNhap'): self.lblHienThiNgayNhap.setText("N/A")
                if hasattr(self, 'lblHienThiTongTien'): self.lblHienThiTongTien.setText("0 VNĐ")
                if hasattr(self, 'btnXemDonNhap'): self.btnXemDonNhap.setEnabled(False) # Khóa nút nếu ko có đơn
        finally:
            conn.close()

    def on_view_po_clicked(self):
        if self.open_purchase_order_callback and self.latest_po_id:
            self.close() # Đóng popup NCC
            # Gọi callback mở chi tiết Đơn Nhập Hàng
            self.open_purchase_order_callback(self.latest_po_id)
            
    def on_edit_clicked(self):
        self.close()
        if self.edit_callback:
            self.edit_callback(self.data)


# ==========================================
# BỘ QUẢN LÝ NHÀ CUNG CẤP (CONTROLLER)
# ==========================================
class SupplierManager:
    def __init__(self, table_widget, txt_search=None, btn_search=None):
        self.table = table_widget
        self.txt_search = txt_search
        
        # Hàm callback từ main.py
        self.open_purchase_order_callback = None
        
        self.init_ui()
        
        if btn_search and txt_search:
            btn_search.clicked.connect(self.load_data)
            txt_search.returnPressed.connect(self.load_data)

    def init_ui(self):
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode.Stretch)
        # Cột thao tác (Cột số 6 - index 5)
        header.setSectionResizeMode(5, QtWidgets.QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(5, 200)

    def load_data(self):
        db = DatabaseManager()
        conn = db.get_connection()
        if not conn: return
        
        search_kw = ""
        if self.txt_search:
            search_kw = self.txt_search.text().strip()
            
        try:
            cursor = conn.cursor()
            # JOIN đếm số sản phẩm
            query = """
                SELECT 
                    s.SupplierID, s.SupplierName, s.SupplierPhone, s.SupplierEmail, s.SupplierAddress,
                    COUNT(p.ProductID) AS ProductCount
                FROM Suppliers s
                LEFT JOIN Products p ON s.SupplierID = p.SupplierID
            """
            
            params = ()
            if search_kw:
                query += " WHERE s.SupplierName LIKE ? OR s.SupplierPhone LIKE ?"
                params = (f"%{search_kw}%", f"%{search_kw}%")
                
            query += " GROUP BY s.SupplierID, s.SupplierName, s.SupplierPhone, s.SupplierEmail, s.SupplierAddress ORDER BY s.SupplierID DESC"
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            self.table.setRowCount(0)
            for i, row in enumerate(rows):
                self.table.insertRow(i)
                self.table.setItem(i, 0, QtWidgets.QTableWidgetItem(str(row[0])))
                self.table.setItem(i, 1, QtWidgets.QTableWidgetItem(row[1]))
                self.table.setItem(i, 2, QtWidgets.QTableWidgetItem(row[2]))
                self.table.setItem(i, 3, QtWidgets.QTableWidgetItem(row[3]))
                self.table.setItem(i, 4, QtWidgets.QTableWidgetItem(row[4]))
                
                # Số SP hiển thị căn giữa
                count_item = QtWidgets.QTableWidgetItem(str(row[5]))
                count_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table.setItem(i, 5, count_item)
                
                item_data = {
                    "id": row[0], "ten": row[1], "sdt": row[2], "email": row[3], "dia_chi": row[4]
                }
                self.add_action_buttons(i, item_data)
                
        except Exception as e:
            print(f"Lỗi load NCC: {e}")
        finally:
            conn.close()

    def add_action_buttons(self, row, item):
        # Chèn widget container vào cột thứ 7 (index 6) nếu bạn có 6 cột dữ liệu, 
        # Cấu trúc: Mã (0), Tên (1), SĐT (2), Email (3), Địa chỉ (4), Số SP (5), Thao tác (6)
        # Sửa lại index cột nếu bảng của bạn khác. Ở đây mặc định là index 6
        if self.table.columnCount() > 6:
            action_col = 6
        else:
            action_col = 5 # Đè lên cột cuối nếu thiết kế UI của bạn chỉ có 6 cột tổng cộng

        container = QtWidgets.QWidget()
        layout = QtWidgets.QHBoxLayout(container)
        layout.setContentsMargins(5, 2, 5, 2)
        layout.setSpacing(5)

        btn_view = QtWidgets.QPushButton("Xem")
        btn_edit = QtWidgets.QPushButton("Sửa")
        btn_delete = QtWidgets.QPushButton("Xóa")

        style = "padding: 5px; font-weight: bold; border-radius: 4px; color: white; border: none;"
        btn_view.setStyleSheet(f"background-color: #10b981; {style}")
        btn_edit.setStyleSheet(f"background-color: #3b82f6; {style}")
        btn_delete.setStyleSheet(f"background-color: #ef4444; {style}")

        btn_view.clicked.connect(lambda: self.open_view(item))
        btn_edit.clicked.connect(lambda: self.open_edit(item))
        btn_delete.clicked.connect(lambda: self.open_delete(item))

        layout.addWidget(btn_view)
        layout.addWidget(btn_edit)
        layout.addWidget(btn_delete)
        self.table.setCellWidget(row, action_col, container)

    def open_view(self, item):
        # Truyền callback gọi chi tiết Đơn nhập hàng và gọi form Edit
        dialog = ViewSupplier(item, self.open_purchase_order_callback, self.open_edit)
        dialog.exec()

    def open_add(self):
        if AddSupplier().exec(): self.load_data()

    def open_edit(self, item):
        if EditSupplier(item).exec(): self.load_data()

    def open_delete(self, item):
        if DeleteSupplier(item).exec(): self.load_data()
