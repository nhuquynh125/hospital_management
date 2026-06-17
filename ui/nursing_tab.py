import json
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView,
    QComboBox, QDialog, QFormLayout, QTextEdit, QMessageBox,
    QDateTimeEdit, QDoubleSpinBox, QSpinBox, QFrame, QGroupBox
)
from PyQt6.QtCore import Qt, QDateTime
from PyQt6.QtGui import QFont

import database.dao as dao
import core.auth as auth


class NursingNoteDialog(QDialog):
    def __init__(self, parent=None, note_data=None):
        super().__init__(parent)
        self.note_data = note_data
        self.is_edit = note_data is not None
        self.patients = dao.get_all_patients()
        self.setWindowTitle("Ghi chú chăm sóc" if not self.is_edit else "Sửa ghi chú")
        self.setMinimumWidth(500)
        self.setModal(True)
        self._build_ui()
        if self.is_edit:
            self._fill_form()
        self._apply_style()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        title = QLabel("🩺 Ghi chú chăm sóc điều dưỡng")
        title.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        title.setObjectName("dlgTitle")
        layout.addWidget(title)

        form = QFormLayout()
        form.setSpacing(10)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        # Patient
        self.f_patient = QComboBox()
        self.f_patient.setEditable(True)
        self.f_patient.lineEdit().setPlaceholderText("Chọn bệnh nhân...")
        for p in self.patients:
            self.f_patient.addItem(f"{p['patient_code']} — {p['full_name']}", p["id"])

        # Date/time
        self.f_datetime = QDateTimeEdit()
        self.f_datetime.setCalendarPopup(True)
        self.f_datetime.setDisplayFormat("dd/MM/yyyy HH:mm")
        self.f_datetime.setDateTime(QDateTime.currentDateTime())

        # Vital signs group
        vital_group = QGroupBox("📊 Dấu hiệu sinh tồn")
        vital_group.setObjectName("vitalGroup")
        vl = QFormLayout(vital_group)
        vl.setSpacing(8)

        self.f_temp   = QDoubleSpinBox(); self.f_temp.setRange(34, 42); self.f_temp.setValue(37.0)
        self.f_temp.setSingleStep(0.1); self.f_temp.setSuffix(" °C")
        self.f_bp     = QLineEdit(); self.f_bp.setPlaceholderText("VD: 120/80")
        self.f_pulse  = QSpinBox(); self.f_pulse.setRange(30,200); self.f_pulse.setValue(72)
        self.f_pulse.setSuffix(" lần/phút")
        self.f_spo2   = QSpinBox(); self.f_spo2.setRange(70,100); self.f_spo2.setValue(98)
        self.f_spo2.setSuffix(" %")
        self.f_resp   = QSpinBox(); self.f_resp.setRange(8,40); self.f_resp.setValue(18)
        self.f_resp.setSuffix(" lần/phút")

        vl.addRow("Nhiệt độ:",          self.f_temp)
        vl.addRow("Huyết áp:",          self.f_bp)
        vl.addRow("Mạch:",              self.f_pulse)
        vl.addRow("SpO2:",              self.f_spo2)
        vl.addRow("Nhịp thở:",         self.f_resp)

        # Care & status
        self.f_care   = QTextEdit(); self.f_care.setMaximumHeight(70)
        self.f_care.setPlaceholderText("Mô tả chăm sóc đã thực hiện: thay băng, truyền dịch, cho uống thuốc,...")
        self.f_status = QComboBox()
        self.f_status.addItems(["Ổn định","Cần theo dõi","Nặng","Nguy kịch","Xuất viện"])
        self.f_notes  = QTextEdit(); self.f_notes.setMaximumHeight(60)
        self.f_notes.setPlaceholderText("Ghi chú thêm...")

        form.addRow("Bệnh nhân *:", self.f_patient)
        form.addRow("Thời gian:",   self.f_datetime)
        layout.addLayout(form)
        layout.addWidget(vital_group)

        form2 = QFormLayout(); form2.setSpacing(10)
        form2.setLabelAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        form2.addRow("Chăm sóc thực hiện:", self.f_care)
        form2.addRow("Tình trạng BN:",       self.f_status)
        form2.addRow("Ghi chú:",             self.f_notes)
        layout.addLayout(form2)

        btn_row = QHBoxLayout(); btn_row.addStretch()
        self.cancel_btn = QPushButton("Huỷ"); self.cancel_btn.setObjectName("cancelBtn")
        self.save_btn   = QPushButton("Lưu"); self.save_btn.setObjectName("saveBtn")
        self.cancel_btn.clicked.connect(self.reject)
        self.save_btn.clicked.connect(self._save)
        btn_row.addWidget(self.cancel_btn); btn_row.addWidget(self.save_btn)
        layout.addLayout(btn_row)

    def _fill_form(self):
        n = self.note_data
        for i in range(self.f_patient.count()):
            if self.f_patient.itemData(i) == n["patient_id"]:
                self.f_patient.setCurrentIndex(i); break
        if n["note_date"]:
            dt = QDateTime.fromString(n["note_date"], "yyyy-MM-dd HH:mm:ss")
            if dt.isValid(): self.f_datetime.setDateTime(dt)
        try:
            vs = json.loads(n["vital_signs"] or "{}")
            self.f_temp.setValue(vs.get("temp", 37.0))
            self.f_bp.setText(vs.get("bp",""))
            self.f_pulse.setValue(vs.get("pulse", 72))
            self.f_spo2.setValue(vs.get("spo2", 98))
            self.f_resp.setValue(vs.get("resp", 18))
        except Exception:
            pass
        self.f_care.setPlainText(n["care_given"] or "")
        idx = self.f_status.findText(n["patient_status"] or "Ổn định")
        if idx >= 0: self.f_status.setCurrentIndex(idx)
        self.f_notes.setPlainText(n["notes"] or "")

    def _save(self):
        patient_id = self.f_patient.currentData()
        if not patient_id:
            QMessageBox.warning(self, "Thiếu thông tin", "Vui lòng chọn bệnh nhân.")
            return
        vital_signs = json.dumps({
            "temp":  self.f_temp.value(),
            "bp":    self.f_bp.text().strip(),
            "pulse": self.f_pulse.value(),
            "spo2":  self.f_spo2.value(),
            "resp":  self.f_resp.value(),
        })
        user = auth.get_current_user()
        nurse_staff_id = dao.get_staff_id_by_user_id(user["id"]) if user else None
        self.result_data = {
            "patient_id":     patient_id,
            "nurse_id":       nurse_staff_id,
            "note_date":      self.f_datetime.dateTime().toString("yyyy-MM-dd HH:mm:ss"),
            "vital_signs":    vital_signs,
            "care_given":     self.f_care.toPlainText().strip(),
            "patient_status": self.f_status.currentText(),
            "notes":          self.f_notes.toPlainText().strip(),
        }
        self.accept()

    def _apply_style(self):
        self.setStyleSheet("""
        QDialog { background: #f7fafc; }
        #dlgTitle { color: #2d3748; }
        QLineEdit, QTextEdit, QComboBox, QDateTimeEdit, QDoubleSpinBox, QSpinBox {
            border: 1.5px solid #cbd5e0; border-radius: 6px;
            padding: 6px 8px; font-size: 12px; background: white;
        }
        QLabel { font-size: 12px; color: #4a5568; }
        #vitalGroup { border: 1.5px solid #bee3f8; border-radius:8px; background:#ebf8ff; }
        #vitalGroup::title { color:#2b6cb0; font-weight:600; }
        #saveBtn { background:#276749; color:white; border:none; border-radius:6px; padding:8px 20px; font-weight:600; }
        #saveBtn:hover { background:#22543d; }
        #cancelBtn { background:#e2e8f0; color:#4a5568; border:none; border-radius:6px; padding:8px 20px; }
        """)


