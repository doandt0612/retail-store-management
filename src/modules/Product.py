import os
from PyQt6 import uic, QtWidgets, QtCore
from datetime import datetime
from src.database.db_connection import DatabaseManager

# Thiết lập đường dẫn gốc
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(os.path.dirname(CURRENT_DIR))
UI_PATH = os.path.join(ROOT_DIR, "ui")

# --- DIALOG THÊM SẢN PHẨM ---
class AddProduct(QtWidgets.QDialog):
    def __init__(self):
        super().__init__()
        uic.loadUi(os.path.join(UI_PATH, "addSP.ui"), self)
        self.load_combobox_data()
        self.btnLuu.clicked.connect(self.save_data)
        self.btnHuy.clicked.connect(self.reject)

    def load_combobox_data(self):
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

    def save_data(self):
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
        except ValueError:
            QtWidgets.QMessageBox.warning(self, "Lỗi", "Giá sản phẩm không hợp lệ!")
            return

        trang_thai = "Còn hàng" if so_luong > 0 else "Hết hàng"
        ngay_nhap = datetime.now().strftime('%Y-%m-%d') if so_luong > 0 else None

        db = DatabaseManager()
        conn = db.get_connection()
        if not conn: return
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT MAX(PRODUCT_ID) FROM PRODUCTS")
            last_id = cursor.fetchone()[0]
            new_id = f"PRO{int(last_id.replace('PRO', '')) + 1:02d}" if last_id else "PRO01"
            
            cursor.execute("""
                INSERT INTO PRODUCTS (PRODUCT_ID, PRODUCT_NAME, UNIT_PRICE, STOCK_QUANTITY, PRODUCT_STATUS, LAST_IMPORT_DATE, CATEGORY_ID, SUPPLIER_ID) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (new_id, ten_sp, gia_tien, so_luong, trang_thai, ngay_nhap, cat_id, sup_id))
            conn.commit()
            self.accept()
        except Exception as e:
            conn.rollback()
            QtWidgets.QMessageBox.critical(self, "Lỗi", f"Lỗi: {str(e)}")
        finally:
            conn.close()

# --- DIALOG SỬA SẢN PHẨM ---
class EditProduct(QtWidgets.QDialog):
    def __init__(self, product_id):
        super().__init__()
        uic.loadUi(os.path.join(UI_PATH, "editSP.ui"), self)
        self.product_id = product_id
        self.load_combobox_data()
        self.load_product_data()
        self.btnLuu.clicked.connect(self.update_data)
        self.btnHuy.clicked.connect(self.reject)

    def load_combobox_data(self):
        db = DatabaseManager()
        conn = db.get_connection()
        if not conn: return
        cursor = conn.cursor()
        cursor.execute("SELECT CATEGORY_ID, CATEGORY_NAME FROM CATEGORIES")
        for cid, cname in cursor.fetchall(): self.cbDanhMuc.addItem(cname, cid)
        cursor.execute("SELECT SUPPLIER_ID, SUPPLIER_NAME FROM SUPPLIERS")
        for sid, sname in cursor.fetchall(): self.cbNCC.addItem(sname, sid)
        conn.close()

    def load_product_data(self):
        db = DatabaseManager()
        conn = db.get_connection()
        if not conn: return
        cursor = conn.cursor()
        cursor.execute("SELECT PRODUCT_NAME, UNIT_PRICE, STOCK_QUANTITY, CATEGORY_ID, SUPPLIER_ID FROM PRODUCTS WHERE PRODUCT_ID = ?", (self.product_id,))
        row = cursor.fetchone()
        if row:
            self.txtTenSP.setText(row[0])
            self.txtGia.setText(f"{row[1]:,.0f}")
            self.spnSoLuong.setValue(int(row[2]))
            self.cbDanhMuc.setCurrentIndex(self.cbDanhMuc.findData(row[3]))
            self.cbNCC.setCurrentIndex(self.cbNCC.findData(row[4]))
        conn.close()

    def update_data(self):
        ten_sp = self.txtTenSP.text().strip()
        gia_str = self.txtGia.text().strip()
        so_luong = self.spnSoLuong.value()
        cat_id = self.cbDanhMuc.currentData()
        sup_id = self.cbNCC.currentData()
        trang_thai = "Còn hàng" if so_luong > 0 else "Hết hàng"

        db = DatabaseManager()
        conn = db.get_connection()
        if not conn: return
        try:
            gia_tien = float(gia_str.replace(",", "").replace(".", ""))
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE PRODUCTS SET PRODUCT_NAME=?, UNIT_PRICE=?, STOCK_QUANTITY=?, PRODUCT_STATUS=?, CATEGORY_ID=?, SUPPLIER_ID=?
                WHERE PRODUCT_ID=?
            """, (ten_sp, gia_tien, so_luong, trang_thai, cat_id, sup_id, self.product_id))
            conn.commit()
            self.accept()
        except Exception as e:
            conn.rollback()
            QtWidgets.QMessageBox.critical(self, "Lỗi", str(e))
        finally:
            conn.close()

