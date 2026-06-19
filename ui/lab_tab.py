from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView,
    QComboBox, QDialog, QFormLayout, QTextEdit, QMessageBox,
    QDateTimeEdit, QFrame
)
from PyQt6.QtCore import Qt, QDateTime
from PyQt6.QtGui import QFont, QColor

import database.dao as dao
import core.auth as auth

TEST_TYPES = [
    "Công thức máu toàn phần (CBC)",
    "Sinh hoá máu",
    "Nước tiểu tổng quát",
    "Đường huyết",
    "HbA1c",
    "Chức năng gan (AST/ALT/GGT)",
    "Chức năng thận (BUN/Creatinine)",
    "Mỡ máu (Cholesterol/Triglycerides)",
    "X-quang ngực",
    "Siêu âm ổ bụng",
    "Điện tâm đồ (ECG)",
    "CT Scan",
    "MRI",
    "Xét nghiệm COVID-19",
    "Cấy vi khuẩn",
    "Khác",
]

STATUS_COLORS = {
    "Chờ":              ("#fff3cd","#856404"),
    "Đang xét nghiệm":  ("#cce5ff","#004085"),
    "Có kết quả":       ("#d4edda","#155724"),
    "Huỷ":              ("#f8d7da","#721c24"),
}


class LabTestDialog(QDialog):
    def __init__(self, parent=None, test_data=None, enter_result=False, view_only=False):
        super().__init__(parent)
        self.test_data   = test_data
        self.is_edit     = test_data is not None
        self.enter_result = enter_result
        self.view_only   = view_only
        self.patients    = dao.get_all_patients()
        self.doctors     = dao.get_doctors()
        title = "Xem kết quả" if view_only else ("Nhập kết quả" if enter_result else ("Sửa" if self.is_edit else "Chỉ định xét nghiệm"))
        self.setWindowTitle(title)
        self.setMinimumWidth(480)
        self.setModal(True)
        self._build_ui()
        if self.is_edit:
            self._fill_form()
        self._apply_style()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20,20,20,20)
        layout.setSpacing(12)

        icon = "👁️" if self.view_only else ("🔬" if self.enter_result else ("✏️" if self.is_edit else "➕"))
        title_str = "Xem kết quả xét nghiệm" if self.view_only else \
                    ("Nhập kết quả xét nghiệm" if self.enter_result else \
                    ("Sửa phiếu xét nghiệm" if self.is_edit else "Chỉ định xét nghiệm mới"))
        title = QLabel(f"{icon} {title_str}")
        title.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        title.setObjectName("dlgTitle")
        layout.addWidget(title)

        form = QFormLayout(); form.setSpacing(10)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        self.f_patient = QComboBox(); self.f_patient.setEditable(True)
        self.f_patient.lineEdit().setPlaceholderText("Chọn bệnh nhân...")
        for p in self.patients:
            self.f_patient.addItem(f"{p['patient_code']} — {p['full_name']}", p["id"])

        self.f_doctor = QComboBox(); self.f_doctor.addItem("-- Bác sĩ chỉ định --", None)
        for d in self.doctors:
            self.f_doctor.addItem(d["full_name"], d["id"])

        self.f_test_type = QComboBox(); self.f_test_type.addItems(TEST_TYPES)

        self.f_ordered = QDateTimeEdit(); self.f_ordered.setCalendarPopup(True)
        self.f_ordered.setDisplayFormat("dd/MM/yyyy HH:mm")
        self.f_ordered.setDateTime(QDateTime.currentDateTime())

        self.f_status = QComboBox()
        self.f_status.addItems(["Chờ","Đang xét nghiệm","Có kết quả","Huỷ"])

        self.f_result = QTextEdit(); self.f_result.setMinimumHeight(100)
        self.f_result.setPlaceholderText(
            "Nhập kết quả xét nghiệm...\nVD:\n- Hb: 14.2 g/dL (BT: 13.5-17.5)\n- WBC: 8.5 x10³/μL (BT: 4.5-11.0)\n- PLT: 250 x10³/μL (BT: 150-400)"
        )
        self.f_result_date = QDateTimeEdit(); self.f_result_date.setCalendarPopup(True)
        self.f_result_date.setDisplayFormat("dd/MM/yyyy HH:mm")
        self.f_result_date.setDateTime(QDateTime.currentDateTime())

        self.f_notes = QTextEdit(); self.f_notes.setMaximumHeight(55)
        self.f_notes.setPlaceholderText("Ghi chú, lưu ý,...")

        if not self.enter_result:
            form.addRow("Bệnh nhân *:",      self.f_patient)
            form.addRow("Bác sĩ chỉ định:", self.f_doctor)
            form.addRow("Loại xét nghiệm:", self.f_test_type)
            form.addRow("Ngày chỉ định:",   self.f_ordered)
        form.addRow("Trạng thái:",       self.f_status)
        form.addRow("Kết quả:",          self.f_result)
        form.addRow("Ngày có kết quả:",  self.f_result_date)
        form.addRow("Ghi chú:",          self.f_notes)
        layout.addLayout(form)

        if self.enter_result:
            self.f_patient.hide(); self.f_doctor.hide()
            self.f_test_type.hide(); self.f_ordered.hide()
            self.f_status.setCurrentText("Có kết quả")

        if self.view_only:
            self.f_patient.setEnabled(False)
            self.f_doctor.setEnabled(False)
            self.f_test_type.setEnabled(False)
            self.f_ordered.setEnabled(False)
            self.f_status.setEnabled(False)
            self.f_result.setReadOnly(True)
            self.f_result_date.setEnabled(False)
            self.f_notes.setReadOnly(True)

        btn_row = QHBoxLayout(); btn_row.addStretch()
        if self.view_only:
            close_btn = QPushButton("Đóng"); close_btn.setObjectName("cancelBtn")
            close_btn.clicked.connect(self.accept)
            btn_row.addWidget(close_btn)
        else:
            cancel_btn = QPushButton("Huỷ"); cancel_btn.setObjectName("cancelBtn")
            save_btn   = QPushButton("Lưu kết quả" if self.enter_result else "Lưu")
            save_btn.setObjectName("saveBtn")
            cancel_btn.clicked.connect(self.reject)
            save_btn.clicked.connect(self._save)
            btn_row.addWidget(cancel_btn); btn_row.addWidget(save_btn)
        layout.addLayout(btn_row)

    def _fill_form(self):
        t = self.test_data
        for i in range(self.f_patient.count()):
            if self.f_patient.itemData(i) == t["patient_id"]:
                self.f_patient.setCurrentIndex(i); break
        for i in range(self.f_doctor.count()):
            if self.f_doctor.itemData(i) == t["doctor_id"]:
                self.f_doctor.setCurrentIndex(i); break
        idx = self.f_test_type.findText(t["test_type"] or "")
        if idx >= 0: self.f_test_type.setCurrentIndex(idx)
        idx = self.f_status.findText(t["status"] or "Chờ")
        if idx >= 0: self.f_status.setCurrentIndex(idx)
        self.f_result.setPlainText(t["result"] or "")
        self.f_notes.setPlainText(t["notes"] or "")

    def _save(self):
        user = auth.get_current_user()
        tech_staff_id = dao.get_staff_id_by_user_id(user["id"]) if user else None
        self.result_data = {
            "patient_id":    self.f_patient.currentData(),
            "doctor_id":     self.f_doctor.currentData(),
            "technician_id": tech_staff_id,
            "test_type":     self.f_test_type.currentText(),
            "ordered_date":  self.f_ordered.dateTime().toString("yyyy-MM-dd HH:mm:ss"),
            "result_date":   self.f_result_date.dateTime().toString("yyyy-MM-dd HH:mm:ss"),
            "result":        self.f_result.toPlainText().strip(),
            "status":        self.f_status.currentText(),
            "notes":         self.f_notes.toPlainText().strip(),
        }
        if not self.enter_result and not self.result_data["patient_id"]:
            QMessageBox.warning(self, "Thiếu thông tin", "Vui lòng chọn bệnh nhân.")
            return
        self.accept()

    def _apply_style(self):
        self.setStyleSheet("""
        QDialog { background:#f7fafc; }
        #dlgTitle { color:#2d3748; }
        QLineEdit, QTextEdit, QComboBox, QDateTimeEdit {
            border:1.5px solid #cbd5e0; border-radius:6px; padding:6px 8px; font-size:12px; background:white;
        }
        QLabel { font-size:12px; color:#4a5568; }
        #saveBtn { background:#553c9a; color:white; border:none; border-radius:6px; padding:8px 20px; font-weight:600; }
        #saveBtn:hover { background:#44337a; }
        #cancelBtn { background:#e2e8f0; color:#4a5568; border:none; border-radius:6px; padding:8px 20px; }
        """)


