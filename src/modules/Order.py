import os
import re
from PyQt6 import uic, QtWidgets
from PyQt6.QtCore import Qt, QDateTime, QDate, QTime
from src.database.db_connection import DatabaseManager

# Lấy đường dẫn gốc
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(os.path.dirname(CURRENT_DIR))
UI_PATH = os.path.join(ROOT_DIR, "ui", "modules_ui", "DonHang")


# ============================================================
# HELPER: Khởi tạo bảng sản phẩm
# ============================================================
def _setup_product_table(table_widget, has_delete_col=False):
    """Cấu hình QTableWidget dùng cho danh sách sản phẩm trong đơn hàng."""
    cols = ["Tên sản phẩm", "Số lượng", "Đơn giá", "Thành tiền"]
    if has_delete_col:
        cols.append("")
    table_widget.setColumnCount(len(cols))
    table_widget.setHorizontalHeaderLabels(cols)
    table_widget.verticalHeader().setVisible(False)
    table_widget.setEditTriggers(QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)
    header = table_widget.horizontalHeader()
    for i in range(len(cols) - (1 if has_delete_col else 0)):
        header.setSectionResizeMode(i, QtWidgets.QHeaderView.ResizeMode.Stretch)
    if has_delete_col:
        header.setSectionResizeMode(len(cols) - 1, QtWidgets.QHeaderView.ResizeMode.Fixed)
        table_widget.setColumnWidth(len(cols) - 1, 60)


# ==========================================
# DIALOG CHI TIẾT ĐƠN HÀNG
# ==========================================
class ViewOrder(QtWidgets.QDialog):
    def __init__(self, data, switch_to_customer_callback=None):
        super().__init__()
        uic.loadUi(os.path.join(UI_PATH, "viewDonHang.ui"), self)

        self.order_id = data['id']
        self.customer_data = data['customer_info']
        self.switch_to_customer_callback = switch_to_customer_callback
        self._data = data  # Lưu lại để nút Sửa dùng

        self.load_general_info(data)
        self.load_product_list()
        self.load_payment_info()

        if hasattr(self, 'btnDong'):
            self.btnDong.clicked.connect(self.close)

        # Kết nối nút Sửa trong màn hình Xem → mở EditOrder
        if hasattr(self, 'btnSua'):
            self.btnSua.clicked.connect(self.open_edit)

    def load_general_info(self, data):
        if hasattr(self, 'lblHienThiMaDon_2'): self.lblHienThiMaDon_2.setText(str(data['id']))
        if hasattr(self, 'lblHienThiNgayMua'): self.lblHienThiNgayMua.setText(data['ngay'])
        if hasattr(self, 'lblHienThiTongTien'): self.lblHienThiTongTien.setText(data['tien'])

        if hasattr(self, 'lblHienThiTrangThai'):
            self.lblHienThiTrangThai.setText(data['trang_thai'])
            if "Đã thanh toán" in data['trang_thai']:
                self.lblHienThiTrangThai.setStyleSheet("color: #10b981; font-weight: bold;")
            else:
                self.lblHienThiTrangThai.setStyleSheet("color: #ef4444; font-weight: bold;")

        if hasattr(self, 'lblHienThiKhachHang'):
            ten_kh = self.customer_data['ten']
            link_html = f'<a href="#cus" style="color: #2563eb; text-decoration: none; font-weight: bold;">{ten_kh}</a>'
            self.lblHienThiKhachHang.setText(link_html)
            self.lblHienThiKhachHang.setOpenExternalLinks(False)
            self.lblHienThiKhachHang.linkActivated.connect(self.on_customer_name_clicked)

    def on_customer_name_clicked(self, link):
        self.close()
        if self.switch_to_customer_callback:
            self.switch_to_customer_callback(self.customer_data)

    def open_edit(self):
        """Mở EditOrder từ màn hình Xem, tự động làm mới sau khi lưu."""
        dialog = EditOrder(self._data)
        if dialog.exec():
            # Làm mới thông tin hiển thị sau khi chỉnh sửa thành công
            self.close()

    def load_product_list(self):
        if not hasattr(self, 'tblDanhSachSP'): return
        self.tblDanhSachSP.verticalHeader().setVisible(False)
        self.tblDanhSachSP.setEditTriggers(QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tblDanhSachSP.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode.Stretch)

        db = DatabaseManager()
        conn = db.get_connection()
        if not conn: return
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT p.ProductName, od.OrderedQuantity, p.UnitPrice, od.SubTotal
                FROM Order_Details od
                JOIN Products p ON od.ProductID = p.ProductID
                WHERE od.OrderID = ?
            """, (self.order_id,))
            rows = cursor.fetchall()
            self.tblDanhSachSP.setRowCount(0)
            for i, row in enumerate(rows):
                self.tblDanhSachSP.insertRow(i)
                self.tblDanhSachSP.setItem(i, 0, QtWidgets.QTableWidgetItem(row[0]))
                self.tblDanhSachSP.setItem(i, 1, QtWidgets.QTableWidgetItem(str(row[1])))
                self.tblDanhSachSP.setItem(i, 2, QtWidgets.QTableWidgetItem(f"{row[2]:,.0f} VNĐ"))
                self.tblDanhSachSP.setItem(i, 3, QtWidgets.QTableWidgetItem(f"{row[3]:,.0f} VNĐ"))
        except Exception as e:
            print(f"Lỗi tải chi tiết SP: {e}")
        finally:
            conn.close()

    def load_payment_info(self):
        db = DatabaseManager()
        conn = db.get_connection()
        if not conn: return
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT BillID, PaymentDate, PaymentAmount, PaymentMethod
                FROM Bills WHERE OrderID = ?
            """, (self.order_id,))
            bill = cursor.fetchone()
            if bill:
                if hasattr(self, 'lblHienThiMaHoaDon'): self.lblHienThiMaHoaDon.setText(str(bill[0]))
                if hasattr(self, 'lblHienThiNgayThanhToan'):
                    date_str = bill[1].strftime('%d/%m/%Y') if bill[1] else ""
                    self.lblHienThiNgayThanhToan.setText(date_str)
                if hasattr(self, 'lblHienThiTongTienThanhToan'):
                    self.lblHienThiTongTienThanhToan.setText(f"{bill[2]:,.0f} VNĐ")
                if hasattr(self, 'lblHienThiPhuongThucThanhToan'):
                    self.lblHienThiPhuongThucThanhToan.setText(bill[3])
            else:
                if hasattr(self, 'lblHienThiMaHoaDon'): self.lblHienThiMaHoaDon.setText("Chưa có")
                if hasattr(self, 'lblHienThiNgayThanhToan'): self.lblHienThiNgayThanhToan.setText("Chưa có")
                if hasattr(self, 'lblHienThiTongTienThanhToan'): self.lblHienThiTongTienThanhToan.setText("0 VNĐ")
                if hasattr(self, 'lblHienThiPhuongThucThanhToan'): self.lblHienThiPhuongThucThanhToan.setText("Chưa có")
        except Exception as e:
            print(f"Lỗi tải hóa đơn: {e}")
        finally:
            conn.close()


