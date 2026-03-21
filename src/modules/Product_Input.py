"""
Module Nhập Hàng (Purchase Orders)
Kết nối với các file UI:
  - viewDonNhap.ui   → ViewPurchaseOrder
  - addDonNhap.ui    → AddPurchaseOrder
  - editDonNhap.ui   → EditPurchaseOrder
  - deleteDonNhap.ui → DeletePurchaseOrder

Widget quan trọng:

  viewDonNhap.ui:
    tblDanhSachSPNhap (5 cột: Mã SP|Tên SP|Số lượng|Đơn giá nhập|Thao tác)
    btnSua
    lblHienThiMaDonNhap, lblHienThiNCC, lblHienThiNgayNhap,
    lblHienThiTongTien,  lblHienThiTrangThai

  addDonNhap.ui:
    txtReadOnlyMaSP (auto-fill khi đổi combo SP)
    cbTenSanPham, spnSoLuong, txtDonGiaNhap, btnThem
    tblDanhSachSPNhap
    txtReadOnlyMaDonNhap (ID mới, readonly)
    cbNCC, dteNgayNhap, lblHienThiTongTien, cbTrangThai
    btnLuu, btnHuy

  editDonNhap.ui:  giống add nhưng load dữ liệu cũ

  deleteDonNhap.ui:  lblCanhBao, btnXoa, btnHuy
"""

import os
from PyQt6 import uic, QtWidgets
from PyQt6.QtCore import Qt, QDateTime, QTimer, QDate
from src.database.db_connection import DatabaseManager

def _get_purchase_status_values(cursor):
    """Lấy giá trị hợp lệ từ CHECK constraint hoặc dữ liệu thực của Purchase_Orders.Status."""
    try:
        cursor.execute("""
            SELECT cc.definition
            FROM   sys.check_constraints cc
            JOIN   sys.columns col ON cc.parent_object_id = col.object_id
                                  AND cc.parent_column_id = col.column_id
            JOIN   sys.tables t   ON cc.parent_object_id = t.object_id
            WHERE  t.name = 'Purchase_Orders' AND col.name = 'Status'
        """)
        row = cursor.fetchone()
        if row:
            import re as _re
            vals = _re.findall(r"'([^']+)'", row[0])
            if vals:
                print(f"[INFO] Purchase_Orders.Status CHECK: {vals}")
                return vals
    except Exception as e:
        print(f"[WARN] Không đọc CHECK constraint: {e}")
    try:
        cursor.execute(
            "SELECT DISTINCT Status FROM Purchase_Orders WHERE Status IS NOT NULL ORDER BY Status"
        )
        vals = [r[0] for r in cursor.fetchall()]
        if vals:
            print(f"[INFO] Purchase_Orders.Status distinct: {vals}")
            return vals
    except Exception:
        pass
    return ["Chưa nhận hàng", "Đã nhận hàng", "Đã hủy"]



CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR    = os.path.dirname(os.path.dirname(CURRENT_DIR))
UI_PATH     = os.path.join(ROOT_DIR, "ui", "modules_ui", "NhapHang")


def _setup_sp_table(tbl):
    tbl.verticalHeader().setVisible(False)
    tbl.setEditTriggers(QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)
    tbl.setFocusPolicy(Qt.FocusPolicy.NoFocus)
    hdr = tbl.horizontalHeader()
    hdr.setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode.Stretch)
    hdr.setSectionResizeMode(4, QtWidgets.QHeaderView.ResizeMode.Fixed)
    tbl.setColumnWidth(4, 80)


