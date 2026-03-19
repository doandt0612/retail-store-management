# File khuyến mãi
"""
Module Khuyến Mãi (Promotions)
Kết nối với các file UI:
  - viewKhuyenMai.ui   → ViewPromotion
  - addKhuyenMai.ui    → AddPromotion
  - editKhuyenMai.ui   → EditPromotion
  - deleteKhuyenMai.ui → DeletePromotion

Widget quan trọng trong từng UI:
  viewKhuyenMai.ui:
    tblDanhSachSP (5 cột: Mã KM | Ngày bắt đầu | Ngày kết thúc | Tổng cộng | Thao tác)
    btnSua
    lblHienThiMaSP, lblHienThiTenSP, lblHienThiNgayApDung,
    lblHienThiGiaTriGiam, lblHienThiGiaKM

  addKhuyenMai.ui / editKhuyenMai.ui:
    tblDanhSachSP (6 cột: Mã KM | Sản phẩm áp dụng | Ngày bắt đầu
                          | Ngày kết thúc | Tổng cộng | Thao tác)
    cbSP, btnThemSPCTKM
    txtTenCTKM, dteNgayBatDau, dteNgayKetThuc, txtGiaTriGiam
    btnLuu, btnHuy

  deleteKhuyenMai.ui:
    lblCanhBao, btnXoa, btnHuy
"""

import os
from PyQt6 import uic, QtWidgets
from PyQt6.QtCore import Qt, QDate
from src.database.db_connection import DatabaseManager

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR    = os.path.dirname(os.path.dirname(CURRENT_DIR))
UI_PATH     = os.path.join(ROOT_DIR, "ui", "modules_ui", "KhuyenMai")


