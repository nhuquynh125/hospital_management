import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QMessageBox, QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView, QGroupBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

import database.dao as dao
import core.auth as auth

class LeaveManagementTab(QWidget):
    def __init__(self):
        super().__init__()
        self.user = auth.get_current_user() or {}
        self.role = self.user.get("role", "")
        self._build_ui()
        self._apply_style()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 20, 20, 20)
        root.setSpacing(20)

        # Header
        header = QFrame()
        hl = QHBoxLayout(header)
        hl.setContentsMargins(0, 0, 0, 0)
        
        title = QLabel("🏖️  Quản lý Đơn xin Nghỉ phép")
        title.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        title.setObjectName("mainTitle")
        hl.addWidget(title)
        hl.addStretch()

        root.addWidget(header)

        # Container
        grp = QGroupBox("Danh sách Đơn xin Nghỉ phép")
        grp.setObjectName("groupBox")
        gl = QVBoxLayout(grp)

        self.table = QTableWidget()
        cols = ["Mã Đơn", "Tên Nhân Viên", "Chức vụ", "Loại Nghỉ", "Từ Ngày", "Đến Ngày", "Lý do", "Trạng thái"]
        self.table.setColumnCount(len(cols))
        self.table.setHorizontalHeaderLabels(cols)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        gl.addWidget(self.table)

        btn_row = QHBoxLayout()
        if self.role == "hr_manager":
            btn_appr = QPushButton("✅ Duyệt Đơn")
            btn_appr.setObjectName("primaryBtn")
            btn_appr.setCursor(Qt.CursorShape.PointingHandCursor)
            btn_appr.clicked.connect(lambda: self._set_status("Đã duyệt"))
            
            btn_rej = QPushButton("❌ Từ chối")
            btn_rej.setObjectName("rejectBtn")
            btn_rej.setCursor(Qt.CursorShape.PointingHandCursor)
            btn_rej.clicked.connect(lambda: self._set_status("Từ chối"))

            btn_row.addWidget(btn_appr)
            btn_row.addWidget(btn_rej)
            
        btn_row.addStretch()

        gl.addLayout(btn_row)
        root.addWidget(grp)
        
        self._load_data()

    def _apply_style(self):
        self.setStyleSheet("""
        QWidget { background: #f7fafc; font-family: 'Segoe UI'; }
        #mainTitle { color: #1a365d; }
        #groupBox {
            border: 1px solid #e2e8f0; border-radius: 10px;
            background: white; font-weight: 600; font-size: 13px; padding: 10px;
        }
        #groupBox::title {
            subcontrol-origin: margin; left: 12px;
            padding: 0 6px; color: #2d3748;
        }
        QTableWidget { border: 1px solid #e2e8f0; font-size: 13px; }
        QHeaderView::section {
            background: #edf2f7; font-weight: 600; padding: 8px; border: none;
        }
        #primaryBtn {
            background: #276749; color: white; border: none;
            border-radius: 7px; padding: 10px 20px; font-weight: 600; font-size: 13px;
        }
        #primaryBtn:hover { background: #22543d; }
        #rejectBtn {
            background: #c53030; color: white; border: none;
            border-radius: 7px; padding: 10px 20px; font-weight: 600; font-size: 13px;
        }
        #rejectBtn:hover { background: #9b2c2c; }
        """)

    def _load_data(self):
        if self.role == "hr_manager":
            raw_reqs = dao.get_all_leave_requests()
            reqs = [dict(r) for r in raw_reqs]
        else:
            staff_row = dao.get_staff_profile(self.user.get("id"))
            if staff_row:
                staff_dict = dict(staff_row)
                raw_reqs = dao.get_leave_requests_for_staff(staff_dict["id"])
                reqs = []
                for r in raw_reqs:
                    d = dict(r)
                    d["staff_name"] = staff_dict.get("full_name", "")
                    d["position"] = staff_dict.get("position", "")
                    reqs.append(d)
            else:
                reqs = []
                
        self.table.setRowCount(len(reqs))
        for r, d in enumerate(reqs):
            vals = [
                f"REQ{d['id']:04d}",
                d["staff_name"],
                d.get("position", ""),
                d["leave_type"],
                d["start_date"],
                d["end_date"],
                d["reason"],
                d["status"]
            ]
            for c, v in enumerate(vals):
                it = QTableWidgetItem(str(v))
                if c == 7:
                    if v == 'Đã duyệt':
                        it.setForeground(Qt.GlobalColor.darkGreen)
                    elif v == 'Từ chối':
                        it.setForeground(Qt.GlobalColor.darkRed)
                it.setData(Qt.ItemDataRole.UserRole, d["id"])
                self.table.setItem(r, c, it)

    def _set_status(self, stat):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Lỗi", "Vui lòng chọn một đơn xin nghỉ phép.")
            return
        
        req_id = self.table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        dao.update_leave_request_status(req_id, stat)
        QMessageBox.information(self, "Thành công", f"Đã cập nhật trạng thái đơn thành '{stat}'.")
        self._load_data()
