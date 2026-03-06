import sys
import os
from PyQt6 import QtWidgets, uic
from src.modules.Category import DanhMucManager
from src.modules.Overview import OverviewManager
from src.modules.Order import OrderManager
from src.modules.Product import ProductManager
from src.modules.Stock import InventoryManager
from src.modules.Customer import CustomerManager
from src.modules.Supplier import SupplierManager

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
        self.order_manager = OrderManager(self.tblDonHang)
        self.product_manager = ProductManager(
                                    self.tblDanhSachSP, 
                                    self.txtTimSP_2, 
                                    self.cbDanhMuc,      # Truyền ComboBox Danh mục
                                    self.cbNhaCungCap    # Truyền ComboBox Nhà cung cấp
                                )
        self.inventory_manager = InventoryManager(self.tblKhoHang)
        self.supplier_manager = SupplierManager(self.tblDanhSachNCC)
        self.customer_manager = CustomerManager(self.tblDanhSachKH)


        self.stackedWidget.setCurrentIndex(0)
        self.overview_manager.load_recent_orders()

        self.connect_button()
        self.show()

    def connect_button(self):
        # Các nút chuyển trang
        self.btnNhaCungCap.clicked.connect(lambda: self.stackedWidget.setCurrentIndex(5))
        self.btnKhachHang.clicked.connect(lambda: self.stackedWidget.setCurrentIndex(6))


        # Kết nối nút với hàm xử lý riêng (để vừa chuyển trang vừa load data)
        self.btnTongQuan.clicked.connect(self.mo_trang_tong_quan)
        self.btnDonHang.clicked.connect(self.mo_trang_don_hang)
        self.btnSanPham.clicked.connect(self.mo_trang_san_pham)
        self.btnDanhMuc.clicked.connect(self.mo_trang_danh_muc)
        self.btnKhoHang.clicked.connect(self.mo_trang_kho_hang)
        self.btnNhaCungCap.clicked.connect(self.mo_trang_nha_cung_cap)
        self.btnKhachHang.clicked.connect(self.mo_trang_khach_hang)


        # Kết nối nút "Thêm danh mục" trên giao diện chính với Dialog Thêm
        self.btnThemDanhMuc.clicked.connect(self.category_manager.open_add)
        self.btnTaoDonHang.clicked.connect(self.order_manager.open_create)
        self.btnThemSP.clicked.connect(self.product_manager.open_add)
        self.btnThemKH.clicked.connect(self.customer_manager.open_add)
        self.btnThemNCC.clicked.connect(self.supplier_manager.open_add)


    def mo_trang_tong_quan(self):
        self.stackedWidget.setCurrentIndex(0)
        self.overview_manager.load_recent_orders()

    def mo_trang_don_hang(self):
        self.stackedWidget.setCurrentIndex(1) # Trang Đơn hàng
        self.order_manager.load_data()

    def mo_trang_san_pham(self):
        # Chuyển đến index của trang Sản phẩm và load dữ liệu
        self.stackedWidget.setCurrentIndex(2)       
        self.product_manager.load_data()

    def mo_trang_danh_muc(self):
        # Hàm vừa chuyển trang vừa yêu cầu manager nạp dữ liệu mới nhất
        self.stackedWidget.setCurrentIndex(3)
        self.category_manager.load_data()

    def mo_trang_kho_hang(self):
        self.stackedWidget.setCurrentIndex(4) # Trang Kho hàng là index 4
        self.inventory_manager.load_data()

    def mo_trang_nha_cung_cap(self):
        self.stackedWidget.setCurrentIndex(5) # Trang Nhà cung cấp  là index 5
        self.supplier_manager.load_data()

    def mo_trang_khach_hang(self):
        self.stackedWidget.setCurrentIndex(6) # Trang Khách hàng (index 6)
        self.customer_manager.load_data()

if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    sys.exit(app.exec())