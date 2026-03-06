import os
from PyQt6 import uic, QtWidgets, QtCore
from datetime import datetime
from src.database.db_connection import DatabaseManager # Đảm bảo import DatabaseManager

# Thiết lập đường dẫn gốc
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(os.path.dirname(CURRENT_DIR))
UI_PATH = os.path.join(ROOT_DIR, "ui")

# CÁC DIALOG CHỨC NĂNG
class AddProduct(QtWidgets.QDialog):
    def __init__(self):
        super().__init__()
        uic.loadUi(os.path.join(UI_PATH, "addSP.ui"), self)
        
        # Nạp dữ liệu vào ComboBox ngay khi mở Dialog
        self.load_combobox_data()
        
        # Kết nối nút bấm
        self.btnLuu.clicked.connect(self.save_data)
        self.btnHuy.clicked.connect(self.reject)

    def load_combobox_data(self):
        """Nạp danh mục và nhà cung cấp vào ComboBox"""
        db = DatabaseManager()
        conn = db.get_connection()
        if not conn: return
        
        cursor = conn.cursor()
        
        # Nạp Danh mục
        cursor.execute("SELECT CATEGORY_ID, CATEGORY_NAME FROM CATEGORIES")
        self.cbDanhMuc.clear()
        for cid, cname in cursor.fetchall():
            self.cbDanhMuc.addItem(cname, cid) # Lưu ID ẩn bên dưới
            
        # Nạp Nhà cung cấp
        cursor.execute("SELECT SUPPLIER_ID, SUPPLIER_NAME FROM SUPPLIERS")
        self.cbNCC.clear()
        for sid, sname in cursor.fetchall():
            self.cbNCC.addItem(sname, sid)
            
        conn.close()

    def save_data(self):
        # Lấy dữ liệu từ các widget chuẩn xác theo hình bạn gửi
        ten_sp = self.txtTenSP.text().strip()
        gia_str = self.txtGia.text().strip()
        so_luong = self.spnSoLuong.value()
        cat_id = self.cbDanhMuc.currentData()
        sup_id = self.cbNCC.currentData()
        
        if not ten_sp or not gia_str:
            QtWidgets.QMessageBox.warning(self, "Lỗi", "Vui lòng nhập Tên sản phẩm và Giá!")
            return
            
        # Xử lý chuỗi giá tiền (đề phòng người dùng nhập 25.000 hoặc 25,000)
        try:
            gia_tien = float(gia_str.replace(",", "").replace(".", ""))
            if gia_tien <= 0:
                QtWidgets.QMessageBox.warning(self, "Lỗi", "Giá sản phẩm phải lớn hơn 0!") #
                return
        except ValueError:
            QtWidgets.QMessageBox.warning(self, "Lỗi", "Giá sản phẩm phải là số hợp lệ!")
            return

        # Tự động gán trạng thái dựa trên số lượng
        trang_thai = "Còn hàng" if so_luong > 0 else "Hết hàng"
        ngay_nhap = datetime.now().strftime('%Y-%m-%d') if so_luong > 0 else None

        db = DatabaseManager()
        conn = db.get_connection()
        if not conn: return
        
        try:
            cursor = conn.cursor()
            
            # Tự động tạo mã (VD: PRO11)
            cursor.execute("SELECT MAX(PRODUCT_ID) FROM PRODUCTS")
            last_id = cursor.fetchone()[0]
            if not last_id:
                new_id = "PRO01"
            else:
                current_num = int(last_id.replace("PRO", ""))
                new_id = f"PRO{current_num + 1:02d}"
            
            # Insert vào database
            cursor.execute("""
                INSERT INTO PRODUCTS (PRODUCT_ID, PRODUCT_NAME, UNIT_PRICE, STOCK_QUANTITY, PRODUCT_STATUS, LAST_IMPORT_DATE, CATEGORY_ID, SUPPLIER_ID) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (new_id, ten_sp, gia_tien, so_luong, trang_thai, ngay_nhap, cat_id, sup_id))
            
            conn.commit()
            QtWidgets.QMessageBox.information(self, "Thành công", "Thêm sản phẩm thành công!")
            self.accept()
        except Exception as e:
            conn.rollback()
            QtWidgets.QMessageBox.critical(self, "Lỗi", f"Lỗi hệ thống: {str(e)}")
        finally:
            conn.close()

# LỚP SỬA & XÓA 
class EditProduct(QtWidgets.QDialog):
    def __init__(self, data):
        super().__init__()
        uic.loadUi(os.path.join(UI_PATH, "editSP.ui"), self)
        
        self.product_id = data['id'] # Lấy ID sản phẩm từ bảng truyền sang
        
        # 1. Nạp danh sách vào ComboBox trước
        self.load_combobox_data()
        
        # 2. Lấy dữ liệu chi tiết của sản phẩm để điền lên form
        self.load_product_data()
        
        self.btnLuu.clicked.connect(self.update_data)
        self.btnHuy.clicked.connect(self.reject)

    def load_combobox_data(self):
        """Nạp danh mục và nhà cung cấp vào ComboBox (Giống hệt hàm AddProduct)"""
        db = DatabaseManager()
        conn = db.get_connection()
        if not conn: return
        cursor = conn.cursor()
        
        cursor.execute("SELECT CATEGORY_ID, CATEGORY_NAME FROM CATEGORIES")
        self.cbDanhMuc.clear()
        for cid, cname in cursor.fetchall():
            self.cbDanhMuc.addItem(cname, cid) 
            
        cursor.execute("SELECT SUPPLIER_ID, SUPPLIER_NAME FROM SUPPLIERS")
        self.cbNCC.clear()
        for sid, sname in cursor.fetchall():
            self.cbNCC.addItem(sname, sid)
        conn.close()

    def load_product_data(self):
        """Truy vấn dữ liệu cũ và đưa lên giao diện"""
        db = DatabaseManager()
        conn = db.get_connection()
        if not conn: return
        
        cursor = conn.cursor()
        cursor.execute("""
            SELECT PRODUCT_NAME, UNIT_PRICE, STOCK_QUANTITY, CATEGORY_ID, SUPPLIER_ID 
            FROM PRODUCTS WHERE PRODUCT_ID = ?
        """, (self.product_id,))
        row = cursor.fetchone() #
        
        if row:
            self.txtTenSP.setText(row[0])
            self.txtGia.setText(f"{row[1]:,.0f}") # Format giá có dấu phẩy
            self.spnSoLuong.setValue(int(row[2]))
            
            # Cực kỳ quan trọng: Tìm vị trí (index) của Danh mục và NCC cũ để tự động chọn đúng
            cat_index = self.cbDanhMuc.findData(row[3])
            if cat_index >= 0:
                self.cbDanhMuc.setCurrentIndex(cat_index)
                
            sup_index = self.cbNCC.findData(row[4])
            if sup_index >= 0:
                self.cbNCC.setCurrentIndex(sup_index)
                
        conn.close()

    def update_data(self):
        """Lưu các thay đổi xuống DB"""
        ten_sp = self.txtTenSP.text().strip()
        gia_str = self.txtGia.text().strip()
        so_luong = self.spnSoLuong.value()
        cat_id = self.cbDanhMuc.currentData()
        sup_id = self.cbNCC.currentData()
        
        if not ten_sp or not gia_str:
            QtWidgets.QMessageBox.warning(self, "Lỗi", "Vui lòng nhập Tên sản phẩm và Giá!")
            return
            
        try:
            gia_tien = float(gia_str.replace(",", "").replace(".", ""))
            if gia_tien <= 0:
                QtWidgets.QMessageBox.warning(self, "Lỗi", "Giá sản phẩm phải lớn hơn 0!")
                return
        except ValueError:
            QtWidgets.QMessageBox.warning(self, "Lỗi", "Giá sản phẩm không hợp lệ!")
            return

        # Tự động gán lại trạng thái nếu số lượng bị chỉnh sửa
        trang_thai = "Còn hàng" if so_luong > 0 else "Hết hàng"

        from src.database.db_connection import DatabaseManager
        db = DatabaseManager()
        conn = db.get_connection()
        if not conn: return
        
        try:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE PRODUCTS 
                SET PRODUCT_NAME = ?, UNIT_PRICE = ?, STOCK_QUANTITY = ?, 
                    PRODUCT_STATUS = ?, CATEGORY_ID = ?, SUPPLIER_ID = ?
                WHERE PRODUCT_ID = ?
            """, (ten_sp, gia_tien, so_luong, trang_thai, cat_id, sup_id, self.product_id)) #
            
            conn.commit()
            QtWidgets.QMessageBox.information(self, "Thành công", "Đã cập nhật sản phẩm!")
            self.accept()
        except Exception as e:
            conn.rollback()
            QtWidgets.QMessageBox.critical(self, "Lỗi", f"Lỗi hệ thống: {str(e)}")
        finally:
            conn.close()


