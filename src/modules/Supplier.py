import os
from PyQt6 import uic, QtWidgets, QtCore
from src.database.db_connection import DatabaseManager 

# Thiết lập đường dẫn gốc
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(os.path.dirname(CURRENT_DIR))
UI_PATH = os.path.join(ROOT_DIR, "ui")

# CÁC DIALOG CHỨC NĂNG

class AddSupplier(QtWidgets.QDialog):
    def __init__(self):
        super().__init__()
        uic.loadUi(os.path.join(UI_PATH, "addNCC.ui"), self)
        
        # Đảm bảo nút của bạn tên là btnLuu và btnHuy trong Qt Designer
        self.btnLuu.clicked.connect(self.save_data)
        self.btnHuy.clicked.connect(self.reject)

    def save_data(self):
        ten_ncc = self.txtTenNCC.text().strip()
        sdt = self.txtSDTNCC.text().strip()
        dia_chi = self.txtDiaChiNCC.text().strip() 
        
        if not ten_ncc or not sdt:
            QtWidgets.QMessageBox.warning(self, "Lỗi", "Vui lòng nhập Tên và Số điện thoại!")
            return
            
        db = DatabaseManager()
        conn = db.get_connection()
        if not conn: return
        
        try:
            cursor = conn.cursor()
            
            # Tự động tạo mã (VD: SUP11)
            cursor.execute("SELECT MAX(SUPPLIER_ID) FROM SUPPLIERS")
            last_id = cursor.fetchone()[0]
            if not last_id:
                new_id = "SUP01"
            else:
                current_num = int(last_id.replace("SUP", ""))
                new_id = f"SUP{current_num + 1:02d}"
            
            cursor.execute("INSERT INTO SUPPLIERS (SUPPLIER_ID, SUPPLIER_NAME, SUPPLIER_PHONE, SUPPLIER_ADDRESS) VALUES (?, ?, ?, ?)", 
                           (new_id, ten_ncc, sdt, dia_chi))
            conn.commit()
            
            QtWidgets.QMessageBox.information(self, "Thành công", "Thêm nhà cung cấp thành công!")
            self.accept()
        except Exception as e:
            conn.rollback()
            QtWidgets.QMessageBox.critical(self, "Lỗi", f"Lỗi hệ thống: {str(e)}")
        finally:
            conn.close()

class EditSupplier(QtWidgets.QDialog):
    def __init__(self, data):
        super().__init__()
        uic.loadUi(os.path.join(UI_PATH, "editNCC.ui"), self)
        
        self.supplier_id = data['id']
        
        # Điền dữ liệu cũ lên giao diện
        self.txtTenNCC.setText(data['ten'])
        self.txtSDTNCC.setText(data['sdt'])
        self.txtDiaChiNCC.setText(data['dc']) 
        
        self.btnLuu.clicked.connect(self.update_data)
        self.btnHuy.clicked.connect(self.reject)

    def update_data(self):
        ten_ncc = self.txtTenNCC.text().strip()
        sdt = self.txtSDTNCC.text().strip()
        dia_chi = self.txtDiaChiNCC.text().strip()
        
        if not ten_ncc:
            QtWidgets.QMessageBox.warning(self, "Lỗi", "Tên nhà cung cấp không được để trống!")
            return
            
        db = DatabaseManager()
        conn = db.get_connection()
        if not conn: return
        
        try:
            cursor = conn.cursor()
            cursor.execute("UPDATE SUPPLIERS SET SUPPLIER_NAME = ?, SUPPLIER_PHONE = ?, SUPPLIER_ADDRESS = ? WHERE SUPPLIER_ID = ?", 
                           (ten_ncc, sdt, dia_chi, self.supplier_id))
            conn.commit()
            QtWidgets.QMessageBox.information(self, "Thành công", "Cập nhật thành công!")
            self.accept()
        except Exception as e:
            conn.rollback()
            QtWidgets.QMessageBox.critical(self, "Lỗi", f"Lỗi hệ thống: {str(e)}")
        finally:
            conn.close()

