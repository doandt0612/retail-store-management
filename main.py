import sys
import os
from PyQt6 import QtWidgets, uic
from PyQt6.QtWidgets import QMessageBox

# Import Database
from src.database.db_connection import DatabaseManager

# Import các Manager (Dành cho Quản lý)
from src.modules.Category import DanhMucManager
from src.modules.Overview import OverviewManager
from src.modules.Order import OrderManager
from src.modules.Invoice import InvoiceManager
from src.modules.Product import ProductManager
from src.modules.Customer import CustomerManager
from src.modules.Supplier import SupplierManager
from src.modules.Account import AccountManager

# Lấy đường dẫn gốc của project
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
UI_DIR = os.path.join(CURRENT_DIR, "ui")


class LoginWindow(QtWidgets.QDialog):
    def __init__(self):
        super().__init__()
        # Load giao diện đăng nhập
        uic.loadUi(os.path.join(UI_DIR, "login.ui"), self)

        # Kiểm tra kết nối DB ngay khi mở app
        self.db = DatabaseManager()
        if not self.db.get_connection():
            QMessageBox.critical(self, "Lỗi Hệ Thống", "Không thể kết nối CSDL!\nVui lòng kiểm tra Server hoặc file .env")

        # Kết nối sự kiện nút đăng nhập
        self.btnDangNhap.clicked.connect(self.handle_login)
        self.txtMatKhau.returnPressed.connect(self.handle_login) # Bấm Enter ở ô mật khẩu để đăng nhập

    def handle_login(self):
        username = self.txtTenDangNhap.text().strip()
        password = self.txtMatKhau.text().strip()

        if not username or not password:
            QMessageBox.warning(self, "Cảnh báo", "Vui lòng nhập đầy đủ Tên đăng nhập và Mật khẩu!")
            return

        conn = self.db.get_connection()
        if not conn: return

        # Các biến lưu trạng thái để chuyển UI sau khi đóng DB
        role = None
        emp_id = None
        login_success = False

        try:
            cursor = conn.cursor()
            query = "SELECT AccountID, EmployeeID, Role, Status FROM Accounts WHERE Username = ? AND Password = ?"
            cursor.execute(query, (username, password))
            account = cursor.fetchone()

            if account:
                acc_id, emp_id, role, status = account

                if status == "Đã bị khóa":
                    QMessageBox.warning(self, "Từ chối truy cập", "Tài khoản của bạn đã bị khóa. Vui lòng liên hệ Quản lý!")
                    return
                
                login_success = True
            else:
                QMessageBox.warning(self, "Thất bại", "Tên đăng nhập hoặc mật khẩu không chính xác!")

        except Exception as e:
            QMessageBox.critical(self, "Lỗi DB", f"Lỗi truy vấn dữ liệu:\n{str(e)}")
        finally:
            conn.close()

        # THỰC HIỆN CHUYỂN TRANG
        if login_success:
            QMessageBox.information(self, "Đăng nhập thành công", f"Chào mừng bạn!\nVai trò: {role}")
            self.route_to_main_window(role, emp_id)


    def route_to_main_window(self, role, emp_id):
        """Hàm điều hướng mở cửa sổ tương ứng với quyền"""
        self.hide() # Ẩn màn hình đăng nhập

        try:
            # TRUYỀN 'self' (tức là LoginWindow) VÀO CÁC WINDOW CHÍNH
            if role == "Quản lý":
                self.main_window = ManagerWindow(emp_id, self)
            elif role == "Nhân viên bán hàng":
                self.main_window = SalesWindow(emp_id, self)
            elif role == "Nhân viên kho":
                self.main_window = WarehouseWindow(emp_id, self)
            else:
                QMessageBox.critical(self, "Lỗi", "Vai trò không hợp lệ trong hệ thống!")
                self.show()
                return

            self.main_window.show()
        except Exception as e:
            QMessageBox.critical(self, "Lỗi Giao Diện", f"Không thể tải giao diện cho vai trò {role}:\n{str(e)}")
            self.show() # Hiện lại form đăng nhập nếu lỗi UI


# ==========================================
# CÁC CỬA SỔ CHÍNH THEO TỪNG VỊ TRÍ
# ==========================================