class NursingTab(QWidget):
    def __init__(self):
        super().__init__()
        self._build_ui()
        self._apply_style()
        self.load_data()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16,16,16,16)
        layout.setSpacing(10)

        header_row = QHBoxLayout()
        title = QLabel("🩺 Chăm sóc điều dưỡng")
        title.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        title.setObjectName("sectionTitle")
        header_row.addWidget(title)
        header_row.addStretch()
        self.add_btn = QPushButton("➕ Ghi chú mới")
        self.add_btn.setObjectName("primaryBtn")
        self.add_btn.clicked.connect(self._add_note)
        header_row.addWidget(self.add_btn)
        layout.addLayout(header_row)

        # Filter
        f_row = QHBoxLayout()
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("🔍  Tìm theo tên bệnh nhân")
        self.search_box.setObjectName("searchBox")
        self.search_box.textChanged.connect(self.load_data)
        self.status_cb = QComboBox()
        self.status_cb.addItems(["Tất cả tình trạng","Ổn định","Cần theo dõi","Nặng","Nguy kịch"])
        self.status_cb.currentIndexChanged.connect(self.load_data)
        f_row.addWidget(self.search_box, 2)
        f_row.addWidget(self.status_cb)
        layout.addLayout(f_row)

        self.count_lbl = QLabel(); self.count_lbl.setObjectName("countLabel")
        layout.addWidget(self.count_lbl)

        self.table = QTableWidget()
        cols = ["Bệnh nhân","Điều dưỡng","Thời gian","Nhiệt độ","Huyết áp","Mạch","SpO2","Tình trạng"]
        self.table.setColumnCount(len(cols))
        self.table.setHorizontalHeaderLabels(cols)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        layout.addWidget(self.table)

        a_row = QHBoxLayout()
        self.edit_btn = QPushButton("✏️ Sửa"); self.edit_btn.setObjectName("actionBtn")
        self.edit_btn.clicked.connect(self._edit_note)
        a_row.addWidget(self.edit_btn); a_row.addStretch()
        layout.addLayout(a_row)

    def load_data(self):
        search = self.search_box.text().strip()
        status = self.status_cb.currentText()
        if status == "Tất cả tình trạng": status = ""
        rows = dao.get_nursing_notes(search, status)
        self.table.setRowCount(len(rows))
        STATUS_COLORS = {
            "Ổn định":      ("#d4edda","#155724"),
            "Cần theo dõi": ("#fff3cd","#856404"),
            "Nặng":         ("#f8d7da","#721c24"),
            "Nguy kịch":    ("#f8d7da","#721c24"),
            "Xuất viện":    ("#e8f4f8","#2c7a7b"),  # soft teal — discharged
        }
        from PyQt6.QtGui import QColor
        for r, n in enumerate(rows):
            try:
                vs = json.loads(n["vital_signs"] or "{}")
            except Exception:
                vs = {}
            st = n["patient_status"] or ""
            vals = [
                n["patient_name"] or "", n["nurse_name"] or "",
                (n["note_date"] or "")[:16],
                f"{vs.get('temp','')} °C", vs.get("bp",""),
                f"{vs.get('pulse','')} lần/phút", f"{vs.get('spo2','')} %", st
            ]
            for c, v in enumerate(vals):
                item = QTableWidgetItem(str(v))
                item.setData(Qt.ItemDataRole.UserRole.value, n["id"])
                if c == 7 and st in STATUS_COLORS:
                    bg, fg = STATUS_COLORS[st]
                    item.setBackground(QColor(bg))
                    item.setForeground(QColor(fg))
                self.table.setItem(r, c, item)
        self.count_lbl.setText(f"Tổng: {len(rows)} ghi chú chăm sóc")

    def _add_note(self):
        dlg = NursingNoteDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            dao.add_nursing_note(dlg.result_data)
            self.load_data()

    def _edit_note(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.information(self, "Chưa chọn", "Vui lòng chọn một ghi chú.")
            return
        nid = self.table.item(row, 0).data(Qt.ItemDataRole.UserRole.value)
        n = dao.get_nursing_note_by_id(nid)
        dlg = NursingNoteDialog(self, note_data=n)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            dao.update_nursing_note(nid, dlg.result_data)
            self.load_data()

    def _apply_style(self):
        self.setStyleSheet("""
        QWidget { background:#f7fafc; font-family:'Segoe UI'; }
        #sectionTitle { color:#1a365d; }
        #searchBox { border:1.5px solid #cbd5e0; border-radius:8px; padding:8px 12px; font-size:13px; background:white; }
        QComboBox { border:1.5px solid #cbd5e0; border-radius:6px; padding:6px 8px; font-size:12px; background:white; }
        #primaryBtn { background:#276749; color:white; border:none; border-radius:7px; padding:8px 16px; font-weight:600; }
        #primaryBtn:hover { background:#22543d; }
        #actionBtn { background:#edf2f7; color:#2d3748; border:none; border-radius:6px; padding:7px 14px; font-size:12px; }
        #countLabel { color:#718096; font-size:12px; }
        QTableWidget { border:1px solid #e2e8f0; border-radius:8px; font-size:12px; }
        QHeaderView::section { background:#edf2f7; font-weight:600; padding:8px; border:none; }
        """)
