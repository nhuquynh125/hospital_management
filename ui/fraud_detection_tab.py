from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView, QProgressBar
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QColor
import random
import database.dao as dao

class FraudDetectionTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()
        self._apply_style()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # Header
        header = QHBoxLayout()
        title = QLabel("🛡️ Phát hiện Gian lận Bảo hiểm (AI)")
        title.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        title.setObjectName("sectionTitle")
        header.addWidget(title)
        header.addStretch()

        self.scan_btn = QPushButton("🔍 Quét Toàn bộ Hồ sơ")
        self.scan_btn.setObjectName("primaryBtn")
        self.scan_btn.clicked.connect(self._start_scan)
        header.addWidget(self.scan_btn)
        layout.addLayout(header)

        # Progress bar
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.progress.setTextVisible(True)
        self.progress.hide()
        layout.addWidget(self.progress)

        # Content Table
        self.table = QTableWidget()
        cols = ["Mã Hồ sơ", "Bệnh nhân", "Loại rủi ro", "Mô tả AI", "Điểm rủi ro", "Hành động"]
        self.table.setColumnCount(len(cols))
        self.table.setHorizontalHeaderLabels(cols)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        layout.addWidget(self.table)
        
        # Load initial empty or cached state
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._update_progress)
        self._scan_progress = 0

    def _start_scan(self):
        self.scan_btn.setEnabled(False)
        self.progress.setValue(0)
        self.progress.show()
        self.table.setRowCount(0)
        self._scan_progress = 0
        self._timer.start(30) # 30ms per tick

    def _update_progress(self):
        self._scan_progress += 2
        self.progress.setValue(self._scan_progress)
        
        if self._scan_progress >= 100:
            self._timer.stop()
            self.progress.hide()
            self.scan_btn.setEnabled(True)
            self._load_mock_data()

    def _load_mock_data(self):
        # Simulate AI detection results
        patients = dao.get_all_patients()
        if not patients:
            return
            
        anomalies = []
        anomaly_types = [
            ("Kê đơn quá mức", "Chỉ định kháng sinh 60 ngày cho bệnh lý thông thường."),
            ("Sai lệch chẩn đoán", "Chụp MRI não cho bệnh nhân bong gân mắt cá chân."),
            ("Tách gói dịch vụ (Unbundling)", "Thanh toán rời từng bước của một ca phẫu thuật trọn gói."),
            ("Upcoding", "Sử dụng mã thanh toán dịch vụ phức tạp cho ca bệnh nhẹ."),
            ("Dịch vụ ảo", "Tính phí vật lý trị liệu nhưng không có hồ sơ phiên làm việc.")
        ]
        
        num_anomalies = random.randint(3, 7)
        for _ in range(num_anomalies):
            patient = random.choice(patients)
            atype, desc = random.choice(anomaly_types)
            score = random.randint(60, 98)
            anomalies.append({
                "record_id": f"MR{random.randint(1000, 9999)}",
                "patient": patient["full_name"],
                "type": atype,
                "desc": desc,
                "score": score
            })
            
        anomalies.sort(key=lambda x: x["score"], reverse=True)
        
        self.table.setRowCount(len(anomalies))
        for r, a in enumerate(anomalies):
            self.table.setItem(r, 0, QTableWidgetItem(a["record_id"]))
            self.table.setItem(r, 1, QTableWidgetItem(a["patient"]))
            self.table.setItem(r, 2, QTableWidgetItem(a["type"]))
            self.table.setItem(r, 3, QTableWidgetItem(a["desc"]))
            
            score_item = QTableWidgetItem(f"{a['score']}/100")
            if a["score"] >= 80:
                score_item.setForeground(QColor("#c53030"))
            elif a["score"] >= 60:
                score_item.setForeground(QColor("#dd6b20"))
            self.table.setItem(r, 4, score_item)
            
            action_btn = QPushButton("Kiểm tra")
            action_btn.setObjectName("actionBtn")
            self.table.setCellWidget(r, 5, action_btn)

    def _apply_style(self):
        self.setStyleSheet("""
        QWidget { background: #f7fafc; font-family: 'Segoe UI'; }
        #sectionTitle { color: #1a365d; }
        #primaryBtn {
            background: #553c9a; color: white; border: none;
            border-radius: 7px; padding: 9px 16px; font-weight: 600; font-size: 12px;
        }
        #primaryBtn:hover { background: #44337a; }
        #primaryBtn:disabled { background: #a0aec0; }
        #actionBtn {
            background: #edf2f7; color: #2b6cb0; border: none;
            border-radius: 4px; padding: 4px 8px; font-size: 11px;
        }
        #actionBtn:hover { background: #e2e8f0; }
        QTableWidget { border: 1px solid #e2e8f0; font-size: 12px; border-radius: 8px; }
        QHeaderView::section { background: #edf2f7; font-weight: 600; padding: 8px; border: none; }
        QProgressBar { border: none; background: #e2e8f0; border-radius: 4px; text-align: center; color: transparent; }
        QProgressBar::chunk { background: #553c9a; border-radius: 4px; }
        """)