# ==========================================
# DIALOG SỬA ĐƠN HÀNG — ĐÃ HOÀN THIỆN
# ==========================================
class EditOrder(QtWidgets.QDialog):
    def __init__(self, data):
        super().__init__()
        ui_file = os.path.join(UI_PATH, "editDonHang.ui")
        if os.path.exists(ui_file):
            uic.loadUi(ui_file, self)

        self.order_id = data['id']
        self._rows = []

        self._setup_ui(data)
        self._connect_signals()

    @staticmethod
    def _to_qdatetime(dt_val):
        """Chuyển datetime Python (hoặc string) sang QDateTime an toàn."""
        import datetime as _dt
        try:
            if isinstance(dt_val, str):
                # Thử parse string dạng 'YYYY-MM-DD HH:MM:SS'
                dt_val = _dt.datetime.fromisoformat(dt_val[:19])
            if isinstance(dt_val, (_dt.datetime, _dt.date)):
                if isinstance(dt_val, _dt.date) and not isinstance(dt_val, _dt.datetime):
                    dt_val = _dt.datetime(dt_val.year, dt_val.month, dt_val.day)
                return QDateTime(
                    QDate(dt_val.year, dt_val.month, dt_val.day),
                    QTime(dt_val.hour, dt_val.minute, dt_val.second)
                )
        except Exception as e:
            print(f"[_to_qdatetime] lỗi: {e}, giá trị: {dt_val!r}")
        return QDateTime.currentDateTime()

    def _setup_ui(self, data):
        """Load toàn bộ dữ liệu đơn hàng hiện tại lên form."""
        # ── Mã đơn (read-only) ──
        if hasattr(self, 'txtReadOnlyMaDon'):
            self.txtReadOnlyMaDon.setText(str(self.order_id))
            self.txtReadOnlyMaDon.setReadOnly(True)

        # ── Thiết lập bảng sản phẩm ──
        if hasattr(self, 'tblDanhSachSP'):
            _setup_product_table(self.tblDanhSachSP, has_delete_col=True)

        db = DatabaseManager()
        conn = db.get_connection()
        if not conn:
            QtWidgets.QMessageBox.critical(self, "Lỗi", "Không thể kết nối CSDL!")
            return

        # ── Dùng 1 cursor, fetchall() ngay sau mỗi execute ──
        cursor = conn.cursor()
        try:
            # 1. Sản phẩm → combobox
            cursor.execute("SELECT ProductID, ProductName, UnitPrice FROM Products ORDER BY ProductName")
            products = cursor.fetchall()
            self._price_map = {}
            if hasattr(self, 'cbSanPham'):
                self.cbSanPham.blockSignals(True)
                self.cbSanPham.clear()
                for pid, pname, price in products:
                    self.cbSanPham.addItem(pname, pid)
                    self._price_map[pid] = float(price)
                self.cbSanPham.blockSignals(False)

            # 2. Khách hàng → combobox
            cursor.execute("SELECT CustomerID, CustomerName FROM Customers ORDER BY CustomerName")
            customers = cursor.fetchall()
            if hasattr(self, 'cbKhachHang'):
                self.cbKhachHang.blockSignals(True)
                self.cbKhachHang.clear()
                for cid, cname in customers:
                    self.cbKhachHang.addItem(cname, cid)
                self.cbKhachHang.blockSignals(False)

            # 3. Thông tin đơn hàng
            cursor.execute(
                "SELECT CustomerID, OrderDate, TotalAmount, Status FROM Orders WHERE OrderID = ?",
                (self.order_id,)
            )
            order = cursor.fetchone()
            order_status = ""
            order_total  = 0
            if order:
                cus_id, order_date, total, order_status = order
                order_total = total or 0
                # Chọn đúng khách hàng
                if hasattr(self, 'cbKhachHang'):
                    idx = self.cbKhachHang.findData(cus_id)
                    if idx >= 0:
                        self.cbKhachHang.setCurrentIndex(idx)
                # Ngày mua
                if hasattr(self, 'dteNgayMua'):
                    self.dteNgayMua.setCalendarPopup(True)
                    self.dteNgayMua.setDateTime(self._to_qdatetime(order_date))
                # Tổng tiền
                if hasattr(self, 'txtTongTien'):
                    self.txtTongTien.setText(f"{order_total:,.0f}")
                    self.txtTongTien.setReadOnly(True)
            else:
                print(f"[EditOrder] Không tìm thấy OrderID={self.order_id}")

            # 4. Trạng thái
            cursor.execute(
                "SELECT DISTINCT Status FROM Orders WHERE Status IS NOT NULL ORDER BY Status"
            )
            status_rows = cursor.fetchall()
            status_values = [r[0] for r in status_rows] if status_rows else ["Chưa thanh toán", "Đã thanh toán", "Đã hủy"]
            if hasattr(self, 'cbTrangThai'):
                self.cbTrangThai.blockSignals(True)
                self.cbTrangThai.clear()
                self.cbTrangThai.addItems(status_values)
                # Chọn đúng trạng thái hiện tại
                idx = self.cbTrangThai.findText(order_status)
                self.cbTrangThai.setCurrentIndex(idx if idx >= 0 else 0)
                self.cbTrangThai.blockSignals(False)

            # 5. Sản phẩm trong đơn → bảng
            cursor.execute("""
                SELECT od.ProductID, p.ProductName, od.OrderedQuantity, p.UnitPrice
                FROM Order_Details od
                JOIN Products p ON od.ProductID = p.ProductID
                WHERE od.OrderID = ?
            """, (self.order_id,))
            order_details = cursor.fetchall()
            print(f"[EditOrder] OrderID={self.order_id}, tìm thấy {len(order_details)} sản phẩm")
            for pid, pname, qty, unit_price in order_details:
                rd = {"pid": pid, "pname": pname, "qty": qty, "price": float(unit_price)}
                self._rows.append(rd)
                self._insert_row(rd)
            # Cập nhật tổng theo sản phẩm thực tế trong bảng
            self._update_total()

            # 6. Hóa đơn
            cursor.execute(
                "SELECT BillID, PaymentDate, PaymentAmount, PaymentMethod FROM Bills WHERE OrderID = ?",
                (self.order_id,)
            )
            bill = cursor.fetchone()

            if hasattr(self, 'txtReadOnlyMaHoaDon'):
                self.txtReadOnlyMaHoaDon.setReadOnly(True)
                self.txtReadOnlyMaHoaDon.setText(str(bill[0]) if bill else "Chưa có")

            if hasattr(self, 'cbPhuongThucThanhToan'):
                self.cbPhuongThucThanhToan.clear()
                self.cbPhuongThucThanhToan.addItems(["Tiền mặt", "Chuyển khoản", "Thẻ tín dụng"])
                if bill and bill[3]:
                    idx = self.cbPhuongThucThanhToan.findText(bill[3])
                    if idx >= 0:
                        self.cbPhuongThucThanhToan.setCurrentIndex(idx)

            if hasattr(self, 'dteNgayThanhToan'):
                self.dteNgayThanhToan.setCalendarPopup(True)
                self.dteNgayThanhToan.setDateTime(
                    self._to_qdatetime(bill[1]) if (bill and bill[1]) else QDateTime.currentDateTime()
                )

            if hasattr(self, 'txtTongTienThanhToan'):
                val = bill[2] if (bill and bill[2]) else order_total
                self.txtTongTienThanhToan.setText(f"{val:,.0f}")

        except Exception as e:
            import traceback
            print(f"[EditOrder] Lỗi load UI:\n{traceback.format_exc()}")
            QtWidgets.QMessageBox.critical(self, "Lỗi load dữ liệu", str(e))
        finally:
            conn.close()


    def _connect_signals(self):
        if hasattr(self, 'cbSanPham'):
            self.cbSanPham.currentIndexChanged.connect(self._on_sp_changed)
            self._on_sp_changed()
        if hasattr(self, 'btnThem'):
            self.btnThem.clicked.connect(self._on_them_sp)
        if hasattr(self, 'btnLuu'):
            self.btnLuu.clicked.connect(self.save_data)
        if hasattr(self, 'btnHuy'):
            self.btnHuy.clicked.connect(self.reject)

    def _on_sp_changed(self):
        if not hasattr(self, 'cbSanPham') or not hasattr(self, 'txtDonGia'):
            return
        pid = self.cbSanPham.currentData()
        if pid and hasattr(self, '_price_map') and pid in self._price_map:
            self.txtDonGia.setText(f"{self._price_map[pid]:,.0f}")

    def _on_them_sp(self):
        if not hasattr(self, 'cbSanPham'): return
        pid        = self.cbSanPham.currentData()
        pname      = self.cbSanPham.currentText()
        qty        = self.spnSoLuong.value() if hasattr(self, 'spnSoLuong') else 1
        price_text = self.txtDonGia.text().strip().replace(",", "") if hasattr(self, 'txtDonGia') else "0"
        try:
            price = float(price_text)
            if price <= 0: raise ValueError
        except ValueError:
            QtWidgets.QMessageBox.warning(self, "Lỗi", "Đơn giá phải là số dương!"); return
        if qty <= 0:
            QtWidgets.QMessageBox.warning(self, "Lỗi", "Số lượng phải lớn hơn 0!"); return
        for r in self._rows:
            if r["pid"] == pid:
                QtWidgets.QMessageBox.warning(self, "Trùng", "Sản phẩm đã có trong đơn!"); return
        rd = {"pid": pid, "pname": pname, "qty": qty, "price": price}
        self._rows.append(rd)
        if hasattr(self, 'tblDanhSachSP'):
            self._insert_row(rd)
        self._update_total()

    def _insert_row(self, rd):
        tbl = self.tblDanhSachSP
        i   = tbl.rowCount()
        tbl.insertRow(i)
        tbl.setItem(i, 0, QtWidgets.QTableWidgetItem(rd["pname"]))
        tbl.setItem(i, 1, QtWidgets.QTableWidgetItem(str(rd["qty"])))
        tbl.setItem(i, 2, QtWidgets.QTableWidgetItem(f"{rd['price']:,.0f} VNĐ"))
        tbl.setItem(i, 3, QtWidgets.QTableWidgetItem(f"{rd['qty']*rd['price']:,.0f} VNĐ"))
        btn = QtWidgets.QPushButton("Xóa")
        btn.setStyleSheet(
            "background-color:#ef4444;color:white;font-weight:bold;"
            "border:none;border-radius:4px;padding:3px;"
        )
        btn.clicked.connect(lambda _, r=rd: self._remove_row(r))
        tbl.setCellWidget(i, 4, btn)

    def _remove_row(self, rd):
        if rd in self._rows: self._rows.remove(rd)
        self._refresh_table()
        self._update_total()

    def _refresh_table(self):
        self.tblDanhSachSP.setRowCount(0)
        for rd in self._rows: self._insert_row(rd)

    def _update_total(self):
        total = sum(r["qty"] * r["price"] for r in self._rows)
        if hasattr(self, 'txtTongTien'):
            self.txtTongTien.setText(f"{total:,.0f}")
        if hasattr(self, 'txtTongTienThanhToan'):
            self.txtTongTienThanhToan.setText(f"{total:,.0f}")

    def save_data(self):
        if not self._rows:
            QtWidgets.QMessageBox.warning(self, "Thiếu", "Vui lòng có ít nhất 1 sản phẩm!"); return

        cus_id = self.cbKhachHang.currentData() if hasattr(self, 'cbKhachHang') else None
        status = self.cbTrangThai.currentText() if hasattr(self, 'cbTrangThai') else ""
        ngay   = self.dteNgayMua.dateTime().toPyDateTime() if hasattr(self, 'dteNgayMua') else None
        total  = sum(r["qty"] * r["price"] for r in self._rows)

        db = DatabaseManager()
        conn = db.get_connection()
        if not conn: return
        try:
            cursor = conn.cursor()

            # 1. Cập nhật đơn hàng chính
            cursor.execute("""
                UPDATE Orders
                SET CustomerID=?, OrderDate=?, TotalAmount=?, Status=?
                WHERE OrderID=?
            """, (cus_id, ngay, total, status, self.order_id))

            # 2. Xóa chi tiết cũ rồi insert lại
            cursor.execute("DELETE FROM Order_Details WHERE OrderID=?", (self.order_id,))
            for rd in self._rows:
                subtotal = rd["qty"] * rd["price"]
                cursor.execute("""
                    INSERT INTO Order_Details (OrderID, ProductID, OrderedQuantity, SubTotal)
                    VALUES (?,?,?,?)
                """, (self.order_id, rd["pid"], rd["qty"], subtotal))

            # 3. Xử lý hóa đơn theo trạng thái
            cursor.execute("SELECT BillID FROM Bills WHERE OrderID=?", (self.order_id,))
            existing_bill = cursor.fetchone()

            if status == "Đã thanh toán":
                ngay_tt = self.dteNgayThanhToan.dateTime().toPyDateTime() if hasattr(self, 'dteNgayThanhToan') else ngay
                pmeth   = self.cbPhuongThucThanhToan.currentText() if hasattr(self, 'cbPhuongThucThanhToan') else "Tiền mặt"
                tt_text = self.txtTongTienThanhToan.text().replace(",", "") if hasattr(self, 'txtTongTienThanhToan') else ""
                tt_amt  = float(tt_text) if tt_text else total

                if existing_bill:
                    cursor.execute("""
                        UPDATE Bills
                        SET PaymentDate=?, PaymentAmount=?, PaymentMethod=?
                        WHERE OrderID=?
                    """, (ngay_tt, tt_amt, pmeth, self.order_id))
                else:
                    cursor.execute("SELECT ISNULL(MAX(BillID),0) FROM Bills")
                    new_bill_id = cursor.fetchone()[0] + 1
                    cursor.execute("""
                        INSERT INTO Bills (BillID, OrderID, PaymentDate, PaymentAmount, PaymentMethod)
                        VALUES (?,?,?,?,?)
                    """, (new_bill_id, self.order_id, ngay_tt, tt_amt, pmeth))
            else:
                # Đổi trạng thái về chưa/hủy → xóa bill cũ nếu có
                if existing_bill:
                    cursor.execute("DELETE FROM Bills WHERE OrderID=?", (self.order_id,))

            conn.commit()
            QtWidgets.QMessageBox.information(self, "Thành công", f"Đã cập nhật đơn hàng #{self.order_id}!")
            self.accept()
        except Exception as e:
            conn.rollback()
            QtWidgets.QMessageBox.critical(self, "Lỗi CSDL", f"{e}")
        finally:
            conn.close()


