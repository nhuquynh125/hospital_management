"""
Hospital Management System — Medicine & Prescription Tab
Kho thuốc, kê đơn, cảnh báo tương tác thuốc
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView,
    QComboBox, QDialog, QFormLayout, QTextEdit, QMessageBox,
    QDateEdit, QSpinBox, QDoubleSpinBox, QFrame, QTabWidget,
    QScrollArea, QGridLayout, QListWidget, QListWidgetItem,
    QSplitter
)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QFont, QColor

import database.dao as dao

MEDICINE_CATEGORIES = [
    "Kháng sinh", "Giảm đau / Hạ sốt", "Tim mạch", "Tiêu hóa",
    "Hô hấp", "Thần kinh", "Nội tiết", "Vitamin & Khoáng chất",
    "Ngoài da", "Mắt / Tai / Mũi", "Khác"
]
SEVERITY_COLORS = {
    "Nguy hiểm": ("#fff5f5", "#c53030"),
    "Thận trọng": ("#fffbeb", "#744210"),
    "Theo dõi":   ("#ebf8ff", "#2b6cb0"),
}


# ═══════════════════════════════════════════════════════════
#  Medicine Form Dialog
# ═══════════════════════════════════════════════════════════
class MedicineFormDialog(QDialog):
    def __init__(self, parent=None, med_data=None):
        super().__init__(parent)
        self.med_data = med_data
        self.is_edit = med_data is not None
        self.setWindowTitle("Sửa thuốc" if self.is_edit else "Thêm thuốc mới")
        self.setMinimumWidth(460)
        self.setModal(True)
        self._build_ui()
        if self.is_edit:
            self._fill_form()
        self._apply_style()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        title = QLabel("✏️ Sửa thuốc" if self.is_edit else "➕ Thêm thuốc mới")
        title.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        title.setObjectName("dlgTitle")
        layout.addWidget(title)

        scroll = QScrollArea(); scroll.setWidgetResizable(True); scroll.setFrameShape(QFrame.Shape.NoFrame)
        fw = QWidget(); form = QFormLayout(fw)
        form.setSpacing(10); form.setLabelAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        self.f_name     = QLineEdit(); self.f_name.setPlaceholderText("Tên thuốc *")
        self.f_generic  = QLineEdit(); self.f_generic.setPlaceholderText("Tên hoạt chất")
        self.f_category = QComboBox(); self.f_category.addItems(MEDICINE_CATEGORIES)
        self.f_unit     = QLineEdit(); self.f_unit.setPlaceholderText("VD: viên, ml, ống, gói")
        self.f_stock    = QSpinBox(); self.f_stock.setRange(0, 999999); self.f_stock.setSuffix(" đơn vị")
        self.f_min_stock= QSpinBox(); self.f_min_stock.setRange(0, 9999); self.f_min_stock.setValue(10)
        self.f_min_stock.setSuffix(" (cảnh báo)")
        self.f_price    = QDoubleSpinBox(); self.f_price.setRange(0, 10_000_000)
        self.f_price.setSuffix(" VNĐ"); self.f_price.setGroupSeparatorShown(True)
        self.f_expiry   = QDateEdit(); self.f_expiry.setCalendarPopup(True)
        self.f_expiry.setDisplayFormat("dd/MM/yyyy"); self.f_expiry.setDate(QDate.currentDate().addYears(2))
        self.f_supplier = QLineEdit(); self.f_supplier.setPlaceholderText("Nhà cung cấp / NSX")
        self.f_desc     = QTextEdit(); self.f_desc.setMaximumHeight(60)
        self.f_desc.setPlaceholderText("Mô tả, chỉ định, chống chỉ định...")

        form.addRow("Tên thuốc *:",   self.f_name)
        form.addRow("Hoạt chất:",     self.f_generic)
        form.addRow("Nhóm thuốc:",    self.f_category)
        form.addRow("Đơn vị:",        self.f_unit)
        form.addRow("Tồn kho:",       self.f_stock)
        form.addRow("Cảnh báo tối thiểu:", self.f_min_stock)
        form.addRow("Đơn giá:",       self.f_price)
        form.addRow("Hạn sử dụng:",   self.f_expiry)
        form.addRow("Nhà cung cấp:",  self.f_supplier)
        form.addRow("Mô tả:",         self.f_desc)

        scroll.setWidget(fw); layout.addWidget(scroll)

        btn_row = QHBoxLayout(); btn_row.addStretch()
        self.cancel_btn = QPushButton("Huỷ"); self.cancel_btn.setObjectName("cancelBtn")
        self.save_btn   = QPushButton("Lưu"); self.save_btn.setObjectName("saveBtn")
        self.cancel_btn.clicked.connect(self.reject)
        self.save_btn.clicked.connect(self._save)
        btn_row.addWidget(self.cancel_btn); btn_row.addWidget(self.save_btn)
        layout.addLayout(btn_row)

    def _fill_form(self):
        m = self.med_data
        self.f_name.setText(m["name"] or "")
        self.f_generic.setText(m["generic_name"] or "")
        idx = self.f_category.findText(m["category"] or "")
        if idx >= 0: self.f_category.setCurrentIndex(idx)
        self.f_unit.setText(m["unit"] or "")
        self.f_stock.setValue(m["stock_qty"] or 0)
        self.f_min_stock.setValue(m["min_stock"] or 10)
        self.f_price.setValue(m["price"] or 0)
        if m["expiry_date"]:
            d = QDate.fromString(m["expiry_date"], "yyyy-MM-dd")
            if d.isValid(): self.f_expiry.setDate(d)
        self.f_supplier.setText(m["supplier"] or "")
        self.f_desc.setPlainText(m["description"] or "")

    def _save(self):
        name = self.f_name.text().strip()
        if not name:
            QMessageBox.warning(self, "Thiếu thông tin", "Vui lòng nhập tên thuốc.")
            return
        self.result_data = {
            "name":         name,
            "generic_name": self.f_generic.text().strip(),
            "category":     self.f_category.currentText(),
            "unit":         self.f_unit.text().strip(),
            "stock_qty":    self.f_stock.value(),
            "min_stock":    self.f_min_stock.value(),
            "price":        self.f_price.value(),
            "expiry_date":  self.f_expiry.date().toString("yyyy-MM-dd"),
            "supplier":     self.f_supplier.text().strip(),
            "description":  self.f_desc.toPlainText().strip(),
        }
        self.accept()

    def _apply_style(self):
        self.setStyleSheet("""
        QDialog { background: #f7fafc; }
        #dlgTitle { color: #2d3748; }
        QLineEdit, QTextEdit, QComboBox, QDateEdit, QSpinBox, QDoubleSpinBox {
            border: 1.5px solid #cbd5e0; border-radius: 6px;
            padding: 6px 8px; font-size: 12px; background: white;
        }
        QLabel { font-size: 12px; color: #4a5568; }
        #saveBtn { background: #553c9a; color: white; border: none; border-radius: 6px; padding: 8px 20px; font-weight: 600; }
        #saveBtn:hover { background: #44337a; }
        #cancelBtn { background: #e2e8f0; color: #4a5568; border: none; border-radius: 6px; padding: 8px 20px; }
        """)


# ═══════════════════════════════════════════════════════════
#  Prescription Dialog (with drug interaction check)
# ═══════════════════════════════════════════════════════════
class PrescriptionDialog(QDialog):
    def __init__(self, parent=None, medical_record_id=None, doctor_id=None):
        super().__init__(parent)
        self.medical_record_id = medical_record_id
        self.doctor_id = doctor_id
        self.medicines = dao.get_all_medicines()
        self.items = []   # list of {medicine_id, name, qty, dosage, duration, notes}
        self.setWindowTitle("Tạo đơn thuốc")
        self.setMinimumSize(700, 500)
        self.setModal(True)
        self._build_ui()
        self._apply_style()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        title = QLabel("📝 Tạo đơn thuốc")
        title.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        title.setObjectName("dlgTitle")
        layout.addWidget(title)

        splitter = QSplitter(Qt.Orientation.Horizontal)

        # LEFT: add medicine to prescription
        left = QFrame()
        left.setObjectName("leftPanel")
        ll = QVBoxLayout(left)
        ll.setContentsMargins(12, 12, 12, 12)
        ll.setSpacing(8)

        ll.addWidget(QLabel("🔍 Chọn thuốc:"))
        self.med_search = QLineEdit()
        self.med_search.setPlaceholderText("Tìm theo tên thuốc...")
        self.med_search.textChanged.connect(self._filter_medicines)
        ll.addWidget(self.med_search)

        self.med_list = QListWidget()
        self.med_list.setAlternatingRowColors(True)
        for m in self.medicines:
            stock_warn = " ⚠️" if m["stock_qty"] <= m["min_stock"] else ""
            item = QListWidgetItem(f"{m['name']} ({m['unit'] or ''}) | Tồn: {m['stock_qty']}{stock_warn}")
            item.setData(Qt.ItemDataRole.UserRole.value, m["id"])
            item.setData(Qt.ItemDataRole.UserRole.value + 1, m["name"])
            self.med_list.addItem(item)
        ll.addWidget(self.med_list)

        # Dosage form
        dose_form = QFormLayout(); dose_form.setSpacing(6)
        self.f_qty      = QSpinBox(); self.f_qty.setRange(1, 9999)
        self.f_dosage   = QLineEdit(); self.f_dosage.setPlaceholderText("VD: 1 viên x 3 lần/ngày")
        self.f_duration = QSpinBox(); self.f_duration.setRange(1, 365); self.f_duration.setSuffix(" ngày")
        self.f_item_notes = QLineEdit(); self.f_item_notes.setPlaceholderText("Ghi chú (tuỳ chọn)")
        dose_form.addRow("Số lượng:", self.f_qty)
        dose_form.addRow("Liều dùng:", self.f_dosage)
        dose_form.addRow("Số ngày:", self.f_duration)
        dose_form.addRow("Ghi chú:", self.f_item_notes)
        ll.addLayout(dose_form)

        add_item_btn = QPushButton("➕ Thêm vào đơn")
        add_item_btn.setObjectName("addItemBtn")
        add_item_btn.clicked.connect(self._add_to_prescription)
        ll.addWidget(add_item_btn)

        splitter.addWidget(left)

        # RIGHT: prescription items + interaction warnings
        right = QFrame()
        right.setObjectName("rightPanel")
        rl = QVBoxLayout(right)
        rl.setContentsMargins(12, 12, 12, 12)
        rl.setSpacing(8)

        rl.addWidget(QLabel("📋 Đơn thuốc:"))
        self.prescription_table = QTableWidget()
        self.prescription_table.setColumnCount(5)
        self.prescription_table.setHorizontalHeaderLabels(["Tên thuốc", "SL", "Liều dùng", "Số ngày", "Xoá"])
        self.prescription_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.prescription_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        rl.addWidget(self.prescription_table)

        # Drug interaction warnings panel
        self.warning_frame = QFrame()
        self.warning_frame.setObjectName("warningFrame")
        self.warning_frame.hide()
        wl = QVBoxLayout(self.warning_frame)
        wl.setContentsMargins(10, 8, 10, 8)
        self.warning_lbl = QLabel()
        self.warning_lbl.setWordWrap(True)
        self.warning_lbl.setObjectName("warningLbl")
        wl.addWidget(self.warning_lbl)
        rl.addWidget(self.warning_frame)

        # Prescription notes
        self.f_presc_notes = QTextEdit()
        self.f_presc_notes.setMaximumHeight(50)
        self.f_presc_notes.setPlaceholderText("Lưu ý chung cho đơn thuốc...")
        rl.addWidget(self.f_presc_notes)

        splitter.addWidget(right)
        splitter.setSizes([300, 400])
        layout.addWidget(splitter)

        # Buttons
        btn_row = QHBoxLayout(); btn_row.addStretch()
        cancel_btn = QPushButton("Huỷ"); cancel_btn.setObjectName("cancelBtn")
        save_btn   = QPushButton("💾 Lưu đơn thuốc"); save_btn.setObjectName("saveBtn")
        cancel_btn.clicked.connect(self.reject)
        save_btn.clicked.connect(self._save)
        btn_row.addWidget(cancel_btn); btn_row.addWidget(save_btn)
        layout.addLayout(btn_row)

    def _filter_medicines(self):
        query = self.med_search.text().lower()
        for i in range(self.med_list.count()):
            item = self.med_list.item(i)
            item.setHidden(query not in item.text().lower())

    def _add_to_prescription(self):
        sel = self.med_list.currentItem()
        if not sel:
            QMessageBox.warning(self, "Chưa chọn", "Vui lòng chọn thuốc từ danh sách.")
            return
        med_id   = sel.data(Qt.ItemDataRole.UserRole.value)
        med_name = sel.data(Qt.ItemDataRole.UserRole.value + 1)
        entry = {
            "medicine_id": med_id,
            "name":        med_name,
            "quantity":    self.f_qty.value(),
            "dosage":      self.f_dosage.text().strip(),
            "duration_days": self.f_duration.value(),
            "notes":       self.f_item_notes.text().strip(),
        }
        self.items.append(entry)
        self._refresh_table()
        self._check_interactions()

    def _refresh_table(self):
        self.prescription_table.setRowCount(len(self.items))
        for r, item in enumerate(self.items):
            self.prescription_table.setItem(r, 0, QTableWidgetItem(item["name"]))
            self.prescription_table.setItem(r, 1, QTableWidgetItem(str(item["quantity"])))
            self.prescription_table.setItem(r, 2, QTableWidgetItem(item["dosage"]))
            self.prescription_table.setItem(r, 3, QTableWidgetItem(f"{item['duration_days']} ngày"))
            del_btn = QPushButton("🗑️")
            del_btn.setFixedWidth(36)
            del_btn.clicked.connect(lambda _, idx=r: self._remove_item(idx))
            self.prescription_table.setCellWidget(r, 4, del_btn)

    def _remove_item(self, idx):
        self.items.pop(idx)
        self._refresh_table()
        self._check_interactions()

    def _check_interactions(self):
        """Check drug interactions between all medicine pairs in the prescription."""
        if len(self.items) < 2:
            self.warning_frame.hide()
            return

        med_ids = [i["medicine_id"] for i in self.items]
        warnings = dao.check_drug_interactions(med_ids)

        if not warnings:
            self.warning_frame.hide()
            return

        msgs = []
        for w in warnings:
            sev = w["severity"]
            icon = "🔴" if sev == "Nguy hiểm" else "🟡" if sev == "Thận trọng" else "🔵"
            msgs.append(f"{icon} <b>{w['med1']} + {w['med2']}</b> — {sev}: {w['description'] or ''}")

        self.warning_lbl.setText("<br>".join(msgs))
        self.warning_frame.show()

        # Show red border for dangerous interactions
        has_danger = any(w["severity"] == "Nguy hiểm" for w in warnings)
        color = "#c53030" if has_danger else "#856404"
        bg    = "#fff5f5" if has_danger else "#fffbeb"
        self.warning_frame.setStyleSheet(
            f"#warningFrame {{ background:{bg}; border:2px solid {color}; border-radius:8px; }}"
        )

    def _save(self):
        if not self.items:
            QMessageBox.warning(self, "Đơn thuốc trống", "Vui lòng thêm ít nhất một loại thuốc.")
            return
        # Check dangerous interactions — warn but allow override
        med_ids  = [i["medicine_id"] for i in self.items]
        warnings = dao.check_drug_interactions(med_ids)
        danger   = [w for w in warnings if w["severity"] == "Nguy hiểm"]
        if danger:
            reply = QMessageBox.warning(
                self, "⚠️ Cảnh báo tương tác nguy hiểm",
                f"Phát hiện {len(danger)} tương tác NGUY HIỂM trong đơn thuốc!\n"
                "Bạn có chắc muốn tiếp tục lưu đơn này không?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply != QMessageBox.StandardButton.Yes:
                return

        self.result_data = {
            "medical_record_id": self.medical_record_id,
            "doctor_id":         self.doctor_id,
            "notes":             self.f_presc_notes.toPlainText().strip(),
            "items":             self.items,
        }
        self.accept()

    def _apply_style(self):
        self.setStyleSheet("""
        QDialog { background: #f7fafc; }
        #dlgTitle { color: #2d3748; }
        QLineEdit, QTextEdit, QComboBox, QSpinBox {
            border: 1.5px solid #cbd5e0; border-radius: 6px;
            padding: 6px 8px; font-size: 12px; background: white;
        }
        QLabel { font-size: 12px; color: #4a5568; }
        #leftPanel, #rightPanel { background: white; border-radius: 8px; border: 1px solid #e2e8f0; }
        #addItemBtn { background: #553c9a; color: white; border: none; border-radius: 6px; padding: 8px; font-weight: 600; }
        #addItemBtn:hover { background: #44337a; }
        #saveBtn { background: #276749; color: white; border: none; border-radius: 6px; padding: 8px 20px; font-weight: 600; }
        #saveBtn:hover { background: #22543d; }
        #cancelBtn { background: #e2e8f0; color: #4a5568; border: none; border-radius: 6px; padding: 8px 20px; }
        #warningLbl { font-size: 12px; color: #2d3748; }
        QTableWidget { border: 1px solid #e2e8f0; font-size: 12px; }
        QHeaderView::section { background: #edf2f7; font-weight: 600; padding: 6px; border: none; }
        QListWidget { border: 1px solid #e2e8f0; font-size: 12px; }
        QListWidget::item:selected { background: #bee3f8; color: #1a365d; }
        """)


# ═══════════════════════════════════════════════════════════
#  Main Medicine Tab
# ═══════════════════════════════════════════════════════════
class MedicineTab(QWidget):
    def __init__(self):
        super().__init__()
        self._build_ui()
        self._apply_style()
        self.load_data()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        tabs = QTabWidget()

        # ── Sub-tab 1: Medicine inventory ─────────────────────────
        inv_widget = QWidget()
        inv_layout = QVBoxLayout(inv_widget)
        inv_layout.setContentsMargins(12, 12, 12, 12)
        inv_layout.setSpacing(8)

        # Header
        h_row = QHBoxLayout()
        h_row.addWidget(QLabel("💊 Kho thuốc"))
        h_row.addStretch()
        self.add_med_btn = QPushButton("➕ Thêm thuốc")
        self.add_med_btn.setObjectName("primaryBtn")
        self.add_med_btn.clicked.connect(self._add_medicine)
        h_row.addWidget(self.add_med_btn)
        inv_layout.addLayout(h_row)

        # Filter
        f_row = QHBoxLayout()
        self.med_search = QLineEdit()
        self.med_search.setPlaceholderText("🔍  Tìm theo tên thuốc, hoạt chất")
        self.med_search.setObjectName("searchBox")
        self.med_search.textChanged.connect(self.load_data)
        self.cat_cb = QComboBox()
        self.cat_cb.addItems(["Tất cả nhóm"] + MEDICINE_CATEGORIES)
        self.cat_cb.currentIndexChanged.connect(self.load_data)
        self.low_stock_cb = QComboBox()
        self.low_stock_cb.addItems(["Tất cả", "⚠️ Sắp hết hàng", "⏰ Sắp hết hạn"])
        self.low_stock_cb.currentIndexChanged.connect(self.load_data)
        f_row.addWidget(self.med_search, 2)
        f_row.addWidget(self.cat_cb)
        f_row.addWidget(self.low_stock_cb)
        inv_layout.addLayout(f_row)

        self.med_count_lbl = QLabel()
        self.med_count_lbl.setObjectName("countLabel")
        inv_layout.addWidget(self.med_count_lbl)

        # Table
        self.med_table = QTableWidget()
        cols = ["Mã", "Tên thuốc", "Hoạt chất", "Nhóm", "Đơn vị",
                "Tồn kho", "Min", "Giá", "Hạn SD", "Nhà CC"]
        self.med_table.setColumnCount(len(cols))
        self.med_table.setHorizontalHeaderLabels(cols)
        self.med_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.med_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.med_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.med_table.setAlternatingRowColors(True)
        self.med_table.verticalHeader().setVisible(False)
        inv_layout.addWidget(self.med_table)

        # Actions
        a_row = QHBoxLayout()
        self.edit_med_btn   = QPushButton("✏️ Sửa");    self.edit_med_btn.setObjectName("actionBtn")
        self.delete_med_btn = QPushButton("🗑️ Xoá");   self.delete_med_btn.setObjectName("dangerBtn")
        self.edit_med_btn.clicked.connect(self._edit_medicine)
        self.delete_med_btn.clicked.connect(self._delete_medicine)
        a_row.addWidget(self.edit_med_btn)
        a_row.addWidget(self.delete_med_btn)
        a_row.addStretch()
        inv_layout.addLayout(a_row)
        tabs.addTab(inv_widget, "💊 Kho thuốc")

        # ── Sub-tab 2: Prescriptions ──────────────────────────────
        presc_widget = QWidget()
        pl = QVBoxLayout(presc_widget)
        pl.setContentsMargins(12, 12, 12, 12)
        pl.setSpacing(8)

        ph_row = QHBoxLayout()
        ph_row.addWidget(QLabel("📝 Danh sách đơn thuốc"))
        ph_row.addStretch()
        self.new_presc_btn = QPushButton("📝 Kê đơn thuốc mới")
        self.new_presc_btn.setObjectName("primaryBtn")
        self.new_presc_btn.clicked.connect(self._new_prescription)
        ph_row.addWidget(self.new_presc_btn)
        pl.addLayout(ph_row)

        self.presc_table = QTableWidget()
        pcols = ["Mã ĐT", "Bệnh nhân", "Bác sĩ", "Ngày kê", "Số loại thuốc", "Ghi chú"]
        self.presc_table.setColumnCount(len(pcols))
        self.presc_table.setHorizontalHeaderLabels(pcols)
        self.presc_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.presc_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.presc_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.presc_table.setAlternatingRowColors(True)
        self.presc_table.verticalHeader().setVisible(False)
        pl.addWidget(self.presc_table)
        tabs.addTab(presc_widget, "📋 Đơn thuốc")

        layout.addWidget(tabs)

    def load_data(self):
        search   = self.med_search.text().strip()
        category = self.cat_cb.currentText()
        filter_t = self.low_stock_cb.currentText()
        if category == "Tất cả nhóm": category = ""
        low_stock  = "⚠️ Sắp hết hàng" in filter_t
        near_expiry = "⏰ Sắp hết hạn"  in filter_t

        rows = dao.get_all_medicines(search, category, low_stock, near_expiry)
        self.med_table.setRowCount(len(rows))
        for r, m in enumerate(rows):
            price_str = f"{int(m['price'] or 0):,}"
            is_low = m["stock_qty"] <= m["min_stock"]
            vals = [m["medicine_code"], m["name"], m["generic_name"] or "",
                    m["category"] or "", m["unit"] or "",
                    str(m["stock_qty"]), str(m["min_stock"]),
                    f"{price_str} VNĐ", m["expiry_date"] or "", m["supplier"] or ""]
            for c, v in enumerate(vals):
                item = QTableWidgetItem(v)
                item.setData(Qt.ItemDataRole.UserRole.value, m["id"])
                if c == 5 and is_low:
                    item.setBackground(QColor("#fff5f5"))
                    item.setForeground(QColor("#c53030"))
                self.med_table.setItem(r, c, item)
        self.med_count_lbl.setText(f"Tổng: {len(rows)} loại thuốc")

        # Load prescriptions
        prescriptions = dao.get_all_prescriptions()
        self.presc_table.setRowCount(len(prescriptions))
        for r, p in enumerate(prescriptions):
            vals = [str(p["id"]), p["patient_name"] or "", p["doctor_name"] or "",
                    (p["issue_date"] or "")[:10], str(p["item_count"]), p["notes"] or ""]
            for c, v in enumerate(vals):
                self.presc_table.setItem(r, c, QTableWidgetItem(v))

    def _selected_med_id(self):
        row = self.med_table.currentRow()
        if row < 0:
            QMessageBox.information(self, "Chưa chọn", "Vui lòng chọn một loại thuốc.")
            return None
        return self.med_table.item(row, 0).data(Qt.ItemDataRole.UserRole.value)

    def _add_medicine(self):
        dlg = MedicineFormDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            dao.add_medicine(dlg.result_data)
            self.load_data()

    def _edit_medicine(self):
        mid = self._selected_med_id()
        if not mid: return
        m = dao.get_medicine_by_id(mid)
        dlg = MedicineFormDialog(self, med_data=m)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            dao.update_medicine(mid, dlg.result_data)
            self.load_data()

    def _delete_medicine(self):
        mid = self._selected_med_id()
        if not mid: return
        m = dao.get_medicine_by_id(mid)
        reply = QMessageBox.question(self, "Xác nhận",
                                     f"Xoá thuốc «{m['name']}»?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            dao.delete_medicine(mid)
            self.load_data()

    def _new_prescription(self):
        # For demo — in real use, link to a medical_record_id
        dlg = PrescriptionDialog(self, medical_record_id=None, doctor_id=None)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            dao.save_prescription(dlg.result_data)
            self.load_data()
            QMessageBox.information(self, "Thành công", "Đã lưu đơn thuốc.")

    def _apply_style(self):
        self.setStyleSheet("""
        QWidget { background: #f7fafc; font-family: 'Segoe UI'; }
        QLabel { font-size: 13px; font-weight: 600; color: #1a365d; }
        #searchBox {
            border: 1.5px solid #cbd5e0; border-radius: 8px;
            padding: 8px 12px; font-size: 13px; background: white;
        }
        QComboBox {
            border: 1.5px solid #cbd5e0; border-radius: 6px;
            padding: 6px 8px; font-size: 12px; background: white;
        }
        #primaryBtn { background: #553c9a; color: white; border: none; border-radius: 7px; padding: 8px 16px; font-weight: 600; }
        #primaryBtn:hover { background: #44337a; }
        #actionBtn { background: #edf2f7; color: #2d3748; border: none; border-radius: 6px; padding: 7px 14px; font-size: 12px; }
        #dangerBtn { background: #fff5f5; color: #c53030; border: 1px solid #fed7d7; border-radius: 6px; padding: 7px 14px; font-size: 12px; }
        #countLabel { color: #718096; font-size: 12px; font-weight: 400; }
        QTableWidget { border: 1px solid #e2e8f0; border-radius: 8px; font-size: 12px; gridline-color: #f0f0f0; }
        QHeaderView::section { background: #edf2f7; font-weight: 600; padding: 8px; border: none; }
        QTabWidget::pane { border: 1px solid #e2e8f0; border-radius: 8px; background: white; }
        QTabBar::tab { padding: 8px 18px; font-size: 12px; }
        QTabBar::tab:selected { background: #553c9a; color: white; border-radius: 6px 6px 0 0; }
        """)
