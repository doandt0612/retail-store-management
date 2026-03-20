import sys
import os
from PyQt6 import QtWidgets, uic
from PyQt6.QtWidgets import QMessageBox

# Import Database
from src.database.db_connection import DatabaseManager

# Import các Manager
from src.modules.Category import DanhMucManager
from src.modules.Overview import OverviewManager
from src.modules.Order import OrderManager
# from src.modules.Invoice import InvoiceManager
from src.modules.Product import ProductManager
from src.modules.Customer import CustomerManager
from src.modules.Supplier import SupplierManager
from src.modules.Employee import EmployeeManager
from src.modules.Promotion import PromotionManager
from src.modules.Product_Input import PurchaseManager
# Lấy đường dẫn gốc của project
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
UI_DIR = os.path.join(CURRENT_DIR, "ui")


class LoginWindow(QtWidgets.QDialog):
    def __init__(self):
        super().__init__()
        uic.loadUi(os.path.join(UI_DIR, "login.ui"), self)

        self.db = DatabaseManager()
        if not self.db.get_connection():
            QMessageBox.critical(self, "Lỗi Hệ Thống", "Không thể kết nối CSDL!\nVui lòng kiểm tra Server hoặc file .env")

        self.btnDangNhap.clicked.connect(self.handle_login)
        self.txtMatKhau.returnPressed.connect(self.handle_login)

    def handle_login(self):
        username = self.txtTenDangNhap.text().strip()
        password = self.txtMatKhau.text().strip()

        if not username or not password:
            QMessageBox.warning(self, "Cảnh báo", "Vui lòng nhập đầy đủ Tên đăng nhập và Mật khẩu!")
            return

        conn = self.db.get_connection()
        if not conn: return

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
                    QMessageBox.warning(self, "Từ chối", "Tài khoản của bạn đã bị khóa!")
                    return
                login_success = True
            else:
                QMessageBox.warning(self, "Thất bại", "Tên đăng nhập hoặc mật khẩu không chính xác!")
        except Exception as e:
            QMessageBox.critical(self, "Lỗi DB", f"Lỗi truy vấn dữ liệu:\n{str(e)}")
        finally:
            conn.close()

        # ==========================================
        # XỬ LÝ ẨN MÀN HÌNH ĐĂNG NHẬP MƯỢT MÀ
        # ==========================================
        if login_success:
            self.hide() # 1. Ẩn màn hình đăng nhập NGAY LẬP TỨC
            # 2. Dùng None thay vì self để thông báo không bị dính vào màn hình đăng nhập cũ
            QMessageBox.information(None, "Thành công", f"Đăng nhập thành công!\nVai trò: {role}")
            # 3. Load giao diện chính
            self.route_to_main_window(role, emp_id)

    def route_to_main_window(self, role, emp_id):
        # Đã bỏ lệnh self.hide() ở đây vì đã gọi ở trên
        try:
            if role == "Quản lý cửa hàng":
                self.main_window = ManagerWindow(emp_id, self)
            elif role == "Nhân viên bán hàng":
                self.main_window = SalesWindow(emp_id, self)
            elif role == "Nhân viên kho":
                self.main_window = WarehouseWindow(emp_id, self)
            else:
                QMessageBox.critical(None, "Lỗi", "Vai trò không hợp lệ!")
                self.show()
                return

            self.main_window.show()
        except Exception as e:
            QMessageBox.critical(None, "Lỗi Giao Diện", f"Không thể tải giao diện {role}:\n{str(e)}")
            self.show() # Hiện lại form đăng nhập nếu lỗi UI


