import os
import sys

os.environ.pop("QT_QPA_PLATFORM", None)

from PyQt6 import QtWidgets, QtGui, QtCore
from PyQt6.QtCore import Qt, QTimer
from src.database.db_connection import DatabaseManager

# ── Matplotlib nhúng vào PyQt6 ──────────────────────────────
import matplotlib
matplotlib.use("QtAgg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.ticker as mticker
import numpy as np

# Font tiếng Việt (dùng font hệ thống nếu có, fallback sans-serif)
plt.rcParams["font.family"]     = ["DejaVu Sans", "Arial", "sans-serif"]
plt.rcParams["axes.unicode_minus"] = False

# ── Bảng màu nhất quán ──────────────────────────────────────
COLORS = ["#2563eb", "#10b981", "#f59e0b", "#ef4444", "#8b5cf6",
          "#06b6d4", "#ec4899", "#84cc16"]
BG     = "#f3f4f6"
WHITE  = "#ffffff"
GRAY   = "#6b7280"
DARK   = "#111827"


# ============================================================
# HELPER: tạo Figure / Canvas sạch
# ============================================================
def _make_canvas(fig_w=5, fig_h=3, bg=BG):
    fig = Figure(figsize=(fig_w, fig_h), facecolor=bg, tight_layout=True)
    canvas = FigureCanvas(fig)
    canvas.setStyleSheet("background: transparent;")
    return fig, canvas


def _clear_frame(frame: QtWidgets.QFrame):
    """Xóa sạch layout cũ của frame trước khi vẽ lại."""
    old = frame.layout()
    if old:
        while old.count():
            item = old.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()
    else:
        frame.setLayout(QtWidgets.QVBoxLayout())
    frame.layout().setContentsMargins(4, 4, 4, 4)
    frame.layout().setSpacing(0)


# ============================================================
# BIỂU ĐỒ CỘT – Doanh thu 7 ngày gần nhất
# ============================================================
def draw_bar_revenue(frame: QtWidgets.QFrame, data):
    """
    data: [(date, amount), ...] đã sort tăng dần
    """
    _clear_frame(frame)

    fig, canvas = _make_canvas(fig_w=5, fig_h=2.6, bg=BG)
    ax = fig.add_subplot(111, facecolor=WHITE)

    if not data:
        ax.text(0.5, 0.5, "Chưa có dữ liệu doanh thu",
                ha="center", va="center", color=GRAY, fontsize=10)
        ax.axis("off")
        frame.layout().addWidget(canvas)
        return

    labels = [d[0].strftime("%d/%m") if hasattr(d[0], "strftime") else str(d[0])
              for d in data]
    values = [float(d[1]) for d in data]
    max_v  = max(values) or 1

    bars = ax.bar(labels, values, color=COLORS[0], width=0.55,
                  zorder=3, edgecolor="white", linewidth=0.5)

    # Tô màu cột cao nhất
    peak_idx = values.index(max_v)
    bars[peak_idx].set_color(COLORS[1])

    # Nhãn giá trị trên cột
    for bar, val in zip(bars, values):
        if val > 0:
            ax.text(bar.get_x() + bar.get_width() / 2,
                    bar.get_height() + max_v * 0.02,
                    f"{val/1_000_000:.1f}M" if val >= 1_000_000 else f"{val/1_000:.0f}K",
                    ha="center", va="bottom", fontsize=7.5, color=DARK, fontweight="bold")

    # Lưới ngang nhẹ
    ax.yaxis.grid(True, linestyle="--", alpha=0.4, zorder=0)
    ax.set_axisbelow(True)
    ax.spines[["top", "right", "left"]].set_visible(False)
    ax.spines["bottom"].set_color("#e5e7eb")
    ax.tick_params(axis="x", labelsize=8, colors=GRAY)
    ax.tick_params(axis="y", labelsize=7, colors=GRAY)
    ax.yaxis.set_major_formatter(
        mticker.FuncFormatter(lambda x, _: f"{x/1_000_000:.1f}M" if x >= 1_000_000 else f"{x/1_000:.0f}K")
    )
    ax.set_title("Doanh thu 7 ngày gần nhất (VNĐ)", fontsize=9,
                 color=DARK, fontweight="bold", pad=6)

    frame.layout().addWidget(canvas)


# ============================================================
# BIỂU ĐỒ TRÒN – Top 5 sản phẩm bán chạy
# ============================================================
def draw_pie_products(frame: QtWidgets.QFrame, data):
    """
    data: [(product_name, qty), ...] top 5
    """
    _clear_frame(frame)

    fig, canvas = _make_canvas(fig_w=5, fig_h=2.6, bg=BG)
    ax = fig.add_subplot(111, facecolor=BG)

    if not data:
        ax.text(0.5, 0.5, "Chưa có dữ liệu sản phẩm",
                ha="center", va="center", color=GRAY, fontsize=10)
        ax.axis("off")
        frame.layout().addWidget(canvas)
        return

    names  = [d[0] if len(d[0]) <= 18 else d[0][:16] + "…" for d in data]
    values = [float(d[1]) for d in data]
    colors = COLORS[:len(data)]

    wedges, texts, autotexts = ax.pie(
        values,
        labels=None,
        autopct="%1.1f%%",
        startangle=90,
        colors=colors,
        pctdistance=0.75,
        wedgeprops=dict(edgecolor="white", linewidth=1.5),
    )
    for at in autotexts:
        at.set_fontsize(7.5)
        at.set_color(WHITE)
        at.set_fontweight("bold")

    # Legend bên phải
    ax.legend(wedges, names,
              loc="center left",
              bbox_to_anchor=(0.9, 0.5),
              fontsize=7.5,
              frameon=False,
              labelcolor=DARK)

    ax.set_title("Top 5 sản phẩm bán chạy", fontsize=9,
                 color=DARK, fontweight="bold", pad=6)

    frame.layout().addWidget(canvas)


# ============================================================
# BIỂU ĐỒ ĐƯỜNG – Số đơn hàng 7 ngày
# ============================================================
def draw_line_orders(frame: QtWidgets.QFrame, data):
    """
    data: [(date, count), ...] đã sort tăng dần
    """
    _clear_frame(frame)

    fig, canvas = _make_canvas(fig_w=5, fig_h=2.2, bg=BG)
    ax = fig.add_subplot(111, facecolor=WHITE)

    if not data:
        ax.text(0.5, 0.5, "Chưa có dữ liệu",
                ha="center", va="center", color=GRAY, fontsize=10)
        ax.axis("off")
        frame.layout().addWidget(canvas)
        return

    labels = [d[0].strftime("%d/%m") if hasattr(d[0], "strftime") else str(d[0])
              for d in data]
    values = [int(d[1]) for d in data]

    ax.plot(labels, values, marker="o", color=COLORS[2], linewidth=2,
            markersize=6, zorder=3)
    ax.fill_between(range(len(values)), values,
                    alpha=0.12, color=COLORS[2])

    for i, (lbl, val) in enumerate(zip(labels, values)):
        ax.text(i, val + 0.3, str(val), ha="center", va="bottom",
                fontsize=8, color=DARK, fontweight="bold")

    ax.yaxis.grid(True, linestyle="--", alpha=0.4)
    ax.set_axisbelow(True)
    ax.spines[["top", "right", "left"]].set_visible(False)
    ax.spines["bottom"].set_color("#e5e7eb")
    ax.tick_params(axis="x", labelsize=8, colors=GRAY)
    ax.tick_params(axis="y", labelsize=7, colors=GRAY)
    ax.set_xticks(range(len(labels)))
    ax.set_xticklabels(labels)
    ax.set_title("Số đơn hàng 7 ngày gần nhất", fontsize=9,
                 color=DARK, fontweight="bold", pad=6)

    frame.layout().addWidget(canvas)


# ============================================================
# OVERVIEW MANAGER
# ============================================================
class OverviewManager:
    def __init__(self, table_widget, lbl_revenue=None, lbl_orders=None):
        self.table       = table_widget
        self.lbl_revenue = lbl_revenue
        self.lbl_orders  = lbl_orders

        # Frame chứa biểu đồ — auto-detect từ UI
        self.fr_chart_revenue  = None   # biểu đồ cột doanh thu
        self.fr_chart_products = None   # biểu đồ tròn sản phẩm
        self.fr_chart_orders   = None   # biểu đồ đường số đơn (nếu có)

        self.switch_to_customer_callback = None

        self.init_ui()
        self.auto_detect_widgets()
        QTimer.singleShot(0, self.load_data)

    # ── Auto detect ──────────────────────────────────────────
    def auto_detect_widgets(self):
        try:
            win = self.table.window()

            if not self.lbl_revenue:
                self.lbl_revenue = win.findChild(QtWidgets.QLabel, "lblHienThiTongDoanhThu")
            if not self.lbl_orders:
                self.lbl_orders  = win.findChild(QtWidgets.QLabel, "lblHienThiTongDonHang")

            self.fr_chart_revenue  = win.findChild(QtWidgets.QFrame, "frChartDoanhThu")
            self.fr_chart_products = win.findChild(QtWidgets.QFrame, "frChartSP")
            self.fr_chart_orders   = win.findChild(QtWidgets.QFrame, "frChartDonHang")

            for fr in [self.fr_chart_revenue, self.fr_chart_products, self.fr_chart_orders]:
                if fr:
                    fr.setMinimumHeight(220)

        except Exception as e:
            print(f"Lỗi nhận diện UI: {e}")

    # ── Cài đặt bảng đơn hàng gần đây ───────────────────────
    def init_ui(self):
        tbl = self.table
        tbl.verticalHeader().setVisible(False)
        tbl.setEditTriggers(QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)
        tbl.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        tbl.setAlternatingRowColors(True)
        hdr = tbl.horizontalHeader()
        hdr.setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode.Stretch)
        if tbl.columnCount() > 5:
            hdr.setSectionResizeMode(5, QtWidgets.QHeaderView.ResizeMode.Fixed)
            tbl.setColumnWidth(5, 120)

    # ── Load tất cả ──────────────────────────────────────────
    def load_data(self):
        self.load_numeric_labels()
        self.render_charts()
        self.load_recent_orders()

    # ── Nhãn số liệu tổng ────────────────────────────────────
    def load_numeric_labels(self):
        db   = DatabaseManager()
        conn = db.get_connection()
        if not conn:
            return
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT ISNULL(SUM(TotalAmount),0) FROM Orders WHERE Status = N'Đã thanh toán'"
            )
            rev = cursor.fetchone()[0]
            if self.lbl_revenue:
                self.lbl_revenue.setText(f"{rev:,.0f} VNĐ")

            cursor.execute("SELECT COUNT(OrderID) FROM Orders")
            cnt = cursor.fetchone()[0]
            if self.lbl_orders:
                self.lbl_orders.setText(f"{cnt} đơn")
        finally:
            conn.close()

    # ── Vẽ biểu đồ ───────────────────────────────────────────
    def render_charts(self):
        self.auto_detect_widgets()

        db   = DatabaseManager()
        conn = db.get_connection()
        if not conn:
            return
        try:
            cursor = conn.cursor()

            # 1. Doanh thu 7 ngày (biểu đồ cột)
            cursor.execute("""
                SELECT CAST(OrderDate AS DATE), SUM(TotalAmount)
                FROM   Orders
                WHERE  Status = N'Đã thanh toán'
                GROUP  BY CAST(OrderDate AS DATE)
                ORDER  BY CAST(OrderDate AS DATE) DESC
            """)
            rev_data = list(reversed(cursor.fetchall()[:7]))

            # 2. Top 5 sản phẩm bán chạy (biểu đồ tròn)
            cursor.execute("""
                SELECT TOP 5 p.ProductName, SUM(od.OrderedQuantity)
                FROM   Order_Details od
                JOIN   Products p ON od.ProductID = p.ProductID
                GROUP  BY p.ProductName
                ORDER  BY SUM(od.OrderedQuantity) DESC
            """)
            prod_data = cursor.fetchall()

            # 3. Số đơn hàng 7 ngày (biểu đồ đường)
            cursor.execute("""
                SELECT CAST(OrderDate AS DATE), COUNT(OrderID)
                FROM   Orders
                GROUP  BY CAST(OrderDate AS DATE)
                ORDER  BY CAST(OrderDate AS DATE) DESC
            """)
            order_data = list(reversed(cursor.fetchall()[:7]))

        finally:
            conn.close()

        # Vẽ vào frame tương ứng
        if self.fr_chart_revenue:
            draw_bar_revenue(self.fr_chart_revenue, rev_data)

        if self.fr_chart_products:
            draw_pie_products(self.fr_chart_products, prod_data)

        if self.fr_chart_orders:
            draw_line_orders(self.fr_chart_orders, order_data)

    # ── Bảng đơn hàng gần đây ────────────────────────────────
    def load_recent_orders(self):
        db   = DatabaseManager()
        conn = db.get_connection()
        if not conn:
            return
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT TOP 10 o.OrderID, o.OrderDate, c.CustomerName,
                              o.TotalAmount, o.Status
                FROM   Orders o
                JOIN   Customers c ON o.CustomerID = c.CustomerID
                ORDER  BY o.OrderDate DESC
            """)
            rows = cursor.fetchall()
            tbl  = self.table
            tbl.setRowCount(0)

            _STATUS_COLOR = {
                "Đã thanh toán": Qt.GlobalColor.darkGreen,
                "Đã hủy":        Qt.GlobalColor.darkRed,
            }

            for i, r in enumerate(rows):
                tbl.insertRow(i)
                tbl.setItem(i, 0, QtWidgets.QTableWidgetItem(str(r[0])))
                tbl.setItem(i, 1, QtWidgets.QTableWidgetItem(
                    r[1].strftime("%d/%m/%Y") if r[1] else ""))
                tbl.setItem(i, 2, QtWidgets.QTableWidgetItem(r[2]))
                tbl.setItem(i, 3, QtWidgets.QTableWidgetItem(f"{r[3]:,.0f} VNĐ"))

                status_item = QtWidgets.QTableWidgetItem(r[4])
                status_item.setForeground(
                    _STATUS_COLOR.get(r[4], Qt.GlobalColor.red)
                )
                tbl.setItem(i, 4, status_item)
        finally:
            conn.close()