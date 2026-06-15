"""
Hospital Management System — Staff Management Tab
Quản lý nhân viên, bác sĩ, y tá, lễ tân
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView,
    QComboBox, QDialog, QFormLayout, QTextEdit, QMessageBox,
    QDateEdit, QDoubleSpinBox, QScrollArea, QFrame
)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QFont

import database.dao as dao
import core.auth as auth

POSITIONS = [
    "B\u00e1c si",             # doctor
    "Y t\u00e1 / \u0110i\u1ec1u d\u01b0\u1ee1ng",   # nurse  (matches seed)
    "L\u1ec5 t\u00e2n",            # receptionist
    "D\u01b0\u1ee3c si",           # pharmacist
    "K\u1ebf to\u00e1n",           # accountant (matches seed)
    "X\u00e9t nghi\u1ec7m vi\u00ean",  # lab_technician (matches seed)
    "Gi\u00e1m \u0111\u1ed1c",          # director (matches seed)
    "Qu\u1ea3n tr\u1ecb vi\u00ean",   # admin
    "Kh\u00e1c",               # other
]
GENDERS   = ["Nam", "Nữ", "Khác"]


# ═══════════════════════════════════════════════════════════
#  Staff Form Dialog
# ═══════════════════════════════════════════════════════════
class StaffFormDialog(QDialog):
    def __init__(self, parent=None, staff_data=None):
        super().__init__(parent)
        self.staff_data = staff_data
        self.is_edit = staff_data is not None
        self.departments = dao.get_departments()
        self.setWindowTitle("Sửa nhân viên" if self.is_edit else "Thêm nhân viên mới")
        self.setMinimumWidth(520)
        self.setModal(True)
        self._build_ui()
        if self.is_edit:
            self._fill_form()
        self._apply_style()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        title = QLabel("✏️ Sửa nhân viên" if self.is_edit else "➕ Thêm nhân viên mới")
        title.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        title.setObjectName("dlgTitle")
        layout.addWidget(title)

        scroll = QScrollArea(); scroll.setWidgetResizable(True); scroll.setFrameShape(QFrame.Shape.NoFrame)
        form_widget = QWidget()
        form = QFormLayout(form_widget)
        form.setSpacing(10)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        self.f_name     = QLineEdit(); self.f_name.setPlaceholderText("Họ và tên *")
        self.f_gender   = QComboBox(); self.f_gender.addItems(GENDERS)
        self.f_dob      = QDateEdit(); self.f_dob.setCalendarPopup(True)
        self.f_dob.setDisplayFormat("dd/MM/yyyy"); self.f_dob.setDate(QDate(1990, 1, 1))
        self.f_idcard   = QLineEdit(); self.f_idcard.setPlaceholderText("CMND/CCCD")
        self.f_phone    = QLineEdit(); self.f_phone.setPlaceholderText("Số điện thoại")
        self.f_email    = QLineEdit(); self.f_email.setPlaceholderText("Email")
        self.f_address  = QLineEdit(); self.f_address.setPlaceholderText("Địa chỉ")
        self.f_position = QComboBox(); self.f_position.addItems(POSITIONS)
        self.f_spec     = QLineEdit(); self.f_spec.setPlaceholderText("VD: Nội khoa, Tim mạch,...")
        self.f_dept     = QComboBox()
        self.f_dept.addItem("-- Chọn khoa --", None)
        for d in self.departments:
            self.f_dept.addItem(d["name"], d["id"])
        self.f_hire     = QDateEdit(); self.f_hire.setCalendarPopup(True)
        self.f_hire.setDisplayFormat("dd/MM/yyyy"); self.f_hire.setDate(QDate.currentDate())
        self.f_salary   = QDoubleSpinBox()
        self.f_salary.setRange(0, 100_000_000); self.f_salary.setSingleStep(500_000)
        self.f_salary.setSuffix(" VNĐ"); self.f_salary.setGroupSeparatorShown(True)
        self.f_bonus    = QDoubleSpinBox()
        self.f_bonus.setRange(0, 50_000_000); self.f_bonus.setSingleStep(100_000)
        self.f_bonus.setSuffix(" VNĐ"); self.f_bonus.setGroupSeparatorShown(True)
        self.f_schedule = QLineEdit()
        self.f_schedule.setPlaceholderText('VD: T2-T6: 07:30-16:30, T7: 07:30-11:30')
        self.f_notes    = QTextEdit(); self.f_notes.setMaximumHeight(60)

        form.addRow("Họ tên *:",      self.f_name)
        form.addRow("Giới tính:",     self.f_gender)
        form.addRow("Ngày sinh:",     self.f_dob)
        form.addRow("CMND/CCCD:",     self.f_idcard)
        form.addRow("Điện thoại:",    self.f_phone)
        form.addRow("Email:",         self.f_email)
        form.addRow("Địa chỉ:",       self.f_address)
        form.addRow("Vị trí *:",      self.f_position)
        form.addRow("Chuyên khoa:",   self.f_spec)
        form.addRow("Khoa/Phòng:",    self.f_dept)
        form.addRow("Ngày vào làm:", self.f_hire)
        form.addRow("Lương cơ bản:", self.f_salary)
        form.addRow("Thưởng:",        self.f_bonus)
        form.addRow("Lịch làm việc:", self.f_schedule)
        form.addRow("Ghi chú:",       self.f_notes)

        scroll.setWidget(form_widget)
        layout.addWidget(scroll)

        btn_row = QHBoxLayout(); btn_row.addStretch()
        self.cancel_btn = QPushButton("Huỷ"); self.cancel_btn.setObjectName("cancelBtn")
        self.save_btn   = QPushButton("Lưu"); self.save_btn.setObjectName("saveBtn")
        self.cancel_btn.clicked.connect(self.reject)
        self.save_btn.clicked.connect(self._save)
        btn_row.addWidget(self.cancel_btn); btn_row.addWidget(self.save_btn)
        layout.addLayout(btn_row)

    def _fill_form(self):
        s = self.staff_data
        self.f_name.setText(s["full_name"] or "")
        idx = self.f_gender.findText(s["gender"] or "Nam")
        if idx >= 0: self.f_gender.setCurrentIndex(idx)
        if s["birth_date"]:
            d = QDate.fromString(s["birth_date"], "yyyy-MM-dd")
            if d.isValid(): self.f_dob.setDate(d)
        self.f_idcard.setText(s["id_card"] or "")
        self.f_phone.setText(s["phone"] or "")
        self.f_email.setText(s["email"] or "")
        self.f_address.setText(s["address"] or "")
        # Safe position lookup: never silently default to index 0 on mismatch
        _pos_val = s["position"] or ""
        _pos_idx = self.f_position.findText(_pos_val)
        if _pos_idx >= 0:
            self.f_position.setCurrentIndex(_pos_idx)
        else:
            # Position from DB not in list: add it as a temporary entry so the
            # value is preserved on save instead of being overwritten with index-0.
            self.f_position.addItem(_pos_val)
            self.f_position.setCurrentIndex(self.f_position.count() - 1)
        self.f_spec.setText(s["specialization"] or "")
        if s["department_id"]:
            for i in range(self.f_dept.count()):
                if self.f_dept.itemData(i) == s["department_id"]:
                    self.f_dept.setCurrentIndex(i); break
        if s["hire_date"]:
            d = QDate.fromString(s["hire_date"], "yyyy-MM-dd")
            if d.isValid(): self.f_hire.setDate(d)
        self.f_salary.setValue(s["salary"] or 0)
        self.f_bonus.setValue(s["bonus"] or 0)
        self.f_schedule.setText(s["work_schedule"] or "")
        self.f_notes.setPlainText(s["notes"] or "")

    def _save(self):
        name = self.f_name.text().strip()
        if not name:
            QMessageBox.warning(self, "Thiếu thông tin", "Vui lòng nhập họ tên nhân viên.")
            return
        self.result_data = {
            "full_name":      name,
            "gender":         self.f_gender.currentText(),
            "birth_date":     self.f_dob.date().toString("yyyy-MM-dd"),
            "id_card":        self.f_idcard.text().strip(),
            "phone":          self.f_phone.text().strip(),
            "email":          self.f_email.text().strip(),
            "address":        self.f_address.text().strip(),
            "position":       self.f_position.currentText(),
            "specialization": self.f_spec.text().strip(),
            "department_id":  self.f_dept.currentData(),
            "hire_date":      self.f_hire.date().toString("yyyy-MM-dd"),
            "salary":         self.f_salary.value(),
            "bonus":          self.f_bonus.value(),
            "work_schedule":  self.f_schedule.text().strip(),
            "notes":          self.f_notes.toPlainText().strip(),
        }
        self.accept()

    def _apply_style(self):
        self.setStyleSheet("""
        QDialog { background: #f7fafc; }
        #dlgTitle { color: #2d3748; margin-bottom: 4px; }
        QLineEdit, QTextEdit, QComboBox, QDateEdit, QDoubleSpinBox {
            border: 1.5px solid #cbd5e0; border-radius: 6px;
            padding: 6px 8px; font-size: 12px; background: white;
        }
        QLabel { font-size: 12px; color: #4a5568; }
        #saveBtn {
            background: #276749; color: white; border: none;
            border-radius: 6px; padding: 8px 20px; font-weight: 600;
        }
        #saveBtn:hover { background: #22543d; }
        #cancelBtn {
            background: #e2e8f0; color: #4a5568; border: none;
            border-radius: 6px; padding: 8px 20px;
        }
        """)


# ═══════════════════════════════════════════════════════════
#  Main Staff Tab
# ═══════════════════════════════════════════════════════════
class StaffTab(QWidget):
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
        title = QLabel("👨‍⚕️ Quản lý nhân viên")
        title.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        title.setObjectName("sectionTitle")
        header_row.addWidget(title)
        header_row.addStretch()
        self.add_btn = QPushButton("➕ Thêm nhân viên")
        self.add_btn.setObjectName("primaryBtn")
        self.add_btn.clicked.connect(self._add_staff)
        header_row.addWidget(self.add_btn)
        layout.addLayout(header_row)

        # Filters
        filter_row = QHBoxLayout()
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("🔍  Tìm kiếm theo tên, mã, SĐT")
        self.search_box.setObjectName("searchBox")
        self.search_box.textChanged.connect(self.load_data)

        self.pos_cb = QComboBox()
        self.pos_cb.addItems(["Tất cả vị trí"] + POSITIONS)
        self.pos_cb.currentIndexChanged.connect(self.load_data)

        self.dept_cb = QComboBox()
        self.dept_cb.addItem("Tất cả khoa")
        for d in dao.get_departments():
            self.dept_cb.addItem(d["name"], d["id"])
        self.dept_cb.currentIndexChanged.connect(self.load_data)

        filter_row.addWidget(self.search_box, 3)
        filter_row.addWidget(self.pos_cb)
        filter_row.addWidget(self.dept_cb)
        layout.addLayout(filter_row)

        self.count_lbl = QLabel(); self.count_lbl.setObjectName("countLabel")
        layout.addWidget(self.count_lbl)

        # Table
        self.table = QTableWidget()
        cols = ["Mã NV", "Họ tên", "Vị trí", "Chuyên khoa", "Khoa/Phòng",
                "Điện thoại", "Lương", "Ngày vào làm"]
        self.table.setColumnCount(len(cols))
        self.table.setHorizontalHeaderLabels(cols)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        layout.addWidget(self.table)

        # Actions
        action_row = QHBoxLayout()
        self.edit_btn   = QPushButton("✏️ Sửa");   self.edit_btn.setObjectName("actionBtn")
        self.delete_btn = QPushButton("🗑️ Xoá");   self.delete_btn.setObjectName("dangerBtn")
        self.edit_btn.clicked.connect(self._edit_staff)
        self.delete_btn.clicked.connect(self._delete_staff)
        action_row.addWidget(self.edit_btn)
        action_row.addWidget(self.delete_btn)
        action_row.addStretch()
        layout.addLayout(action_row)

    def load_data(self):
        search   = self.search_box.text().strip()
        position = self.pos_cb.currentText()
        dept_id  = self.dept_cb.currentData()
        if position == "Tất cả vị trí": position = ""

        rows = dao.get_all_staff(search, position, dept_id)
        self.table.setRowCount(len(rows))
        for r, s in enumerate(rows):
            salary_str = f"{int(s['salary'] or 0):,} VNĐ"
            vals = [s["staff_code"], s["full_name"], s["position"] or "",
                    s["specialization"] or "", s["dept_name"] or "",
                    s["phone"] or "", salary_str, s["hire_date"] or ""]
            for c, v in enumerate(vals):
                item = QTableWidgetItem(v)
                item.setData(Qt.ItemDataRole.UserRole.value, s["id"])
                self.table.setItem(r, c, item)
        self.count_lbl.setText(f"Tổng: {len(rows)} nhân viên")

    def _selected_id(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.information(self, "Chưa chọn", "Vui lòng chọn một nhân viên.")
            return None
        return self.table.item(row, 0).data(Qt.ItemDataRole.UserRole.value)

    def _add_staff(self):
        dlg = StaffFormDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            dao.add_staff(dlg.result_data)
            self.load_data()
            QMessageBox.information(self, "Thành công", "Đã thêm nhân viên mới.")

    def _edit_staff(self):
        sid = self._selected_id()
        if not sid: return
        s = dao.get_staff_by_id(sid)
        dlg = StaffFormDialog(self, staff_data=s)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            dao.update_staff(sid, dlg.result_data)
            self.load_data()

    def _delete_staff(self):
        sid = self._selected_id()
        if not sid: return
        s = dao.get_staff_by_id(sid)
        reply = QMessageBox.question(
            self, "Xác nhận",
            f"Xoá nhân viên «{s['full_name']}»?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            dao.delete_staff(sid)
            self.load_data()

    def _apply_style(self):
        self.setStyleSheet("""
        QWidget { background: #f7fafc; font-family: 'Segoe UI'; }
        #sectionTitle { color: #1a365d; }
        #searchBox {
            border: 1.5px solid #cbd5e0; border-radius: 8px;
            padding: 8px 12px; font-size: 13px; background: white;
        }
        QComboBox {
            border: 1.5px solid #cbd5e0; border-radius: 6px;
            padding: 6px 10px; font-size: 12px; background: white;
        }
        #primaryBtn {
            background: #276749; color: white; border: none;
            border-radius: 7px; padding: 8px 16px; font-weight: 600;
        }
        #primaryBtn:hover { background: #22543d; }
        #actionBtn {
            background: #edf2f7; color: #2d3748; border: none;
            border-radius: 6px; padding: 7px 14px; font-size: 12px;
        }
        #actionBtn:hover { background: #e2e8f0; }
        #dangerBtn {
            background: #fff5f5; color: #c53030; border: 1px solid #fed7d7;
            border-radius: 6px; padding: 7px 14px; font-size: 12px;
        }
        #countLabel { color: #718096; font-size: 12px; }
        QTableWidget {
            border: 1px solid #e2e8f0; border-radius: 8px;
            font-size: 12px; gridline-color: #f0f0f0;
        }
        QHeaderView::section {
            background: #edf2f7; font-weight: 600;
            padding: 8px; border: none;
        }
        """)