class LabTab(QWidget):
    def __init__(self):
        super().__init__()
        self._build_ui()
        self._apply_style()
        self.load_data()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16,16,16,16); layout.setSpacing(10)

        header_row = QHBoxLayout()
        title = QLabel("🔬 Quản lý xét nghiệm")
        title.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        title.setObjectName("sectionTitle")
        header_row.addWidget(title); header_row.addStretch()
        self.add_btn = QPushButton("➕ Chỉ định xét nghiệm")
        self.add_btn.setObjectName("primaryBtn")
        self.add_btn.clicked.connect(self._add_test)
        header_row.addWidget(self.add_btn)
        layout.addLayout(header_row)

        f_row = QHBoxLayout()
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("🔍  Tìm theo tên bệnh nhân, loại xét nghiệm")
        self.search_box.setObjectName("searchBox")
        self.search_box.textChanged.connect(self.load_data)
        self.status_cb = QComboBox()
        self.status_cb.addItems(["Tất cả","Chờ","Đang xét nghiệm","Có kết quả","Huỷ"])
        self.status_cb.currentIndexChanged.connect(self.load_data)
        f_row.addWidget(self.search_box, 2); f_row.addWidget(self.status_cb)
        layout.addLayout(f_row)

        self.count_lbl = QLabel(); self.count_lbl.setObjectName("countLabel")
        layout.addWidget(self.count_lbl)

        self.table = QTableWidget()
        cols = ["Bệnh nhân","Loại XN","Bác sĩ CĐ","Ngày CĐ","Xét nghiệm viên","Ngày KQ","Trạng thái"]
        self.table.setColumnCount(len(cols))
        self.table.setHorizontalHeaderLabels(cols)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        self.table.itemDoubleClicked.connect(self._view_test_from_item)
        layout.addWidget(self.table)

        a_row = QHBoxLayout()
        self.view_btn   = QPushButton("👁️ Xem");           self.view_btn.setObjectName("actionBtn")
        self.result_btn = QPushButton("🔬 Nhập kết quả"); self.result_btn.setObjectName("primaryBtn")
        self.edit_btn   = QPushButton("✏️ Sửa");           self.edit_btn.setObjectName("actionBtn")
        self.view_btn.clicked.connect(self._view_test)
        self.result_btn.clicked.connect(self._enter_result)
        self.edit_btn.clicked.connect(self._edit_test)
        a_row.addWidget(self.view_btn); a_row.addWidget(self.result_btn); a_row.addWidget(self.edit_btn); a_row.addStretch()
        layout.addLayout(a_row)

        user = auth.get_current_user()
        if user and user.get("role") == "doctor":
            self.result_btn.hide()
            self.edit_btn.hide()

    def load_data(self):
        search = self.search_box.text().strip()
        status = self.status_cb.currentText()
        if status == "Tất cả": status = ""
        rows = dao.get_all_lab_tests(search, status)
        self.table.setRowCount(len(rows))
        for r, t in enumerate(rows):
            vals = [
                t["patient_name"] or "", t["test_type"] or "",
                t["doctor_name"] or "", (t["ordered_date"] or "")[:16],
                t["technician_name"] or "—", (t["result_date"] or "")[:16],
                t["status"] or ""
            ]
            for c, v in enumerate(vals):
                item = QTableWidgetItem(v)
                item.setData(Qt.ItemDataRole.UserRole.value, t["id"])
                if c == 6 and v in STATUS_COLORS:
                    bg, fg = STATUS_COLORS[v]
                    item.setBackground(QColor(bg)); item.setForeground(QColor(fg))
                self.table.setItem(r, c, item)
        self.count_lbl.setText(f"Tổng: {len(rows)} phiếu xét nghiệm")

    def _selected_id(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.information(self, "Chưa chọn", "Vui lòng chọn một phiếu xét nghiệm.")
            return None
        return self.table.item(row, 0).data(Qt.ItemDataRole.UserRole.value)

    def _add_test(self):
        dlg = LabTestDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            dao.add_lab_test(dlg.result_data); self.load_data()

    def _edit_test(self):
        tid = self._selected_id()
        if not tid: return
        t = dao.get_lab_test_by_id(tid)
        dlg = LabTestDialog(self, test_data=t)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            dao.update_lab_test(tid, dlg.result_data); self.load_data()

    def _enter_result(self):
        tid = self._selected_id()
        if not tid: return
        t = dao.get_lab_test_by_id(tid)
        dlg = LabTestDialog(self, test_data=t, enter_result=True)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            dao.update_lab_test(tid, dlg.result_data); self.load_data()

    def _view_test(self):
        tid = self._selected_id()
        if not tid: return
        t = dao.get_lab_test_by_id(tid)
        dlg = LabTestDialog(self, test_data=t, view_only=True)
        dlg.exec()

    def _view_test_from_item(self, item):
        tid = self.table.item(item.row(), 0).data(Qt.ItemDataRole.UserRole.value)
        if not tid: return
        t = dao.get_lab_test_by_id(tid)
        dlg = LabTestDialog(self, test_data=t, view_only=True)
        dlg.exec()

    def _apply_style(self):
        self.setStyleSheet("""
        QWidget { background:#f7fafc; font-family:'Segoe UI'; }
        #sectionTitle { color:#1a365d; }
        #searchBox { border:1.5px solid #cbd5e0; border-radius:8px; padding:8px 12px; font-size:13px; background:white; }
        QComboBox { border:1.5px solid #cbd5e0; border-radius:6px; padding:6px 8px; font-size:12px; background:white; }
        #primaryBtn { background:#553c9a; color:white; border:none; border-radius:7px; padding:8px 16px; font-weight:600; }
        #primaryBtn:hover { background:#44337a; }
        #actionBtn { background:#edf2f7; color:#2d3748; border:none; border-radius:6px; padding:7px 14px; font-size:12px; }
        #countLabel { color:#718096; font-size:12px; }
        QTableWidget { border:1px solid #e2e8f0; border-radius:8px; font-size:12px; }
        QHeaderView::section { background:#edf2f7; font-weight:600; padding:8px; border:none; }
        """)
