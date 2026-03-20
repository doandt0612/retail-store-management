import os
from PyQt6 import uic, QtWidgets
from PyQt6.QtCore import Qt
from src.database.db_connection import DatabaseManager 

# Lấy đường dẫn thư mục
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__)) 
ROOT_DIR = os.path.dirname(os.path.dirname(CURRENT_DIR))
UI_PATH = os.path.join(ROOT_DIR, "ui", "modules_ui", "DanhMuc")


# DIALOG THÊM DANH MỤC 
class AddDanhMuc(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        uic.loadUi(os.path.join(UI_PATH, "addDanhMuc.ui"), self)

        # 1. Khóa tương tác với cửa sổ chính để chống đơ form
        self.setWindowModality(Qt.WindowModality.ApplicationModal)

        # 2. Kết nối nút bấm theo đúng ID trong file UI
        self.btnLuu.clicked.connect(self.save_data)
        self.btnHuy.clicked.connect(self.reject)

        # 3. XỬ LÝ ÉP KIỂU VÌ KHÔNG ĐƯỢC SỬA FILE UI
        # Biến QComboBox thành ô nhập chữ (LineEdit) để người dùng có thể gõ dữ liệu
        self.cbDanhMuc.setEditable(True)
        self.cbTenSP.setEditable(True)

        # Thêm Placeholder text để che đi sự nhầm lẫn của nhãn (Label)
        self.cbDanhMuc.lineEdit().setPlaceholderText("Nhập tên danh mục vào đây...")
        self.cbTenSP.lineEdit().setPlaceholderText("Nhập mô tả danh mục vào đây...")

        # 4. Sinh mã tự động ngay khi mở form
        self.new_id = self.generate_new_id()

    def generate_new_id(self):
        """Hàm tự động lấy mã danh mục dạng số nguyên (int) tiếp theo"""
        db = DatabaseManager()
        conn = db.get_connection()
        new_id = 1  # Mặc định là 1 nếu CSDL chưa có danh mục nào
        if not conn:
            return new_id

        try:
            cursor = conn.cursor()
            # Tìm ID lớn nhất hiện có trong CSDL
            cursor.execute("SELECT MAX(CategoryID) FROM Categories")
            last_id = cursor.fetchone()[0]

            # Nếu đã có dữ liệu, lấy số lớn nhất cộng thêm 1
            if last_id is not None:
                new_id = int(last_id) + 1

            # Điền vào ô mã có sẵn trên giao diện (phải ép kiểu int về str khi hiển thị)
            self.txtReadOnlyMaSP.setText(str(new_id))

        except Exception as e:
            print(f"Lỗi tạo mã tự động: {e}")
        finally:
            conn.close()

        return new_id

    def save_data(self):
        # Lấy dữ liệu từ các ComboBox đã được biến thành ô nhập
        ten_dm = self.cbDanhMuc.currentText().strip()
        mo_ta = self.cbTenSP.currentText().strip()

        if not ten_dm:
            QtWidgets.QMessageBox.warning(self, "Lỗi", "Vui lòng nhập tên danh mục!")
            return

        db = DatabaseManager()
        conn = db.get_connection()
        if not conn:
            return

        try:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO CATEGORIES (CATEGORYID, CATEGORYNAME, DESCRIPTION) VALUES (?, ?, ?)",
                           (self.new_id, ten_dm, mo_ta))
            conn.commit()

            QtWidgets.QMessageBox.information(self, "Thành công", "Thêm danh mục thành công!")
            self.accept()
        except Exception as e:
            conn.rollback()
            QtWidgets.QMessageBox.critical(self, "Lỗi", f"Lỗi hệ thống: {str(e)}")
        finally:
            conn.close()


