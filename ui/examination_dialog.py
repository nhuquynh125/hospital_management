import json
import os
from datetime import datetime

from PyQt6.QtWidgets import (
    QDialog, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QTabWidget, QFrame, QFormLayout, QLineEdit,
    QTextEdit, QComboBox, QDateEdit, QTableWidget, QTableWidgetItem,
    QHeaderView, QAbstractItemView, QMessageBox, QListWidget, QListWidgetItem,
    QSpinBox, QDoubleSpinBox, QCheckBox, QScrollArea, QSizePolicy, QSplitter,
    QGroupBox, QGridLayout
)
from PyQt6.QtCore import Qt, QDate, QTimer
from PyQt6.QtGui import QFont, QColor, QTextDocument
from PyQt6.QtPrintSupport import QPrinter, QPrintDialog
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

        # ── Chỉ số sinh tồn ──────────────────────────────────────
        vital_group = QGroupBox("📊 Chỉ số sinh tồn")
        vital_group.setObjectName("vitalGroup")
        vg = QGridLayout(vital_group)
        vg.setSpacing(8)

        self.f_height = QDoubleSpinBox(); self.f_height.setRange(0, 250); self.f_height.setSuffix(" cm")
        self.f_weight = QDoubleSpinBox(); self.f_weight.setRange(0, 300); self.f_weight.setSuffix(" kg")
        self.f_bp     = QLineEdit(); self.f_bp.setPlaceholderText("VD: 120/80")
        self.f_heart_rate = QSpinBox(); self.f_heart_rate.setRange(0, 250); self.f_heart_rate.setSuffix(" lần/phút")
        self.f_temp   = QDoubleSpinBox(); self.f_temp.setRange(34, 42); self.f_temp.setValue(37.0)
        self.f_temp.setSingleStep(0.1); self.f_temp.setSuffix(" °C")
        self.f_spo2   = QSpinBox(); self.f_spo2.setRange(0, 100); self.f_spo2.setSuffix(" %")

        vg.addWidget(QLabel("Chiều cao:"), 0, 0); vg.addWidget(self.f_height, 0, 1)
        vg.addWidget(QLabel("Cân nặng:"),  0, 2); vg.addWidget(self.f_weight, 0, 3)
        vg.addWidget(QLabel("Huyết áp:"),  1, 0); vg.addWidget(self.f_bp, 1, 1)
        vg.addWidget(QLabel("Nhịp tim:"),  1, 2); vg.addWidget(self.f_heart_rate, 1, 3)
        vg.addWidget(QLabel("Nhiệt độ:"),  2, 0); vg.addWidget(self.f_temp, 2, 1)
        vg.addWidget(QLabel("SpO2:"),      2, 2); vg.addWidget(self.f_spo2, 2, 3)

        layout.addWidget(vital_group)

        form = QFormLayout()
        form.setSpacing(10)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        self.f_symptoms = QTextEdit()
        self.f_symptoms.setPlaceholderText(
            "Mô tả triệu chứng bệnh nhân khai báo...\n"
            "VD: Sốt 38.5°C, ho khan 3 ngày, đau họng, sổ mũi, mệt mỏi."
        )
        self.f_symptoms.setMinimumHeight(80)

        # Tiền sử bệnh — tự gợi ý từ các chẩn đoán trước đó, bác sĩ có thể sửa
        self.f_history = QTextEdit()
        self.f_history.setMaximumHeight(60)
        self.f_history.setPlaceholderText("Tiền sử bệnh, dị ứng, bệnh mạn tính,...")
        try:
            prior = dao.get_patient_medical_history(patient["id"])
            diag_set = []
            for h in prior:
                d = h["diagnosis"]
                if d and d not in diag_set:
                    diag_set.append(d)
            if diag_set:
                self.f_history.setPlainText("; ".join(diag_set))
        except Exception:
            pass

        self.f_diagnosis = QTextEdit()
        self.f_diagnosis.setPlaceholderText(
            "Chẩn đoán sơ bộ / chính thức...\n"
            "VD: Viêm đường hô hấp trên cấp. ICD-10: J06.9"
        )
        self.f_diagnosis.setMinimumHeight(70)

        self.f_conclusion = QTextEdit()
        self.f_conclusion.setMaximumHeight(65)
        self.f_conclusion.setPlaceholderText("Kết luận chung về tình trạng bệnh nhân sau khi khám...")

        self.f_treatment = QTextEdit()
        self.f_treatment.setPlaceholderText(
            "Phác đồ điều trị...\n"
            "VD: Nghỉ ngơi, uống nhiều nước, dùng thuốc theo đơn."
        )
        self.f_treatment.setMinimumHeight(70)

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
        self.f_notes.setMaximumHeight(55)

        form.addRow("🤒 Triệu chứng *:",  self.f_symptoms)
        form.addRow("📜 Tiền sử bệnh:",   self.f_history)
        form.addRow("🔍 Chẩn đoán *:",    self.f_diagnosis)
        form.addRow("✅ Kết luận khám:",  self.f_conclusion)
        form.addRow("💊 Phác đồ ĐT:",     self.f_treatment)
        form.addRow("📅 Tái khám:",       followup_row)
        form.addRow("📝 Ghi chú:",        self.f_notes)

        layout.addLayout(form)
        self._prefill_vital_signs()

    def _prefill_vital_signs(self):
        note = dao.get_latest_nursing_note_for_patient_today(self.patient["id"])
        if note and note["vital_signs"]:
            try:
                vs = json.loads(note["vital_signs"])
                if "height" in vs and vs["height"] > 0: self.f_height.setValue(vs["height"])
                if "weight" in vs and vs["weight"] > 0: self.f_weight.setValue(vs["weight"])
                if "bp" in vs and vs["bp"]: self.f_bp.setText(vs["bp"])
                if "pulse" in vs and vs["pulse"] > 0: self.f_heart_rate.setValue(vs["pulse"])
                if "temp" in vs and vs["temp"] > 0: self.f_temp.setValue(vs["temp"])
                if "spo2" in vs and vs["spo2"] > 0: self.f_spo2.setValue(vs["spo2"])
            except Exception:
                pass

    def get_data(self):
        return {
            "symptoms":        self.f_symptoms.toPlainText().strip(),
            "medical_history": self.f_history.toPlainText().strip(),
            "diagnosis":       self.f_diagnosis.toPlainText().strip(),
            "conclusion":      self.f_conclusion.toPlainText().strip(),
            "treatment_plan":  self.f_treatment.toPlainText().strip(),
            "follow_up_date":  (self.f_followup.date().toString("yyyy-MM-dd")
                                if self.f_need_followup.isChecked() else None),
            "notes":           self.f_notes.toPlainText().strip(),
            "height":          self.f_height.value() or None,
            "weight":          self.f_weight.value() or None,
            "blood_pressure":  self.f_bp.text().strip() or None,
            "heart_rate":      self.f_heart_rate.value() or None,
            "temperature":     self.f_temp.value() or None,
            "spo2":            self.f_spo2.value() or None,
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

        # Send orders button
        btn_send = QPushButton("📤 Gửi chỉ định xuống Khoa Xét nghiệm")
        btn_send.setObjectName("primaryBtn")
        btn_send.setStyleSheet("background:#2b6cb0; color:white; padding:8px; border-radius:6px; font-weight:bold;")
        btn_send.clicked.connect(self._send_orders)
        layout.addWidget(btn_send)

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

    def _send_orders(self):
        orders = self.get_orders()
        if not orders["tests"]:
            QMessageBox.warning(self, "Trống", "Vui lòng chọn ít nhất một xét nghiệm.")
            return

        user = auth.get_current_user()
        doc_staff_id = dao.get_staff_id_by_user_id(user["id"]) if user else None

        for test_type in orders["tests"]:
            dao.add_lab_test({
                "patient_id":   self.patient["id"],
                "doctor_id":    doc_staff_id,
                "test_type":    test_type,
                "ordered_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "status":       "Chờ",
                "notes":        f"[{orders['priority']}] {orders['notes']}",
            })

        QMessageBox.information(self, "Thành công", f"Đã gửi {len(orders['tests'])} chỉ định xét nghiệm.")
        for cb in self._checkboxes.values():
            cb.setChecked(False)
        self.lab_orders.clear()
        if hasattr(self, 'custom_input'):
            self.custom_input.clear()
        self._update_list()


# ═══════════════════════════════════════════════════════════
#  Tab Kết quả
# ═══════════════════════════════════════════════════════════
class ResultTab(QWidget):
    def __init__(self, patient, exam_tab):
        super().__init__()
        self.patient = patient
        self.exam_tab = exam_tab
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(10)

        group_nurse = QGroupBox("Dữ liệu của Y tá (Chỉ số sinh tồn)")
        gn_layout = QVBoxLayout(group_nurse)
        self.f_nurse_data = QTextEdit()
        self.f_nurse_data.setReadOnly(True)
        self.f_nurse_data.setMaximumHeight(50)
        gn_layout.addWidget(self.f_nurse_data)
        layout.addWidget(group_nurse)

        group_lab = QGroupBox("Kết quả xét nghiệm")
        gl_layout = QVBoxLayout(group_lab)
        self.f_lab_results = QTextEdit()
        self.f_lab_results.setReadOnly(True)
        gl_layout.addWidget(self.f_lab_results)
        btn_refresh = QPushButton("🔄 Làm mới kết quả XN")
        btn_refresh.clicked.connect(self.refresh_data)
        gl_layout.addWidget(btn_refresh)
        layout.addWidget(group_lab)

        group_doc = QGroupBox("Chẩn đoán và Kết luận")
        gd_layout = QVBoxLayout(group_doc)
        self.f_doc_diag = QTextEdit()
        self.f_doc_diag.setReadOnly(True)
        self.f_doc_diag.setMaximumHeight(50)
        self.f_doc_concl = QTextEdit()
        self.f_doc_concl.setReadOnly(True)
        self.f_doc_concl.setMaximumHeight(50)
        gd_layout.addWidget(QLabel("Chẩn đoán:"))
        gd_layout.addWidget(self.f_doc_diag)
        gd_layout.addWidget(QLabel("Kết luận cuối cùng:"))
        gd_layout.addWidget(self.f_doc_concl)
        layout.addWidget(group_doc)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.refresh_data)
        self.timer.start(5000)

        self.refresh_data()

    def refresh_data(self):
        note = dao.get_latest_nursing_note_for_patient_today(self.patient["id"])
        if note and note["vital_signs"]:
            try:
                vs = json.loads(note["vital_signs"])
                text = f"Chiều cao: {vs.get('height', '—')} cm | Cân nặng: {vs.get('weight', '—')} kg | Huyết áp: {vs.get('bp', '—')} | Nhịp tim: {vs.get('pulse', '—')} | Nhiệt độ: {vs.get('temp', '—')} °C | SpO2: {vs.get('spo2', '—')} %"
                self.f_nurse_data.setText(text)
            except:
                self.f_nurse_data.setText("Không có dữ liệu sinh tồn hợp lệ trong ngày.")
        else:
            self.f_nurse_data.setText("Chưa có ghi chú chăm sóc trong ngày.")

        tests = dao.get_all_lab_tests(self.patient["patient_code"], "")
        today = datetime.now().strftime("%Y-%m-%d")
        today_tests = [t for t in tests if t["ordered_date"] and t["ordered_date"].startswith(today)]
        if not today_tests:
            self.f_lab_results.setText("Không có xét nghiệm nào được chỉ định trong ngày hôm nay.")
        else:
            res_text = ""
            for t in today_tests:
                res_text += f"[{t['ordered_date'][11:16]}] {t['test_type']} - Trạng thái: {t['status']}\n"
                if t["result"]:
                    res_text += f"Kết quả:\n{t['result']}\n"
                res_text += "-"*40 + "\n"
            self.f_lab_results.setText(res_text)

        diag = self.exam_tab.f_diagnosis.toPlainText()
        self.f_doc_diag.setText(diag if diag else "Chưa nhập chẩn đoán.")
        concl = self.exam_tab.f_conclusion.toPlainText()
        self.f_doc_concl.setText(concl if concl else "Chưa nhập kết luận.")


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

        # Warning panel
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
        self._check_warnings()

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
        self._check_warnings()

    def _check_warnings(self):
        self.warn_lbl.clear()
        if not self.rx_items:
            self.warn_frame.hide(); return

        msgs = []
        has_danger = False

        # 1. Allergy check
        allergies_str = (self.patient["allergies"] or "").lower()
        import re
        allergies = [a.strip() for a in re.split(r'[,;]+', allergies_str) if a.strip()]
        
        for item in self.rx_items:
            med_info = next((m for m in self.medicines if m["id"] == item["medicine_id"]), None)
            if med_info:
                med_text = f"{med_info['name']} {med_info['generic_name']} {med_info['category']}".lower()
                for allergy in allergies:
                    if len(allergy) > 2 and allergy in med_text:
                        msgs.append(f"🔴 <b>CẢNH BÁO DỊ ỨNG:</b> Bệnh nhân dị ứng '{allergy}' -> <b>{med_info['name']}</b>")
                        has_danger = True

        if not msgs:
            self.warn_frame.hide(); return

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
#  Save Success & Print Dialog
# ═══════════════════════════════════════════════════════════
class SaveSuccessDialog(QDialog):
    def __init__(self, summary, patient, exam_data, rx_data, lab_data, doctor_name,
                 department=None, record_id=None, presc_id=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Lưu thành công")
        self.setMinimumWidth(400)
        self.patient     = patient
        self.exam_data   = exam_data
        self.rx_data     = rx_data
        self.lab_data    = lab_data
        self.doctor_name = doctor_name
        self.department  = department or "—"
        self.phieu_code  = f"PK{datetime.now().year}{(record_id or 0):04d}"
        self.don_code    = f"DT{datetime.now().year}{(presc_id or 0):04d}" if presc_id else None

        layout = QVBoxLayout(self)

        lbl = QLabel(summary)
        lbl.setWordWrap(True)
        lbl.setStyleSheet("font-size: 13px; color: #2d3748; padding: 10px;")
        layout.addWidget(lbl)

        btn_layout = QHBoxLayout()

        self.btn_print_exam = QPushButton("🖨️ In phiếu khám bệnh")
        self.btn_print_exam.setStyleSheet("padding: 8px; background: #3182ce; color: white; border-radius: 4px;")
        self.btn_print_exam.clicked.connect(self._print_exam)
        btn_layout.addWidget(self.btn_print_exam)

        self.btn_print_rx = QPushButton("🖨️ In đơn thuốc")
        self.btn_print_rx.setStyleSheet("padding: 8px; background: #3182ce; color: white; border-radius: 4px;")
        self.btn_print_rx.clicked.connect(self._print_rx)
        if not self.rx_data.get("items"):
            self.btn_print_rx.setEnabled(False)
            self.btn_print_rx.setStyleSheet("padding: 8px; background: #cbd5e0; color: #718096; border-radius: 4px;")
        btn_layout.addWidget(self.btn_print_rx)

        self.btn_close = QPushButton("Đóng")
        self.btn_close.setStyleSheet("padding: 8px; background: #e2e8f0; border-radius: 4px;")
        self.btn_close.clicked.connect(self.accept)
        btn_layout.addWidget(self.btn_close)

        layout.addLayout(btn_layout)

    def _logo_html(self):
        try:
            logo_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'assets', 'logo.png'
            )
            if os.path.exists(logo_path):
                return f'<div style="text-align:left; margin-bottom:10px;"><img src="file:///{logo_path}" width="65" height="65"></div>'
        except Exception:
            pass
        return ""

    def _checklist_items(self):
        tests = [t.lower() for t in self.lab_data.get('tests', [])]
        def has(*keywords):
            return any(any(k in t for k in keywords) for t in tests)
        return [
            ("Kê đơn thuốc",        bool(self.rx_data.get('items'))),
            ("Xét nghiệm máu",      has("máu")),
            ("Xét nghiệm nước tiểu", has("nước tiểu")),
            ("Chụp X-Quang",        has("x-quang", "x quang")),
            ("Siêu âm",             has("siêu âm")),
            ("CT Scan",             has("ct scan", "ct ")),
            ("MRI",                 has("mri")),
            ("Tái khám",            bool(self.exam_data.get('follow_up_date'))),
        ]

    def _print_exam(self):
        vitals_html = f"""
        <table class="vitals-table">
            <tr>
                <td><b>Chiều cao:</b> {self.exam_data.get('height') or '—'} cm</td>
                <td><b>Cân nặng:</b> {self.exam_data.get('weight') or '—'} kg</td>
            </tr>
            <tr>
                <td><b>Huyết áp:</b> {self.exam_data.get('blood_pressure') or '—'} mmHg</td>
                <td><b>Nhịp tim:</b> {self.exam_data.get('heart_rate') or '—'} lần/phút</td>
            </tr>
            <tr>
                <td><b>Nhiệt độ:</b> {self.exam_data.get('temperature') or '—'} °C</td>
                <td><b>SpO2:</b> {self.exam_data.get('spo2') or '—'} %</td>
            </tr>
        </table>
        """

        checklist_html = "".join(
            f"<div class='check-item'>{'☑' if checked else '☐'} {label}</div>"
            for label, checked in self._checklist_items()
        )

        html = f"""
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body {{ font-family: 'Roboto', 'Noto Sans', Arial, sans-serif; font-size: 13pt; line-height: 1.6; color: #333; }}
                h2 {{ text-align: center; margin: 0; font-size: 22pt; color: #0D47A1; letter-spacing: 1px; }}
                h4 {{ text-align: center; margin-top: 2px; font-weight: normal; font-size: 14pt; color: #666; text-transform: uppercase; }}
                .code-row {{ text-align: center; font-size: 12pt; color: #555; margin: 4px 0 10px 0; }}
                hr {{ border: 0; border-top: 2px solid #1565C0; margin: 10px 0 18px 0; }}
                .section-title {{ font-weight: bold; font-size: 15pt; color: #0D47A1; margin: 16px 0 8px 0;
                                   border-bottom: 1px solid #DADCE0; padding-bottom: 4px; }}
                .info-table {{ width: 100%; border: none; margin-bottom: 6px; }}
                .info-table td {{ padding: 3px 4px; border: none; vertical-align: top; font-size: 13pt; }}
                .vitals-table {{ width: 100%; border-collapse: collapse; margin-bottom: 6px; }}
                .vitals-table td {{ border: 1px solid #DADCE0; padding: 6px 10px; width: 50%; font-size: 13pt; }}
                .check-item {{ display: inline-block; width: 48%; padding: 3px 0; font-size: 13pt; }}
                .sign {{ text-align: center; float: right; width: 250px; margin-top: 30px; font-size: 13pt; }}
                .text-block {{ margin: 4px 0 0 0; min-height: 16px; font-size: 13pt; }}
            </style>
        </head>
        <body>
            {self._logo_html()}
            <h2>PHIẾU KHÁM BỆNH</h2>
            <h4>HOSPITAL MANAGEMENT SYSTEM</h4>
            <div class="code-row">Mã phiếu: {self.phieu_code} &nbsp;&nbsp;|&nbsp;&nbsp; Ngày khám: {datetime.now().strftime('%d/%m/%Y')}</div>
            <hr>

            <div class="section-title">THÔNG TIN BỆNH NHÂN</div>
            <table class="info-table">
                <tr>
                    <td style="width:15%;"><b>Họ và tên:</b></td>
                    <td style="width:35%;">{self.patient['full_name']}</td>
                    <td style="width:15%;"><b>Mã BN:</b></td>
                    <td style="width:35%;">{self.patient['patient_code']}</td>
                </tr>
                <tr>
                    <td><b>Ngày sinh:</b></td>
                    <td>{self.patient['birth_date'] or '—'}</td>
                    <td><b>Giới tính:</b></td>
                    <td>{self.patient['gender'] or '—'}</td>
                </tr>
                <tr>
                    <td><b>SĐT:</b></td>
                    <td>{self.patient['phone'] or '—'}</td>
                    <td><b>Địa chỉ:</b></td>
                    <td>{self.patient['address'] or '—'}</td>
                </tr>
            </table>

            <div class="section-title">THÔNG TIN KHÁM</div>
            <table class="info-table">
                <tr>
                    <td style="width:15%;"><b>Bác sĩ khám:</b></td>
                    <td style="width:35%;">BS. {self.doctor_name}</td>
                    <td style="width:15%;"><b>Khoa:</b></td>
                    <td style="width:35%;">{self.department}</td>
                </tr>

            </table>

            <div class="section-title">CHỈ SỐ SINH TỒN</div>
            {vitals_html}

            <div class="section-title">TRIỆU CHỨNG</div>
            <div class="text-block">{self.exam_data.get('symptoms', '') or '—'}</div>

            <div class="section-title">TIỀN SỬ BỆNH</div>
            <div class="text-block">{self.exam_data.get('medical_history', '') or '—'}</div>

            <div class="section-title">CHẨN ĐOÁN</div>
            <div class="text-block">{self.exam_data.get('diagnosis', '') or '—'}</div>

            <div class="section-title">KẾT LUẬN KHÁM</div>
            <div class="text-block">{self.exam_data.get('conclusion', '') or '—'}</div>

            <div class="section-title">CHỈ ĐỊNH</div>
            {checklist_html}

            <div class="section-title">LỜI DẶN CỦA BÁC SĨ</div>
            <div class="text-block">{self.exam_data.get('notes', '') or '—'}</div>

            <div class="section-title">NGÀY TÁI KHÁM</div>
            <div class="text-block">{self.exam_data.get('follow_up_date') or 'Không hẹn tái khám'}</div>

            <div class="sign">
                <p>Đà Nẵng, ngày {datetime.now().strftime('%d')} tháng {datetime.now().strftime('%m')} năm {datetime.now().strftime('%Y')}</p>
                <p><b>BÁC SĨ KHÁM</b><br><i>(Ký và ghi rõ họ tên)</i></p>
                <br><br><br><br>
                <p>BS. {self.doctor_name}</p>
            </div>
        </body>
        </html>
        """
        self._do_print(html, f"phieu_kham_{self.phieu_code}.pdf")

    def _print_rx(self):
        rows = ""
        for i, item in enumerate(self.rx_data.get('items', [])):
            bg_color = "#FFFFFF" if i % 2 == 0 else "#E3F2FD"
            rows += f"""
            <tr style="background-color: {bg_color};">
                <td style="text-align:center;">{i+1}</td>
                <td>{item['name']}</td>
                <td style="text-align:center;">{item.get('unit','') or '—'}</td>
                <td style="text-align:center;">{item['quantity']}</td>
                <td style="text-align:center;">{item['dosage']}</td>
                <td style="text-align:center;">{item['duration_days']} ngày</td>
                <td>{item.get('notes', '') or ''}</td>
            </tr>
            """

        html = f"""
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body {{ font-family: 'Roboto', 'Noto Sans', Arial, sans-serif; font-size: 13pt; line-height: 1.6; color: #333; }}
                h2 {{ text-align: center; margin: 0; font-size: 22pt; color: #0D47A1; letter-spacing: 1px; }}
                h4 {{ text-align: center; margin-top: 2px; font-weight: normal; font-size: 14pt; color: #666; text-transform: uppercase; }}
                .code-row {{ text-align: center; font-size: 12pt; color: #555; margin: 4px 0 10px 0; }}
                hr {{ border: 0; border-top: 2px solid #1565C0; margin: 10px 0 18px 0; }}
                .section-title {{ font-weight: bold; font-size: 15pt; color: #0D47A1; margin: 16px 0 8px 0;
                                   border-bottom: 1px solid #DADCE0; padding-bottom: 4px; }}
                .info-table {{ width: 100%; border: none; margin-bottom: 6px; }}
                .info-table td {{ padding: 3px 4px; border: none; font-size: 13pt; }}
                .rx-table {{ width: 100%; border-collapse: collapse; margin-top: 8px; }}
                .rx-table th, .rx-table td {{ border: 1px solid #DADCE0; padding: 7px; font-size: 12pt; }}
                .rx-table th {{ background-color: #1565C0; color: white; text-align: center; font-weight: bold; font-size: 13pt; }}
                .note-list {{ margin: 4px 0 0 18px; padding: 0; font-size: 13pt; }}
                .note-list li {{ margin-bottom: 3px; }}
                .sign {{ text-align: center; float: right; width: 250px; margin-top: 30px; font-size: 13pt; }}
            </style>
        </head>
        <body>
            {self._logo_html()}
            <h2>ĐƠN THUỐC</h2>
            <h4>HOSPITAL MANAGEMENT SYSTEM</h4>
            <div class="code-row">Mã đơn: {self.don_code or '—'} &nbsp;&nbsp;|&nbsp;&nbsp; Ngày kê đơn: {datetime.now().strftime('%d/%m/%Y')}</div>
            <hr>

            <div class="section-title">THÔNG TIN BỆNH NHÂN</div>
            <table class="info-table">
                <tr>
                    <td style="width:15%;"><b>Họ và tên:</b></td>
                    <td style="width:35%;">{self.patient['full_name']}</td>
                    <td style="width:15%;"><b>Bác sĩ:</b></td>
                    <td style="width:35%;">BS. {self.doctor_name}</td>
                </tr>
                <tr>
                    <td><b>Ngày sinh:</b></td>
                    <td>{self.patient['birth_date'] or '—'}</td>
                    <td><b>Khoa khám:</b></td>
                    <td>{self.department}</td>
                </tr>
                <tr>
                    <td><b>Giới tính:</b></td>
                    <td>{self.patient['gender'] or '—'}</td>
                    <td><b>SĐT:</b></td>
                    <td>{self.patient['phone'] or '—'}</td>
                </tr>
            </table>

            <div class="section-title">CHI TIẾT ĐƠN THUỐC</div>
            <table class="rx-table">
                <tr>
                    <th style="width:5%;">STT</th>
                    <th style="width:25%;">Tên thuốc</th>
                    <th style="width:10%;">Đơn vị</th>
                    <th style="width:10%;">Số lượng</th>
                    <th style="width:20%;">Liều dùng</th>
                    <th style="width:10%;">Số ngày</th>
                    <th style="width:20%;">Ghi chú</th>
                </tr>
                {rows}
            </table>

            <div class="section-title">HƯỚNG DẪN SỬ DỤNG THUỐC</div>
            <ul class="note-list">
                <li>Uống thuốc đúng liều lượng được kê.</li>
                <li>Không tự ý ngưng thuốc khi chưa có chỉ định.</li>
                <li>Báo ngay cho bác sĩ nếu xuất hiện dấu hiệu dị ứng.</li>
            </ul>

            <div class="section-title">LỜI DẶN CỦA BÁC SĨ</div>
            <p>{self.rx_data.get('notes', '') or '—'}</p>

            <div class="section-title">THÔNG TIN TÁI KHÁM</div>
            <p>Ngày tái khám: {self.exam_data.get('follow_up_date') or 'Không hẹn tái khám'}<br>
               Ghi chú: Mang theo đơn thuốc và kết quả xét nghiệm (nếu có).</p>

            <div class="sign">
                <p>Đà Nẵng, ngày {datetime.now().strftime('%d')} tháng {datetime.now().strftime('%m')} năm {datetime.now().strftime('%Y')}</p>
                <p><b>BÁC SĨ ĐIỀU TRỊ</b><br><i>(Ký và ghi rõ họ tên)</i></p>
                <br><br><br><br>
                <p>BS. {self.doctor_name}</p>
            </div>
        </body>
        </html>
        """
        self._do_print(html, f"don_thuoc_{self.don_code or self.patient['patient_code']}.pdf")

    def _do_print(self, html, default_filename="export.pdf"):
        from PyQt6.QtWidgets import QFileDialog, QMessageBox

        # Thư mục mặc định cross-platform (thay vì hardcode C:\Users\Admin\...)
        export_dir = os.path.join(os.path.expanduser("~"), "Downloads", "HospitalExports")
        if not os.path.exists(export_dir):
            try:
                os.makedirs(export_dir, exist_ok=True)
            except Exception:
                export_dir = os.path.expanduser("~")

        default_path = os.path.join(export_dir, default_filename)

        filepath, _ = QFileDialog.getSaveFileName(
            self, "Lưu file PDF", default_path, "PDF Files (*.pdf)"
        )
        if not filepath:
            return

        from PyQt6.QtGui import QPageSize
        printer = QPrinter()
        printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
        printer.setOutputFileName(filepath)
        printer.setPageSize(QPageSize(QPageSize.PageSizeId.A4))

        doc = QTextDocument()
        doc.setHtml(html)
        doc.print(printer)

        QMessageBox.information(self, "Thành công", f"Đã lưu thành file:\n{filepath}")


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
        self.result_tab = ResultTab(self.patient, self.exam_tab)
        self.rx_tab   = PrescriptionTab(self.patient)

        self.tabs.addTab(self.exam_tab, "1️⃣  Khám & Chẩn đoán")
        self.tabs.addTab(self.lab_tab,  "2️⃣  Chỉ định Xét nghiệm")
        self.tabs.addTab(self.result_tab, "3️⃣  Kết quả")
        self.tabs.addTab(self.rx_tab,   "4️⃣  Kê đơn thuốc")

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
        if idx == 2:
            self.result_tab.refresh_data()
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

        # Warn dangerous allergies
        if rx_data["items"]:
            danger_msgs = []
            med_ids  = [i["medicine_id"] for i in rx_data["items"]]
            
            allergies_str = (self.patient["allergies"] or "").lower()
            import re
            allergies = [a.strip() for a in re.split(r'[,;]+', allergies_str) if a.strip()]
            for item in rx_data["items"]:
                med_info = next((m for m in self.rx_tab.medicines if m["id"] == item["medicine_id"]), None)
                if med_info:
                    med_text = f"{med_info['name']} {med_info['generic_name']} {med_info['category']}".lower()
                    for allergy in allergies:
                        if len(allergy) > 2 and allergy in med_text:
                            danger_msgs.append(f"- Dị ứng '{allergy}' với {med_info['name']}")
            
            if danger_msgs:
                reply = QMessageBox.warning(
                    self, "⚠️ CẢNH BÁO NGUY HIỂM",
                    "Phát hiện cảnh báo nguy hiểm hoặc dị ứng thuốc:\n" + "\n".join(danger_msgs) +
                    "\n\nBạn có chắc muốn lưu đơn này không?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                if reply != QMessageBox.StandardButton.Yes:
                    self.tabs.setCurrentIndex(2); return

        user = auth.get_current_user()
        # Resolve users.id -> staff.id so FK columns point to the right row
        doc_staff_id = dao.get_staff_id_by_user_id(user["id"]) if user else None

        # Khoa để in lên phiếu
        department = None
        if doc_staff_id:
            staff_row = dao.get_staff_by_id(doc_staff_id)
            department = staff_row["dept_name"] if staff_row else None

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
        presc_id = None
        if rx_data["items"]:
            try:
                presc_id = dao.save_prescription({
                    "medical_record_id": record_id,
                    "doctor_id":         doc_staff_id,
                    "notes":             rx_data["notes"],
                    "items":             rx_data["items"],
                })
            except ValueError as e:
                dao.delete_medical_record(record_id)
                QMessageBox.critical(
                    self, "Không đủ tồn kho",
                    str(e) + "\n\nĐơn thuốc chưa được lưu.\n"
                             "Vui lòng điều chỉnh số lượng và thử lại."
                )
                self.tabs.setCurrentIndex(2)
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

        doc_name = user['full_name'] if user else '—'
        dialog = SaveSuccessDialog(
            summary, self.patient, exam_data, rx_data, lab_data, doc_name,
            department=department,
            record_id=record_id, presc_id=presc_id, parent=self
        )
        dialog.exec()
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

        /* Warning */
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