# ==========================================
# DIALOG XÓA ĐƠN HÀNG
# ==========================================
class DeleteOrder(QtWidgets.QDialog):
    def __init__(self, data):
        super().__init__()
        uic.loadUi(os.path.join(UI_PATH, "deleteDonHang.ui"), self)
        self.order_id = data['id']
        self.order_info = data

        # Hiển thị thông tin xác nhận lên label
        if hasattr(self, 'lblCanhBao'):
            self.lblCanhBao.setText(
                f"Bạn có chắc muốn xóa đơn hàng #{self.order_id} "
                f"của khách hàng {data.get('customer_info', {}).get('ten', '')} không?\n"
                f"Hành động này không thể hoàn tác!"
            )
            self.lblCanhBao.setWordWrap(True)

        if hasattr(self, 'btnXoa'): self.btnXoa.clicked.connect(self.delete_data)
        if hasattr(self, 'btnHuy'): self.btnHuy.clicked.connect(self.reject)

    def delete_data(self):
        db = DatabaseManager()
        conn = db.get_connection()
        if not conn: return
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM Order_Details WHERE OrderID = ?", (self.order_id,))
            cursor.execute("DELETE FROM Bills WHERE OrderID = ?", (self.order_id,))
            cursor.execute("DELETE FROM Orders WHERE OrderID = ?", (self.order_id,))
            conn.commit()
            QtWidgets.QMessageBox.information(self, "Thành công", f"Đã xóa đơn hàng #{self.order_id}!")
            self.accept()
        except Exception as e:
            conn.rollback()
            QtWidgets.QMessageBox.critical(self, "Lỗi", f"Không thể xóa đơn hàng:\n{e}")
        finally:
            conn.close()


