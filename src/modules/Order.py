import os
from PyQt6 import uic, QtWidgets, QtCore
from src.database.db_connection import DatabaseManager
from datetime import datetime

# Thiết lập đường dẫn gốc
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(os.path.dirname(CURRENT_DIR))
UI_PATH = os.path.join(ROOT_DIR, "ui")

# --- LỚP TẠO ĐƠN HÀNG MỚI ---
class CreateOrder(QtWidgets.QDialog):
    def __init__(self):
        super().__init__()
        uic.loadUi(os.path.join(UI_PATH, "createDonHang.ui"), self)
        self.selected_products = [] 
        self.tblDanhSachSP.verticalHeader().setVisible(False)
        self.tblDanhSachSP.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode.Stretch)
        self.load_combobox_data()
        self.btnThem.clicked.connect(self.add_product_to_list)
        self.btnTaoDonHang.clicked.connect(self.submit_order)

    def load_combobox_data(self):
        db = DatabaseManager()
        conn = db.get_connection()
        if not conn: return
        cursor = conn.cursor()
        cursor.execute("SELECT CUSTOMER_ID, CUSTOMER_NAME FROM CUSTOMERS")
        self.cbKhachHang.clear()
        for cid, name in cursor.fetchall(): 
            self.cbKhachHang.addItem(f"{cid} - {name}", cid)
            
        cursor.execute("SELECT PRODUCT_ID, PRODUCT_NAME, UNIT_PRICE FROM PRODUCTS WHERE PRODUCT_STATUS = N'Còn hàng'")
        self.cbSanPham.clear()
        for pid, name, price in cursor.fetchall(): 
            self.cbSanPham.addItem(name, {"id": pid, "price": float(price)})
        conn.close()

    def add_product_to_list(self):
        product_name = self.cbSanPham.currentText()
        product_data = self.cbSanPham.currentData()
        quantity = self.spnSoLuong.value()
        if quantity <= 0: return

        for i, item in enumerate(self.selected_products):
            if item["id"] == product_data["id"]:
                item["qty"] += quantity
                item["total"] = item["qty"] * product_data["price"]
                self.tblDanhSachSP.setItem(i, 1, QtWidgets.QTableWidgetItem(str(item["qty"])))
                self.tblDanhSachSP.setItem(i, 2, QtWidgets.QTableWidgetItem(f"{item['total']:,.0f}"))
                self.update_summary()
                return

        total_item_price = product_data["price"] * quantity
        row = self.tblDanhSachSP.rowCount()
        self.tblDanhSachSP.insertRow(row)
        self.tblDanhSachSP.setItem(row, 0, QtWidgets.QTableWidgetItem(product_name))
        self.tblDanhSachSP.setItem(row, 1, QtWidgets.QTableWidgetItem(str(quantity)))
        self.tblDanhSachSP.setItem(row, 2, QtWidgets.QTableWidgetItem(f"{total_item_price:,.0f}"))
        
        self.selected_products.append({
            "id": product_data["id"], 
            "name": product_name, 
            "qty": quantity, 
            "price": product_data["price"], 
            "total": total_item_price
        })
        self.update_summary()

    def update_summary(self):
        total_items = sum(p['qty'] for p in self.selected_products)
        total_amount = sum(p['total'] for p in self.selected_products)
        self.lblHienThiSoMon.setText(str(total_items))
        self.lblHienThiSoTienTongCong.setText(f"{total_amount:,.0f} VNĐ")

    def submit_order(self):
        if not self.selected_products: return
        db = DatabaseManager()
        conn = db.get_connection()
        if not conn: return
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT MAX(ORDER_ID) FROM ORDERS")
            last_id = cursor.fetchone()[0]
            new_id = f"ORD{int(last_id.replace('ORD', '')) + 1:02d}" if last_id else "ORD01"
            
            cursor.execute("INSERT INTO ORDERS (ORDER_ID, CUSTOMER_ID, ORDER_DATE, ORDER_STATUS) VALUES (?, ?, ?, ?)", 
                           (new_id, self.cbKhachHang.currentData(), datetime.now().strftime('%Y-%m-%d'), "Đã thanh toán"))
            
            for p in self.selected_products:
                cursor.execute("INSERT INTO ORDERDETAILS (ORDER_ID, PRODUCT_ID, ORDER_QUANTITY) VALUES (?, ?, ?)", (new_id, p['id'], p['qty']))
            
            conn.commit()
            self.accept()
        except Exception as e: 
            conn.rollback()
            QtWidgets.QMessageBox.critical(self, "Lỗi", str(e))
        finally: 
            conn.close()

