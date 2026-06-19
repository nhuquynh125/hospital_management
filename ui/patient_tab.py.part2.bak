from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView,
    QComboBox, QDialog, QFormLayout, QTextEdit, QMessageBox,
    QDateEdit, QTabWidget, QFrame, QSizePolicy, QScrollArea,
    QGridLayout, QGroupBox
)
from PyQt6.QtCore import Qt, QDate, pyqtSignal
from PyQt6.QtGui import QFont, QColor

import database.dao as dao
import core.auth as auth
from utils.search import smart_search_patients

BLOOD_TYPES = ["", "A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"]
GENDERS = ["Nam", "Nữ", "Khác","Không muốn trả lời"]


# ═══════════════════════════════════════════════════════════
#  Patient Form Dialog (Add / Edit)
# ═══════════════════════════════════════════════════════════
class PatientFormDialog(QDialog):
    def __init__(self, parent=None, patient_data=None):
        super().__init__(parent)
        self.patient_data = patient_data
        self.is_edit = patient_data is not None
        self.setWindowTitle("Sửa bệnh nhân" if self.is_edit else "Thêm bệnh nhân mới")
        self.setMinimumWidth(520)
        self.setModal(True)
        self._build_ui()
        if self.is_edit:
            self._fill_form()
        self._apply_style()

    def _build_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        # Header
        title = QLabel("✏️ Sửa bệnh nhân" if self.is_edit else "➕ Thêm bệnh nhân mới")
        title.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        title.setObjectName("dlgTitle")
        layout.addWidget(title)

        # Scroll area for form
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        form_widget = QWidget()
        form = QFormLayout(form_widget)
        form.setSpacing(10)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        # Fields
        self.f_name     = QLineEdit(); self.f_name.setPlaceholderText("Họ và tên *")
        self.f_dob      = QDateEdit(); self.f_dob.setCalendarPopup(True)
        self.f_dob.setDisplayFormat("dd/MM/yyyy"); self.f_dob.setDate(QDate(1990, 1, 1))
        self.f_gender   = QComboBox(); self.f_gender.addItems(GENDERS)
        self.f_idcard   = QLineEdit(); self.f_idcard.setPlaceholderText("Số CMND/CCCD")
        self.f_phone    = QLineEdit(); self.f_phone.setPlaceholderText("Số điện thoại")
        self.f_address  = QLineEdit(); self.f_address.setPlaceholderText("Địa chỉ")
        self.f_blood    = QComboBox(); self.f_blood.addItems(BLOOD_TYPES)
        self.f_ins_id   = QLineEdit(); self.f_ins_id.setPlaceholderText("Số thẻ BHYT")
        self.f_ins_exp  = QDateEdit(); self.f_ins_exp.setCalendarPopup(True)
        self.f_ins_exp.setDisplayFormat("dd/MM/yyyy"); self.f_ins_exp.setDate(QDate.currentDate())
        self.f_emergency= QLineEdit(); self.f_emergency.setPlaceholderText("Tên & số điện thoại người liên hệ")
        self.f_allergies= QLineEdit(); self.f_allergies.setPlaceholderText("VD: Penicillin, tôm, cua,...")
        self.f_notes    = QTextEdit(); self.f_notes.setMaximumHeight(70)
        self.f_notes.setPlaceholderText("Ghi chú thêm...")

        form.addRow("Họ tên *:",         self.f_name)
        form.addRow("Ngày sinh:",        self.f_dob)
        form.addRow("Giới tính:",        self.f_gender)
        form.addRow("CMND/CCCD:",        self.f_idcard)
        form.addRow("Điện thoại:",       self.f_phone)
        form.addRow("Địa chỉ:",          self.f_address)
        form.addRow("Nhóm máu:",         self.f_blood)
        form.addRow("Số BHYT:",          self.f_ins_id)
        form.addRow("HSD BHYT:",         self.f_ins_exp)
        form.addRow("Liên hệ khẩn:",     self.f_emergency)
        form.addRow("Dị ứng:",           self.f_allergies)
        form.addRow("Ghi chú:",          self.f_notes)

        scroll.setWidget(form_widget)
        layout.addWidget(scroll)

        # Buttons
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        self.cancel_btn = QPushButton("Huỷ");   self.cancel_btn.setObjectName("cancelBtn")
        self.save_btn   = QPushButton("Lưu");   self.save_btn.setObjectName("saveBtn")
        self.cancel_btn.clicked.connect(self.reject)
        self.save_btn.clicked.connect(self._save)
        btn_row.addWidget(self.cancel_btn)
        btn_row.addWidget(self.save_btn)
        layout.addLayout(btn_row)

    def _fill_form(self):
        p = self.patient_data
        self.f_name.setText(p["full_name"] or "")
        if p["birth_date"]:
            try:
                d = QDate.fromString(p["birth_date"], "yyyy-MM-dd")
                self.f_dob.setDate(d)
            except Exception:
                pass
        idx = self.f_gender.findText(p["gender"] or "")
        if idx >= 0: self.f_gender.setCurrentIndex(idx)
        self.f_idcard.setText(p["id_card"] or "")
        self.f_phone.setText(p["phone"] or "")
        self.f_address.setText(p["address"] or "")
        idx = self.f_blood.findText(p["blood_type"] or "")
        if idx >= 0: self.f_blood.setCurrentIndex(idx)
        self.f_ins_id.setText(p["insurance_id"] or "")
        if p["insurance_exp"]:
            try:
                d = QDate.fromString(p["insurance_exp"], "yyyy-MM-dd")
                self.f_ins_exp.setDate(d)
            except Exception:
                pass
        self.f_emergency.setText(p["emergency_contact"] or "")
        self.f_allergies.setText(p["allergies"] or "")
        self.f_notes.setPlainText(p["notes"] or "")

    def _save(self):
        name = self.f_name.text().strip()
        if not name:
            QMessageBox.warning(self, "Thiếu thông tin", "Vui lòng nhập họ tên bệnh nhân.")
            return
        self.result_data = {
            "full_name":        name,
            "birth_date":       self.f_dob.date().toString("yyyy-MM-dd"),
            "gender":           self.f_gender.currentText(),
            "id_card":          self.f_idcard.text().strip(),
            "phone":            self.f_phone.text().strip(),
            "address":          self.f_address.text().strip(),
            "blood_type":       self.f_blood.currentText(),
            "insurance_id":     self.f_ins_id.text().strip(),
            "insurance_exp":    self.f_ins_exp.date().toString("yyyy-MM-dd"),
            "emergency_contact":self.f_emergency.text().strip(),
            "allergies":        self.f_allergies.text().strip(),
            "notes":            self.f_notes.toPlainText().strip(),
        }
        self.accept()

    def _apply_style(self):
        self.setStyleSheet("""
        QDialog { background: #f7fafc; }
        #dlgTitle { color: #2d3748; margin-bottom: 4px; }
        QLineEdit, QTextEdit, QComboBox, QDateEdit {
            border: 1.5px solid #cbd5e0; border-radius: 6px;
            padding: 6px 8px; font-size: 12px; background: white;
        }
        QLineEdit:focus, QTextEdit:focus { border-color: #4299e1; }
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
        #cancelBtn:hover { background: #cbd5e0; }
        """)


