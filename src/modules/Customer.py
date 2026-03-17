import os
from PyQt6 import uic, QtWidgets
from PyQt6.QtCore import Qt
from src.database.db_connection import DatabaseManager

# Lấy đường dẫn gốc
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(os.path.dirname(CURRENT_DIR))
UI_PATH = os.path.join(ROOT_DIR, "ui", "modules_ui", "KhachHang")


# ==========================================
# DIALOG THÊM KHÁCH HÀNG
# ==========================================
class AddCustomer(QtWidgets.QDialog):
    def __init__(self):
        super().__init__()
        uic.loadUi(os.path.join(UI_PATH, "addKH.ui"), self)
        
        self.btnLuu.clicked.connect(self.save_data)
        self.btnHuy.clicked.connect(self.reject)

    def save_data(self):
        ten = self.txtTenKH.text().strip()
        sdt = self.txtSDTKH.text().strip()
        
        if not ten or not sdt:
            QtWidgets.QMessageBox.warning(self, "Lỗi", "Vui lòng nhập đầy đủ Tên và Số điện thoại!")
            return
            
        db = DatabaseManager()
        conn = db.get_connection()
        if not conn: return
        
        try:
            cursor = conn.cursor()
            
            # Kiểm tra SĐT có bị trùng không (Ràng buộc UNIQUE trong DB)
            cursor.execute("SELECT COUNT(*) FROM Customers WHERE CustomerPhone = ?", (sdt,))
            if cursor.fetchone()[0] > 0:
                QtWidgets.QMessageBox.warning(self, "Từ chối", "Số điện thoại này đã tồn tại trong hệ thống!")
                return
            
            # Tạo Mã KH tự động tăng (ID kiểu INT)
            cursor.execute("SELECT ISNULL(MAX(CustomerID), 0) FROM Customers")
            new_cus_id = cursor.fetchone()[0] + 1
            
            # Thêm mới KH (Điểm LoyaltyPoints mặc định bằng 0, Giới tính để NULL vì form không có)
            cursor.execute("""
                INSERT INTO Customers (CustomerID, CustomerName, CustomerPhone, LoyaltyPoints)
                VALUES (?, ?, ?, 0)
            """, (new_cus_id, ten, sdt))
            
            conn.commit()
            QtWidgets.QMessageBox.information(self, "Thành công", "Đã thêm khách hàng mới thành công!")
            self.accept()
            
        except Exception as e:
            conn.rollback()
            QtWidgets.QMessageBox.critical(self, "Lỗi hệ thống", f"Không thể thêm KH:\n{str(e)}")
        finally:
            conn.close()


# ==========================================
# DIALOG SỬA KHÁCH HÀNG
# ==========================================
class EditCustomer(QtWidgets.QDialog):
    def __init__(self, data):
        super().__init__()
        uic.loadUi(os.path.join(UI_PATH, "editKH.ui"), self)
        
        self.customer_id = data['id']
        
        # Điền dữ liệu cũ lên giao diện
        if hasattr(self, 'txtReadOnlyMaKH'):
            self.txtReadOnlyMaKH.setText(str(data['id']))
        self.txtTenKH.setText(data['ten'])
        self.txtSDTKH.setText(data['sdt'])
            
        self.btnLuu.clicked.connect(self.update_data)
        self.btnHuy.clicked.connect(self.reject)

    def update_data(self):
        ten = self.txtTenKH.text().strip()
        sdt = self.txtSDTKH.text().strip()
        
        if not ten or not sdt:
            QtWidgets.QMessageBox.warning(self, "Lỗi", "Vui lòng nhập Tên và Số điện thoại!")
            return
            
        db = DatabaseManager()
        conn = db.get_connection()
        if not conn: return
        
        try:
            cursor = conn.cursor()
            
            # Kiểm tra SĐT bị trùng (Ngoại trừ chính khách hàng này)
            cursor.execute("SELECT COUNT(*) FROM Customers WHERE CustomerPhone = ? AND CustomerID != ?", (sdt, self.customer_id))
            if cursor.fetchone()[0] > 0:
                QtWidgets.QMessageBox.warning(self, "Từ chối", "Số điện thoại này đã được khách hàng khác sử dụng!")
                return
                
            cursor.execute("""
                UPDATE Customers 
                SET CustomerName = ?, CustomerPhone = ? 
                WHERE CustomerID = ?
            """, (ten, sdt, self.customer_id))
            
            conn.commit()
            QtWidgets.QMessageBox.information(self, "Thành công", "Đã cập nhật thông tin khách hàng!")
            self.accept()
        except Exception as e:
            conn.rollback()
            QtWidgets.QMessageBox.critical(self, "Lỗi", f"Lỗi hệ thống:\n{str(e)}")
        finally:
            conn.close()


