import os
from PyQt6 import uic, QtWidgets, QtCore
from src.database.db_connection import DatabaseManager

# Thiết lập đường dẫn gốc
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(os.path.dirname(CURRENT_DIR))
UI_PATH = os.path.join(ROOT_DIR, "ui")

# CÁC DIALOG CHỨC NĂNG
class AddCustomer(QtWidgets.QDialog):
    def __init__(self):
        super().__init__()
        uic.loadUi(os.path.join(UI_PATH, "addKH.ui"), self)
        
        self.btnLuu.clicked.connect(self.save_data)
        self.btnHuy.clicked.connect(self.reject)

    def save_data(self):
        ten = self.txtTenKH.text().strip()
        sdt = self.txtSDTKH.text().strip()
        gt = self.cbGioiTinhKH.currentText().strip()
        
        if not ten or not sdt:
            QtWidgets.QMessageBox.warning(self, "Lỗi", "Vui lòng nhập Tên và Số điện thoại!")
            return
            
        db = DatabaseManager()
        conn = db.get_connection()
        if not conn: return
        
        try:
            cursor = conn.cursor()
            
            # KIỂM TRA TRÙNG SĐT: SĐT là UNIQUE trong Database
            cursor.execute("SELECT COUNT(*) FROM CUSTOMERS WHERE CUSTOMER_PHONE = ?", (sdt,))
            if cursor.fetchone()[0] > 0:
                QtWidgets.QMessageBox.warning(self, "Lỗi", "Số điện thoại này đã được đăng ký cho khách hàng khác!")
                return
            
            # 1. TẠO TÀI KHOẢN NGẦM TRONG BẢNG ACCOUNTS
            cursor.execute("SELECT MAX(ACCOUNT_ID) FROM ACCOUNTS")
            last_acc = cursor.fetchone()[0]
            new_acc_num = int(last_acc.replace("ACC", "")) + 1 if last_acc else 1
            new_acc_id = f"ACC{new_acc_num:02d}"
            
            # Dùng SĐT làm Username, Mật khẩu mặc định là 123456
            cursor.execute("""
                INSERT INTO ACCOUNTS (ACCOUNT_ID, USERNAME, PASSWORD, ROLE, ACCOUNT_STATUS)
                VALUES (?, ?, ?, ?, ?)
            """, (new_acc_id, sdt, "123456", "Customer", "Active"))
            
            # TẠO KHÁCH HÀNG MỚI TRONG BẢNG CUSTOMERS
            cursor.execute("SELECT MAX(CUSTOMER_ID) FROM CUSTOMERS")
            last_cus = cursor.fetchone()[0]
            new_cus_num = int(last_cus.replace("CUS", "")) + 1 if last_cus else 1
            new_cus_id = f"CUS{new_cus_num:02d}"
            
            # Sinh Email ảo vì database yêu cầu NOT NULL
            email_ao = f"{sdt}@khachhang.com"
            
            cursor.execute("""
                INSERT INTO CUSTOMERS (CUSTOMER_ID, CUSTOMER_NAME, CUSTOMER_GENDER, CUSTOMER_PHONE, CUSTOMER_EMAIL, ACCOUNT_ID)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (new_cus_id, ten, gt, sdt, email_ao, new_acc_id))
            
            conn.commit()
            QtWidgets.QMessageBox.information(self, "Thành công", "Đã thêm khách hàng mới (Kèm tài khoản mặc định)!")
            self.accept()
            
        except Exception as e:
            conn.rollback()
            QtWidgets.QMessageBox.critical(self, "Lỗi hệ thống", f"Không thể thêm KH: {str(e)}")
        finally:
            conn.close()


class EditCustomer(QtWidgets.QDialog):
    def __init__(self, data):
        super().__init__()
        uic.loadUi(os.path.join(UI_PATH, "editKH.ui"), self)
        
        self.customer_id = data['id']
        
        # Điền dữ liệu cũ lên giao diện
        self.txtTenKH.setText(data['ten'])
        self.txtSDTKH.setText(data['sdt'])
        
        # Tự động chọn đúng Giới tính
        index = self.cbGioiTinhKH.findText(data['gt'])
        if index >= 0:
            self.cbGioiTinhKH.setCurrentIndex(index)
            
        self.btnLuu.clicked.connect(self.update_data)
        self.btnHuy.clicked.connect(self.reject)

    def update_data(self):
        ten = self.txtTenKH.text().strip()
        sdt = self.txtSDTKH.text().strip()
        gt = self.cbGioiTinhKH.currentText().strip()
        
        if not ten or not sdt:
            QtWidgets.QMessageBox.warning(self, "Lỗi", "Vui lòng nhập Tên và Số điện thoại!")
            return
            
        db = DatabaseManager()
        conn = db.get_connection()
        if not conn: return
        
        try:
            cursor = conn.cursor()
            # Chỉ cập nhật 3 trường thông tin hiển thị trên UI
            cursor.execute("""
                UPDATE CUSTOMERS 
                SET CUSTOMER_NAME = ?, CUSTOMER_PHONE = ?, CUSTOMER_GENDER = ? 
                WHERE CUSTOMER_ID = ?
            """, (ten, sdt, gt, self.customer_id))
            
            conn.commit()
            QtWidgets.QMessageBox.information(self, "Thành công", "Cập nhật thành công!")
            self.accept()
        except Exception as e:
            conn.rollback()
            QtWidgets.QMessageBox.critical(self, "Lỗi", f"Lỗi hệ thống: {str(e)}")
        finally:
            conn.close()


class DeleteCustomer(QtWidgets.QDialog):
    def __init__(self, data):
        super().__init__()
        uic.loadUi(os.path.join(UI_PATH, "deleteKH.ui"), self)
        
        self.customer_id = data['id']
        self.customer_name = data['ten']
        
        # Nếu file ui có label hiển thị thông báo
        if hasattr(self, 'lblThongBao'):
            self.lblThongBao.setText(f"Bạn có chắc muốn xóa khách hàng:\n{self.customer_name}?")
            
        self.btnXoa.clicked.connect(self.delete_data)
        self.btnHuy.clicked.connect(self.reject)

    def delete_data(self):
        db = DatabaseManager()
        conn = db.get_connection()
        if not conn: return
        
        try:
            cursor = conn.cursor()
            
            # KIỂM TRA RÀNG BUỘC: Khách hàng này đã từng mua hàng chưa?
            cursor.execute("SELECT COUNT(*) FROM ORDERS WHERE CUSTOMER_ID = ?", (self.customer_id,))
            if cursor.fetchone()[0] > 0:
                QtWidgets.QMessageBox.warning(self, "Từ chối xóa", 
                    f"Không thể xóa '{self.customer_name}' vì khách hàng này đã có lịch sử Đơn hàng trong hệ thống!")
                return
            
            # Lấy Account_ID để xóa luôn tài khoản đi kèm
            cursor.execute("SELECT ACCOUNT_ID FROM CUSTOMERS WHERE CUSTOMER_ID = ?", (self.customer_id,))
            acc_id = cursor.fetchone()[0]
            
            # Xóa khách hàng trước, xóa tài khoản sau (Ràng buộc FK)
            cursor.execute("DELETE FROM CUSTOMERS WHERE CUSTOMER_ID = ?", (self.customer_id,))
            cursor.execute("DELETE FROM ACCOUNTS WHERE ACCOUNT_ID = ?", (acc_id,))
            
            conn.commit()
            QtWidgets.QMessageBox.information(self, "Thành công", "Đã xóa khách hàng và tài khoản liên kết!")
            self.accept()
            
        except Exception as e:
            conn.rollback()
            QtWidgets.QMessageBox.critical(self, "Lỗi", f"Lỗi hệ thống: {str(e)}")
        finally:
            conn.close()


# BỘ QUẢN LÝ KHÁCH HÀNG 
class CustomerManager:
    def __init__(self, table_widget):
        self.table = table_widget
        self.init_ui_style()

    def init_ui_style(self):
        """Cấu hình bảng chuyên nghiệp phù hợp với cấu trúc 7 cột mới"""
        self.table.verticalHeader().setVisible(False)
        header = self.table.horizontalHeader()
        
        # Cấu hình tự động co giãn cho các cột thông tin
        header.setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode.Stretch)
        
        # Cột 0 (Mã KH) và Cột 1 (Mã tài khoản) co theo nội dung
        header.setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
        
        # Cột 6 (Thao tác) đặt độ rộng cố định
        header.setSectionResizeMode(6, QtWidgets.QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(6, 160) 

        self.table.setStyleSheet("""
            QTableWidget { gridline-color: #e5e7eb; selection-background-color: #dbeafe; selection-color: #1e40af; alternate-background-color: #f9fafb; }
            QHeaderView::section { background-color: #f8fafc; padding: 6px; font-weight: bold; border-bottom: 2px solid #e2e8f0; }
        """)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows)

    def load_data(self):
        """Nạp danh sách khách hàng từ Database khớp với cấu trúc image_1d1b89.png"""
        db = DatabaseManager()
        conn = db.get_connection()
        if not conn: return
        
        cursor = conn.cursor()
        # Lấy đầy đủ các trường: Mã KH, Mã TK, Tên, GT, SĐT, Email
        cursor.execute("SELECT CUSTOMER_ID, ACCOUNT_ID, CUSTOMER_NAME, CUSTOMER_GENDER, CUSTOMER_PHONE, CUSTOMER_EMAIL FROM CUSTOMERS")
        rows = cursor.fetchall()
        
        self.table.setRowCount(0)
        
        for row_idx, row_data in enumerate(rows):
            self.table.insertRow(row_idx)
            
            # Cột 0: Mã KH
            self.table.setItem(row_idx, 0, QtWidgets.QTableWidgetItem(str(row_data[0])))
            # Cột 1: Mã tài khoản
            self.table.setItem(row_idx, 1, QtWidgets.QTableWidgetItem(str(row_data[1])))
            # Cột 2: Tên KH
            self.table.setItem(row_idx, 2, QtWidgets.QTableWidgetItem(str(row_data[2])))
            
            # Cột 3: Giới tính
            gioi_tinh = row_data[3] if row_data[3] else "N/A"
            self.table.setItem(row_idx, 3, QtWidgets.QTableWidgetItem(gioi_tinh))
            
            # Cột 4: SĐT
            self.table.setItem(row_idx, 4, QtWidgets.QTableWidgetItem(str(row_data[4])))
            # Cột 5: Email
            self.table.setItem(row_idx, 5, QtWidgets.QTableWidgetItem(str(row_data[5])))
            
            # Lưu lại thông tin cần thiết để truyền vào Dialog Sửa/Xóa
            item_dict = {
                "id": row_data[0], 
                "ten": row_data[2], 
                "gt": gioi_tinh, 
                "sdt": row_data[4],
                "email": row_data[5]
            }
            
            # Cột 6: Thao tác (Nút bấm)
            self.add_action_buttons(row_idx, item_dict)
            
        conn.close()

    def add_action_buttons(self, row, item):
        container = QtWidgets.QWidget()
        layout = QtWidgets.QHBoxLayout(container)
        layout.setContentsMargins(5, 2, 5, 2)
        layout.setSpacing(10)

        btn_edit = QtWidgets.QPushButton("Sửa")
        btn_delete = QtWidgets.QPushButton("Xóa")

        common = "padding: 5px; font-weight: bold; min-width: 60px; border-radius: 3px; color: white; border: none;"
        btn_edit.setStyleSheet(f"QPushButton {{ background-color: #3b82f6; {common} }} QPushButton:hover {{ background-color: #2563eb; }}")
        btn_delete.setStyleSheet(f"QPushButton {{ background-color: #ef4444; {common} }} QPushButton:hover {{ background-color: #dc2626; }}")

        btn_edit.clicked.connect(lambda: self.open_edit(item))
        btn_delete.clicked.connect(lambda: self.open_delete(item))

        layout.addWidget(btn_edit)
        layout.addWidget(btn_delete)
        
        # Đưa vào cột cuối cùng (cột 6) theo thiết kế
        self.table.setCellWidget(row, 6, container)

    def open_add(self):
        if AddCustomer().exec(): 
            self.load_data()

    def open_edit(self, item):
        if EditCustomer(item).exec(): 
            self.load_data()

    def open_delete(self, item):
        if DeleteCustomer(item).exec(): 
            self.load_data()