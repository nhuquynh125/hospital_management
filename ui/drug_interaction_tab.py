from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QTableWidget, QTableWidgetItem, QHeaderView,
    QAbstractItemView, QMessageBox, QLineEdit, QComboBox,
    QDialog, QFormLayout, QTextEdit, QSplitter, QScrollArea,
    QGridLayout, QGroupBox
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QColor

import core.auth as auth
from database.dao import (
    get_all_medicines, get_all_patients, get_patient_by_id,
    check_drug_interactions, get_patient_allergies,
    get_drug_interactions_list, add_drug_interaction,
    delete_drug_interaction, get_patient_prescriptions_active
)


# ─── Severity config ──────────────────────────────────────────────
SEVERITY_CONFIG = {
    "Nguy hiểm": {
        "label": "NGUY HIEM",
        "color": "#E53E3E",
        "bg":    "#FFF5F5",
        "border":"#FC8181",
        "icon":  "🔴",
        "desc":  "Chong chi dinh – Khong nen ke don"
    },
    "Thận trọng": {
        "label": "THAN TRONG",
        "color": "#DD6B20",
        "bg":    "#FFFAF0",
        "border":"#F6AD55",
        "icon":  "🟠",
        "desc":  "Tuong tac nghiem trong – Can ghi nhan ly do"
    },
    "Theo dõi": {
        "label": "THEO DOI",
        "color": "#D69E2E",
        "bg":    "#FFFFF0",
        "border":"#F6E05E",
        "icon":  "🟡",
        "desc":  "Tuong tac nhe – Theo doi benh nhan"
    },
}


class AlertBanner(QFrame):
    """A styled alert card for one drug interaction."""

    def __init__(self, med1, med2, severity, description, parent=None):
        super().__init__(parent)
        cfg = SEVERITY_CONFIG.get(severity, SEVERITY_CONFIG["Theo dõi"])
        self.setStyleSheet(f"""
            QFrame {{
                background: {cfg['bg']};
                border: 1.5px solid {cfg['border']};
                border-radius: 10px;
            }}
        """)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(14, 10, 14, 10)
        lay.setSpacing(4)

        # Header row
        header = QHBoxLayout()
        icon_lbl = QLabel(cfg["icon"])
        icon_lbl.setFont(QFont("Segoe UI", 16))
        icon_lbl.setStyleSheet("background:transparent;")

        sev_lbl = QLabel(cfg["label"])
        sev_lbl.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        sev_lbl.setStyleSheet(f"color:{cfg['color']}; background:transparent;")

        pair_lbl = QLabel(f"  {med1}  ×  {med2}")
        pair_lbl.setFont(QFont("Segoe UI", 11))
        pair_lbl.setStyleSheet(f"color:#2D3748; background:transparent;")

        header.addWidget(icon_lbl)
        header.addWidget(sev_lbl)
        header.addWidget(pair_lbl)
        header.addStretch()
        lay.addLayout(header)

        # Description
        if description:
            desc_lbl = QLabel(description)
            desc_lbl.setWordWrap(True)
            desc_lbl.setStyleSheet(f"color:#4A5568; font-size:12px; background:transparent;")
            lay.addWidget(desc_lbl)

        # Advisory line
        adv_lbl = QLabel(cfg["desc"])
        adv_lbl.setStyleSheet(f"color:{cfg['color']}; font-size:11px; font-weight:600; background:transparent;")
        lay.addWidget(adv_lbl)


