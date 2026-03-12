import os
from PyQt6 import uic, QtWidgets, QtCore
from src.database.db_connection import DatabaseManager

# Thiết lập đường dẫn gốc
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(os.path.dirname(CURRENT_DIR))
UI_PATH = os.path.join(ROOT_DIR, "ui")

# --- DIALOG THÊM TÀI KHOẢN ---
class AddAccount(QtWidgets.QDialog):
    def __init__(self):
        super().__init__()
        uic.loadUi(os.path.join(UI_PATH, "addTaiKhoan.ui"), self)
        
        # Thiết lập giá trị mặc định cho ComboBox
        self.cbVaiTro.addItems(["Admin", "Employee", "Customer"])
        self.cbTrangThai.addItems(["Active", "Inactive"])
        
        self.btnLuu.clicked.connect(self.save_data)
        self.btnHuy.clicked.connect(self.reject)

    def save_data(self):
        ma_tk = self.txtMaTK.text().strip()
        username = self.txtTenDangNhap.text().strip()
        role = self.cbVaiTro.currentText()
        status = self.cbTrangThai.currentText()
        password = "123" # Mật khẩu mặc định khi tạo mới

        if not ma_tk or not username:
            QtWidgets.QMessageBox.warning(self, "Lỗi", "Vui lòng nhập đầy đủ Mã tài khoản và Tên đăng nhập!")
            return

        db = DatabaseManager()
        conn = db.get_connection()
        if not conn: return
        
        try:
            cursor = conn.cursor()
            # Kiểm tra trùng ID hoặc Username
            cursor.execute("SELECT COUNT(*) FROM ACCOUNTS WHERE ACCOUNT_ID = ? OR USERNAME = ?", (ma_tk, username))
            if cursor.fetchone()[0] > 0:
                QtWidgets.QMessageBox.warning(self, "Lỗi", "Mã tài khoản hoặc Tên đăng nhập đã tồn tại!")
                return

            cursor.execute("""
                INSERT INTO ACCOUNTS (ACCOUNT_ID, USERNAME, PASSWORD, ROLE, ACCOUNT_STATUS)
                VALUES (?, ?, ?, ?, ?)
            """, (ma_tk, username, password, role, status))
            
            conn.commit()
            QtWidgets.QMessageBox.information(self, "Thành công", f"Đã tạo tài khoản {username} thành công!\nMật khẩu mặc định là: 123")
            self.accept()
        except Exception as e:
            conn.rollback()
            QtWidgets.QMessageBox.critical(self, "Lỗi hệ thống", str(e))
        finally:
            conn.close()