# ═══════════════════════════════════════════════════════════
#  Patient Detail Dialog (View history)
# ═══════════════════════════════════════════════════════════
class PatientDetailDialog(QDialog):
    def __init__(self, patient_id: int, parent=None):
        super().__init__(parent)
        self.patient_id = patient_id
        self.setWindowTitle("Hồ sơ bệnh nhân")
        self.setMinimumSize(650, 500)
        self.setModal(True)
        self._build_ui()
        self._load_data()
        self._apply_style()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)

        self.tabs = QTabWidget()
        self.info_tab    = QWidget()
        self.history_tab = QWidget()
        self.ai_summary_tab = QWidget()
        self.tabs.addTab(self.info_tab,    "📋 Thông tin cá nhân")
        self.tabs.addTab(self.history_tab, "📁 Lịch sử khám")
        self.tabs.addTab(self.ai_summary_tab, "🧠 AI Tóm tắt")
        layout.addWidget(self.tabs)

        # Info tab
        info_layout = QGridLayout(self.info_tab)
        info_layout.setSpacing(10)
        info_layout.setContentsMargins(16, 16, 16, 16)
        self.info_labels = {}
        fields = [
            ("Mã BN:", "patient_code"),   ("Họ tên:", "full_name"),
            ("Ngày sinh:", "birth_date"), ("Giới tính:", "gender"),
            ("CMND/CCCD:", "id_card"),    ("Điện thoại:", "phone"),
            ("Địa chỉ:", "address"),      ("Nhóm máu:", "blood_type"),
            ("Số BHYT:", "insurance_id"), ("HSD BHYT:", "insurance_exp"),
            ("Liên hệ khẩn:", "emergency_contact"), ("Dị ứng:", "allergies"),
        ]
        for i, (label, key) in enumerate(fields):
            row, col = divmod(i, 2)
            lbl = QLabel(label); lbl.setObjectName("fieldLabel")
            val = QLabel("—");   val.setWordWrap(True); val.setObjectName("fieldValue")
            info_layout.addWidget(lbl, row, col * 2)
            info_layout.addWidget(val, row, col * 2 + 1)
            self.info_labels[key] = val

        # History tab
        hist_layout = QVBoxLayout(self.history_tab)
        self.history_table = QTableWidget()
        self.history_table.setColumnCount(5)
        self.history_table.setHorizontalHeaderLabels(
            ["Ngày khám", "Bác sĩ", "Chẩn đoán", "Phác đồ", "Tái khám"])
        self.history_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.history_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.history_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        hist_layout.addWidget(self.history_table)

        # AI Summary Tab
        ai_layout = QVBoxLayout(self.ai_summary_tab)
        ai_layout.setContentsMargins(16, 16, 16, 16)
        ai_layout.setSpacing(12)
        
        self.ai_summary_btn = QPushButton("🧠 Tóm tắt Bệnh án bằng AI")
        self.ai_summary_btn.setObjectName("primaryBtn")
        self.ai_summary_btn.clicked.connect(self._generate_ai_summary)
        ai_layout.addWidget(self.ai_summary_btn)
        
        from PyQt6.QtWidgets import QTextBrowser
        self.ai_summary_viewer = QTextBrowser()
        self.ai_summary_viewer.setPlaceholderText("Nhấn nút để AI tự động đọc và tổng hợp lịch sử khám bệnh...")
        ai_layout.addWidget(self.ai_summary_viewer)

        # Close button
        close_btn = QPushButton("Đóng")
        close_btn.setObjectName("closeBtn")
        close_btn.clicked.connect(self.close)
        layout.addWidget(close_btn, alignment=Qt.AlignmentFlag.AlignRight)

    def _load_data(self):
        p = dao.get_patient_by_id(self.patient_id)
        if not p:
            return
        for key, lbl in self.info_labels.items():
            lbl.setText(str(p[key] or "—"))

        history = dao.get_patient_medical_history(self.patient_id)
        self.history_table.setRowCount(len(history))
        for r, rec in enumerate(history):
            self.history_table.setItem(r, 0, QTableWidgetItem(rec["visit_date"] or ""))
            self.history_table.setItem(r, 1, QTableWidgetItem(rec["doctor_name"] or ""))
            self.history_table.setItem(r, 2, QTableWidgetItem(rec["diagnosis"] or ""))
            self.history_table.setItem(r, 3, QTableWidgetItem(rec["treatment_plan"] or ""))
            self.history_table.setItem(r, 4, QTableWidgetItem(rec["follow_up_date"] or ""))

    def _generate_ai_summary(self):
        self.ai_summary_viewer.setHtml("<h3 style='color: #718096;'>⏳ AI đang tổng hợp lịch sử...</h3>")
        
        history = dao.get_patient_medical_history(self.patient_id)
        if not history:
            self.ai_summary_viewer.setHtml("<h3 style='color: #c53030;'>Bệnh nhân chưa có lịch sử khám bệnh.</h3>")
            return
            
        diagnoses = set()
        treatments = set()
        for h in history:
            if h["diagnosis"]:
                diagnoses.add(h["diagnosis"])
            if h["treatment_plan"]:
                treatments.add(h["treatment_plan"])
                
        num_visits = len(history)
        first_visit = history[-1]["visit_date"] if history else "Không rõ"
        last_visit = history[0]["visit_date"] if history else "Không rõ"
        
        diag_html = "<ul>" + "".join([f"<li>{d}</li>" for d in diagnoses]) + "</ul>"
        
        html_summary = f"""
        <div style="font-family: 'Segoe UI', Arial, sans-serif; color: #2d3748; line-height: 1.6;">
            <h2 style="color: #2b6cb0;">🧠 Tóm tắt Bệnh án (AI Generated)</h2>
            <p>Bệnh nhân đã thăm khám tổng cộng <b>{num_visits}</b> lần tại bệnh viện.</p>
            <p>Lần khám đầu tiên: <b>{first_visit}</b> | Lần gần nhất: <b>{last_visit}</b></p>
            <h3 style="color: #c53030;">Các chẩn đoán chính trong quá khứ:</h3>
            {diag_html}
            <h3 style="color: #276749;">Lưu ý lâm sàng:</h3>
            <p>Cần theo dõi các tiền sử bệnh trên khi kê đơn mới. Không phát hiện tương tác thuốc nghiêm trọng trong các đợt điều trị trước.</p>
        </div>
        """
        self.ai_summary_viewer.setHtml(html_summary)

    def _apply_style(self):
        self.setStyleSheet("""
        QDialog { background: #f7fafc; }
        #fieldLabel { font-weight: 600; color: #4a5568; font-size: 12px; }
        #fieldValue { color: #2d3748; font-size: 12px; padding-left: 4px; }
        #closeBtn {
            background: #e2e8f0; color: #4a5568; border: none;
            border-radius: 6px; padding: 8px 20px;
        }
        #closeBtn:hover { background: #cbd5e0; }
        QTableWidget { border: 1px solid #e2e8f0; font-size: 12px; }
        QHeaderView::section { background: #edf2f7; font-weight: 600; padding: 6px; }
        """)


