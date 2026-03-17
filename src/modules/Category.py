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
    def __init__(self):
        super().__init__()
        uic.loadUi(os.path.join(UI_PATH, "addDanhMuc.ui"), self)
        
        # Kết nối nút bấm với hàm xử lý SQL
        self.btnLuu.clicked.connect(self.save_data)
        self.btnHuy.clicked.connect(self.reject)

    def save_data(self):
        # Lấy dữ liệu từ giao diện (Giả định bạn đặt tên ô nhập là txtTen và txtMoTa)
        ten_dm = self.txtTenDanhMuc.text().strip()
        mo_ta = self.txtMoTaDanhMuc.text().strip()
        
        if not ten_dm:
            QtWidgets.QMessageBox.warning(self, "Lỗi", "Vui lòng nhập tên danh mục!")
            return
            
        db = DatabaseManager()
        conn = db.get_connection()
        if not conn: 
            return
        
        try:
            cursor = conn.cursor()
            
            # Tự động tạo mã danh mục (VD: CAT11)
            cursor.execute("SELECT MAX(CATEGORYID) FROM CATEGORIES")
            last_id = cursor.fetchone()[0]
            if not last_id:
                new_id = "CAT01"
            else:
                current_num = int(last_id.replace("CAT", ""))
                new_id = f"CAT{current_num + 1:02d}"
            
            # Thêm vào DB
            cursor.execute("INSERT INTO CATEGORIES (CATEGORYID, CATEGORYNAME, DESCRIPTION) VALUES (?, ?, ?)", 
                           (new_id, ten_dm, mo_ta))
            conn.commit()
            
            QtWidgets.QMessageBox.information(self, "Thành công", "Thêm danh mục thành công!")
            self.accept() 
        except Exception as e:
            conn.rollback()
            QtWidgets.QMessageBox.critical(self, "Lỗi", f"Lỗi hệ thống: {str(e)}")
        finally:
            conn.close()


#  DIALOG SỬA DANH MỤC 
class EditDanhMuc(QtWidgets.QDialog):
    def __init__(self, data):
        super().__init__()
        uic.loadUi(os.path.join(UI_PATH, "editDanhMuc.ui"), self) 
        
        self.category_id = data['id']
        
        # Điền dữ liệu cũ lên giao diện
        self.txtTenDanhMuc.setText(data['ten'])
        self.txtMoTaDanhMuc.setText(data['mota'] if data['mota'] else "")
        
        self.btnLuu.clicked.connect(self.update_data)
        self.btnHuy.clicked.connect(self.reject)

    def update_data(self):
        ten_dm = self.txtTenDanhMuc.text().strip()
        mo_ta = self.txtMoTaDanhMuc.text().strip()
        
        if not ten_dm:
            QtWidgets.QMessageBox.warning(self, "Lỗi", "Vui lòng nhập tên danh mục!")
            return
            
        db = DatabaseManager()
        conn = db.get_connection()
        if not conn: 
            return
        
        try:
            cursor = conn.cursor()
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

class DanhMucManager:
    # 1. Thêm txt_search=None, btn_search=None vào đây
    def __init__(self, table_widget, txt_search=None, btn_search=None):
        self.table = table_widget
        self.txt_search = txt_search # 2. Lưu lại biến tìm kiếm
        
        # Cấu hình giao diện bảng (giữ nguyên code cũ của bạn)
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode.Stretch)
        # Cột 4 là cột Thao tác, set kích thước cố định
        if self.table.columnCount() > 4:
            header.setSectionResizeMode(4, QtWidgets.QHeaderView.ResizeMode.Fixed)
            self.table.setColumnWidth(4, 140) 
        
        # 3. Kết nối sự kiện tìm kiếm (MỚI THÊM VÀO)
        if btn_search and txt_search:
            btn_search.clicked.connect(self.load_data)
            txt_search.returnPressed.connect(self.load_data)

    def load_data(self):
        """Hàm nạp dữ liệu từ SQL và vẽ bảng"""
        db = DatabaseManager()
        conn = db.get_connection()
        if not conn: return
        
        cursor = conn.cursor()
        cursor.execute("""
                        SELECT 
                            c.CATEGORYID, 
                            c.CATEGORYNAME, 
                            c.DESCRIPTION,
                            COUNT(p.PRODUCTID) as PRODUCT_COUNT
                        FROM CATEGORIES c
                        LEFT JOIN PRODUCTS p ON c.CATEGORYID = p.CATEGORYID
                        GROUP BY c.CATEGORYID, c.CATEGORYNAME, c.DESCRIPTION
                    """)
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
            
        conn.close()

    def add_buttons(self, row, item):
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
        dialog = AddDanhMuc()
        if dialog.exec():
            self.load_data() 

    def open_edit(self, item):
        dialog = EditDanhMuc(item)
        if dialog.exec():
            self.load_data()

    def open_delete(self, item):
        # Truyền toàn bộ biến 'item'
        dialog = DeleteDanhMuc(item)
        if dialog.exec():
            self.load_data()