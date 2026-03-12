import os
from PyQt6 import uic, QtWidgets, QtCore
from src.database.db_connection import DatabaseManager

# Thiết lập đường dẫn gốc
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(os.path.dirname(CURRENT_DIR))
UI_PATH = os.path.join(ROOT_DIR, "ui")

# --- DIALOG XÁC NHẬN XÓA HÓA ĐƠN ---
class DeleteInvoice(QtWidgets.QDialog):
    def __init__(self, invoice_id):
        super().__init__()
        # Sử dụng giao diện xóa chung
        uic.loadUi(os.path.join(UI_PATH, "deleteDonHang.ui"), self) 
        
        self.invoice_id = invoice_id
        if hasattr(self, 'lblCanhBao'):
            self.lblCanhBao.setText(f"Bạn có chắc muốn xóa hóa đơn: {self.invoice_id}?\nHành động này không thể hoàn tác.")
        
        self.btnXoa.clicked.connect(self.confirm_delete)
        self.btnHuy.clicked.connect(self.reject)

    def confirm_delete(self):
        db = DatabaseManager()
        conn = db.get_connection()
        if not conn: return
        
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM INVOICES WHERE INVOICE_ID = ?", (self.invoice_id,))
            conn.commit()
            QtWidgets.QMessageBox.information(self, "Thành công", f"Đã xóa hóa đơn {self.invoice_id}!")
            self.accept()
        except Exception as e:
            conn.rollback()
            QtWidgets.QMessageBox.critical(self, "Lỗi", f"Lỗi hệ thống: {str(e)}")
        finally:
            conn.close()

# --- BỘ QUẢN LÝ TRANG HÓA ĐƠN (CÓ PHÂN TRANG) ---
class InvoiceManager:
    def __init__(self, table_widget, btn_prev, btn_next, lbl_status):
        self.table = table_widget
        self.btn_prev = btn_prev
        self.btn_next = btn_next
        self.lbl_status = lbl_status
        
        # Cấu hình phân trang (5 dòng mỗi trang)
        self.current_page = 0
        self.items_per_page = 5
        self.all_data = [] 
        
        self.init_ui_style()
        self.connect_events()

    def init_ui_style(self):
        """Cấu hình bảng tblHoaDon"""
        self.table.verticalHeader().setVisible(False)
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(3, QtWidgets.QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(3, 110)

        self.table.setStyleSheet("""
            QTableWidget { gridline-color: #e5e7eb; alternate-background-color: #f9fafb; }
            QHeaderView::section { background-color: #f8fafc; padding: 6px; font-weight: bold; border-bottom: 2px solid #e2e8f0; }
        """)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows)

    def connect_events(self):
        """Kết nối sự kiện cho các nút điều hướng"""
        # Đảm bảo các nút tồn tại trước khi gán sự kiện
        if self.btn_prev:
            self.btn_prev.clicked.connect(self.prev_page)
        if self.btn_next:
            self.btn_next.clicked.connect(self.next_page)

    def load_data(self):
        """Tải toàn bộ dữ liệu từ SQL và reset về trang đầu tiên"""
        db = DatabaseManager()
        conn = db.get_connection()
        if not conn: return
        
        try:
            cursor = conn.cursor()
            # Lấy toàn bộ hóa đơn để thực hiện phân trang tại chỗ (In-memory pagination)
            cursor.execute("SELECT INVOICE_ID, ORDER_ID, PAYMENT_TIME FROM INVOICES ORDER BY INVOICE_ID DESC")
            self.all_data = cursor.fetchall()
            
            # Quay về trang đầu tiên mỗi khi tải lại dữ liệu mới
            self.current_page = 0
            self.render_page()
            
        except Exception as e:
            print(f"Lỗi load data Invoice: {e}")
        finally:
            conn.close()

    def render_page(self):
        """Vẽ dữ liệu lên bảng dựa trên số trang hiện tại"""
        if not self.table: return
        
        self.table.setRowCount(0)
        total_items = len(self.all_data)
        
        # Tính toán dải dữ liệu
        start_idx = self.current_page * self.items_per_page
        end_idx = start_idx + self.items_per_page
        page_data = self.all_data[start_idx:end_idx]
        
        # Đưa dữ liệu vào bảng
        for row_idx, row_data in enumerate(page_data):
            self.table.insertRow(row_idx)
            self.table.setItem(row_idx, 0, QtWidgets.QTableWidgetItem(str(row_data[0])))
            self.table.setItem(row_idx, 1, QtWidgets.QTableWidgetItem(str(row_data[1])))
            
            date_val = str(row_data[2]) if row_data[2] else "N/A"
            self.table.setItem(row_idx, 2, QtWidgets.QTableWidgetItem(date_val))
            
            self.add_delete_button(row_idx, str(row_data[0]))
            
        # Cập nhật thông tin hiển thị (Ví dụ: Hiển thị 5 / 12 hóa đơn)
        if self.lbl_status:
            showing = len(page_data)
            self.lbl_status.setText(f"Hiển thị {showing} / {total_items} hóa đơn")
        
        # QUAN TRỌNG: Cập nhật trạng thái nút bấm (Enable/Disable)
        if self.btn_prev:
            self.btn_prev.setEnabled(self.current_page > 0)
        if self.btn_next:
            self.btn_next.setEnabled(end_idx < total_items)

    def add_delete_button(self, row, invoice_id):
        """Tạo nút Xóa cho mỗi dòng"""
        container = QtWidgets.QWidget()
        layout = QtWidgets.QHBoxLayout(container)
        layout.setContentsMargins(10, 2, 10, 2)

        btn_delete = QtWidgets.QPushButton("Xóa")
        btn_delete.setStyleSheet("""
            QPushButton {
                background-color: #ef4444; color: white; padding: 4px; 
                font-weight: bold; border-radius: 3px; border: none;
            }
            QPushButton:hover { background-color: #dc2626; }
        """)
        btn_delete.clicked.connect(lambda: self.open_delete(invoice_id))

        layout.addWidget(btn_delete)
        self.table.setCellWidget(row, 3, container)

    def next_page(self):
        """Chuyển sang trang sau"""
        if (self.current_page + 1) * self.items_per_page < len(self.all_data):
            self.current_page += 1
            self.render_page()

    def prev_page(self):
        """Quay lại trang trước"""
        if self.current_page > 0:
            self.current_page -= 1
            self.render_page()

    def open_delete(self, invoice_id):
        """Mở dialog xóa và tải lại dữ liệu"""
        dialog = DeleteInvoice(invoice_id)
        if dialog.exec():
            self.load_data()