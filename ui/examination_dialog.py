import json
from datetime import datetime

from PyQt6.QtWidgets import (
    QDialog, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QTabWidget, QFrame, QFormLayout, QLineEdit,
    QTextEdit, QComboBox, QDateEdit, QTableWidget, QTableWidgetItem,
    QHeaderView, QAbstractItemView, QMessageBox, QListWidget, QListWidgetItem,
    QSpinBox, QCheckBox, QScrollArea, QSizePolicy, QSplitter,
    QGroupBox, QGridLayout
)
from PyQt6.QtCore import Qt, QDate
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
    "CT Scan", "MRI",
    "Cấy vi khuẩn", "Khác",
]


# ═══════════════════════════════════════════════════════════
#  Patient Info Panel (sidebar)
# ═══════════════════════════════════════════════════════════
class PatientInfoPanel(QFrame):
    def __init__(self, patient):
        super().__init__()
        self.setObjectName("infoPanel")
        self.setFixedWidth(240)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(8)

        # Avatar + name
        avatar = QLabel("👤")
        avatar.setFont(QFont("Segoe UI", 32))
        avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(avatar)

        name = QLabel(patient["full_name"])
        name.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        name.setAlignment(Qt.AlignmentFlag.AlignCenter)
        name.setWordWrap(True)
        name.setObjectName("patientName")
        layout.addWidget(name)

        code = QLabel(patient["patient_code"])
        code.setAlignment(Qt.AlignmentFlag.AlignCenter)
        code.setObjectName("patientCode")
        layout.addWidget(code)

        sep = QFrame(); sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("color:#e2e8f0;")
        layout.addWidget(sep)

        # Info fields
        fields = [
            ("🎂 Năm sinh",  (patient["birth_date"] or "")[:4] or "—"),
            ("⚧ Giới tính", patient["gender"] or "—"),
            ("🩸 Nhóm máu", patient["blood_type"] or "—"),
            ("📞 SĐT",      patient["phone"] or "—"),
            ("🏥 BHYT",     patient["insurance_id"] or "Không có"),
        ]
        for label, value in fields:
            row = QHBoxLayout()
            lbl = QLabel(label); lbl.setObjectName("infoLabel")
            val = QLabel(value); val.setObjectName("infoValue")
            val.setWordWrap(True)
            row.addWidget(lbl); row.addWidget(val, 1)
            layout.addLayout(row)

        # Allergies warning
        if patient["allergies"] and patient["allergies"].strip():
            allergy_frame = QFrame()
            allergy_frame.setStyleSheet("""
                QFrame { background:#fff5f5; border:1.5px solid #fc8181;
                         border-radius:8px; padding:2px; }
            """)
            al = QVBoxLayout(allergy_frame)
            al.setContentsMargins(8, 6, 8, 6)
            al_title = QLabel("⚠️ DỊ ỨNG")
            al_title.setStyleSheet("color:#c53030; font-weight:700; font-size:11px; background:transparent;")
            al_text = QLabel(patient["allergies"])
            al_text.setWordWrap(True)
            al_text.setStyleSheet("color:#742a2a; font-size:11px; background:transparent;")
            al.addWidget(al_title); al.addWidget(al_text)
            layout.addWidget(allergy_frame)

        layout.addStretch()

        # Previous visits count
        history = dao.get_patient_medical_history(patient["id"])
        hist_lbl = QLabel(f"📁 Đã khám: {len(history)} lần")
        hist_lbl.setObjectName("histLabel")
        hist_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(hist_lbl)


