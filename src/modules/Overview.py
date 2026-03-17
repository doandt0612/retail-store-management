import os
import sys

os.environ.pop("QT_QPA_PLATFORM", None)

from PyQt6 import QtWidgets, QtGui, QtCore
from PyQt6.QtCore import Qt, QTimer
from src.database.db_connection import DatabaseManager

try:
    from src.modules.Order import ViewOrder
except ImportError:
    ViewOrder = None


class OverviewManager:
    def __init__(self, table_widget, lbl_revenue=None, lbl_orders=None):
        self.table = table_widget
        self.lbl_revenue = lbl_revenue  
        self.lbl_orders = lbl_orders    

        self.fr_chart_revenue = None
        self.fr_chart_products = None
        
        self.switch_to_customer_callback = None
        
        self.init_ui()
        self.auto_detect_widgets()
        
        QTimer.singleShot(0, self.load_data)

    # ================= AUTO DETECT =================
    def auto_detect_widgets(self):
        try:
            main_window = self.table.window()

            if not self.lbl_revenue:
                self.lbl_revenue = main_window.findChild(QtWidgets.QLabel, "lblHienThiTongDoanhThu")
            if not self.lbl_orders:
                self.lbl_orders = main_window.findChild(QtWidgets.QLabel, "lblHienThiTongDonHang")

            self.fr_chart_revenue = main_window.findChild(QtWidgets.QFrame, "frChartDoanhThu")
            self.fr_chart_products = main_window.findChild(QtWidgets.QFrame, "frChartSP")

            if self.fr_chart_revenue: self.fr_chart_revenue.setMinimumHeight(180)
            if self.fr_chart_products: self.fr_chart_products.setMinimumHeight(180)

        except Exception as e:
            print(f"Lỗi nhận diện UI: {e}")

    # ================= UI =================
    def init_ui(self):
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode.Stretch)

        if self.table.columnCount() > 5:
            header.setSectionResizeMode(5, QtWidgets.QHeaderView.ResizeMode.Fixed)
            self.table.setColumnWidth(5, 120)

    # ================= LOAD ALL =================
    def load_data(self):
        self.load_numeric_labels()
        self.render_charts()
        self.load_recent_orders()

    # ================= LABEL =================
    def load_numeric_labels(self):
        db = DatabaseManager()
        conn = db.get_connection()
        if not conn: return

        try:
            cursor = conn.cursor()

            cursor.execute("SELECT ISNULL(SUM(TotalAmount), 0) FROM Orders WHERE Status = N'Đã thanh toán'")
            rev = cursor.fetchone()[0]
            if self.lbl_revenue:
                self.lbl_revenue.setText(f"{rev:,.0f} VNĐ")

            cursor.execute("SELECT COUNT(OrderID) FROM Orders")
            cnt = cursor.fetchone()[0]
            if self.lbl_orders:
                self.lbl_orders.setText(f"{cnt} đơn")

        finally:
            conn.close()

    # ================= CLEAR =================
    def clear_layout(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    # ================= CHART =================
    def render_charts(self):
        if not self.fr_chart_revenue or not self.fr_chart_products:
            self.auto_detect_widgets()
            if not self.fr_chart_revenue:
                return

        db = DatabaseManager()
        conn = db.get_connection()
        if not conn: return

        try:
            cursor = conn.cursor()

            # Doanh thu 7 ngày
            cursor.execute("""
                SELECT CAST(OrderDate AS DATE), SUM(TotalAmount)
                FROM Orders
                WHERE Status = N'Đã thanh toán'
                GROUP BY CAST(OrderDate AS DATE)
                ORDER BY CAST(OrderDate AS DATE) DESC
            """)
            rev_data = cursor.fetchall()[:7]
            rev_data.reverse()

            # Top sản phẩm
            cursor.execute("""
                SELECT TOP 5 p.ProductName, SUM(od.OrderedQuantity)
                FROM Order_Details od
                JOIN Products p ON od.ProductID = p.ProductID
                GROUP BY p.ProductName
                ORDER BY SUM(od.OrderedQuantity) DESC
            """)
            prod_data = cursor.fetchall()

            self.draw_chart(self.fr_chart_revenue, rev_data, is_money=True)
            self.draw_chart(self.fr_chart_products, prod_data, is_money=False)

        finally:
            conn.close()

    # ================= DRAW =================
    def draw_chart(self, frame, data, is_money=False):
        if not frame:
            return

        layout = frame.layout()

        if layout is None:
            layout = QtWidgets.QVBoxLayout()
            frame.setLayout(layout)

        self.clear_layout(layout)

        if not data:
            lbl = QtWidgets.QLabel("Không có dữ liệu")
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(lbl)
            return

        max_val = max(d[1] for d in data) or 1

        for name, val in data:
            row = QtWidgets.QWidget()
            row_layout = QtWidgets.QHBoxLayout(row)

            # label name
            name_str = name.strftime('%d/%m') if hasattr(name, 'strftime') else str(name)

            lbl_name = QtWidgets.QLabel(name_str)

            lbl_name.setMinimumWidth(120)
            lbl_name.setToolTip(name_str)

            lbl_name.setSizePolicy(
                QtWidgets.QSizePolicy.Policy.Expanding,
                QtWidgets.QSizePolicy.Policy.Preferred
            )

            # bar
            bar = QtWidgets.QProgressBar()
            bar.setMaximum(int(max_val))
            bar.setValue(int(val))
            bar.setTextVisible(False)

            # value
            val_str = f"{val:,.0f}" if is_money else str(val)
            lbl_val = QtWidgets.QLabel(val_str)
            lbl_val.setFixedWidth(80)
            lbl_val.setAlignment(Qt.AlignmentFlag.AlignRight)

            row_layout.addWidget(lbl_name)
            row_layout.addWidget(bar)
            row_layout.addWidget(lbl_val)

            layout.addWidget(row)

        layout.addStretch()

    # ================= TABLE =================
    def load_recent_orders(self):
        db = DatabaseManager()
        conn = db.get_connection()
        if not conn: return

        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT TOP 10 o.OrderID, o.OrderDate, c.CustomerName, o.TotalAmount, o.Status
                FROM Orders o
                JOIN Customers c ON o.CustomerID = c.CustomerID
                ORDER BY o.OrderDate DESC
            """)

            rows = cursor.fetchall()
            self.table.setRowCount(0)

            for i, r in enumerate(rows):
                self.table.insertRow(i)

                self.table.setItem(i, 0, QtWidgets.QTableWidgetItem(str(r[0])))
                self.table.setItem(i, 1, QtWidgets.QTableWidgetItem(r[1].strftime('%d/%m/%Y')))
                self.table.setItem(i, 2, QtWidgets.QTableWidgetItem(r[2]))
                self.table.setItem(i, 3, QtWidgets.QTableWidgetItem(f"{r[3]:,.0f} VNĐ"))
                self.table.setItem(i, 4, QtWidgets.QTableWidgetItem(r[4]))

                status = r[4]
                status_item = QtWidgets.QTableWidgetItem(status)
                if status == "Đã thanh toán": status_item.setForeground(Qt.GlobalColor.darkGreen)
                elif status == "Đã hủy": status_item.setForeground(Qt.GlobalColor.darkRed)
                else: status_item.setForeground(Qt.GlobalColor.red)
                self.table.setItem(i, 4, status_item)

        finally:
            conn.close()