# --- LỚP CHỈNH SỬA ĐƠN HÀNG ---
class EditOrder(QtWidgets.QDialog):
    def __init__(self, order_id):
        super().__init__()
        uic.loadUi(os.path.join(UI_PATH, "editDonHang.ui"), self)
        self.order_id = order_id
        self.selected_products = []
        
        self.tblDanhSachSP.verticalHeader().setVisible(False)
        self.tblDanhSachSP.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode.Stretch)
        
        self.load_initial_data()
        self.btnThem.clicked.connect(self.add_product_to_list)
        self.btnSuaDonHang.clicked.connect(self.save_changes)

    def load_initial_data(self):
        db = DatabaseManager()
        conn = db.get_connection()
        if not conn: return
        cursor = conn.cursor()
        
        # 1. Nạp Combo Boxes
        cursor.execute("SELECT CUSTOMER_ID, CUSTOMER_NAME FROM CUSTOMERS")
        for cid, name in cursor.fetchall(): 
            self.cbKhachHang.addItem(f"{cid} - {name}", cid)
            
        cursor.execute("SELECT PRODUCT_ID, PRODUCT_NAME, UNIT_PRICE FROM PRODUCTS WHERE PRODUCT_STATUS = N'Còn hàng'")
        for pid, name, price in cursor.fetchall(): 
            self.cbSanPham.addItem(name, {"id": pid, "price": float(price)})
        
        # 2. Lấy Header đơn hàng cũ
        cursor.execute("SELECT CUSTOMER_ID FROM ORDERS WHERE ORDER_ID = ?", (self.order_id,))
        res = cursor.fetchone()
        if res: 
            self.cbKhachHang.setCurrentIndex(self.cbKhachHang.findData(res[0]))
        
        # 3. Lấy danh sách sản phẩm cũ
        cursor.execute("""
            SELECT P.PRODUCT_ID, P.PRODUCT_NAME, OD.ORDER_QUANTITY, P.UNIT_PRICE
            FROM ORDERDETAILS OD JOIN PRODUCTS P ON OD.PRODUCT_ID = P.PRODUCT_ID
            WHERE OD.ORDER_ID = ?
        """, (self.order_id,))
        
        for row in cursor.fetchall():
            pid, name, qty, price = row
            total = qty * float(price)
            self.selected_products.append({
                "id": pid, "name": name, "qty": qty, "price": float(price), "total": total
            })
            
        self.refresh_table()
        conn.close()

    def refresh_table(self):
        self.tblDanhSachSP.setRowCount(0)
        for row_idx, p in enumerate(self.selected_products):
            self.tblDanhSachSP.insertRow(row_idx)
            self.tblDanhSachSP.setItem(row_idx, 0, QtWidgets.QTableWidgetItem(p["name"]))
            self.tblDanhSachSP.setItem(row_idx, 1, QtWidgets.QTableWidgetItem(str(p["qty"])))
            self.tblDanhSachSP.setItem(row_idx, 2, QtWidgets.QTableWidgetItem(f"{p['total']:,.0f}"))
        self.update_summary()

    def add_product_to_list(self):
        name = self.cbSanPham.currentText()
        data = self.cbSanPham.currentData()
        qty = self.spnSoLuong.value()
        if qty <= 0: return
        
        for item in self.selected_products:
            if item["id"] == data["id"]:
                item["qty"] += qty
                item["total"] = item["qty"] * data["price"]
                self.refresh_table()
                return
                
        self.selected_products.append({
            "id": data["id"], "name": name, "qty": qty, "price": data["price"], "total": qty * data["price"]
        })
        self.refresh_table()

    def update_summary(self):
        total_items = sum(p['qty'] for p in self.selected_products)
        total_amount = sum(p['total'] for p in self.selected_products)
        self.lblHienThiSoMon.setText(str(total_items))
        self.lblHienThiSoTienTongCong.setText(f"{total_amount:,.0f} VNĐ")

    def save_changes(self):
        if not self.selected_products: return
        db = DatabaseManager()
        conn = db.get_connection()
        if not conn: return
        try:
            cursor = conn.cursor()
            # Cập nhật khách hàng
            cursor.execute("UPDATE ORDERS SET CUSTOMER_ID = ? WHERE ORDER_ID = ?", (self.cbKhachHang.currentData(), self.order_id))
            # Xóa chi tiết cũ và chèn lại
            cursor.execute("DELETE FROM ORDERDETAILS WHERE ORDER_ID = ?", (self.order_id,))
            for p in self.selected_products:
                cursor.execute("INSERT INTO ORDERDETAILS (ORDER_ID, PRODUCT_ID, ORDER_QUANTITY) VALUES (?, ?, ?)", (self.order_id, p['id'], p['qty']))
            conn.commit()
            self.accept()
        except Exception as e: 
            conn.rollback()
            QtWidgets.QMessageBox.critical(self, "Lỗi", str(e))
        finally: 
            conn.close()

