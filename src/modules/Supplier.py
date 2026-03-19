"""
Module Nhà Cung Cấp (Suppliers)
Kết nối với các file UI:
  - viewNCC.ui   → ViewSupplier
  - addNCC.ui    → AddSupplier
  - editNCC.ui   → EditSupplier
  - deleteNCC.ui → DeleteSupplier

Widget quan trọng trong từng UI:
  viewNCC.ui:
    tblDanhSachSPCungCap (4 cột: Mã SP | Tên SP | Số lượng | Giá nhập)
    btnSua
    lblHienThiMaNCC, lblHienThiSDT, lblHienThiEmail, lblHienThiDiaChi
    lblHienThiMaDonNhap, lblHienThiNgayNhap, lblHienThiTongTien
    btnXemDonNhap

  addNCC.ui / editNCC.ui:
    tblDanhSachSPCungCap (5 cột: Mã SP | Tên SP | Số lượng | Giá nhập | Thao tác)
    txtReadOnlyMaSP (auto-fill khi chọn combo)
    btnTenSP  (QComboBox chọn sản phẩm — tên widget là btnTenSP)
    spnSoLuong, txtGiaNhap
    btnThem
    txtOnlyReadMaNCC (readonly - hiển thị mã NCC mới)
    txtSDT, txtEmail, txtDiaChi
    btnLuu, btnHuy

  deleteNCC.ui:
    lblCanhBao (text từ UI), btnXoa, btnHuy
"""

import os
from PyQt6 import uic, QtWidgets
from PyQt6.QtCore import Qt
from src.database.db_connection import DatabaseManager

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR    = os.path.dirname(os.path.dirname(CURRENT_DIR))
UI_PATH     = os.path.join(ROOT_DIR, "ui", "modules_ui", "NhaCungCap")