class DeleteProduct(QtWidgets.QDialog):
    def __init__(self, data):
        super().__init__()
        uic.loadUi(os.path.join(UI_PATH, "deleteSP.ui"), self)
        
        self.product_id = data['id']
        self.product_name = data['ten']
        
        # Nếu bạn có label thông báo trong file UI
        if hasattr(self, 'lblThongBao'):
            self.lblThongBao.setText(f"Bạn có chắc muốn xóa sản phẩm:\n{self.product_name}?")
            
        self.btnXoa.clicked.connect(self.delete_data)
        self.btnHuy.clicked.connect(self.reject)

    def delete_data(self):
        """Xóa sản phẩm với cơ chế bảo vệ toàn vẹn dữ liệu"""
        from src.database.db_connection import DatabaseManager
        db = DatabaseManager()
        conn = db.get_connection()
        if not conn: return
        
        try:
            cursor = conn.cursor()
            
            # BẢO VỆ TOÀN VẸN DỮ LIỆU: Kiểm tra xem sản phẩm đã có ai mua (nằm trong đơn hàng) chưa?
            cursor.execute("SELECT COUNT(*) FROM ORDERDETAILS WHERE PRODUCT_ID = ?", (self.product_id,))
            if cursor.fetchone()[0] > 0:
                QtWidgets.QMessageBox.warning(self, "Từ chối xóa", 
                    f"Không thể xóa '{self.product_name}' vì sản phẩm này đã tồn tại trong lịch sử Đơn hàng. Bạn chỉ có thể cập nhật số lượng về 0!")
                return
                
            cursor.execute("DELETE FROM PRODUCTS WHERE PRODUCT_ID = ?", (self.product_id,))
            conn.commit()
            
            QtWidgets.QMessageBox.information(self, "Thành công", "Đã xóa sản phẩm khỏi hệ thống!")
            self.accept()
        except Exception as e:
            conn.rollback()
            QtWidgets.QMessageBox.critical(self, "Lỗi", f"Lỗi hệ thống: {str(e)}")
        finally:
            conn.close()

