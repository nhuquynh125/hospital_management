"""
Hospital Management System — Statistics & Charts Dashboard
Biểu đồ: bệnh nhân theo thời gian, tỉ lệ bệnh, thống kê tổng quan
Dùng Matplotlib nhúng vào PyQt6
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QComboBox, QGridLayout, QSizePolicy, QTabWidget
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

import database.dao as dao

try:
    import matplotlib
    matplotlib.use("QtAgg")
    from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
    from matplotlib.figure import Figure
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches
    MATPLOTLIB = True
except ImportError:
    MATPLOTLIB = False


# ── Matplotlib canvas wrapper ────────────────────────────
if MATPLOTLIB:
    class MplCanvas(FigureCanvas):
        def __init__(self, width=5, height=4, dpi=100):
            self.fig = Figure(figsize=(width, height), dpi=dpi, facecolor="#f7fafc")
            self.axes = self.fig.add_subplot(111)
            super().__init__(self.fig)
            self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
            self.updateGeometry()
else:
    class MplCanvas(QWidget):
        def __init__(self, *args, **kwargs):
            super().__init__()
            layout = QVBoxLayout(self)
            layout.addWidget(QLabel("Matplotlib not installed"))


# ═══════════════════════════════════════════════════════════
#  Stats Tab
# ═══════════════════════════════════════════════════════════
class StatsTab(QWidget):
    def __init__(self):
        super().__init__()
        self._build_ui()
        self._apply_style()
        if MATPLOTLIB:
            self._draw_all_charts()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # Header
        header_row = QHBoxLayout()
        title = QLabel("📊 Thống kê & Biểu đồ")
        title.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        title.setObjectName("sectionTitle")
        header_row.addWidget(title)
        header_row.addStretch()
        refresh_btn = QPushButton("🔄 Làm mới")
        refresh_btn.setObjectName("actionBtn")
        refresh_btn.clicked.connect(self._draw_all_charts)
        header_row.addWidget(refresh_btn)
        layout.addLayout(header_row)

        if not MATPLOTLIB:
            warn = QLabel("⚠️  matplotlib chưa được cài.\nChạy: pip install matplotlib")
            warn.setAlignment(Qt.AlignmentFlag.AlignCenter)
            warn.setStyleSheet("color:#744210; background:#fffbeb; border-radius:8px; padding:16px; font-size:13px;")
            layout.addWidget(warn)
            return

        # KPI row
        self.kpi_row = QHBoxLayout()
        self.kpi_row.setSpacing(12)
        self._kpi_frames = {}
        kpis = [
            ("total_patients",        "👥", "Tổng bệnh nhân",    "#2b6cb0", "#ebf8ff"),
            ("total_staff",           "👨‍⚕️","Nhân viên",         "#276749", "#f0fff4"),
            ("today_appointments",    "🗓️", "Lịch hẹn hôm nay", "#744210", "#fffbeb"),
            ("available_rooms",       "🏠", "Phòng trống",       "#553c9a", "#faf5ff"),
            ("low_stock_medicines",   "⚠️", "Thuốc sắp hết",    "#c53030", "#fff5f5"),
        ]
        for key, icon, label, color, bg in kpis:
            card = self._make_kpi_card(icon, label, "—", color, bg)
            self._kpi_frames[key] = card
            self.kpi_row.addWidget(card)
        layout.addLayout(self.kpi_row)

        # Charts tabs
        chart_tabs = QTabWidget()
        chart_tabs.setObjectName("chartTabs")

        # Tab 1: patients over time + pie
        tab1 = QWidget()
        t1l = QHBoxLayout(tab1)
        t1l.setSpacing(12)
        self.canvas_bar   = MplCanvas(width=6, height=3.5)
        self.canvas_pie   = MplCanvas(width=4, height=3.5)
        t1l.addWidget(self.canvas_bar, 3)
        t1l.addWidget(self.canvas_pie, 2)
        chart_tabs.addTab(tab1, "📈 Bệnh nhân & Tỉ lệ bệnh")

        # Tab 2: appointments by doctor + room status
        tab2 = QWidget()
        t2l = QHBoxLayout(tab2)
        t2l.setSpacing(12)
        self.canvas_doctor = MplCanvas(width=5, height=3.5)
        self.canvas_room   = MplCanvas(width=4, height=3.5)
        t2l.addWidget(self.canvas_doctor, 3)
        t2l.addWidget(self.canvas_room, 2)
        chart_tabs.addTab(tab2, "🗓️ Lịch hẹn & Phòng bệnh")

        # Tab 3: medicine stock
        tab3 = QWidget()
        t3l = QVBoxLayout(tab3)
        self.canvas_medicine = MplCanvas(width=9, height=3.5)
        t3l.addWidget(self.canvas_medicine)
        chart_tabs.addTab(tab3, "💊 Tồn kho thuốc")

        layout.addWidget(chart_tabs)

    def _make_kpi_card(self, icon, label, value, color, bg):
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{ background:{bg}; border-radius:10px; border:1px solid {color}30; }}
        """)
        cl = QVBoxLayout(card)
        cl.setContentsMargins(14, 12, 14, 12)
        cl.setSpacing(2)
        icon_lbl = QLabel(icon); icon_lbl.setFont(QFont("Segoe UI", 20))
        icon_lbl.setStyleSheet("background:transparent;")
        val_lbl  = QLabel(str(value))
        val_lbl.setFont(QFont("Segoe UI", 22, QFont.Weight.Bold))
        val_lbl.setStyleSheet(f"color:{color}; background:transparent;")
        name_lbl = QLabel(label)
        name_lbl.setStyleSheet(f"color:{color}; font-size:11px; background:transparent;")
        cl.addWidget(icon_lbl)
        cl.addWidget(val_lbl)
        cl.addWidget(name_lbl)
        card._val_lbl = val_lbl
        return card

    # ── Drawing ──────────────────────────────────────────────────
    def _draw_all_charts(self):
        if not MATPLOTLIB:
            return
        self._update_kpis()
        self._draw_patients_bar()
        self._draw_diagnosis_pie()
        self._draw_appointments_by_doctor()
        self._draw_room_status()
        self._draw_medicine_stock()

    def _update_kpis(self):
        stats = dao.get_dashboard_stats()
        for key, card in self._kpi_frames.items():
            card._val_lbl.setText(str(stats.get(key, 0)))

    def _draw_patients_bar(self):
        data = dao.get_patients_by_month()   # [(month_label, count), ...]
        ax = self.canvas_bar.axes
        ax.clear()
        if not data:
            ax.text(0.5, 0.5, "Chưa có dữ liệu", ha="center", va="center",
                    transform=ax.transAxes, color="#a0aec0", fontsize=12)
        else:
            labels = [d[0] for d in data]
            values = [d[1] for d in data]
            bars = ax.bar(labels, values, color="#4299e1", edgecolor="white", linewidth=0.5)
            ax.set_title("Số lượng bệnh nhân theo tháng", fontsize=11, fontweight="bold", pad=10)
            ax.set_ylabel("Số bệnh nhân", fontsize=9)
            ax.tick_params(axis="x", rotation=30, labelsize=8)
            ax.tick_params(axis="y", labelsize=8)
            ax.spines["top"].set_visible(False)
            ax.spines["right"].set_visible(False)
            ax.set_facecolor("#f7fafc")
            # Value labels on bars
            for bar, v in zip(bars, values):
                ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1,
                        str(v), ha="center", va="bottom", fontsize=8, color="#2d3748")
        self.canvas_bar.fig.tight_layout()
        self.canvas_bar.draw()

    def _draw_diagnosis_pie(self):
        data = dao.get_top_diagnoses()   # [(diagnosis, count), ...]
        ax = self.canvas_pie.axes
        ax.clear()
        if not data:
            ax.text(0.5, 0.5, "Chưa có chẩn đoán", ha="center", va="center",
                    transform=ax.transAxes, color="#a0aec0", fontsize=11)
        else:
            labels = [d[0][:20] for d in data]
            values = [d[1] for d in data]
            colors_list = ["#4299e1","#68d391","#f6ad55","#fc8181","#b794f4",
                           "#76e4f7","#fbd38d","#9ae6b4"]
            wedges, texts, autotexts = ax.pie(
                values, labels=None, autopct="%1.0f%%",
                colors=colors_list[:len(values)],
                startangle=90, pctdistance=0.8,
                wedgeprops={"edgecolor":"white","linewidth":1.5}
            )
            for at in autotexts:
                at.set_fontsize(8)
            ax.set_title("Top bệnh lý chẩn đoán", fontsize=11, fontweight="bold", pad=10)
            ax.legend(wedges, labels, loc="lower center", bbox_to_anchor=(0.5, -0.25),
                      fontsize=7, ncol=2)
        self.canvas_pie.fig.tight_layout()
        self.canvas_pie.draw()

    def _draw_appointments_by_doctor(self):
        data = dao.get_appointments_by_doctor()   # [(doctor_name, count), ...]
        ax = self.canvas_doctor.axes
        ax.clear()
        if not data:
            ax.text(0.5, 0.5, "Chưa có lịch hẹn", ha="center", va="center",
                    transform=ax.transAxes, color="#a0aec0", fontsize=12)
        else:
            names  = [d[0][:18] for d in data]
            counts = [d[1] for d in data]
            colors_list = ["#48bb78","#4299e1","#ed8936","#9f7aea","#f56565"]
            ax.barh(names, counts,
                    color=colors_list[:len(names)], edgecolor="white")
            ax.set_title("Lịch hẹn theo bác sĩ", fontsize=11, fontweight="bold", pad=10)
            ax.set_xlabel("Số lịch hẹn", fontsize=9)
            ax.tick_params(labelsize=8)
            ax.spines["top"].set_visible(False)
            ax.spines["right"].set_visible(False)
            ax.set_facecolor("#f7fafc")
            for i, v in enumerate(counts):
                ax.text(v + 0.05, i, str(v), va="center", fontsize=8)
        self.canvas_doctor.fig.tight_layout()
        self.canvas_doctor.draw()

    def _draw_room_status(self):
        rooms = dao.get_all_rooms()
        ax = self.canvas_room.axes
        ax.clear()
        if not rooms:
            ax.text(0.5, 0.5, "Chưa có phòng", ha="center", va="center",
                    transform=ax.transAxes, color="#a0aec0")
        else:
            from collections import Counter
            status_counts = Counter(r["status"] for r in rooms)
            labels = list(status_counts.keys())
            values = list(status_counts.values())
            color_map = {"Trống":"#68d391","Đang dùng":"#4299e1","Bảo trì":"#f6ad55"}
            colors_list = [color_map.get(l,"#cbd5e0") for l in labels]
            wedges, texts, autotexts = ax.pie(
                values, labels=labels, autopct="%1.0f%%",
                colors=colors_list, startangle=90,
                wedgeprops={"edgecolor":"white","linewidth":2},
                textprops={"fontsize":9}
            )
            for at in autotexts:
                at.set_fontsize(9); at.set_fontweight("bold")
            ax.set_title("Trạng thái phòng bệnh", fontsize=11, fontweight="bold", pad=10)
        self.canvas_room.fig.tight_layout()
        self.canvas_room.draw()

    def _draw_medicine_stock(self):
        meds = dao.get_all_medicines()
        ax = self.canvas_medicine.axes
        ax.clear()
        if not meds:
            ax.text(0.5, 0.5, "Chưa có thuốc", ha="center", va="center",
                    transform=ax.transAxes, color="#a0aec0")
        else:
            # Show top 12 by stock
            meds_sorted = sorted(meds, key=lambda m: m["stock_qty"], reverse=True)[:12]
            names   = [m["name"][:16] for m in meds_sorted]
            stocks  = [m["stock_qty"] for m in meds_sorted]
            mins    = [m["min_stock"] for m in meds_sorted]
            x = range(len(names))
            bar_colors = ["#fc8181" if s <= mn else "#4299e1"
                          for s, mn in zip(stocks, mins)]
            ax.bar(x, stocks, color=bar_colors, edgecolor="white", label="Tồn kho")
            ax.step([i-0.5 for i in x] + [len(x)-0.5], mins + [mins[-1]],
                    color="#e53e3e", linewidth=1.5, linestyle="--", label="Mức tối thiểu")
            ax.set_xticks(list(x))
            ax.set_xticklabels(names, rotation=35, ha="right", fontsize=7)
            ax.set_title("Tồn kho thuốc (đỏ = sắp hết)", fontsize=11, fontweight="bold", pad=10)
            ax.set_ylabel("Số lượng", fontsize=9)
            ax.legend(fontsize=8)
            ax.spines["top"].set_visible(False)
            ax.spines["right"].set_visible(False)
            ax.set_facecolor("#f7fafc")
        self.canvas_medicine.fig.tight_layout()
        self.canvas_medicine.draw()

    def _apply_style(self):
        self.setStyleSheet("""
        QWidget { background: #f7fafc; font-family: 'Segoe UI'; }
        #sectionTitle { color: #1a365d; }
        #actionBtn {
            background: #edf2f7; color: #2d3748; border: none;
            border-radius: 6px; padding: 7px 14px; font-size: 12px;
        }
        #chartTabs::pane { border:1px solid #e2e8f0; border-radius:8px; background:white; }
        QTabBar::tab { padding:8px 16px; font-size:12px; }
        QTabBar::tab:selected { background:#2b6cb0; color:white; border-radius:6px 6px 0 0; }
        """)
