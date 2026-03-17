import os
from PyQt6 import uic, QtWidgets
from PyQt6.QtCore import Qt
from src.database.db_connection import DatabaseManager

# Thiết lập đường dẫn gốc
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(os.path.dirname(CURRENT_DIR))
UI_PATH = os.path.join(ROOT_DIR, "ui", "modules_ui", "SanPham")


# ==========================================
# DIALOG THÊM SẢN PHẨM
# ==========================================
class AddProduct(QtWidgets.QDialog):
    def __init__(self):
        super().__init__()
        uic.loadUi(os.path.join(UI_PATH, "addSP.ui"), self)
        
        self.load_combobox_data()
        
        if hasattr(self, 'btnLuu'): self.btnLuu.clicked.connect(self.save_data)
        if hasattr(self, 'btnHuy'): self.btnHuy.clicked.connect(self.reject)

    def load_combobox_data(self):
        db = DatabaseManager()
        conn = db.get_connection()
        if not conn: return
        cursor = conn.cursor()
        
        # Load Danh mục
        cursor.execute("SELECT CategoryID, CategoryName FROM Categories")
        self.cbDanhMuc.clear()
        for cid, cname in cursor.fetchall():
            self.cbDanhMuc.addItem(cname, cid) # Gắn ID ẩn phía sau
            
        # Load NCC
        cursor.execute("SELECT SupplierID, SupplierName FROM Suppliers")
        self.cbNCC.clear()
        for sid, sname in cursor.fetchall():
            self.cbNCC.addItem(sname, sid)
            
        conn.close()

    def save_data(self):
        ten = self.txtTenSP.text().strip()
        gia = self.txtGia.text().strip()
        so_luong = self.spnSoLuong.value()
        
        if not ten or not gia:
            QtWidgets.QMessageBox.warning(self, "Lỗi", "Vui lòng nhập đầy đủ Tên và Đơn giá!")
            return
            
        try:
            gia_float = float(gia)
            if gia_float <= 0: raise ValueError
        except ValueError:
            QtWidgets.QMessageBox.warning(self, "Lỗi", "Đơn giá phải là số lớn hơn 0!")
            return
            
        cat_id = self.cbDanhMuc.currentData()
        sup_id = self.cbNCC.currentData()
        trang_thai = "Còn hàng" if so_luong > 0 else "Hết hàng"
        
        db = DatabaseManager()
        conn = db.get_connection()
        if not conn: return
        
        try:
            cursor = conn.cursor()
            # ID tự tăng
            cursor.execute("SELECT ISNULL(MAX(ProductID), 0) FROM Products")
            new_id = cursor.fetchone()[0] + 1
            
            cursor.execute("""
                INSERT INTO Products (ProductID, ProductName, SupplierID, CategoryID, UnitPrice, UnitsInStock, Status)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (new_id, ten, sup_id, cat_id, gia_float, so_luong, trang_thai))
            
            conn.commit()
            QtWidgets.QMessageBox.information(self, "Thành công", "Đã thêm sản phẩm mới!")
            self.accept()
        except Exception as e:
            conn.rollback()
            QtWidgets.QMessageBox.critical(self, "Lỗi", f"Lỗi cơ sở dữ liệu:\n{e}")
        finally:
            conn.close()


# ==========================================
# DIALOG SỬA SẢN PHẨM
# ==========================================
class EditProduct(QtWidgets.QDialog):
    def __init__(self, data):
        super().__init__()
        uic.loadUi(os.path.join(UI_PATH, "editSP.ui"), self)
        
        self.product_id = data['id']
        self.load_combobox_data()
        self.load_old_data(data)
        
        if hasattr(self, 'btnLuu'): self.btnLuu.clicked.connect(self.update_data)
        if hasattr(self, 'btnHuy'): self.btnHuy.clicked.connect(self.reject)

    def load_combobox_data(self):
        db = DatabaseManager()
        conn = db.get_connection()
        if not conn: return
        cursor = conn.cursor()
        
        cursor.execute("SELECT CategoryID, CategoryName FROM Categories")
        self.cbDanhMuc.clear()
        for cid, cname in cursor.fetchall():
            self.cbDanhMuc.addItem(cname, cid)
            
        cursor.execute("SELECT SupplierID, SupplierName FROM Suppliers")
        self.cbNCC.clear()
        for sid, sname in cursor.fetchall():
            self.cbNCC.addItem(sname, sid)
        conn.close()

    def load_old_data(self, data):
        if hasattr(self, 'txtReadOnlyMaSP'): self.txtReadOnlyMaSP.setText(str(data['id']))
        self.txtTenSP.setText(data['ten'])
        self.txtGia.setText(str(data['gia']))
        self.spnSoLuong.setValue(data['so_luong'])
        
        # Set ComboBox về giá trị cũ
        cat_idx = self.cbDanhMuc.findData(data['cat_id'])
        if cat_idx >= 0: self.cbDanhMuc.setCurrentIndex(cat_idx)
            
        sup_idx = self.cbNCC.findData(data['sup_id'])
        if sup_idx >= 0: self.cbNCC.setCurrentIndex(sup_idx)

    def update_data(self):
        ten = self.txtTenSP.text().strip()
        gia = self.txtGia.text().strip()
        so_luong = self.spnSoLuong.value()
        
        if not ten or not gia:
            QtWidgets.QMessageBox.warning(self, "Lỗi", "Vui lòng nhập đầy đủ Tên và Đơn giá!")
            return
            
        try:
            gia_float = float(gia)
            if gia_float <= 0: raise ValueError
        except ValueError:
            QtWidgets.QMessageBox.warning(self, "Lỗi", "Đơn giá phải là số dương!")
            return
            
        cat_id = self.cbDanhMuc.currentData()
        sup_id = self.cbNCC.currentData()
        trang_thai = "Còn hàng" if so_luong > 0 else "Hết hàng"
        
        db = DatabaseManager()
        conn = db.get_connection()
        if not conn: return
        
        try:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE Products 
                SET ProductName=?, SupplierID=?, CategoryID=?, UnitPrice=?, UnitsInStock=?, Status=?
                WHERE ProductID=?
            """, (ten, sup_id, cat_id, gia_float, so_luong, trang_thai, self.product_id))
            
            conn.commit()
            QtWidgets.QMessageBox.information(self, "Thành công", "Đã cập nhật sản phẩm!")
            self.accept()
        except Exception as e:
            conn.rollback()
            QtWidgets.QMessageBox.critical(self, "Lỗi", f"Lỗi hệ thống:\n{e}")
        finally:
            conn.close()


