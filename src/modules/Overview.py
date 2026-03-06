import os
from PyQt6 import uic, QtWidgets
from src.database.db_connection import DatabaseManager


CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(os.path.dirname(CURRENT_DIR))
UI_PATH = os.path.join(ROOT_DIR, "ui")

# Lớp hiển thị chi tiết đơn hàng 
class OrderDetails(QtWidgets.QDialog):
    def __init__(self, order_data):
        super().__init__()
        uic.loadUi(os.path.join(UI_PATH, "viewTongQuan.ui"), self)
        
        # Lấy ID đơn hàng từ dictionary truyền vào
        self.order_id = order_data['id'] 
        
        # Cấu hình bảng hiển thị sản phẩm
        self.tblDanhSachSP.verticalHeader().setVisible(False)
        self.tblDanhSachSP.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode.Stretch)
        
        # Gọi hàm nạp dữ liệu SQL
        self.load_order_details()

    def load_order_details(self):
        """Truy vấn thông tin chi tiết đơn hàng từ Database"""
        db = DatabaseManager()
        conn = db.get_connection()
        if not conn: 
            return
        
        cursor = conn.cursor()
        
        # Lấy thông tin chung: Mã đơn, Tên khách
        query_header = """
            SELECT O.ORDER_ID, C.CUSTOMER_NAME
            FROM ORDERS O
            JOIN CUSTOMERS C ON O.CUSTOMER_ID = C.CUSTOMER_ID
            WHERE O.ORDER_ID = ?
        """
        cursor.execute(query_header, (self.order_id,))
        header_data = cursor.fetchone()
        
        if header_data:
            self.lblMaDon.setText(f"Đơn hàng: {header_data[0]}")
            # Giả định ID Label là lblHienThiKH giống bên Order.py
            self.lblHienThiKH.setText(header_data[1]) 

        # Lấy danh sách sản phẩm trong đơn
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
            self.tblDanhSachSP.setItem(row_idx, 0, QtWidgets.QTableWidgetItem(row_data[0])) 
            self.tblDanhSachSP.setItem(row_idx, 1, QtWidgets.QTableWidgetItem(str(row_data[1]))) 
            self.tblDanhSachSP.setItem(row_idx, 2, QtWidgets.QTableWidgetItem(f"{row_data[2]:,.0f}")) 
            self.tblDanhSachSP.setItem(row_idx, 3, QtWidgets.QTableWidgetItem(f"{row_data[3]:,.0f}")) 

            total_items += row_data[1]
            total_amount += row_data[3]

        # Cập nhật phần tóm tắt
        self.lblHienThiSoMon.setText(str(total_items))
        self.lblHienThiTongCong.setText(f"{total_amount:,.0f} VNĐ")

        conn.close()
        

# Bộ quản lý trang Tổng quan 
class OverviewManager:
    def __init__(self, table_widget):
        self.table = table_widget
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode.Stretch)

    def load_recent_orders(self):
        """Nạp 15 đơn hàng mới nhất từ cơ sở dữ liệu"""
        db = DatabaseManager()
        conn = db.get_connection()
        if not conn: return
        
        cursor = conn.cursor()
        # Dùng TOP 15 và ORDER BY DESC để lấy các đơn hàng vừa tạo
        query = """
            SELECT TOP 15 O.ORDER_ID, O.ORDER_DATE, 
                   SUM(OD.ORDER_QUANTITY * P.UNIT_PRICE) AS TOTAL_AMOUNT, 
                   O.ORDER_STATUS
            FROM ORDERS O
            LEFT JOIN ORDERDETAILS OD ON O.ORDER_ID = OD.ORDER_ID
            LEFT JOIN PRODUCTS P ON OD.PRODUCT_ID = P.PRODUCT_ID
            GROUP BY O.ORDER_ID, O.ORDER_DATE, O.ORDER_STATUS
            ORDER BY O.ORDER_ID DESC
        """
        cursor.execute(query)
        rows = cursor.fetchall()
        
        self.table.setRowCount(0)
        for row_idx, row_data in enumerate(rows):
            self.table.insertRow(row_idx)
            
            # Cột 0: Mã đơn
            self.table.setItem(row_idx, 0, QtWidgets.QTableWidgetItem(str(row_data[0])))
            # Cột 1: Ngày (chuyển sang kiểu chuỗi)
            self.table.setItem(row_idx, 1, QtWidgets.QTableWidgetItem(str(row_data[1])))
            
            # Cột 2: Tổng tiền
            total = row_data[2] if row_data[2] else 0
            self.table.setItem(row_idx, 2, QtWidgets.QTableWidgetItem(f"{total:,.0f} VNĐ"))
            
            # Cột 3: Trạng thái
            self.table.setItem(row_idx, 3, QtWidgets.QTableWidgetItem(row_data[3]))
            
            # Cột 4: Thêm nút "Xem chi tiết"
            order_dict = {"id": row_data[0]}
            self.add_view_button(row_idx, order_dict)
            
        conn.close()

    def add_view_button(self, row, order):
        container = QtWidgets.QWidget()
        layout = QtWidgets.QHBoxLayout(container)
        layout.setContentsMargins(5, 2, 5, 2)

        btn_view = QtWidgets.QPushButton("Xem chi tiết")
        btn_view.setStyleSheet("background-color: #10b981; color: white; font-weight: bold; padding: 4px; border-radius: 3px;")
        btn_view.clicked.connect(lambda: self.open_details(order))

        layout.addWidget(btn_view)
        self.table.setCellWidget(row, 4, container)

    def open_details(self, order):
        dialog = OrderDetails(order)
        dialog.exec()