class DeleteSupplier(QtWidgets.QDialog):
    def __init__(self, data):
        super().__init__()
        uic.loadUi(os.path.join(UI_PATH, "deleteNCC.ui"), self)
        
        self.supplier_id = data['id']
        self.supplier_name = data['ten']
        
        self.lblCanhBao.setText(f"Bạn có chắc muốn xóa nhà cung cấp:\n{self.supplier_name}?")
        
        self.btnXoa.clicked.connect(self.delete_data)
        self.btnHuy.clicked.connect(self.reject)

    def delete_data(self):
        db = DatabaseManager()
        conn = db.get_connection()
        if not conn: return
        
        try:
            cursor = conn.cursor()
            
            # KIỂM TRA RÀNG BUỘC KHÓA NGOẠI TỪ BẢNG PRODUCTS
            cursor.execute("SELECT COUNT(*) FROM PRODUCTS WHERE SUPPLIER_ID = ?", (self.supplier_id,))
            if cursor.fetchone()[0] > 0:
                QtWidgets.QMessageBox.warning(self, "Từ chối xóa", 
                    f"Không thể xóa '{self.supplier_name}' vì đang cung cấp sản phẩm cho cửa hàng!")
                return
                
            cursor.execute("DELETE FROM SUPPLIERS WHERE SUPPLIER_ID = ?", (self.supplier_id,))
            conn.commit()
            QtWidgets.QMessageBox.information(self, "Thành công", "Đã xóa nhà cung cấp!")
            self.accept()
        except Exception as e:
            conn.rollback()
            QtWidgets.QMessageBox.critical(self, "Lỗi", f"Lỗi hệ thống: {str(e)}")
        finally:
            conn.close()

# BỘ QUẢN LÝ NHÀ CUNG CẤP
class SupplierManager:
    def __init__(self, table_widget):
        self.table = table_widget
        self.init_ui_style()

    def init_ui_style(self):
        """Cấu hình bảng chuyên nghiệp"""
        self.table.verticalHeader().setVisible(False)
        header = self.table.horizontalHeader()
        
        header.setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeMode.ResizeToContents) 
        header.setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeMode.Stretch)          
        header.setSectionResizeMode(3, QtWidgets.QHeaderView.ResizeMode.Stretch)          
        header.setSectionResizeMode(4, QtWidgets.QHeaderView.ResizeMode.ResizeToContents) 
        
        header.setSectionResizeMode(5, QtWidgets.QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(5, 160) 

        self.table.setStyleSheet("""
            QTableWidget { gridline-color: #e5e7eb; selection-background-color: #dbeafe; selection-color: #1e40af; alternate-background-color: #f9fafb; }
            QHeaderView::section { background-color: #f8fafc; padding: 5px; font-weight: bold; font-size: 13px; border-bottom: 2px solid #e2e8f0; }
        """)      
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows)

    def load_data(self):
        """Truy vấn dữ liệu và đếm số lượng sản phẩm bằng LEFT JOIN"""
        db = DatabaseManager()
        conn = db.get_connection()
        if not conn: return
        
        cursor = conn.cursor()
        query = """
            SELECT S.SUPPLIER_ID, S.SUPPLIER_NAME, S.SUPPLIER_PHONE, S.SUPPLIER_ADDRESS, COUNT(P.PRODUCT_ID) AS PRODUCT_COUNT
            FROM SUPPLIERS S
            LEFT JOIN PRODUCTS P ON S.SUPPLIER_ID = P.SUPPLIER_ID
            GROUP BY S.SUPPLIER_ID, S.SUPPLIER_NAME, S.SUPPLIER_PHONE, S.SUPPLIER_ADDRESS
        """
        cursor.execute(query)
        rows = cursor.fetchall()
        
        self.table.setRowCount(0)
        for row_idx, row_data in enumerate(rows):
            self.table.insertRow(row_idx)
            
            self.table.setItem(row_idx, 0, QtWidgets.QTableWidgetItem(str(row_data[0])))
            self.table.setItem(row_idx, 1, QtWidgets.QTableWidgetItem(row_data[1]))
            self.table.setItem(row_idx, 2, QtWidgets.QTableWidgetItem(row_data[2]))
            self.table.setItem(row_idx, 3, QtWidgets.QTableWidgetItem(row_data[3]))
            self.table.setItem(row_idx, 4, QtWidgets.QTableWidgetItem(str(row_data[4]))) 
            
            item_dict = {"id": row_data[0], "ten": row_data[1], "sdt": row_data[2], "dc": row_data[3]}
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
        self.table.setCellWidget(row, 5, container)

    def open_add(self):
        if AddSupplier().exec(): 
            self.load_data()

    def open_edit(self, item):
        if EditSupplier(item).exec(): 
            self.load_data()

    def open_delete(self, item):
        if DeleteSupplier(item).exec(): 
            self.load_data()