# --- LỚP XEM CHI TIẾT ---
class ViewOrder(QtWidgets.QDialog):
    def __init__(self, order_data):
        super().__init__()
        uic.loadUi(os.path.join(UI_PATH, "viewDonHang.ui"), self)
        self.order_id = order_data['id'] 
        self.tblDanhSachSP.verticalHeader().setVisible(False)
        self.tblDanhSachSP.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode.Stretch)
        self.load_order_details()

    def load_order_details(self):
        db = DatabaseManager(); conn = db.get_connection()
        if not conn: return
        cursor = conn.cursor()
        
        # 1. Lấy danh sách sản phẩm trước để tính tổng số món
        cursor.execute("""
            SELECT P.PRODUCT_NAME, OD.ORDER_QUANTITY, P.UNIT_PRICE, (OD.ORDER_QUANTITY * P.UNIT_PRICE) 
            FROM ORDERDETAILS OD JOIN PRODUCTS P ON OD.PRODUCT_ID = P.PRODUCT_ID 
            WHERE OD.ORDER_ID = ?
        """, (self.order_id,))
        rows = cursor.fetchall()
        
        total_a = 0; total_q = 0
        for r in rows:
            total_q += r[1]; total_a += r[3]

        # 2. Lấy Header và hiển thị số món ngay tại khúc này
        cursor.execute("SELECT O.ORDER_ID, C.CUSTOMER_NAME FROM ORDERS O JOIN CUSTOMERS C ON O.CUSTOMER_ID = C.CUSTOMER_ID WHERE O.ORDER_ID = ?", (self.order_id,))
        header = cursor.fetchone()
        if header: 
            self.lblSoMon.setText(f"Đơn hàng: {header[0]} ({total_q} món)")
            self.lblHienThiKH.setText(header[1])
            
        # 3. Đổ dữ liệu vào bảng
        self.tblDanhSachSP.setRowCount(0)
        for i, r in enumerate(rows):
            self.tblDanhSachSP.insertRow(i)
            self.tblDanhSachSP.setItem(i, 0, QtWidgets.QTableWidgetItem(r[0]))
            self.tblDanhSachSP.setItem(i, 1, QtWidgets.QTableWidgetItem(str(r[1])))
            self.tblDanhSachSP.setItem(i, 2, QtWidgets.QTableWidgetItem(f"{r[2]:,.0f}"))
            self.tblDanhSachSP.setItem(i, 3, QtWidgets.QTableWidgetItem(f"{r[3]:,.0f}"))
            
        # 4. Cập nhật các nhãn tóm tắt bên dưới
        self.lblHienThiSoMon.setText(str(total_q))
        self.lblHienThiTongCong.setText(f"{total_a:,.0f} VNĐ")
        conn.close()