# ==========================================
# DIALOG XÓA KHÁCH HÀNG
# ==========================================
class DeleteCustomer(QtWidgets.QDialog):
    def __init__(self, data):
        super().__init__()
        uic.loadUi(os.path.join(UI_PATH, "deleteKH.ui"), self)
        
        self.customer_id = data['id']
        self.customer_name = data['ten']
            
        self.btnXoa.clicked.connect(self.delete_data)
        self.btnHuy.clicked.connect(self.reject)

    def delete_data(self):
        db = DatabaseManager()
        conn = db.get_connection()
        if not conn: return
        
        try:
            cursor = conn.cursor()
            
            # KIỂM TRA RÀNG BUỘC: Khách hàng này có Đơn hàng chưa?
            cursor.execute("SELECT COUNT(*) FROM Orders WHERE CustomerID = ?", (self.customer_id,))
            if cursor.fetchone()[0] > 0:
                QtWidgets.QMessageBox.warning(self, "Từ chối xóa", 
                    f"Không thể xóa '{self.customer_name}' vì khách hàng này đã có lịch sử Đơn hàng!")
                return
            
            # Xóa khách hàng
            cursor.execute("DELETE FROM Customers WHERE CustomerID = ?", (self.customer_id,))
            conn.commit()
            
            QtWidgets.QMessageBox.information(self, "Thành công", "Đã xóa khách hàng khỏi hệ thống!")
            self.accept()
        except Exception as e:
            conn.rollback()
            QtWidgets.QMessageBox.critical(self, "Lỗi", f"Lỗi hệ thống:\n{str(e)}")
        finally:
            conn.close()


# ==========================================
# DIALOG LỊCH SỬ MUA HÀNG (MỚI)
# ==========================================
class ViewHistoryCustomer(QtWidgets.QDialog):
    def __init__(self, data):
        super().__init__()
        uic.loadUi(os.path.join(UI_PATH, "viewLichSuMuaHangCuaKhach.ui"), self)
        
        # Load thông tin tĩnh
        self.lblHienThiMaKH.setText(str(data['id']))
        self.lblHienThiTenKH.setText(data['ten'])
        self.lblHienThiSDT.setText(data['sdt'])
        
        # Cấu hình bảng lịch sử
        self.tblDanhSachMuaHang.verticalHeader().setVisible(False)
        self.tblDanhSachMuaHang.setEditTriggers(QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tblDanhSachMuaHang.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        header = self.tblDanhSachMuaHang.horizontalHeader()
        header.setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode.Stretch)
        
        # Tải dữ liệu lịch sử từ DB
        self.load_history(data['id'])
        
    def load_history(self, customer_id):
        db = DatabaseManager()
        conn = db.get_connection()
        if not conn: return
        
        try:
            cursor = conn.cursor()
            # Lấy các đơn hàng của khách hàng này
            cursor.execute("""
                SELECT OrderID, OrderDate, TotalAmount, Status 
                FROM Orders 
                WHERE CustomerID = ?
                ORDER BY OrderDate DESC
            """, (customer_id,))
            rows = cursor.fetchall()
            
            self.tblDanhSachMuaHang.setRowCount(0)
            for row_idx, row in enumerate(rows):
                self.tblDanhSachMuaHang.insertRow(row_idx)
                
                # Mã đơn
                self.tblDanhSachMuaHang.setItem(row_idx, 0, QtWidgets.QTableWidgetItem(str(row[0])))
                # Ngày mua
                date_str = row[1].strftime('%d/%m/%Y') if row[1] else ""
                self.tblDanhSachMuaHang.setItem(row_idx, 1, QtWidgets.QTableWidgetItem(date_str))
                # Tổng tiền
                money_str = f"{row[2]:,.0f} VNĐ" if row[2] else "0 VNĐ"
                self.tblDanhSachMuaHang.setItem(row_idx, 2, QtWidgets.QTableWidgetItem(money_str))
                
                # Trạng thái (để thay cho cột Thao tác tạm thời, hoặc làm 1 nút Xem chi tiết đơn)
                status_item = QtWidgets.QTableWidgetItem(row[3])
                if row[3] == "Đã thanh toán":
                    status_item.setForeground(Qt.GlobalColor.darkGreen)
                else:
                    status_item.setForeground(Qt.GlobalColor.darkRed)
                self.tblDanhSachMuaHang.setItem(row_idx, 3, status_item)
                
        except Exception as e:
            print(f"Lỗi tải lịch sử: {e}")
        finally:
            conn.close()


