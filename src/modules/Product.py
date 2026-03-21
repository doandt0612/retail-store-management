"""
Module Sản Phẩm (Products)
Kết nối với các file UI:
  - viewSanPham.ui → ViewProduct
  - addSP.ui       → AddProduct
  - editSP.ui      → EditProduct
  - deleteSP.ui    → DeleteProduct

Widget quan trọng trong từng UI:

  viewSanPham.ui:
    tableWidget   (5 cột: Mã SP | Đơn giá | Tồn kho | Danh mục | Nhà cung cấp)
    btnSua
    lblHienThiDonGia, lblHienThiSoLuongBan, lblHienThiNgayMua, lblHienThiMaDon
    lblHienThiGiaNhap, lblHienThiNgayNhap, lblHienThiMaDonNhap

  addSP.ui:
    txtReadOnlyMaSP (readonly - tự điền ID mới)
    txtTenSP, spnSoLuong, cbDanhMuc, txtGia, cbNCC
    btnLuu, btnHuy

  editSP.ui:
    txtReadOnlyMaSP (readonly)
    txtTenSP, spnSoLuong, cbDanhMuc, txtGia, cbNCC
    btnLuu, btnHuy

  deleteSP.ui:
    lblCanhBao (text từ UI), btnXoa, btnHuy

Lưu ý schema DB:
  - Bảng Products KHÔNG có cột SupplierID
  - Liên kết NCC ↔ SP qua Purchase_Orders → Purchase_Details
  - cbNCC trong Add/Edit chỉ dùng để lưu tham khảo, không UPDATE Products.SupplierID
"""

import os
from PyQt6 import uic, QtWidgets
from PyQt6.QtCore import Qt, QTimer
from src.database.db_connection import DatabaseManager

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR    = os.path.dirname(os.path.dirname(CURRENT_DIR))
UI_PATH     = os.path.join(ROOT_DIR, "ui", "modules_ui", "SanPham")