#  DIALOG SỬA DANH MỤC 
#  DIALOG SỬA DANH MỤC
class EditDanhMuc(QtWidgets.QDialog):
    # Thêm tham số parent để chống đơ/crash
    def __init__(self, data, parent=None):
        super().__init__(parent)
        uic.loadUi(os.path.join(UI_PATH, "editDanhMuc.ui"), self)

        # Khóa tương tác với cửa sổ phía sau
        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.category_id = data['id']

        # KIỂM TRA VÀ ĐIỀN DỮ LIỆU CŨ LÊN GIAO DIỆN
        try:
            # Trường hợp 1: Nếu file UI đã đặt tên chuẩn
            self.txtTenDanhMuc.setText(data['ten'])
            self.txtMoTaDanhMuc.setText(data['mota'] if data['mota'] else "")

            self.btnLuu.clicked.connect(self.update_data)
            self.btnHuy.clicked.connect(self.reject)
        except AttributeError:
            # Trường hợp 2: Nếu file UI bị nhầm tên giống file addDanhMuc.ui
            self.cbDanhMuc.setEditable(True)
            self.cbTenSP.setEditable(True)

            # Hiển thị mã danh mục (chỉ đọc)
            if hasattr(self, 'txtReadOnlyMaSP'):
                self.txtReadOnlyMaSP.setText(str(self.category_id))

            # Hiển thị Tên và Mô tả cũ
            self.cbDanhMuc.setCurrentText(data['ten'])
            self.cbTenSP.setCurrentText(data['mota'] if data['mota'] else "")

            self.btnLuu.clicked.connect(self.update_data)
            self.btnHuy.clicked.connect(self.reject)

    def update_data(self):
        # Lấy dữ liệu an toàn dựa trên loại giao diện đang dùng
        if hasattr(self, 'txtTenDanhMuc'):
            ten_dm = self.txtTenDanhMuc.text().strip()
            mo_ta = self.txtMoTaDanhMuc.text().strip()
        else:
            ten_dm = self.cbDanhMuc.currentText().strip()
            mo_ta = self.cbTenSP.currentText().strip()

        if not ten_dm:
            QtWidgets.QMessageBox.warning(self, "Lỗi", "Vui lòng nhập tên danh mục!")
            return

        db = DatabaseManager()
        conn = db.get_connection()
        if not conn:
            return

        try:
            cursor = conn.cursor()
            # Cập nhật vào DB theo Mã danh mục (kiểu int)
            cursor.execute("UPDATE CATEGORIES SET CATEGORYNAME = ?, DESCRIPTION = ? WHERE CATEGORYID = ?",
                           (ten_dm, mo_ta, self.category_id))
            conn.commit()

            QtWidgets.QMessageBox.information(self, "Thành công", "Cập nhật danh mục thành công!")
            self.accept()
        except Exception as e:
            conn.rollback()
            QtWidgets.QMessageBox.critical(self, "Lỗi", f"Lỗi hệ thống: {str(e)}")
        finally:
            conn.close()


# DIALOG XÓA DANH MỤC
class DeleteDanhMuc(QtWidgets.QDialog):
    def __init__(self, data):
        super().__init__()
        uic.loadUi(os.path.join(UI_PATH, "deleteDanhMuc.ui"), self) 
        
        self.category_id = data['id']
        self.category_name = data['ten']
        
        # Hiển thị thông báo lên giao diện
        self.lblCanhBao.setText(f"Bạn có chắc muốn xóa danh mục:\n{self.category_name}?")
        
        self.btnXoa.clicked.connect(self.delete_data)
        self.btnHuy.clicked.connect(self.reject)

    def delete_data(self):
        db = DatabaseManager()
        conn = db.get_connection()
        if not conn: return
        
        try:
            cursor = conn.cursor()
            
            # KIỂM TRA RÀNG BUỘC: Có sản phẩm nào thuộc danh mục này không?
            cursor.execute("SELECT COUNT(*) FROM PRODUCTS WHERE CATEGORYID = ?", (self.category_id,))
            if cursor.fetchone()[0] > 0:
                QtWidgets.QMessageBox.warning(self, "Cảnh báo", 
                    f"Không thể xóa '{self.category_name}' vì đang có sản phẩm thuộc danh mục này. Vui lòng xóa/chuyển các sản phẩm đó trước!")
                return
            
            # Nếu không vướng sản phẩm, tiến hành xóa
            cursor.execute("DELETE FROM CATEGORIES WHERE CATEGORYID = ?", (self.category_id,))
            conn.commit()
            
            QtWidgets.QMessageBox.information(self, "Thành công", "Xóa danh mục thành công!")
            self.accept()
        except Exception as e:
            conn.rollback()
            QtWidgets.QMessageBox.critical(self, "Lỗi", f"Lỗi hệ thống: {str(e)}")
        finally:
            conn.close()



# BỘ QUẢN LÝ (CONTROLLER CHO MAIN WINDOW)

# BỘ QUẢN LÝ (CONTROLLER CHO MAIN WINDOW)