# ==========================================
# DIALOG XÓA SẢN PHẨM
# ==========================================
class DeleteProduct(QtWidgets.QDialog):
    def __init__(self, data):
        super().__init__()
        uic.loadUi(os.path.join(UI_PATH, "deleteSP.ui"), self)
        
        self.product_id = data['id']
        self.product_name = data['ten']
        
        if hasattr(self, 'lblCanhBao'):
            self.lblCanhBao.setText(f"Bạn có chắc chắn muốn xóa sản phẩm:\n'{self.product_name}'?\nThao tác này sẽ xóa mọi dữ liệu liên quan và không thể hoàn tác.")
            
        if hasattr(self, 'btnXoa'): self.btnXoa.clicked.connect(self.delete_data)
        if hasattr(self, 'btnHuy'): self.btnHuy.clicked.connect(self.reject)

    def delete_data(self):
        db = DatabaseManager()
        conn = db.get_connection()
        if not conn: return
        
        try:
            cursor = conn.cursor()
            
            # KIỂM TRA RÀNG BUỘC
            cursor.execute("SELECT COUNT(*) FROM Order_Details WHERE ProductID = ?", (self.product_id,))
            if cursor.fetchone()[0] > 0:
                QtWidgets.QMessageBox.warning(self, "Từ chối", "Sản phẩm này đã từng được bán. Không thể xóa!")
                return
                
            cursor.execute("SELECT COUNT(*) FROM Purchase_Details WHERE ProductID = ?", (self.product_id,))
            if cursor.fetchone()[0] > 0:
                QtWidgets.QMessageBox.warning(self, "Từ chối", "Sản phẩm này có trong lịch sử nhập hàng. Không thể xóa!")
                return

            # Xóa
            cursor.execute("DELETE FROM Products WHERE ProductID = ?", (self.product_id,))
            conn.commit()
            QtWidgets.QMessageBox.information(self, "Thành công", "Đã xóa sản phẩm!")
            self.accept()
        except Exception as e:
            conn.rollback()
            QtWidgets.QMessageBox.critical(self, "Lỗi", f"Lỗi hệ thống:\n{e}")
        finally:
            conn.close()


