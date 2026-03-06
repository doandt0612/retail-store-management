import os
from PyQt6 import uic, QtWidgets, QtCore
import pyodbc
from src.database.db_connection import DatabaseManager
from datetime import datetime

# Thiết lập đường dẫn gốc để nạp các file .ui
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(os.path.dirname(CURRENT_DIR))
UI_PATH = os.path.join(ROOT_DIR, "ui")

# LỚP TẠO ĐƠN HÀNG MỚI 
class CreateOrder(QtWidgets.QDialog):
    def __init__(self):
        super().__init__()
        uic.loadUi(os.path.join(UI_PATH, "createDonHang.ui"), self)
        
        self.selected_products = [] 
        

        self.tblDanhSachSP.verticalHeader().setVisible(False)
        self.tblDanhSachSP.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode.Stretch)

        # Nạp dữ liệu từ DB ngay khi mở Dialog 
        self.load_combobox_data()

        # Nút kết nối sự kiện
        self.btnThem.clicked.connect(self.add_product_to_list)
        self.btnTaoDonHang.clicked.connect(self.submit_order)

    def load_combobox_data(self):
        """Hàm nạp khách hàng và sản phẩm từ SQL Server"""
        db = DatabaseManager()
        conn = db.get_connection()
        if not conn: 
            return
        
        cursor = conn.cursor()
        
        # Nạp Khách hàng (Hiển thị tên, lưu ID vào userData)
        cursor.execute("SELECT CUSTOMER_ID, CUSTOMER_NAME FROM CUSTOMERS")
        self.cbKhachHang.clear()
        for cid, name in cursor.fetchall():
            self.cbKhachHang.addItem(name, cid)

        # Nạp Sản phẩm (Hiển thị tên, lưu ID và Giá vào userData)
        cursor.execute("SELECT PRODUCT_ID, PRODUCT_NAME, UNIT_PRICE FROM PRODUCTS WHERE PRODUCT_STATUS = N'Còn hàng'")
        self.cbSanPham.clear()
        for pid, name, price in cursor.fetchall():
            # Lưu cả ID và Giá vào một dictionary để dùng sau
            self.cbSanPham.addItem(name, {"id": pid, "price": float(price)})
        
        conn.close()

    def add_product_to_list(self):
        """CẬP NHẬT: Lấy giá thật từ ComboBox thay vì giá giả lập"""
        product_name = self.cbSanPham.currentText()
        product_data = self.cbSanPham.currentData() # Lấy {"id":..., "price":...}
        quantity = self.spnSoLuong.value()
        
        if quantity <= 0:
            QtWidgets.QMessageBox.warning(self, "Lỗi", "Số lượng phải lớn hơn 0")
            return


        # KIỂM TRA XEM SẢN PHẨM ĐÃ CÓ TRONG DANH SÁCH CHƯA
        for i, item in enumerate(self.selected_products):
            if item["id"] == product_data["id"]:
                # Nếu đã có, cộng dồn số lượng
                new_qty = item["qty"] + quantity
                new_total = new_qty * product_data["price"]
                
                # Cập nhật dữ liệu trong mảng tạm
                self.selected_products[i]["qty"] = new_qty
                self.selected_products[i]["price"] = new_total
                
                # Cập nhật hiển thị lên QTableWidget
                self.tblDanhSachSP.setItem(i, 1, QtWidgets.QTableWidgetItem(str(new_qty)))
                self.tblDanhSachSP.setItem(i, 2, QtWidgets.QTableWidgetItem(f"{new_total:,.0f}"))
                
                self.update_summary()
                return # Thoát hàm, không thêm dòng mới nữa

        # NẾU CHƯA CÓ, THÌ MỚI THÊM DÒNG MỚI
        price = product_data["price"]
        total_item_price = price * quantity

        row = self.tblDanhSachSP.rowCount()
        self.tblDanhSachSP.insertRow(row)
        self.tblDanhSachSP.setItem(row, 0, QtWidgets.QTableWidgetItem(product_name))
        self.tblDanhSachSP.setItem(row, 1, QtWidgets.QTableWidgetItem(str(quantity)))
        self.tblDanhSachSP.setItem(row, 2, QtWidgets.QTableWidgetItem(f"{total_item_price:,.0f}"))

        self.selected_products.append({
            "id": product_data["id"], 
            "name": product_name, 
            "qty": quantity, 
            "price": total_item_price
        })
        self.update_summary()

    def update_summary(self):
        """GIỮ NGUYÊN: Cập nhật phần Tóm tắt đơn hàng"""
        total_items = sum(p['qty'] for p in self.selected_products)
        total_amount = sum(p['price'] for p in self.selected_products)
        self.lblHienThiSoMon.setText(str(total_items))
        self.lblHienThiSoTienTongCong.setText(f"{total_amount:,.0f} VNĐ")

    def submit_order(self):
        """Xác nhận Tạo đơn và lưu vào Database theo cơ chế Transaction"""
        if not self.selected_products:
            QtWidgets.QMessageBox.warning(self, "Lỗi", "Vui lòng chọn ít nhất 1 sản phẩm")
            return
            
        db = DatabaseManager()
        conn = db.get_connection()
        if not conn: 
            return
        
        try:
            cursor = conn.cursor()
            
            # TỰ ĐỘNG TẠO MÃ ĐƠN HÀNG (VD: ORD11)
            cursor.execute("SELECT MAX(ORDER_ID) FROM ORDERS")
            last_id = cursor.fetchone()[0]
            if not last_id:
                new_id = "ORD01"
            else:
                # Tách phần số sau chữ 'ORD', tăng 1, và định dạng lại 2 chữ số
                current_num = int(last_id.replace("ORD", ""))
                new_id = f"ORD{current_num + 1:02d}"
            
            # CHUẨN BỊ DỮ LIỆU CHUNG
            customer_id = self.cbKhachHang.currentData() # Lấy ID ẩn trong ComboBox
            order_date = datetime.now().strftime('%Y-%m-%d')
            status = "Đã thanh toán" # Giá trị hợp lệ theo ràng buộc CHK_Order_Status

            # LƯU VÀO BẢNG ORDERS
            cursor.execute("""
                INSERT INTO ORDERS (ORDER_ID, CUSTOMER_ID, ORDER_DATE, ORDER_STATUS)
                VALUES (?, ?, ?, ?)
            """, (new_id, customer_id, order_date, status))

            # LƯU VÀO BẢNG ORDERDETAILS
            for p in self.selected_products:
                cursor.execute("""
                    INSERT INTO ORDERDETAILS (ORDER_ID, PRODUCT_ID, ORDER_QUANTITY)
                    VALUES (?, ?, ?)
                """, (new_id, p['id'], p['qty']))

            # XÁC NHẬN LƯU THAY ĐỔI
            conn.commit()
            QtWidgets.QMessageBox.information(self, "Thành công", f"Đã tạo đơn hàng {new_id} thành công!")
            self.accept() # Đóng Dialog và báo cho OrderManager biết để load lại bảng

        except Exception as e:
            conn.rollback() # QUAN TRỌNG: Hủy bỏ mọi thay đổi nếu có bất kỳ lỗi nào xảy ra
            QtWidgets.QMessageBox.critical(self, "Lỗi hệ thống", f"Không thể lưu đơn hàng: {str(e)}")
        finally:
            conn.close()