# ============================================================
# DIALOG XEM CHI TIẾT SẢN PHẨM
# ============================================================
class ViewProduct(QtWidgets.QDialog):
    """
    Hiển thị chi tiết 1 sản phẩm.

    Panel trái – tableWidget (5 cột):
      Mã SP | Đơn giá | Tồn kho | Danh mục | Nhà cung cấp
      (hiển thị 1 dòng duy nhất cho sản phẩm hiện tại)

    Panel phải trên – frame_2 (Lịch sử bán hàng - giao dịch mới nhất):
      lblHienThiDonGia / lblHienThiSoLuongBan /
      lblHienThiNgayMua / lblHienThiMaDon

    Panel phải dưới – frame_3 (Lịch sử nhập hàng - giao dịch mới nhất):
      lblHienThiGiaNhap / lblHienThiNgayNhap / lblHienThiMaDonNhap

    btnSua → gọi edit_callback
    """

    def __init__(self, data, edit_callback=None,
                 switch_to_category_callback=None,
                 open_supplier_callback=None,
                 parent=None):
        super().__init__(parent)
        uic.loadUi(os.path.join(UI_PATH, "viewSanPham.ui"), self)

        self.data                        = data
        self.edit_callback               = edit_callback
        self.switch_to_category_callback = switch_to_category_callback
        self.open_supplier_callback      = open_supplier_callback

        self._setup_table()
        self._load_product_info()
        self._load_latest_sale()
        self._load_latest_purchase()
        self._connect_signals()

    # ---------- Cài đặt bảng ----------
    def _setup_table(self):
        tbl = self.tableWidget
        tbl.verticalHeader().setVisible(False)
        tbl.setEditTriggers(QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)
        tbl.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        tbl.horizontalHeader().setSectionResizeMode(
            QtWidgets.QHeaderView.ResizeMode.Stretch
        )

    # ---------- Thông tin sản phẩm vào bảng ----------
    def _load_product_info(self):
        d   = self.data
        tbl = self.tableWidget
        tbl.setRowCount(0)
        tbl.insertRow(0)
        tbl.setItem(0, 0, QtWidgets.QTableWidgetItem(str(d["id"])))
        tbl.setItem(0, 1, QtWidgets.QTableWidgetItem(f"{d['gia']:,.0f} VNĐ"))
        tbl.setItem(0, 2, QtWidgets.QTableWidgetItem(str(d["so_luong"])))
        tbl.setItem(0, 3, QtWidgets.QTableWidgetItem(d.get("cat_name", "—")))

        # NCC lấy qua Purchase_Orders vì Products không có SupplierID
        db   = DatabaseManager()
        conn = db.get_connection()
        ncc_name = "—"
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT TOP 1 s.SupplierName
                    FROM   Purchase_Details pd
                    JOIN   Purchase_Orders  po ON pd.PurchaseOrderID = po.PurchaseOrderID
                    JOIN   Suppliers        s  ON po.SupplierID      = s.SupplierID
                    WHERE  pd.ProductID = ?
                    ORDER  BY po.PurchasedDate DESC
                """, (d["id"],))
                row = cursor.fetchone()
                if row:
                    ncc_name = row[0]
            finally:
                conn.close()

        tbl.setItem(0, 4, QtWidgets.QTableWidgetItem(ncc_name))

    # ---------- Lịch sử bán hàng (giao dịch mới nhất) ----------
    def _load_latest_sale(self):
        db   = DatabaseManager()
        conn = db.get_connection()
        if not conn:
            return
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT TOP 1 od.SubTotal / NULLIF(od.OrderedQuantity, 0),
                             od.OrderedQuantity,
                             o.OrderDate,
                             o.OrderID
                FROM   Order_Details od
                JOIN   Orders        o  ON od.OrderID = o.OrderID
                WHERE  od.ProductID = ?
                ORDER  BY o.OrderDate DESC
            """, (self.data["id"],))
            row = cursor.fetchone()
            if row:
                don_gia  = row[0] or 0
                so_luong = row[1] or 0
                ngay     = row[2].strftime("%d/%m/%Y") if row[2] else "—"
                ma_don   = str(row[3])
                self.lblHienThiDonGia.setText(f"{don_gia:,.0f} VNĐ")
                self.lblHienThiSoLuongBan.setText(str(so_luong))
                self.lblHienThiNgayMua.setText(ngay)
                self.lblHienThiMaDon.setText(ma_don)
            else:
                self.lblHienThiDonGia.setText("Chưa có")
                self.lblHienThiSoLuongBan.setText("—")
                self.lblHienThiNgayMua.setText("—")
                self.lblHienThiMaDon.setText("—")
        finally:
            conn.close()

    # ---------- Lịch sử nhập hàng (giao dịch mới nhất) ----------
    def _load_latest_purchase(self):
        db   = DatabaseManager()
        conn = db.get_connection()
        if not conn:
            return
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT TOP 1 pd.UnitCost, po.PurchasedDate, po.PurchaseOrderID
                FROM   Purchase_Details pd
                JOIN   Purchase_Orders  po ON pd.PurchaseOrderID = po.PurchaseOrderID
                WHERE  pd.ProductID = ?
                ORDER  BY po.PurchasedDate DESC
            """, (self.data["id"],))
            row = cursor.fetchone()
            if row:
                self.lblHienThiGiaNhap.setText(f"{row[0]:,.0f} VNĐ")
                self.lblHienThiNgayNhap.setText(
                    row[1].strftime("%d/%m/%Y") if row[1] else "—"
                )
                self.lblHienThiMaDonNhap.setText(str(row[2]))
            else:
                self.lblHienThiGiaNhap.setText("Chưa có")
                self.lblHienThiNgayNhap.setText("—")
                self.lblHienThiMaDonNhap.setText("—")
        finally:
            conn.close()

    # ---------- Kết nối nút ----------
    def _connect_signals(self):
        self.btnSua.clicked.connect(self._on_sua)

    def _on_sua(self):
        self.close()
        if self.edit_callback:
            self.edit_callback(self.data)


# ============================================================
# DIALOG THÊM SẢN PHẨM
# ============================================================
class AddProduct(QtWidgets.QDialog):
    """
    Tạo sản phẩm mới.
    - txtReadOnlyMaSP : tự điền ID mới (readonly)
    - txtTenSP        : tên sản phẩm
    - spnSoLuong      : tồn kho ban đầu
    - cbDanhMuc       : chọn danh mục
    - txtGia          : đơn giá
    - cbNCC           : chọn nhà cung cấp (tham khảo, không ghi vào Products)
    - btnLuu / btnHuy
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        uic.loadUi(os.path.join(UI_PATH, "addSP.ui"), self)

        self._fill_new_id()
        self._load_combos()
        self.btnLuu.clicked.connect(self._on_luu)
        self.btnHuy.clicked.connect(self.reject)

    def _fill_new_id(self):
        db   = DatabaseManager()
        conn = db.get_connection()
        if not conn:
            return
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT ISNULL(MAX(ProductID), 0) FROM Products")
            new_id = cursor.fetchone()[0] + 1
            self.txtReadOnlyMaSP.setText(str(new_id))
        finally:
            conn.close()

    def _load_combos(self):
        db   = DatabaseManager()
        conn = db.get_connection()
        if not conn:
            return
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT CategoryID, CategoryName FROM Categories ORDER BY CategoryName")
            self.cbDanhMuc.clear()
            for cid, cname in cursor.fetchall():
                self.cbDanhMuc.addItem(cname, cid)

            cursor.execute("SELECT SupplierID, SupplierName FROM Suppliers ORDER BY SupplierName")
            self.cbNCC.clear()
            for sid, sname in cursor.fetchall():
                self.cbNCC.addItem(sname, sid)
        finally:
            conn.close()

    def _on_luu(self):
        ten      = self.txtTenSP.text().strip()
        gia_text = self.txtGia.text().strip().replace(",", "")
        so_luong = self.spnSoLuong.value()
        cat_id   = self.cbDanhMuc.currentData()

        if not ten:
            QtWidgets.QMessageBox.warning(self, "Thiếu thông tin", "Vui lòng nhập Tên sản phẩm!")
            return
        if not gia_text:
            QtWidgets.QMessageBox.warning(self, "Thiếu thông tin", "Vui lòng nhập Đơn giá!")
            return
        try:
            gia = float(gia_text)
            if gia <= 0:
                raise ValueError
        except ValueError:
            QtWidgets.QMessageBox.warning(self, "Lỗi", "Đơn giá phải là số dương!")
            return

        trang_thai = "Còn hàng" if so_luong > 0 else "Hết hàng"

        db   = DatabaseManager()
        conn = db.get_connection()
        if not conn:
            return
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT ISNULL(MAX(ProductID), 0) FROM Products")
            new_id = cursor.fetchone()[0] + 1

            cursor.execute("""
                INSERT INTO Products
                    (ProductID, ProductName, CategoryID, UnitPrice, UnitsInStock, Status)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (new_id, ten, cat_id, gia, so_luong, trang_thai))

            conn.commit()
            QtWidgets.QMessageBox.information(
                self, "Thành công", f"Đã thêm sản phẩm #{new_id} thành công!"
            )
            self.accept()
        except Exception as e:
            conn.rollback()
            QtWidgets.QMessageBox.critical(self, "Lỗi CSDL", f"Lỗi khi lưu:\n{e}")
        finally:
            conn.close()


# ============================================================
# DIALOG SỬA SẢN PHẨM
# ============================================================
class EditProduct(QtWidgets.QDialog):
    """
    Chỉnh sửa thông tin sản phẩm.
    - txtReadOnlyMaSP : hiển thị ID (readonly)
    - txtTenSP, spnSoLuong, cbDanhMuc, txtGia, cbNCC
    - btnLuu / btnHuy
    """

    def __init__(self, data, parent=None):
        super().__init__(parent)
        uic.loadUi(os.path.join(UI_PATH, "editSP.ui"), self)

        self.data = data
        self._load_combos()
        self._fill_old_data()
        self.btnLuu.clicked.connect(self._on_luu)
        self.btnHuy.clicked.connect(self.reject)

    def _load_combos(self):
        db   = DatabaseManager()
        conn = db.get_connection()
        if not conn:
            return
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT CategoryID, CategoryName FROM Categories ORDER BY CategoryName")
            self.cbDanhMuc.clear()
            for cid, cname in cursor.fetchall():
                self.cbDanhMuc.addItem(cname, cid)

            cursor.execute("SELECT SupplierID, SupplierName FROM Suppliers ORDER BY SupplierName")
            self.cbNCC.clear()
            for sid, sname in cursor.fetchall():
                self.cbNCC.addItem(sname, sid)
        finally:
            conn.close()

    def _fill_old_data(self):
        d = self.data
        self.txtReadOnlyMaSP.setText(str(d["id"]))
        self.txtTenSP.setText(d["ten"])
        self.txtGia.setText(str(d["gia"]))
        self.spnSoLuong.setValue(d["so_luong"])

        # Set combobox danh mục về giá trị cũ
        idx = self.cbDanhMuc.findData(d.get("cat_id"))
        if idx >= 0:
            self.cbDanhMuc.setCurrentIndex(idx)

        # Set combobox NCC — lấy NCC gần nhất qua Purchase_Orders
        db   = DatabaseManager()
        conn = db.get_connection()
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT TOP 1 po.SupplierID
                    FROM   Purchase_Details pd
                    JOIN   Purchase_Orders  po ON pd.PurchaseOrderID = po.PurchaseOrderID
                    WHERE  pd.ProductID = ?
                    ORDER  BY po.PurchasedDate DESC
                """, (d["id"],))
                row = cursor.fetchone()
                if row:
                    idx_ncc = self.cbNCC.findData(row[0])
                    if idx_ncc >= 0:
                        self.cbNCC.setCurrentIndex(idx_ncc)
            finally:
                conn.close()

    def _on_luu(self):
        ten      = self.txtTenSP.text().strip()
        gia_text = self.txtGia.text().strip().replace(",", "")
        so_luong = self.spnSoLuong.value()
        cat_id   = self.cbDanhMuc.currentData()

        if not ten:
            QtWidgets.QMessageBox.warning(self, "Thiếu thông tin", "Vui lòng nhập Tên sản phẩm!")
            return
        if not gia_text:
            QtWidgets.QMessageBox.warning(self, "Thiếu thông tin", "Vui lòng nhập Đơn giá!")
            return
        try:
            gia = float(gia_text)
            if gia <= 0:
                raise ValueError
        except ValueError:
            QtWidgets.QMessageBox.warning(self, "Lỗi", "Đơn giá phải là số dương!")
            return

        trang_thai = "Còn hàng" if so_luong > 0 else "Hết hàng"

        db   = DatabaseManager()
        conn = db.get_connection()
        if not conn:
            return
        try:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE Products
                SET ProductName  = ?,
                    CategoryID   = ?,
                    UnitPrice    = ?,
                    UnitsInStock = ?,
                    Status       = ?
                WHERE ProductID = ?
            """, (ten, cat_id, gia, so_luong, trang_thai, self.data["id"]))

            conn.commit()
            QtWidgets.QMessageBox.information(self, "Thành công", "Đã cập nhật sản phẩm!")
            self.accept()
        except Exception as e:
            conn.rollback()
            QtWidgets.QMessageBox.critical(self, "Lỗi CSDL", f"Lỗi khi lưu:\n{e}")
        finally:
            conn.close()


# ============================================================
# DIALOG XÓA SẢN PHẨM
# ============================================================
class DeleteProduct(QtWidgets.QDialog):
    """
    Xác nhận xóa sản phẩm.
    lblCanhBao giữ nguyên nội dung từ UI.
    btnXoa → kiểm tra ràng buộc → xóa DB.
    btnHuy → đóng.
    """

    def __init__(self, data, parent=None):
        super().__init__(parent)
        uic.loadUi(os.path.join(UI_PATH, "deleteSP.ui"), self)

        self.data = data
        self.btnXoa.clicked.connect(self._on_xoa)
        self.btnHuy.clicked.connect(self.reject)

    def _on_xoa(self):
        pid  = self.data["id"]
        name = self.data["ten"]

        db   = DatabaseManager()
        conn = db.get_connection()
        if not conn:
            return
        try:
            cursor = conn.cursor()

            # Ràng buộc: đã có đơn hàng bán
            cursor.execute(
                "SELECT COUNT(*) FROM Order_Details WHERE ProductID = ?", (pid,)
            )
            if cursor.fetchone()[0] > 0:
                QtWidgets.QMessageBox.warning(
                    self, "Từ chối",
                    f"'{name}' đã có lịch sử bán hàng. Không thể xóa!"
                )
                return

            # Ràng buộc: đã có đơn nhập hàng
            cursor.execute(
                "SELECT COUNT(*) FROM Purchase_Details WHERE ProductID = ?", (pid,)
            )
            if cursor.fetchone()[0] > 0:
                QtWidgets.QMessageBox.warning(
                    self, "Từ chối",
                    f"'{name}' đã có lịch sử nhập hàng. Không thể xóa!"
                )
                return

            # Xóa khuyến mãi liên quan trước
            cursor.execute(
                "DELETE FROM Promotion_Details WHERE ProductID = ?", (pid,)
            )
            cursor.execute(
                "DELETE FROM Products WHERE ProductID = ?", (pid,)
            )
            conn.commit()
            QtWidgets.QMessageBox.information(self, "Thành công", "Đã xóa sản phẩm!")
            self.accept()
        except Exception as e:
            conn.rollback()
            QtWidgets.QMessageBox.critical(self, "Lỗi CSDL", f"Lỗi khi xóa:\n{e}")
        finally:
            conn.close()


# ============================================================
# BỘ QUẢN LÝ SẢN PHẨM – CONTROLLER
# ============================================================
class ProductManager:
    """
    Controller cho trang Sản Phẩm.

    Khai báo trong main.py → setup_module_product():
        if not hasattr(self, 'tblDanhSachSP'): return
        txt_search = self.get_widget(['txtTimSP_2'],   QtWidgets.QLineEdit)
        cb_cat     = self.get_widget(['cbDanhMuc'],    QtWidgets.QComboBox)
        cb_sup     = self.get_widget(['cbNhaCungCap'], QtWidgets.QComboBox)
        self.product_manager = ProductManager(self.tblDanhSachSP, txt_search, cb_cat, cb_sup)

        # Callback click tên danh mục → nhảy sang trang Danh mục
        def handle_switch_to_category(cat_id, cat_name): ...
        # Callback click tên NCC → mở ViewSupplier
        def handle_open_supplier(sup_id): ...

        self.product_manager.switch_to_category_callback = handle_switch_to_category
        self.product_manager.open_supplier_callback      = handle_open_supplier

        if hasattr(self, 'btnSanPham'):
            self.btnSanPham.clicked.connect(
                lambda: self.change_page(self.pageSanPham, self.product_manager.load_data)
            )
        if hasattr(self, 'btnThemSP'):
            self.btnThemSP.clicked.connect(self.product_manager.open_add)

    Bảng tblDanhSachSP cần có 7 cột trong UI:
        Mã SP | Tên SP | Đơn giá | Tồn kho | Danh mục | Nhà cung cấp | Thao tác
    """

    def __init__(self, table_widget, txt_search=None, cb_cat=None, cb_sup=None):
        self.table      = table_widget
        self.txt_search = txt_search
        self.cb_cat     = cb_cat
        self.cb_sup     = cb_sup

        self.switch_to_category_callback = None
        self.open_supplier_callback      = None

        self._init_ui()
        self._init_filters()

    # ---------- Cài đặt bảng chính ----------
    def _init_ui(self):
        tbl = self.table
        tbl.verticalHeader().setVisible(False)
        tbl.setEditTriggers(QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)
        tbl.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        hdr  = tbl.horizontalHeader()
        hdr.setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode.Stretch)
        last = tbl.columnCount() - 1
        hdr.setSectionResizeMode(last, QtWidgets.QHeaderView.ResizeMode.Fixed)
        tbl.setColumnWidth(last, 200)

    # ---------- Bộ lọc ----------
    def _init_filters(self):
        if self.txt_search:
            # Tìm kiếm realtime với debounce 300ms
            self._search_timer = QTimer()
            self._search_timer.setSingleShot(True)
            self._search_timer.setInterval(300)
            self._search_timer.timeout.connect(self.load_data)
            self.txt_search.textChanged.connect(self._search_timer.start)

        db   = DatabaseManager()
        conn = db.get_connection()
        if not conn:
            return
        try:
            cursor = conn.cursor()
            if self.cb_cat:
                self.cb_cat.blockSignals(True)
                self.cb_cat.clear()
                self.cb_cat.addItem("Tất cả danh mục", 0)
                cursor.execute("SELECT CategoryID, CategoryName FROM Categories ORDER BY CategoryName")
                for r in cursor.fetchall():
                    self.cb_cat.addItem(r[1], r[0])
                self.cb_cat.blockSignals(False)
                self.cb_cat.currentIndexChanged.connect(self.load_data)

            if self.cb_sup:
                self.cb_sup.blockSignals(True)
                self.cb_sup.clear()
                self.cb_sup.addItem("Tất cả nhà cung cấp", 0)
                cursor.execute("SELECT SupplierID, SupplierName FROM Suppliers ORDER BY SupplierName")
                for r in cursor.fetchall():
                    self.cb_sup.addItem(r[1], r[0])
                self.cb_sup.blockSignals(False)
                self.cb_sup.currentIndexChanged.connect(self.load_data)
        finally:
            conn.close()

    # ---------- Load dữ liệu bảng chính ----------
    def load_data(self):
        db   = DatabaseManager()
        conn = db.get_connection()
        if not conn:
            return

        # Lấy NCC gần nhất qua Purchase_Orders vì Products không có SupplierID
        query = """
            SELECT p.ProductID, p.ProductName, p.UnitPrice, p.UnitsInStock,
                   c.CategoryName, c.CategoryID,
                   ISNULL(
                       (SELECT TOP 1 s.SupplierName
                        FROM Purchase_Details pd2
                        JOIN Purchase_Orders  po2 ON pd2.PurchaseOrderID = po2.PurchaseOrderID
                        JOIN Suppliers        s   ON po2.SupplierID      = s.SupplierID
                        WHERE pd2.ProductID = p.ProductID
                        ORDER BY po2.PurchasedDate DESC),
                       N'Chưa có'
                   ) AS SupplierName,
                   ISNULL(
                       (SELECT TOP 1 po2.SupplierID
                        FROM Purchase_Details pd2
                        JOIN Purchase_Orders  po2 ON pd2.PurchaseOrderID = po2.PurchaseOrderID
                        WHERE pd2.ProductID = p.ProductID
                        ORDER BY po2.PurchasedDate DESC),
                       0
                   ) AS SupplierID
            FROM   Products  p
            JOIN   Categories c ON p.CategoryID = c.CategoryID
            WHERE  1 = 1
        """
        params = []

        kw = self.txt_search.text().strip() if self.txt_search else ""
        if kw:
            query += " AND p.ProductName LIKE ?"
            params.append(f"%{kw}%")

        cat_val = self.cb_cat.currentData() if self.cb_cat else 0
        if cat_val:
            query += " AND p.CategoryID = ?"
            params.append(cat_val)

        sup_val = self.cb_sup.currentData() if self.cb_sup else 0
        if sup_val:
            # Lọc theo NCC qua Purchase_Orders
            query += """
                AND EXISTS (
                    SELECT 1 FROM Purchase_Details pd3
                    JOIN Purchase_Orders po3 ON pd3.PurchaseOrderID = po3.PurchaseOrderID
                    WHERE pd3.ProductID = p.ProductID AND po3.SupplierID = ?
                )
            """
            params.append(sup_val)

        query += " ORDER BY p.ProductID DESC"

        try:
            cursor = conn.cursor()
            cursor.execute(query, params)
            rows = cursor.fetchall()

            self.table.setRowCount(0)
            for i, row in enumerate(rows):
                self.table.insertRow(i)
                # Thứ tự cột UI: Mã SP | Tên SP | Danh mục | Đơn giá | NCC | Tồn kho | Thao tác
                self.table.setItem(i, 0, QtWidgets.QTableWidgetItem(str(row[0])))           # Mã SP
                self.table.setItem(i, 1, QtWidgets.QTableWidgetItem(row[1]))                # Tên SP
                self.table.setItem(i, 2, QtWidgets.QTableWidgetItem(row[4]))                # Danh mục
                self.table.setItem(i, 3, QtWidgets.QTableWidgetItem(f"{row[2]:,.0f} VNĐ")) # Đơn giá
                self.table.setItem(i, 4, QtWidgets.QTableWidgetItem(row[6]))                # NCC
                self.table.setItem(i, 5, QtWidgets.QTableWidgetItem(str(row[3])))           # Tồn kho

                item_data = {
                    "id":       row[0],
                    "ten":      row[1],
                    "gia":      float(row[2]),
                    "so_luong": row[3],
                    "cat_name": row[4],
                    "cat_id":   row[5],
                    "sup_name": row[6],
                    "sup_id":   row[7],
                }
                self._add_action_buttons(i, item_data)
        except Exception as e:
            print(f"Lỗi load Sản phẩm: {e}")
        finally:
            conn.close()

    # ---------- Nút thao tác mỗi hàng ----------
    def _add_action_buttons(self, row_idx, item_data):
        last      = self.table.columnCount() - 1
        container = QtWidgets.QWidget()
        h = QtWidgets.QHBoxLayout(container)
        h.setContentsMargins(4, 2, 4, 2)
        h.setSpacing(4)

        style    = "padding:5px;font-weight:bold;border-radius:4px;color:white;border:none;"
        btn_view = QtWidgets.QPushButton("Xem")
        btn_edit = QtWidgets.QPushButton("Sửa")
        btn_del  = QtWidgets.QPushButton("Xóa")
        btn_view.setStyleSheet(f"background-color:#10b981;{style}")
        btn_edit.setStyleSheet(f"background-color:#3b82f6;{style}")
        btn_del.setStyleSheet(f"background-color:#ef4444;{style}")

        btn_view.clicked.connect(lambda _, d=item_data: self.open_view(d))
        btn_edit.clicked.connect(lambda _, d=item_data: self.open_edit(d))
        btn_del.clicked.connect(lambda _, d=item_data:  self.open_delete(d))

        h.addWidget(btn_view)
        h.addWidget(btn_edit)
        h.addWidget(btn_del)
        self.table.setCellWidget(row_idx, last, container)

    # ---------- Mở các dialog ----------
    def open_view(self, item_data):
        ViewProduct(
            item_data,
            edit_callback=self.open_edit,
            switch_to_category_callback=self.switch_to_category_callback,
            open_supplier_callback=self.open_supplier_callback,
        ).exec()

    def open_add(self):
        if AddProduct().exec():
            self.load_data()

    def open_edit(self, item_data):
        if EditProduct(item_data).exec():
            self.load_data()

    def open_delete(self, item_data):
        if DeleteProduct(item_data).exec():
            self.load_data()