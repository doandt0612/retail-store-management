import sys
import os
from PyQt6 import QtWidgets, uic
from src.modules.Category import DanhMucManager
from src.modules.Overview import OverviewManager
from src.modules.Order import OrderManager
from src.modules.Invoice import InvoiceManager
from src.modules.Product import ProductManager
from src.modules.Customer import CustomerManager
from src.modules.Supplier import SupplierManager
from src.modules.Account import AccountManager

from src.database.db_connection import DatabaseManager
from PyQt6.QtWidgets import QMessageBox


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        # Thiết lập đường dẫn và nạp giao diện
        current_dir = os.path.dirname(os.path.abspath(__file__))
        ui_path = os.path.join(current_dir, "ui", "main.ui")
        uic.loadUi(ui_path, self)

        # Kiểm tra kết nối database ngay lúc khởi động
        self.db = DatabaseManager()
        if not self.db.get_connection():
            QMessageBox.critical(self, "Lỗi Hệ Thống", 
                "Không thể kết nối đến cơ sở dữ liệu.\nVui lòng kiểm tra file .env hoặc Server!")

        # Khởi tạo bộ quản lý 
        
        # Truyền đối tượng bảng vào bộ quản lý
        self.category_manager = DanhMucManager(self.tblDanhMuc)
        self.overview_manager = OverviewManager(self.tblDonHangGanDay)
        self.invoice_manager = InvoiceManager(
                                    self.tblHoaDon,
                                    self.btnTruoc_3,
                                    self.btnSau_3,
                                    self.lblHienThiHD
                                )
        self.order_manager = OrderManager(self.tblDonHang)
        self.product_manager = ProductManager(
                                    self.tblDanhSachSP,  # Bảng danh sách
                                    self.btnTruoc_2,     # Nút Trước
                                    self.btnSau_2,       # Nút Sau
                                    self.lblHienThiSP,   # Nhãn "Hiển thị 10 sản phẩm..."
                                    self.txtTimSP_2,     # Ô tìm kiếm
                                    self.cbDanhMuc,      # Combobox Danh mục
                                    self.cbNhaCungCap    # Combobox Nhà cung cấp
                                )

        self.supplier_manager = SupplierManager(self.tblDanhSachNCC)
        self.customer_manager = CustomerManager(self.tblDanhSachKH)
        self.account_manager = AccountManager(self.tblDanhSachTK)


        self.stackedWidget.setCurrentIndex(0)
        self.overview_manager.load_recent_orders()

        self.connect_button()
        self.show()

    def connect_button(self):

        # Kết nối nút với hàm xử lý riêng (để vừa chuyển trang vừa load data)
        self.btnTongQuan.clicked.connect(self.mo_trang_tong_quan)
        self.btnDonHang.clicked.connect(self.mo_trang_don_hang)
        self.btnHoaDon.clicked.connect(self.mo_trang_hoa_don)
        self.btnSanPham.clicked.connect(self.mo_trang_san_pham)
        self.btnDanhMuc.clicked.connect(self.mo_trang_danh_muc)
        self.btnNhaCungCap.clicked.connect(self.mo_trang_nha_cung_cap)
        self.btnKhachHang.clicked.connect(self.mo_trang_khach_hang)
        self.btnTaiKhoan.clicked.connect(self.mo_trang_tai_khoan)


        # Kết nối nút trên giao diện chính với Dialog Thêm
        self.btnThemDanhMuc.clicked.connect(self.category_manager.open_add)
        self.btnTaoDonHang.clicked.connect(self.order_manager.open_create)

        self.btnThemSP.clicked.connect(self.product_manager.open_add)
        self.btnThemKH.clicked.connect(self.customer_manager.open_add)
        self.btnThemNCC.clicked.connect(self.supplier_manager.open_add)
        self.btnThemTK.clicked.connect(self.account_manager.open_add)


    def mo_trang_tong_quan(self):
        self.stackedWidget.setCurrentIndex(0)
        self.overview_manager.load_recent_orders()

    def mo_trang_don_hang(self):
        self.stackedWidget.setCurrentIndex(1) # Trang Đơn hàng
        self.order_manager.load_data()

    def mo_trang_hoa_don(self):
        self.stackedWidget.setCurrentIndex(2)
        self.invoice_manager.load_data()

    def mo_trang_san_pham(self):
        # Chuyển đến index của trang Sản phẩm và load dữ liệu
        self.stackedWidget.setCurrentIndex(3)       
        self.product_manager.load_data()

    def mo_trang_danh_muc(self):
        # Hàm vừa chuyển trang vừa yêu cầu manager nạp dữ liệu mới nhất
        self.stackedWidget.setCurrentIndex(4)
        self.category_manager.load_data()

    def mo_trang_nha_cung_cap(self):
        self.stackedWidget.setCurrentIndex(5) 
        self.supplier_manager.load_data()

    def mo_trang_khach_hang(self):
        self.stackedWidget.setCurrentIndex(6) 
        self.customer_manager.load_data()

    def mo_trang_tai_khoan(self):
        self.stackedWidget.setCurrentIndex(7)
        self.account_manager.load_data()

if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    sys.exit(app.exec())