# ============================================================
# DIALOG TẠO ĐƠN HÀNG MỚI
# ============================================================
class AddOrder(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        uic.loadUi(os.path.join(UI_PATH, "addDonHang.ui"), self)

        self._rows = []

        _setup_product_table(self.tblDanhSachSP, has_delete_col=True)
        self._fill_new_id()
        self._load_combos()
        self._setup_datetime()
        self._connect_signals()

    def _fill_new_id(self):
        db   = DatabaseManager()
        conn = db.get_connection()
        if not conn: return
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT ISNULL(MAX(OrderID),0) FROM Orders")
            self.txtReadOnlyMaDon.setText(str(cursor.fetchone()[0] + 1))
            cursor.execute("SELECT ISNULL(MAX(BillID),0) FROM Bills")
            self.txtReadOnlyMaHoaDon.setText(str(cursor.fetchone()[0] + 1))
        finally:
            conn.close()

    def _load_combos(self):
        db   = DatabaseManager()
        conn = db.get_connection()
        if not conn: return
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT ProductID, ProductName, UnitPrice FROM Products "
                "WHERE UnitsInStock > 0 ORDER BY ProductName"
            )
            self.cbSanPham.clear()
            self._price_map = {}
            for pid, pname, price in cursor.fetchall():
                self.cbSanPham.addItem(pname, pid)
                self._price_map[pid] = float(price)

            cursor.execute("SELECT CustomerID, CustomerName FROM Customers ORDER BY CustomerName")
            self.cbKhachHang.clear()
            for cid, cname in cursor.fetchall():
                self.cbKhachHang.addItem(cname, cid)

            self.cbTrangThai.clear()
            status_values = self._get_status_values(cursor)
            self.cbTrangThai.addItems(status_values)

            self.cbPhuongThucThanhToan.clear()
            self.cbPhuongThucThanhToan.addItems(["Tiền mặt", "Chuyển khoản", "Thẻ tín dụng"])
        finally:
            conn.close()

        self.cbSanPham.currentIndexChanged.connect(self._on_sp_changed)
        self._on_sp_changed()

    def _get_status_values(self, cursor):
        try:
            cursor.execute("""
                SELECT cc.definition
                FROM   sys.check_constraints cc
                JOIN   sys.columns col ON cc.parent_object_id = col.object_id
                                      AND cc.parent_column_id = col.column_id
                JOIN   sys.tables t   ON cc.parent_object_id = t.object_id
                WHERE  t.name = 'Orders' AND col.name = 'Status'
            """)
            row = cursor.fetchone()
            if row:
                vals = re.findall(r"'([^']+)'", row[0])
                if vals:
                    return vals
        except Exception as e:
            print(f"[WARN] Không đọc được CHECK constraint: {e}")
        try:
            cursor.execute("SELECT DISTINCT Status FROM Orders WHERE Status IS NOT NULL ORDER BY Status")
            vals = [r[0] for r in cursor.fetchall()]
            if vals:
                return vals
        except Exception:
            pass
        return ["Chưa thanh toán", "Đã thanh toán", "Đã hủy"]

    def _on_sp_changed(self):
        pid = self.cbSanPham.currentData()
        if pid and pid in self._price_map:
            self.txtDonGia.setText(f"{self._price_map[pid]:,.0f}")

    def _setup_datetime(self):
        now = QDateTime.currentDateTime()
        self.dteNgayMua.setCalendarPopup(True)
        self.dteNgayMua.setDateTime(now)
        self.dteNgayThanhToan.setCalendarPopup(True)
        self.dteNgayThanhToan.setDateTime(now)

    def _connect_signals(self):
        self.btnThem.clicked.connect(self._on_them_sp)
        self.btnLuu.clicked.connect(self._on_luu)
        self.btnHuy.clicked.connect(self.reject)

    def _on_them_sp(self):
        pid        = self.cbSanPham.currentData()
        pname      = self.cbSanPham.currentText()
        qty        = self.spnSoLuong.value()
        price_text = self.txtDonGia.text().strip().replace(",", "")

        if not price_text:
            QtWidgets.QMessageBox.warning(self, "Thiếu", "Vui lòng nhập Đơn giá!"); return
        try:
            price = float(price_text)
            if price <= 0: raise ValueError
        except ValueError:
            QtWidgets.QMessageBox.warning(self, "Lỗi", "Đơn giá phải là số dương!"); return
        if qty <= 0:
            QtWidgets.QMessageBox.warning(self, "Lỗi", "Số lượng phải lớn hơn 0!"); return
        for r in self._rows:
            if r["pid"] == pid:
                QtWidgets.QMessageBox.warning(self, "Trùng", "Sản phẩm đã có trong đơn!"); return

        rd = {"pid": pid, "pname": pname, "qty": qty, "price": price}
        self._rows.append(rd)
        self._insert_row(rd)
        self._update_total()

    def _insert_row(self, rd):
        tbl = self.tblDanhSachSP
        i   = tbl.rowCount()
        tbl.insertRow(i)
        tbl.setItem(i, 0, QtWidgets.QTableWidgetItem(rd["pname"]))
        tbl.setItem(i, 1, QtWidgets.QTableWidgetItem(str(rd["qty"])))
        tbl.setItem(i, 2, QtWidgets.QTableWidgetItem(f"{rd['price']:,.0f} VNĐ"))
        tbl.setItem(i, 3, QtWidgets.QTableWidgetItem(f"{rd['qty']*rd['price']:,.0f} VNĐ"))
        btn = QtWidgets.QPushButton("Xóa")
        btn.setStyleSheet(
            "background-color:#ef4444;color:white;font-weight:bold;"
            "border:none;border-radius:4px;padding:3px;"
        )
        btn.clicked.connect(lambda _, r=rd: self._remove_row(r))
        tbl.setCellWidget(i, 4, btn)

    def _remove_row(self, rd):
        if rd in self._rows: self._rows.remove(rd)
        self._refresh_table()
        self._update_total()

    def _refresh_table(self):
        self.tblDanhSachSP.setRowCount(0)
        for rd in self._rows: self._insert_row(rd)

    def _update_total(self):
        total = sum(r["qty"] * r["price"] for r in self._rows)
        self.txtTongTien.setText(f"{total:,.0f}")
        self.txtTongTienThanhToan.setText(f"{total:,.0f}")

    def _on_luu(self):
        if not self._rows:
            QtWidgets.QMessageBox.warning(self, "Thiếu", "Vui lòng thêm ít nhất 1 sản phẩm!"); return

        cus_id = self.cbKhachHang.currentData()
        status = self.cbTrangThai.currentText()
        ngay   = self.dteNgayMua.dateTime().toPyDateTime()
        total  = sum(r["qty"] * r["price"] for r in self._rows)

        db   = DatabaseManager()
        conn = db.get_connection()
        if not conn: return
        try:
            cursor = conn.cursor()

            cursor.execute("SELECT TOP 1 EmployeeID FROM Employees")
            emp_row = cursor.fetchone()
            emp_id  = emp_row[0] if emp_row else 1

            cursor.execute("SELECT ISNULL(MAX(OrderID),0) FROM Orders")
            new_order_id = cursor.fetchone()[0] + 1

            cursor.execute("""
                INSERT INTO Orders (OrderID, CustomerID, EmployeeID, OrderDate, TotalAmount, Status)
                VALUES (?,?,?,?,?,?)
            """, (new_order_id, cus_id, emp_id, ngay, total, status))

            for rd in self._rows:
                subtotal = rd["qty"] * rd["price"]
                cursor.execute("""
                    INSERT INTO Order_Details (OrderID, ProductID, OrderedQuantity, SubTotal)
                    VALUES (?,?,?,?)
                """, (new_order_id, rd["pid"], rd["qty"], subtotal))
                cursor.execute(
                    "UPDATE Products SET UnitsInStock = UnitsInStock - ? WHERE ProductID = ?",
                    (rd["qty"], rd["pid"])
                )

            if status == "Đã thanh toán":
                cursor.execute("SELECT ISNULL(MAX(BillID),0) FROM Bills")
                new_bill_id = cursor.fetchone()[0] + 1
                ngay_tt = self.dteNgayThanhToan.dateTime().toPyDateTime()
                pmeth   = self.cbPhuongThucThanhToan.currentText()
                tt_text = self.txtTongTienThanhToan.text().replace(",", "")
                tt_amt  = float(tt_text) if tt_text else total
                cursor.execute("""
                    INSERT INTO Bills (BillID, OrderID, PaymentDate, PaymentAmount, PaymentMethod)
                    VALUES (?,?,?,?,?)
                """, (new_bill_id, new_order_id, ngay_tt, tt_amt, pmeth))

            conn.commit()
            QtWidgets.QMessageBox.information(self, "Thành công", f"Đã tạo đơn hàng #{new_order_id}!")
            self.accept()
        except Exception as e:
            conn.rollback()
            QtWidgets.QMessageBox.critical(self, "Lỗi CSDL", f"{e}")
        finally:
            conn.close()


