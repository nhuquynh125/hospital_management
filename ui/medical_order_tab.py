import json
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

STATUS_COLORS = {
    "Pending":   ("#fff3cd", "#856404"),
    "Done":      ("#d4edda", "#155724"),
    "Cancelled": ("#f8d7da", "#721c24"),
}

class MedicalOrderFormDialog(QDialog):
    def __init__(self, parent=None, order_data=None):
        super().__init__(parent)
        self.order_data = order_data
        self.is_edit = order_data is not None
        self.patients = dao.get_all_patients()
        self.doctors = dao.get_doctors()
        self.setWindowTitle("Sửa y lệnh" if self.is_edit else "Thêm y lệnh mới")
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

        title = QLabel("✏️ Sửa y lệnh" if self.is_edit else "➕ Thêm y lệnh mới")
        title.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        title.setObjectName("dlgTitle")
        layout.addWidget(title)

        form = QFormLayout()
        form.setSpacing(10)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        self.f_patient = QComboBox()
        self.f_patient.setEditable(True)
        self.f_patient.lineEdit().setPlaceholderText("Chọn hoặc tìm bệnh nhân...")
        for p in self.patients:
            self.f_patient.addItem(f"{p['patient_code']} — {p['full_name']}", p["id"])

        self.f_doctor = QComboBox()
        self.f_doctor.addItem("-- Chọn bác sĩ --", None)
        for d in self.doctors:
            spec = f" ({d['specialization']})" if d["specialization"] else ""
            self.f_doctor.addItem(f"{d['full_name']}{spec}", d["id"])

        self.f_type = QComboBox()
        self.f_type.addItems(["Tiêm thuốc", "Truyền dịch", "Lấy mẫu xét nghiệm", "Cho uống thuốc", "Khác"])

        self.f_desc = QTextEdit()
        self.f_desc.setMaximumHeight(80)
        self.f_desc.setPlaceholderText("Nội dung y lệnh (VD: Tiêm 1 ống kháng sinh...)")

        self.f_status = QComboBox()
        self.f_status.addItems(["Pending", "Done", "Cancelled"])

        form.addRow("Bệnh nhân *:", self.f_patient)
        form.addRow("Bác sĩ *:", self.f_doctor)
        form.addRow("Loại y lệnh:", self.f_type)
        form.addRow("Nội dung *:", self.f_desc)
        form.addRow("Trạng thái:", self.f_status)
        layout.addLayout(form)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        self.cancel_btn = QPushButton("Huỷ")
        self.cancel_btn.setObjectName("cancelBtn")
        self.save_btn = QPushButton("Lưu")
        self.save_btn.setObjectName("saveBtn")
        self.cancel_btn.clicked.connect(self.reject)
        self.save_btn.clicked.connect(self._save)
        btn_row.addWidget(self.cancel_btn)
        btn_row.addWidget(self.save_btn)
        layout.addLayout(btn_row)

    def _fill_form(self):
        o = self.order_data
        for i in range(self.f_patient.count()):
            if self.f_patient.itemData(i) == o["patient_id"]:
                self.f_patient.setCurrentIndex(i)
                break
        for i in range(self.f_doctor.count()):
            if self.f_doctor.itemData(i) == o["doctor_id"]:
                self.f_doctor.setCurrentIndex(i)
                break
        
        idx = self.f_type.findText(o["order_type"] or "")
        if idx >= 0:
            self.f_type.setCurrentIndex(idx)
        else:
            if o["order_type"]:
                self.f_type.addItem(o["order_type"])
                self.f_type.setCurrentIndex(self.f_type.count() - 1)
                
        self.f_desc.setPlainText(o["description"] or "")
        idx = self.f_status.findText(o["status"] or "Pending")
        if idx >= 0:
            self.f_status.setCurrentIndex(idx)

    def _save(self):
        patient_id = self.f_patient.currentData()
        if not patient_id:
            QMessageBox.warning(self, "Thiếu thông tin", "Vui lòng chọn bệnh nhân.")
            return
        desc = self.f_desc.toPlainText().strip()
        if not desc:
            QMessageBox.warning(self, "Thiếu thông tin", "Vui lòng nhập nội dung y lệnh.")
            return
            
        self.result_data = {
            "patient_id": patient_id,
            "doctor_id": self.f_doctor.currentData(),
            "order_type": self.f_type.currentText(),
            "description": desc,
            "status": self.f_status.currentText()
        }
        self.accept()

    def _apply_style(self):
        self.setStyleSheet("""
        QDialog { background: #f7fafc; }
        #dlgTitle { color: #2d3748; margin-bottom: 4px; }
        QLineEdit, QTextEdit, QComboBox {
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

class StatusDialog(QDialog):
    def __init__(self, parent=None, current_status="Pending"):
        super().__init__(parent)
        self.setWindowTitle("Cập nhật trạng thái")
        self.setMinimumWidth(300)
        self.setModal(True)
        
        layout = QVBoxLayout(self)
        form = QFormLayout()
        
        self.status_cb = QComboBox()
        self.status_cb.addItems(["Pending", "Done", "Cancelled"])
        idx = self.status_cb.findText(current_status)
        if idx >= 0:
            self.status_cb.setCurrentIndex(idx)
            
        form.addRow("Trạng thái mới:", self.status_cb)
        layout.addLayout(form)
        
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        self.cancel_btn = QPushButton("Huỷ")
        self.save_btn = QPushButton("Lưu")
        self.cancel_btn.clicked.connect(self.reject)
        self.save_btn.clicked.connect(self.accept)
        btn_row.addWidget(self.cancel_btn)
        btn_row.addWidget(self.save_btn)
        layout.addLayout(btn_row)
        self.setStyleSheet("""
            QDialog { background: white; }
            QComboBox { padding: 5px; border: 1px solid #ccc; border-radius: 4px; }
            QPushButton { padding: 6px 12px; border-radius: 4px; }
        """)
        
    def get_status(self):
        return self.status_cb.currentText()

class MedicalOrderTab(QWidget):
    def __init__(self):
        super().__init__()
        self._build_ui()
        self._apply_style()
        self.load_data()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        header_row = QHBoxLayout()
        title = QLabel("📋 Quản lý Y lệnh (To-do List)")
        title.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        title.setObjectName("sectionTitle")
        header_row.addWidget(title)
        header_row.addStretch()

        self.add_btn = QPushButton("➕ Thêm y lệnh")
        self.add_btn.setObjectName("primaryBtn")
        self.add_btn.clicked.connect(self._add_order)
        header_row.addWidget(self.add_btn)
        layout.addLayout(header_row)

        filter_row = QHBoxLayout()
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("🔍 Tìm theo tên bệnh nhân")
        self.search_box.setObjectName("searchBox")
        self.search_box.textChanged.connect(self.load_data)

        self.status_cb = QComboBox()
        self.status_cb.addItems(["Tất cả", "Pending", "Done", "Cancelled"])
        self.status_cb.currentIndexChanged.connect(self.load_data)

        filter_row.addWidget(self.search_box, 2)
        filter_row.addWidget(self.status_cb)
        layout.addLayout(filter_row)

        self.count_lbl = QLabel()
        self.count_lbl.setObjectName("countLabel")
        layout.addWidget(self.count_lbl)

        self.table = QTableWidget()
        cols = ["ID", "Thời gian", "Bệnh nhân", "Bác sĩ", "Loại y lệnh", "Nội dung", "Trạng thái", "Người thực hiện", "TG thực hiện"]
        self.table.setColumnCount(len(cols))
        self.table.setHorizontalHeaderLabels(cols)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        layout.addWidget(self.table)

        action_row = QHBoxLayout()
        btn_specs = [
            ("✏️ Sửa", "actionBtn", self._edit_order),
            ("🔄 Thay đổi trạng thái", "successBtn", self._change_status),
        ]
        for label, obj, handler in btn_specs:
            btn = QPushButton(label)
            btn.setObjectName(obj)
            btn.clicked.connect(handler)
            action_row.addWidget(btn)
        action_row.addStretch()
        layout.addLayout(action_row)

    def load_data(self):
        search = self.search_box.text().strip()
        status = self.status_cb.currentText()
        if status == "Tất cả": status = ""

        rows = dao.get_medical_orders(search, status)
        self.table.setRowCount(len(rows))
        for r, o in enumerate(rows):
            vals = [
                str(o["id"]), o["order_time"], f"{o['patient_code']} - {o['patient_name']}",
                o["doctor_name"] or "", o["order_type"], o["description"], o["status"],
                o["nurse_name"] or "", o["execution_time"] or ""
            ]
            for c, v in enumerate(vals):
                item = QTableWidgetItem(str(v))
                item.setData(Qt.ItemDataRole.UserRole.value, o["id"])
                if c == 6:  # status
                    bg, fg = STATUS_COLORS.get(v, ("#ffffff", "#000000"))
                    item.setBackground(QColor(bg))
                    item.setForeground(QColor(fg))
                self.table.setItem(r, c, item)
        self.count_lbl.setText(f"Tìm thấy {len(rows)} y lệnh")

    def _selected_id(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.information(self, "Chưa chọn", "Vui lòng chọn một y lệnh.")
            return None
        return self.table.item(row, 0).data(Qt.ItemDataRole.UserRole.value)

    def _add_order(self):
        dlg = MedicalOrderFormDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            dao.add_medical_order(dlg.result_data)
            self.load_data()

    def _edit_order(self):
        oid = self._selected_id()
        if not oid: return
        o = dao.get_medical_order_by_id(oid)
        dlg = MedicalOrderFormDialog(self, order_data=o)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            dao.update_medical_order(oid, dlg.result_data)
            self.load_data()

    def _change_status(self):
        oid = self._selected_id()
        if not oid: return
        o = dao.get_medical_order_by_id(oid)
        if o["status"] == "Done":
            QMessageBox.information(self, "Thông báo", "Y lệnh này đã hoàn thành (Done), không thể thay đổi trạng thái.")
            return
            
        dlg = StatusDialog(self, current_status=o["status"])
        if dlg.exec() == QDialog.DialogCode.Accepted:
            new_status = dlg.get_status()
            if new_status != o["status"]:
                user = auth.get_current_user()
                nurse_id = dao.get_staff_id_by_user_id(user["id"]) if user else None
                dao.update_medical_order_status(oid, new_status, nurse_id=nurse_id)
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
            padding: 6px 8px; font-size: 12px; background: white;
        }
        #primaryBtn {
            background: #2b6cb0; color: white; border: none;
            border-radius: 7px; padding: 8px 16px; font-weight: 600;
        }
        #primaryBtn:hover { background: #2c5282; }
        #actionBtn {
            background: #edf2f7; color: #2d3748; border: none;
            border-radius: 6px; padding: 7px 14px; font-size: 12px;
        }
        #successBtn {
            background: #f0fff4; color: #276749; border: 1px solid #9ae6b4;
            border-radius: 6px; padding: 7px 14px; font-size: 12px;
        }
        #countLabel { color: #718096; font-size: 12px; }
        QTableWidget {
            border: 1px solid #e2e8f0; border-radius: 8px;
            font-size: 12px; gridline-color: #f0f0f0;
        }
        QHeaderView::section {
            background: #edf2f7; font-weight: 600; padding: 8px; border: none;
        }
        """)