# --- DIALOG SỬA TÀI KHOẢN ---
class EditAccount(QtWidgets.QDialog):
    def __init__(self, account_id):
        super().__init__()
        uic.loadUi(os.path.join(UI_PATH, "editTaiKhoan.ui"), self)
        self.account_id = account_id
        
        self.cbVaiTro.addItems(["Admin", "Employee", "Customer"])
        self.cbTrangThai.addItems(["Active", "Inactive"])
        
        self.load_data()
        self.btnLuu.clicked.connect(self.update_data)
        self.btnHuy.clicked.connect(self.reject)

    def load_data(self):
        db = DatabaseManager()
        conn = db.get_connection()
        if not conn: return
        cursor = conn.cursor()
        cursor.execute("SELECT USERNAME, ROLE, ACCOUNT_STATUS FROM ACCOUNTS WHERE ACCOUNT_ID = ?", (self.account_id,))
        row = cursor.fetchone()
        if row:
            self.txtMaTK.setText(self.account_id)
            self.txtMaTK.setEnabled(False) # Không cho sửa khóa chính
            self.txtTenDangNhap.setText(row[0])
            self.cbVaiTro.setCurrentText(row[1])
            self.cbTrangThai.setCurrentText(row[2])
        conn.close()

    def update_data(self):
        username = self.txtTenDangNhap.text().strip()
        role = self.cbVaiTro.currentText()
        status = self.cbTrangThai.currentText()

        db = DatabaseManager()
        conn = db.get_connection()
        if not conn: return
        try:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE ACCOUNTS SET USERNAME = ?, ROLE = ?, ACCOUNT_STATUS = ?
                WHERE ACCOUNT_ID = ?
            """, (username, role, status, self.account_id))
            conn.commit()
            self.accept()
        except Exception as e:
            conn.rollback()
            QtWidgets.QMessageBox.critical(self, "Lỗi", str(e))
        finally:
            conn.close()

# --- DIALOG XÓA TÀI KHOẢN ---
class DeleteAccount(QtWidgets.QDialog):
    def __init__(self, account_id, username):
        super().__init__()
        # Giả định bạn dùng chung file deleteDonHang.ui cho thống nhất
        uic.loadUi(os.path.join(UI_PATH, "deleteDonHang.ui"), self)
        self.account_id = account_id
        if hasattr(self, 'lblCanhBao'):
            self.lblCanhBao.setText(f"Xác nhận xóa tài khoản: {username}?\n(Mã: {account_id})")
        self.btnXoa.clicked.connect(self.delete_data)
        self.btnHuy.clicked.connect(self.reject)

    def delete_data(self):
        db = DatabaseManager()
        conn = db.get_connection()
        if not conn: return
        try:
            cursor = conn.cursor()
            # Kiểm tra xem tài khoản này có đang gắn với Khách hàng hay Nhân viên nào không
            cursor.execute("SELECT COUNT(*) FROM CUSTOMERS WHERE ACCOUNT_ID = ?", (self.account_id,))
            if cursor.fetchone()[0] > 0:
                QtWidgets.QMessageBox.warning(self, "Lỗi", "Không thể xóa vì tài khoản này đang liên kết với một Khách hàng!")
                return
            
            cursor.execute("DELETE FROM ACCOUNTS WHERE ACCOUNT_ID = ?", (self.account_id,))
            conn.commit()
            self.accept()
        except Exception as e:
            conn.rollback()
            QtWidgets.QMessageBox.critical(self, "Lỗi", str(e))
        finally:
            conn.close()

# --- QUẢN LÝ CHÍNH TRANG TÀI KHOẢN ---
class AccountManager:
    def __init__(self, table_widget):
        self.table = table_widget
        self.init_ui_style()

    def init_ui_style(self):
        self.table.verticalHeader().setVisible(False)
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(4, QtWidgets.QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(4, 150)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows)

    def load_data(self):
        """Nạp danh sách tài khoản từ SQL Server"""
        db = DatabaseManager()
        conn = db.get_connection()
        if not conn: return
        
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT ACCOUNT_ID, USERNAME, ROLE, ACCOUNT_STATUS FROM ACCOUNTS ORDER BY ACCOUNT_ID DESC")
            rows = cursor.fetchall()
            
            self.table.setRowCount(0)
            for row_idx, row_data in enumerate(rows):
                self.table.insertRow(row_idx)
                for col_idx, val in enumerate(row_data):
                    item = QtWidgets.QTableWidgetItem(str(val))
                    if col_idx in [0, 2, 3]: item.setTextAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
                    self.table.setItem(row_idx, col_idx, item)
                
                # Thêm nút bấm vào cột 4 (Thao tác)
                self.add_action_buttons(row_idx, row_data[0], row_data[1])
        except Exception as e:
            print(f"Lỗi load tài khoản: {e}")
        finally:
            conn.close()

    def add_action_buttons(self, row, acc_id, username):
        container = QtWidgets.QWidget()
        layout = QtWidgets.QHBoxLayout(container)
        layout.setContentsMargins(5, 2, 5, 2)
        
        btn_e = QtWidgets.QPushButton("Sửa")
        btn_e.setStyleSheet("background-color: #3b82f6; color: white; font-weight: bold; border-radius: 3px;")
        btn_e.clicked.connect(lambda: self.open_edit(acc_id))
        
        btn_d = QtWidgets.QPushButton("Xóa")
        btn_d.setStyleSheet("background-color: #ef4444; color: white; font-weight: bold; border-radius: 3px;")
        btn_d.clicked.connect(lambda: self.open_delete(acc_id, username))
        
        layout.addWidget(btn_e)
        layout.addWidget(btn_d)
        self.table.setCellWidget(row, 4, container)

    def open_add(self):
        if AddAccount().exec(): self.load_data()

    def open_edit(self, acc_id):
        if EditAccount(acc_id).exec(): self.load_data()

    def open_delete(self, acc_id, username):
        if DeleteAccount(acc_id, username).exec(): self.load_data()