# ==========================================
# BỘ QUẢN LÝ ĐƠN HÀNG (CONTROLLER)
# ==========================================
class OrderManager:
    def __init__(self, table_widget, txt_search=None, date_filter=None, btn_search=None, cb_status=None,
                 dte_from=None, dte_to=None, cb_customer=None):
        self.table = table_widget
        self.txt_search = txt_search
        self.date_filter = date_filter
        self.btn_search = btn_search
        self.cb_status   = cb_status   # Nhận trực tiếp từ UI widget
        self.dte_from    = dte_from    # QDateEdit — từ ngày
        self.dte_to      = dte_to      # QDateEdit — đến ngày
        self.cb_customer = cb_customer # QComboBox — lọc theo khách hàng

        self.switch_to_customer_callback = None

        self.init_ui()

        if self.btn_search:
            self.btn_search.clicked.connect(self.on_search_triggered)
        if self.txt_search:
            self.txt_search.textChanged.connect(self.on_search_triggered)
        if self.date_filter:
            self.date_filter.textChanged.connect(self.on_search_triggered)
        if self.cb_status:
            self.cb_status.currentIndexChanged.connect(self.on_search_triggered)
        if self.dte_from:
            self.dte_from.dateChanged.connect(self.on_search_triggered)
        if self.dte_to:
            self.dte_to.dateChanged.connect(self.on_search_triggered)
        if self.cb_customer:
            self.cb_customer.currentIndexChanged.connect(self.on_search_triggered)

    def on_search_triggered(self, *args):
        self.load_data()

    def _create_status_combobox(self):
        """Tạo ComboBox lọc trạng thái và chèn vào layout cạnh date_filter."""
        cb = QtWidgets.QComboBox()
        cb.addItems(["Tất cả", "Đã thanh toán", "Chưa thanh toán"])
        cb.setMinimumWidth(180)
        cb.setFixedHeight(self.date_filter.height() if self.date_filter else 36)
        cb.setStyleSheet("""
            QComboBox {
                background-color: #f9fafb;
                border: 1px solid #e5e7eb;
                border-radius: 8px;
                padding: 6px 12px;
                color: #111827;
                font-size: 13px;
            }
            QComboBox:focus {
                border: 2px solid #2563eb;
                background-color: #ffffff;
            }
            QComboBox::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 28px;
                border-left: 1px solid #e5e7eb;
                border-top-right-radius: 8px;
                border-bottom-right-radius: 8px;
            }
            QComboBox QAbstractItemView {
                background-color: #ffffff;
                border: 1px solid #d1d5db;
                border-radius: 6px;
                selection-background-color: #2563eb;
                selection-color: white;
                padding: 4px;
                outline: none;
            }
        """)

        # Chèn vào layout cha của date_filter (ngay sau date_filter)
        if self.date_filter:
            parent_widget = self.date_filter.parent()
            layout = parent_widget.layout() if parent_widget else None
            if layout:
                idx = layout.indexOf(self.date_filter)
                if idx >= 0:
                    layout.insertWidget(idx + 1, cb)
                else:
                    layout.addWidget(cb)
            else:
                # Fallback: đặt cạnh date_filter bằng geometry
                geo = self.date_filter.geometry()
                cb.setParent(parent_widget)
                cb.setGeometry(geo.right() + 8, geo.top(), 180, geo.height())
                cb.show()
        elif self.table:
            # Fallback cuối: đặt vào parent của table
            parent_widget = self.table.parent()
            if parent_widget and parent_widget.layout():
                parent_widget.layout().insertWidget(0, cb)

        cb.currentIndexChanged.connect(self.on_search_triggered)
        return cb

    def init_ui(self):
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(
            ["Mã đơn", "Tên KH", "Ngày đặt hàng", "Tổng tiền", "Trạng thái", "Thao tác"])

        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(5, QtWidgets.QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(5, 200)

        if self.date_filter:
            self.date_filter.setStyleSheet("""
                QLineEdit {
                    background-color: #f9fafb;
                    border: 1px solid #e5e7eb;
                    border-radius: 8px;
                    padding: 8px 12px;
                    color: #111827;
                }
                QLineEdit:focus {
                    border: 2px solid #2563eb;
                    background-color: #ffffff;
                }
            """)
            self.date_filter.setPlaceholderText("VD: 03/2026, 2026, 02/03...")

        # Populate cb_status nếu được truyền vào từ UI
        if self.cb_status:
            self.cb_status.blockSignals(True)
            self.cb_status.clear()
            self.cb_status.addItems(["Tất cả", "Đã thanh toán", "Chưa thanh toán"])
            self.cb_status.blockSignals(False)

        # Khởi tạo bộ lọc ngày
        from PyQt6.QtCore import QDate
        if self.dte_from:
            self.dte_from.setCalendarPopup(True)
            self.dte_from.setDisplayFormat("dd/MM/yyyy")
            self.dte_from.setDate(QDate(QDate.currentDate().year(), 1, 1))
        if self.dte_to:
            self.dte_to.setCalendarPopup(True)
            self.dte_to.setDisplayFormat("dd/MM/yyyy")
            self.dte_to.setDate(QDate.currentDate())

        # Populate cb_customer — lọc theo khách hàng
        if self.cb_customer:
            db = DatabaseManager()
            conn = db.get_connection()
            if conn:
                try:
                    self.cb_customer.blockSignals(True)
                    self.cb_customer.clear()
                    self.cb_customer.addItem("Tất cả KH", 0)
                    cursor = conn.cursor()
                    cursor.execute("SELECT CustomerID, CustomerName FROM Customers ORDER BY CustomerName")
                    for cid, cname in cursor.fetchall():
                        self.cb_customer.addItem(cname, cid)
                    self.cb_customer.blockSignals(False)
                finally:
                    conn.close()

    def load_data(self):
        db = DatabaseManager()
        conn = db.get_connection()
        if not conn: return

        search_kw = self.txt_search.text().strip() if self.txt_search else ""
        date_kw   = self.date_filter.text().strip() if self.date_filter else ""
        status_kw = self.cb_status.currentText() if self.cb_status else "Tất cả"

        try:
            cursor = conn.cursor()
            query = """
                SELECT 
                    o.OrderID, o.OrderDate, c.CustomerName, o.TotalAmount, o.Status,
                    c.CustomerID, c.CustomerPhone
                FROM Orders o
                JOIN Customers c ON o.CustomerID = c.CustomerID
                WHERE 1=1
            """
            params = []

            if search_kw:
                query += " AND (CAST(o.OrderID AS VARCHAR(50)) LIKE ? OR c.CustomerName LIKE ?)"
                params.extend([f"%{search_kw}%", f"%{search_kw}%"])

            # FIX 1: Dùng FORMAT() để luôn ra dd/MM/yyyy đúng, kể cả ngày 02, 03 (có số 0 đứng trước)
            if date_kw:
                query += """
                    AND (
                        FORMAT(o.OrderDate, 'dd/MM/yyyy') LIKE ?
                        OR FORMAT(o.OrderDate, 'MM/yyyy')  LIKE ?
                        OR FORMAT(o.OrderDate, 'yyyy')      LIKE ?
                        OR FORMAT(o.OrderDate, 'dd')        LIKE ?
                    )
                """
                params.extend([f"%{date_kw}%", f"%{date_kw}%", f"%{date_kw}%", f"%{date_kw}%"])

            if status_kw and status_kw != "Tất cả":
                query += " AND o.Status = ?"
                params.append(status_kw)

            # Lọc theo khoảng thời gian
            if self.dte_from:
                date_from = self.dte_from.date().toPyDate()
                query += " AND CAST(o.OrderDate AS DATE) >= ?"
                params.append(date_from)
            if self.dte_to:
                date_to = self.dte_to.date().toPyDate()
                query += " AND CAST(o.OrderDate AS DATE) <= ?"
                params.append(date_to)

            # Lọc theo khách hàng
            if self.cb_customer:
                cus_val = self.cb_customer.currentData()
                if cus_val:
                    query += " AND c.CustomerID = ?"
                    params.append(cus_val)

            query += " ORDER BY o.OrderDate DESC"

            cursor.execute(query, tuple(params))
            rows = cursor.fetchall()

            self.table.setRowCount(0)
            for i, row in enumerate(rows):
                self.table.insertRow(i)

                order_id  = row[0]
                date_str  = row[1].strftime('%d/%m/%Y') if row[1] else ""
                cus_name  = row[2]
                total_str = f"{row[3]:,.0f} VNĐ" if row[3] else "0 VNĐ"
                status    = row[4]

                self.table.setItem(i, 0, QtWidgets.QTableWidgetItem(str(order_id)))
                self.table.setItem(i, 1, QtWidgets.QTableWidgetItem(cus_name))
                self.table.setItem(i, 2, QtWidgets.QTableWidgetItem(date_str))
                self.table.setItem(i, 3, QtWidgets.QTableWidgetItem(total_str))

                status_item = QtWidgets.QTableWidgetItem(status)
                if status == "Đã thanh toán":
                    status_item.setForeground(Qt.GlobalColor.darkGreen)
                elif status == "Đã hủy":
                    status_item.setForeground(Qt.GlobalColor.darkRed)
                else:
                    status_item.setForeground(Qt.GlobalColor.red)
                self.table.setItem(i, 4, status_item)

                item_data = {
                    "id": order_id, "ngay": date_str, "tien": total_str, "trang_thai": status,
                    "customer_info": {"id": row[5], "ten": cus_name, "sdt": row[6]}
                }
                self.add_action_buttons(i, item_data)

        except Exception as e:
            QtWidgets.QMessageBox.critical(self.table.window(), "Lỗi SQL", f"Lỗi load Đơn hàng:\n{e}")
        finally:
            conn.close()

    def add_action_buttons(self, row, item):
        container = QtWidgets.QWidget()
        layout = QtWidgets.QHBoxLayout(container)
        layout.setContentsMargins(5, 2, 5, 2)
        layout.setSpacing(5)

        btn_view   = QtWidgets.QPushButton("Xem")
        btn_edit   = QtWidgets.QPushButton("Sửa")
        btn_delete = QtWidgets.QPushButton("Xóa")

        style = "padding: 5px; font-weight: bold; border-radius: 4px; color: white; border: none;"
        btn_view.setStyleSheet(f"background-color: #10b981; {style}")
        btn_edit.setStyleSheet(f"background-color: #f59e0b; {style}")
        btn_delete.setStyleSheet(f"background-color: #ef4444; {style}")

        btn_view.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_edit.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_delete.setCursor(Qt.CursorShape.PointingHandCursor)

        btn_view.clicked.connect(lambda checked=False, d=item: self.open_view(d))
        btn_edit.clicked.connect(lambda checked=False, d=item: self.open_edit(d))
        btn_delete.clicked.connect(lambda checked=False, d=item: self.open_delete(d))

        layout.addWidget(btn_view)
        layout.addWidget(btn_edit)
        layout.addWidget(btn_delete)
        self.table.setCellWidget(row, 5, container)

    def open_view(self, item):
        dialog = ViewOrder(item, self.switch_to_customer_callback)
        dialog.exec()

    def open_create(self):
        dialog = AddOrder(self.table.window())
        if dialog.exec():
            self.load_data()

    def open_edit(self, item):
        if EditOrder(item).exec():
            self.load_data()

    def open_delete(self, item):
        if DeleteOrder(item).exec():
            self.load_data()