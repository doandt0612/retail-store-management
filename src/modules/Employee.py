import os
from PyQt6 import uic, QtWidgets
from PyQt6.QtCore import Qt, QDate
from src.database.db_connection import DatabaseManager

# Thiết lập đường dẫn (Vẫn giữ trỏ về thư mục NhanVien chứa file UI của bạn)
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(os.path.dirname(CURRENT_DIR))
UI_PATH = os.path.join(ROOT_DIR, "ui", "modules_ui", "NhanVien")


# ==========================================
# 1. DIALOG: ADD EMPLOYEE
# ==========================================
class AddEmployee(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        uic.loadUi(os.path.join(UI_PATH, "addNhanVien.ui"), self)

        # Chống đơ form khi click ra ngoài
        self.setWindowModality(Qt.WindowModality.ApplicationModal)

        # Tự động set Ngày bắt đầu làm việc là ngày hôm nay
        if hasattr(self, 'deNgayBatDau'):
            self.deNgayBatDau.setDate(QDate.currentDate())

        # Kết nối sự kiện nút bấm
        self.btnLuu.clicked.connect(self.save_data)
        self.btnHuy.clicked.connect(self.reject)

    def save_data(self):
        # Lấy dữ liệu an toàn từ giao diện
        ten = self.txtTenNV.text().strip() if hasattr(self, 'txtTenNV') else ""
        sdt = self.txtSDTNV.text().strip() if hasattr(self, 'txtSDTNV') else ""
        email = self.txtEmailNV.text().strip() if hasattr(self, 'txtEmailNV') else ""
        ngay_vao = self.deNgayBatDau.date().toString("yyyy-MM-dd") if hasattr(self,
                                                                              'deNgayBatDau') else QDate.currentDate().toString(
            "yyyy-MM-dd")

        # Phân loại nhân viên (Chuyển đổi text từ ComboBox sang chuẩn của Database)
        loai_nv = "Full_time"
        if hasattr(self, 'cbLoaiNV'):
            text_loai = self.cbLoaiNV.currentText().strip().lower()
            if "part" in text_loai:
                loai_nv = "Part_time"
            else:
                loai_nv = "Full_time"

        # 1. KIỂM TRA ĐẦU VÀO CƠ BẢN
        if not ten or not sdt:
            QtWidgets.QMessageBox.warning(self, "Cảnh báo", "Vui lòng không được để trống Tên và Số điện thoại!")
            return

        db = DatabaseManager()
        conn = db.get_connection()
        if not conn: return

        try:
            cursor = conn.cursor()

            # 2. KIỂM TRA TRÙNG LẶP SỐ ĐIỆN THOẠI VÀ EMAIL (Theo ràng buộc UNIQUE của SQL)
            cursor.execute("SELECT COUNT(*) FROM Employees WHERE EmployeePhone = ?", (sdt,))
            if cursor.fetchone()[0] > 0:
                QtWidgets.QMessageBox.warning(self, "Từ chối", "Số điện thoại này đã được nhân viên khác sử dụng!")
                return

            if email:  # Chỉ kiểm tra Email nếu có nhập
                cursor.execute("SELECT COUNT(*) FROM Employees WHERE EmployeeEmail = ?", (email,))
                if cursor.fetchone()[0] > 0:
                    QtWidgets.QMessageBox.warning(self, "Từ chối", "Email này đã tồn tại trong hệ thống!")
                    return

            # 3. TẠO ID MỚI (Tự động tăng)
            cursor.execute("SELECT ISNULL(MAX(EmployeeID), 0) FROM Employees")
            new_id = cursor.fetchone()[0] + 1

            # 4. THÊM VÀO BẢNG EMPLOYEES CHÍNH
            cursor.execute("""
                INSERT INTO Employees (EmployeeID, EmployeeName, EmployeePhone, EmployeeEmail, HireDate, Status, EmployeeType)
                VALUES (?, ?, ?, ?, ?, N'Đang làm việc', ?)
            """, (new_id, ten, sdt, email, ngay_vao, loai_nv))

            # 5. TẠO SẴN BẢN GHI TRỐNG Ở BẢNG LƯƠNG TƯƠNG ỨNG
            # (Bước này CỰC KỲ QUAN TRỌNG để khi bạn bấm nút "Sửa" sau này sẽ không bị lỗi do thiếu dữ liệu)
            # 5. TẠO SẴN BẢN GHI TRỐNG (Đã sửa số 0 thành số 1 để thỏa mãn điều kiện CHECK > 0 của SQL)
            if loai_nv == 'Full_time':
                cursor.execute(
                    "INSERT INTO Full_Time (EmployeeID, MonthlySalary, Position) VALUES (?, 1, N'Chưa cập nhật')",
                    (new_id,))
            else:
                cursor.execute("INSERT INTO Part_Time (EmployeeID, HourlyRate, WorkingHoursPerWeek) VALUES (?, 1, 1)",
                               (new_id,))

            conn.commit()
            QtWidgets.QMessageBox.information(self, "Thành công", f"Đã thêm nhân viên '{ten}' thành công!")
            self.accept()

        except Exception as e:
            conn.rollback()  # Hoàn tác nếu có lỗi
            QtWidgets.QMessageBox.critical(self, "Lỗi hệ thống", f"Không thể thêm nhân viên:\n{str(e)}")
        finally:
            conn.close()



# ==========================================
# 2. DIALOG: EDIT EMPLOYEE FULL-TIME
# ==========================================
# ==========================================
# 2. DIALOG: EDIT EMPLOYEE FULL-TIME
# ==========================================
# ==========================================
# 2. DIALOG: EDIT EMPLOYEE FULL-TIME
# ==========================================
# ==========================================
# 2. DIALOG: EDIT EMPLOYEE FULL-TIME
# ==========================================
class EditEmployeeFullTime(QtWidgets.QDialog):
    def __init__(self, emp_id, parent=None):
        super().__init__(parent)
        uic.loadUi(os.path.join(UI_PATH, "editNhanVietFullTime.ui"), self)
        self.setWindowModality(Qt.WindowModality.ApplicationModal)

        # Kéo dài cửa sổ thêm một chút để không bị cắt đuôi nút Hủy
        self.resize(self.width(), self.height() + 30)

        # Ép màu chữ và làm đẹp lại nút Hủy
        self.setStyleSheet(self.styleSheet() + " QLineEdit, QComboBox { color: #111827; }")
        if hasattr(self, 'btnHuy'):
            self.btnHuy.setStyleSheet(
                "background-color: #ffffff; color: #374151; border: 1px solid #d1d5db; border-radius: 8px; font-weight: bold; padding: 10px;")

        self.emp_id = emp_id
        self.load_old_data()

        self.btnLuu.clicked.connect(self.update_data)
        if hasattr(self, 'btnHuy'): self.btnHuy.clicked.connect(self.reject)

    def load_old_data(self):
        db = DatabaseManager()
        conn = db.get_connection()
        try:
            cursor = conn.cursor()
            query = """
                SELECT e.EmployeeName, e.EmployeePhone, e.EmployeeEmail, e.Status, 
                       f.Position, f.MonthlySalary
                FROM Employees e
                LEFT JOIN Full_Time f ON e.EmployeeID = f.EmployeeID
                WHERE e.EmployeeID = ?
            """
            cursor.execute(query, (self.emp_id,))
            row = cursor.fetchone()

            if row:
                if hasattr(self, 'txtReadOnlyMaNV'): self.txtReadOnlyMaNV.setText(str(self.emp_id))
                if hasattr(self, 'txtTenNV'): self.txtTenNV.setText(row[0])
                if hasattr(self, 'txtSDT'): self.txtSDT.setText(row[1])
                if hasattr(self, 'txtEmail'): self.txtEmail.setText(row[2] if row[2] else "")

                if hasattr(self, 'cbTrangThai'):
                    status_text = "Còn làm việc" if row[3] == "Đang làm việc" else "Đã nghỉ việc"
                    self.cbTrangThai.setCurrentText(status_text)

                if hasattr(self, 'txtChucVu'): self.txtChucVu.setText(row[4] if row[4] else "")
                if hasattr(self, 'txtLuongCoBan'): self.txtLuongCoBan.setText(str(int(row[5] if row[5] else 0)))

                # MỞ KHÓA COMBOBOX: Thêm cả 2 lựa chọn để xổ xuống được
                if hasattr(self, 'comboBox'):
                    self.comboBox.clear()
                    self.comboBox.addItems(["Full-time", "Part-time"])
                    self.comboBox.setCurrentText("Full-time")
                    # Đã xóa dòng setEnabled(False)

        except Exception as e:
            print(e)
        finally:
            conn.close()

    def update_data(self):
        ten = self.txtTenNV.text().strip() if hasattr(self, 'txtTenNV') else ""
        sdt = self.txtSDT.text().strip() if hasattr(self, 'txtSDT') else ""
        email = self.txtEmail.text().strip() if hasattr(self, 'txtEmail') else ""
        chuc_vu = self.txtChucVu.text().strip() if hasattr(self, 'txtChucVu') else ""

        trang_thai = "Đang làm việc"
        if hasattr(self, 'cbTrangThai') and self.cbTrangThai.currentText() == "Đã nghỉ việc":
            trang_thai = "Đã nghỉ việc"

        # Lấy loại nhân viên mới từ ComboBox
        loai_nv_moi = "Full_time"
        if hasattr(self, 'comboBox') and "Part" in self.comboBox.currentText():
            loai_nv_moi = "Part_time"

        try:
            luong = float(self.txtLuongCoBan.text().strip() or 0)
            if luong <= 0:
                QtWidgets.QMessageBox.warning(self, "Lỗi", "Lương cơ bản phải lớn hơn 0!")
                return
        except ValueError:
            QtWidgets.QMessageBox.warning(self, "Lỗi", "Vui lòng nhập lương là một số hợp lệ!")
            return

        if not ten or not sdt:
            QtWidgets.QMessageBox.warning(self, "Lỗi", "Vui lòng không để trống Tên và Số điện thoại!")
            return

        db = DatabaseManager()
        conn = db.get_connection()
        try:
            cursor = conn.cursor()

            cursor.execute("SELECT COUNT(*) FROM Employees WHERE EmployeePhone = ? AND EmployeeID != ?",
                           (sdt, self.emp_id))
            if cursor.fetchone()[0] > 0:
                QtWidgets.QMessageBox.warning(self, "Từ chối", "Số điện thoại đã bị trùng với người khác!")
                return

            if email:
                cursor.execute("SELECT COUNT(*) FROM Employees WHERE EmployeeEmail = ? AND EmployeeID != ?",
                               (email, self.emp_id))
                if cursor.fetchone()[0] > 0:
                    QtWidgets.QMessageBox.warning(self, "Từ chối", "Email đã bị trùng với người khác!")
                    return

            # CẬP NHẬT THÔNG TIN CHUNG VÀ LOẠI NHÂN VIÊN MỚI
            cursor.execute("""
                UPDATE Employees SET EmployeeName = ?, EmployeePhone = ?, EmployeeEmail = ?, Status = ?, EmployeeType = ? 
                WHERE EmployeeID = ?
            """, (ten, sdt, email, trang_thai, loai_nv_moi, self.emp_id))

            # LƯU THÔNG TIN FULL-TIME HIỆN TẠI (Để giữ lại lịch sử nếu sau này họ đổi lại)
            cursor.execute("""
                UPDATE Full_Time SET Position = ?, MonthlySalary = ? WHERE EmployeeID = ?
            """, (chuc_vu, luong, self.emp_id))

            # CHUYỂN ĐỔI: NẾU ĐỔI SANG PART-TIME, TẠO SẴN BẢN GHI ĐỂ TRÁNH LỖI MỞ FORM
            if loai_nv_moi == "Part_time":
                cursor.execute("SELECT COUNT(*) FROM Part_Time WHERE EmployeeID = ?", (self.emp_id,))
                if cursor.fetchone()[0] == 0:
                    cursor.execute(
                        "INSERT INTO Part_Time (EmployeeID, HourlyRate, WorkingHoursPerWeek) VALUES (?, 1, 1)",
                        (self.emp_id,))

            conn.commit()
            QtWidgets.QMessageBox.information(self, "Thành công", "Cập nhật thông tin nhân viên thành công!")
            self.accept()
        except Exception as e:
            conn.rollback()
            QtWidgets.QMessageBox.critical(self, "Lỗi SQL", f"Lỗi hệ thống: {e}")
        finally:
            conn.close()

# ==========================================
# 3. DIALOG: EDIT EMPLOYEE PART-TIME
# ==========================================
# ==========================================
# 3. DIALOG: EDIT EMPLOYEE PART-TIME
# ==========================================
# ==========================================
# 3. DIALOG: EDIT EMPLOYEE PART-TIME
# ==========================================
# ==========================================
# 3. DIALOG: EDIT EMPLOYEE PART-TIME
# ==========================================
class EditEmployeePartTime(QtWidgets.QDialog):
    def __init__(self, emp_id, parent=None):
        super().__init__(parent)
        uic.loadUi(os.path.join(UI_PATH, "editNhanVietPartTime.ui"), self)
        self.setWindowModality(Qt.WindowModality.ApplicationModal)

        # Kéo dài cửa sổ thêm một chút để không bị cắt đuôi nút Hủy
        self.resize(self.width(), self.height() + 30)

        # Ép màu chữ và làm đẹp lại nút Hủy
        self.setStyleSheet(self.styleSheet() + " QLineEdit, QComboBox { color: #111827; }")
        if hasattr(self, 'btnHuy'):
            self.btnHuy.setStyleSheet(
                "background-color: #ffffff; color: #374151; border: 1px solid #d1d5db; border-radius: 8px; font-weight: bold; padding: 10px;")

        self.emp_id = emp_id
        self.load_old_data()

        self.btnLuu.clicked.connect(self.update_data)
        if hasattr(self, 'btnHuy'): self.btnHuy.clicked.connect(self.reject)

    def load_old_data(self):
        db = DatabaseManager()
        conn = db.get_connection()
        try:
            cursor = conn.cursor()
            query = """
                SELECT e.EmployeeName, e.EmployeePhone, e.EmployeeEmail, e.Status, 
                       p.HourlyRate, p.WorkingHoursPerWeek
                FROM Employees e
                LEFT JOIN Part_Time p ON e.EmployeeID = p.EmployeeID
                WHERE e.EmployeeID = ?
            """
            cursor.execute(query, (self.emp_id,))
            row = cursor.fetchone()

            if row:
                if hasattr(self, 'txtReadOnlyMaNV'): self.txtReadOnlyMaNV.setText(str(self.emp_id))
                if hasattr(self, 'txtTenNV'): self.txtTenNV.setText(row[0])
                if hasattr(self, 'txtSDT'): self.txtSDT.setText(row[1])
                if hasattr(self, 'txtEmail'): self.txtEmail.setText(row[2] if row[2] else "")

                if hasattr(self, 'cbTrangThai'):
                    status_text = "Còn làm việc" if row[3] == "Đang làm việc" else "Đã nghỉ việc"
                    self.cbTrangThai.setCurrentText(status_text)

                if hasattr(self, 'txtLuongGio'): self.txtLuongGio.setText(str(int(row[4] if row[4] else 0)))
                if hasattr(self, 'txtSoGioLamViec'): self.txtSoGioLamViec.setText(str(row[5] if row[5] else 0))

                # MỞ KHÓA COMBOBOX
                if hasattr(self, 'comboBox'):
                    self.comboBox.clear()
                    self.comboBox.addItems(["Part-time", "Full-time"])
                    self.comboBox.setCurrentText("Part-time")
                    # Đã xóa dòng setEnabled(False)

        except Exception as e:
            print(e)
        finally:
            conn.close()

    def update_data(self):
        ten = self.txtTenNV.text().strip() if hasattr(self, 'txtTenNV') else ""
        sdt = self.txtSDT.text().strip() if hasattr(self, 'txtSDT') else ""
        email = self.txtEmail.text().strip() if hasattr(self, 'txtEmail') else ""

        trang_thai = "Đang làm việc"
        if hasattr(self, 'cbTrangThai') and self.cbTrangThai.currentText() == "Đã nghỉ việc":
            trang_thai = "Đã nghỉ việc"

        # Lấy loại nhân viên mới từ ComboBox
        loai_nv_moi = "Part_time"
        if hasattr(self, 'comboBox') and "Full" in self.comboBox.currentText():
            loai_nv_moi = "Full_time"

        try:
            luong_gio = float(self.txtLuongGio.text().strip() or 0)
            so_gio = int(self.txtSoGioLamViec.text().strip() or 0)
            if luong_gio <= 0 or so_gio <= 0:
                QtWidgets.QMessageBox.warning(self, "Lỗi", "Lương giờ và Số giờ làm việc phải lớn hơn 0!")
                return
        except ValueError:
            QtWidgets.QMessageBox.warning(self, "Lỗi", "Vui lòng nhập số hợp lệ cho Lương và Giờ làm!")
            return

        if not ten or not sdt:
            QtWidgets.QMessageBox.warning(self, "Lỗi", "Vui lòng không để trống Tên và Số điện thoại!")
            return

        db = DatabaseManager()
        conn = db.get_connection()
        try:
            cursor = conn.cursor()

            cursor.execute("SELECT COUNT(*) FROM Employees WHERE EmployeePhone = ? AND EmployeeID != ?",
                           (sdt, self.emp_id))
            if cursor.fetchone()[0] > 0:
                QtWidgets.QMessageBox.warning(self, "Từ chối", "Số điện thoại đã bị trùng với người khác!")
                return

            if email:
                cursor.execute("SELECT COUNT(*) FROM Employees WHERE EmployeeEmail = ? AND EmployeeID != ?",
                               (email, self.emp_id))
                if cursor.fetchone()[0] > 0:
                    QtWidgets.QMessageBox.warning(self, "Từ chối", "Email đã bị trùng với người khác!")
                    return

            # CẬP NHẬT THÔNG TIN CHUNG VÀ LOẠI NHÂN VIÊN MỚI
            cursor.execute("""
                UPDATE Employees SET EmployeeName = ?, EmployeePhone = ?, EmployeeEmail = ?, Status = ?, EmployeeType = ? 
                WHERE EmployeeID = ?
            """, (ten, sdt, email, trang_thai, loai_nv_moi, self.emp_id))

            # LƯU THÔNG TIN PART-TIME HIỆN TẠI
            cursor.execute("""
                UPDATE Part_Time SET HourlyRate = ?, WorkingHoursPerWeek = ? WHERE EmployeeID = ?
            """, (luong_gio, so_gio, self.emp_id))

            # CHUYỂN ĐỔI: NẾU ĐỔI SANG FULL-TIME, TẠO SẴN BẢN GHI ĐỂ TRÁNH LỖI MỞ FORM
            if loai_nv_moi == "Full_time":
                cursor.execute("SELECT COUNT(*) FROM Full_Time WHERE EmployeeID = ?", (self.emp_id,))
                if cursor.fetchone()[0] == 0:
                    cursor.execute(
                        "INSERT INTO Full_Time (EmployeeID, MonthlySalary, Position) VALUES (?, 1, N'Chưa cập nhật')",
                        (self.emp_id,))

            conn.commit()
            QtWidgets.QMessageBox.information(self, "Thành công", "Cập nhật thông tin nhân viên thành công!")
            self.accept()
        except Exception as e:
            conn.rollback()
            QtWidgets.QMessageBox.critical(self, "Lỗi SQL", f"Lỗi hệ thống: {e}")
        finally:
            conn.close()
# ==========================================
# 4. DIALOGS: VIEW & DELETE EMPLOYEE
# ==========================================
class ViewEmployeeFullTime(QtWidgets.QDialog):
    def __init__(self, emp_id, parent=None):
        super().__init__(parent)
        uic.loadUi(os.path.join(UI_PATH, "viewNhanVienFullTime.ui"), self)

        self.emp_id = emp_id
        self.load_data()

        if hasattr(self, 'btnSua'):
            self.btnSua.clicked.connect(self.open_edit)

    def open_edit(self):
        """Đóng form Xem và mở form Sửa lên thay thế"""
        self.accept()
        EditEmployeeFullTime(self.emp_id, self.parent()).exec()

    def load_data(self):
        db = DatabaseManager()
        conn = db.get_connection()
        if not conn: return

        try:
            cursor = conn.cursor()
            query = """
                SELECT 
                    e.EmployeeID, e.EmployeeName, e.EmployeePhone, e.EmployeeEmail, e.HireDate, e.Status, e.EmployeeType,
                    f.Position, f.MonthlySalary
                FROM Employees e
                LEFT JOIN Full_Time f ON e.EmployeeID = f.EmployeeID
                WHERE e.EmployeeID = ?
            """
            cursor.execute(query, (self.emp_id,))
            row = cursor.fetchone()

            if row:
                if hasattr(self, 'lblHienThiMaNV'): self.lblHienThiMaNV.setText(str(row[0]))
                if hasattr(self, 'lblHienThiTenNV'): self.lblHienThiTenNV.setText(row[1])
                if hasattr(self, 'lblHienThiSDT'): self.lblHienThiSDT.setText(row[2])
                if hasattr(self, 'lblHienThiEmail'): self.lblHienThiEmail.setText(row[3] if row[3] else "Chưa cập nhật")

                # Tên biến trong file UI của bạn không có lblHienThiNgayBatDau, nên tôi đã bỏ qua để tránh lỗi.

                if hasattr(self, 'lblHienThiTrangThai'):
                    self.lblHienThiTrangThai.setText(row[5])
                    if row[5] == "Đang làm việc":
                        self.lblHienThiTrangThai.setStyleSheet("color: #10b981; font-weight: bold;")
                    else:
                        self.lblHienThiTrangThai.setStyleSheet("color: #ef4444; font-weight: bold;")

                # ĐÃ SỬA: Dùng đúng tên biến lblHienThiLoaiNV_2 [cite: 125]
                if hasattr(self, 'lblHienThiLoaiNV_2'):
                    loai_nv = "Toàn thời gian" if row[6] == "Full_time" else "Bán thời gian"
                    self.lblHienThiLoaiNV_2.setText(loai_nv)
                    self.lblHienThiLoaiNV_2.setStyleSheet("color: #1d4ed8; font-weight: bold;")

                if hasattr(self, 'lblHienThiChucVu'): self.lblHienThiChucVu.setText(
                    row[7] if row[7] else "Chưa cập nhật")
                if hasattr(self, 'lblHienThiLuongCoBan'):
                    luong = float(row[8]) if row[8] else 0
                    self.lblHienThiLuongCoBan.setText(f"{luong:,.0f} VNĐ")

        except Exception as e:
            print(f"Lỗi load chi tiết Full-time: {e}")
        finally:
            conn.close()


class ViewEmployeePartTime(QtWidgets.QDialog):
    def __init__(self, emp_id, parent=None):
        super().__init__(parent)
        uic.loadUi(os.path.join(UI_PATH, "viewNhanVienPartTime.ui"), self)

        self.emp_id = emp_id
        self.load_data()

        if hasattr(self, 'btnSua'):
            self.btnSua.clicked.connect(self.open_edit)

    def open_edit(self):
        """Đóng form Xem và mở form Sửa lên thay thế"""
        self.accept()
        EditEmployeePartTime(self.emp_id, self.parent()).exec()

    def load_data(self):
        db = DatabaseManager()
        conn = db.get_connection()
        if not conn: return

        try:
            cursor = conn.cursor()
            query = """
                SELECT 
                    e.EmployeeID, e.EmployeeName, e.EmployeePhone, e.EmployeeEmail, e.HireDate, e.Status, e.EmployeeType,
                    p.HourlyRate, p.WorkingHoursPerWeek
                FROM Employees e
                LEFT JOIN Part_Time p ON e.EmployeeID = p.EmployeeID
                WHERE e.EmployeeID = ?
            """
            cursor.execute(query, (self.emp_id,))
            row = cursor.fetchone()

            if row:
                if hasattr(self, 'lblHienThiMaNV'): self.lblHienThiMaNV.setText(str(row[0]))
                if hasattr(self, 'lblHienThiTenNV'): self.lblHienThiTenNV.setText(row[1])
                if hasattr(self, 'lblHienThiSDT'): self.lblHienThiSDT.setText(row[2])
                if hasattr(self, 'lblHienThiEmail'): self.lblHienThiEmail.setText(row[3] if row[3] else "Chưa cập nhật")

                if hasattr(self, 'lblHienThiTrangThai'):
                    self.lblHienThiTrangThai.setText(row[5])
                    if row[5] == "Đang làm việc":
                        self.lblHienThiTrangThai.setStyleSheet("color: #10b981; font-weight: bold;")
                    else:
                        self.lblHienThiTrangThai.setStyleSheet("color: #ef4444; font-weight: bold;")

                # ĐÃ SỬA: Dùng đúng tên biến lblHienThiLoaiNV_2 [cite: 159]
                if hasattr(self, 'lblHienThiLoaiNV_2'):
                    loai_nv = "Bán thời gian" if row[6] == "Part_time" else "Toàn thời gian"
                    self.lblHienThiLoaiNV_2.setText(loai_nv)
                    self.lblHienThiLoaiNV_2.setStyleSheet("color: #7e22ce; font-weight: bold;")

                if hasattr(self, 'lblHienThiLuongGio'):
                    luong_gio = float(row[7]) if row[7] else 0
                    self.lblHienThiLuongGio.setText(f"{luong_gio:,.0f} VNĐ/h")
                if hasattr(self, 'lblHienThiSoGioLamViec'):
                    so_gio = int(row[8]) if row[8] else 0
                    self.lblHienThiSoGioLamViec.setText(f"{so_gio} giờ/tuần")

        except Exception as e:
            print(f"Lỗi load chi tiết Part-time: {e}")
        finally:
            conn.close()


class DeleteEmployee(QtWidgets.QDialog):
    def __init__(self, emp_id, parent=None):
        super().__init__(parent)
        uic.loadUi(os.path.join(UI_PATH, "deleteNhanVien.ui"), self)

        # Khóa nền màn hình chính khi popup hiện lên
        self.setWindowModality(Qt.WindowModality.ApplicationModal)

        self.emp_id = emp_id

        # Kết nối sự kiện cho 2 nút [cite: 31, 32]
        if hasattr(self, 'btnXoa'):
            self.btnXoa.clicked.connect(self.delete_logic)
        if hasattr(self, 'btnHuy'):
            self.btnHuy.clicked.connect(self.reject)

    def delete_logic(self):
        # Xác nhận lại một lần nữa cho chắc chắn
        reply = QtWidgets.QMessageBox.question(
            self,
            'Xác nhận',
            'Bạn có chắc chắn muốn cho nhân viên này nghỉ việc?',
            QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No,
            QtWidgets.QMessageBox.StandardButton.No
        )

        if reply == QtWidgets.QMessageBox.StandardButton.No:
            return

        db = DatabaseManager()
        conn = db.get_connection()
        if not conn: return

        try:
            cursor = conn.cursor()

            # KIỂM TRA TRẠNG THÁI HIỆN TẠI: Nếu đã nghỉ rồi thì không cần xử lý nữa
            cursor.execute("SELECT Status FROM Employees WHERE EmployeeID = ?", (self.emp_id,))
            current_status = cursor.fetchone()
            if current_status and current_status[0] == "Đã nghỉ việc":
                QtWidgets.QMessageBox.information(self, "Thông báo", "Nhân viên này vốn đã ở trạng thái nghỉ việc rồi!")
                self.reject()
                return

            # THỰC HIỆN SOFT DELETE: Đổi trạng thái thay vì DELETE vĩnh viễn
            cursor.execute("UPDATE Employees SET Status = N'Đã nghỉ việc' WHERE EmployeeID = ?", (self.emp_id,))
            conn.commit()

            QtWidgets.QMessageBox.information(self, "Thành công",
                                              "Đã chuyển nhân viên sang trạng thái 'Đã nghỉ việc")
            self.accept()  # Đóng form và báo hiệu thành công để bảng bên ngoài tự load lại

        except Exception as e:
            conn.rollback()
            QtWidgets.QMessageBox.critical(self, "Lỗi SQL", f"Không thể xử lý:\n{str(e)}")
        finally:
            conn.close()

# ==========================================
# 5. CONTROLLER: EMPLOYEE MANAGER
# ==========================================
class EmployeeManager:
    def __init__(self, table_widget, txt_search=None, btn_search=None, cb_type=None):
        self.table = table_widget
        self.txt_search = txt_search
        self.cb_type = cb_type

        self.init_ui_style()

        if btn_search:
            btn_search.clicked.connect(self.on_search_triggered)
        if txt_search:
            txt_search.textChanged.connect(self.on_search_triggered)
        if self.cb_type:
            self.cb_type.currentIndexChanged.connect(self.on_search_triggered)

    def on_search_triggered(self, *args):
        self.load_data()

    def init_ui_style(self):
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["Mã NV", "Tên NV", "Loại NV", "SĐT", "Email", "Thao tác"])
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(5, QtWidgets.QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(5, 210)

    def load_data(self, *args):
        db = DatabaseManager()
        conn = db.get_connection()
        if not conn: return

        search_kw = self.txt_search.text().strip() if self.txt_search else ""
        type_kw   = self.cb_type.currentText() if self.cb_type else "Tất cả"

        try:
            cursor = conn.cursor()
            query = """
                SELECT EmployeeID, EmployeeName, EmployeePhone, EmployeeEmail, EmployeeType, Status 
                FROM Employees WHERE 1=1
            """
            params = []

            if search_kw:
                query += " AND (EmployeeName LIKE ? OR EmployeePhone LIKE ?)"
                params.extend([f"%{search_kw}%", f"%{search_kw}%"])

            # Lọc theo loại nhân viên
            if type_kw == "Toàn thời gian":
                query += " AND EmployeeType = 'Full_time'"
            elif type_kw == "Bán thời gian":
                query += " AND EmployeeType = 'Part_time'"

            query += " ORDER BY EmployeeID DESC"
            cursor.execute(query, tuple(params))
            rows = cursor.fetchall()

            self.table.setRowCount(0)
            for row_idx, row in enumerate(rows):
                self.table.insertRow(row_idx)

                is_nghi_viec = (row[5] == "Đã nghỉ việc")

                item_ma   = QtWidgets.QTableWidgetItem(str(row[0]))
                ten_hien_thi = f"{row[1]} (Đã nghỉ)" if is_nghi_viec else row[1]
                item_ten  = QtWidgets.QTableWidgetItem(ten_hien_thi)
                loai_nv   = "Toàn thời gian" if row[4] == "Full_time" else "Bán thời gian"
                item_loai = QtWidgets.QTableWidgetItem(loai_nv)
                item_sdt  = QtWidgets.QTableWidgetItem(row[2])
                item_email= QtWidgets.QTableWidgetItem(row[3] if row[3] else "")

                if is_nghi_viec:
                    for it in [item_ma, item_ten, item_loai, item_sdt, item_email]:
                        it.setForeground(Qt.GlobalColor.gray)
                    item_ten.setForeground(Qt.GlobalColor.red)
                else:
                    item_loai.setForeground(
                        Qt.GlobalColor.darkBlue if row[4] == "Full_time" else Qt.GlobalColor.darkMagenta
                    )

                self.table.setItem(row_idx, 0, item_ma)
                self.table.setItem(row_idx, 1, item_ten)
                self.table.setItem(row_idx, 2, item_loai)
                self.table.setItem(row_idx, 3, item_sdt)
                self.table.setItem(row_idx, 4, item_email)

                item_dict = {"id": row[0], "loai": row[4]}
                self.add_action_buttons(row_idx, item_dict)

        except Exception as e:
            QtWidgets.QMessageBox.critical(self.table.window(), "Lỗi SQL", str(e))
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

        style = "padding: 5px; font-weight: bold; border-radius: 4px; color: white;"
        btn_view.setStyleSheet(f"background-color: #0ea5e9; {style}")
        btn_edit.setStyleSheet(f"background-color: #f59e0b; {style}")
        btn_delete.setStyleSheet(f"background-color: #ef4444; {style}")

        btn_view.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_edit.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_delete.setCursor(Qt.CursorShape.PointingHandCursor)

        # Fix lambda closure bug
        btn_view.clicked.connect(lambda checked=False, d=item: self.open_view(d))
        btn_edit.clicked.connect(lambda checked=False, d=item: self.open_edit(d))
        btn_delete.clicked.connect(lambda checked=False, d=item: self.open_delete(d))

        layout.addWidget(btn_view)
        layout.addWidget(btn_edit)
        layout.addWidget(btn_delete)
        self.table.setCellWidget(row, 5, container)

    def open_view(self, item):
        if item["loai"] == "Full_time":
            ViewEmployeeFullTime(item["id"], self.table.window()).exec()
        else:
            ViewEmployeePartTime(item["id"], self.table.window()).exec()
        self.load_data()

    def open_edit(self, item):
        if item["loai"] == "Full_time":
            if EditEmployeeFullTime(item["id"], self.table.window()).exec(): self.load_data()
        else:
            if EditEmployeePartTime(item["id"], self.table.window()).exec(): self.load_data()

    def open_delete(self, item):
        if DeleteEmployee(item["id"], self.table.window()).exec():
            self.load_data()

    def open_add(self):
        if AddEmployee(self.table.window()).exec():
            self.load_data()