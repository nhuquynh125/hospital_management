from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QComboBox,
    QDialog, QFormLayout, QLineEdit, QTextEdit, QSpinBox,
    QMessageBox, QFrame, QScrollArea
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QColor

import database.dao as dao

ROOM_TYPES    = ["Khám", "Thường", "VIP", "ICU", "Phẫu thuật"]
ROOM_STATUSES = ["Trống", "Đang dùng", "Bảo trì"]
STATUS_COLORS = {
    "Trống":     ("#d4edda", "#155724"),
    "Đang dùng": ("#cce5ff", "#004085"),
    "Bảo trì":   ("#fff3cd", "#856404"),
}


# ── Room Form Dialog ─────────────────────────────────────
class RoomFormDialog(QDialog):
    def __init__(self, parent=None, room_data=None):
        super().__init__(parent)
        self.room_data = room_data
        self.is_edit = room_data is not None
        self.setWindowTitle("Sửa phòng" if self.is_edit else "Thêm phòng mới")
        self.setMinimumWidth(400)
        self.setModal(True)
        self._build_ui()
        if self.is_edit:
            self._fill_form()
        self._apply_style()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        icon = "✏️" if self.is_edit else "➕"
        title = QLabel(f"{icon} {'Sửa phòng' if self.is_edit else 'Thêm phòng mới'}")
        title.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        title.setObjectName("dlgTitle")
        layout.addWidget(title)

        form = QFormLayout()
        form.setSpacing(10)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        self.f_number   = QLineEdit(); self.f_number.setPlaceholderText("VD: P101, ICU01, V301")
        self.f_type     = QComboBox(); self.f_type.addItems(ROOM_TYPES)
        self.f_capacity = QSpinBox();  self.f_capacity.setRange(1, 20); self.f_capacity.setValue(2)
        self.f_floor    = QSpinBox();  self.f_floor.setRange(1, 20);    self.f_floor.setValue(1)
        self.f_status   = QComboBox(); self.f_status.addItems(ROOM_STATUSES)
        self.f_notes    = QTextEdit(); self.f_notes.setMaximumHeight(60)

        form.addRow("Số phòng *:",  self.f_number)
        form.addRow("Loại phòng:", self.f_type)
        form.addRow("Sức chứa:",   self.f_capacity)
        form.addRow("Tầng:",       self.f_floor)
        form.addRow("Trạng thái:", self.f_status)
        form.addRow("Ghi chú:",    self.f_notes)
        layout.addLayout(form)

        btn_row = QHBoxLayout(); btn_row.addStretch()
        self.cancel_btn = QPushButton("Huỷ"); self.cancel_btn.setObjectName("cancelBtn")
        self.save_btn   = QPushButton("Lưu"); self.save_btn.setObjectName("saveBtn")
        self.cancel_btn.clicked.connect(self.reject)
        self.save_btn.clicked.connect(self._save)
        btn_row.addWidget(self.cancel_btn); btn_row.addWidget(self.save_btn)
        layout.addLayout(btn_row)

    def _fill_form(self):
        r = self.room_data
        self.f_number.setText(r["room_number"] or "")
        idx = self.f_type.findText(r["room_type"] or "Khám")
        if idx >= 0: self.f_type.setCurrentIndex(idx)
        self.f_capacity.setValue(r["capacity"] or 1)
        self.f_floor.setValue(r["floor"] or 1)
        idx = self.f_status.findText(r["status"] or "Trống")
        if idx >= 0: self.f_status.setCurrentIndex(idx)
        self.f_notes.setPlainText(r["notes"] or "")

    def _save(self):
        number = self.f_number.text().strip()
        if not number:
            QMessageBox.warning(self, "Thiếu thông tin", "Vui lòng nhập số phòng.")
            return
        self.result_data = {
            "room_number": number,
            "room_type":   self.f_type.currentText(),
            "capacity":    self.f_capacity.value(),
            "floor":       self.f_floor.value(),
            "status":      self.f_status.currentText(),
            "notes":       self.f_notes.toPlainText().strip(),
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
        #saveBtn  { background: #744210; color: white; border: none; border-radius: 6px; padding: 8px 20px; font-weight: 600; }
        #saveBtn:hover { background: #5c3209; }
        #cancelBtn { background: #e2e8f0; color: #4a5568; border: none; border-radius: 6px; padding: 8px 20px; }
        """)


# ── Room Card ─────────────────────────────────────────────
class RoomCard(QFrame):
    def __init__(self, room, on_click, selected_id_ref):
        super().__init__()
        self._room        = room
        self._on_click    = on_click
        self._sel_ref     = selected_id_ref
        self._render()

    def _render(self):
        room   = self._room
        status = room["status"]
        bg, fg = STATUS_COLORS.get(status, ("#f7fafc", "#2d3748"))
        self.setFixedSize(130, 100)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._bg = bg; self._fg = fg
        self._update_border(False)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(3)

        icon_map = {"Khám": "🏥", "Thường": "🛏️", "VIP": "⭐", "ICU": "🚨", "Phẫu thuật": "🔪"}
        icon = QLabel(icon_map.get(room["room_type"], "🏠"))
        icon.setFont(QFont("Segoe UI", 18))
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon.setStyleSheet("background:transparent;")

        num = QLabel(f"Phòng {room['room_number']}")
        num.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        num.setStyleSheet(f"color:{fg}; background:transparent;")
        num.setAlignment(Qt.AlignmentFlag.AlignCenter)

        st = QLabel(status)
        st.setFont(QFont("Segoe UI", 8))
        st.setStyleSheet(f"color:{fg}; background:transparent;")
        st.setAlignment(Qt.AlignmentFlag.AlignCenter)

        cap = QLabel(f"Sức chứa: {room['capacity']}")
        cap.setFont(QFont("Segoe UI", 8))
        cap.setStyleSheet("color:#718096; background:transparent;")
        cap.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(icon)
        layout.addWidget(num)
        layout.addWidget(st)
        layout.addWidget(cap)

    def _update_border(self, selected: bool):
        bg, fg = self._bg, self._fg
        border = f"2px solid {fg}" if selected else f"1.5px solid {fg}40"
        self.setStyleSheet(f"""
            QFrame {{
                background:{bg}; border-radius:10px; border:{border};
            }}
            QFrame:hover {{ border:2px solid {fg}; }}
        """)

    def mousePressEvent(self, event):
        self._on_click(self._room["id"])


# ── Main Room Tab ─────────────────────────────────────────
class RoomTab(QWidget):
    def __init__(self):
        super().__init__()
        self._selected_room_id = None
        self._cards = {}   # room_id → RoomCard
        self._build_ui()
        self._apply_style()
        self.load_data()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        # Header
        header_row = QHBoxLayout()
        title = QLabel("🏠 Quản lý phòng / giường bệnh")
        title.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        title.setObjectName("sectionTitle")
        header_row.addWidget(title)
        header_row.addStretch()

        self.add_btn = QPushButton("➕ Thêm phòng")
        self.add_btn.setObjectName("primaryBtn")
        self.add_btn.clicked.connect(self._add_room)
        header_row.addWidget(self.add_btn)
        layout.addLayout(header_row)

        # Filter + stats row
        filter_row = QHBoxLayout()
        self.type_cb   = QComboBox(); self.type_cb.addItems(["Tất cả loại"] + ROOM_TYPES)
        self.status_cb = QComboBox(); self.status_cb.addItems(["Tất cả trạng thái"] + ROOM_STATUSES)
        self.type_cb.currentIndexChanged.connect(self.load_data)
        self.status_cb.currentIndexChanged.connect(self.load_data)

        self.lbl_total = self._stat_lbl("Tổng",      "0", "#2b6cb0", "#ebf8ff")
        self.lbl_empty = self._stat_lbl("Trống",     "0", "#155724", "#d4edda")
        self.lbl_inuse = self._stat_lbl("Đang dùng", "0", "#004085", "#cce5ff")
        self.lbl_maint = self._stat_lbl("Bảo trì",   "0", "#856404", "#fff3cd")

        filter_row.addWidget(self.type_cb)
        filter_row.addWidget(self.status_cb)
        filter_row.addStretch()
        for lbl in [self.lbl_total, self.lbl_empty, self.lbl_inuse, self.lbl_maint]:
            filter_row.addWidget(lbl)
        layout.addLayout(filter_row)

        # Grid scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        self.grid_widget = QWidget()
        self.grid_widget.setObjectName("gridFrame")
        from PyQt6.QtWidgets import QGridLayout
        self.grid_layout = QGridLayout(self.grid_widget)
        self.grid_layout.setSpacing(12)
        self.grid_layout.setContentsMargins(12, 12, 12, 12)
        self.grid_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)

        scroll.setWidget(self.grid_widget)
        layout.addWidget(scroll)

        # Actions
        action_row = QHBoxLayout()
        self.edit_btn   = QPushButton("✏️ Sửa");          self.edit_btn.setObjectName("actionBtn")
        self.status_btn = QPushButton("🔄 Đổi trạng thái"); self.status_btn.setObjectName("actionBtn")
        self.delete_btn = QPushButton("🗑️ Xoá");           self.delete_btn.setObjectName("dangerBtn")
        self.edit_btn.clicked.connect(self._edit_room)
        self.status_btn.clicked.connect(self._change_status)
        self.delete_btn.clicked.connect(self._delete_room)
        action_row.addWidget(self.edit_btn)
        action_row.addWidget(self.status_btn)
        action_row.addWidget(self.delete_btn)
        action_row.addStretch()
        layout.addLayout(action_row)

    def _stat_lbl(self, label, value, fg, bg):
        f = QFrame()
        f.setStyleSheet(f"background:{bg}; border-radius:8px; border:1px solid {fg}30;")
        fl = QHBoxLayout(f); fl.setContentsMargins(10, 6, 10, 6); fl.setSpacing(6)
        v = QLabel(value); v.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        v.setStyleSheet(f"color:{fg}; background:transparent;")
        n = QLabel(label); n.setStyleSheet(f"color:{fg}; font-size:11px; background:transparent;")
        fl.addWidget(v); fl.addWidget(n)
        f._value_lbl = v
        return f

    def load_data(self):
        type_f   = self.type_cb.currentText()
        status_f = self.status_cb.currentText()
        if type_f   == "Tất cả loại":       type_f   = ""
        if status_f == "Tất cả trạng thái": status_f = ""

        rooms     = dao.get_all_rooms(type_f, status_f)
        all_rooms = dao.get_all_rooms()

        # Update stats
        self.lbl_total._value_lbl.setText(str(len(all_rooms)))
        self.lbl_empty._value_lbl.setText(str(sum(1 for r in all_rooms if r["status"] == "Trống")))
        self.lbl_inuse._value_lbl.setText(str(sum(1 for r in all_rooms if r["status"] == "Đang dùng")))
        self.lbl_maint._value_lbl.setText(str(sum(1 for r in all_rooms if r["status"] == "Bảo trì")))

        # ── Xoá sạch grid ────────────────────────────────────────
        self._cards.clear()
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            w = item.widget()
            if w:
                w.setParent(None)
                w.deleteLater()

        # ── Render card (chỉ đúng số phòng, không thêm ô trống) ──
        COLS = 6
        for idx, room in enumerate(rooms):
            card = RoomCard(room, self._on_card_click, self._selected_room_id)
            self.grid_layout.addWidget(card, idx // COLS, idx % COLS)
            self._cards[room["id"]] = card

        # Highlight card đang chọn (nếu còn tồn tại)
        if self._selected_room_id in self._cards:
            self._cards[self._selected_room_id]._update_border(True)

    def _on_card_click(self, room_id):
        # Bỏ highlight cũ
        if self._selected_room_id and self._selected_room_id in self._cards:
            self._cards[self._selected_room_id]._update_border(False)
        self._selected_room_id = room_id
        if room_id in self._cards:
            self._cards[room_id]._update_border(True)

    def _get_selected(self):
        if not self._selected_room_id:
            QMessageBox.information(self, "Chưa chọn", "Vui lòng click vào một phòng.")
            return None
        return dao.get_room_by_id(self._selected_room_id)

    def _add_room(self):
        dlg = RoomFormDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            dao.add_room(dlg.result_data)
            self.load_data()

    def _edit_room(self):
        room = self._get_selected()
        if not room: return
        dlg = RoomFormDialog(self, room_data=room)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            dao.update_room(room["id"], dlg.result_data)
            self.load_data()

    def _change_status(self):
        room = self._get_selected()
        if not room: return
        cycle = {"Trống": "Đang dùng", "Đang dùng": "Bảo trì", "Bảo trì": "Trống"}
        new_status = cycle.get(room["status"], "Trống")
        dao.update_room_status(room["id"], new_status)
        self.load_data()

    def _delete_room(self):
        room = self._get_selected()
        if not room: return
        reply = QMessageBox.question(self, "Xác nhận",
                                     f"Xoá phòng {room['room_number']}?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            dao.delete_room(room["id"])
            self._selected_room_id = None
            self.load_data()

    def _apply_style(self):
        self.setStyleSheet("""
        QWidget { background: #f7fafc; font-family: 'Segoe UI'; }
        #sectionTitle { color: #1a365d; }
        QComboBox {
            border: 1.5px solid #cbd5e0; border-radius: 6px;
            padding: 6px 8px; font-size: 12px; background: white;
        }
        #primaryBtn { background: #744210; color: white; border: none;
            border-radius: 7px; padding: 8px 16px; font-weight: 600; }
        #primaryBtn:hover { background: #5c3209; }
        #actionBtn { background: #edf2f7; color: #2d3748; border: none;
            border-radius: 6px; padding: 7px 14px; font-size: 12px; }
        #actionBtn:hover { background: #e2e8f0; }
        #dangerBtn { background: #fff5f5; color: #c53030; border: 1px solid #fed7d7;
            border-radius: 6px; padding: 7px 14px; font-size: 12px; }
        #gridFrame { background: white; border-radius: 10px; border: 1px solid #e2e8f0; }
        """)
