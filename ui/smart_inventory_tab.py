from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QColor
import database.dao as dao

class SmartInventoryWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()
        self._apply_style()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)

        # Header
        header = QHBoxLayout()
        title = QLabel("🤖 Dự đoán Tồn kho & Đề xuất Nhập hàng (AI)")
        title.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        title.setObjectName("sectionTitle")
        header.addWidget(title)
        header.addStretch()
        
        self.analyze_btn = QPushButton("🔄 Phân tích & Dự đoán ngay")
        self.analyze_btn.setObjectName("primaryBtn")
        self.analyze_btn.clicked.connect(self.load_data)
        header.addWidget(self.analyze_btn)
        layout.addLayout(header)

        # Content Table
        self.table = QTableWidget()
        cols = ["Mã thuốc", "Tên thuốc", "Tồn kho hiện tại", "Dự báo cạn kiệt (ngày)", "Đề xuất nhập (đơn vị)", "Mức độ ưu tiên"]
        self.table.setColumnCount(len(cols))
        self.table.setHorizontalHeaderLabels(cols)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        layout.addWidget(self.table)

    def load_data(self):
        # Lấy dữ liệu thuốc và giả lập thuật toán AI dự báo
        try:
            medicines = dao.get_all_medicines()
        except Exception:
            return
            
        predictions = []
        for m in medicines:
            stock = m["stock_qty"] or 0
            min_stock = m["min_stock"] or 0
            
            # Giả lập heuristic cho AI: nếu kho nhỏ hơn 2 lần min_stock
            if stock <= min_stock * 2:
                # Giả sử tốc độ tiêu thụ trung bình là 2 đơn vị/ngày
                days_left = stock // 2 if stock > 0 else 0
                suggest_qty = max(min_stock * 3, 50)
                
                if days_left <= 3:
                    priority = "Cao"
                elif days_left <= 7:
                    priority = "Trung bình"
                else:
                    priority = "Thấp"
                    
                predictions.append({
                    "code": m.get("medicine_code", ""),
                    "name": m.get("name", ""),
                    "stock": stock,
                    "days_left": days_left,
                    "suggest": suggest_qty,
                    "priority": priority
                })
                
        # Sắp xếp theo số ngày dự kiến cạn kiệt
        predictions.sort(key=lambda x: x["days_left"])
        
        self.table.setRowCount(len(predictions))
        for r, p in enumerate(predictions):
            self.table.setItem(r, 0, QTableWidgetItem(p["code"]))
            self.table.setItem(r, 1, QTableWidgetItem(p["name"]))
            self.table.setItem(r, 2, QTableWidgetItem(str(p["stock"])))
            
            days_item = QTableWidgetItem(f"{p['days_left']} ngày")
            if p["days_left"] <= 3:
                days_item.setForeground(QColor("#c53030"))
            self.table.setItem(r, 3, days_item)
            
            self.table.setItem(r, 4, QTableWidgetItem(str(p["suggest"])))
            
            prio_item = QTableWidgetItem(p["priority"])
            if p["priority"] == "Cao":
                prio_item.setForeground(QColor("#c53030"))
            elif p["priority"] == "Trung bình":
                prio_item.setForeground(QColor("#dd6b20"))
            self.table.setItem(r, 5, prio_item)

    def _apply_style(self):
        self.setStyleSheet("""
        QWidget { background: #f7fafc; font-family: 'Segoe UI'; }
        #sectionTitle { color: #1a365d; }
        #primaryBtn {
            background: #553c9a; color: white; border: none;
            border-radius: 7px; padding: 9px 16px; font-weight: 600; font-size: 12px;
        }
        #primaryBtn:hover { background: #44337a; }
        QTableWidget { border: 1px solid #e2e8f0; font-size: 12px; border-radius: 8px; }
        QHeaderView::section { background: #edf2f7; font-weight: 600; padding: 8px; border: none; }
        """)