class DeleteProduct(QtWidgets.QDialog):
    def __init__(self, data):
        super().__init__()
        uic.loadUi(os.path.join(UI_PATH, "deleteSP.ui"), self)
        # Sẽ code logic xóa sau
        self.btnXoa.clicked.connect(self.accept)
        self.btnHuy.clicked.connect(self.reject)

# BỘ QUẢN LÝ SẢN PHẨM
class ProductManager:
    # 1. Nhận thêm 2 tham số là 2 ComboBox từ giao diện
    def __init__(self, table_widget, search_box=None, cb_category=None, cb_supplier=None):
        self.table = table_widget
        self.search_box = search_box
        self.cb_category = cb_category
        self.cb_supplier = cb_supplier
        
        self.init_ui_style()
        
        # BẮT BUỘC nạp dữ liệu ComboBox TRƯỚC KHI kết nối sự kiện
        self.init_filter_comboboxes()

        # Kết nối sự kiện lọc realtime
        if self.search_box:
            self.search_box.textChanged.connect(self.filter_data)
        if self.cb_category:
            self.cb_category.currentIndexChanged.connect(self.filter_data)
        if self.cb_supplier:
            self.cb_supplier.currentIndexChanged.connect(self.filter_data)

    def init_filter_comboboxes(self):
        """Nạp danh sách từ SQL vào 2 ComboBox lọc"""
        
        db = DatabaseManager()
        conn = db.get_connection()
        if not conn: 
            return
        
        cursor = conn.cursor()
        
        # Nạp Danh mục
        if self.cb_category is not None:
            self.cb_category.clear()
            self.cb_category.addItem("Tất cả Danh mục", "")
            cursor.execute("SELECT CATEGORY_ID, CATEGORY_NAME FROM CATEGORIES")
            rows_cat = cursor.fetchall()
            for cid, cname in rows_cat:
                self.cb_category.addItem(cname, cid)
                
        # Nạp Nhà cung cấp
        if self.cb_supplier is not None:
            self.cb_supplier.clear()
            self.cb_supplier.addItem("Tất cả Nhà cung cấp", "")
            cursor.execute("SELECT SUPPLIER_ID, SUPPLIER_NAME FROM SUPPLIERS")
            rows_sup = cursor.fetchall()
            for sid, sname in rows_sup:
                self.cb_supplier.addItem(sname, sid)
                
        conn.close()

    def filter_data(self):
        """Lọc đa năng: Siêu an toàn (Bỏ qua hoa thường và khoảng trắng thừa)"""
        # Lấy và chuẩn hóa từ khóa tìm kiếm
        search_text = self.search_box.text().lower().strip() if self.search_box is not None else ""
        
        # Lấy và chuẩn hóa giá trị đang được chọn trong ComboBox
        selected_cat = self.cb_category.currentText().lower().strip() if self.cb_category is not None and self.cb_category.currentIndex() > 0 else ""
        selected_sup = self.cb_supplier.currentText().lower().strip() if self.cb_supplier is not None and self.cb_supplier.currentIndex() > 0 else ""
        
        for row in range(self.table.rowCount()):
            # Quét tìm kiếm chữ/số trên TOÀN BỘ 6 CỘT
            match_text = False
            if not search_text:
                match_text = True
            else:
                for col in range(6): 
                    item = self.table.item(row, col)
                    if item:
                        # Chuẩn hóa dữ liệu trong từng ô của bảng
                        cell_text = item.text().lower().strip()
                        cell_raw_number = cell_text.replace(",", "").replace(" vnđ", "")
                        
                        if search_text in cell_text or search_text in cell_raw_number:
                            match_text = True
                            break 

            # Kiểm tra Danh mục và Nhà cung cấp
            item_cat = self.table.item(row, 2)
            item_sup = self.table.item(row, 4)
            
            # Chuẩn hóa dữ liệu nằm trong cột Danh mục (cột 2) và NCC (cột 4)
            val_cat = item_cat.text().lower().strip() if item_cat else ""
            val_sup = item_sup.text().lower().strip() if item_sup else ""
            
            # So sánh 2 giá trị đã được chuẩn hóa
            match_cat = (selected_cat == "") or (selected_cat == val_cat)
            match_sup = (selected_sup == "") or (selected_sup == val_sup)
            
            # Nếu thỏa mãn TẤT CẢ, mới cho phép hiện hàng đó
            if match_text and match_cat and match_sup:
                self.table.setRowHidden(row, False)
            else:
                self.table.setRowHidden(row, True)

    def init_ui_style(self):
        """Cấu hình bảng"""
        self.table.verticalHeader().setVisible(False)
        header = self.table.horizontalHeader()
        
        header.setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(4, QtWidgets.QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(5, QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(6, QtWidgets.QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(6, 170) 

        # CSS đã được làm sạch
        self.table.setStyleSheet("""
            QTableWidget { gridline-color: #e5e7eb; selection-background-color: #dbeafe; selection-color: #1e40af; alternate-background-color: #f9fafb; }
            QHeaderView::section { background-color: #f8fafc; padding: 5px; font-weight: bold; font-size: 13px; border-bottom: 2px solid #e2e8f0; }
        """)      
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows)


    def load_data(self):
        """Dùng JOIN để lấy tên Danh mục và Nhà cung cấp thay vì ID""" 
        db = DatabaseManager()
        conn = db.get_connection()
        if not conn: return
        
        cursor = conn.cursor()
        query = """
            SELECT P.PRODUCT_ID, P.PRODUCT_NAME, C.CATEGORY_NAME, P.UNIT_PRICE, S.SUPPLIER_NAME, P.PRODUCT_STATUS
            FROM PRODUCTS P
            JOIN CATEGORIES C ON P.CATEGORY_ID = C.CATEGORY_ID
            JOIN SUPPLIERS S ON P.SUPPLIER_ID = S.SUPPLIER_ID
        """ #
        cursor.execute(query)
        rows = cursor.fetchall()
        
        self.table.setRowCount(0)
        
        for row_idx, row_data in enumerate(rows):
            self.table.insertRow(row_idx)
            
            self.table.setItem(row_idx, 0, QtWidgets.QTableWidgetItem(str(row_data[0])))
            self.table.setItem(row_idx, 1, QtWidgets.QTableWidgetItem(row_data[1]))
            self.table.setItem(row_idx, 2, QtWidgets.QTableWidgetItem(row_data[2]))
            
            # Format giá tiền (VD: 25,000,000)
            gia = row_data[3] if row_data[3] else 0
            self.table.setItem(row_idx, 3, QtWidgets.QTableWidgetItem(f"{gia:,.0f} VNĐ"))
            
            self.table.setItem(row_idx, 4, QtWidgets.QTableWidgetItem(row_data[4]))
            self.table.setItem(row_idx, 5, QtWidgets.QTableWidgetItem(row_data[5]))
            
            item_dict = {"id": row_data[0], "ten": row_data[1]}
            self.add_action_buttons(row_idx, item_dict)
            
        conn.close()

    def add_action_buttons(self, row, item):
        container = QtWidgets.QWidget()
        layout = QtWidgets.QHBoxLayout(container)
        layout.setContentsMargins(4, 2, 4, 2)
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
        self.table.setCellWidget(row, 6, container)

    def open_add(self):
        if AddProduct().exec(): 
            self.load_data()

    def open_edit(self, item):
        if EditProduct(item).exec(): 
            self.load_data()

    def open_delete(self, item):
        if DeleteProduct(item).exec(): 
            self.load_data()