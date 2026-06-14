"""
Hospital Management System — Settings, Backup & Restore Tab
"""

import os, shutil, glob
from datetime import datetime

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QFileDialog, QMessageBox, QTableWidget,
    QTableWidgetItem, QHeaderView, QAbstractItemView, QLineEdit, QGroupBox,
    QFormLayout, QComboBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from database.schema import DB_PATH
import database.dao as dao
import core.auth as auth

BACKUP_DIR = os.path.join(os.path.dirname(os.path.dirname(DB_PATH)), "backups")


class SettingsTab(QWidget):
    def __init__(self):
        super().__init__()
        os.makedirs(BACKUP_DIR, exist_ok=True)
        self._build_ui()
        self._apply_style()
        self._load_backups()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        title = QLabel("⚙️ Cài đặt & Backup")
        title.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        title.setObjectName("sectionTitle")
        layout.addWidget(title)

        row = QHBoxLayout()
        row.setSpacing(16)
        row.setAlignment(Qt.AlignmentFlag.AlignTop)

        # ── LEFT: Backup/Restore ──────────────────────────────────
        backup_group = QGroupBox("💾 Sao lưu & Phục hồi Database")
        backup_group.setObjectName("groupBox")
        bl = QVBoxLayout(backup_group)
        bl.setSpacing(10)

        db_info = QLabel(f"📁 Database: {os.path.basename(DB_PATH)}\n"
                         f"📂 Thư mục backup: {BACKUP_DIR}")
        db_info.setObjectName("infoLbl")
        bl.addWidget(db_info)

        backup_btn = QPushButton("📦 Tạo Backup ngay")
        backup_btn.setObjectName("backupBtn")
        backup_btn.clicked.connect(self._do_backup)
        bl.addWidget(backup_btn)

        bl.addWidget(QLabel("📋 Danh sách backup:"))
        self.backup_table = QTableWidget()
        self.backup_table.setColumnCount(3)
        self.backup_table.setHorizontalHeaderLabels(["Tên file", "Kích thước", "Thời gian"])
        self.backup_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.backup_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.backup_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.backup_table.setMaximumHeight(200)
        self.backup_table.verticalHeader().setVisible(False)
        bl.addWidget(self.backup_table)

        restore_btn = QPushButton("🔄 Phục hồi từ backup đã chọn")
        restore_btn.setObjectName("restoreBtn")
        restore_btn.clicked.connect(self._do_restore)
        bl.addWidget(restore_btn)

        open_dir_btn = QPushButton("📂 Mở thư mục backup")
        open_dir_btn.setObjectName("actionBtn")
        open_dir_btn.clicked.connect(self._open_backup_dir)
        bl.addWidget(open_dir_btn)

        row.addWidget(backup_group, 2)

        # ── RIGHT: System info + User management ─────────────────
        right_col = QVBoxLayout()
        right_col.setSpacing(16)

        # System info
        info_group = QGroupBox("ℹ️ Thông tin hệ thống")
        info_group.setObjectName("groupBox")
        il = QFormLayout(info_group)
        il.setSpacing(8)

        stats = dao.get_dashboard_stats()
        info_fields = [
            ("Tổng bệnh nhân:",   str(stats["total_patients"])),
            ("Tổng nhân viên:",   str(stats["total_staff"])),
            ("Database size:",    self._get_db_size()),
            ("Python:",           self._get_python_version()),
            ("PyQt6:",            self._get_pyqt_version()),
        ]
        for label, value in info_fields:
            lbl = QLabel(label); lbl.setObjectName("fieldLabel")
            val = QLabel(value); val.setObjectName("fieldValue")
            il.addRow(lbl, val)

        right_col.addWidget(info_group)

        # Change password
        pass_group = QGroupBox("🔐 Đổi mật khẩu")
        pass_group.setObjectName("groupBox")
        pl = QFormLayout(pass_group)
        pl.setSpacing(8)
        self.old_pass = QLineEdit(); self.old_pass.setEchoMode(QLineEdit.EchoMode.Password)
        self.old_pass.setPlaceholderText("Mật khẩu hiện tại")
        self.new_pass = QLineEdit(); self.new_pass.setEchoMode(QLineEdit.EchoMode.Password)
        self.new_pass.setPlaceholderText("Mật khẩu mới (tối thiểu 6 ký tự)")
        self.conf_pass = QLineEdit(); self.conf_pass.setEchoMode(QLineEdit.EchoMode.Password)
        self.conf_pass.setPlaceholderText("Xác nhận mật khẩu mới")
        pl.addRow("Mật khẩu cũ:", self.old_pass)
        pl.addRow("Mật khẩu mới:", self.new_pass)
        pl.addRow("Xác nhận:",     self.conf_pass)
        change_btn = QPushButton("🔑 Đổi mật khẩu")
        change_btn.setObjectName("primaryBtn")
        change_btn.clicked.connect(self._change_password)
        pl.addRow("", change_btn)
        right_col.addWidget(pass_group)

        row.addLayout(right_col, 1)
        layout.addLayout(row)

    # ── Backup/Restore ───────────────────────────────────────────
    def _do_backup(self):
        if not os.path.exists(DB_PATH):
            QMessageBox.warning(self, "Lỗi", "Không tìm thấy file database.")
            return
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        dest = os.path.join(BACKUP_DIR, f"hospital_backup_{ts}.db")
        shutil.copy2(DB_PATH, dest)
        self._load_backups()
        QMessageBox.information(self, "✅ Backup thành công",
                                f"File backup đã được tạo:\n{os.path.basename(dest)}")

    def _do_restore(self):
        row = self.backup_table.currentRow()
        if row < 0:
            QMessageBox.information(self, "Chưa chọn", "Vui lòng chọn một file backup.")
            return
        filename = self.backup_table.item(row, 0).text()
        src = os.path.join(BACKUP_DIR, filename)
        if not os.path.exists(src):
            QMessageBox.warning(self, "Không tìm thấy file", f"File {filename} không tồn tại.")
            return
        reply = QMessageBox.warning(
            self, "⚠️ Xác nhận phục hồi",
            f"Bạn có chắc muốn phục hồi database từ:\n<b>{filename}</b>?\n\n"
            "Dữ liệu hiện tại sẽ bị GHI ĐÈ. Thao tác này không thể hoàn tác.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel
        )
        if reply == QMessageBox.StandardButton.Yes:
            # Auto-backup current before restoring
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            auto = os.path.join(BACKUP_DIR, f"hospital_auto_before_restore_{ts}.db")
            if os.path.exists(DB_PATH):
                shutil.copy2(DB_PATH, auto)
            shutil.copy2(src, DB_PATH)
            QMessageBox.information(self, "✅ Phục hồi thành công",
                                    "Database đã được phục hồi.\nVui lòng khởi động lại ứng dụng.")

    def _load_backups(self):
        backups = sorted(glob.glob(os.path.join(BACKUP_DIR, "*.db")), reverse=True)
        self.backup_table.setRowCount(len(backups))
        for r, path in enumerate(backups):
            name = os.path.basename(path)
            size = f"{os.path.getsize(path) / 1024:.1f} KB"
            mtime = datetime.fromtimestamp(os.path.getmtime(path)).strftime("%d/%m/%Y %H:%M")
            for c, v in enumerate([name, size, mtime]):
                self.backup_table.setItem(r, c, QTableWidgetItem(v))

    def _open_backup_dir(self):
        import subprocess, sys
        if sys.platform == "win32":
            os.startfile(BACKUP_DIR)
        elif sys.platform == "darwin":
            subprocess.Popen(["open", BACKUP_DIR])
        else:
            subprocess.Popen(["xdg-open", BACKUP_DIR])

    # ── Change password ──────────────────────────────────────────
    def _change_password(self):
        import bcrypt
        user = auth.get_current_user()
        if not user:
            return
        old = self.old_pass.text()
        new = self.new_pass.text()
        conf = self.conf_pass.text()

        row = dao.get_user_by_username(user["username"])
        if not bcrypt.checkpw(old.encode(), row["password"].encode()):
            QMessageBox.warning(self, "Sai mật khẩu", "Mật khẩu hiện tại không đúng.")
            return
        if len(new) < 6:
            QMessageBox.warning(self, "Mật khẩu yếu", "Mật khẩu mới phải có ít nhất 6 ký tự.")
            return
        if new != conf:
            QMessageBox.warning(self, "Không khớp", "Mật khẩu mới và xác nhận không khớp.")
            return

        hashed = bcrypt.hashpw(new.encode(), bcrypt.gensalt()).decode()
        from database.schema import get_connection
        conn = get_connection()
        conn.execute("UPDATE users SET password=? WHERE id=?", (hashed, user["id"]))
        conn.commit()
        conn.close()

        self.old_pass.clear(); self.new_pass.clear(); self.conf_pass.clear()
        QMessageBox.information(self, "✅ Thành công", "Mật khẩu đã được đổi thành công.")

    # ── Helper ───────────────────────────────────────────────────
    def _get_db_size(self):
        if os.path.exists(DB_PATH):
            return f"{os.path.getsize(DB_PATH) / 1024:.1f} KB"
        return "N/A"

    def _get_python_version(self):
        import sys
        return f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"

    def _get_pyqt_version(self):
        try:
            from PyQt6.QtCore import PYQT_VERSION_STR
            return PYQT_VERSION_STR
        except Exception:
            return "N/A"

    def _apply_style(self):
        self.setStyleSheet("""
        QWidget { background: #f7fafc; font-family: 'Segoe UI'; }
        #sectionTitle { color: #1a365d; }
        #groupBox {
            border: 1px solid #e2e8f0; border-radius: 10px;
            background: white; font-weight: 600; font-size: 12px;
            padding: 8px;
        }
        #groupBox::title { subcontrol-origin: margin; left: 12px; padding: 0 6px; color: #2d3748; }
        #infoLbl { color: #4a5568; font-size: 12px; background: #f7fafc; border-radius:6px; padding:8px; }
        #fieldLabel { font-weight: 600; color: #4a5568; font-size: 12px; }
        #fieldValue { color: #2d3748; font-size: 12px; }
        QLineEdit {
            border: 1.5px solid #cbd5e0; border-radius: 6px;
            padding: 7px 10px; font-size: 12px; background: white;
        }
        #backupBtn {
            background: #2b6cb0; color: white; border: none;
            border-radius: 7px; padding: 9px; font-weight: 600;
        }
        #backupBtn:hover { background: #2c5282; }
        #restoreBtn {
            background: #744210; color: white; border: none;
            border-radius: 7px; padding: 9px; font-weight: 600;
        }
        #restoreBtn:hover { background: #5c3209; }
        #primaryBtn {
            background: #276749; color: white; border: none;
            border-radius: 7px; padding: 8px 16px; font-weight: 600;
        }
        #primaryBtn:hover { background: #22543d; }
        #actionBtn {
            background: #edf2f7; color: #2d3748; border: none;
            border-radius: 6px; padding: 7px 14px; font-size: 12px;
        }
        QTableWidget { border: 1px solid #e2e8f0; font-size: 12px; }
        QHeaderView::section { background: #edf2f7; font-weight: 600; padding: 6px; border: none; }
        """)