# --- LỚP XÓA ---
class DeleteOrder(QtWidgets.QDialog):
    def __init__(self, order_id):
        super().__init__()
        uic.loadUi(os.path.join(UI_PATH, "deleteDonHang.ui"), self)
        self.order_id = order_id
        self.lblCanhBao.setText(f"Bạn có chắc muốn xóa đơn hàng {self.order_id}?\nHành động này không thể hoàn tác.")
        self.btnXoa.clicked.connect(self.confirm_delete)
        self.btnHuy.clicked.connect(self.reject)

    def confirm_delete(self):
        db = DatabaseManager()
        conn = db.get_connection()
        if not conn: return
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM INVOICES WHERE ORDER_ID = ?", (self.order_id,))
            if cursor.fetchone()[0] > 0:
                QtWidgets.QMessageBox.warning(self, "Lỗi", "Đơn hàng đã xuất hóa đơn, không thể xóa!")
                return
            cursor.execute("DELETE FROM ORDERDETAILS WHERE ORDER_ID = ?", (self.order_id,))
            cursor.execute("DELETE FROM ORDERS WHERE ORDER_ID = ?", (self.order_id,))
            conn.commit()
            self.accept()
        except Exception as e: 
            conn.rollback()
            QtWidgets.QMessageBox.critical(self, "Lỗi", str(e))
        finally: 
            conn.close()

