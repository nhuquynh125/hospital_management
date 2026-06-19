from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView, QComboBox
)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QFont, QColor
import random
import database.dao as dao

class PredictiveAnalyticsTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()
        self._apply_style()
        self.load_data()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)

        # Header
        header = QHBoxLayout()
        title = QLabel("🔮 Dự báo Lượng bệnh nhân (AI)")
        title.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        title.setObjectName("sectionTitle")
        header.addWidget(title)
        header.addStretch()
        
        self.period_cb = QComboBox()
        self.period_cb.addItems(["7 ngày tới", "14 ngày tới", "30 ngày tới"])
        self.period_cb.currentIndexChanged.connect(self.load_data)
        header.addWidget(self.period_cb)
        
        self.refresh_btn = QPushButton("🔄 Cập nhật dự báo")
        self.refresh_btn.setObjectName("primaryBtn")
        self.refresh_btn.clicked.connect(self.load_data)
        header.addWidget(self.refresh_btn)
        layout.addLayout(header)
        
        # Summary Cards
        cards_layout = QHBoxLayout()
        self.trend_card = self._create_card("📈 Xu hướng", "Tăng 12%", "So với tháng trước")
        self.peak_card = self._create_card("⚠️ Ngày cao điểm dự kiến", "Thứ Hai tới", "Cần tăng cường nhân sự")
        self.dept_card = self._create_card("🏥 Khoa quá tải dự kiến", "Khoa Nội", "Cần thêm nhân sự")
        cards_layout.addWidget(self.trend_card)
        cards_layout.addWidget(self.peak_card)
        cards_layout.addWidget(self.dept_card)
        layout.addLayout(cards_layout)

        # Content Table
        layout.addWidget(QLabel("Chi tiết dự báo theo khoa:"))
        self.table = QTableWidget()
        cols = ["Ngày dự báo", "Khoa", "Lượng bệnh nhân dự kiến", "Mức độ tải", "Khuyến nghị nhân sự"]
        self.table.setColumnCount(len(cols))
        self.table.setHorizontalHeaderLabels(cols)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        layout.addWidget(self.table)

    def _create_card(self, title, value, subtitle):
        card = QFrame()
        card.setObjectName("summaryCard")
        cl = QVBoxLayout(card)
        t_lbl = QLabel(title)
        t_lbl.setObjectName("cardTitle")
        v_lbl = QLabel(value)
        v_lbl.setObjectName("cardValue")
        s_lbl = QLabel(subtitle)
        s_lbl.setObjectName("cardSubtitle")
        cl.addWidget(t_lbl)
        cl.addWidget(v_lbl)
        cl.addWidget(s_lbl)
        return card

    def load_data(self):
        days_map = {0: 7, 1: 14, 2: 30}
        days = days_map[self.period_cb.currentIndex()]
        
        departments = ["Khoa Nội", "Khoa Ngoại", "Khoa Nhi", "Khoa Sản", "Khoa Cấp cứu"]
        base_volumes = {"Khoa Nội": 45, "Khoa Ngoại": 20, "Khoa Nhi": 35, "Khoa Sản": 15, "Khoa Cấp cứu": 50}
        
        predictions = []
        current_date = QDate.currentDate()
        
        for d in range(1, days + 1):
            target_date = current_date.addDays(d)
            # Simulate weekend drop
            day_of_week = target_date.dayOfWeek()
            multiplier = 0.7 if day_of_week > 5 else 1.0
            if day_of_week == 1:  # Monday peak
                multiplier = 1.3
                
            for dept in departments:
                # Add some random noise
                vol = int(base_volumes[dept] * multiplier * random.uniform(0.8, 1.2))
                
                status = "Bình thường"
                recommendation = "Giữ nguyên"
                if vol > base_volumes[dept] * 1.2:
                    status = "Quá tải"
                    recommendation = "Tăng cường 1-2 BS"
                elif vol < base_volumes[dept] * 0.7:
                    status = "Thấp"
                    recommendation = "Có thể giảm ca"
                    
                predictions.append({
                    "date": target_date.toString("dd/MM/yyyy"),
                    "dept": dept,
                    "volume": vol,
                    "status": status,
                    "recommendation": recommendation
                })
                
        self.table.setRowCount(len(predictions))
        for r, p in enumerate(predictions):
            self.table.setItem(r, 0, QTableWidgetItem(p["date"]))
            self.table.setItem(r, 1, QTableWidgetItem(p["dept"]))
            self.table.setItem(r, 2, QTableWidgetItem(str(p["volume"])))
            
            status_item = QTableWidgetItem(p["status"])
            if p["status"] == "Quá tải":
                status_item.setForeground(QColor("#c53030"))
            elif p["status"] == "Bình thường":
                status_item.setForeground(QColor("#276749"))
            self.table.setItem(r, 3, status_item)
            self.table.setItem(r, 4, QTableWidgetItem(p["recommendation"]))

    def _apply_style(self):
        self.setStyleSheet("""
        QWidget { background: #f7fafc; font-family: 'Segoe UI'; }
        #sectionTitle { color: #1a365d; }
        #primaryBtn {
            background: #2b6cb0; color: white; border: none;
            border-radius: 7px; padding: 9px 16px; font-weight: 600; font-size: 12px;
        }
        #primaryBtn:hover { background: #2c5282; }
        QComboBox {
            border: 1.5px solid #cbd5e0; border-radius: 6px;
            padding: 6px 12px; font-size: 12px; background: white;
        }
        QTableWidget { border: 1px solid #e2e8f0; font-size: 12px; border-radius: 8px; }
        QHeaderView::section { background: #edf2f7; font-weight: 600; padding: 8px; border: none; }
        
        #summaryCard {
            background: white; border-radius: 12px; border: 1px solid #e2e8f0;
            padding: 4px;
        }
        #cardTitle { font-size: 13px; color: #718096; font-weight: bold; }
        #cardValue { font-size: 22px; color: #2b6cb0; font-weight: bold; }
        #cardSubtitle { font-size: 11px; color: #a0aec0; }
        """)
