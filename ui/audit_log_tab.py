from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, Http, QHBoxLayout, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QLabel
)
from PyQt6.QtGui import QFont, QColor
from PyQt6.QtCore import Qt
from database.dao import get_audit_logs

class AuditLogTab(QWidget):
    def __init__(self):
        super().__init__()
        self._build_ui()
        self.load_data()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Header
        header = QHBoxLayout()
        title = QLabel("🛡️ Audit Trail (Log Hệ Thống)")
        title.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        title.setStyleSheet("color: #1a365d;")
        header.addWidget(title)
        
        refresh_btn = QPushButton("🔄 Làm mới")
        refresh_btn.setFixedWidth(100)
        refresh_btn.clicked.connect(self.load_data)
        header.addWidget(refresh_btn, alignment=Qt.AlignmentFlag.AlignRight)
        layout.addLayout(header)

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            "ID", "Thời gian", "Người dùng", "Hành động", 
            "Bảng", "Record ID", "Giá trị cũ", "Giá trị mới"
        ])
        
        header_view = self.table.horizontalHeader()
        header_view.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header_view.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header_view.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header_view.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header_view.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        header_view.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        header_view.setSectionResizeMode(6, QHeaderView.ResizeMode.Stretch)
        header_view.setSectionResizeMode(7, QHeaderView.ResizeMode.Stretch)

        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        
        layout.addWidget(self.table)

    def load_data(self):
        self.table.setRowCount(0)
        logs = get_audit_logs(limit=200)
        
        for row_idx, log in enumerate(logs):
            self.table.insertRow(row_idx)
            self.table.setItem(row_idx, 0, QTableWidgetItem(str(log["id"])))
            self.table.setItem(row_idx, 1, QTableWidgetItem(log["timestamp"] or ""))
            self.table.setItem(row_idx, 2, QTableWidgetItem(log["username"] or f"UID:{log['user_id']}"))
            self.table.setItem(row_idx, 3, QTableWidgetItem(log["action"] or ""))
            self.table.setItem(row_idx, 4, QTableWidgetItem(log["table_name"] or ""))
            self.table.setItem(row_idx, 5, QTableWidgetItem(str(log["record_id"]) if log["record_id"] else ""))
            self.table.setItem(row_idx, 6, QTableWidgetItem(str(log["old_value"]) if log["old_value"] else ""))
            self.table.setItem(row_idx, 7, QTableWidgetItem(str(log["new_value"]) if log["new_value"] else ""))

            # Optional coloring based on action
            action = log["action"]
            color = None
            if action in ("UPDATE", "EDIT"):
                color = QColor("#fdf6e3")
            elif action in ("DELETE", "CANCEL"):
                color = QColor("#fee2e2")
            elif action in ("INSERT", "ADD", "CREATE"):
                color = QColor("#dcfce7")
            elif action in ("LOGIN", "LOGOUT"):
                color = QColor("#e0f2fe")
            
            if color:
                for col in range(8):
                    item = self.table.item(row_idx, col)
                    if item:
                        item.setBackground(color)