# LỚP XEM CHI TIẾT ĐƠN HÀNG

class ViewOrder(QtWidgets.QDialog):
    def __init__(self, order_data):
        super().__init__()
        uic.loadUi(os.path.join(UI_PATH, "viewDonHang.ui"), self)
        
        # Lấy ID đơn hàng từ dictionary truyền vào
        self.order_id = order_data['id'] 
        
        # Cấu hình bảng hiển thị sản phẩm
        self.tblDanhSachSP.verticalHeader().setVisible(False)
        self.tblDanhSachSP.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode.Stretch)
        
        # Nạp dữ liệu từ SQL Server
        self.load_order_details()

    def load_order_details(self):
        """Truy vấn thông tin chi tiết đơn hàng từ Database"""
        db = DatabaseManager()
        conn = db.get_connection()
        if not conn: return
        
        cursor = conn.cursor()
        
        # Lấy thông tin chung (Header): Mã đơn, Tên khách, Ngày đặt, Trạng thái
        query_header = """
            SELECT O.ORDER_ID, C.CUSTOMER_NAME, O.ORDER_DATE, O.ORDER_STATUS
            FROM ORDERS O
            JOIN CUSTOMERS C ON O.CUSTOMER_ID = C.CUSTOMER_ID
            WHERE O.ORDER_ID = ?
        """
        cursor.execute(query_header, (self.order_id,))
        header_data = cursor.fetchone()
        
        if header_data:
            self.lblMaDon.setText(f"Đơn hàng: {header_data[0]}")
            self.lblHienThiKH.setText(header_data[1])

        # Lấy danh sách sản phẩm trong đơn (Line Items)
        query_details = """
            SELECT P.PRODUCT_NAME, OD.ORDER_QUANTITY, P.UNIT_PRICE, 
                   (OD.ORDER_QUANTITY * P.UNIT_PRICE) AS SUBTOTAL
            FROM ORDERDETAILS OD
            JOIN PRODUCTS P ON OD.PRODUCT_ID = P.PRODUCT_ID
            WHERE OD.ORDER_ID = ?
        """
        cursor.execute(query_details, (self.order_id,))
        rows = cursor.fetchall()

        self.tblDanhSachSP.setRowCount(0)
        total_amount = 0
        total_items = 0

        for row_idx, row_data in enumerate(rows):
            self.tblDanhSachSP.insertRow(row_idx)
            # Cột 0: Tên sản phẩm
            self.tblDanhSachSP.setItem(row_idx, 0, QtWidgets.QTableWidgetItem(row_data[0])) 
            # Cột 1: Số lượng
            self.tblDanhSachSP.setItem(row_idx, 1, QtWidgets.QTableWidgetItem(str(row_data[1]))) 
            # Cột 2: Giá (Định dạng tiền tệ)
            self.tblDanhSachSP.setItem(row_idx, 2, QtWidgets.QTableWidgetItem(f"{row_data[2]:,.0f}")) 
            # Cột 3: Thành tiền
            self.tblDanhSachSP.setItem(row_idx, 3, QtWidgets.QTableWidgetItem(f"{row_data[3]:,.0f}")) 

            total_items += row_data[1]
            total_amount += row_data[3]

        # Cập nhật phần tóm tắt tổng số tiền
        self.lblHienThiSoMon.setText(str(total_items))
        self.lblHienThiTongCong.setText(f"{total_amount:,.0f} VNĐ")

        conn.close()
        