# ============================================================
# DIALOG XEM CHI TIẾT ĐƠN NHẬP
# ============================================================
class ViewPurchaseOrder(QtWidgets.QDialog):
    def __init__(self, po_id, edit_callback=None, parent=None):
        super().__init__(parent)
        uic.loadUi(os.path.join(UI_PATH, "viewDonNhap.ui"), self)
        self.po_id         = po_id
        self.edit_callback = edit_callback
        self._po_data      = {}

        _setup_sp_table(self.tblDanhSachSPNhap)
        self.tblDanhSachSPNhap.setColumnHidden(4, True)  # ẩn cột Thao tác khi xem

        self._load_info()
        self._load_products()
        self.btnSua.clicked.connect(self._on_sua)

    def _load_info(self):
        db   = DatabaseManager()
        conn = db.get_connection()
        if not conn:
            return
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT po.PurchaseOrderID, s.SupplierName, po.PurchasedDate,
                       po.TotalAmount, po.Status, po.SupplierID, po.EmployeeID
                FROM   Purchase_Orders po
                JOIN   Suppliers s ON po.SupplierID = s.SupplierID
                WHERE  po.PurchaseOrderID = ?
            """, (self.po_id,))
            row = cursor.fetchone()
            if row:
                self._po_data = {
                    "id": row[0], "sup_id": row[5], "emp_id": row[6],
                    "sup_name": row[1], "ngay_nhap": row[2],
                    "tong_tien": float(row[3]), "status": row[4],
                }
                self.lblHienThiMaDonNhap.setText(str(row[0]))
                self.lblHienThiNCC.setText(row[1])
                self.lblHienThiNgayNhap.setText(
                    row[2].strftime("%d/%m/%Y") if row[2] else "—"
                )
                self.lblHienThiTongTien.setText(f"{row[3]:,.0f} VNĐ")
                self.lblHienThiTrangThai.setText(row[4])
                # Màu theo nội dung status
                def _status_color(s):
                    s = s.lower()
                    if "nhận" in s and "chưa" not in s and "chờ" not in s: return "#15803d"
                    if "hủy" in s: return "#dc2626"
                    return "#b45309"
                color = {st: _status_color(st) for st in [self._po_data.get("status","")]}
                self.lblHienThiTrangThai.setStyleSheet(
                    f"font-weight:bold;color:{color.get(row[4], '#111827')};"
                )
        finally:
            conn.close()

    def _load_products(self):
        db   = DatabaseManager()
        conn = db.get_connection()
        if not conn:
            return
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT pd.ProductID, p.ProductName, pd.PurchasedQuantity, pd.UnitCost
                FROM   Purchase_Details pd
                JOIN   Products p ON pd.ProductID = p.ProductID
                WHERE  pd.PurchaseOrderID = ?
                ORDER  BY pd.ProductID
            """, (self.po_id,))
            rows = cursor.fetchall()
            tbl  = self.tblDanhSachSPNhap
            tbl.setRowCount(0)
            for i, r in enumerate(rows):
                tbl.insertRow(i)
                tbl.setItem(i, 0, QtWidgets.QTableWidgetItem(str(r[0])))
                tbl.setItem(i, 1, QtWidgets.QTableWidgetItem(r[1]))
                tbl.setItem(i, 2, QtWidgets.QTableWidgetItem(str(r[2])))
                tbl.setItem(i, 3, QtWidgets.QTableWidgetItem(f"{r[3]:,.0f} VNĐ"))
        finally:
            conn.close()

    def _on_sua(self):
        self.close()
        if self.edit_callback and self._po_data:
            self.edit_callback(self._po_data)