class InteractionCheckerPanel(QWidget):
    """Left panel: select patient + drugs, run check, show alerts."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._selected_meds = []   # list of (id, name)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        # ── Patient selector ────────────────────────────────────────
        grp_patient = QGroupBox("👤  Benh nhan")
        grp_patient.setStyleSheet(self._grp_style())
        gl = QVBoxLayout(grp_patient)

        self._patient_combo = QComboBox()
        self._patient_combo.setPlaceholderText("-- Chon benh nhan --")
        self._patient_combo.setFixedHeight(34)
        self._patient_combo.currentIndexChanged.connect(self._on_patient_changed)
        gl.addWidget(self._patient_combo)

        self._allergy_label = QLabel("Di ung: –")
        self._allergy_label.setWordWrap(True)
        self._allergy_label.setStyleSheet(
            "background:#FFF5F5; border:1px solid #FC8181; border-radius:6px;"
            "padding:6px 10px; color:#C53030; font-size:12px;"
        )
        self._allergy_label.setVisible(False)
        gl.addWidget(self._allergy_label)
        layout.addWidget(grp_patient)

        # ── Drug selector ───────────────────────────────────────────
        grp_drugs = QGroupBox("💊  Them thuoc vao don")
        grp_drugs.setStyleSheet(self._grp_style())
        dl = QVBoxLayout(grp_drugs)

        search_row = QHBoxLayout()
        self._drug_search = QLineEdit()
        self._drug_search.setPlaceholderText("Tim thuoc theo ten...")
        self._drug_search.setFixedHeight(32)
        self._drug_search.textChanged.connect(self._filter_medicines)
        search_row.addWidget(self._drug_search)
        dl.addLayout(search_row)

        self._medicine_list = QTableWidget()
        self._medicine_list.setColumnCount(3)
        self._medicine_list.setHorizontalHeaderLabels(["Ten thuoc", "Danh muc", "Ton kho"])
        self._medicine_list.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self._medicine_list.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self._medicine_list.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self._medicine_list.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._medicine_list.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._medicine_list.setFixedHeight(160)
        self._medicine_list.setStyleSheet("QTableWidget { border:1px solid #E2E8F0; border-radius:6px; }")
        dl.addWidget(self._medicine_list)

        add_btn = QPushButton("➕  Them vao don")
        add_btn.setFixedHeight(32)
        add_btn.setStyleSheet(self._btn_style("#2B6CB0", "#2C5282"))
        add_btn.clicked.connect(self._add_selected_medicine)
        dl.addWidget(add_btn)
        layout.addWidget(grp_drugs)

        # ── Selected drug list ──────────────────────────────────────
        grp_selected = QGroupBox("📋  Thuoc trong don hien tai")
        grp_selected.setStyleSheet(self._grp_style())
        sl = QVBoxLayout(grp_selected)

        self._selected_table = QTableWidget()
        self._selected_table.setColumnCount(2)
        self._selected_table.setHorizontalHeaderLabels(["Ten thuoc", ""])
        self._selected_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self._selected_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self._selected_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._selected_table.setFixedHeight(130)
        self._selected_table.setStyleSheet("QTableWidget { border:1px solid #E2E8F0; border-radius:6px; }")
        sl.addWidget(self._selected_table)
        layout.addWidget(grp_selected)

        # ── Check button ────────────────────────────────────────────
        self._check_btn = QPushButton("🔍  Kiem tra tuong tac & di ung")
        self._check_btn.setFixedHeight(42)
        self._check_btn.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        self._check_btn.setStyleSheet(self._btn_style("#276749", "#22543D"))
        self._check_btn.clicked.connect(self._run_check)
        layout.addWidget(self._check_btn)

        layout.addStretch()
        self._load_data()

    def _load_data(self):
        patients = get_all_patients()
        self._patients_data = list(patients)
        self._patient_combo.clear()
        self._patient_combo.addItem("-- Chon benh nhan --", None)
        for p in self._patients_data:
            self._patient_combo.addItem(f"{p['patient_code']}  –  {p['full_name']}", p["id"])

        self._all_medicines = list(get_all_medicines())
        self._fill_medicine_table(self._all_medicines)

    def _fill_medicine_table(self, meds):
        self._medicine_list.setRowCount(0)
        for m in meds:
            r = self._medicine_list.rowCount()
            self._medicine_list.insertRow(r)
            self._medicine_list.setItem(r, 0, QTableWidgetItem(m["name"]))
            self._medicine_list.setItem(r, 1, QTableWidgetItem(m["category"] or "–"))
            self._medicine_list.setItem(r, 2, QTableWidgetItem(str(m["stock_qty"])))
            self._medicine_list.item(r, 0).setData(Qt.ItemDataRole.UserRole, m["id"])

    def _filter_medicines(self, text):
        filtered = [m for m in self._all_medicines if text.lower() in m["name"].lower()]
        self._fill_medicine_table(filtered)

    def _on_patient_changed(self, idx):
        patient_id = self._patient_combo.itemData(idx)
        if not patient_id:
            self._allergy_label.setVisible(False)
            return
        patient = get_patient_by_id(patient_id)
        allergies = patient["allergies"] if patient else None
        if allergies and allergies.strip():
            self._allergy_label.setText(f"⚠️  Di ung da biet: {allergies}")
            self._allergy_label.setVisible(True)
        else:
            self._allergy_label.setVisible(False)

    def _add_selected_medicine(self):
        row = self._medicine_list.currentRow()
        if row < 0:
            QMessageBox.information(self, "Thong bao", "Vui long chon mot thuoc tu danh sach.")
            return
        med_id = self._medicine_list.item(row, 0).data(Qt.ItemDataRole.UserRole)
        med_name = self._medicine_list.item(row, 0).text()
        if any(m[0] == med_id for m in self._selected_meds):
            QMessageBox.information(self, "Thong bao", "Thuoc nay da co trong don.")
            return
        self._selected_meds.append((med_id, med_name))
        self._refresh_selected_table()

    def _refresh_selected_table(self):
        self._selected_table.setRowCount(0)
        for med_id, med_name in self._selected_meds:
            r = self._selected_table.rowCount()
            self._selected_table.insertRow(r)
            self._selected_table.setItem(r, 0, QTableWidgetItem(med_name))
            rm_btn = QPushButton("✖")
            rm_btn.setFixedSize(28, 24)
            rm_btn.setStyleSheet("background:#FED7D7; border:none; border-radius:4px; color:#C53030; font-weight:bold;")
            rm_btn.clicked.connect(lambda _, mid=med_id: self._remove_medicine(mid))
            self._selected_table.setCellWidget(r, 1, rm_btn)
            self._selected_table.item(r, 0).setData(Qt.ItemDataRole.UserRole, med_id)

    def _remove_medicine(self, med_id):
        self._selected_meds = [(i, n) for i, n in self._selected_meds if i != med_id]
        self._refresh_selected_table()

    def _run_check(self):
        if len(self._selected_meds) < 1:
            QMessageBox.information(self, "Thong bao", "Vui long them it nhat 1 thuoc.")
            return
        self.check_requested.emit(
            [m[0] for m in self._selected_meds],
            self._patient_combo.currentData()
        )

    # Signal emitted when check is triggered
    from PyQt6.QtCore import pyqtSignal
    check_requested = None  # will be replaced below

    def _grp_style(self):
        return """
            QGroupBox {
                font-weight: 600; font-size: 12px; color: #2D3748;
                border: 1px solid #CBD5E0; border-radius: 8px; margin-top: 8px; padding: 10px 8px;
            }
            QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 4px; }
        """

    def _btn_style(self, color, hover):
        return f"""
            QPushButton {{
                background: {color}; color: white; border: none;
                border-radius: 7px; font-size: 12px; padding: 6px 12px;
            }}
            QPushButton:hover {{ background: {hover}; }}
        """


# Fix: define the signal properly on class level
from PyQt6.QtCore import pyqtSignal as _sig
InteractionCheckerPanel.check_requested = _sig(list, object)


class ResultPanel(QWidget):
    """Right panel: displays check results."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        # Header
        hdr = QLabel("📊  Ket qua kiem tra")
        hdr.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        hdr.setStyleSheet("color:#1A365D;")
        layout.addWidget(hdr)

        # Status banner
        self._status_banner = QLabel("Chua co ket qua. Them thuoc va nhan 'Kiem tra'.")
        self._status_banner.setStyleSheet(
            "background:#EBF8FF; border:1px solid #90CDF4; border-radius:8px;"
            "padding:10px 14px; color:#2C5282; font-size:12px;"
        )
        self._status_banner.setWordWrap(True)
        layout.addWidget(self._status_banner)

        # Scrollable alerts area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        self._alerts_container = QWidget()
        self._alerts_layout = QVBoxLayout(self._alerts_container)
        self._alerts_layout.setSpacing(10)
        self._alerts_layout.addStretch()
        scroll.setWidget(self._alerts_container)
        layout.addWidget(scroll, 1)

    def show_results(self, interactions, allergy_text, drug_names):
        # Clear previous
        while self._alerts_layout.count() > 1:
            item = self._alerts_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        total_alerts = len(interactions)
        has_allergy = bool(allergy_text and allergy_text.strip())
        critical = sum(1 for i in interactions if i.get("severity") == "Nguy hiểm")

        # Status banner
        if total_alerts == 0 and not has_allergy:
            self._status_banner.setText(
                f"✅  An toan  –  Kiem tra {len(drug_names)} thuoc, khong phat hien tuong tac hoac di ung."
            )
            self._status_banner.setStyleSheet(
                "background:#F0FFF4; border:1px solid #9AE6B4; border-radius:8px;"
                "padding:10px 14px; color:#276749; font-size:12px; font-weight:600;"
            )
        else:
            msg = f"⚠️  Phat hien {total_alerts} tuong tac thuoc"
            if critical:
                msg += f"  (🔴 {critical} NGUY HIEM)"
            if has_allergy:
                msg += "  +  Di ung benh nhan"
            self._status_banner.setText(msg)
            self._status_banner.setStyleSheet(
                "background:#FFF5F5; border:1px solid #FC8181; border-radius:8px;"
                "padding:10px 14px; color:#C53030; font-size:12px; font-weight:600;"
            )

        # Allergy card
        if has_allergy:
            allergy_card = QFrame()
            allergy_card.setStyleSheet("""
                QFrame { background:#FFF5F5; border:2px solid #E53E3E; border-radius:10px; }
            """)
            al = QVBoxLayout(allergy_card)
            al.setContentsMargins(14, 10, 14, 10)
            lbl = QLabel(f"🔴  DI UNG BENH NHAN – {allergy_text}")
            lbl.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
            lbl.setStyleSheet("color:#C53030; background:transparent;")
            lbl.setWordWrap(True)
            note = QLabel("Kiem tra ky cac thuoc ke don co phan ung cheo voi tien su di ung.")
            note.setStyleSheet("color:#E53E3E; font-size:11px; background:transparent;")
            al.addWidget(lbl); al.addWidget(note)
            self._alerts_layout.insertWidget(self._alerts_layout.count() - 1, allergy_card)

        # Interaction cards
        for interaction in interactions:
            card = AlertBanner(
                interaction.get("med1", "?"),
                interaction.get("med2", "?"),
                interaction.get("severity", "Theo dõi"),
                interaction.get("description", "")
            )
            self._alerts_layout.insertWidget(self._alerts_layout.count() - 1, card)