# ═══════════════════════════════════════════════════════════
#  Tab 1 — Khám & Chẩn đoán
# ═══════════════════════════════════════════════════════════
class ExamTab(QWidget):
    def __init__(self, patient):
        super().__init__()
        self.patient = patient
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(10)

        form = QFormLayout()
        form.setSpacing(10)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        self.f_symptoms = QTextEdit()
        self.f_symptoms.setPlaceholderText(
            "Mô tả triệu chứng bệnh nhân khai báo...\n"
            "VD: Sốt 38.5°C, ho khan 3 ngày, đau họng, sổ mũi, mệt mỏi."
        )
        self.f_symptoms.setMinimumHeight(90)

        self.f_diagnosis = QTextEdit()
        self.f_diagnosis.setPlaceholderText(
            "Chẩn đoán sơ bộ / chính thức...\n"
            "VD: Viêm đường hô hấp trên cấp. ICD-10: J06.9"
        )
        self.f_diagnosis.setMinimumHeight(80)

        self.f_treatment = QTextEdit()
        self.f_treatment.setPlaceholderText(
            "Phác đồ điều trị...\n"
            "VD: Nghỉ ngơi, uống nhiều nước, dùng thuốc theo đơn."
        )
        self.f_treatment.setMinimumHeight(80)

        self.f_followup = QDateEdit()
        self.f_followup.setCalendarPopup(True)
        self.f_followup.setDisplayFormat("dd/MM/yyyy")
        self.f_followup.setDate(QDate.currentDate().addDays(7))
        self.f_followup.setSpecialValueText("Không cần tái khám")

        self.f_need_followup = QCheckBox("Hẹn tái khám")
        self.f_need_followup.setChecked(False)
        self.f_need_followup.toggled.connect(self.f_followup.setEnabled)
        self.f_followup.setEnabled(False)

        followup_row = QHBoxLayout()
        followup_row.addWidget(self.f_need_followup)
        followup_row.addWidget(self.f_followup)
        followup_row.addStretch()

        self.f_notes = QTextEdit()
        self.f_notes.setPlaceholderText("Ghi chú thêm cho lần khám này...")
        self.f_notes.setMaximumHeight(60)

        form.addRow("🤒 Triệu chứng *:", self.f_symptoms)
        form.addRow("🔍 Chẩn đoán *:",   self.f_diagnosis)
        form.addRow("💊 Phác đồ ĐT:",    self.f_treatment)
        form.addRow("📅 Tái khám:",       followup_row)
        form.addRow("📝 Ghi chú:",        self.f_notes)

        layout.addLayout(form)

    def get_data(self):
        return {
            "symptoms":      self.f_symptoms.toPlainText().strip(),
            "diagnosis":     self.f_diagnosis.toPlainText().strip(),
            "treatment_plan":self.f_treatment.toPlainText().strip(),
            "follow_up_date":(self.f_followup.date().toString("yyyy-MM-dd")
                              if self.f_need_followup.isChecked() else None),
            "notes":         self.f_notes.toPlainText().strip(),
        }

    def validate(self):
        if not self.f_symptoms.toPlainText().strip():
            QMessageBox.warning(self, "Thiếu thông tin", "Vui lòng nhập triệu chứng.")
            return False
        if not self.f_diagnosis.toPlainText().strip():
            QMessageBox.warning(self, "Thiếu thông tin", "Vui lòng nhập chẩn đoán.")
            return False
        return True