# ==========================================
# DIALOG CHI TIẾT SẢN PHẨM (XEM LỊCH SỬ & CÓ LINK CHUYỂN TRANG)
# ==========================================
class ViewProduct(QtWidgets.QDialog):
    def __init__(self, data, switch_cat_callback=None, open_sup_callback=None, edit_callback=None):
        super().__init__()
        uic.loadUi(os.path.join(UI_PATH, "viewSanPham.ui"), self)
        
        self.data = data
        self.switch_cat_callback = switch_cat_callback
        self.open_sup_callback = open_sup_callback
        self.edit_callback = edit_callback # Hàm gọi form Edit
        
        self.load_general_info()
        self.load_sales_history()
        self.load_purchase_history()
        
        if hasattr(self, 'btnSua'): 
            self.btnSua.clicked.connect(self.on_edit_clicked)
        if hasattr(self, 'btnDong'): 
            self.btnDong.clicked.connect(self.close)

    def load_general_info(self):
        """Load thông tin cơ bản và tạo Hyperlink"""
        if hasattr(self, 'lblHienThiMaSP'): self.lblHienThiMaSP.setText(str(self.data['id']))
        if hasattr(self, 'lblHienThiTenSP'): self.lblHienThiTenSP.setText(self.data['ten'])
        if hasattr(self, 'lblHienThiGia'): self.lblHienThiGia.setText(f"{self.data['gia']:,.0f} VNĐ")
        if hasattr(self, 'lblHienThiTonKho'): self.lblHienThiTonKho.setText(str(self.data['so_luong']))
        
        # 1. TẠO LINK DANH MỤC
        if hasattr(self, 'lblHienThiDanhMuc'):
            cat_html = f'<a href="cat_{self.data["cat_id"]}" style="color: #2563eb; text-decoration: none; font-weight: bold;">{self.data["cat_name"]}</a>'
            self.lblHienThiDanhMuc.setText(cat_html)
            self.lblHienThiDanhMuc.setOpenExternalLinks(False)
            self.lblHienThiDanhMuc.linkActivated.connect(self.on_category_clicked)

        # 2. TẠO LINK NHÀ CUNG CẤP
        if hasattr(self, 'lblHienThiNhaCungCap'):
            sup_html = f'<a href="sup_{self.data["sup_id"]}" style="color: #2563eb; text-decoration: none; font-weight: bold;">{self.data["sup_name"]}</a>'
            self.lblHienThiNhaCungCap.setText(sup_html)
            self.lblHienThiNhaCungCap.setOpenExternalLinks(False)
            self.lblHienThiNhaCungCap.linkActivated.connect(self.on_supplier_clicked)

    def on_category_clicked(self, link):
        self.close()
        if self.switch_cat_callback:
            # link có dạng 'cat_1', cắt lấy số 1
            cat_id = int(link.split('_')[1])
            self.switch_cat_callback(cat_id, self.data["cat_name"])

    def on_supplier_clicked(self, link):
        # Không đóng cửa sổ SP, chỉ bật popup đè lên
        if self.open_sup_callback:
            sup_id = int(link.split('_')[1])
            self.open_sup_callback(sup_id)
            
    def on_edit_clicked(self):
        self.close()
        if self.edit_callback:
            self.edit_callback(self.data)

    def load_sales_history(self):
        """Lịch sử bán hàng: OrderDetails JOIN Orders"""
        if not hasattr(self, 'tblLichSuBanHang'): return
        self.setup_table(self.tblLichSuBanHang)
        
        db = DatabaseManager()
        conn = db.get_connection()
        if not conn: return
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT o.OrderID, o.OrderDate, od.Quantity, od.UnitPrice, od.Subtotal
                FROM Order_Details od
                JOIN Orders o ON od.OrderID = o.OrderID
                WHERE od.ProductID = ?
                ORDER BY o.OrderDate DESC
            """, (self.data['id'],))
            
            rows = cursor.fetchall()
            self.tblLichSuBanHang.setRowCount(0)
            for i, row in enumerate(rows):
                self.tblLichSuBanHang.insertRow(i)
                self.tblLichSuBanHang.setItem(i, 0, QtWidgets.QTableWidgetItem(str(row[0])))
                date_str = row[1].strftime('%d/%m/%Y') if row[1] else ""
                self.tblLichSuBanHang.setItem(i, 1, QtWidgets.QTableWidgetItem(date_str))
                self.tblLichSuBanHang.setItem(i, 2, QtWidgets.QTableWidgetItem(str(row[2])))
                self.tblLichSuBanHang.setItem(i, 3, QtWidgets.QTableWidgetItem(f"{row[3]:,.0f} VNĐ"))
        finally:
            conn.close()

    def load_purchase_history(self):
        """Lịch sử nhập hàng: PurchaseDetails JOIN PurchaseOrders"""
        if not hasattr(self, 'tblLichSuNhapHang'): return
        self.setup_table(self.tblLichSuNhapHang)
        
        db = DatabaseManager()
        conn = db.get_connection()
        if not conn: return
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT po.PurchaseOrderID, po.PurchasedDate, pd.Quantity, pd.UnitPrice
                FROM Purchase_Details pd
                JOIN Purchase_Orders po ON pd.PurchaseOrderID = po.PurchaseOrderID
                WHERE pd.ProductID = ?
                ORDER BY po.PurchasedDate DESC
            """, (self.data['id'],))
            
            rows = cursor.fetchall()
            self.tblLichSuNhapHang.setRowCount(0)
            for i, row in enumerate(rows):
                self.tblLichSuNhapHang.insertRow(i)
                self.tblLichSuNhapHang.setItem(i, 0, QtWidgets.QTableWidgetItem(str(row[0])))
                date_str = row[1].strftime('%d/%m/%Y') if row[1] else ""
                self.tblLichSuNhapHang.setItem(i, 1, QtWidgets.QTableWidgetItem(date_str))
                self.tblLichSuNhapHang.setItem(i, 2, QtWidgets.QTableWidgetItem(str(row[2])))
                self.tblLichSuNhapHang.setItem(i, 3, QtWidgets.QTableWidgetItem(f"{row[3]:,.0f} VNĐ"))
        finally:
            conn.close()

    def setup_table(self, table_widget):
        table_widget.verticalHeader().setVisible(False)
        table_widget.setEditTriggers(QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)
        table_widget.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode.Stretch)


