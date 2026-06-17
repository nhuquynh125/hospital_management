from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QCalendarWidget, QFrame,
    QHBoxLayout, QTableWidget, QTableWidgetItem, QHeaderView
)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QFont
from database.schema import get_connection
import core.auth as auth

class ShiftScheduleTab(QWidget):
    def __init__(self):
        super().__init__()
        self._build_ui()
        self._load_data()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)

        title = QLabel("📅 Lịch Trực Của Tôi")
        title.setFont(QFont("Segoe UI", 24, QFont.Weight.Bold))
        title.setStyleSheet("color: #2b6cb0;")
        layout.addWidget(title)

        content_layout = QHBoxLayout()
        layout.addLayout(content_layout)

        # Calendar
        self.calendar = QCalendarWidget()
        self.calendar.setGridVisible(True)
        self.calendar.setStyleSheet("""
            QCalendarWidget QWidget { alternate-background-color: #edf2f7; }
            QCalendarWidget QAbstractItemView:enabled { font-size: 14px; color: #2d3748; selection-background-color: #3182ce; selection-color: white; }
        """)
        content_layout.addWidget(self.calendar, 1)

        # Details table
        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["Ngày", "Ca Trực", "Ghi Chú"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setStyleSheet("""
            QTableWidget { background: white; border: 1px solid #e2e8f0; border-radius: 8px; }
            QHeaderView::section { background: #ebf8ff; font-weight: bold; padding: 4px; border: none; }
        """)
        content_layout.addWidget(self.table, 1)

        self.schedule_label = QLabel()
        self.schedule_label.setFont(QFont("Segoe UI", 12))
        self.schedule_label.setWordWrap(True)
        self.schedule_label.setStyleSheet("background: #ebf8ff; padding: 15px; border-radius: 8px; border: 1px solid #bee3f8; color: #2c5282;")
        layout.addWidget(self.schedule_label)

    def _load_data(self):
        user = auth.get_current_user()
        if not user:
            return

        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT full_name, work_schedule, department_id FROM staff WHERE user_id = ?", (user['id'],))
        row = cur.fetchone()
        
        if row:
            schedule = row['work_schedule'] or "Chưa có lịch trực cố định."
            self.schedule_label.setText(f"Ghi chú lịch trực: {schedule}")

            # Demo some shifts based on user ID
            import random
            random.seed(user['id'])
            
            self.table.setRowCount(0)
            current_date = QDate.currentDate()
            start_date = QDate(current_date.year(), current_date.month(), 1)
            days_in_month = current_date.daysInMonth()
            
            row_idx = 0
            for i in range(days_in_month):
                date = start_date.addDays(i)
                # Randomize shifts
                if random.random() < 0.3:
                    shift = random.choice(["Sáng (07:00 - 15:00)", "Chiều (15:00 - 23:00)", "Đêm (23:00 - 07:00)"])
                    self.table.insertRow(row_idx)
                    self.table.setItem(row_idx, 0, QTableWidgetItem(date.toString("dd/MM/yyyy")))
                    self.table.setItem(row_idx, 1, QTableWidgetItem(shift))
                    self.table.setItem(row_idx, 2, QTableWidgetItem("Trực chính" if random.random() < 0.5 else "Trực phụ"))
                    row_idx += 1
        else:
            self.schedule_label.setText("Không tìm thấy thông tin nhân viên.")
            
        conn.close()