# --- BỘ QUẢN LÝ ĐƠN HÀNG (CONTROLLER CÓ PHÂN TRANG) ---
class OrderManager:
    def __init__(self, table_widget, btn_prev, btn_next, lbl_status):
        self.table = table_widget
        self.btn_prev = btn_prev
        self.btn_next = btn_next
        self.lbl_status = lbl_status
        
        # Cấu hình phân trang (5 đơn hàng mỗi trang)
        self.current_page = 0
        self.items_per_page = 5
        self.all_data = []

        self.init_table_ui()
        self.connect_events()

    def init_table_ui(self):
        """Cấu hình giao diện bảng hiển thị"""
        self.table.verticalHeader().setVisible(False)
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode.Stretch)
        # Cột Thao tác (Cột 5) đặt độ rộng cố định
        header.setSectionResizeMode(5, QtWidgets.QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(5, 220) 
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows)

    def connect_events(self):
        """Kết nối sự kiện cho các nút điều hướng Trước/Sau"""
        # Ngắt các kết nối cũ trước khi gán mới
        try: self.btn_prev.clicked.disconnect()
        except: pass
        try: self.btn_next.clicked.disconnect()
        except: pass

        self.btn_prev.clicked.connect(self.prev_page)
        self.btn_next.clicked.connect(self.next_page)

    def load_data(self):
        """Tải toàn bộ dữ liệu đơn hàng và reset về trang đầu"""
        db = DatabaseManager()
        conn = db.get_connection()
        if not conn: return
        
        try:
            cursor = conn.cursor()
            # Truy vấn đầy đủ thông tin đơn hàng và tổng tiền
            query = """
                SELECT O.ORDER_ID, O.CUSTOMER_ID, O.ORDER_DATE, O.ORDER_STATUS, 
                       SUM(OD.ORDER_QUANTITY * P.UNIT_PRICE)
                FROM ORDERS O 
                LEFT JOIN ORDERDETAILS OD ON O.ORDER_ID = OD.ORDER_ID
                LEFT JOIN PRODUCTS P ON OD.PRODUCT_ID = P.PRODUCT_ID
                GROUP BY O.ORDER_ID, O.CUSTOMER_ID, O.ORDER_DATE, O.ORDER_STATUS
                ORDER BY O.ORDER_ID DESC
            """
            cursor.execute(query)
            self.all_data = cursor.fetchall()
            
            # Reset về trang 0 và vẽ trang
            self.current_page = 0
            self.render_page()
            
        except Exception as e:
            print(f"Lỗi load dữ liệu Đơn hàng: {e}")
        finally:
            conn.close()

    def render_page(self):
        """Hiển thị 5 dòng dữ liệu dựa trên trang hiện tại"""
        if not self.table: return
        
        self.table.setRowCount(0)
        total_items = len(self.all_data)
        
        # Tính toán chỉ số bắt đầu và kết thúc của trang
        start_idx = self.current_page * self.items_per_page
        end_idx = start_idx + self.items_per_page
        page_data = self.all_data[start_idx:end_idx]
        
        for i, row in enumerate(page_data):
            self.table.insertRow(i)
            # Cột 0: Mã Đơn
            self.table.setItem(i, 0, QtWidgets.QTableWidgetItem(str(row[0])))
            # Cột 1: Mã Khách Hàng
            self.table.setItem(i, 1, QtWidgets.QTableWidgetItem(str(row[1])))
            # Cột 2: Ngày Đặt
            self.table.setItem(i, 2, QtWidgets.QTableWidgetItem(str(row[2])))
            # Cột 3: Tổng Tiền
            total_val = row[4] if row[4] else 0
            self.table.setItem(i, 3, QtWidgets.QTableWidgetItem(f"{total_val:,.0f}"))
            # Cột 4: Trạng Thái
            self.table.setItem(i, 4, QtWidgets.QTableWidgetItem(str(row[3])))
            
            # Nút Thao tác
            self.add_action_buttons(i, {"id": row[0]})
            
        # Cập nhật Label trạng thái (Ví dụ: Hiển thị 5 / 20 đơn hàng)
        if self.lbl_status:
            count_on_page = len(page_data)
            self.lbl_status.setText(f"Hiển thị {count_on_page} / {total_items} đơn hàng")
        
        # Bật/Tắt nút điều hướng
        self.btn_prev.setEnabled(self.current_page > 0)
        self.btn_next.setEnabled(end_idx < total_items)

    def add_action_buttons(self, row, item):
        """Tạo cụm nút thao tác Xem - Sửa - Xóa cho mỗi hàng"""
        container = QtWidgets.QWidget()
        layout = QtWidgets.QHBoxLayout(container)
        layout.setContentsMargins(4, 2, 4, 2)
        layout.setSpacing(8)
        style = "padding: 4px; font-weight: bold; min-width: 50px; border-radius: 3px; color: white; border: none;"

        btn_view = QtWidgets.QPushButton("Xem")
        btn_view.setStyleSheet(f"background-color: #10b981; {style}")
        btn_view.clicked.connect(lambda: self.open_view(item))

        btn_edit = QtWidgets.QPushButton("Sửa")
        btn_edit.setStyleSheet(f"background-color: #3b82f6; {style}")
        btn_edit.clicked.connect(lambda: self.open_edit(item))

        btn_delete = QtWidgets.QPushButton("Xóa")
        btn_delete.setStyleSheet(f"background-color: #ef4444; {style}")
        btn_delete.clicked.connect(lambda: self.open_delete(item))

        layout.addWidget(btn_view)
        layout.addWidget(btn_edit)
        layout.addWidget(btn_delete)
        self.table.setCellWidget(row, 5, container)

    def next_page(self):
        """Chuyển sang trang sau"""
        if (self.current_page + 1) * self.items_per_page < len(self.all_data):
            self.current_page += 1
            self.render_page()

    def prev_page(self):
        """Quay lại trang trước"""
        if self.current_page > 0:
            self.current_page -= 1
            self.render_page()

    def open_create(self):
        if CreateOrder().exec(): self.load_data()

    def open_view(self, item):
        ViewOrder(item).exec()

    def open_edit(self, item):
        if EditOrder(item['id']).exec(): self.load_data()

    def open_delete(self, item):
        if DeleteOrder(item['id']).exec(): self.load_data()