# ============================================================
# DIALOG XEM CHI TIẾT NHÀ CUNG CẤP
# ============================================================
class ViewSupplier(QtWidgets.QDialog):
    """
    Hiển thị chi tiết 1 nhà cung cấp.

    Panel trái  – tblDanhSachSPCungCap: danh sách SP cung cấp
      Cột: Mã SP | Tên SP | Số lượng | Giá nhập

    Panel phải trên – frame_3 (Thông tin liên hệ):
      lblHienThiMaNCC / lblHienThiSDT / lblHienThiEmail / lblHienThiDiaChi

    Panel phải dưới – frame_2 (Đơn hàng nhập mới nhất):
      lblHienThiMaDonNhap / lblHienThiNgayNhap / lblHienThiTongTien
      btnXemDonNhap → gọi open_purchase_order_callback

    btnSua → gọi edit_callback
    """

    def __init__(self, data, open_purchase_order_callback=None, edit_callback=None, parent=None):
        super().__init__(parent)
        uic.loadUi(os.path.join(UI_PATH, "viewNCC.ui"), self)

        self.data                          = data
        self.open_purchase_order_callback  = open_purchase_order_callback
        self.edit_callback                 = edit_callback
        self.latest_po_id                  = None

        self._load_contact_info()
        self._load_products()
        self._load_latest_purchase_order()
        self._connect_signals()

    # ---------- Thông tin liên hệ ----------
    def _load_contact_info(self):
        self.lblHienThiMaNCC.setText(str(self.data["id"]))
        self.lblHienThiSDT.setText(self.data.get("sdt", ""))
        self.lblHienThiEmail.setText(self.data.get("email", ""))
        self.lblHienThiDiaChi.setText(self.data.get("dia_chi", ""))

    # ---------- Danh sách sản phẩm cung cấp ----------
    def _load_products(self):
        tbl = self.tblDanhSachSPCungCap
        tbl.verticalHeader().setVisible(False)
        tbl.setEditTriggers(QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)
        tbl.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        tbl.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode.Stretch)

        db   = DatabaseManager()
        conn = db.get_connection()
        if not conn:
            return
        try:
            cursor = conn.cursor()
            # Lấy SP qua Purchase_Details vì Products không có cột SupplierID
            cursor.execute("""
                SELECT DISTINCT p.ProductID, p.ProductName,
                       p.UnitsInStock, pd.UnitCost
                FROM   Purchase_Details pd
                JOIN   Purchase_Orders  po ON pd.PurchaseOrderID = po.PurchaseOrderID
                JOIN   Products         p  ON pd.ProductID       = p.ProductID
                WHERE  po.SupplierID = ?
                ORDER  BY p.ProductID
            """, (self.data["id"],))

            rows = cursor.fetchall()
            tbl.setRowCount(0)
            for i, r in enumerate(rows):
                tbl.insertRow(i)
                tbl.setItem(i, 0, QtWidgets.QTableWidgetItem(str(r[0])))
                tbl.setItem(i, 1, QtWidgets.QTableWidgetItem(r[1]))
                tbl.setItem(i, 2, QtWidgets.QTableWidgetItem(str(r[2])))
                tbl.setItem(i, 3, QtWidgets.QTableWidgetItem(f"{r[3]:,.0f} VNĐ"))
        finally:
            conn.close()

    # ---------- Đơn nhập hàng mới nhất ----------
    def _load_latest_purchase_order(self):
        db   = DatabaseManager()
        conn = db.get_connection()
        if not conn:
            return
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT TOP 1 PurchaseOrderID, PurchasedDate, TotalAmount
                FROM   Purchase_Orders
                WHERE  SupplierID = ?
                ORDER  BY PurchasedDate DESC
            """, (self.data["id"],))

            po = cursor.fetchone()
            if po:
                self.latest_po_id = po[0]
                self.lblHienThiMaDonNhap.setText(str(po[0]))
                self.lblHienThiNgayNhap.setText(
                    po[1].strftime("%d/%m/%Y") if po[1] else "—"
                )
                self.lblHienThiTongTien.setText(f"{po[2]:,.0f} VNĐ")
                self.btnXemDonNhap.setEnabled(True)
            else:
                self.lblHienThiMaDonNhap.setText("Chưa có")
                self.lblHienThiNgayNhap.setText("—")
                self.lblHienThiTongTien.setText("0 VNĐ")
                self.btnXemDonNhap.setEnabled(False)
        finally:
            conn.close()

    # ---------- Kết nối nút ----------
    def _connect_signals(self):
        self.btnSua.clicked.connect(self._on_sua)
        self.btnXemDonNhap.clicked.connect(self._on_xem_don_nhap)

    def _on_sua(self):
        self.close()
        if self.edit_callback:
            self.edit_callback(self.data)

    def _on_xem_don_nhap(self):
        if self.open_purchase_order_callback and self.latest_po_id:
            self.close()
            self.open_purchase_order_callback(self.latest_po_id)


# ============================================================
# DIALOG THÊM NHÀ CUNG CẤP
# ============================================================
class AddSupplier(QtWidgets.QDialog):
    """
    Tạo nhà cung cấp mới kèm danh sách sản phẩm cung cấp.

    Luồng sử dụng:
      1. Điền SĐT, Email, Địa chỉ vào frame_3 (txtOnlyReadMaNCC tự điền mã mới).
      2. Chọn SP trong btnTenSP (QComboBox), nhập Số lượng + Giá nhập.
      3. Bấm btnThem → SP vào tblDanhSachSPCungCap.
      4. Bấm btnLuu → lưu NCC và Products liên kết vào DB.

    Lưu ý thiết kế UI:
      - btnTenSP  : QComboBox (tên widget lạ nhưng đúng trong file .ui)
      - txtReadOnlyMaSP : auto-fill Mã SP khi đổi combo
      - txtOnlyReadMaNCC: hiển thị ID sẽ được tạo (readonly)
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        uic.loadUi(os.path.join(UI_PATH, "addNCC.ui"), self)

        self._product_rows = []   # [{pid, pname, qty, price}]
        self._price_map    = {}   # {pid: float(UnitPrice)}

        self._setup_table()
        self._load_products_combo()
        self._fill_new_id()
        self._connect_signals()

    # ---------- Cài đặt bảng ----------
    def _setup_table(self):
        tbl = self.tblDanhSachSPCungCap
        tbl.verticalHeader().setVisible(False)
        tbl.setEditTriggers(QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)
        tbl.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        hdr = tbl.horizontalHeader()
        hdr.setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode.Stretch)
        hdr.setSectionResizeMode(4, QtWidgets.QHeaderView.ResizeMode.Fixed)
        tbl.setColumnWidth(4, 80)

    # ---------- Load combo sản phẩm ----------
    def _load_products_combo(self):
        db   = DatabaseManager()
        conn = db.get_connection()
        if not conn:
            return
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT ProductID, ProductName, UnitPrice FROM Products ORDER BY ProductName"
            )
            self.btnTenSP.clear()
            for pid, pname, price in cursor.fetchall():
                self.btnTenSP.addItem(pname, pid)
                self._price_map[pid] = float(price)
            # Tự điền mã SP khi combo thay đổi
            self.btnTenSP.currentIndexChanged.connect(self._on_sp_changed)
            self._on_sp_changed()
        finally:
            conn.close()

    def _on_sp_changed(self):
        pid = self.btnTenSP.currentData()
        self.txtReadOnlyMaSP.setText(str(pid) if pid else "")

    # ---------- Hiển thị mã NCC mới ----------
    def _fill_new_id(self):
        db   = DatabaseManager()
        conn = db.get_connection()
        if not conn:
            return
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT ISNULL(MAX(SupplierID), 0) FROM Suppliers")
            new_id = cursor.fetchone()[0] + 1
            self.txtOnlyReadMaNCC.setText(str(new_id))
        finally:
            conn.close()

    # ---------- Kết nối tín hiệu ----------
    def _connect_signals(self):
        self.btnThem.clicked.connect(self._on_them_sp)
        self.btnLuu.clicked.connect(self._on_luu)
        self.btnHuy.clicked.connect(self.reject)

    # ---------- Thêm SP vào bảng ----------
    def _on_them_sp(self):
        pid   = self.btnTenSP.currentData()
        pname = self.btnTenSP.currentText()
        qty   = self.spnSoLuong.value()

        price_text = self.txtGiaNhap.text().strip().replace(",", "")
        if not price_text:
            QtWidgets.QMessageBox.warning(self, "Thiếu thông tin", "Vui lòng nhập Giá nhập!")
            return
        try:
            price = float(price_text)
            if price <= 0:
                raise ValueError
        except ValueError:
            QtWidgets.QMessageBox.warning(self, "Lỗi", "Giá nhập phải là số dương!")
            return

        for rd in self._product_rows:
            if rd["pid"] == pid:
                QtWidgets.QMessageBox.warning(self, "Trùng", "Sản phẩm này đã có trong danh sách!")
                return

        row_data = {"pid": pid, "pname": pname, "qty": qty, "price": price}
        self._product_rows.append(row_data)
        self._insert_table_row(row_data)
        # Reset input
        self.spnSoLuong.setValue(0)
        self.txtGiaNhap.clear()

    def _insert_table_row(self, row_data):
        tbl = self.tblDanhSachSPCungCap
        i   = tbl.rowCount()
        tbl.insertRow(i)
        tbl.setItem(i, 0, QtWidgets.QTableWidgetItem(str(row_data["pid"])))
        tbl.setItem(i, 1, QtWidgets.QTableWidgetItem(row_data["pname"]))
        tbl.setItem(i, 2, QtWidgets.QTableWidgetItem(str(row_data["qty"])))
        tbl.setItem(i, 3, QtWidgets.QTableWidgetItem(f"{row_data['price']:,.0f} VNĐ"))

        btn_xoa = QtWidgets.QPushButton("Xóa")
        btn_xoa.setStyleSheet(
            "background-color:#ef4444;color:white;font-weight:bold;"
            "border:none;border-radius:4px;padding:4px;"
        )
        btn_xoa.clicked.connect(lambda _, r=row_data: self._remove_row(r))
        tbl.setCellWidget(i, 4, btn_xoa)

    def _remove_row(self, row_data):
        if row_data in self._product_rows:
            self._product_rows.remove(row_data)
        self._refresh_table()

    def _refresh_table(self):
        self.tblDanhSachSPCungCap.setRowCount(0)
        for rd in self._product_rows:
            self._insert_table_row(rd)

    # ---------- Lưu ----------
    def _on_luu(self):
        sdt      = self.txtSDT.text().strip()
        email    = self.txtEmail.text().strip()
        dia_chi  = self.txtDiaChi.text().strip()

        if not sdt:
            QtWidgets.QMessageBox.warning(self, "Thiếu thông tin", "Vui lòng nhập Số điện thoại!")
            return

        # Đọc tên NCC — UI không có txtTenNCC nên dùng SĐT làm định danh
        # hoặc bạn có thể thêm 1 QLineEdit tên txtTenNCC vào UI sau
        ten = getattr(self, "txtTenNCC", None)
        ten = ten.text().strip() if ten else sdt   # fallback: dùng SĐT làm tên tạm

        db   = DatabaseManager()
        conn = db.get_connection()
        if not conn:
            return
        try:
            cursor = conn.cursor()

            # Kiểm tra trùng SĐT
            cursor.execute(
                "SELECT COUNT(*) FROM Suppliers WHERE SupplierPhone = ?", (sdt,)
            )
            if cursor.fetchone()[0] > 0:
                QtWidgets.QMessageBox.warning(self, "Từ chối", "Số điện thoại này đã tồn tại!")
                return

            cursor.execute("SELECT ISNULL(MAX(SupplierID), 0) FROM Suppliers")
            new_id = cursor.fetchone()[0] + 1

            cursor.execute("""
                INSERT INTO Suppliers
                    (SupplierID, SupplierName, SupplierPhone, SupplierEmail, SupplierAddress)
                VALUES (?, ?, ?, ?, ?)
            """, (new_id, ten, sdt, email, dia_chi))

            # Products không có cột SupplierID nên không cần UPDATE Products
            # Liên kết NCC-SP được quản lý qua Purchase_Orders và Purchase_Details

            conn.commit()
            QtWidgets.QMessageBox.information(
                self, "Thành công", f"Đã thêm Nhà cung cấp #{new_id} thành công!"
            )
            self.accept()
        except Exception as e:
            conn.rollback()
            QtWidgets.QMessageBox.critical(self, "Lỗi CSDL", f"Lỗi khi lưu:\n{e}")
        finally:
            conn.close()