# --- DIALOG XÓA SẢN PHẨM ---
class DeleteProduct(QtWidgets.QDialog):
    def __init__(self, product_id, product_name):
        super().__init__()
        uic.loadUi(os.path.join(UI_PATH, "deleteSP.ui"), self)
        self.product_id = product_id
        if hasattr(self, 'lblThongBao'):
            self.lblThongBao.setText(f"Xóa sản phẩm: {product_name}?")
        self.btnXoa.clicked.connect(self.delete_data)
        self.btnHuy.clicked.connect(self.reject)

    def delete_data(self):
        db = DatabaseManager()
        conn = db.get_connection()
        if not conn: return
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM ORDERDETAILS WHERE PRODUCT_ID = ?", (self.product_id,))
            if cursor.fetchone()[0] > 0:
                QtWidgets.QMessageBox.warning(self, "Lỗi", "Sản phẩm đã có trong đơn hàng, không thể xóa!")
                return
            cursor.execute("DELETE FROM PRODUCTS WHERE PRODUCT_ID = ?", (self.product_id,))
            conn.commit()
            self.accept()
        except Exception as e:
            conn.rollback()
            QtWidgets.QMessageBox.critical(self, "Lỗi", str(e))
        finally:
            conn.close()

# --- BỘ QUẢN LÝ CHÍNH ---
class ProductManager:
    def __init__(self, table, btn_prev, btn_next, lbl_status, txt_search, cb_cat, cb_sup):
        self.table = table
        self.btn_prev = btn_prev
        self.btn_next = btn_next
        self.lbl_status = lbl_status
        self.txt_search = txt_search
        self.cb_cat = cb_cat
        self.cb_sup = cb_sup
        
        self.current_page = 0
        self.items_per_page = 10
        self.all_data = []
        self.filtered_data = []
        
        self.init_ui_style()
        self.init_filter_comboboxes()
        self.connect_events()

    def init_ui_style(self):
        self.table.verticalHeader().setVisible(False)
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(8, QtWidgets.QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(8, 130)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows)

    def init_filter_comboboxes(self):
        db = DatabaseManager()
        conn = db.get_connection()
        if not conn: return
        cursor = conn.cursor()
        
        self.cb_cat.clear()
        self.cb_cat.addItem("Tất cả danh mục", "")
        cursor.execute("SELECT CATEGORY_NAME FROM CATEGORIES")
        for row in cursor.fetchall(): self.cb_cat.addItem(row[0])
        
        self.cb_sup.clear()
        self.cb_sup.addItem("Tất cả nhà cung cấp", "")
        cursor.execute("SELECT SUPPLIER_NAME FROM SUPPLIERS")
        for row in cursor.fetchall(): self.cb_sup.addItem(row[0])
        conn.close()

    def connect_events(self):
        self.btn_prev.clicked.connect(self.prev_page)
        self.btn_next.clicked.connect(self.next_page)
        self.txt_search.textChanged.connect(self.apply_filter)
        self.cb_cat.currentTextChanged.connect(self.apply_filter)
        self.cb_sup.currentTextChanged.connect(self.apply_filter)

    def load_data(self):
        db = DatabaseManager()
        conn = db.get_connection()
        if not conn: return
        try:
            cursor = conn.cursor()
            query = """
                SELECT p.PRODUCT_ID, p.PRODUCT_NAME, c.CATEGORY_NAME, p.UNIT_PRICE, 
                       s.SUPPLIER_NAME, p.STOCK_QUANTITY, p.PRODUCT_STATUS, p.LAST_IMPORT_DATE
                FROM PRODUCTS p
                JOIN CATEGORIES c ON p.CATEGORY_ID = c.CATEGORY_ID
                JOIN SUPPLIERS s ON p.SUPPLIER_ID = s.SUPPLIER_ID
                ORDER BY p.PRODUCT_ID DESC
            """
            cursor.execute(query)
            self.all_data = cursor.fetchall()
            self.apply_filter()
        except Exception as e: print(f"Lỗi: {e}")
        finally: conn.close()

    def apply_filter(self):
        st = self.txt_search.text().lower().strip()
        cat = self.cb_cat.currentText()
        sup = self.cb_sup.currentText()
        
        self.filtered_data = [
            row for row in self.all_data
            if (st in str(row[0]).lower() or st in str(row[1]).lower())
            and (cat == "Tất cả danh mục" or cat == "" or row[2] == cat)
            and (sup == "Tất cả nhà cung cấp" or sup == "" or row[4] == sup)
        ]
        self.current_page = 0
        self.render_page()

    def render_page(self):
        self.table.setRowCount(0)
        start = self.current_page * self.items_per_page
        end = start + self.items_per_page
        page_data = self.filtered_data[start:end]
        
        for r_idx, r_data in enumerate(page_data):
            self.table.insertRow(r_idx)
            for c_idx, val in enumerate(r_data):
                txt = f"{val:,.0f} VNĐ" if c_idx == 3 else str(val if val else "")
                item = QtWidgets.QTableWidgetItem(txt)
                if c_idx in [0, 3, 5, 6, 7]: item.setTextAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
                self.table.setItem(r_idx, c_idx, item)
            self.add_action_buttons(r_idx, r_data[0], r_data[1])
            
        total = len(self.filtered_data)
        self.lbl_status.setText(f"Hiển thị {len(page_data)} / {total} sản phẩm")
        self.btn_prev.setEnabled(self.current_page > 0)
        self.btn_next.setEnabled(end < total)

    def add_action_buttons(self, row, pid, pname):
        container = QtWidgets.QWidget()
        layout = QtWidgets.QHBoxLayout(container)
        layout.setContentsMargins(5, 2, 5, 2)
        
        btn_e = QtWidgets.QPushButton("Sửa")
        btn_e.setStyleSheet("background-color: #3b82f6; color: white; border-radius: 3px; font-weight: bold;")
        btn_e.clicked.connect(lambda: self.open_edit(pid))
        
        btn_d = QtWidgets.QPushButton("Xóa")
        btn_d.setStyleSheet("background-color: #ef4444; color: white; border-radius: 3px; font-weight: bold;")
        btn_d.clicked.connect(lambda: self.open_delete(pid, pname))
        
        layout.addWidget(btn_e)
        layout.addWidget(btn_d)
        self.table.setCellWidget(row, 8, container)

    def next_page(self):
        self.current_page += 1
        self.render_page()

    def prev_page(self):
        self.current_page -= 1
        self.render_page()

    def open_add(self):
        if AddProduct().exec(): self.load_data()

    def open_edit(self, pid):
        if EditProduct(pid).exec(): self.load_data()

    def open_delete(self, pid, pname):
        if DeleteProduct(pid, pname).exec(): self.load_data()