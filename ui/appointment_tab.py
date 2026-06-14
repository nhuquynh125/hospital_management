"""
Hospital Management System — Appointment Management Tab
Đặt / huỷ lịch hẹn, lịch tái khám, trạng thái khám
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView,
    QComboBox, QDialog, QFormLayout, QTextEdit, QMessageBox,
    QDateEdit, QTimeEdit, QFrame, QScrollArea, QTabWidget
)
from PyQt6.QtCore import Qt, QDate, QTime
from PyQt6.QtGui import QFont, QColor

import database.dao as dao

STATUSES = ["Chờ", "Đang khám", "Hoàn thành", "Huỷ"]
STATUS_COLORS = {
    "Chờ":        ("#fff3cd", "#856404"),
    "Đang khám":  ("#cce5ff", "#004085"),
    "Hoàn thành": ("#d4edda", "#155724"),
    "Huỷ":        ("#f8d7da", "#721c24"),
}


# ═══════════════════════════════════════════════════════════
#  Appointment Form Dialog
# ═══════════════════════════════════════════════════════════
class AppointmentFormDialog(QDialog):
    def __init__(self, parent=None, appt_data=None, is_followup=False):
        super().__init__(parent)
        self.appt_data  = appt_data
        self.is_edit    = appt_data is not None
        self.is_followup = is_followup
        self.patients   = dao.get_all_patients()
        self.doctors    = dao.get_doctors()
        self.rooms      = dao.get_all_rooms()
        title = "Lịch tái khám" if is_followup else ("Sửa lịch hẹn" if self.is_edit else "Đặt lịch hẹn mới")
        self.setWindowTitle(title)
        self.setMinimumWidth(480)
        self.setModal(True)
        self._build_ui()
        if self.is_edit:
            self._fill_form()
        self._apply_style()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        icon = "🔁" if self.is_followup else ("✏️" if self.is_edit else "📅")
        title_str = "Lịch tái khám" if self.is_followup else ("Sửa lịch hẹn" if self.is_edit else "Đặt lịch hẹn mới")
        title = QLabel(f"{icon} {title_str}")
        title.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        title.setObjectName("dlgTitle")
        layout.addWidget(title)

        form = QFormLayout()
        form.setSpacing(10)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        # Patient selector
        self.f_patient = QComboBox()
        self.f_patient.setEditable(True)
        self.f_patient.lineEdit().setPlaceholderText("Chọn hoặc tìm bệnh nhân...")
        for p in self.patients:
            self.f_patient.addItem(f"{p['patient_code']} — {p['full_name']}", p["id"])

        # Doctor selector
        self.f_doctor = QComboBox()
        self.f_doctor.addItem("-- Chọn bác sĩ --", None)
        for d in self.doctors:
            spec = f" ({d['specialization']})" if d["specialization"] else ""
            self.f_doctor.addItem(f"{d['full_name']}{spec}", d["id"])

        # Room selector
        self.f_room = QComboBox()
        self.f_room.addItem("-- Chọn phòng khám --", None)
        for r in self.rooms:
            if r["room_type"] == "Khám" or r["status"] == "Trống":
                self.f_room.addItem(f"Phòng {r['room_number']} — {r['room_type']}", r["id"])

        self.f_date = QDateEdit()
        self.f_date.setCalendarPopup(True)
        self.f_date.setDisplayFormat("dd/MM/yyyy")
        self.f_date.setDate(QDate.currentDate().addDays(1))
        self.f_date.setMinimumDate(QDate.currentDate())

        self.f_time = QTimeEdit()
        self.f_time.setDisplayFormat("HH:mm")
        self.f_time.setTime(QTime(8, 0))

        self.f_reason = QLineEdit()
        self.f_reason.setPlaceholderText("Lý do khám / triệu chứng ban đầu")

        self.f_status = QComboBox()
        self.f_status.addItems(STATUSES)

        self.f_notes = QTextEdit()
        self.f_notes.setMaximumHeight(60)
        self.f_notes.setPlaceholderText("Ghi chú thêm...")

        form.addRow("Bệnh nhân *:", self.f_patient)
        form.addRow("Bác sĩ *:",    self.f_doctor)
        form.addRow("Phòng khám:",  self.f_room)
        form.addRow("Ngày hẹn *:",  self.f_date)
        form.addRow("Giờ hẹn *:",   self.f_time)
        form.addRow("Lý do:",       self.f_reason)
        form.addRow("Trạng thái:",  self.f_status)
        form.addRow("Ghi chú:",     self.f_notes)
        layout.addLayout(form)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        self.cancel_btn = QPushButton("Huỷ");  self.cancel_btn.setObjectName("cancelBtn")
        self.save_btn   = QPushButton("Lưu");  self.save_btn.setObjectName("saveBtn")
        self.cancel_btn.clicked.connect(self.reject)
        self.save_btn.clicked.connect(self._save)
        btn_row.addWidget(self.cancel_btn)
        btn_row.addWidget(self.save_btn)
        layout.addLayout(btn_row)

    def _fill_form(self):
        a = self.appt_data
        for i in range(self.f_patient.count()):
            if self.f_patient.itemData(i) == a["patient_id"]:
                self.f_patient.setCurrentIndex(i); break
        for i in range(self.f_doctor.count()):
            if self.f_doctor.itemData(i) == a["doctor_id"]:
                self.f_doctor.setCurrentIndex(i); break
        if a["room_id"]:
            for i in range(self.f_room.count()):
                if self.f_room.itemData(i) == a["room_id"]:
                    self.f_room.setCurrentIndex(i); break
        if a["appointment_date"]:
            d = QDate.fromString(a["appointment_date"], "yyyy-MM-dd")
            if d.isValid(): self.f_date.setDate(d)
        if a["appointment_time"]:
            t = QTime.fromString(a["appointment_time"], "HH:mm")
            if t.isValid(): self.f_time.setTime(t)
        self.f_reason.setText(a["reason"] or "")
        idx = self.f_status.findText(a["status"] or "Chờ")
        if idx >= 0: self.f_status.setCurrentIndex(idx)
        self.f_notes.setPlainText(a["notes"] or "")

    def _save(self):
        patient_id = self.f_patient.currentData()
        doctor_id  = self.f_doctor.currentData()
        if not patient_id:
            QMessageBox.warning(self, "Thiếu thông tin", "Vui lòng chọn bệnh nhân.")
            return
        if not doctor_id:
            QMessageBox.warning(self, "Thiếu thông tin", "Vui lòng chọn bác sĩ.")
            return
        self.result_data = {
            "patient_id":       patient_id,
            "doctor_id":        doctor_id,
            "room_id":          self.f_room.currentData(),
            "appointment_date": self.f_date.date().toString("yyyy-MM-dd"),
            "appointment_time": self.f_time.time().toString("HH:mm"),
            "reason":           self.f_reason.text().strip(),
            "status":           self.f_status.currentText(),
            "is_followup":      1 if self.is_followup else 0,
            "notes":            self.f_notes.toPlainText().strip(),
        }
        self.accept()

    def _apply_style(self):
        self.setStyleSheet("""
        QDialog { background: #f7fafc; }
        #dlgTitle { color: #2d3748; margin-bottom: 4px; }
        QLineEdit, QTextEdit, QComboBox, QDateEdit, QTimeEdit {
            border: 1.5px solid #cbd5e0; border-radius: 6px;
            padding: 6px 8px; font-size: 12px; background: white;
        }
        QLabel { font-size: 12px; color: #4a5568; }
        #saveBtn {
            background: #2b6cb0; color: white; border: none;
            border-radius: 6px; padding: 8px 20px; font-weight: 600;
        }
        #saveBtn:hover { background: #2c5282; }
        #cancelBtn {
            background: #e2e8f0; color: #4a5568; border: none;
            border-radius: 6px; padding: 8px 20px;
        }
        """)


# ═══════════════════════════════════════════════════════════
#  Main Appointment Tab
# ═══════════════════════════════════════════════════════════
class AppointmentTab(QWidget):
    def __init__(self):
        super().__init__()
        self._build_ui()
        self._apply_style()
        self.load_data()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        # Header
        header_row = QHBoxLayout()
        title = QLabel("🗓️ Quản lý lịch hẹn")
        title.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        title.setObjectName("sectionTitle")
        header_row.addWidget(title)
        header_row.addStretch()

        self.add_btn      = QPushButton("➕ Đặt lịch hẹn")
        self.followup_btn = QPushButton("🔁 Lịch tái khám")
        self.add_btn.setObjectName("primaryBtn")
        self.followup_btn.setObjectName("secondaryBtn")
        self.add_btn.clicked.connect(self._add_appointment)
        self.followup_btn.clicked.connect(self._add_followup)
        header_row.addWidget(self.add_btn)
        header_row.addWidget(self.followup_btn)
        layout.addLayout(header_row)

        # Filters
        filter_row = QHBoxLayout()
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("🔍  Tìm theo tên bệnh nhân, bác sĩ")
        self.search_box.setObjectName("searchBox")
        self.search_box.textChanged.connect(self.load_data)

        self.date_filter = QDateEdit()
        self.date_filter.setCalendarPopup(True)
        self.date_filter.setDisplayFormat("dd/MM/yyyy")
        self.date_filter.setDate(QDate.currentDate())
        self.date_filter.dateChanged.connect(self.load_data)

        self.status_cb = QComboBox()
        self.status_cb.addItems(["Tất cả trạng thái"] + STATUSES)
        self.status_cb.currentIndexChanged.connect(self.load_data)

        self.today_btn = QPushButton("📅 Hôm nay")
        self.today_btn.setObjectName("clearBtn")
        self.today_btn.clicked.connect(lambda: self.date_filter.setDate(QDate.currentDate()))

        self.all_btn = QPushButton("Tất cả ngày")
        self.all_btn.setObjectName("clearBtn")
        self.all_btn.setCheckable(True)
        self.all_btn.toggled.connect(self.load_data)

        filter_row.addWidget(self.search_box, 2)
        filter_row.addWidget(self.date_filter)
        filter_row.addWidget(self.today_btn)
        filter_row.addWidget(self.all_btn)
        filter_row.addWidget(self.status_cb)
        layout.addLayout(filter_row)

        self.count_lbl = QLabel()
        self.count_lbl.setObjectName("countLabel")
        layout.addWidget(self.count_lbl)

        # Table
        self.table = QTableWidget()
        cols = ["Mã", "Bệnh nhân", "Bác sĩ", "Phòng", "Ngày hẹn",
                "Giờ", "Lý do", "Tái khám", "Trạng thái"]
        self.table.setColumnCount(len(cols))
        self.table.setHorizontalHeaderLabels(cols)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        layout.addWidget(self.table)

        # Actions
        action_row = QHBoxLayout()
        btn_specs = [
            ("✏️ Sửa",        "actionBtn",  self._edit_appointment),
            ("✅ Hoàn thành", "successBtn", self._mark_done),
            ("❌ Huỷ lịch",  "dangerBtn",  self._cancel_appointment),
        ]
        for label, obj, handler in btn_specs:
            btn = QPushButton(label)
            btn.setObjectName(obj)
            btn.clicked.connect(handler)
            action_row.addWidget(btn)
        action_row.addStretch()
        layout.addLayout(action_row)

    def load_data(self):
        search  = self.search_box.text().strip()
        status  = self.status_cb.currentText()
        all_days = self.all_btn.isChecked()
        date_str = None if all_days else self.date_filter.date().toString("yyyy-MM-dd")
        if status == "Tất cả trạng thái": status = ""

        rows = dao.get_all_appointments(search, status, date_str)
        self.table.setRowCount(len(rows))
        for r, a in enumerate(rows):
            is_fu = "🔁 Có" if a["is_followup"] else ""
            vals = [str(a["id"]), a["patient_name"] or "", a["doctor_name"] or "",
                    a["room_number"] or "", a["appointment_date"] or "",
                    a["appointment_time"] or "", a["reason"] or "",
                    is_fu, a["status"] or ""]
            for c, v in enumerate(vals):
                item = QTableWidgetItem(v)
                item.setData(Qt.ItemDataRole.UserRole.value, a["id"])
                if c == 8:  # status column colour
                    bg, fg = STATUS_COLORS.get(v, ("#ffffff", "#000000"))
                    item.setBackground(QColor(bg))
                    item.setForeground(QColor(fg))
                self.table.setItem(r, c, item)
        self.count_lbl.setText(f"Tìm thấy {len(rows)} lịch hẹn")

    def _selected_id(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.information(self, "Chưa chọn", "Vui lòng chọn một lịch hẹn.")
            return None
        return self.table.item(row, 0).data(Qt.ItemDataRole.UserRole.value)

    def _add_appointment(self):
        dlg = AppointmentFormDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            dao.add_appointment(dlg.result_data)
            self.load_data()

    def _add_followup(self):
        aid = self._selected_id()
        if not aid: return
        a = dao.get_appointment_by_id(aid)
        dlg = AppointmentFormDialog(self, appt_data=a, is_followup=True)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            dlg.result_data["parent_appointment_id"] = aid
            dao.add_appointment(dlg.result_data)
            self.load_data()

    def _edit_appointment(self):
        aid = self._selected_id()
        if not aid: return
        a = dao.get_appointment_by_id(aid)
        dlg = AppointmentFormDialog(self, appt_data=a)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            dao.update_appointment(aid, dlg.result_data)
            self.load_data()

    def _mark_done(self):
        aid = self._selected_id()
        if not aid: return
        dao.update_appointment_status(aid, "Hoàn thành")
        self.load_data()

    def _cancel_appointment(self):
        aid = self._selected_id()
        if not aid: return
        reply = QMessageBox.question(self, "Huỷ lịch hẹn",
                                     "Xác nhận huỷ lịch hẹn này?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            dao.update_appointment_status(aid, "Huỷ")
            self.load_data()

    def _apply_style(self):
        self.setStyleSheet("""
        QWidget { background: #f7fafc; font-family: 'Segoe UI'; }
        #sectionTitle { color: #1a365d; }
        #searchBox {
            border: 1.5px solid #cbd5e0; border-radius: 8px;
            padding: 8px 12px; font-size: 13px; background: white;
        }
        QComboBox, QDateEdit {
            border: 1.5px solid #cbd5e0; border-radius: 6px;
            padding: 6px 8px; font-size: 12px; background: white;
        }
        #primaryBtn {
            background: #2b6cb0; color: white; border: none;
            border-radius: 7px; padding: 8px 16px; font-weight: 600;
        }
        #primaryBtn:hover { background: #2c5282; }
        #secondaryBtn {
            background: #553c9a; color: white; border: none;
            border-radius: 7px; padding: 8px 16px; font-weight: 600;
        }
        #secondaryBtn:hover { background: #44337a; }
        #actionBtn {
            background: #edf2f7; color: #2d3748; border: none;
            border-radius: 6px; padding: 7px 14px; font-size: 12px;
        }
        #successBtn {
            background: #f0fff4; color: #276749; border: 1px solid #9ae6b4;
            border-radius: 6px; padding: 7px 14px; font-size: 12px;
        }
        #dangerBtn {
            background: #fff5f5; color: #c53030; border: 1px solid #fed7d7;
            border-radius: 6px; padding: 7px 14px; font-size: 12px;
        }
        #clearBtn {
            background: transparent; color: #718096; border: 1px solid #cbd5e0;
            border-radius: 6px; padding: 6px 10px; font-size: 12px;
        }
        #examBtn {
            background: #276749; color: white; border: none;
            border-radius: 7px; padding: 8px 18px; font-weight: 700; font-size: 13px;
        }
        #examBtn:hover { background: #22543d; }
        #countLabel { color: #718096; font-size: 12px; }
        QTableWidget {
            border: 1px solid #e2e8f0; border-radius: 8px;
            font-size: 12px; gridline-color: #f0f0f0;
        }
        QHeaderView::section {
            background: #edf2f7; font-weight: 600; padding: 8px; border: none;
        }
        """)


    def _start_examination(self):
        """Mở màn hình khám bệnh tích hợp cho lịch hẹn được chọn."""
        aid = self._selected_id()
        if not aid:
            return
        a = dao.get_appointment_by_id(aid)
        if a["status"] == "Huỷ":
            QMessageBox.warning(self, "Không thể khám",
                                "Lịch hẹn này đã bị huỷ.")
            return
        if a["status"] == "Hoàn thành":
            reply = QMessageBox.question(
                self, "Lịch đã hoàn thành",
                "Lịch hẹn này đã hoàn thành.\n"
                "Bạn có muốn mở lại để chỉnh sửa không?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply != QMessageBox.StandardButton.Yes:
                return

        # Mark as 'Đang khám'
        dao.update_appointment_status(aid, "Đang khám")
        self.load_data()

        from ui.examination_dialog import ExaminationDialog
        dlg = ExaminationDialog(
            patient_id=a["patient_id"],
            appointment_id=aid,
            parent=self
        )
        dlg.exec()
        self.load_data()   # refresh after save