# ==========================================
# LỚP CƠ SỞ (Chứa logic Đăng xuất hiện lại Login)
# ==========================================
class BaseRoleWindow(QtWidgets.QMainWindow):
    def __init__(self, emp_id, login_window):
        super().__init__()
        self.emp_id = emp_id
        self.login_window = login_window

    def setup_common_events(self):
        """Hàm dùng chung: Gắn sự kiện đăng xuất nếu UI có nút btnDangXuat"""
        if hasattr(self, 'btnDangXuat'):
            self.btnDangXuat.clicked.connect(self.logout)

    def logout(self):
        """Logic đăng xuất với Xác nhận"""
        reply = QMessageBox.question(
            self, 'Xác nhận', 'Bạn có chắc chắn muốn đăng xuất khỏi hệ thống?',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.close()                          # 1. Tắt giao diện chính (Quản lý/Bán hàng...)
            self.login_window.txtMatKhau.clear()  # 2. Xóa ô mật khẩu để bảo mật
            self.login_window.show()              # 3. HIỆN LẠI màn hình đăng nhập

    def change_page(self, page_widget, load_function=None):
        self.stackedWidget.setCurrentWidget(page_widget)
        if load_function:
            load_function()

    # --- CÔNG CỤ TẠO WIDGET ẢO ĐỂ CHỐNG LỖI (ANTI-CRASH) ---
    def get_widget(self, names, widget_class):
        """Tìm widget theo tên. Nếu UI thiết kế thiếu, tự động tạo widget ảo tàng hình để chống crash Manager."""
        for name in names:
            if hasattr(self, name):
                return getattr(self, name)
        # Nếu không có nút thật trên giao diện, tạo nút ảo không hiển thị
        dummy = widget_class(self)
        dummy.hide()
        return dummy

    # --- CÁC HÀM KHỞI TẠO MODULE ---

    def setup_module_overview(self):
        if not hasattr(self, 'tblDonHangGanDay'): return

        # ĐỔI TÊN Ở 2 DÒNG NÀY CHO KHỚP VỚI HÌNH ẢNH:
        lbl_revenue = self.get_widget(['lblHienThiTongDoanhThu'], QtWidgets.QLabel)
        lbl_orders = self.get_widget(['lblHienThiTongDonHang'], QtWidgets.QLabel)

        self.overview_manager = OverviewManager(self.tblDonHangGanDay, lbl_revenue, lbl_orders)

        # --- Kế thừa chức năng nhảy trang Khách hàng từ bảng Đơn hàng gần đây ---
        def handle_switch_to_customer(customer_data):
            if hasattr(self, 'pageKhachHang'):
                self.stackedWidget.setCurrentWidget(self.pageKhachHang)
            if hasattr(self, 'customer_manager'):
                self.customer_manager.open_history(customer_data)

        self.overview_manager.switch_to_customer_callback = handle_switch_to_customer
        # ------------------------------------------------------------------------

        if hasattr(self, 'btnTongQuan'):
            self.btnTongQuan.clicked.connect(lambda: self.change_page(self.pageTongQuan, self.overview_manager.load_data))
        # ------------------------------------------------------------------------

        if hasattr(self, 'btnTongQuan'):
            self.btnTongQuan.clicked.connect(lambda: self.change_page(self.pageTongQuan, self.overview_manager.load_data))

    def setup_module_order(self):
        if not hasattr(self, 'tblDonHang'): return

        # TÌM KIẾM VÀ LỌC: Đảm bảo deLocNgay được lấy bằng QLineEdit
        txt_search_order = self.get_widget(['txtTimKiemDonHang', 'txtTimDonHang'], QtWidgets.QLineEdit)
        de_filter_order = self.get_widget(['deLocNgay', 'deLocNgayDonHang'], QtWidgets.QLineEdit)
        btn_search_order = self.get_widget(['btnTimDonHang', 'btnTimKiemDH'], QtWidgets.QPushButton)

        # Khởi tạo OrderManager với các thanh tìm kiếm mới
        self.order_manager = OrderManager(
            table_widget=self.tblDonHang,
            txt_search=txt_search_order,
            date_filter=de_filter_order,
            btn_search=btn_search_order
        )

        # --- THÊM ĐOẠN NÀY ĐỂ KẾT NỐI VỚI MODULE KHÁCH HÀNG ---
        def handle_switch_to_customer(customer_data):
            # 1. Chuyển sang trang Khách hàng (nếu có)
            if hasattr(self, 'pageKhachHang'):
                self.stackedWidget.setCurrentWidget(self.pageKhachHang)

            # 2. Gọi hàm mở Lịch sử mua hàng của Khách hàng
            if hasattr(self, 'customer_manager'):
                self.customer_manager.open_history(customer_data)

        # Gán callback vào OrderManager
        self.order_manager.switch_to_customer_callback = handle_switch_to_customer
        # -----------------------------------------------------

        if hasattr(self, 'btnDonHang'):
            self.btnDonHang.clicked.connect(lambda: self.change_page(self.pageDonHang, self.order_manager.load_data))
        if hasattr(self, 'btnTaoDonHang'):
            self.btnTaoDonHang.clicked.connect(self.order_manager.open_create)

    # def setup_module_invoice(self):
    #     if not hasattr(self, 'tblHoaDon'): return

    #     btn_prev = self.get_widget(['btnTruoc_3'], QtWidgets.QPushButton)
    #     btn_next = self.get_widget(['btnSau_3'], QtWidgets.QPushButton)
    #     lbl_status = self.get_widget(['lblHienThiHD'], QtWidgets.QLabel)

    #     self.invoice_manager = InvoiceManager(self.tblHoaDon, btn_prev, btn_next, lbl_status)

    #     if hasattr(self, 'btnHoaDon'):
    #         self.btnHoaDon.clicked.connect(lambda: self.change_page(self.pageHoaDon, self.invoice_manager.load_data))

    def setup_module_product(self):
        if not hasattr(self, 'tblDanhSachSP'): return

        txt_search = self.get_widget(['txtTimSP_2'], QtWidgets.QLineEdit)
        cb_cat = self.get_widget(['cbDanhMuc'], QtWidgets.QComboBox)
        cb_sup = self.get_widget(['cbNhaCungCap'], QtWidgets.QComboBox)

        self.product_manager = ProductManager(self.tblDanhSachSP, txt_search, cb_cat, cb_sup)

        # --- THIẾT LẬP CALLBACK CHO MODULE SẢN PHẨM ---

        # 1. Callback khi click tên Danh Mục
        def handle_switch_to_category(cat_id, cat_name):
            if hasattr(self, 'pageDanhMuc'):
                # Nhảy sang trang Danh mục
                self.stackedWidget.setCurrentWidget(self.pageDanhMuc)
                # Tự động gõ tên danh mục vào ô tìm kiếm và lọc
                if hasattr(self, 'category_manager') and hasattr(self.category_manager, 'txt_search') and self.category_manager.txt_search:
                    self.category_manager.txt_search.setText(cat_name)
                    self.category_manager.load_data()

        # 2. Callback khi click tên Nhà cung cấp
        def handle_open_supplier(sup_id):
            if hasattr(self, 'supplier_manager'):
                # Gọi hàm xem chi tiết NCC (Bạn cần tạo hàm này bên SupplierManager)
                # Tạm thời hiển thị thông báo:
                QtWidgets.QMessageBox.information(self, "Thông tin", f"Mở chi tiết NCC ID: {sup_id}")

        self.product_manager.switch_to_category_callback = handle_switch_to_category
        self.product_manager.open_supplier_callback = handle_open_supplier
        # -----------------------------------------------

        if hasattr(self, 'btnSanPham'):
            self.btnSanPham.clicked.connect(lambda: self.change_page(self.pageSanPham, self.product_manager.load_data))
        if hasattr(self, 'btnThemSP'):
            self.btnThemSP.clicked.connect(self.product_manager.open_add)

    def setup_module_category(self):
        if not hasattr(self, 'tblDanhMuc'): return

        # Lấy thêm ô tìm kiếm và nút tìm kiếm (nếu có trên giao diện)
        txt_search = self.get_widget(['txtTimKiemDanhMuc'], QtWidgets.QLineEdit)
        btn_search = self.get_widget(['btnTimKiemDanhMuc'], QtWidgets.QPushButton)

        # Truyền vào Manager
        self.category_manager = DanhMucManager(self.tblDanhMuc, txt_search, btn_search)

        if hasattr(self, 'btnDanhMuc'):
            self.btnDanhMuc.clicked.connect(lambda: self.change_page(self.pageDanhMuc, self.category_manager.load_data))
        if hasattr(self, 'btnThemDanhMuc'):
            self.btnThemDanhMuc.clicked.connect(self.category_manager.open_add)

    def setup_module_customer(self):
        if not hasattr(self, 'tblDanhSachKH'): return

        txt_search = self.get_widget(['txtTimKiemKH'], QtWidgets.QLineEdit)
        btn_search = self.get_widget(['btnTimKiemKH'], QtWidgets.QPushButton)

        self.customer_manager = CustomerManager(self.tblDanhSachKH, txt_search, btn_search)

        if hasattr(self, 'btnKhachHang'):
            self.btnKhachHang.clicked.connect(lambda: self.change_page(self.pageKhachHang, self.customer_manager.load_data))
        if hasattr(self, 'btnThemKH'):
            self.btnThemKH.clicked.connect(self.customer_manager.open_add)

    def setup_module_promotion(self):
        if not hasattr(self, 'tblDanhSachKM'): return

        txt_search = self.get_widget(['txtTimKhuyenMai'], QtWidgets.QLineEdit)
        cb_status  = self.get_widget(['cbTrangThaiKM'],   QtWidgets.QComboBox)

        self.promotion_manager = PromotionManager(self.tblDanhSachKM, txt_search, cb_status)

        if hasattr(self, 'btnKhuyenMai'):
            self.btnKhuyenMai.clicked.connect(
                lambda: self.change_page(self.pageKhuyenMai, self.promotion_manager.load_data)
            )
        if hasattr(self, 'btnThemKhuyenMai'):
            self.btnThemKhuyenMai.clicked.connect(self.promotion_manager.open_add)

    def setup_module_purchase(self):
        """
        Module Nhập Hàng.
        Tìm bảng theo nhiều tên có thể có trong UI, gắn sự kiện nút.
        Tên widget trong mainQLCH.ui:
          tblDanhSachDonNhap hoặc tblNhapHang – QTableWidget 6 cột
          pageNhapHang, btnNhapHang, btnThemDonNhap
          txtTimNhapHang, cbTrangThaiNhapHang (tùy chọn)
        """
        # Tên bảng thực tế trong UI: tblDanhSachNhapHang
        if not hasattr(self, 'tblDanhSachNhapHang'): return

        txt_search = self.get_widget(['txtTimNhapHang'],      QtWidgets.QLineEdit)
        cb_status  = self.get_widget(['cbTrangThaiNhapHang'], QtWidgets.QComboBox)
        self.purchase_manager = PurchaseManager(self.tblDanhSachNhapHang, txt_search, cb_status)

        if hasattr(self, 'btnNhapHang'):
            self.btnNhapHang.clicked.connect(
                lambda: self.change_page(self.pageNhapHang, self.purchase_manager.load_data)
            )
        if hasattr(self, 'btnThemDonNhap'):
            self.btnThemDonNhap.clicked.connect(self.purchase_manager.open_add)


    def setup_module_supplier(self):
        if not hasattr(self, 'tblDanhSachNCC'): return

        txt_search = self.get_widget(['txtTimKiemNCC'], QtWidgets.QLineEdit)
        btn_search = self.get_widget(['btnTimKiemNCC'], QtWidgets.QPushButton)
        self.supplier_manager = SupplierManager(self.tblDanhSachNCC, txt_search, btn_search)

        def handle_open_purchase_order(po_id):
            if hasattr(self, 'pageNhapHang'):
                self.stackedWidget.setCurrentWidget(self.pageNhapHang)
            if hasattr(self, 'purchase_manager'):
                self.purchase_manager.load_data()
                self.purchase_manager.open_view(po_id)

        self.supplier_manager.open_purchase_order_callback = handle_open_purchase_order

        if hasattr(self, 'btnNhaCungCap'):
            self.btnNhaCungCap.clicked.connect(
                lambda: self.change_page(self.pageNhaCungCap, self.supplier_manager.load_data)
            )
        if hasattr(self, 'btnThemNCC'):
            self.btnThemNCC.clicked.connect(self.supplier_manager.open_add)

    def setup_module_employee(self):
        tbl_nv = self.get_widget(['tblDanhSachNV', 'tblNhanVien', 'tblDanhSachNhanVien'], QtWidgets.QTableWidget)

        if not hasattr(self, 'tblDanhSachNV') and not hasattr(self, 'tblNhanVien') and not hasattr(self, 'tblDanhSachNhanVien'):
            return

        txt_search = self.get_widget(['txtTimKiemNV', 'txtTimNhanVien'], QtWidgets.QLineEdit)
        btn_search = self.get_widget(['btnTimKiemNV', 'btnTimNhanVien'], QtWidgets.QPushButton)

        # Dùng hasattr để lấy widget thật, populate items
        cb_type = None
        if hasattr(self, 'cbLocLoaiNV'):
            self.cbLocLoaiNV.clear()
            self.cbLocLoaiNV.addItems(["Tất cả", "Toàn thời gian", "Bán thời gian"])
            cb_type = self.cbLocLoaiNV

        self.employee_manager = EmployeeManager(tbl_nv, txt_search, btn_search, cb_type)

        if hasattr(self, 'btnNhanVien'):
            self.btnNhanVien.clicked.connect(
                lambda: self.change_page(self.pageNhanVien, self.employee_manager.load_data)
            )

        btn_add = self.get_widget(['btnThemNhanVien', 'btnThemNV'], QtWidgets.QPushButton)
        if btn_add and not btn_add.isHidden():
            btn_add.clicked.connect(self.employee_manager.open_add)


# ==========================================
# CÁC CỬA SỔ CHÍNH THEO TỪNG ROLE
# ==========================================

class ManagerWindow(BaseRoleWindow):
    def __init__(self, emp_id, login_window):
        super().__init__(emp_id, login_window)
        uic.loadUi(os.path.join(UI_DIR, "QuanLyCuaHang", "mainQLCH.ui"), self)

        self.setup_common_events()

        self.setup_module_overview()
        self.setup_module_order()
        self.setup_module_product()
        self.setup_module_category()
        self.setup_module_supplier()
        self.setup_module_customer()

        # Gọi thêm các module mới cho Quản lý
        self.setup_module_promotion()
        self.setup_module_purchase()
        self.setup_module_employee()

        # ---> NÚT ĐẦU TIÊN CỦA QUẢN LÝ LÀ: TỔNG QUAN <---
        if hasattr(self, 'pageTongQuan') and hasattr(self, 'overview_manager'):
            self.change_page(self.pageTongQuan, self.overview_manager.load_data)


class SalesWindow(BaseRoleWindow):
    def __init__(self, emp_id, login_window):
        super().__init__(emp_id, login_window)
        uic.loadUi(os.path.join(UI_DIR, "NhanVienBanHang", "mainNVBH.ui"), self)

        self.setup_common_events()

        self.setup_module_category()
        self.setup_module_order()
        self.setup_module_customer()
        self.setup_module_product()
        self.setup_module_promotion()

        # ---> NÚT ĐẦU TIÊN CỦA BÁN HÀNG LÀ: ĐƠN HÀNG <---
        if hasattr(self, 'pageDonHang') and hasattr(self, 'order_manager'):
            self.change_page(self.pageDonHang, self.order_manager.load_data)


class WarehouseWindow(BaseRoleWindow):
    def __init__(self, emp_id, login_window):
        super().__init__(emp_id, login_window)
        uic.loadUi(os.path.join(UI_DIR, "NhanVienKho", "mainNVK.ui"), self)

        self.setup_common_events()

        self.setup_module_category()
        self.setup_module_supplier()
        self.setup_module_product()
        self.setup_module_purchase()

        # ---> NÚT ĐẦU TIÊN CỦA THỦ KHO LÀ: DANH MỤC <---
        if hasattr(self, 'pageDanhMuc') and hasattr(self, 'category_manager'):
            self.change_page(self.pageDanhMuc, self.category_manager.load_data)


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    login_window = LoginWindow()
    login_window.show()
    sys.exit(app.exec())