"""
Hospital Management System — Billing Tab
Kế toán: quản lý viện phí, thanh toán
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,
    QComboBox, QDialog, QFormLayout, QTextEdit, QMessageBox,
    QDoubleSpinBox, QFrame, QScrollArea, QAbstractItemView
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QColor

import database.dao as dao
import core.auth as auth

PAYMENT_METHODS = ["Tiền mặt","Chuyển khoản","BHYT","Thẻ"]
BILL_STATUSES   = ["Chưa thanh toán","Đã thanh toán","Một phần","Huỷ"]
ITEM_TYPES      = ["Khám","Thuốc","Xét nghiệm","Phòng","Dịch vụ"]

STATUS_COLORS = {
    "Chưa thanh toán": ("#fff3cd","#856404"),
    "Đã thanh toán":   ("#d4edda","#155724"),
    "Một phần":        ("#cce5ff","#004085"),
    "Huỷ":             ("#f8d7da","#721c24"),
}


class BillFormDialog(QDialog):
    def __init__(self, parent=None, bill_data=None):
        super().__init__(parent)
        self.bill_data = bill_data
        self.is_edit   = bill_data is not None
        self.patients  = dao.get_all_patients()
        self.items     = []
        self.setWindowTitle("Sửa hoá đơn" if self.is_edit else "Tạo hoá đơn viện phí")
        self.setMinimumSize(640, 520)
        self.setModal(True)
        self._build_ui()
        if self.is_edit:
            self._fill_form()
        self._apply_style()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20,20,20,20); layout.setSpacing(12)

        title = QLabel("💰 " + ("Sửa hoá đơn" if self.is_edit else "Tạo hoá đơn viện phí"))
        title.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        title.setObjectName("dlgTitle"); layout.addWidget(title)

        top = QHBoxLayout(); top.setSpacing(16)

        # LEFT: bill info
        left = QFrame(); left.setObjectName("panel")
        ll = QFormLayout(left); ll.setSpacing(8)
        ll.setLabelAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        self.f_patient = QComboBox(); self.f_patient.setEditable(True)
        self.f_patient.lineEdit().setPlaceholderText("Chọn bệnh nhân...")
        for p in self.patients:
            self.f_patient.addItem(f"{p['patient_code']} — {p['full_name']}", p["id"])

        self.f_payment = QComboBox(); self.f_payment.addItems(PAYMENT_METHODS)
        self.f_status  = QComboBox(); self.f_status.addItems(BILL_STATUSES)
        self.f_discount= QDoubleSpinBox(); self.f_discount.setRange(0,100)
        self.f_discount.setSuffix(" %"); self.f_discount.setSingleStep(5)
        self.f_ins_cover = QDoubleSpinBox(); self.f_ins_cover.setRange(0,100_000_000)
        self.f_ins_cover.setSuffix(" VNĐ"); self.f_ins_cover.setGroupSeparatorShown(True)
        self.f_paid    = QDoubleSpinBox(); self.f_paid.setRange(0,100_000_000)
        self.f_paid.setSuffix(" VNĐ"); self.f_paid.setGroupSeparatorShown(True)
        self.f_notes   = QTextEdit(); self.f_notes.setMaximumHeight(55)

        ll.addRow("Bệnh nhân *:",   self.f_patient)
        ll.addRow("Hình thức TT:",  self.f_payment)
        ll.addRow("Trạng thái:",    self.f_status)
        ll.addRow("Giảm giá:",      self.f_discount)
        ll.addRow("BHYT chi trả:",  self.f_ins_cover)
        ll.addRow("Đã thanh toán:", self.f_paid)
        ll.addRow("Ghi chú:",       self.f_notes)
        top.addWidget(left, 1)

        # RIGHT: bill items
        right = QFrame(); right.setObjectName("panel")
        rl = QVBoxLayout(right); rl.setContentsMargins(10,10,10,10); rl.setSpacing(6)
        rl.addWidget(QLabel("📋 Chi tiết dịch vụ:"))

        self.items_table = QTableWidget()
        self.items_table.setColumnCount(5)
        self.items_table.setHorizontalHeaderLabels(["Loại","Mô tả","SL","Đơn giá","Thành tiền"])
        self.items_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.items_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.items_table.setMaximumHeight(160)
        rl.addWidget(self.items_table)

        # Add item row
        add_row = QHBoxLayout(); add_row.setSpacing(6)
        self.f_item_type = QComboBox(); self.f_item_type.addItems(ITEM_TYPES)
        self.f_item_desc = QLineEdit(); self.f_item_desc.setPlaceholderText("Mô tả dịch vụ")
        self.f_item_qty  = QDoubleSpinBox(); self.f_item_qty.setRange(1,999); self.f_item_qty.setValue(1)
        self.f_item_price= QDoubleSpinBox(); self.f_item_price.setRange(0,100_000_000)
        self.f_item_price.setSuffix(" VNĐ"); self.f_item_price.setGroupSeparatorShown(True)
        self.f_item_price.setSingleStep(10000)
        add_item_btn = QPushButton("➕"); add_item_btn.setObjectName("addItemBtn")
        add_item_btn.setFixedWidth(36)
        add_item_btn.clicked.connect(self._add_item)
        add_row.addWidget(self.f_item_type)
        add_row.addWidget(self.f_item_desc, 2)
        add_row.addWidget(self.f_item_qty)
        add_row.addWidget(self.f_item_price, 2)
        add_row.addWidget(add_item_btn)
        rl.addLayout(add_row)

        # Totals
        self.total_lbl = QLabel("Tổng tiền: 0 VNĐ")
        self.total_lbl.setObjectName("totalLbl")
        rl.addWidget(self.total_lbl)
        top.addWidget(right, 2)
        layout.addLayout(top)

        btn_row = QHBoxLayout(); btn_row.addStretch()
        cancel_btn = QPushButton("Huỷ"); cancel_btn.setObjectName("cancelBtn")
        save_btn   = QPushButton("💾 Lưu hoá đơn"); save_btn.setObjectName("saveBtn")
        cancel_btn.clicked.connect(self.reject)
        save_btn.clicked.connect(self._save)
        btn_row.addWidget(cancel_btn); btn_row.addWidget(save_btn)
        layout.addLayout(btn_row)

    def _add_item(self):
        desc = self.f_item_desc.text().strip()
        if not desc:
            QMessageBox.warning(self, "Thiếu thông tin", "Vui lòng nhập mô tả dịch vụ.")
            return
        qty   = self.f_item_qty.value()
        price = self.f_item_price.value()
        total = qty * price
        item = {
            "item_type":   self.f_item_type.currentText(),
            "description": desc,
            "quantity":    int(qty),
            "unit_price":  price,
            "total":       total,
        }
        self.items.append(item)
        self.f_item_desc.clear()
        self._refresh_items()

    def _refresh_items(self):
        self.items_table.setRowCount(len(self.items))
        grand_total = 0
        for r, it in enumerate(self.items):
            vals = [it["item_type"], it["description"], str(it["quantity"]),
                    f"{int(it['unit_price']):,}", f"{int(it['total']):,}"]
            for c, v in enumerate(vals):
                self.items_table.setItem(r, c, QTableWidgetItem(v))
            grand_total += it["total"]
        self.total_lbl.setText(f"Tổng tiền: {int(grand_total):,} VNĐ")

    def _fill_form(self):
        b = self.bill_data
        for i in range(self.f_patient.count()):
            if self.f_patient.itemData(i) == b["patient_id"]:
                self.f_patient.setCurrentIndex(i); break
        idx = self.f_payment.findText(b["payment_method"] or "")
        if idx >= 0: self.f_payment.setCurrentIndex(idx)
        idx = self.f_status.findText(b["status"] or "")
        if idx >= 0: self.f_status.setCurrentIndex(idx)
        self.f_discount.setValue(b["discount"] or 0)
        self.f_ins_cover.setValue(b["insurance_cover"] or 0)
        self.f_paid.setValue(b["paid_amount"] or 0)
        self.f_notes.setPlainText(b["notes"] or "")
        self.items = dao.get_bill_items(b["id"])
        self.items = [dict(i) for i in self.items]
        self._refresh_items()

    def _save(self):
        patient_id = self.f_patient.currentData()
        if not patient_id:
            QMessageBox.warning(self, "Thiếu thông tin", "Vui lòng chọn bệnh nhân.")
            return
        user = auth.get_current_user()
        grand_total = sum(i["total"] for i in self.items)
        self.result_data = {
            "patient_id":     patient_id,
            "accountant_id":  user["id"] if user else None,
            "total_amount":   grand_total,
            "paid_amount":    self.f_paid.value(),
            "discount":       self.f_discount.value(),
            "insurance_cover":self.f_ins_cover.value(),
            "payment_method": self.f_payment.currentText(),
            "status":         self.f_status.currentText(),
            "notes":          self.f_notes.toPlainText().strip(),
            "items":          self.items,
        }
        self.accept()

    def _apply_style(self):
        self.setStyleSheet("""
        QDialog { background:#f7fafc; }
        #dlgTitle { color:#2d3748; }
        QLineEdit, QTextEdit, QComboBox, QDoubleSpinBox {
            border:1.5px solid #cbd5e0; border-radius:6px; padding:6px 8px; font-size:12px; background:white;
        }
        QLabel { font-size:12px; color:#4a5568; }
        #panel { background:white; border-radius:8px; border:1px solid #e2e8f0; padding:4px; }
        #totalLbl { font-size:13px; font-weight:700; color:#276749; padding:4px 0; }
        #addItemBtn { background:#276749; color:white; border:none; border-radius:6px; font-size:16px; }
        #saveBtn { background:#276749; color:white; border:none; border-radius:6px; padding:8px 20px; font-weight:600; }
        #saveBtn:hover { background:#22543d; }
        #cancelBtn { background:#e2e8f0; color:#4a5568; border:none; border-radius:6px; padding:8px 20px; }
        QTableWidget { border:1px solid #e2e8f0; font-size:12px; }
        QHeaderView::section { background:#edf2f7; font-weight:600; padding:5px; border:none; }
        """)


class BillingTab(QWidget):
    def __init__(self):
        super().__init__()
        self._build_ui(); self._apply_style(); self.load_data()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16,16,16,16); layout.setSpacing(10)

        header_row = QHBoxLayout()
        title = QLabel("💰 Quản lý viện phí")
        title.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        title.setObjectName("sectionTitle")
        header_row.addWidget(title); header_row.addStretch()
        self.add_btn = QPushButton("➕ Tạo hoá đơn")
        self.add_btn.setObjectName("primaryBtn")
        self.add_btn.clicked.connect(self._add_bill)
        header_row.addWidget(self.add_btn)
        layout.addLayout(header_row)

        f_row = QHBoxLayout()
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("🔍  Tìm theo tên bệnh nhân")
        self.search_box.setObjectName("searchBox"); self.search_box.textChanged.connect(self.load_data)
        self.status_cb = QComboBox()
        self.status_cb.addItems(["Tất cả trạng thái"] + BILL_STATUSES)
        self.status_cb.currentIndexChanged.connect(self.load_data)
        f_row.addWidget(self.search_box, 2); f_row.addWidget(self.status_cb)
        layout.addLayout(f_row)

        self.count_lbl = QLabel(); self.count_lbl.setObjectName("countLabel")
        layout.addWidget(self.count_lbl)

        self.table = QTableWidget()
        cols = ["Mã HĐ","Bệnh nhân","Ngày","Tổng tiền","Đã TT","Giảm giá","BHYT","Hình thức","Trạng thái"]
        self.table.setColumnCount(len(cols))
        self.table.setHorizontalHeaderLabels(cols)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        layout.addWidget(self.table)

        a_row = QHBoxLayout()
        self.edit_btn    = QPushButton("✏️ Sửa");       self.edit_btn.setObjectName("actionBtn")
        self.paid_btn    = QPushButton("✅ Đánh dấu đã TT"); self.paid_btn.setObjectName("successBtn")
        self.edit_btn.clicked.connect(self._edit_bill)
        self.paid_btn.clicked.connect(self._mark_paid)
        a_row.addWidget(self.edit_btn); a_row.addWidget(self.paid_btn); a_row.addStretch()
        layout.addLayout(a_row)

    def load_data(self):
        search = self.search_box.text().strip()
        status = self.status_cb.currentText()
        if status == "Tất cả trạng thái": status = ""
        rows = dao.get_all_bills(search, status)
        self.table.setRowCount(len(rows))
        for r, b in enumerate(rows):
            st = b["status"] or ""
            vals = [
                str(b["id"]), b["patient_name"] or "",
                (b["bill_date"] or "")[:10],
                f"{int(b['total_amount'] or 0):,} VNĐ",
                f"{int(b['paid_amount'] or 0):,} VNĐ",
                f"{int(b['discount'] or 0)} %",
                f"{int(b['insurance_cover'] or 0):,} VNĐ",
                b["payment_method"] or "", st
            ]
            for c, v in enumerate(vals):
                item = QTableWidgetItem(v)
                item.setData(Qt.ItemDataRole.UserRole.value, b["id"])
                if c == 8 and st in STATUS_COLORS:
                    bg, fg = STATUS_COLORS[st]
                    item.setBackground(QColor(bg)); item.setForeground(QColor(fg))
                self.table.setItem(r, c, item)
        self.count_lbl.setText(f"Tổng: {len(rows)} hoá đơn")

    def _selected_id(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.information(self, "Chưa chọn", "Vui lòng chọn một hoá đơn.")
            return None
        return self.table.item(row, 0).data(Qt.ItemDataRole.UserRole.value)

    def _add_bill(self):
        dlg = BillFormDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            dao.add_bill(dlg.result_data); self.load_data()

    def _edit_bill(self):
        bid = self._selected_id()
        if not bid: return
        b = dao.get_bill_by_id(bid)
        dlg = BillFormDialog(self, bill_data=b)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            dao.update_bill(bid, dlg.result_data); self.load_data()

    def _mark_paid(self):
        bid = self._selected_id()
        if not bid: return
        dao.update_bill_status(bid, "Đã thanh toán"); self.load_data()

    def _apply_style(self):
        self.setStyleSheet("""
        QWidget { background:#f7fafc; font-family:'Segoe UI'; }
        #sectionTitle { color:#1a365d; }
        #searchBox { border:1.5px solid #cbd5e0; border-radius:8px; padding:8px 12px; font-size:13px; background:white; }
        QComboBox { border:1.5px solid #cbd5e0; border-radius:6px; padding:6px 8px; font-size:12px; background:white; }
        #primaryBtn { background:#276749; color:white; border:none; border-radius:7px; padding:8px 16px; font-weight:600; }
        #primaryBtn:hover { background:#22543d; }
        #actionBtn { background:#edf2f7; color:#2d3748; border:none; border-radius:6px; padding:7px 14px; font-size:12px; }
        #successBtn { background:#f0fff4; color:#276749; border:1px solid #9ae6b4; border-radius:6px; padding:7px 14px; font-size:12px; }
        #countLabel { color:#718096; font-size:12px; }
        QTableWidget { border:1px solid #e2e8f0; border-radius:8px; font-size:12px; }
        QHeaderView::section { background:#edf2f7; font-weight:600; padding:8px; border:none; }
        """)