# ==========================================
# BỘ QUẢN LÝ SẢN PHẨM (CONTROLLER)
# ==========================================
class ProductManager:
    def __init__(self, table_widget, txt_search=None, cb_cat=None, cb_sup=None):
        self.table = table_widget
        self.txt_search = txt_search
        self.cb_cat = cb_cat
        self.cb_sup = cb_sup
        
        # Hàm callback từ main.py
        self.switch_to_category_callback = None
        self.open_supplier_callback = None
        
        self.init_ui()
        self.init_filters()

    def init_ui(self):
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(6, QtWidgets.QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(6, 200) # Cột thao tác

    def init_filters(self):
        if self.txt_search: self.txt_search.returnPressed.connect(self.load_data)
        if self.cb_cat: self.cb_cat.currentIndexChanged.connect(self.load_data)
        if self.cb_sup: self.cb_sup.currentIndexChanged.connect(self.load_data)
        
        db = DatabaseManager()
        conn = db.get_connection()
        if not conn: return
        cursor = conn.cursor()
        
        if self.cb_cat:
            self.cb_cat.blockSignals(True)
            self.cb_cat.clear()
            self.cb_cat.addItem("Tất cả danh mục", 0)
            cursor.execute("SELECT CategoryID, CategoryName FROM Categories")
            for r in cursor.fetchall(): self.cb_cat.addItem(r[1], r[0])
            self.cb_cat.blockSignals(False)
            
        if self.cb_sup:
            self.cb_sup.blockSignals(True)
            self.cb_sup.clear()
            self.cb_sup.addItem("Tất cả nhà cung cấp", 0)
            cursor.execute("SELECT SupplierID, SupplierName FROM Suppliers")
            for r in cursor.fetchall(): self.cb_sup.addItem(r[1], r[0])
            self.cb_sup.blockSignals(False)
        conn.close()

    def load_data(self):
        db = DatabaseManager()
        conn = db.get_connection()
        if not conn: return
        
        query = """
            SELECT 
                p.ProductID, p.ProductName, p.UnitPrice, p.UnitsInStock, 
                c.CategoryName, s.SupplierName, c.CategoryID, s.SupplierID
            FROM Products p
            JOIN Categories c ON p.CategoryID = c.CategoryID
            JOIN Suppliers s ON p.SupplierID = s.SupplierID
            WHERE 1=1
        """
        params = []
        
        if self.txt_search and self.txt_search.text().strip():
            query += " AND p.ProductName LIKE ?"
            params.append(f"%{self.txt_search.text().strip()}%")
            
        if self.cb_cat and self.cb_cat.currentData() != 0:
            query += " AND p.CategoryID = ?"
            params.append(self.cb_cat.currentData())
            
        if self.cb_sup and self.cb_sup.currentData() != 0:
            query += " AND p.SupplierID = ?"
            params.append(self.cb_sup.currentData())
            
        query += " ORDER BY p.ProductID DESC"
        
        try:
            cursor = conn.cursor()
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            self.table.setRowCount(0)
            for i, row in enumerate(rows):
                self.table.insertRow(i)
                self.table.setItem(i, 0, QtWidgets.QTableWidgetItem(str(row[0])))
                self.table.setItem(i, 1, QtWidgets.QTableWidgetItem(row[1]))
                self.table.setItem(i, 2, QtWidgets.QTableWidgetItem(f"{row[2]:,.0f} VNĐ"))
                self.table.setItem(i, 3, QtWidgets.QTableWidgetItem(str(row[3])))
                self.table.setItem(i, 4, QtWidgets.QTableWidgetItem(row[4]))
                self.table.setItem(i, 5, QtWidgets.QTableWidgetItem(row[5]))
                
                item_data = {
                    "id": row[0], "ten": row[1], "gia": float(row[2]), "so_luong": row[3],
                    "cat_name": row[4], "sup_name": row[5],
                    "cat_id": row[6], "sup_id": row[7]
                }
                self.add_action_buttons(i, item_data)
                
        except Exception as e:
            print(f"Lỗi load Sản phẩm: {e}")
        finally:
            conn.close()

    def add_action_buttons(self, row, item):
        container = QtWidgets.QWidget()
        layout = QtWidgets.QHBoxLayout(container)
        layout.setContentsMargins(5, 2, 5, 2)
        layout.setSpacing(5)

        btn_view = QtWidgets.QPushButton("Xem")
        btn_edit = QtWidgets.QPushButton("Sửa")
        btn_delete = QtWidgets.QPushButton("Xóa")

        style = "padding: 5px; font-weight: bold; border-radius: 4px; color: white; border: none;"
        btn_view.setStyleSheet(f"background-color: #10b981; {style}")
        btn_edit.setStyleSheet(f"background-color: #3b82f6; {style}")
        btn_delete.setStyleSheet(f"background-color: #ef4444; {style}")

        btn_view.clicked.connect(lambda: self.open_view(item))
        btn_edit.clicked.connect(lambda: self.open_edit(item))
        btn_delete.clicked.connect(lambda: self.open_delete(item))

        layout.addWidget(btn_view)
        layout.addWidget(btn_edit)
        layout.addWidget(btn_delete)
        self.table.setCellWidget(row, 6, container)

    def open_view(self, item):
        # Truyền callback chuyển trang, popup NCC và gọi form Edit
        dialog = ViewProduct(item, self.switch_to_category_callback, self.open_supplier_callback, self.open_edit)
        dialog.exec()

    def open_add(self):
        if AddProduct().exec(): self.load_data()

    def open_edit(self, item):
        if EditProduct(item).exec(): self.load_data()

    def open_delete(self, item):
        if DeleteProduct(item).exec(): self.load_data()