# ==========================================
# BỘ QUẢN LÝ KHÁCH HÀNG (CONTROLLER)
# ==========================================
class CustomerManager:
    def __init__(self, table_widget, txt_search=None, btn_search=None):
        self.table = table_widget
        self.txt_search = txt_search
        
        self.init_ui_style()
        
        # Kết nối sự kiện tìm kiếm nếu có truyền vào
        if btn_search and txt_search:
            btn_search.clicked.connect(self.load_data)
            txt_search.returnPressed.connect(self.load_data)

    def init_ui_style(self):
        """Cấu hình bảng với 5 cột chuẩn: Mã, Tên, SĐT, Tổng chi tiêu, Thao tác"""
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode.Stretch)
        
        # Cột cuối (Thao tác - index 4) cần không gian rộng hơn để chứa 3 nút
        header.setSectionResizeMode(4, QtWidgets.QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(4, 200) 

    def load_data(self):
        """Nạp danh sách khách hàng và tự động JOIN để tính TỔNG CHI TIÊU"""
        db = DatabaseManager()
        conn = db.get_connection()
        if not conn: return
        
        search_kw = ""
        if self.txt_search:
            search_kw = self.txt_search.text().strip()
            
        try:
            cursor = conn.cursor()
            
            # Truy vấn lấy Khách hàng + Tổng tiền đã mua từ bảng Orders (Chỉ tính đơn Đã thanh toán)
            query = """
                SELECT 
                    c.CustomerID, 
                    c.CustomerName, 
                    c.CustomerPhone, 
                    ISNULL(SUM(o.TotalAmount), 0) AS TongChiTieu
                FROM Customers c
                LEFT JOIN Orders o ON c.CustomerID = o.CustomerID AND o.Status = N'Đã thanh toán'
            """
            
            params = ()
            if search_kw:
                query += " WHERE c.CustomerPhone LIKE ? OR c.CustomerName LIKE ?"
                params = (f"%{search_kw}%", f"%{search_kw}%")
                
            query += " GROUP BY c.CustomerID, c.CustomerName, c.CustomerPhone ORDER BY c.CustomerID DESC"
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            self.table.setRowCount(0)
            
            for row_idx, row in enumerate(rows):
                self.table.insertRow(row_idx)
                
                # Nạp dữ liệu
                self.table.setItem(row_idx, 0, QtWidgets.QTableWidgetItem(str(row[0])))
                self.table.setItem(row_idx, 1, QtWidgets.QTableWidgetItem(row[1]))
                self.table.setItem(row_idx, 2, QtWidgets.QTableWidgetItem(row[2]))
                
                # Định dạng tiền tệ
                money_str = f"{row[3]:,.0f} VNĐ"
                self.table.setItem(row_idx, 3, QtWidgets.QTableWidgetItem(money_str))
                
                # Thông tin gửi sang Dialog
                item_dict = {
                    "id": row[0], 
                    "ten": row[1], 
                    "sdt": row[2]
                }
                
                self.add_action_buttons(row_idx, item_dict)
                
        except Exception as e:
            print(f"Lỗi load KH: {e}")
        finally:
            conn.close()

    def add_action_buttons(self, row, item):
        """Thêm 3 nút: Lịch sử, Sửa, Xóa vào cột cuối cùng"""
        container = QtWidgets.QWidget()
        layout = QtWidgets.QHBoxLayout(container)
        layout.setContentsMargins(5, 2, 5, 2)
        layout.setSpacing(5)

        btn_history = QtWidgets.QPushButton("Lịch sử")
        btn_edit = QtWidgets.QPushButton("Sửa")
        btn_delete = QtWidgets.QPushButton("Xóa")

        style = "padding: 5px; font-weight: bold; border-radius: 4px; color: white;"
        btn_history.setStyleSheet(f"background-color: #10b981; {style}") # Màu xanh lá
        btn_edit.setStyleSheet(f"background-color: #f59e0b; {style}")    # Màu cam
        btn_delete.setStyleSheet(f"background-color: #ef4444; {style}")  # Màu đỏ
        
        btn_history.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_edit.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_delete.setCursor(Qt.CursorShape.PointingHandCursor)

        # Gán sự kiện
        btn_history.clicked.connect(lambda: self.open_history(item))
        btn_edit.clicked.connect(lambda: self.open_edit(item))
        btn_delete.clicked.connect(lambda: self.open_delete(item))

        layout.addWidget(btn_history)
        layout.addWidget(btn_edit)
        layout.addWidget(btn_delete)
        
        # Cột Thao tác là index 4
        self.table.setCellWidget(row, 4, container)

    def open_history(self, item):
        ViewHistoryCustomer(item).exec()

    def open_add(self):
        if AddCustomer().exec(): 
            self.load_data()

    def open_edit(self, item):
        if EditCustomer(item).exec(): 
            self.load_data()

    def open_delete(self, item):
        if DeleteCustomer(item).exec(): 
            self.load_data()