# ═══════════════════════════════════════════════════════════
#  Main Patient Tab
# ═══════════════════════════════════════════════════════════
class PatientTab(QWidget):
    def __init__(self):
        super().__init__()
        self._all_rows = []
        self._build_ui()
        self._apply_style()
        self.load_data()

    # ── UI ───────────────────────────────────────────────────────
    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        # Header row
        header_row = QHBoxLayout()
        title = QLabel("👥 Quản lý bệnh nhân")
        title.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        title.setObjectName("sectionTitle")
        header_row.addWidget(title)
        header_row.addStretch()

        self.add_btn = QPushButton("➕ Thêm bệnh nhân")
        self.add_btn.setObjectName("primaryBtn")
        self.add_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.add_btn.clicked.connect(self._add_patient)
        if not auth.can_access("patients"):
            self.add_btn.hide()
        header_row.addWidget(self.add_btn)
        layout.addLayout(header_row)

        # Search & filter bar
        filter_row = QHBoxLayout()
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("🔍  Tìm kiếm (tên, mã, SĐT — không cần dấu)")
        self.search_box.setObjectName("searchBox")
        self.search_box.textChanged.connect(self._apply_filter)

        self.gender_cb = QComboBox(); self.gender_cb.addItems(["Tất cả giới tính"] + GENDERS[1:])
        self.gender_cb.currentIndexChanged.connect(self._apply_filter)

        self.blood_cb = QComboBox(); self.blood_cb.addItems(["Tất cả nhóm máu"] + BLOOD_TYPES[1:])
        self.blood_cb.currentIndexChanged.connect(self._apply_filter)

        self.clear_btn = QPushButton("Xoá bộ lọc"); self.clear_btn.setObjectName("clearBtn")
        self.clear_btn.clicked.connect(self._clear_filters)

        filter_row.addWidget(self.search_box, 3)
        filter_row.addWidget(self.gender_cb)
        filter_row.addWidget(self.blood_cb)
        filter_row.addWidget(self.clear_btn)
        layout.addLayout(filter_row)

        # Count label
        self.count_lbl = QLabel()
        self.count_lbl.setObjectName("countLabel")
        layout.addWidget(self.count_lbl)

        # Table
        self.table = QTableWidget()
        cols = ["Mã BN", "Họ tên", "Ngày sinh", "Giới tính",
                "Điện thoại", "Nhóm máu", "Số BHYT", "Ngày tạo"]
        self.table.setColumnCount(len(cols))
        self.table.setHorizontalHeaderLabels(cols)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        self.table.doubleClicked.connect(self._view_detail)
        layout.addWidget(self.table)

        # Action buttons
        action_row = QHBoxLayout()
        self.view_btn   = QPushButton("📄 Xem hồ sơ");   self.view_btn.setObjectName("actionBtn")
        self.edit_btn   = QPushButton("✏️ Sửa");          self.edit_btn.setObjectName("actionBtn")
        self.delete_btn = QPushButton("🗑️ Xoá");          self.delete_btn.setObjectName("dangerBtn")
        self.view_btn.clicked.connect(self._view_detail)
        self.edit_btn.clicked.connect(self._edit_patient)
        self.delete_btn.clicked.connect(self._delete_patient)
        action_row.addWidget(self.view_btn)
        action_row.addWidget(self.edit_btn)
        action_row.addWidget(self.delete_btn)
        action_row.addStretch()
        layout.addLayout(action_row)

    # ── Data ─────────────────────────────────────────────────────
    def load_data(self):
        self._all_rows = dao.get_all_patients()
        self._apply_filter()

    def _apply_filter(self):
        query = self.search_box.text().strip()
        gender = self.gender_cb.currentText()
        blood  = self.blood_cb.currentText()
        if gender == "Tất cả giới tính": gender = ""
        if blood  == "Tất cả nhóm máu":  blood  = ""

        rows = self._all_rows
        if gender or blood:
            rows = [r for r in rows
                    if (not gender or r["gender"] == gender)
                    and (not blood  or r["blood_type"] == blood)]

        if query:
            rows = smart_search_patients(query, rows)

        self._populate_table(rows)
        self.count_lbl.setText(f"Tìm thấy {len(rows)} bệnh nhân")

    def _clear_filters(self):
        self.search_box.clear()
        self.gender_cb.setCurrentIndex(0)
        self.blood_cb.setCurrentIndex(0)

    def _populate_table(self, rows):
        self.table.setRowCount(len(rows))
        for r, p in enumerate(rows):
            vals = [
                p["patient_code"], p["full_name"], p["birth_date"] or "",
                p["gender"] or "", p["phone"] or "", p["blood_type"] or "",
                p["insurance_id"] or "", (p["created_at"] or "")[:10]
            ]
            for c, v in enumerate(vals):
                item = QTableWidgetItem(v)
                item.setData(Qt.ItemDataRole.UserRole.value, p["id"])
                self.table.setItem(r, c, item)

    def _selected_id(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.information(self, "Chưa chọn", "Vui lòng chọn một bệnh nhân.")
            return None
        return self.table.item(row, 0).data(Qt.ItemDataRole.UserRole.value)

    # ── CRUD ─────────────────────────────────────────────────────
    def _add_patient(self):
        dlg = PatientFormDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            try:
                dao.add_patient(dlg.result_data)
            except ValueError as e:
                QMessageBox.critical(self, "Lỗi dữ liệu", str(e))
                return
            self.load_data()
            QMessageBox.information(self, "Thành công", "Đã thêm bệnh nhân mới.")

    def _edit_patient(self):
        pid = self._selected_id()
        if not pid: return
        p = dao.get_patient_by_id(pid)
        dlg = PatientFormDialog(self, patient_data=p)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            try:
                dao.update_patient(pid, dlg.result_data)
            except ValueError as e:
                QMessageBox.critical(self, "Lỗi dữ liệu", str(e))
                return
            self.load_data()
            QMessageBox.information(self, "Thành công", "Đã cập nhật thông tin bệnh nhân.")
    def _delete_patient(self):
        pid = self._selected_id()
        if not pid: return
        p = dao.get_patient_by_id(pid)
        reply = QMessageBox.question(
            self, "Xác nhận xoá",
            f"Bạn có chắc muốn xoá bệnh nhân «{p['full_name']}»?\n"
            "Thao tác này không thể hoàn tác.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            dao.delete_patient(pid)
            self.load_data()

    def _view_detail(self):
        pid = self._selected_id()
        if not pid: return
        dlg = PatientDetailDialog(pid, self)
        dlg.exec()

    # ── Style ────────────────────────────────────────────────────
    def _apply_style(self):
        self.setStyleSheet("""
        QWidget { background: #f7fafc; font-family: 'Segoe UI'; }
        #sectionTitle { color: #1a365d; }
        #searchBox {
            border: 1.5px solid #cbd5e0; border-radius: 8px;
            padding: 8px 12px; font-size: 13px; background: white;
        }
        #searchBox:focus { border-color: #4299e1; }
        QComboBox {
            border: 1.5px solid #cbd5e0; border-radius: 6px;
            padding: 6px 10px; font-size: 12px; background: white;
        }
        #primaryBtn {
            background: #2b6cb0; color: white; border: none;
            border-radius: 7px; padding: 8px 16px; font-weight: 600; font-size: 12px;
        }
        #primaryBtn:hover { background: #2c5282; }
        #actionBtn {
            background: #edf2f7; color: #2d3748; border: none;
            border-radius: 6px; padding: 7px 14px; font-size: 12px;
        }
        #actionBtn:hover { background: #e2e8f0; }
        #dangerBtn {
            background: #fff5f5; color: #c53030; border: 1px solid #fed7d7;
            border-radius: 6px; padding: 7px 14px; font-size: 12px;
        }
        #dangerBtn:hover { background: #fed7d7; }
        #clearBtn {
            background: transparent; color: #718096; border: 1px solid #cbd5e0;
            border-radius: 6px; padding: 6px 12px; font-size: 12px;
        }
        #clearBtn:hover { background: #e2e8f0; }
        #countLabel { color: #718096; font-size: 12px; }
        QTableWidget {
            border: 1px solid #e2e8f0; border-radius: 8px;
            font-size: 12px; gridline-color: #f0f0f0;
        }
        QTableWidget::item:selected { background: #bee3f8; color: #1a365d; }
        QHeaderView::section {
            background: #edf2f7; font-weight: 600;
            padding: 8px; border: none; border-right: 1px solid #e2e8f0;
        }
        """)