# ============================================================
# DIALOG XEM CHI TIẾT KHUYẾN MÃI
# ============================================================
class ViewPromotion(QtWidgets.QDialog):
    """
    Hiển thị chi tiết 1 chương trình khuyến mãi.
    - tblDanhSachSP: danh sách tất cả SP áp dụng.
      Ta đổi tiêu đề cột cho đúng với dữ liệu thực:
        Col 0: Mã SP | Col 1: Tên SP | Col 2: Ngày áp dụng
        Col 3: Giá trị giảm | Col 4: Giá KM
    - Panel phải frame_3: khi click 1 hàng → cập nhật
        lblHienThiMaSP / lblHienThiTenSP / lblHienThiNgayApDung /
        lblHienThiGiaTriGiam / lblHienThiGiaKM
    - btnSua → gọi edit_callback
    """

    def __init__(self, promo_data, edit_callback=None, parent=None):
        super().__init__(parent)
        uic.loadUi(os.path.join(UI_PATH, "viewKhuyenMai.ui"), self)

        self.promo_data    = promo_data
        self.edit_callback = edit_callback

        self._setup_table()
        self._load_promo_products()
        self._connect_signals()

    def _setup_table(self):
        tbl = self.tblDanhSachSP
        tbl.verticalHeader().setVisible(False)
        tbl.setEditTriggers(QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)
        tbl.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        tbl.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows)
        tbl.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode.Stretch)
        # Đổi tiêu đề cột cho khớp với dữ liệu thực
        tbl.setHorizontalHeaderLabels(
            ["Mã SP", "Tên sản phẩm", "Ngày áp dụng", "Giá trị giảm", "Giá KM"]
        )
        # Click hàng → cập nhật panel chi tiết bên phải
        tbl.itemSelectionChanged.connect(self._on_row_selected)

    def _load_promo_products(self):
        db   = DatabaseManager()
        conn = db.get_connection()
        if not conn:
            return
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT pd.ProductID, p.ProductName, pd.ApplicableDate,
                       pd.DiscountValue, pd.DiscountedPrice
                FROM   Promotion_Details pd
                JOIN   Products p ON pd.ProductID = p.ProductID
                WHERE  pd.PromotionID = ?
                ORDER  BY pd.ApplicableDate
            """, (self.promo_data["id"],))

            rows = cursor.fetchall()
            tbl  = self.tblDanhSachSP
            tbl.setRowCount(0)
            for i, r in enumerate(rows):
                tbl.insertRow(i)
                tbl.setItem(i, 0, QtWidgets.QTableWidgetItem(str(r[0])))
                tbl.setItem(i, 1, QtWidgets.QTableWidgetItem(r[1]))
                tbl.setItem(i, 2, QtWidgets.QTableWidgetItem(
                    r[2].strftime("%d/%m/%Y") if r[2] else "—"))
                tbl.setItem(i, 3, QtWidgets.QTableWidgetItem(
                    f"{r[3]:,.0f} VNĐ" if r[3] is not None else "—"))
                tbl.setItem(i, 4, QtWidgets.QTableWidgetItem(
                    f"{r[4]:,.0f} VNĐ" if r[4] is not None else "—"))

            # Tự chọn dòng đầu để hiện panel chi tiết
            if rows:
                tbl.selectRow(0)
        finally:
            conn.close()

    def _on_row_selected(self):
        tbl = self.tblDanhSachSP
        row = tbl.currentRow()
        if row < 0:
            return
        def cell(col):
            item = tbl.item(row, col)
            return item.text() if item else "—"
        self.lblHienThiMaSP.setText(cell(0))
        self.lblHienThiTenSP.setText(cell(1))
        self.lblHienThiNgayApDung.setText(cell(2))
        self.lblHienThiGiaTriGiam.setText(cell(3))
        self.lblHienThiGiaKM.setText(cell(4))

    def _connect_signals(self):
        self.btnSua.clicked.connect(self._on_sua)

    def _on_sua(self):
        self.close()
        if self.edit_callback:
            self.edit_callback(self.promo_data)


# ============================================================
# DIALOG THÊM KHUYẾN MÃI
# ============================================================
class AddPromotion(QtWidgets.QDialog):
    """
    Tạo chương trình khuyến mãi mới.
    Luồng sử dụng:
      1. Nhập Tên chương trình, Ngày bắt đầu, Ngày kết thúc, Giá trị giảm.
      2. Chọn SP trong cbSP → bấm btnThemSPCTKM → SP được thêm vào tblDanhSachSP.
      3. Bấm btnLuu → lưu vào DB.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        uic.loadUi(os.path.join(UI_PATH, "addKhuyenMai.ui"), self)

        self._product_rows = []   # [{pid, pname, original, discount, after}]
        self._price_map    = {}   # {pid: float}

        self._setup_table()
        self._setup_dates()
        self._load_products_combo()
        self._connect_signals()

    def _setup_table(self):
        tbl = self.tblDanhSachSP
        tbl.verticalHeader().setVisible(False)
        tbl.setEditTriggers(QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)
        tbl.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        tbl.setHorizontalHeaderLabels(
            ["Mã SP", "Sản phẩm áp dụng", "Giá gốc", "Giá trị giảm", "Giá sau giảm", "Xóa"]
        )
        hdr = tbl.horizontalHeader()
        hdr.setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode.Stretch)
        hdr.setSectionResizeMode(5, QtWidgets.QHeaderView.ResizeMode.Fixed)
        tbl.setColumnWidth(5, 70)

    def _setup_dates(self):
        today = QDate.currentDate()
        self.dteNgayBatDau.setCalendarPopup(True)
        self.dteNgayKetThuc.setCalendarPopup(True)
        self.dteNgayBatDau.setDate(today)
        self.dteNgayKetThuc.setDate(today.addDays(30))

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
            self.cbSP.clear()
            for pid, pname, price in cursor.fetchall():
                self.cbSP.addItem(f"[{pid}] {pname}", pid)
                self._price_map[pid] = float(price)
        finally:
            conn.close()

    def _connect_signals(self):
        self.btnThemSPCTKM.clicked.connect(self._on_them_sp)
        self.btnLuu.clicked.connect(self._on_luu)
        self.btnHuy.clicked.connect(self.reject)

    def _on_them_sp(self):
        pid   = self.cbSP.currentData()
        pname = self.cbSP.currentText().split("] ", 1)[-1]

        disc_text = self.txtGiaTriGiam.text().strip().replace(",", "")
        if not disc_text:
            QtWidgets.QMessageBox.warning(
                self, "Thiếu thông tin",
                "Vui lòng nhập Giá trị giảm trước khi thêm sản phẩm!"
            )
            return
        try:
            discount = float(disc_text)
            if discount < 0:
                raise ValueError
        except ValueError:
            QtWidgets.QMessageBox.warning(self, "Lỗi", "Giá trị giảm phải là số không âm!")
            return

        for rd in self._product_rows:
            if rd["pid"] == pid:
                QtWidgets.QMessageBox.warning(self, "Trùng", "Sản phẩm này đã có trong danh sách!")
                return

        original = self._price_map.get(pid, 0.0)
        after    = max(0.0, original - discount)
        row_data = {"pid": pid, "pname": pname,
                    "original": original, "discount": discount, "after": after}
        self._product_rows.append(row_data)
        self._insert_table_row(row_data)

    def _insert_table_row(self, row_data):
        tbl = self.tblDanhSachSP
        i   = tbl.rowCount()
        tbl.insertRow(i)
        tbl.setItem(i, 0, QtWidgets.QTableWidgetItem(str(row_data["pid"])))
        tbl.setItem(i, 1, QtWidgets.QTableWidgetItem(row_data["pname"]))
        tbl.setItem(i, 2, QtWidgets.QTableWidgetItem(f"{row_data['original']:,.0f} VNĐ"))
        tbl.setItem(i, 3, QtWidgets.QTableWidgetItem(f"{row_data['discount']:,.0f} VNĐ"))
        tbl.setItem(i, 4, QtWidgets.QTableWidgetItem(f"{row_data['after']:,.0f} VNĐ"))

        btn_xoa = QtWidgets.QPushButton("Xóa")
        btn_xoa.setStyleSheet(
            "background-color:#ef4444;color:white;font-weight:bold;"
            "border:none;border-radius:4px;padding:4px;"
        )
        btn_xoa.clicked.connect(lambda _, r=row_data: self._remove_row(r))
        tbl.setCellWidget(i, 5, btn_xoa)

    def _remove_row(self, row_data):
        if row_data in self._product_rows:
            self._product_rows.remove(row_data)
        self._refresh_table()

    def _refresh_table(self):
        self.tblDanhSachSP.setRowCount(0)
        for rd in self._product_rows:
            self._insert_table_row(rd)

    def _on_luu(self):
        ten = self.txtTenCTKM.text().strip()
        if not ten:
            QtWidgets.QMessageBox.warning(self, "Thiếu thông tin", "Vui lòng nhập Tên chương trình!")
            return
        if not self._product_rows:
            QtWidgets.QMessageBox.warning(
                self, "Thiếu thông tin", "Vui lòng thêm ít nhất 1 sản phẩm áp dụng!"
            )
            return

        start = self.dteNgayBatDau.date().toPyDate()
        end   = self.dteNgayKetThuc.date().toPyDate()
        if end <= start:
            QtWidgets.QMessageBox.warning(self, "Lỗi ngày", "Ngày kết thúc phải sau ngày bắt đầu!")
            return

        from datetime import date
        today = date.today()
        if today < start:
            status = "Sắp diễn ra"
        elif today > end:
            status = "Đã kết thúc"
        else:
            status = "Đang diễn ra"

        db   = DatabaseManager()
        conn = db.get_connection()
        if not conn:
            return
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT ISNULL(MAX(PromotionID), 0) FROM Promotions")
            new_id = cursor.fetchone()[0] + 1

            cursor.execute("""
                INSERT INTO Promotions
                    (PromotionID, PromotionName, PromotionForm, StartDate, EndDate, Status)
                VALUES (?, ?, N'Giảm giá trực tiếp', ?, ?, ?)
            """, (new_id, ten, start, end, status))

            for rd in self._product_rows:
                cursor.execute("""
                    INSERT INTO Promotion_Details
                        (PromotionID, ProductID, ApplicableDate, DiscountValue, DiscountedPrice)
                    VALUES (?, ?, ?, ?, ?)
                """, (new_id, rd["pid"], start, rd["discount"], rd["after"]))

            conn.commit()
            QtWidgets.QMessageBox.information(
                self, "Thành công", f"Đã tạo chương trình khuyến mãi #{new_id}!"
            )
            self.accept()
        except Exception as e:
            conn.rollback()
            QtWidgets.QMessageBox.critical(self, "Lỗi CSDL", f"Lỗi khi lưu:\n{e}")
        finally:
            conn.close()


