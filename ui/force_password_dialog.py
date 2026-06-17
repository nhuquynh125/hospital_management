"""
ui/force_password_dialog.py
────────────────────────────────────────────────────────────────────────
Mandatory first-login password change dialog.

Behaviour:
  • Modal – cannot be dismissed (no X, no Escape).
  • Shown BEFORE MainWindow is created.
  • On success: clears must_change_password flag in DB, then emits `accepted`.
"""
import bcrypt
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton,
    QHBoxLayout, QFrame, QProgressBar, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

import core.auth as auth
import database.dao as dao


class ForcePasswordDialog(QDialog):
    """Non-dismissible dialog that forces the user to set a new password."""

    password_changed = pyqtSignal()   # emitted after DB update succeeds

    def __init__(self, user: dict, parent=None):
        super().__init__(parent)
        self._user = user

        # ── Window flags: remove ? and X buttons ───────────────────
        self.setWindowFlags(
            Qt.WindowType.Dialog
            | Qt.WindowType.CustomizeWindowHint
            | Qt.WindowType.WindowTitleHint          # keep title bar
            # no Close | no ContextHelp
        )
        self.setWindowTitle("Đổi mật khẩu bắt buộc — Hospital Management")
        self.setFixedWidth(420)
        self.setModal(True)

        self._build_ui()
        self._apply_style()

    # ── reject() guard – blocks Escape & system close ────────────────
    def reject(self):
        """Prevent dialog from being closed without changing password."""
        pass

    def closeEvent(self, event):
        event.ignore()   # block window X button (if ever shown)

    # ─────────────────────────────────────────────────────────────────
    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(32, 28, 32, 28)
        root.setSpacing(16)

        # ── Header ────────────────────────────────────────────────────
        icon_lbl = QLabel("🔐")
        icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_lbl.setFont(QFont("Segoe UI", 36))
        root.addWidget(icon_lbl)

        title = QLabel("Đổi mật khẩu bắt buộc")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setFont(QFont("Segoe UI", 15, QFont.Weight.Bold))
        title.setObjectName("dlgTitle")
        root.addWidget(title)

        desc = QLabel(
            f"Chào mừng <b>{self._user.get('full_name', '')}</b>!<br>"
            "Đây là lần đăng nhập đầu tiên của bạn.<br>"
            "Vui lòng đặt mật khẩu cá nhân trước khi tiếp tục."
        )
        desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc.setWordWrap(True)
        desc.setObjectName("dlgDesc")
        root.addWidget(desc)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setObjectName("dlgSep")
        root.addWidget(sep)

        # ── Form ──────────────────────────────────────────────────────
        def _make_field(placeholder, label_text):
            lbl = QLabel(label_text)
            lbl.setObjectName("fieldLbl")
            inp = QLineEdit()
            inp.setEchoMode(QLineEdit.EchoMode.Password)
            inp.setPlaceholderText(placeholder)
            inp.setObjectName("authInput")

            # Show/hide toggle
            toggle = QPushButton("👁")
            toggle.setFixedSize(28, 28)
            toggle.setObjectName("toggleBtn")
            toggle.setCursor(Qt.CursorShape.PointingHandCursor)

            def _toggle():
                if inp.echoMode() == QLineEdit.EchoMode.Password:
                    inp.setEchoMode(QLineEdit.EchoMode.Normal)
                    toggle.setText("🙈")
                else:
                    inp.setEchoMode(QLineEdit.EchoMode.Password)
                    toggle.setText("👁")
            toggle.clicked.connect(_toggle)

            row = QHBoxLayout()
            row.addWidget(inp)
            row.addWidget(toggle)
            return lbl, inp, row

        new_lbl,  self._new_pass,  new_row  = _make_field("Tối thiểu 8 ký tự", "Mật khẩu mới")
        conf_lbl, self._conf_pass, conf_row = _make_field("Nhập lại mật khẩu mới", "Xác nhận mật khẩu")

        root.addWidget(new_lbl)
        root.addLayout(new_row)

        # Strength meter
        self._strength_bar = QProgressBar()
        self._strength_bar.setRange(0, 4)
        self._strength_bar.setValue(0)
        self._strength_bar.setTextVisible(False)
        self._strength_bar.setFixedHeight(6)
        self._strength_bar.setObjectName("strengthBar")
        root.addWidget(self._strength_bar)

        self._strength_lbl = QLabel("")
        self._strength_lbl.setObjectName("strengthLbl")
        root.addWidget(self._strength_lbl)

        root.addWidget(conf_lbl)
        root.addLayout(conf_row)

        # ── Confirm button ────────────────────────────────────────────
        self._confirm_btn = QPushButton("✅  Đặt mật khẩu & Tiếp tục")
        self._confirm_btn.setObjectName("confirmBtn")
        self._confirm_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._confirm_btn.setEnabled(False)
        self._confirm_btn.clicked.connect(self._on_confirm)
        root.addWidget(self._confirm_btn)

        # ── Wire up live validation ───────────────────────────────────
        self._new_pass.textChanged.connect(self._validate)
        self._conf_pass.textChanged.connect(self._validate)
        self._new_pass.returnPressed.connect(self._conf_pass.setFocus)
        self._conf_pass.returnPressed.connect(self._on_confirm)

    # ─────────────────────────────────────────────────────────────────
    def _password_strength(self, pwd: str) -> int:
        """Return 0–4 strength score."""
        score = 0
        if len(pwd) >= 8:   score += 1
        if len(pwd) >= 12:  score += 1
        if any(c.isdigit() for c in pwd):   score += 1
        if any(c in "!@#$%^&*()_+-=[]{}|;':\",./<>?" for c in pwd): score += 1
        return score

    def _validate(self):
        pwd  = self._new_pass.text()
        conf = self._conf_pass.text()

        # Update strength
        score = self._password_strength(pwd)
        self._strength_bar.setValue(score)
        labels = ["", "⚠️ Yếu", "🟡 Trung bình", "🟢 Tốt", "💪 Rất mạnh"]
        colors = ["", "#e53e3e", "#d69e2e", "#38a169", "#2b6cb0"]
        self._strength_lbl.setText(labels[score] if pwd else "")
        if score:
            self._strength_bar.setStyleSheet(
                f"QProgressBar::chunk {{ background: {colors[score]}; border-radius: 3px; }}"
            )

        ok = len(pwd) >= 8 and pwd == conf
        self._confirm_btn.setEnabled(ok)
        self._confirm_btn.setToolTip(
            "" if ok else "Mật khẩu phải có ít nhất 8 ký tự và khớp với xác nhận."
        )

    def _on_confirm(self):
        if not self._confirm_btn.isEnabled():
            return

        new_pwd  = self._new_pass.text()
        new_hash = bcrypt.hashpw(new_pwd.encode(), bcrypt.gensalt()).decode()

        try:
            dao.update_user_password(self._user["id"], new_hash, clear_force_change=True)
            dao.log_action(
                self._user["id"],
                "FIRST_LOGIN_PASSWORD_CHANGE",
                detail=f"User '{self._user['username']}' completed mandatory password change"
            )
            # Update the in-memory user dict so MainWindow sees correct state
            self._user["must_change_password"] = 0
            auth.get_current_user()["must_change_password"] = 0
        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"Không thể cập nhật mật khẩu:\n{e}")
            return

        self.password_changed.emit()
        super().accept()   # bypass our overridden reject(); directly accept

    # ─────────────────────────────────────────────────────────────────
    def _apply_style(self):
        self.setStyleSheet("""
        QDialog { background: #f7fafc; }
        QLabel  { background: transparent; }
        #dlgTitle { color: #1a365d; margin-top: 4px; }
        #dlgDesc  { color: #4a5568; font-size: 13px; line-height: 1.5; }
        #dlgSep   { color: #e2e8f0; }
        #fieldLbl { font-size: 12px; font-weight: 600; color: #2d3748; margin-top: 4px; }
        #authInput {
            border: 1.5px solid #cbd5e0;
            border-radius: 8px;
            padding: 10px 12px;
            font-size: 13px;
            background: white;
        }
        #authInput:focus { border-color: #4299e1; background: white; }
        #toggleBtn {
            border: none; background: transparent;
            font-size: 14px; border-radius: 4px;
        }
        #toggleBtn:hover { background: #edf2f7; }
        #strengthBar {
            border: none; border-radius: 3px;
            background: #e2e8f0;
        }
        #strengthBar::chunk { border-radius: 3px; }
        #strengthLbl { font-size: 11px; color: #718096; }
        #confirmBtn {
            background: #276749; color: white;
            border: none; border-radius: 8px;
            padding: 12px; font-size: 14px; font-weight: 600;
            margin-top: 6px;
        }
        #confirmBtn:hover   { background: #22543d; }
        #confirmBtn:pressed { background: #1c4532; }
        #confirmBtn:disabled {
            background: #a0aec0; color: #e2e8f0;
        }
        """)