class InteractionDatabasePanel(QWidget):
    """Panel to view/add/delete drug interaction rules (admin/pharmacist)."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()
        self._load_data()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        # Toolbar
        toolbar = QHBoxLayout()
        title = QLabel("📚  Co so du lieu tuong tac thuoc")
        title.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        title.setStyleSheet("color:#1A365D;")
        toolbar.addWidget(title)
        toolbar.addStretch()

        self._search_box = QLineEdit()
        self._search_box.setPlaceholderText("Tim thuoc...")
        self._search_box.setFixedWidth(220)
        self._search_box.setFixedHeight(30)
        self._search_box.textChanged.connect(self._filter_table)
        toolbar.addWidget(self._search_box)

        add_btn = QPushButton("➕  Them tuong tac moi")
        add_btn.setFixedHeight(30)
        add_btn.setStyleSheet("""
            QPushButton { background:#2B6CB0; color:white; border:none; border-radius:6px; padding:0 12px; font-size:12px; }
            QPushButton:hover { background:#2C5282; }
        """)
        add_btn.clicked.connect(self._add_interaction)
        toolbar.addWidget(add_btn)
        layout.addLayout(toolbar)

        # Table
        self._table = QTableWidget()
        self._table.setColumnCount(5)
        self._table.setHorizontalHeaderLabels(["Thuoc 1", "Thuoc 2", "Muc do", "Mo ta", ""])
        self._table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self._table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self._table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self._table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        self._table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        self._table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._table.setAlternatingRowColors(True)
        self._table.setStyleSheet("""
            QTableWidget { border:1px solid #E2E8F0; border-radius:8px; gridline-color:#EDF2F7; }
            QHeaderView::section { background:#EBF8FF; color:#2B6CB0; font-weight:600; border:none; padding:6px; }
            QTableWidget::item:alternate { background:#F7FAFC; }
        """)
        layout.addWidget(self._table)

    def _load_data(self):
        self._all_rows = list(get_drug_interactions_list())
        self._fill_table(self._all_rows)

    def _fill_table(self, rows):
        self._table.setRowCount(0)
        severity_colors = {
            "Nguy hiểm":  "#E53E3E",
            "Thận trọng": "#DD6B20",
            "Theo dõi":   "#D69E2E",
        }
        for row in rows:
            r = self._table.rowCount()
            self._table.insertRow(r)
            self._table.setItem(r, 0, QTableWidgetItem(row["med1"]))
            self._table.setItem(r, 1, QTableWidgetItem(row["med2"]))

            sev_item = QTableWidgetItem(row["severity"])
            color = severity_colors.get(row["severity"], "#718096")
            sev_item.setForeground(QColor(color))
            sev_item.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
            self._table.setItem(r, 2, sev_item)
            self._table.setItem(r, 3, QTableWidgetItem(row["description"] or ""))

            del_btn = QPushButton("🗑")
            del_btn.setFixedSize(30, 24)
            del_btn.setStyleSheet("background:#FED7D7; border:none; border-radius:4px; color:#C53030;")
            del_btn.setToolTip("Xoa tuong tac nay")
            del_btn.clicked.connect(lambda _, rid=row["id"]: self._delete_interaction(rid))
            self._table.setCellWidget(r, 4, del_btn)
            self._table.item(r, 0).setData(Qt.ItemDataRole.UserRole, row["id"])

    def _filter_table(self, text):
        t = text.lower()
        filtered = [r for r in self._all_rows
                    if t in r["med1"].lower() or t in r["med2"].lower()]
        self._fill_table(filtered)

    def _add_interaction(self):
        dlg = AddInteractionDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self._load_data()

    def _delete_interaction(self, row_id):
        reply = QMessageBox.question(self, "Xac nhan xoa",
                                     "Ban co chac muon xoa tuong tac nay?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            delete_drug_interaction(row_id)
            self._load_data()


class AddInteractionDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Them tuong tac thuoc moi")
        self.setFixedSize(480, 340)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        title = QLabel("➕  Them tuong tac thuoc")
        title.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        title.setStyleSheet("color:#1A365D;")
        layout.addWidget(title)

        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        form.setSpacing(10)

        meds = list(get_all_medicines())
        med_names = [m["name"] for m in meds]
        self._med_ids = [m["id"] for m in meds]

        self._combo1 = QComboBox()
        self._combo1.addItems(med_names)
        self._combo1.setFixedHeight(32)
        form.addRow("Thuoc 1:", self._combo1)

        self._combo2 = QComboBox()
        self._combo2.addItems(med_names)
        self._combo2.setFixedHeight(32)
        form.addRow("Thuoc 2:", self._combo2)

        self._severity_combo = QComboBox()
        self._severity_combo.addItems(["Nguy hiểm", "Thận trọng", "Theo dõi"])
        self._severity_combo.setFixedHeight(32)
        form.addRow("Muc do:", self._severity_combo)

        self._desc_edit = QTextEdit()
        self._desc_edit.setFixedHeight(80)
        self._desc_edit.setPlaceholderText("Mo ta co che tuong tac, nguy co lam sang...")
        form.addRow("Mo ta:", self._desc_edit)

        layout.addLayout(form)

        # Buttons
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        cancel_btn = QPushButton("Huy")
        cancel_btn.setFixedHeight(34)
        cancel_btn.setStyleSheet("background:#EDF2F7; border:none; border-radius:6px; padding:0 16px;")
        cancel_btn.clicked.connect(self.reject)

        save_btn = QPushButton("Luu tuong tac")
        save_btn.setFixedHeight(34)
        save_btn.setStyleSheet("background:#2B6CB0; color:white; border:none; border-radius:6px; padding:0 16px;")
        save_btn.clicked.connect(self._save)
        btn_row.addWidget(cancel_btn)
        btn_row.addWidget(save_btn)
        layout.addLayout(btn_row)

    def _save(self):
        idx1 = self._combo1.currentIndex()
        idx2 = self._combo2.currentIndex()
        if idx1 == idx2:
            QMessageBox.warning(self, "Loi", "Vui long chon hai thuoc khac nhau.")
            return
        try:
            add_drug_interaction({
                "medicine_id_1": self._med_ids[idx1],
                "medicine_id_2": self._med_ids[idx2],
                "severity":      self._severity_combo.currentText(),
                "description":   self._desc_edit.toPlainText().strip(),
            })
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Loi", str(e))


class DrugInteractionTab(QWidget):
    """
    Module 1.2 – Drug Interaction & Allergy AI Alert System.
    Accessible to: doctor, pharmacist, admin.
    Two sub-sections:
      [Checker] – select patient + drugs, scan for interactions/allergies
      [Database] – manage interaction knowledge base (pharmacist/admin)
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._role = auth.get_current_user()["role"] if auth.get_current_user() else ""
        self._build_ui()
        self._apply_style()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 16, 20, 16)
        root.setSpacing(0)

        # ── Page header ─────────────────────────────────────────────
        hdr_frame = QFrame()
        hdr_frame.setObjectName("pageHeader")
        hdr_lay = QHBoxLayout(hdr_frame)
        hdr_lay.setContentsMargins(20, 14, 20, 14)

        icon_lbl = QLabel("💊")
        icon_lbl.setFont(QFont("Segoe UI", 26))
        icon_lbl.setStyleSheet("background:transparent;")

        txt_lay = QVBoxLayout()
        title = QLabel("He thong Canh bao Tuong tac Thuoc & Di ung")
        title.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        title.setStyleSheet("color:#1A365D; background:transparent;")
        sub = QLabel("Kiem tra tuong tac thuoc trong don ke va di ung benh nhan theo thoi gian thuc")
        sub.setStyleSheet("color:#4A5568; font-size:12px; background:transparent;")
        txt_lay.addWidget(title)
        txt_lay.addWidget(sub)

        hdr_lay.addWidget(icon_lbl)
        hdr_lay.addSpacing(10)
        hdr_lay.addLayout(txt_lay)
        hdr_lay.addStretch()
        root.addWidget(hdr_frame)
        root.addSpacing(12)

        # ── Tab switcher ─────────────────────────────────────────────
        tab_bar = QHBoxLayout()
        self._check_tab_btn = QPushButton("🔍  Kiem tra tuong tac")
        self._db_tab_btn    = QPushButton("📚  Quan ly co so du lieu")
        for btn in [self._check_tab_btn, self._db_tab_btn]:
            btn.setFixedHeight(36)
            btn.setCheckable(True)
            btn.setStyleSheet("""
                QPushButton { background:#EDF2F7; color:#4A5568; border:none; border-radius:7px; padding:0 16px; font-size:12px; }
                QPushButton:checked { background:#2B6CB0; color:white; font-weight:600; }
                QPushButton:hover:!checked { background:#E2E8F0; }
            """)
        self._check_tab_btn.setChecked(True)
        self._check_tab_btn.clicked.connect(lambda: self._switch_tab(0))
        self._db_tab_btn.clicked.connect(lambda: self._switch_tab(1))
        tab_bar.addWidget(self._check_tab_btn)
        tab_bar.addWidget(self._db_tab_btn)
        tab_bar.addStretch()
        root.addLayout(tab_bar)
        root.addSpacing(10)

        # ── Content stack ────────────────────────────────────────────
        from PyQt6.QtWidgets import QStackedWidget
        self._stack = QStackedWidget()

        # Page 0: Checker
        checker_widget = QWidget()
        checker_lay = QHBoxLayout(checker_widget)
        checker_lay.setSpacing(16)
        checker_lay.setContentsMargins(0, 0, 0, 0)

        self._checker_panel = InteractionCheckerPanel()
        self._checker_panel.setFixedWidth(380)
        self._result_panel  = ResultPanel()

        self._checker_panel.check_requested.connect(self._run_check)
        checker_lay.addWidget(self._checker_panel)
        checker_lay.addWidget(self._result_panel, 1)
        self._stack.addWidget(checker_widget)

        # Page 1: DB manager
        self._db_panel = InteractionDatabasePanel()
        self._stack.addWidget(self._db_panel)

        root.addWidget(self._stack, 1)

    def _switch_tab(self, idx):
        self._check_tab_btn.setChecked(idx == 0)
        self._db_tab_btn.setChecked(idx == 1)
        self._stack.setCurrentIndex(idx)
        if idx == 1:
            self._db_panel._load_data()

    def _run_check(self, med_ids, patient_id):
        interactions = check_drug_interactions(med_ids)
        allergy_text = ""
        if patient_id:
            patient = get_patient_by_id(patient_id)
            allergy_text = patient["allergies"] if patient else ""
        med_names = []
        for mid in med_ids:
            meds = [m for m in self._checker_panel._all_medicines if m["id"] == mid]
            if meds:
                med_names.append(meds[0]["name"])
        self._result_panel.show_results(interactions, allergy_text, med_names)

    def _apply_style(self):
        self.setStyleSheet("""
            QWidget { font-family:'Segoe UI'; background:#F7FAFC; }
            #pageHeader {
                background:white; border-radius:12px;
                border:1px solid #E2E8F0;
            }
        """)
