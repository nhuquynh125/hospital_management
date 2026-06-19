from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QCalendarWidget, QFrame,
    QHBoxLayout, QTableWidget, QTableWidgetItem, QHeaderView,
    QPushButton, QDialog, QFormLayout, QDateEdit, QComboBox, QLineEdit, QMessageBox
)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QFont
from database.schema import get_connection
import database.dao as dao
import core.auth as auth

class ShiftDialog(QDialog):
    def __init__(self, parent=None, schedule=None):
        super().__init__(parent)
        self.setWindowTitle("Thông tin Lịch Trực")
        self.setFixedSize(350, 250)
        self.schedule = schedule

        layout = QFormLayout(self)
        self.date_edit = QDateEdit()
        self.date_edit.setCalendarPopup(True)
        if self.schedule:
            self.date_edit.setDate(QDate.fromString(self.schedule['shift_date'], "yyyy-MM-dd"))
        else:
            self.date_edit.setDate(QDate.currentDate())
        
        self.shift_combo = QComboBox()
        self.shift_combo.addItems(["Sáng", "Chiều", "Đêm"])
        if self.schedule:
            self.shift_combo.setCurrentText(self.schedule['shift_type'])
            
        self.note_edit = QLineEdit()
        if self.schedule:
            self.note_edit.setText(self.schedule['notes'])
            
        layout.addRow("Ngày trực:", self.date_edit)
        layout.addRow("Ca trực:", self.shift_combo)
        layout.addRow("Ghi chú:", self.note_edit)
        
        btn_layout = QHBoxLayout()
        save_btn = QPushButton("Lưu")
        save_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton("Hủy")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addRow(btn_layout)
        
    def get_data(self):
        return {
            "shift_date": self.date_edit.date().toString("yyyy-MM-dd"),
            "shift_type": self.shift_combo.currentText(),
            "notes": self.note_edit.text()
        }

class ShiftScheduleTab(QWidget):
    def __init__(self):
        super().__init__()
        self.user = auth.get_current_user()
        self.staff_profile = dao.get_staff_profile(self.user['id']) if self.user else None
        self._build_ui()
        self._load_data()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)

        header_layout = QHBoxLayout()
        title = QLabel("📅 Lịch Trực Của Tôi")
        title.setFont(QFont("Segoe UI", 24, QFont.Weight.Bold))
        title.setStyleSheet("color: #2b6cb0;")
        header_layout.addWidget(title)
        header_layout.addStretch()
        
        self.add_btn = QPushButton("➕ Thêm Lịch Trực")
        self.add_btn.setStyleSheet("background: #3182ce; color: white; padding: 8px 16px; border-radius: 4px; font-weight: bold;")
        self.add_btn.clicked.connect(self._add_shift)
        self.edit_btn = QPushButton("✏️ Sửa Lịch Trực")
        self.edit_btn.setStyleSheet("background: #ecc94b; color: white; padding: 8px 16px; border-radius: 4px; font-weight: bold;")
        self.edit_btn.clicked.connect(self._edit_shift)
        self.delete_btn = QPushButton("❌ Xóa Lịch Trực")
        self.delete_btn.setStyleSheet("background: #e53e3e; color: white; padding: 8px 16px; border-radius: 4px; font-weight: bold;")
        self.delete_btn.clicked.connect(self._delete_shift)
        
        header_layout.addWidget(self.add_btn)
        header_layout.addWidget(self.edit_btn)
        header_layout.addWidget(self.delete_btn)
        layout.addLayout(header_layout)

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
        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["ID", "Ngày", "Ca Trực", "Ghi Chú"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setColumnHidden(0, True) # Hide ID column
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
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
        if not self.staff_profile:
            self.schedule_label.setText("Không tìm thấy thông tin nhân viên.")
            self.add_btn.setEnabled(False)
            self.edit_btn.setEnabled(False)
            self.delete_btn.setEnabled(False)
            return

        schedule = self.staff_profile['work_schedule'] or "Chưa có lịch trực cố định."
        self.schedule_label.setText(f"Ghi chú lịch trực chung: {schedule}")

        self.table.setRowCount(0)
        shifts = dao.get_shift_schedules_for_staff(self.staff_profile['id'])
        for shift in shifts:
            row_idx = self.table.rowCount()
            self.table.insertRow(row_idx)
            self.table.setItem(row_idx, 0, QTableWidgetItem(str(shift['id'])))
            
            # Format date for display
            date_obj = QDate.fromString(shift['shift_date'], "yyyy-MM-dd")
            self.table.setItem(row_idx, 1, QTableWidgetItem(date_obj.toString("dd/MM/yyyy")))
            
            self.table.setItem(row_idx, 2, QTableWidgetItem(shift['shift_type']))
            self.table.setItem(row_idx, 3, QTableWidgetItem(shift['notes'] or ""))

    def _add_shift(self):
        if not self.staff_profile: return
        dialog = ShiftDialog(self)
        if dialog.exec():
            data = dialog.get_data()
            dao.create_shift_schedule(self.staff_profile['id'], data['shift_date'], data['shift_type'], data['notes'])
            self._load_data()

    def _edit_shift(self):
        selected = self.table.selectedItems()
        if not selected:
            QMessageBox.warning(self, "Lỗi", "Vui lòng chọn một lịch trực để sửa.")
            return
            
        row = selected[0].row()
        schedule_id = int(self.table.item(row, 0).text())
        
        # We need to construct a schedule dict to pass to dialog
        date_str = QDate.fromString(self.table.item(row, 1).text(), "dd/MM/yyyy").toString("yyyy-MM-dd")
        schedule = {
            'id': schedule_id,
            'shift_date': date_str,
            'shift_type': self.table.item(row, 2).text(),
            'notes': self.table.item(row, 3).text()
        }
        
        dialog = ShiftDialog(self, schedule)
        if dialog.exec():
            data = dialog.get_data()
            dao.update_shift_schedule(schedule_id, data['shift_date'], data['shift_type'], data['notes'])
            self._load_data()

    def _delete_shift(self):
        selected = self.table.selectedItems()
        if not selected:
            QMessageBox.warning(self, "Lỗi", "Vui lòng chọn một lịch trực để xóa.")
            return
            
        row = selected[0].row()
        schedule_id = int(self.table.item(row, 0).text())
        
        reply = QMessageBox.question(self, "Xác nhận", "Bạn có chắc chắn muốn xóa lịch trực này?", 
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        
        if reply == QMessageBox.StandardButton.Yes:
            dao.delete_shift_schedule(schedule_id)
            self._load_data()