# ============================================================
# DIALOG THÊM ĐƠN NHẬP
# ============================================================
class AddPurchaseOrder(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        uic.loadUi(os.path.join(UI_PATH, "addDonNhap.ui"), self)
        self._product_rows = []
        self._price_map    = {}

        _setup_sp_table(self.tblDanhSachSPNhap)
        self._fill_new_id()
        self._load_combos()
        self._setup_datetime()
        self._connect_signals()

    def _fill_new_id(self):
        db   = DatabaseManager()
        conn = db.get_connection()
        if not conn:
            return
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT ISNULL(MAX(PurchaseOrderID), 0) FROM Purchase_Orders")
            self.txtReadOnlyMaDonNhap.setText(str(cursor.fetchone()[0] + 1))
        finally:
            conn.close()

    def _load_combos(self):
        db   = DatabaseManager()
        conn = db.get_connection()
        if not conn:
            return
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT ProductID, ProductName, UnitPrice FROM Products ORDER BY ProductName")
            self.cbTenSanPham.clear()
            for pid, pname, price in cursor.fetchall():
                self.cbTenSanPham.addItem(pname, pid)
                self._price_map[pid] = float(price)

            cursor.execute("SELECT SupplierID, SupplierName FROM Suppliers ORDER BY SupplierName")
            self.cbNCC.clear()
            for sid, sname in cursor.fetchall():
                self.cbNCC.addItem(sname, sid)

            self.cbTrangThai.clear()
            self.cbTrangThai.addItems(_get_purchase_status_values(cursor))
        finally:
            conn.close()

        self.cbTenSanPham.currentIndexChanged.connect(self._on_sp_changed)
        self._on_sp_changed()

    def _on_sp_changed(self):
        pid = self.cbTenSanPham.currentData()
        self.txtReadOnlyMaSP.setText(str(pid) if pid else "")

    def _setup_datetime(self):
        self.dteNgayNhap.setCalendarPopup(True)
        self.dteNgayNhap.setDateTime(QDateTime.currentDateTime())

    def _connect_signals(self):
        self.btnThem.clicked.connect(self._on_them_sp)
        self.btnLuu.clicked.connect(self._on_luu)
        self.btnHuy.clicked.connect(self.reject)

    def _on_them_sp(self):
        pid        = self.cbTenSanPham.currentData()
        pname      = self.cbTenSanPham.currentText()
        qty        = self.spnSoLuong.value()
        price_text = self.txtDonGiaNhap.text().strip().replace(",", "")

        if not price_text:
            QtWidgets.QMessageBox.warning(self, "Thiếu", "Vui lòng nhập Đơn giá nhập!"); return
        try:
            price = float(price_text)
            if price <= 0: raise ValueError
        except ValueError:
            QtWidgets.QMessageBox.warning(self, "Lỗi", "Đơn giá nhập phải là số dương!"); return
        if qty <= 0:
            QtWidgets.QMessageBox.warning(self, "Lỗi", "Số lượng phải lớn hơn 0!"); return
        for rd in self._product_rows:
            if rd["pid"] == pid:
                QtWidgets.QMessageBox.warning(self, "Trùng", "Sản phẩm đã có trong đơn!"); return

        rd = {"pid": pid, "pname": pname, "qty": qty, "price": price}
        self._product_rows.append(rd)
        self._insert_row(rd)
        self._update_total()
        self.spnSoLuong.setValue(1)
        self.txtDonGiaNhap.clear()

    def _insert_row(self, rd):
        tbl = self.tblDanhSachSPNhap
        i   = tbl.rowCount()
        tbl.insertRow(i)
        tbl.setItem(i, 0, QtWidgets.QTableWidgetItem(str(rd["pid"])))
        tbl.setItem(i, 1, QtWidgets.QTableWidgetItem(rd["pname"]))
        tbl.setItem(i, 2, QtWidgets.QTableWidgetItem(str(rd["qty"])))
        tbl.setItem(i, 3, QtWidgets.QTableWidgetItem(f"{rd['price']:,.0f} VNĐ"))
        btn = QtWidgets.QPushButton("Xóa")
        btn.setStyleSheet("background-color:#ef4444;color:white;font-weight:bold;"
                          "border:none;border-radius:4px;padding:4px;")
        btn.clicked.connect(lambda _, r=rd: self._remove_row(r))
        tbl.setCellWidget(i, 4, btn)

    def _remove_row(self, rd):
        if rd in self._product_rows: self._product_rows.remove(rd)
        self._refresh(); self._update_total()

    def _refresh(self):
        self.tblDanhSachSPNhap.setRowCount(0)
        for rd in self._product_rows: self._insert_row(rd)

    def _update_total(self):
        total = sum(r["qty"] * r["price"] for r in self._product_rows)
        self.lblHienThiTongTien.setText(f"{total:,.0f} VNĐ")

    def _on_luu(self):
        if not self._product_rows:
            QtWidgets.QMessageBox.warning(self, "Thiếu", "Vui lòng thêm ít nhất 1 sản phẩm!"); return

        sup_id = self.cbNCC.currentData()
        status = self.cbTrangThai.currentText()
        ngay   = self.dteNgayNhap.dateTime().toPyDateTime()
        total  = sum(r["qty"] * r["price"] for r in self._product_rows)

        db   = DatabaseManager()
        conn = db.get_connection()
        if not conn: return
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT TOP 1 EmployeeID FROM Employees")
            emp_row = cursor.fetchone()
            emp_id  = emp_row[0] if emp_row else 1

            cursor.execute("SELECT ISNULL(MAX(PurchaseOrderID), 0) FROM Purchase_Orders")
            new_id = cursor.fetchone()[0] + 1

            cursor.execute("""
                INSERT INTO Purchase_Orders
                    (PurchaseOrderID, SupplierID, EmployeeID,
                     PurchasedDate, ExpectedDate, TotalAmount, Status)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (new_id, sup_id, emp_id, ngay, ngay, total, status))

            for rd in self._product_rows:
                cursor.execute("""
                    INSERT INTO Purchase_Details
                        (PurchaseOrderID, ProductID, PurchasedQuantity, UnitCost, SubTotal)
                    VALUES (?, ?, ?, ?, ?)
                """, (new_id, rd["pid"], rd["qty"], rd["price"], rd["qty"] * rd["price"]))
                if "nhận" in status.lower() and "chưa" not in status.lower() and "chờ" not in status.lower():
                    cursor.execute("""
                        UPDATE Products SET UnitsInStock = UnitsInStock + ?, Status = N'Còn hàng'
                        WHERE ProductID = ?
                    """, (rd["qty"], rd["pid"]))

            conn.commit()
            QtWidgets.QMessageBox.information(self, "Thành công", f"Đã tạo đơn nhập #{new_id}!")
            self.accept()
        except Exception as e:
            conn.rollback()
            QtWidgets.QMessageBox.critical(self, "Lỗi CSDL", f"{e}")
        finally:
            conn.close()


# ============================================================
# DIALOG SỬA ĐƠN NHẬP
# ============================================================
class EditPurchaseOrder(QtWidgets.QDialog):
    def __init__(self, po_data, parent=None):
        super().__init__(parent)
        uic.loadUi(os.path.join(UI_PATH, "editDonNhap.ui"), self)
        self.po_data       = po_data
        self._product_rows = []
        self._price_map    = {}
        self._old_status   = po_data.get("status", "")

        _setup_sp_table(self.tblDanhSachSPNhap)
        self._load_combos()
        self._load_old_data()
        self._connect_signals()

    def _load_combos(self):
        db   = DatabaseManager()
        conn = db.get_connection()
        if not conn: return
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT ProductID, ProductName, UnitPrice FROM Products ORDER BY ProductName")
            self.cbTenSanPham.clear()
            for pid, pname, price in cursor.fetchall():
                self.cbTenSanPham.addItem(pname, pid)
                self._price_map[pid] = float(price)

            cursor.execute("SELECT SupplierID, SupplierName FROM Suppliers ORDER BY SupplierName")
            self.cbNCC.clear()
            for sid, sname in cursor.fetchall():
                self.cbNCC.addItem(sname, sid)

            self.cbTrangThai.clear()
            self.cbTrangThai.addItems(_get_purchase_status_values(cursor))
        finally:
            conn.close()

        self.cbTenSanPham.currentIndexChanged.connect(self._on_sp_changed)
        self._on_sp_changed()

    def _on_sp_changed(self):
        pid = self.cbTenSanPham.currentData()
        self.txtReadOnlyMaSP.setText(str(pid) if pid else "")

    def _load_old_data(self):
        d = self.po_data
        self.txtReadOnlyMaDonNhap.setText(str(d["id"]))

        idx = self.cbNCC.findData(d.get("sup_id"))
        if idx >= 0: self.cbNCC.setCurrentIndex(idx)

        if d.get("ngay_nhap"):
            import datetime
            ng = d["ngay_nhap"]
            if isinstance(ng, (datetime.date, datetime.datetime)):
                self.dteNgayNhap.setCalendarPopup(True)
                self.dteNgayNhap.setDateTime(
                    QDateTime(ng.year, ng.month, ng.day, 0, 0, 0)
                )

        idx2 = self.cbTrangThai.findText(d.get("status", ""))
        if idx2 >= 0: self.cbTrangThai.setCurrentIndex(idx2)

        # Load SP cũ
        db   = DatabaseManager()
        conn = db.get_connection()
        if not conn: return
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT pd.ProductID, p.ProductName, pd.PurchasedQuantity, pd.UnitCost
                FROM   Purchase_Details pd
                JOIN   Products p ON pd.ProductID = p.ProductID
                WHERE  pd.PurchaseOrderID = ?
            """, (d["id"],))
            for row in cursor.fetchall():
                rd = {"pid": row[0], "pname": row[1], "qty": row[2], "price": float(row[3])}
                self._product_rows.append(rd)
                self._insert_row(rd)
        finally:
            conn.close()

        self._update_total()

    def _connect_signals(self):
        self.btnThem.clicked.connect(self._on_them_sp)
        self.btnLuu.clicked.connect(self._on_luu)
        self.btnHuy.clicked.connect(self.reject)

    def _on_them_sp(self):
        pid        = self.cbTenSanPham.currentData()
        pname      = self.cbTenSanPham.currentText()
        qty        = self.spnSoLuong.value()
        price_text = self.txtDonGiaNhap.text().strip().replace(",", "")

        if not price_text:
            QtWidgets.QMessageBox.warning(self, "Thiếu", "Vui lòng nhập Đơn giá nhập!"); return
        try:
            price = float(price_text)
            if price <= 0: raise ValueError
        except ValueError:
            QtWidgets.QMessageBox.warning(self, "Lỗi", "Đơn giá nhập phải là số dương!"); return
        if qty <= 0:
            QtWidgets.QMessageBox.warning(self, "Lỗi", "Số lượng phải lớn hơn 0!"); return
        for rd in self._product_rows:
            if rd["pid"] == pid:
                QtWidgets.QMessageBox.warning(self, "Trùng", "Sản phẩm đã có trong đơn!"); return

        rd = {"pid": pid, "pname": pname, "qty": qty, "price": price}
        self._product_rows.append(rd)
        self._insert_row(rd)
        self._update_total()
        self.spnSoLuong.setValue(1)
        self.txtDonGiaNhap.clear()

    def _insert_row(self, rd):
        tbl = self.tblDanhSachSPNhap
        i   = tbl.rowCount()
        tbl.insertRow(i)
        tbl.setItem(i, 0, QtWidgets.QTableWidgetItem(str(rd["pid"])))
        tbl.setItem(i, 1, QtWidgets.QTableWidgetItem(rd["pname"]))
        tbl.setItem(i, 2, QtWidgets.QTableWidgetItem(str(rd["qty"])))
        tbl.setItem(i, 3, QtWidgets.QTableWidgetItem(f"{rd['price']:,.0f} VNĐ"))
        btn = QtWidgets.QPushButton("Xóa")
        btn.setStyleSheet("background-color:#ef4444;color:white;font-weight:bold;"
                          "border:none;border-radius:4px;padding:4px;")
        btn.clicked.connect(lambda _, r=rd: self._remove_row(r))
        tbl.setCellWidget(i, 4, btn)

    def _remove_row(self, rd):
        if rd in self._product_rows: self._product_rows.remove(rd)
        self._refresh(); self._update_total()

    def _refresh(self):
        self.tblDanhSachSPNhap.setRowCount(0)
        for rd in self._product_rows: self._insert_row(rd)

    def _update_total(self):
        total = sum(r["qty"] * r["price"] for r in self._product_rows)
        self.lblHienThiTongTien.setText(f"{total:,.0f} VNĐ")

    def _on_luu(self):
        if not self._product_rows:
            QtWidgets.QMessageBox.warning(self, "Thiếu", "Vui lòng thêm ít nhất 1 sản phẩm!"); return

        po_id      = self.po_data["id"]
        sup_id     = self.cbNCC.currentData()
        new_status = self.cbTrangThai.currentText()
        ngay       = self.dteNgayNhap.dateTime().toPyDateTime()
        total      = sum(r["qty"] * r["price"] for r in self._product_rows)

        db   = DatabaseManager()
        conn = db.get_connection()
        if not conn: return
        try:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE Purchase_Orders
                SET SupplierID=?, PurchasedDate=?, TotalAmount=?, Status=?
                WHERE PurchaseOrderID=?
            """, (sup_id, ngay, total, new_status, po_id))

            cursor.execute("DELETE FROM Purchase_Details WHERE PurchaseOrderID=?", (po_id,))
            for rd in self._product_rows:
                cursor.execute("""
                    INSERT INTO Purchase_Details
                        (PurchaseOrderID, ProductID, PurchasedQuantity, UnitCost, SubTotal)
                    VALUES (?,?,?,?,?)
                """, (po_id, rd["pid"], rd["qty"], rd["price"], rd["qty"] * rd["price"]))

            # Cộng tồn kho nếu vừa đổi sang "Đã nhận"
            received = lambda s: "nhận" in s.lower() and "chưa" not in s.lower() and "chờ" not in s.lower()
            if received(new_status) and not received(self._old_status):
                for rd in self._product_rows:
                    cursor.execute("""
                        UPDATE Products SET UnitsInStock=UnitsInStock+?, Status=N'Còn hàng'
                        WHERE ProductID=?
                    """, (rd["qty"], rd["pid"]))

            conn.commit()
            QtWidgets.QMessageBox.information(self, "Thành công", "Đã cập nhật đơn nhập!")
            self.accept()
        except Exception as e:
            conn.rollback()
            QtWidgets.QMessageBox.critical(self, "Lỗi CSDL", f"{e}")
        finally:
            conn.close()


# ============================================================
# DIALOG XÓA ĐƠN NHẬP
# ============================================================
class DeletePurchaseOrder(QtWidgets.QDialog):
    def __init__(self, po_data, parent=None):
        super().__init__(parent)
        uic.loadUi(os.path.join(UI_PATH, "deleteDonNhap.ui"), self)
        self.po_data = po_data
        self.btnXoa.clicked.connect(self._on_xoa)
        self.btnHuy.clicked.connect(self.reject)

    def _on_xoa(self):
        st = self.po_data.get("status", "")
        if "nhận" in st.lower() and "chưa" not in st.lower() and "chờ" not in st.lower():
            QtWidgets.QMessageBox.warning(
                self, "Từ chối",
                "Không thể xóa đơn nhập đã nhận hàng!\n"
                "Vui lòng đổi trạng thái sang 'Đã hủy' trước."
            )
            return

        po_id = self.po_data["id"]
        db    = DatabaseManager()
        conn  = db.get_connection()
        if not conn: return
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM Purchase_Details WHERE PurchaseOrderID=?", (po_id,))
            cursor.execute("DELETE FROM Purchase_Orders  WHERE PurchaseOrderID=?", (po_id,))
            conn.commit()
            QtWidgets.QMessageBox.information(self, "Thành công", "Đã xóa đơn nhập hàng!")
            self.accept()
        except Exception as e:
            conn.rollback()
            QtWidgets.QMessageBox.critical(self, "Lỗi CSDL", f"{e}")
        finally:
            conn.close()


# ============================================================
# BỘ QUẢN LÝ NHẬP HÀNG – CONTROLLER
# ============================================================
class PurchaseManager:
    """
    Controller cho trang Nhập Hàng.

    Khai báo trong main.py → setup_module_purchase():
        if not hasattr(self, 'tblDanhSachDonNhap'): return
        txt_search = self.get_widget(['txtTimNhapHang'],      QtWidgets.QLineEdit)
        cb_status  = self.get_widget(['cbTrangThaiNhapHang'], QtWidgets.QComboBox)
        self.purchase_manager = PurchaseManager(self.tblDanhSachDonNhap, txt_search, cb_status)
        if hasattr(self, 'btnNhapHang'):
            self.btnNhapHang.clicked.connect(
                lambda: self.change_page(self.pageNhapHang, self.purchase_manager.load_data)
            )
        if hasattr(self, 'btnThemDonNhap'):
            self.btnThemDonNhap.clicked.connect(self.purchase_manager.open_add)

    Bảng tblDanhSachDonNhap cần 6 cột trong mainQLCH.ui:
        Mã đơn | Ngày nhập | Nhà cung cấp | Tổng tiền | Trạng thái | Thao tác
    """

    def __init__(self, table_widget, txt_search=None, cb_ncc=None,
                 dte_from=None, dte_to=None):
        self.table      = table_widget
        self.txt_search = txt_search
        self.cb_ncc     = cb_ncc     # QComboBox lọc theo NCC
        self.cb_status  = None       # không dùng cb_status nữa
        self.dte_from   = dte_from
        self.dte_to     = dte_to
        self._init_ui()
        self._init_filters()

    def _init_ui(self):
        tbl = self.table
        tbl.verticalHeader().setVisible(False)
        tbl.setEditTriggers(QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)
        tbl.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        tbl.setAlternatingRowColors(True)
        hdr  = tbl.horizontalHeader()
        hdr.setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode.Stretch)
        last = tbl.columnCount() - 1
        hdr.setSectionResizeMode(last, QtWidgets.QHeaderView.ResizeMode.Fixed)
        tbl.setColumnWidth(last, 200)

    def _init_filters(self):
        if self.txt_search:
            self._search_timer = QTimer()
            self._search_timer.setSingleShot(True)
            self._search_timer.setInterval(300)
            self._search_timer.timeout.connect(self.load_data)
            self.txt_search.textChanged.connect(self._search_timer.start)
        # Kết nối DateTimeEdit lọc khoảng thời gian
        if self.dte_from:
            self.dte_from.setCalendarPopup(True)
            self.dte_from.setDisplayFormat('dd/MM/yyyy')
            self.dte_from.setDate(QDate(QDate.currentDate().year(), 1, 1))
            self.dte_from.dateChanged.connect(self.load_data)
        if self.dte_to:
            self.dte_to.setCalendarPopup(True)
            self.dte_to.setDisplayFormat('dd/MM/yyyy')
            self.dte_to.setDate(QDate.currentDate())
            self.dte_to.dateChanged.connect(self.load_data)
        # Populate cbLocNCC với danh sách nhà cung cấp
        if self.cb_ncc:
            db2   = DatabaseManager()
            conn2 = db2.get_connection()
            if conn2:
                try:
                    self.cb_ncc.blockSignals(True)
                    self.cb_ncc.clear()
                    self.cb_ncc.addItem("Tất cả NCC", 0)
                    cur2 = conn2.cursor()
                    cur2.execute("SELECT SupplierID, SupplierName FROM Suppliers ORDER BY SupplierName")
                    for sid, sname in cur2.fetchall():
                        self.cb_ncc.addItem(sname, sid)
                    self.cb_ncc.blockSignals(False)
                    self.cb_ncc.currentIndexChanged.connect(self.load_data)
                finally:
                    conn2.close()

    def load_data(self):
        db   = DatabaseManager()
        conn = db.get_connection()
        if not conn: return

        query = """
            SELECT po.PurchaseOrderID, po.PurchasedDate, s.SupplierName,
                   po.TotalAmount, po.Status, po.SupplierID, po.EmployeeID
            FROM   Purchase_Orders po
            JOIN   Suppliers s ON po.SupplierID = s.SupplierID
            WHERE  1=1
        """
        params = []

        kw = self.txt_search.text().strip() if self.txt_search else ""
        if kw:
            query += " AND (s.SupplierName LIKE ? OR CAST(po.PurchaseOrderID AS VARCHAR) LIKE ?)"
            params.extend([f"%{kw}%", f"%{kw}%"])

        # Lọc theo NCC
        ncc_val = self.cb_ncc.currentData() if self.cb_ncc else 0
        if ncc_val:
            query += " AND po.SupplierID = ?"
            params.append(ncc_val)

        # Lọc theo khoảng thời gian
        if self.dte_from:
            date_from = self.dte_from.date().toPyDate()
            query += " AND CAST(po.PurchasedDate AS DATE) >= ?"
            params.append(date_from)
        if self.dte_to:
            date_to = self.dte_to.date().toPyDate()
            query += " AND CAST(po.PurchasedDate AS DATE) <= ?"
            params.append(date_to)

        query += " ORDER BY po.PurchasedDate DESC"

        def _clr(s):
            s = s.lower()
            if "nhận" in s and "chưa" not in s and "chờ" not in s:
                return Qt.GlobalColor.darkGreen
            if "hủy" in s: return Qt.GlobalColor.darkRed
            return Qt.GlobalColor.darkYellow

        try:
            cursor = conn.cursor()
            cursor.execute(query, params)
            rows = cursor.fetchall()
            self.table.setRowCount(0)
            for i, row in enumerate(rows):
                self.table.insertRow(i)
                self.table.setItem(i, 0, QtWidgets.QTableWidgetItem(str(row[0])))
                self.table.setItem(i, 1, QtWidgets.QTableWidgetItem(
                    row[1].strftime("%d/%m/%Y") if row[1] else "—"))
                self.table.setItem(i, 2, QtWidgets.QTableWidgetItem(row[2]))
                self.table.setItem(i, 3, QtWidgets.QTableWidgetItem(f"{row[3]:,.0f} VNĐ"))

                si = QtWidgets.QTableWidgetItem(row[4])
                si.setForeground(_clr(row[4]))
                self.table.setItem(i, 4, si)

                po_data = {
                    "id": row[0], "sup_id": row[5], "emp_id": row[6],
                    "sup_name": row[2], "ngay_nhap": row[1],
                    "tong_tien": float(row[3]), "status": row[4],
                }
                self._add_buttons(i, po_data)
        except Exception as e:
            print(f"Lỗi load Nhập hàng: {e}")
        finally:
            conn.close()

    def _add_buttons(self, row_idx, po_data):
        last = self.table.columnCount() - 1
        w    = QtWidgets.QWidget()
        h    = QtWidgets.QHBoxLayout(w)
        h.setContentsMargins(4, 2, 4, 2); h.setSpacing(4)

        s = "padding:5px;font-weight:bold;border-radius:4px;color:white;border:none;"
        bv = QtWidgets.QPushButton("Xem")
        be = QtWidgets.QPushButton("Sửa")
        bd = QtWidgets.QPushButton("Xóa")
        bv.setStyleSheet(f"background-color:#10b981;{s}")
        be.setStyleSheet(f"background-color:#3b82f6;{s}")
        bd.setStyleSheet(f"background-color:#ef4444;{s}")

        bv.clicked.connect(lambda _, d=po_data: self.open_view(d["id"]))
        be.clicked.connect(lambda _, d=po_data: self.open_edit(d))
        bd.clicked.connect(lambda _, d=po_data: self.open_delete(d))

        h.addWidget(bv); h.addWidget(be); h.addWidget(bd)
        self.table.setCellWidget(row_idx, last, w)

    def open_view(self, po_id):
        ViewPurchaseOrder(po_id, edit_callback=self.open_edit).exec()

    def open_add(self):
        if AddPurchaseOrder().exec(): self.load_data()

    def open_edit(self, po_data):
        if EditPurchaseOrder(po_data).exec(): self.load_data()

    def open_delete(self, po_data):
        if DeletePurchaseOrder(po_data).exec(): self.load_data()