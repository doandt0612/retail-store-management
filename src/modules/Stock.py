import os
from PyQt6 import uic, QtWidgets, QtCore
from datetime import datetime
from src.database.db_connection import DatabaseManager 

# Thiết lập đường dẫn gốc
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(os.path.dirname(CURRENT_DIR))
UI_PATH = os.path.join(ROOT_DIR, "ui")

# LỚP CẬP NHẬT TỒN KHO 
class UpdateInventory(QtWidgets.QDialog):
    def __init__(self, data):
        super().__init__()
        uic.loadUi(os.path.join(UI_PATH, "updateKho.ui"), self)
        
        self.product_id = data['id']
        
        if hasattr(self, 'spnSoLuong'):
            self.spnSoLuongTonKho.setValue(int(data['qty']))
        
        # Kết nối sự kiện lưu
        self.btnLuu.clicked.connect(self.update_data)
        self.btnHuy.clicked.connect(self.reject)

    def update_data(self):
        """Cập nhật số lượng, tự động chỉnh Trạng thái và Ngày nhập"""
        new_qty = self.spnSoLuongTonKho.value()
        
        # Ràng buộc số lượng không được âm theo CHK_Stock_Quantity
        if new_qty < 0:
            QtWidgets.QMessageBox.warning(self, "Lỗi", "Số lượng tồn kho không được âm!")
            return

        # Tự động xác định trạng thái theo CHK_Product_Status
        new_status = "Còn hàng" if new_qty > 0 else "Hết hàng"
        
        # Lấy ngày hiện tại làm ngày nhập kho mới nhất
        current_date = datetime.now().strftime('%Y-%m-%d')

        db = DatabaseManager()
        conn = db.get_connection()
        if not conn: return
        
        try:
            cursor = conn.cursor()
            # Cập nhật 3 trường dữ liệu kho hàng trong bảng PRODUCTS
            cursor.execute("""
                UPDATE PRODUCTS 
                SET STOCK_QUANTITY = ?, PRODUCT_STATUS = ?, LAST_IMPORT_DATE = ? 
                WHERE PRODUCT_ID = ?
            """, (new_qty, new_status, current_date, self.product_id))
            
            conn.commit()
            QtWidgets.QMessageBox.information(self, "Thành công", f"Đã cập nhật tồn kho cho {self.product_id}!")
            self.accept()
        except Exception as e:
            conn.rollback()
            QtWidgets.QMessageBox.critical(self, "Lỗi", f"Lỗi hệ thống: {str(e)}")
        finally:
            conn.close()


# BỘ QUẢN LÝ KHO HÀNG
class InventoryManager:
    def __init__(self, table_widget):
        self.table = table_widget
        self.init_ui_style()

    def init_ui_style(self):
        """Cấu hình bảng chuyên nghiệp"""
        self.table.verticalHeader().setVisible(False)
        header = self.table.horizontalHeader()
        
        header.setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(3, QtWidgets.QHeaderView.ResizeMode.ResizeToContents) # Ngày nhập
        
        header.setSectionResizeMode(5, QtWidgets.QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(5, 120) 

        self.table.setStyleSheet("""
            QTableWidget { 
                gridline-color: #e5e7eb; 
                selection-background-color: #dbeafe; 
                selection-color: #1e40af; 
                alternate-background-color: #f9fafb;
            }
            QHeaderView::section { 
                background-color: #f8fafc; 
                padding: 6px; 
                font-weight: bold; 
                border-bottom: 2px solid #e2e8f0; 
            }
        """)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows)

    def load_data(self):
        """Nạp dữ liệu kho hàng từ bảng PRODUCTS"""
        db = DatabaseManager()
        conn = db.get_connection()
        if not conn: return
        
        cursor = conn.cursor()
        # Chỉ lấy các cột liên quan đến kho hàng
        cursor.execute("""
            SELECT PRODUCT_ID, PRODUCT_NAME, STOCK_QUANTITY, LAST_IMPORT_DATE, PRODUCT_STATUS 
            FROM PRODUCTS
        """)
        rows = cursor.fetchall()
        
        self.table.setRowCount(0)
        
        for row_idx, row_data in enumerate(rows):
            self.table.insertRow(row_idx)
            
            self.table.setItem(row_idx, 0, QtWidgets.QTableWidgetItem(str(row_data[0]))) # Mã SP
            self.table.setItem(row_idx, 1, QtWidgets.QTableWidgetItem(row_data[1]))      # Tên SP
            self.table.setItem(row_idx, 2, QtWidgets.QTableWidgetItem(str(row_data[2]))) # Tồn kho
            
            # Xử lý ngày nhập (tránh lỗi None nếu sản phẩm chưa nhập bao giờ)
            date_str = str(row_data[3]) if row_data[3] else "Chưa nhập kho"
            self.table.setItem(row_idx, 3, QtWidgets.QTableWidgetItem(date_str))         # Ngày nhập
            
            self.table.setItem(row_idx, 4, QtWidgets.QTableWidgetItem(row_data[4]))      # Trạng thái
            
            # Đóng gói dữ liệu để gửi sang Dialog Cập nhật
            item_dict = {
                "id": row_data[0], 
                "name": row_data[1], 
                "qty": row_data[2]
            }
            self.add_update_button(row_idx, item_dict)

        conn.close()

    def add_update_button(self, row, item):
        """Tạo nút Cập nhật"""
        container = QtWidgets.QWidget()
        layout = QtWidgets.QHBoxLayout(container)
        layout.setContentsMargins(10, 2, 10, 2)

        btn_edit = QtWidgets.QPushButton("Cập nhật")
        
        btn_style = """
            QPushButton {
                background-color: #3b82f6; color: white; padding: 4px; 
                font-weight: bold; border-radius: 3px; border: none;
            }
            QPushButton:hover { background-color: #2563eb; }
        """
        btn_edit.setStyleSheet(btn_style)
        btn_edit.clicked.connect(lambda: self.open_update(item))

        layout.addWidget(btn_edit)
        self.table.setCellWidget(row, 5, container)

    def open_update(self, item):
        dialog = UpdateInventory(item)
        if dialog.exec():
            self.load_data() # Load lại bảng sau khi cập nhật thành công