# ═══════════════════════════════════════════════════════════
#  Tab 2 — Chỉ định Xét nghiệm
# ═══════════════════════════════════════════════════════════
class LabOrderTab(QWidget):
    def __init__(self, patient):
        super().__init__()
        self.patient    = patient
        self.lab_orders = []   # list of test_type strings
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(10)

        note = QLabel(
            "ℹ️  Chọn các xét nghiệm cần chỉ định. "
            "Kết quả sẽ do Xét nghiệm viên cập nhật sau."
        )
        note.setWordWrap(True)
        note.setStyleSheet(
            "background:#ebf8ff; color:#2b6cb0; border-radius:6px; "
            "padding:8px 12px; font-size:12px;"
        )
        layout.addWidget(note)

        # Checkboxes grouped
        scroll = QScrollArea(); scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        cw = QWidget(); grid = QGridLayout(cw)
        grid.setSpacing(8); grid.setContentsMargins(0, 4, 0, 4)

        self._checkboxes = {}
        for i, t in enumerate(TEST_TYPES):
            cb = QCheckBox(t)
            cb.setStyleSheet("font-size:12px;")
            grid.addWidget(cb, i // 2, i % 2)
            self._checkboxes[t] = cb
        scroll.setWidget(cw)
        layout.addWidget(scroll)

        # Custom test
        custom_row = QHBoxLayout()
        self.custom_input = QLineEdit()
        self.custom_input.setPlaceholderText("Xét nghiệm khác (nhập tên)...")
        self.custom_input.setObjectName("customInput")
        add_custom_btn = QPushButton("➕ Thêm")
        add_custom_btn.setObjectName("addCustomBtn")
        add_custom_btn.clicked.connect(self._add_custom)
        custom_row.addWidget(self.custom_input)
        custom_row.addWidget(add_custom_btn)
        layout.addLayout(custom_row)

        # Selected list
        layout.addWidget(QLabel("📋 Xét nghiệm đã chọn:"))
        self.selected_list = QListWidget()
        self.selected_list.setMaximumHeight(100)
        self.selected_list.setStyleSheet(
            "border:1px solid #e2e8f0; border-radius:6px; font-size:12px;"
        )
        layout.addWidget(self.selected_list)

        # Connect checkboxes to list
        for t, cb in self._checkboxes.items():
            cb.toggled.connect(lambda checked, name=t: self._update_list())

        # Priority / notes
        form = QFormLayout(); form.setSpacing(8)
        self.f_priority = QComboBox()
        self.f_priority.addItems(["Bình thường","Khẩn cấp","Cấp cứu"])
        self.f_lab_notes = QLineEdit()
        self.f_lab_notes.setPlaceholderText("Lưu ý cho xét nghiệm viên (nếu có)...")
        form.addRow("Mức độ ưu tiên:", self.f_priority)
        form.addRow("Ghi chú:",        self.f_lab_notes)
        layout.addLayout(form)

    def _add_custom(self):
        text = self.custom_input.text().strip()
        if text:
            self.lab_orders.append(text)
            self._update_list()
            self.custom_input.clear()

    def _update_list(self):
        self.selected_list.clear()
        all_selected = [t for t, cb in self._checkboxes.items() if cb.isChecked()]
        all_selected += self.lab_orders
        for t in all_selected:
            self.selected_list.addItem(f"🔬 {t}")

    def get_orders(self):
        checked = [t for t, cb in self._checkboxes.items() if cb.isChecked()]
        return {
            "tests":    checked + self.lab_orders,
            "priority": self.f_priority.currentText(),
            "notes":    self.f_lab_notes.text().strip(),
        }


# ═══════════════════════════════════════════════════════════
#  Tab 3 — Kê đơn Thuốc
# ═══════════════════════════════════════════════════════════
class PrescriptionTab(QWidget):
    def __init__(self, patient):
        super().__init__()
        self.patient   = patient
        self.rx_items  = []
        self.medicines = dao.get_all_medicines()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(8)

        splitter = QSplitter(Qt.Orientation.Horizontal)

        # LEFT: medicine picker
        left = QFrame(); left.setObjectName("rxLeft")
        ll = QVBoxLayout(left); ll.setContentsMargins(10,10,10,10); ll.setSpacing(6)

        ll.addWidget(QLabel("🔍 Tìm thuốc:"))
        self.med_search = QLineEdit()
        self.med_search.setPlaceholderText("Nhập tên thuốc / hoạt chất...")
        self.med_search.setObjectName("medSearch")
        self.med_search.textChanged.connect(self._filter_meds)
        ll.addWidget(self.med_search)

        self.med_list = QListWidget()
        self.med_list.setAlternatingRowColors(True)
        self._populate_med_list(self.medicines)
        ll.addWidget(self.med_list)

        # Dosage form
        dose_box = QGroupBox("📋 Thông tin liều dùng")
        dose_box.setObjectName("doseBox")
        dl = QFormLayout(dose_box); dl.setSpacing(6)
        self.f_qty      = QSpinBox(); self.f_qty.setRange(1,9999); self.f_qty.setValue(1)
        self.f_dosage   = QLineEdit()
        self.f_dosage.setPlaceholderText("VD: 1 viên x 3 lần/ngày, sau ăn")
        self.f_duration = QSpinBox(); self.f_duration.setRange(1,365)
        self.f_duration.setValue(5); self.f_duration.setSuffix(" ngày")
        self.f_rx_note  = QLineEdit()
        self.f_rx_note.setPlaceholderText("Lưu ý riêng (uống trước/sau ăn,...)")
        dl.addRow("Số lượng:", self.f_qty)
        dl.addRow("Liều dùng:", self.f_dosage)
        dl.addRow("Số ngày:", self.f_duration)
        dl.addRow("Lưu ý:", self.f_rx_note)
        ll.addWidget(dose_box)

        add_rx_btn = QPushButton("➕ Thêm vào đơn thuốc")
        add_rx_btn.setObjectName("addRxBtn")
        add_rx_btn.clicked.connect(self._add_to_rx)
        ll.addWidget(add_rx_btn)

        splitter.addWidget(left)

        # RIGHT: prescription list
        right = QFrame(); right.setObjectName("rxRight")
        rl = QVBoxLayout(right); rl.setContentsMargins(10,10,10,10); rl.setSpacing(8)

        rl.addWidget(QLabel("📄 Đơn thuốc:"))
        self.rx_table = QTableWidget()
        self.rx_table.setColumnCount(6)
        self.rx_table.setHorizontalHeaderLabels(
            ["Tên thuốc","SL","Đơn vị","Liều dùng","Số ngày","Xoá"]
        )
        self.rx_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.rx_table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        self.rx_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.rx_table.setAlternatingRowColors(True)
        self.rx_table.verticalHeader().setVisible(False)
        rl.addWidget(self.rx_table)

        # Drug interaction warning
        self.warn_frame = QFrame()
        self.warn_frame.setObjectName("warnFrame")
        self.warn_frame.hide()
        wl = QVBoxLayout(self.warn_frame)
        wl.setContentsMargins(10, 8, 10, 8)
        self.warn_lbl = QLabel()
        self.warn_lbl.setWordWrap(True)
        self.warn_lbl.setObjectName("warnLbl")
        wl.addWidget(self.warn_lbl)
        rl.addWidget(self.warn_frame)

        # Prescription notes
        rl.addWidget(QLabel("📝 Lời dặn dò bệnh nhân:"))
        self.f_presc_notes = QTextEdit()
        self.f_presc_notes.setMaximumHeight(65)
        self.f_presc_notes.setPlaceholderText(
            "VD: Uống nhiều nước, nghỉ ngơi, tái khám nếu sốt không giảm sau 3 ngày..."
        )
        rl.addWidget(self.f_presc_notes)

        splitter.addWidget(right)
        splitter.setSizes([280, 420])
        layout.addWidget(splitter)

    def _populate_med_list(self, meds):
        self.med_list.clear()
        for m in meds:
            low = m["stock_qty"] <= m["min_stock"]
            label = f"{m['name']}  ({m['unit'] or ''})  | Tồn: {m['stock_qty']}"
            if low: label += "  ⚠️"
            item = QListWidgetItem(label)
            item.setData(Qt.ItemDataRole.UserRole.value, m["id"])
            item.setData(Qt.ItemDataRole.UserRole.value + 1, m["name"])
            item.setData(Qt.ItemDataRole.UserRole.value + 2, m["unit"] or "")
            if low:
                item.setForeground(QColor("#c53030"))
            self.med_list.addItem(item)

    def _filter_meds(self):
        query = self.med_search.text().lower()
        filtered = [m for m in self.medicines
                    if query in (m["name"] or "").lower()
                    or query in (m["generic_name"] or "").lower()]
        self._populate_med_list(filtered)

    def _add_to_rx(self):
        sel = self.med_list.currentItem()
        if not sel:
            QMessageBox.warning(self, "Chưa chọn", "Vui lòng chọn thuốc từ danh sách.")
            return
        dosage = self.f_dosage.text().strip()
        if not dosage:
            QMessageBox.warning(self, "Thiếu liều dùng", "Vui lòng nhập liều dùng.")
            return
        self.rx_items.append({
            "medicine_id": sel.data(Qt.ItemDataRole.UserRole.value),
            "name":        sel.data(Qt.ItemDataRole.UserRole.value + 1),
            "unit":        sel.data(Qt.ItemDataRole.UserRole.value + 2),
            "quantity":    self.f_qty.value(),
            "dosage":      dosage,
            "duration_days": self.f_duration.value(),
            "notes":       self.f_rx_note.text().strip(),
        })
        self.f_dosage.clear(); self.f_rx_note.clear()
        self._refresh_rx_table()
        self._check_interactions()

    def _refresh_rx_table(self):
        self.rx_table.setRowCount(len(self.rx_items))
        for r, item in enumerate(self.rx_items):
            vals = [item["name"], str(item["quantity"]), item["unit"],
                    item["dosage"], f"{item['duration_days']} ngày"]
            for c, v in enumerate(vals):
                self.rx_table.setItem(r, c, QTableWidgetItem(v))
            del_btn = QPushButton("🗑️")
            del_btn.setFixedWidth(34)
            del_btn.setStyleSheet(
                "QPushButton{background:#fff5f5;color:#c53030;"
                "border:none;border-radius:4px;font-size:13px;}"
                "QPushButton:hover{background:#fed7d7;}"
            )
            del_btn.clicked.connect(lambda _, idx=r: self._remove_rx(idx))
            self.rx_table.setCellWidget(r, 5, del_btn)

    def _remove_rx(self, idx):
        self.rx_items.pop(idx)
        self._refresh_rx_table()
        self._check_interactions()

    def _check_interactions(self):
        if len(self.rx_items) < 2:
            self.warn_frame.hide(); return
        med_ids  = [i["medicine_id"] for i in self.rx_items]
        warnings = dao.check_drug_interactions(med_ids)
        if not warnings:
            self.warn_frame.hide(); return
        msgs = []
        has_danger = False
        for w in warnings:
            sev = w["severity"]
            icon = "🔴" if sev == "Nguy hiểm" else "🟡" if sev == "Thận trọng" else "🔵"
            msgs.append(f"{icon} <b>{w['med1']} + {w['med2']}</b> — {sev}: {w['description'] or ''}")
            if sev == "Nguy hiểm": has_danger = True
        self.warn_lbl.setText("<br>".join(msgs))
        color = "#c53030" if has_danger else "#856404"
        bg    = "#fff5f5" if has_danger else "#fffbeb"
        self.warn_frame.setStyleSheet(
            f"#warnFrame{{background:{bg};border:2px solid {color};border-radius:8px;}}"
        )
        self.warn_frame.show()

    def get_data(self):
        return {
            "items": self.rx_items,
            "notes": self.f_presc_notes.toPlainText().strip(),
        }


# ═══════════════════════════════════════════════════════════
#  Main Examination Dialog
# ═══════════════════════════════════════════════════════════
class ExaminationDialog(QDialog):
    def __init__(self, patient_id: int, appointment_id: int = None, parent=None):
        super().__init__(parent)
        self.patient_id     = patient_id
        self.appointment_id = appointment_id
        self.patient        = dao.get_patient_by_id(patient_id)
        self.setWindowTitle(
            f"Khám bệnh — {self.patient['full_name']}  ({self.patient['patient_code']})"
        )
        self.setMinimumSize(1000, 680)
        self.setModal(True)
        self._build_ui()
        self._apply_style()

    def _build_ui(self):
        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Left: patient info sidebar ────────────────────────────
        self.info_panel = PatientInfoPanel(self.patient)
        root.addWidget(self.info_panel)

        # ── Right: tabbed workflow ────────────────────────────────
        right_frame = QFrame()
        right_frame.setObjectName("rightFrame")
        rl = QVBoxLayout(right_frame)
        rl.setContentsMargins(0, 0, 0, 0)
        rl.setSpacing(0)

        # Header bar
        header = QFrame(); header.setObjectName("examHeader")
        hl = QHBoxLayout(header); hl.setContentsMargins(16, 12, 16, 12)
        title = QLabel(f"🩺 Phiên khám  —  {datetime.now().strftime('%d/%m/%Y %H:%M')}")
        title.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        title.setObjectName("examTitle")
        hl.addWidget(title); hl.addStretch()

        # Doctor info
        user = auth.get_current_user()
        doc_lbl = QLabel(f"Bác sĩ: {user['full_name'] if user else '—'}")
        doc_lbl.setObjectName("docLabel")
        hl.addWidget(doc_lbl)
        rl.addWidget(header)

        # Tabs
        self.tabs = QTabWidget()
        self.tabs.setObjectName("examTabs")

        self.exam_tab = ExamTab(self.patient)
        self.lab_tab  = LabOrderTab(self.patient)
        self.rx_tab   = PrescriptionTab(self.patient)

        self.tabs.addTab(self.exam_tab, "1️⃣  Khám & Chẩn đoán")
        self.tabs.addTab(self.lab_tab,  "2️⃣  Chỉ định Xét nghiệm")
        self.tabs.addTab(self.rx_tab,   "3️⃣  Kê đơn thuốc")

        rl.addWidget(self.tabs)

        # Footer buttons
        footer = QFrame(); footer.setObjectName("examFooter")
        fl = QHBoxLayout(footer); fl.setContentsMargins(16, 10, 16, 10)

        # Navigation buttons
        self.prev_btn = QPushButton("◀ Bước trước")
        self.prev_btn.setObjectName("navBtn")
        self.prev_btn.clicked.connect(self._prev_tab)
        self.prev_btn.setEnabled(False)

        self.next_btn = QPushButton("Bước tiếp ▶")
        self.next_btn.setObjectName("navBtn")
        self.next_btn.clicked.connect(self._next_tab)

        self.tabs.currentChanged.connect(self._on_tab_change)

        cancel_btn = QPushButton("✖ Huỷ")
        cancel_btn.setObjectName("cancelBtn")
        cancel_btn.clicked.connect(self.reject)

        self.save_btn = QPushButton("💾 Lưu hồ sơ khám")
        self.save_btn.setObjectName("saveBtn")
        self.save_btn.setVisible(False)
        self.save_btn.clicked.connect(self._save_all)

        fl.addWidget(cancel_btn)
        fl.addStretch()
        fl.addWidget(self.prev_btn)
        fl.addWidget(self.next_btn)
        fl.addWidget(self.save_btn)
        rl.addWidget(footer)

        root.addWidget(right_frame, 1)

    # ── Tab navigation ───────────────────────────────────────────
    def _prev_tab(self):
        idx = self.tabs.currentIndex()
        if idx > 0:
            self.tabs.setCurrentIndex(idx - 1)

    def _next_tab(self):
        idx = self.tabs.currentIndex()
        # Validate tab 0 before moving
        if idx == 0 and not self.exam_tab.validate():
            return
        if idx < self.tabs.count() - 1:
            self.tabs.setCurrentIndex(idx + 1)

    def _on_tab_change(self, idx):
        self.prev_btn.setEnabled(idx > 0)
        is_last = idx == self.tabs.count() - 1
        self.next_btn.setVisible(not is_last)
        self.save_btn.setVisible(is_last)

    # ── Save all ─────────────────────────────────────────────────
    def _save_all(self):
        # 1. Validate exam
        if not self.exam_tab.validate():
            self.tabs.setCurrentIndex(0); return

        exam_data = self.exam_tab.get_data()
        lab_data  = self.lab_tab.get_orders()
        rx_data   = self.rx_tab.get_data()

        # Warn dangerous interactions
        if rx_data["items"]:
            med_ids  = [i["medicine_id"] for i in rx_data["items"]]
            warnings = dao.check_drug_interactions(med_ids)
            danger   = [w for w in warnings if w["severity"] == "Nguy hiểm"]
            if danger:
                reply = QMessageBox.warning(
                    self, "⚠️ Tương tác thuốc NGUY HIỂM",
                    f"Phát hiện {len(danger)} tương tác nguy hiểm trong đơn thuốc!\n"
                    "Bạn có chắc muốn lưu đơn này không?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                if reply != QMessageBox.StandardButton.Yes:
                    self.tabs.setCurrentIndex(2); return

        user = auth.get_current_user()
        # Resolve users.id -> staff.id so FK columns point to the right row
        doc_staff_id = dao.get_staff_id_by_user_id(user["id"]) if user else None

        # 2. Save medical record
        record_data = {
            "patient_id":    self.patient_id,
            "doctor_id":     doc_staff_id,
            "visit_date":    datetime.now().strftime("%Y-%m-%d %H:%M"),
            **exam_data,
        }
        record_id = dao.add_medical_record(record_data)

        # 3. Save lab orders (if any)
        for test_type in lab_data["tests"]:
            dao.add_lab_test({
                "patient_id":   self.patient_id,
                "doctor_id":    doc_staff_id,
                "test_type":    test_type,
                "ordered_date": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "status":       "Chờ",
                "notes":        f"[{lab_data['priority']}] {lab_data['notes']}",
            })

        # 4. Save prescription (if items exist)
        if rx_data["items"]:
            try:
                dao.save_prescription({
                    "medical_record_id": record_id,
                    "doctor_id":         doc_staff_id,
                    "notes":             rx_data["notes"],
                    "items":             rx_data["items"],
                })
            except ValueError as e:
                # Prescription failed (insufficient stock) —
                # compensate by removing the medical_record we just wrote,
                # then surface a clear error dialog to the user.
                dao.delete_medical_record(record_id)
                QMessageBox.critical(
                    self, "Không đủ tồn kho",
                    str(e) + "\n\nĐơn thuốc chưa được lưu.\n"
                             "Vui lòng điều chỉnh số lượng và thử lại."
                )
                self.tabs.setCurrentIndex(2)   # jump back to Prescription tab
                return

        # 5. Update appointment status → Hoàn thành
        if self.appointment_id:
            dao.update_appointment_status(self.appointment_id, "Hoàn thành")

        # 6. Summary message
        n_tests = len(lab_data["tests"])
        n_meds  = len(rx_data["items"])
        summary = (
            f"✅ Đã lưu hồ sơ khám thành công!\n\n"
            f"📋 Chẩn đoán: {exam_data['diagnosis'][:60]}...\n"
            f"🔬 Xét nghiệm chỉ định: {n_tests} loại\n"
            f"💊 Đơn thuốc: {n_meds} loại thuốc"
        )
        if exam_data.get("follow_up_date"):
            summary += f"\n📅 Hẹn tái khám: {exam_data['follow_up_date']}"

        QMessageBox.information(self, "Lưu thành công", summary)
        self.accept()

    # ── Style ────────────────────────────────────────────────────
    def _apply_style(self):
        self.setStyleSheet("""
        QDialog { background:#f7fafc; font-family:'Segoe UI'; }

        /* Sidebar */
        #infoPanel {
            background:white; border-right:1px solid #e2e8f0;
        }
        #patientName { color:#1a365d; font-size:13px; }
        #patientCode { color:#718096; font-size:11px; }
        #infoLabel { color:#718096; font-size:11px; min-width:80px; }
        #infoValue { color:#2d3748; font-size:12px; font-weight:600; }
        #histLabel { color:#553c9a; font-size:11px; font-weight:600;
                     background:#faf5ff; border-radius:6px; padding:4px 8px; }

        /* Header */
        #rightFrame { background:#f7fafc; }
        #examHeader { background:white; border-bottom:1px solid #e2e8f0; }
        #examTitle  { color:#1a365d; }
        #docLabel   { color:#718096; font-size:12px; }

        /* Tabs */
        #examTabs::pane { border:none; background:#f7fafc; }
        QTabBar::tab {
            padding:10px 20px; font-size:12px; font-weight:600;
            color:#718096; border-bottom:2px solid transparent;
        }
        QTabBar::tab:selected { color:#2b6cb0; border-bottom:2px solid #2b6cb0; }
        QTabBar::tab:hover    { color:#2d3748; }

        /* Forms */
        QTextEdit, QLineEdit, QComboBox, QDateEdit, QSpinBox {
            border:1.5px solid #cbd5e0; border-radius:6px;
            padding:7px 9px; font-size:12px; background:white;
        }
        QTextEdit:focus, QLineEdit:focus { border-color:#4299e1; }
        QLabel { font-size:12px; color:#4a5568; }
        QCheckBox { font-size:12px; color:#2d3748; }

        /* Prescription panels */
        #rxLeft, #rxRight {
            background:white; border-radius:8px; border:1px solid #e2e8f0;
        }
        #doseBox {
            border:1.5px solid #bee3f8; border-radius:8px; background:#ebf8ff;
            font-size:12px; font-weight:600;
        }
        #doseBox::title { color:#2b6cb0; }
        #medSearch {
            border:1.5px solid #cbd5e0; border-radius:6px;
            padding:7px 10px; font-size:12px; background:white;
        }
        #addRxBtn {
            background:#553c9a; color:white; border:none;
            border-radius:7px; padding:9px; font-weight:600; font-size:12px;
        }
        #addRxBtn:hover { background:#44337a; }
        #customInput {
            border:1.5px solid #cbd5e0; border-radius:6px;
            padding:7px 9px; font-size:12px; background:white;
        }
        #addCustomBtn {
            background:#2b6cb0; color:white; border:none;
            border-radius:6px; padding:7px 12px; font-size:12px;
        }

        /* Footer */
        #examFooter { background:white; border-top:1px solid #e2e8f0; }
        #saveBtn {
            background:#276749; color:white; border:none;
            border-radius:8px; padding:9px 24px; font-weight:700; font-size:13px;
        }
        #saveBtn:hover { background:#22543d; }
        #navBtn {
            background:#edf2f7; color:#2d3748; border:none;
            border-radius:7px; padding:8px 18px; font-size:12px; font-weight:600;
        }
        #navBtn:hover   { background:#e2e8f0; }
        #navBtn:disabled{ background:#f7fafc; color:#cbd5e0; }
        #cancelBtn {
            background:#fff5f5; color:#c53030; border:1px solid #fed7d7;
            border-radius:7px; padding:8px 14px; font-size:12px;
        }
        #cancelBtn:hover { background:#fed7d7; }

        /* Interaction warning */
        #warnLbl { font-size:12px; color:#2d3748; }

        QTableWidget {
            border:1px solid #e2e8f0; border-radius:6px;
            font-size:12px; gridline-color:#f0f0f0;
        }
        QHeaderView::section {
            background:#edf2f7; font-weight:600; padding:6px; border:none;
        }
        QListWidget { font-size:12px; }
        QListWidget::item:selected { background:#bee3f8; color:#1a365d; }
        QGroupBox { font-size:12px; }
        """)