# ============================================================
# DIALOG SỬA NHÀ CUNG CẤP
# ============================================================
class EditSupplier(QtWidgets.QDialog):
    """
    Chỉnh sửa thông tin NCC và danh sách SP cung cấp.

    Luồng:
      - Load thông tin cũ vào txtOnlyReadMaNCC (readonly), txtSDT, txtEmail, txtDiaChi.
      - Load danh sách SP hiện tại (SupplierID = id) vào tblDanhSachSPCungCap.
      - Người dùng thêm/xóa SP, sửa thông tin liên hệ.
      - btnLuu → cập nhật DB.
    """

    def __init__(self, data, parent=None):
        super().__init__(parent)
        uic.loadUi(os.path.join(UI_PATH, "editNCC.ui"), self)

        self.data          = data
        self._product_rows = []
        self._price_map    = {}

        self._setup_table()
        self._load_products_combo()
        self._load_old_data()
        self._connect_signals()

    # ---------- Cài đặt bảng ----------
    def _setup_table(self):
        tbl = self.tblDanhSachSPCungCap
        tbl.verticalHeader().setVisible(False)
        tbl.setEditTriggers(QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)
        tbl.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        hdr = tbl.horizontalHeader()
        hdr.setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode.Stretch)
        hdr.setSectionResizeMode(4, QtWidgets.QHeaderView.ResizeMode.Fixed)
        tbl.setColumnWidth(4, 80)

    # ---------- Load combo sản phẩm ----------
    def _load_products_combo(self):
        db   = DatabaseManager()
        conn = db.get_connection()
        if not conn:
            return
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT ProductID, ProductName, UnitPrice FROM Products ORDER BY ProductName"
            )
            self.btnTenSP.clear()
            for pid, pname, price in cursor.fetchall():
                self.btnTenSP.addItem(pname, pid)
                self._price_map[pid] = float(price)
            self.btnTenSP.currentIndexChanged.connect(self._on_sp_changed)
            self._on_sp_changed()
        finally:
            conn.close()

    def _on_sp_changed(self):
        pid = self.btnTenSP.currentData()
        self.txtReadOnlyMaSP.setText(str(pid) if pid else "")

    # ---------- Load dữ liệu cũ ----------
    def _load_old_data(self):
        d = self.data
        self.txtOnlyReadMaNCC.setText(str(d["id"]))
        self.txtSDT.setText(d.get("sdt", ""))
        self.txtEmail.setText(d.get("email", ""))
        self.txtDiaChi.setText(d.get("dia_chi", ""))

        # Load SP đã từng nhập từ NCC này (qua Purchase_Details)
        db   = DatabaseManager()
        conn = db.get_connection()
        if not conn:
            return
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT DISTINCT p.ProductID, p.ProductName,
                       p.UnitsInStock, pd.UnitCost
                FROM   Purchase_Details pd
                JOIN   Purchase_Orders  po ON pd.PurchaseOrderID = po.PurchaseOrderID
                JOIN   Products         p  ON pd.ProductID       = p.ProductID
                WHERE  po.SupplierID = ?
                ORDER  BY p.ProductID
            """, (d["id"],))
            for row in cursor.fetchall():
                rd = {
                    "pid":   row[0],
                    "pname": row[1],
                    "qty":   row[2],
                    "price": float(row[3]),
                }
                self._product_rows.append(rd)
                self._insert_table_row(rd)
        finally:
            conn.close()

    # ---------- Kết nối tín hiệu ----------
    def _connect_signals(self):
        self.btnThem.clicked.connect(self._on_them_sp)
        self.btnLuu.clicked.connect(self._on_luu)
        self.btnHuy.clicked.connect(self.reject)

    # ---------- Thêm SP vào bảng ----------
    def _on_them_sp(self):
        pid   = self.btnTenSP.currentData()
        pname = self.btnTenSP.currentText()
        qty   = self.spnSoLuong.value()

        price_text = self.txtGiaNhap.text().strip().replace(",", "")
        if not price_text:
            QtWidgets.QMessageBox.warning(self, "Thiếu thông tin", "Vui lòng nhập Giá nhập!")
            return
        try:
            price = float(price_text)
            if price <= 0:
                raise ValueError
        except ValueError:
            QtWidgets.QMessageBox.warning(self, "Lỗi", "Giá nhập phải là số dương!")
            return

        for rd in self._product_rows:
            if rd["pid"] == pid:
                QtWidgets.QMessageBox.warning(self, "Trùng", "Sản phẩm này đã có trong danh sách!")
                return

        row_data = {"pid": pid, "pname": pname, "qty": qty, "price": price}
        self._product_rows.append(row_data)
        self._insert_table_row(row_data)
        self.spnSoLuong.setValue(0)
        self.txtGiaNhap.clear()

    def _insert_table_row(self, row_data):
        tbl = self.tblDanhSachSPCungCap
        i   = tbl.rowCount()
        tbl.insertRow(i)
        tbl.setItem(i, 0, QtWidgets.QTableWidgetItem(str(row_data["pid"])))
        tbl.setItem(i, 1, QtWidgets.QTableWidgetItem(row_data["pname"]))
        tbl.setItem(i, 2, QtWidgets.QTableWidgetItem(str(row_data["qty"])))
        tbl.setItem(i, 3, QtWidgets.QTableWidgetItem(f"{row_data['price']:,.0f} VNĐ"))

        btn_xoa = QtWidgets.QPushButton("Xóa")
        btn_xoa.setStyleSheet(
            "background-color:#ef4444;color:white;font-weight:bold;"
            "border:none;border-radius:4px;padding:4px;"
        )
        btn_xoa.clicked.connect(lambda _, r=row_data: self._remove_row(r))
        tbl.setCellWidget(i, 4, btn_xoa)

    def _remove_row(self, row_data):
        if row_data in self._product_rows:
            self._product_rows.remove(row_data)
        self._refresh_table()

    def _refresh_table(self):
        self.tblDanhSachSPCungCap.setRowCount(0)
        for rd in self._product_rows:
            self._insert_table_row(rd)

    # ---------- Lưu ----------
    def _on_luu(self):
        sdt     = self.txtSDT.text().strip()
        email   = self.txtEmail.text().strip()
        dia_chi = self.txtDiaChi.text().strip()

        if not sdt:
            QtWidgets.QMessageBox.warning(self, "Thiếu thông tin", "Vui lòng nhập Số điện thoại!")
            return

        sup_id = self.data["id"]

        db   = DatabaseManager()
        conn = db.get_connection()
        if not conn:
            return
        try:
            cursor = conn.cursor()

            # Kiểm tra trùng SĐT (trừ chính nó)
            cursor.execute(
                "SELECT COUNT(*) FROM Suppliers WHERE SupplierPhone = ? AND SupplierID != ?",
                (sdt, sup_id)
            )
            if cursor.fetchone()[0] > 0:
                QtWidgets.QMessageBox.warning(self, "Từ chối", "Số điện thoại này đã được sử dụng!")
                return

            # Cập nhật thông tin NCC
            cursor.execute("""
                UPDATE Suppliers
                SET SupplierPhone = ?, SupplierEmail = ?, SupplierAddress = ?
                WHERE SupplierID = ?
            """, (sdt, email, dia_chi, sup_id))

            # Products không có cột SupplierID — liên kết NCC-SP qua Purchase_Orders
            # Không cần cập nhật Products khi sửa thông tin NCC

            conn.commit()
            QtWidgets.QMessageBox.information(self, "Thành công", "Đã cập nhật Nhà cung cấp!")
            self.accept()
        except Exception as e:
            conn.rollback()
            QtWidgets.QMessageBox.critical(self, "Lỗi CSDL", f"Lỗi khi lưu:\n{e}")
        finally:
            conn.close()


# ============================================================
# DIALOG XÓA NHÀ CUNG CẤP
# ============================================================
class DeleteSupplier(QtWidgets.QDialog):
    """
    Xác nhận xóa nhà cung cấp.
    lblCanhBao giữ nguyên nội dung từ UI.
    btnXoa → kiểm tra ràng buộc → xóa DB.
    btnHuy → đóng.
    """

    def __init__(self, data, parent=None):
        super().__init__(parent)
        uic.loadUi(os.path.join(UI_PATH, "deleteNCC.ui"), self)

        self.data = data
        self.btnXoa.clicked.connect(self._on_xoa)
        self.btnHuy.clicked.connect(self.reject)

    def _on_xoa(self):
        sup_id   = self.data["id"]
        sup_name = self.data["ten"]

        db   = DatabaseManager()
        conn = db.get_connection()
        if not conn:
            return
        try:
            cursor = conn.cursor()

            # Ràng buộc: còn đơn nhập hàng (Products không có SupplierID nên check qua Purchase_Orders)
            cursor.execute(
                "SELECT COUNT(*) FROM Purchase_Orders WHERE SupplierID = ?", (sup_id,)
            )
            if cursor.fetchone()[0] > 0:
                QtWidgets.QMessageBox.warning(
                    self, "Từ chối",
                    f"'{sup_name}' đã có lịch sử đơn nhập hàng. Không thể xóa!"
                )
                return

            cursor.execute("DELETE FROM Suppliers WHERE SupplierID = ?", (sup_id,))
            conn.commit()
            QtWidgets.QMessageBox.information(self, "Thành công", "Đã xóa nhà cung cấp!")
            self.accept()
        except Exception as e:
            conn.rollback()
            QtWidgets.QMessageBox.critical(self, "Lỗi CSDL", f"Lỗi khi xóa:\n{e}")
        finally:
            conn.close()


# ============================================================
# BỘ QUẢN LÝ NHÀ CUNG CẤP – CONTROLLER
# ============================================================
class SupplierManager:
    """
    Controller cho trang Nhà Cung Cấp.

    Khai báo trong main.py → setup_module_supplier():
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

    Bảng tblDanhSachNCC cần có 7 cột trong mainQLCH.ui:
        Mã NCC | Tên NCC | SĐT | Email | Địa chỉ | Số SP | Thao tác
    """

    def __init__(self, table_widget, txt_search=None, btn_search=None):
        self.table      = table_widget
        self.txt_search = txt_search

        # Callback từ main.py để nhảy sang trang Nhập hàng
        self.open_purchase_order_callback = None

        self._init_ui()

        if btn_search and txt_search:
            btn_search.clicked.connect(self.load_data)
            txt_search.returnPressed.connect(self.load_data)

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

    # ---------- Load dữ liệu bảng chính ----------
    def load_data(self):
        db   = DatabaseManager()
        conn = db.get_connection()
        if not conn:
            return

        kw    = self.txt_search.text().strip() if self.txt_search else ""
        # Đếm SP qua Purchase_Details vì Products không có cột SupplierID
        query = """
            SELECT s.SupplierID, s.SupplierName, s.SupplierPhone,
                   s.SupplierEmail, s.SupplierAddress,
                   COUNT(DISTINCT pd.ProductID) AS ProductCount
            FROM   Suppliers s
            LEFT JOIN Purchase_Orders  po ON po.SupplierID      = s.SupplierID
            LEFT JOIN Purchase_Details pd ON pd.PurchaseOrderID = po.PurchaseOrderID
        """
        params = ()
        if kw:
            query += " WHERE s.SupplierName LIKE ? OR s.SupplierPhone LIKE ?"
            params = (f"%{kw}%", f"%{kw}%")

        query += """
            GROUP BY s.SupplierID, s.SupplierName, s.SupplierPhone,
                     s.SupplierEmail, s.SupplierAddress
            ORDER BY s.SupplierID DESC
        """

        try:
            cursor = conn.cursor()
            cursor.execute(query, params)
            rows = cursor.fetchall()

            self.table.setRowCount(0)
            for i, row in enumerate(rows):
                self.table.insertRow(i)
                self.table.setItem(i, 0, QtWidgets.QTableWidgetItem(str(row[0])))
                self.table.setItem(i, 1, QtWidgets.QTableWidgetItem(row[1]))
                self.table.setItem(i, 2, QtWidgets.QTableWidgetItem(row[2] or ""))
                self.table.setItem(i, 3, QtWidgets.QTableWidgetItem(row[3] or ""))
                self.table.setItem(i, 4, QtWidgets.QTableWidgetItem(row[4] or ""))

                count_item = QtWidgets.QTableWidgetItem(str(row[5]))
                count_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table.setItem(i, 5, count_item)

                item_data = {
                    "id":      row[0],
                    "ten":     row[1],
                    "sdt":     row[2] or "",
                    "email":   row[3] or "",
                    "dia_chi": row[4] or "",
                }
                self._add_action_buttons(i, item_data)
        except Exception as e:
            print(f"Lỗi load NCC: {e}")
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
        ViewSupplier(
            item_data,
            open_purchase_order_callback=self.open_purchase_order_callback,
            edit_callback=self.open_edit
        ).exec()

    def open_add(self):
        if AddSupplier().exec():
            self.load_data()

    def open_edit(self, item_data):
        if EditSupplier(item_data).exec():
            self.load_data()

    def open_delete(self, item_data):
        if DeleteSupplier(item_data).exec():
            self.load_data()