class DanhMucManager:
    def __init__(self, table_widget, txt_search=None, btn_search=None):
        self.table = table_widget
        self.txt_search = txt_search

        # Cấu hình giao diện bảng
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode.Stretch)
        # Cột 4 là cột Thao tác, set kích thước cố định
        if self.table.columnCount() > 4:
            header.setSectionResizeMode(4, QtWidgets.QHeaderView.ResizeMode.Fixed)
            self.table.setColumnWidth(4, 140)

            # 3. KẾT NỐI SỰ KIỆN TÌM KIẾM THỜI GIAN THỰC (Đã sửa)
        if btn_search:
            btn_search.clicked.connect(self.load_data)
        if txt_search:
            # Thay vì returnPressed, dùng textChanged để bắt sự kiện gõ phím liên tục
            txt_search.textChanged.connect(self.load_data)

    def load_data(self):
        """Hàm nạp dữ liệu từ SQL và vẽ bảng, có hỗ trợ tìm kiếm"""
        db = DatabaseManager()
        conn = db.get_connection()
        if not conn: return

        # Lấy từ khóa tìm kiếm (nếu có)
        keyword = ""
        if hasattr(self, 'txt_search') and self.txt_search is not None:
            keyword = self.txt_search.text().strip()

        try:
            cursor = conn.cursor()

            # Câu lệnh SQL cơ bản
            query = """
                SELECT 
                    c.CATEGORYID, 
                    c.CATEGORYNAME, 
                    c.DESCRIPTION,
                    COUNT(p.PRODUCTID) as PRODUCT_COUNT
                FROM CATEGORIES c
                LEFT JOIN PRODUCTS p ON c.CATEGORYID = p.CATEGORYID
            """

            params = ()
            # Thêm điều kiện WHERE nếu người dùng có gõ từ khóa
            if keyword:
                query += " WHERE c.CATEGORYNAME LIKE ? OR c.CATEGORYID LIKE ?"
                # Tìm kiếm chứa từ khóa (có phân biệt hoặc không phân biệt tùy vào Collation của SQL Server)
                params = (f'%{keyword}%', f'%{keyword}%')

            query += " GROUP BY c.CATEGORYID, c.CATEGORYNAME, c.DESCRIPTION"

            cursor.execute(query, params)
            rows = cursor.fetchall()

            self.table.setRowCount(0)
            for row_idx, row_data in enumerate(rows):
                self.table.insertRow(row_idx)

                # Nạp dữ liệu vào bảng
                self.table.setItem(row_idx, 0, QtWidgets.QTableWidgetItem(str(row_data[0])))
                self.table.setItem(row_idx, 1, QtWidgets.QTableWidgetItem(row_data[1]))

                mota = row_data[2] if row_data[2] else ""
                self.table.setItem(row_idx, 2, QtWidgets.QTableWidgetItem(mota))
                self.table.setItem(row_idx, 3, QtWidgets.QTableWidgetItem(str(row_data[3])))

                # Tạo dictionary lưu thông tin để truyền sang các Dialog Sửa/Xóa
                item_dict = {"id": row_data[0], "ten": row_data[1], "mota": mota}
                self.add_buttons(row_idx, item_dict)

        except Exception as e:
            print(f"Lỗi khi load dữ liệu: {e}")
        finally:
            conn.close()

    def add_buttons(self, row, item):
        # ... (Giữ nguyên code phần này của bạn) ...
        container = QtWidgets.QWidget()
        layout = QtWidgets.QHBoxLayout(container)
        layout.setContentsMargins(5, 2, 5, 2)
        layout.setSpacing(10)

        btn_edit = QtWidgets.QPushButton("Sửa")
        btn_delete = QtWidgets.QPushButton("Xóa")

        style = "padding: 5px; font-weight: bold; min-width: 60px; border-radius: 3px;"
        btn_edit.setStyleSheet(f"background-color: #3b82f6; color: white; {style}")
        btn_delete.setStyleSheet(f"background-color: #ef4444; color: white; {style}")

        btn_edit.clicked.connect(lambda: self.open_edit(item))
        btn_delete.clicked.connect(lambda: self.open_delete(item))

        layout.addWidget(btn_edit)
        layout.addWidget(btn_delete)
        self.table.setCellWidget(row, 4, container)

    def open_add(self):
        # Truyền self.table.window() để form con nhận diện được cửa sổ gốc
        dialog = AddDanhMuc(self.table.window())
        if dialog.exec():
            self.load_data()

    def open_edit(self, item):
        # Truyền cửa sổ gốc vào để tránh crash
        dialog = EditDanhMuc(item, self.table.window())
        if dialog.exec():
            self.load_data()

    def open_delete(self, item):
        # ... (Giữ nguyên) ...
        dialog = DeleteDanhMuc(item)
        if dialog.exec():
            self.load_data()