class ManagerWindow(QtWidgets.QMainWindow):
    """Cửa sổ dành cho Quản lý cửa hàng (Toàn quyền)"""
    def __init__(self, emp_id, login_window):
        super().__init__()
        self.emp_id = emp_id
        self.login_window = login_window  # Lưu lại màn hình đăng nhập
        
        ui_path = os.path.join(UI_DIR, "QuanLyCuaHang", "mainQLCH.ui")
        if not os.path.exists(ui_path):
            raise FileNotFoundError(f"Lỗi đường dẫn: Không tìm thấy file tại '{ui_path}'")
        uic.loadUi(ui_path, self)

        self.init_managers()
        self.connect_buttons()
        
        # Mặc định mở trang tổng quan
        self.stackedWidget.setCurrentIndex(0)
        self.overview_manager.load_recent_orders()

    def init_managers(self):
        self.category_manager = DanhMucManager(self.tblDanhMuc)
        self.overview_manager = OverviewManager(self.tblDonHangGanDay)
        self.invoice_manager = InvoiceManager(self.tblHoaDon, self.btnTruoc_3, self.btnSau_3, self.lblHienThiHD)
        self.order_manager = OrderManager(self.tblDonHang, self.btnTruoc, self.btnSau, self.lblHienThiDH)
        self.product_manager = ProductManager(
            self.tblDanhSachSP, self.btnTruoc_2, self.btnSau_2, 
            self.lblHienThiSP, self.txtTimSP_2, self.cbDanhMuc, self.cbNhaCungCap
        )
        self.supplier_manager = SupplierManager(self.tblDanhSachNCC)
        self.customer_manager = CustomerManager(self.tblDanhSachKH)
        self.account_manager = AccountManager(self.tblDanhSachTK)

    def connect_buttons(self):
        # Chuyển trang
        self.btnTongQuan.clicked.connect(lambda: self.change_page(0, self.overview_manager.load_recent_orders))
        self.btnDonHang.clicked.connect(lambda: self.change_page(1, self.order_manager.load_data))
        self.btnHoaDon.clicked.connect(lambda: self.change_page(2, self.invoice_manager.load_data))
        self.btnSanPham.clicked.connect(lambda: self.change_page(3, self.product_manager.load_data))
        self.btnDanhMuc.clicked.connect(lambda: self.change_page(4, self.category_manager.load_data))
        self.btnNhaCungCap.clicked.connect(lambda: self.change_page(5, self.supplier_manager.load_data))
        self.btnKhachHang.clicked.connect(lambda: self.change_page(6, self.customer_manager.load_data))
        self.btnTaiKhoan.clicked.connect(lambda: self.change_page(7, self.account_manager.load_data))

        # Nút chức năng
        self.btnThemDanhMuc.clicked.connect(self.category_manager.open_add)
        self.btnTaoDonHang.clicked.connect(self.order_manager.open_create)
        self.btnThemSP.clicked.connect(self.product_manager.open_add)
        self.btnThemKH.clicked.connect(self.customer_manager.open_add)
        self.btnThemNCC.clicked.connect(self.supplier_manager.open_add)
        self.btnThemTK.clicked.connect(self.account_manager.open_add)
        
        # NÚT ĐĂNG XUẤT
        self.btnDangXuat.clicked.connect(self.logout)

    def change_page(self, index, load_function=None):
        self.stackedWidget.setCurrentIndex(index)
        if load_function:
            load_function()

    def logout(self):
        """Hàm xử lý đăng xuất chung"""
        QMessageBox.information(self, "Đăng xuất", "Bạn đã đăng xuất thành công!")
        self.close()                             # Đóng cửa sổ hiện tại
        self.login_window.txtMatKhau.clear()     # Xóa ô mật khẩu cũ để bảo mật
        self.login_window.show()                 # Hiển thị lại màn hình Đăng nhập


class SalesWindow(QtWidgets.QMainWindow):
    """Cửa sổ dành cho Nhân viên bán hàng"""
    def __init__(self, emp_id, login_window):
        super().__init__()
        self.emp_id = emp_id
        self.login_window = login_window  # Lưu lại màn hình đăng nhập
        
        ui_path = os.path.join(UI_DIR, "NhanVienBanHang", "mainNVBH.ui")
        if not os.path.exists(ui_path): raise FileNotFoundError(f"Không tìm thấy: {ui_path}")
        uic.loadUi(ui_path, self)
        
        # TODO: Cấu hình manager cho Sales tại đây
        
        # NÚT ĐĂNG XUẤT
        self.btnDangXuat.clicked.connect(self.logout)

    def logout(self):
        QMessageBox.information(self, "Đăng xuất", "Bạn đã đăng xuất thành công!")
        self.close()
        self.login_window.txtMatKhau.clear()
        self.login_window.show()


class WarehouseWindow(QtWidgets.QMainWindow):
    """Cửa sổ dành cho Nhân viên kho"""
    def __init__(self, emp_id, login_window):
        super().__init__()
        self.emp_id = emp_id
        self.login_window = login_window  # Lưu lại màn hình đăng nhập
        
        ui_path = os.path.join(UI_DIR, "NhanVienKho", "mainNVK.ui")
        if not os.path.exists(ui_path): raise FileNotFoundError(f"Không tìm thấy: {ui_path}")
        uic.loadUi(ui_path, self)
        
        # TODO: Cấu hình manager cho Warehouse tại đây
        
        # NÚT ĐĂNG XUẤT
        self.btnDangXuat.clicked.connect(self.logout)

    def logout(self):
        QMessageBox.information(self, "Đăng xuất", "Bạn đã đăng xuất thành công!")
        self.close()
        self.login_window.txtMatKhau.clear()
        self.login_window.show()


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    
    # Khởi động ứng dụng bằng Màn hình Đăng nhập
    login_window = LoginWindow()
    login_window.show()
    
    sys.exit(app.exec())