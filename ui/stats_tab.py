from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QComboBox, QGridLayout, QSizePolicy, QTabWidget
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont

import database.dao as dao
from datetime import datetime

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
    def __init__(self, role=None):
        super().__init__()
        self.role = role
        self._build_ui()
        self._apply_style()
        if MATPLOTLIB:
            self._draw_all_charts()
            self._timer = QTimer(self)
            self._timer.timeout.connect(self._draw_all_charts)
            self._timer.start(30000)

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



        # Charts tabs
        chart_tabs = QTabWidget()
        chart_tabs.setObjectName("chartTabs")

        # Tab 1: patients over time + pie
        tab1 = QWidget()
        t1l = QVBoxLayout(tab1)
        
        f1 = QHBoxLayout()
        self.diag_month_combo = QComboBox()
        self.diag_month_combo.addItems([f"Tháng {i}" for i in range(1, 13)])
        self.diag_year_combo = QComboBox()
        self.diag_year_combo.addItems([str(y) for y in range(2020, 2030)])
        now = datetime.now()
        self.diag_month_combo.setCurrentIndex(now.month - 1)
        self.diag_year_combo.setCurrentText(str(now.year))
        btn1 = QPushButton("Lọc")
        btn1.clicked.connect(self._draw_diagnosis_pie)
        f1.addWidget(QLabel("Tỉ lệ bệnh theo tháng/năm:"))
        f1.addWidget(self.diag_month_combo)
        f1.addWidget(self.diag_year_combo)
        f1.addWidget(btn1)
        f1.addStretch()
        t1l.addLayout(f1)
        
        t1l_charts = QHBoxLayout()
        self.canvas_bar   = MplCanvas(width=6, height=3.5)
        self.canvas_pie   = MplCanvas(width=4, height=3.5)
        t1l_charts.addWidget(self.canvas_bar, 3)
        t1l_charts.addWidget(self.canvas_pie, 2)
        t1l.addLayout(t1l_charts)
        chart_tabs.addTab(tab1, "📈 Bệnh nhân & Tỉ lệ bệnh")

        # Tab 2: appointments by doctor + room status
        tab2 = QWidget()
        t2l = QVBoxLayout(tab2)
        
        f2 = QHBoxLayout()
        self.appt_type_combo = QComboBox()
        self.appt_type_combo.addItems(["Theo tháng", "Theo tuần"])
        self.appt_val_combo = QComboBox()
        now = datetime.now()
        self.appt_val_combo.addItems([f"Tháng {i}" for i in range(1, 13)])
        self.appt_val_combo.setCurrentIndex(now.month - 1)
        self.appt_year_combo = QComboBox()
        self.appt_year_combo.addItems([str(y) for y in range(2020, 2030)])
        self.appt_year_combo.setCurrentText(str(now.year))
        
        def update_appt_combo():
            self.appt_val_combo.clear()
            if self.appt_type_combo.currentText() == "Theo tháng":
                self.appt_val_combo.addItems([f"Tháng {i}" for i in range(1, 13)])
                self.appt_val_combo.setCurrentIndex(datetime.now().month - 1)
            else:
                self.appt_val_combo.addItems([f"Tuần {i}" for i in range(1, 54)])
                curr_week = datetime.now().isocalendar()[1]
                self.appt_val_combo.setCurrentIndex(curr_week - 1)
                
        self.appt_type_combo.currentIndexChanged.connect(update_appt_combo)
        btn2 = QPushButton("Lọc")
        btn2.clicked.connect(self._draw_appointments_by_doctor)
        f2.addWidget(QLabel("Lịch hẹn theo:"))
        f2.addWidget(self.appt_type_combo)
        f2.addWidget(self.appt_val_combo)
        f2.addWidget(self.appt_year_combo)
        f2.addWidget(btn2)
        f2.addStretch()
        t2l.addLayout(f2)
        
        t2l_charts = QHBoxLayout()
        self.canvas_doctor = MplCanvas(width=9, height=3.5)
        t2l_charts.addWidget(self.canvas_doctor)
        t2l.addLayout(t2l_charts)
        chart_tabs.addTab(tab2, "🗓️ Lịch hẹn")

        # Tab 3: medicine stock
        if self.role != "doctor":
            tab3 = QWidget()
            t3l = QVBoxLayout(tab3)
            self.canvas_medicine = MplCanvas(width=9, height=3.5)
            t3l.addWidget(self.canvas_medicine)
            chart_tabs.addTab(tab3, "💊 Tồn kho thuốc")

        # Tab 4: Revenue
        if self.role != "doctor":
            tab4 = QWidget()
            t4l = QVBoxLayout(tab4)
            
            f4 = QHBoxLayout()
            self.rev_type_combo = QComboBox()
            self.rev_type_combo.addItems(["Theo tháng", "Theo tuần"])
            self.rev_val_combo = QComboBox()
            self.rev_val_combo.addItems([f"Tháng {i}" for i in range(1, 13)])
            now = datetime.now()
            self.rev_val_combo.setCurrentIndex(now.month - 1)
            self.rev_year_combo = QComboBox()
            self.rev_year_combo.addItems([str(y) for y in range(2020, 2030)])
            self.rev_year_combo.setCurrentText(str(now.year))
            
            def update_rev_combo():
                self.rev_val_combo.clear()
                if self.rev_type_combo.currentText() == "Theo tháng":
                    self.rev_val_combo.addItems([f"Tháng {i}" for i in range(1, 13)])
                    self.rev_val_combo.setCurrentIndex(datetime.now().month - 1)
                else:
                    self.rev_val_combo.addItems([f"Tuần {i}" for i in range(1, 54)])
                    curr_week = datetime.now().isocalendar()[1]
                    self.rev_val_combo.setCurrentIndex(curr_week - 1)
                    
            self.rev_type_combo.currentIndexChanged.connect(update_rev_combo)
            btn4 = QPushButton("Lọc")
            btn4.clicked.connect(self._draw_revenue_chart)
            f4.addWidget(QLabel("Doanh thu theo:"))
            f4.addWidget(self.rev_type_combo)
            f4.addWidget(self.rev_val_combo)
            f4.addWidget(self.rev_year_combo)
            f4.addWidget(btn4)
            f4.addStretch()
            t4l.addLayout(f4)
            
            self.canvas_revenue = MplCanvas(width=9, height=3.5)
            t4l.addWidget(self.canvas_revenue)
            chart_tabs.addTab(tab4, "💰 Doanh thu")

        layout.addWidget(chart_tabs)



    # ── Drawing ──────────────────────────────────────────────────
    def _draw_all_charts(self):
        if not MATPLOTLIB:
            return

        self._draw_patients_bar()
        self._draw_diagnosis_pie()
        self._draw_appointments_by_doctor()
        
        if self.role != "doctor":
            self._draw_medicine_stock()
            self._draw_revenue_chart()



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
        m = getattr(self, "diag_month_combo", None)
        if m:
            month = m.currentIndex() + 1
            year = int(self.diag_year_combo.currentText())
            data = dao.get_top_diagnoses(month=month, year=year)
        else:
            data = dao.get_top_diagnoses()
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
        cb = getattr(self, "appt_type_combo", None)
        if cb:
            ft = "month" if cb.currentText() == "Theo tháng" else "week"
            val = self.appt_val_combo.currentIndex() + 1
            y = int(self.appt_year_combo.currentText())
            if ft == "month":
                data = dao.get_appointments_by_doctor(filter_type="month", month=val, year=y)
            else:
                w_str = f"{y}-W{val:02d}"
                data = dao.get_appointments_by_doctor(filter_type="week", week_str=w_str)
        else:
            data = dao.get_appointments_by_doctor()
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

    def _draw_revenue_chart(self):
        cb = getattr(self, "rev_type_combo", None)
        if cb:
            ft = "month" if cb.currentText() == "Theo tháng" else "week"
            val = self.rev_val_combo.currentIndex() + 1
            y = int(self.rev_year_combo.currentText())
            if ft == "month":
                data = dao.get_revenue_by_time(filter_type="month", month=val, year=y)
            else:
                w_str = f"{y}-W{val:02d}"
                data = dao.get_revenue_by_time(filter_type="week", week_str=w_str)
        else:
            data = dao.get_revenue_by_time()
        ax = self.canvas_revenue.axes
        ax.clear()
        if not data:
            ax.text(0.5, 0.5, "Chưa có dữ liệu doanh thu", ha="center", va="center",
                    transform=ax.transAxes, color="#a0aec0", fontsize=12)
        else:
            labels = [d[0] for d in data]
            values = [d[1] / 1_000_000 for d in data]
            
            ax.bar(labels, values, color="#9ae6b4", edgecolor="white", alpha=0.6, label="Doanh thu (Triệu VNĐ)")
            ax.plot(labels, values, color="#276749", marker="o", linewidth=2)
            
            ax.set_title("Doanh thu theo tháng (Triệu VNĐ)", fontsize=11, fontweight="bold", pad=10)
            ax.set_ylabel("Triệu VNĐ", fontsize=9)
            ax.tick_params(axis="x", rotation=30, labelsize=8)
            ax.tick_params(axis="y", labelsize=8)
            ax.spines["top"].set_visible(False)
            ax.spines["right"].set_visible(False)
            ax.set_facecolor("#f7fafc")
            
            for i, v in enumerate(values):
                offset = max(values)*0.02 if max(values) > 0 else 1
                ax.text(i, v + offset, f"{v:,.1f}", ha="center", va="bottom", fontsize=8, color="#2d3748")
        
        self.canvas_revenue.fig.tight_layout()
        self.canvas_revenue.draw()

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