# LỚP XÁC NHẬN XÓA ĐƠN HÀNG
class DeleteOrder(QtWidgets.QDialog):
    def __init__(self, order_id):
        super().__init__()
        uic.loadUi(os.path.join(UI_PATH, "deleteDonHang.ui"), self)
        self.order_id = order_id
        
        # Hiển thị thông báo xác nhận
        self.lblCanhBao.setText(f"Bạn có chắc muốn xóa đơn hàng {self.order_id}?\nHành động này không thể hoàn tác.")
        
        # Kết nối nút bấm
        self.btnXoa.clicked.connect(self.confirm_delete)
        self.btnHuy.clicked.connect(self.reject)

    def confirm_delete(self):
        """Logic xóa đơn hàng trực tiếp với cơ chế Transaction"""
        db = DatabaseManager()
        conn = db.get_connection()
        if not conn: 
            return
        
        try:
            cursor = conn.cursor()
            
            # 1. Kiểm tra ràng buộc Hóa đơn (INVOICES)
            # INVOICES có khóa ngoại tham chiếu tới ORDERS
            cursor.execute("SELECT COUNT(*) FROM INVOICES WHERE ORDER_ID = ?", (self.order_id,))
            if cursor.fetchone()[0] > 0:
                QtWidgets.QMessageBox.warning(self, "Không thể xóa", 
                                              "Đơn hàng này đã được xuất hóa đơn!")
                return

            # 2. Xóa dữ liệu trong bảng ORDERDETAILS trước (Ràng buộc FK)
            cursor.execute("DELETE FROM ORDERDETAILS WHERE ORDER_ID = ?", (self.order_id,))
            
            # 3. Xóa dữ liệu trong bảng ORDERS
            cursor.execute("DELETE FROM ORDERS WHERE ORDER_ID = ?", (self.order_id,))
            
            conn.commit()
            QtWidgets.QMessageBox.information(self, "Thành công", f"Đã xóa đơn hàng {self.order_id} thành công!")
            self.accept() # Đóng dialog và báo thành công cho OrderManager
            
        except Exception as e:
            conn.rollback()
            QtWidgets.QMessageBox.critical(self, "Lỗi hệ thống", f"Không thể xóa đơn hàng: {str(e)}")
        finally:
            conn.close()