# ============================================================
# DIALOG SỬA KHUYẾN MÃI
# ============================================================
class EditPromotion(QtWidgets.QDialog):
    """
    Chỉnh sửa chương trình khuyến mãi đã có.
    - Load dữ liệu cũ vào txtTenCTKM, dteNgayBatDau, dteNgayKetThuc.
    - Load danh sách SP đã áp dụng vào tblDanhSachSP.
    - Người dùng thêm/xóa SP, sửa ngày/tên → btnLuu → cập nhật DB.
    """

    def __init__(self, promo_data, parent=None):
        super().__init__(parent)
        uic.loadUi(os.path.join(UI_PATH, "editKhuyenMai.ui"), self)

        self.promo_data    = promo_data
        self._product_rows = []
        self._price_map    = {}

        self._setup_table()
        self._setup_dates()
        self._load_products_combo()
        self._load_old_data()
        self._connect_signals()

    def _setup_table(self):
        tbl = self.tblDanhSachSP
        tbl.verticalHeader().setVisible(False)
        tbl.setEditTriggers(QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)
        tbl.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        tbl.setHorizontalHeaderLabels(
            ["Mã SP", "Sản phẩm áp dụng", "Giá gốc", "Giá trị giảm", "Giá sau giảm", "Xóa"]
        )
        hdr = tbl.horizontalHeader()
        hdr.setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode.Stretch)
        hdr.setSectionResizeMode(5, QtWidgets.QHeaderView.ResizeMode.Fixed)
        tbl.setColumnWidth(5, 70)

    def _setup_dates(self):
        self.dteNgayBatDau.setCalendarPopup(True)
        self.dteNgayKetThuc.setCalendarPopup(True)

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
            self.cbSP.clear()
            for pid, pname, price in cursor.fetchall():
                self.cbSP.addItem(f"[{pid}] {pname}", pid)
                self._price_map[pid] = float(price)
        finally:
            conn.close()

    def _load_old_data(self):
        d = self.promo_data
        self.txtTenCTKM.setText(d["name"])

        import datetime
        def parse(s):
            try:
                return datetime.datetime.strptime(s, "%d/%m/%Y").date()
            except Exception:
                return datetime.date.today()

        sd = parse(d["start_date"])
        ed = parse(d["end_date"])
        self.dteNgayBatDau.setDate(QDate(sd.year, sd.month, sd.day))
        self.dteNgayKetThuc.setDate(QDate(ed.year, ed.month, ed.day))

        # Load SP đã áp dụng
        db   = DatabaseManager()
        conn = db.get_connection()
        if not conn:
            return
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT pd.ProductID, p.ProductName, p.UnitPrice,
                       pd.DiscountValue, pd.DiscountedPrice
                FROM   Promotion_Details pd
                JOIN   Products p ON pd.ProductID = p.ProductID
                WHERE  pd.PromotionID = ?
            """, (d["id"],))
            for row in cursor.fetchall():
                rd = {
                    "pid":      row[0],
                    "pname":    row[1],
                    "original": float(row[2]),
                    "discount": float(row[3]) if row[3] is not None else 0.0,
                    "after":    float(row[4]) if row[4] is not None else float(row[2]),
                }
                self._product_rows.append(rd)
                self._insert_table_row(rd)
        finally:
            conn.close()

    def _connect_signals(self):
        self.btnThemSPCTKM.clicked.connect(self._on_them_sp)
        self.btnLuu.clicked.connect(self._on_luu)
        self.btnHuy.clicked.connect(self.reject)

    def _on_them_sp(self):
        pid   = self.cbSP.currentData()
        pname = self.cbSP.currentText().split("] ", 1)[-1]

        disc_text = self.txtGiaTriGiam.text().strip().replace(",", "")
        if not disc_text:
            QtWidgets.QMessageBox.warning(
                self, "Thiếu thông tin",
                "Vui lòng nhập Giá trị giảm trước khi thêm sản phẩm!"
            )
            return
        try:
            discount = float(disc_text)
            if discount < 0:
                raise ValueError
        except ValueError:
            QtWidgets.QMessageBox.warning(self, "Lỗi", "Giá trị giảm phải là số không âm!")
            return

        for rd in self._product_rows:
            if rd["pid"] == pid:
                QtWidgets.QMessageBox.warning(self, "Trùng", "Sản phẩm này đã có trong danh sách!")
                return

        original = self._price_map.get(pid, 0.0)
        after    = max(0.0, original - discount)
        row_data = {"pid": pid, "pname": pname,
                    "original": original, "discount": discount, "after": after}
        self._product_rows.append(row_data)
        self._insert_table_row(row_data)

    def _insert_table_row(self, row_data):
        tbl = self.tblDanhSachSP
        i   = tbl.rowCount()
        tbl.insertRow(i)
        tbl.setItem(i, 0, QtWidgets.QTableWidgetItem(str(row_data["pid"])))
        tbl.setItem(i, 1, QtWidgets.QTableWidgetItem(row_data["pname"]))
        tbl.setItem(i, 2, QtWidgets.QTableWidgetItem(f"{row_data['original']:,.0f} VNĐ"))
        tbl.setItem(i, 3, QtWidgets.QTableWidgetItem(f"{row_data['discount']:,.0f} VNĐ"))
        tbl.setItem(i, 4, QtWidgets.QTableWidgetItem(f"{row_data['after']:,.0f} VNĐ"))

        btn_xoa = QtWidgets.QPushButton("Xóa")
        btn_xoa.setStyleSheet(
            "background-color:#ef4444;color:white;font-weight:bold;"
            "border:none;border-radius:4px;padding:4px;"
        )
        btn_xoa.clicked.connect(lambda _, r=row_data: self._remove_row(r))
        tbl.setCellWidget(i, 5, btn_xoa)

    def _remove_row(self, row_data):
        if row_data in self._product_rows:
            self._product_rows.remove(row_data)
        self._refresh_table()

    def _refresh_table(self):
        self.tblDanhSachSP.setRowCount(0)
        for rd in self._product_rows:
            self._insert_table_row(rd)

    def _on_luu(self):
        ten = self.txtTenCTKM.text().strip()
        if not ten:
            QtWidgets.QMessageBox.warning(self, "Thiếu thông tin", "Vui lòng nhập Tên chương trình!")
            return
        if not self._product_rows:
            QtWidgets.QMessageBox.warning(
                self, "Thiếu thông tin", "Vui lòng thêm ít nhất 1 sản phẩm áp dụng!"
            )
            return

        start = self.dteNgayBatDau.date().toPyDate()
        end   = self.dteNgayKetThuc.date().toPyDate()
        if end <= start:
            QtWidgets.QMessageBox.warning(self, "Lỗi ngày", "Ngày kết thúc phải sau ngày bắt đầu!")
            return

        from datetime import date
        today = date.today()
        if today < start:
            status = "Sắp diễn ra"
        elif today > end:
            status = "Đã kết thúc"
        else:
            status = "Đang diễn ra"

        db   = DatabaseManager()
        conn = db.get_connection()
        if not conn:
            return
        try:
            cursor   = conn.cursor()
            promo_id = self.promo_data["id"]

            cursor.execute("""
                UPDATE Promotions
                SET PromotionName = ?, StartDate = ?, EndDate = ?, Status = ?
                WHERE PromotionID = ?
            """, (ten, start, end, status, promo_id))

            # Xóa SP cũ → thêm lại mới
            cursor.execute("DELETE FROM Promotion_Details WHERE PromotionID = ?", (promo_id,))
            for rd in self._product_rows:
                cursor.execute("""
                    INSERT INTO Promotion_Details
                        (PromotionID, ProductID, ApplicableDate, DiscountValue, DiscountedPrice)
                    VALUES (?, ?, ?, ?, ?)
                """, (promo_id, rd["pid"], start, rd["discount"], rd["after"]))

            conn.commit()
            QtWidgets.QMessageBox.information(
                self, "Thành công", "Đã cập nhật chương trình khuyến mãi!"
            )
            self.accept()
        except Exception as e:
            conn.rollback()
            QtWidgets.QMessageBox.critical(self, "Lỗi CSDL", f"Lỗi khi lưu:\n{e}")
        finally:
            conn.close()


# ============================================================
# DIALOG XÓA KHUYẾN MÃI
# ============================================================
class DeletePromotion(QtWidgets.QDialog):
    """
    Xác nhận xóa chương trình khuyến mãi.
    lblCanhBao giữ nguyên nội dung từ UI.
    btnXoa → xóa DB.
    btnHuy → đóng.
    """

    def __init__(self, promo_data, parent=None):
        super().__init__(parent)
        uic.loadUi(os.path.join(UI_PATH, "deleteKhuyenMai.ui"), self)

        self.promo_data = promo_data

        self.btnXoa.clicked.connect(self._on_xoa)
        self.btnHuy.clicked.connect(self.reject)

    def _on_xoa(self):
        if self.promo_data.get("status") == "Đang diễn ra":
            QtWidgets.QMessageBox.warning(
                self, "Từ chối",
                "Không thể xóa chương trình đang diễn ra!\n"
                "Vui lòng kết thúc hoặc hủy chương trình trước."
            )
            return

        db   = DatabaseManager()
        conn = db.get_connection()
        if not conn:
            return
        try:
            cursor   = conn.cursor()
            promo_id = self.promo_data["id"]
            cursor.execute("DELETE FROM Promotion_Details WHERE PromotionID = ?", (promo_id,))
            cursor.execute("DELETE FROM Promotions WHERE PromotionID = ?", (promo_id,))
            conn.commit()
            QtWidgets.QMessageBox.information(self, "Thành công", "Đã xóa chương trình khuyến mãi!")
            self.accept()
        except Exception as e:
            conn.rollback()
            QtWidgets.QMessageBox.critical(self, "Lỗi CSDL", f"Lỗi khi xóa:\n{e}")
        finally:
            conn.close()


# ============================================================
# BỘ QUẢN LÝ KHUYẾN MÃI – CONTROLLER
# ============================================================
class PromotionManager:
    """
    Controller cho trang Khuyến Mãi.

    Khai báo trong main.py → setup_module_promotion():
        if not hasattr(self, 'tblDanhSachKM'): return
        txt_search = self.get_widget(['txtTimKhuyenMai'], QtWidgets.QLineEdit)
        cb_status  = self.get_widget(['cbTrangThaiKM'],   QtWidgets.QComboBox)
        self.promotion_manager = PromotionManager(self.tblDanhSachKM, txt_search, cb_status)
        if hasattr(self, 'btnKhuyenMai'):
            self.btnKhuyenMai.clicked.connect(
                lambda: self.change_page(self.pageKhuyenMai, self.promotion_manager.load_data)
            )
        if hasattr(self, 'btnThemKhuyenMai'):
            self.btnThemKhuyenMai.clicked.connect(self.promotion_manager.open_add)

    Bảng tblDanhSachKM cần có 6 cột trong UI:
        Mã KM | Tên CT | Ngày bắt đầu | Ngày kết thúc | Trạng thái | Thao tác
    """

    def __init__(self, table_widget, txt_search=None, cb_status=None):
        self.table      = table_widget
        self.txt_search = txt_search
        self.cb_status  = cb_status
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
            self.txt_search.returnPressed.connect(self.load_data)
        if self.cb_status:
            self.cb_status.blockSignals(True)
            self.cb_status.clear()
            self.cb_status.addItem("Tất cả trạng thái", "")
            for s in ["Sắp diễn ra", "Đang diễn ra", "Đã kết thúc", "Đã hủy"]:
                self.cb_status.addItem(s, s)
            self.cb_status.blockSignals(False)
            self.cb_status.currentIndexChanged.connect(self.load_data)

    def load_data(self):
        db   = DatabaseManager()
        conn = db.get_connection()
        if not conn:
            return

        query  = """
            SELECT PromotionID, PromotionName, StartDate, EndDate, Status
            FROM   Promotions WHERE 1=1
        """
        params = []

        kw = self.txt_search.text().strip() if self.txt_search else ""
        if kw:
            query += " AND PromotionName LIKE ?"
            params.append(f"%{kw}%")

        status_val = self.cb_status.currentData() if self.cb_status else ""
        if status_val:
            query += " AND Status = ?"
            params.append(status_val)

        query += " ORDER BY StartDate DESC"

        _COLOR = {
            "Đang diễn ra": Qt.GlobalColor.darkGreen,
            "Sắp diễn ra":  Qt.GlobalColor.darkBlue,
            "Đã kết thúc":  Qt.GlobalColor.darkGray,
            "Đã hủy":       Qt.GlobalColor.darkRed,
        }

        try:
            cursor = conn.cursor()
            cursor.execute(query, params)
            rows = cursor.fetchall()

            self.table.setRowCount(0)
            for i, row in enumerate(rows):
                self.table.insertRow(i)
                self.table.setItem(i, 0, QtWidgets.QTableWidgetItem(str(row[0])))
                self.table.setItem(i, 1, QtWidgets.QTableWidgetItem(row[1]))
                self.table.setItem(i, 2, QtWidgets.QTableWidgetItem(
                    row[2].strftime("%d/%m/%Y") if row[2] else "—"))
                self.table.setItem(i, 3, QtWidgets.QTableWidgetItem(
                    row[3].strftime("%d/%m/%Y") if row[3] else "—"))

                status_item = QtWidgets.QTableWidgetItem(row[4])
                status_item.setForeground(_COLOR.get(row[4], Qt.GlobalColor.black))
                self.table.setItem(i, 4, status_item)

                promo_data = {
                    "id":         row[0],
                    "name":       row[1],
                    "start_date": row[2].strftime("%d/%m/%Y") if row[2] else "",
                    "end_date":   row[3].strftime("%d/%m/%Y") if row[3] else "",
                    "status":     row[4],
                }
                self._add_action_buttons(i, promo_data)
        except Exception as e:
            print(f"Lỗi load Khuyến mãi: {e}")
        finally:
            conn.close()

    def _add_action_buttons(self, row_idx, promo_data):
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

        btn_view.clicked.connect(lambda _, d=promo_data: self.open_view(d))
        btn_edit.clicked.connect(lambda _, d=promo_data: self.open_edit(d))
        btn_del.clicked.connect(lambda _, d=promo_data:  self.open_delete(d))

        h.addWidget(btn_view)
        h.addWidget(btn_edit)
        h.addWidget(btn_del)
        self.table.setCellWidget(row_idx, last, container)

    def open_view(self, promo_data):
        ViewPromotion(promo_data, edit_callback=self.open_edit).exec()

    def open_add(self):
        if AddPromotion().exec():
            self.load_data()

    def open_edit(self, promo_data):
        if EditPromotion(promo_data).exec():
            self.load_data()

    def open_delete(self, promo_data):
        if DeletePromotion(promo_data).exec():
            self.load_data()