# BỘ QUẢN LÝ ĐƠN HÀNG (CONTROLLER)
class OrderManager:
    def __init__(self, table_widget):
        self.table = table_widget
        self.init_table_ui()

    def init_table_ui(self):
        """Cấu hình giao diện bảng để không bị che chữ và mất nét"""
        self.table.verticalHeader().setVisible(False)
        header = self.table.horizontalHeader()
        
        header.setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeMode.ResizeToContents) # Mã đơn
        header.setSectionResizeMode(2, QtWidgets.QHeaderView.ResizeMode.ResizeToContents) # Ngày
        header.setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeMode.Stretch)          # Khách hàng
        
        header.setSectionResizeMode(5, QtWidgets.QHeaderView.ResizeMode.Fixed)           # Thao tác
        self.table.setColumnWidth(6, 170) 
        header.setDefaultAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)

        # Áp dụng Stylesheet 
        self.table.setStyleSheet("""
            QTableWidget {
                gridline-color: #e5e7eb;
                selection-background-color: #dbeafe;
                selection-color: #1e40af;
                alternate-background-color: #f9fafb;
            }
            QHeaderView::section {
                background-color: #f8fafc;
                padding: 5px;
                font-weight: bold;
                font-size: 13px;
                border-bottom: 2px solid #e2e8f0;
            }
        """)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows)


    def load_data(self):
        db = DatabaseManager()
        conn = db.get_connection()
        if not conn: return

        cursor = conn.cursor()
        query = """
            SELECT O.ORDER_ID, C.CUSTOMER_NAME, O.ORDER_DATE, O.ORDER_STATUS, 
                SUM(OD.ORDER_QUANTITY * P.UNIT_PRICE)
            FROM ORDERS O
            JOIN CUSTOMERS C ON O.CUSTOMER_ID = C.CUSTOMER_ID
            LEFT JOIN ORDERDETAILS OD ON O.ORDER_ID = OD.ORDER_ID
            LEFT JOIN PRODUCTS P ON OD.PRODUCT_ID = P.PRODUCT_ID
            GROUP BY O.ORDER_ID, C.CUSTOMER_NAME, O.ORDER_DATE, O.ORDER_STATUS
        """
        
        cursor.execute(query)
        rows = cursor.fetchall()

        self.table.setRowCount(0)
        for row_idx, row_data in enumerate(rows):
            self.table.insertRow(row_idx)
            # Nạp dữ liệu vào từng cột
            self.table.setItem(row_idx, 0, QtWidgets.QTableWidgetItem(str(row_data[0]))) # ID
            self.table.setItem(row_idx, 1, QtWidgets.QTableWidgetItem(row_data[1]))      # Tên khách
            self.table.setItem(row_idx, 2, QtWidgets.QTableWidgetItem(str(row_data[2]))) # Ngày
            
            # Định dạng tiền tệ: 1,200,000 VNĐ
            total = row_data[4] if row_data[4] else 0
            self.table.setItem(row_idx, 3, QtWidgets.QTableWidgetItem(f"{total:,.0f}")) 
            
            self.table.setItem(row_idx, 4, QtWidgets.QTableWidgetItem(row_data[3]))      # Trạng thái
            
            # Thêm nút bấm thao tác (đã có trong code của bạn)
            item_dict = {"id": row_data[0], "khach": row_data[1]}
            self.add_action_buttons(row_idx, item_dict)

        conn.close()

    def add_action_buttons(self, row, item):
        container = QtWidgets.QWidget()
        layout = QtWidgets.QHBoxLayout(container)
        layout.setContentsMargins(4, 2, 4, 2)
        layout.setSpacing(10)

        style = "padding: 5px; font-weight: bold; min-width: 60px; border-radius: 3px;"

        btn_view = QtWidgets.QPushButton("Xem")
        btn_view.setStyleSheet(f"background-color: #10b981; color: white; {style}")
        btn_view.clicked.connect(lambda: self.open_view(item))

        btn_delete = QtWidgets.QPushButton("Xóa")
        btn_delete.setStyleSheet(f"background-color: #ef4444; color: white; {style}")
        btn_delete.clicked.connect(lambda: self.open_delete(item))

        layout.addWidget(btn_view)
        layout.addWidget(btn_delete)
        self.table.setCellWidget(row, 5, container)

    def open_create(self):
        dialog = CreateOrder()
        print("Đang thêm dữ liệu đơn hàng mới vào Database...")
        if dialog.exec():
            self.load_data() 

    def open_view(self, item):
        dialog = ViewOrder(item)
        dialog.exec()

    def open_delete(self, item):
        dialog = DeleteOrder(item['id'])
        if dialog.exec():
            print(f"Đã xóa đơn hàng: {item['id']}")
            self.load_data()