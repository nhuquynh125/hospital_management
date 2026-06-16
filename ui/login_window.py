"""
Hospital Management System — Login Window
Card đăng nhập luôn nằm giữa, width cố định 400px, window tùy chỉnh kích thước
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QMessageBox, QFrame, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
import core.auth as auth
from ui.register_dialog import RegisterDialog


class LoginWindow(QWidget):
    login_success = pyqtSignal(dict)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Đăng nhập — Hospital Management System")
        self.resize(860, 600)
        self.setMinimumSize(500, 460)
        self._build_ui()
        self._apply_style()

    def _build_ui(self):
        # Root: full background, centers everything
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Vertical center
        root.addStretch(1)

        # Horizontal center row
        h_row = QHBoxLayout()
        h_row.setContentsMargins(0, 0, 0, 0)
        h_row.addStretch(1)

        # ── Card container (fixed width 400px) ────────────────────
        container = QWidget()
        container.setFixedWidth(400)
        container.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Preferred)
        container.setObjectName("container")

        cl = QVBoxLayout(container)
        cl.setContentsMargins(0, 0, 0, 0)
        cl.setSpacing(0)

        # Logo
        logo = QLabel("🏥")
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo.setFont(QFont("Segoe UI", 42))
        cl.addWidget(logo)

        app_name = QLabel("Hospital Management")
        app_name.setAlignment(Qt.AlignmentFlag.AlignCenter)
        app_name.setFont(QFont("Segoe UI", 17, QFont.Weight.Bold))
        app_name.setObjectName("appName")
        cl.addWidget(app_name)

        sub = QLabel("Hệ thống quản lý bệnh viện")
        sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sub.setObjectName("subTitle")
        cl.addSpacing(4)
        cl.addWidget(sub)
        cl.addSpacing(28)

        # Card
        card = QFrame()
        card.setObjectName("loginCard")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(28, 28, 28, 28)
        card_layout.setSpacing(14)

        user_lbl = QLabel("Tên đăng nhập")
        user_lbl.setObjectName("fieldLabel")
        card_layout.addWidget(user_lbl)

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("admin / bacsi01 / letan01 ...")
        self.username_input.setObjectName("authInput")
        self.username_input.returnPressed.connect(self._on_login)
        card_layout.addWidget(self.username_input)

        pass_lbl = QLabel("Mật khẩu")
        pass_lbl.setObjectName("fieldLabel")
        card_layout.addWidget(pass_lbl)

        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setPlaceholderText("Nhập mật khẩu")
        self.password_input.setObjectName("authInput")
        self.password_input.returnPressed.connect(self._on_login)
        card_layout.addWidget(self.password_input)

        self.toggle_pwd_btn = QPushButton("👁")
        self.toggle_pwd_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.toggle_pwd_btn.setFixedSize(24, 24)
        self.toggle_pwd_btn.setToolTip("Hiện mật khẩu")
        self.toggle_pwd_btn.setStyleSheet("QPushButton { border: none; background: transparent; font-size: 14px; }")
        self.toggle_pwd_btn.clicked.connect(self._toggle_password)

        pwd_layout = QHBoxLayout(self.password_input)
        pwd_layout.setContentsMargins(0, 0, 8, 0)
        pwd_layout.addWidget(self.toggle_pwd_btn, alignment=Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        card_layout.addSpacing(6)

        self.login_btn = QPushButton("Đăng nhập")
        self.login_btn.setObjectName("loginBtn")
        self.login_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.login_btn.clicked.connect(self._on_login)
        card_layout.addWidget(self.login_btn)

        card_layout.addSpacing(8)
        
        register_lbl = QLabel("Chưa có tài khoản?")
        register_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        register_lbl.setObjectName("registerLabel")
        card_layout.addWidget(register_lbl)
        
        self.register_btn = QPushButton("Đăng ký")
        self.register_btn.setObjectName("registerBtn")
        self.register_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.register_btn.clicked.connect(self._on_register)
        card_layout.addWidget(self.register_btn)

        cl.addWidget(card)
        cl.addSpacing(16)

        footer = QLabel("Hospital Management System by Doan Thi Nhu Quynh 25AI043")
        footer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        footer.setObjectName("footer")
        cl.addWidget(footer)

        hint = QLabel("Demo: admin / admin123")
        hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hint.setObjectName("hint")
        cl.addWidget(hint)

        h_row.addWidget(container)
        h_row.addStretch(1)

        root.addLayout(h_row)
        root.addStretch(1)

    def _on_login(self):
        username = self.username_input.text().strip()
        password = self.password_input.text()
        if not username or not password:
            QMessageBox.warning(self, "Thiếu thông tin",
                                "Vui lòng nhập tên đăng nhập và mật khẩu.")
            return
        self.login_btn.setEnabled(False)
        self.login_btn.setText("Đang xác thực…")
        user = auth.login(username, password)
        self.login_btn.setEnabled(True)
        self.login_btn.setText("Đăng nhập")
        if user:
            self.login_success.emit(user)
            self.close()
        else:
            QMessageBox.critical(self, "Sai thông tin",
                                 "Tên đăng nhập hoặc mật khẩu không đúng.\nVui lòng thử lại.")
            self.password_input.clear()
            self.password_input.setFocus()

    def _on_register(self):
        dialog = RegisterDialog(self)
        if dialog.exec():
            # If user successfully registers, you might want to automatically
            # fill the username, but for now we just close the dialog.
            pass

    def _toggle_password(self):
        if self.password_input.echoMode() == QLineEdit.EchoMode.Password:
            self.password_input.setEchoMode(QLineEdit.EchoMode.Normal)
            self.toggle_pwd_btn.setText("🙈")
            self.toggle_pwd_btn.setToolTip("Ẩn mật khẩu")
        else:
            self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
            self.toggle_pwd_btn.setText("👁")
            self.toggle_pwd_btn.setToolTip("Hiện mật khẩu")

    def _apply_style(self):
        self.setStyleSheet("""
        QWidget {
            background-color: #f0f4f8;
            font-family: 'Segoe UI', Arial;
        }
        QLabel { background: transparent; }
        #container { background: transparent; }
        #appName   { color: #1a365d; margin-top: 4px; }
        #subTitle  { color: #718096; font-size: 12px; }
        #loginCard {
            background: white;
            border-radius: 14px;
            border: 1px solid #e2e8f0;
        }
        #fieldLabel {
            font-size: 13px; font-weight: 600;
            color: #2d3748; margin-bottom: 2px;
        }
        #authInput {
            border: 1.5px solid #cbd5e0;
            border-radius: 8px;
            padding: 10px 36px 10px 12px;
            font-size: 13px;
            background: #f7fafc;
        }
        #authInput:focus { border-color: #4299e1; background: white; }
        #loginBtn {
            background: #2b6cb0; color: white; border: none;
            border-radius: 8px; padding: 11px;
            font-size: 14px; font-weight: 600;
        }
        #loginBtn:hover   { background: #2c5282; }
        #loginBtn:pressed { background: #1a365d; }
        #loginBtn:disabled{ background: #a0aec0; }
        #registerLabel {
            font-size: 13px; color: #718096; margin-top: 4px;
        }
        #registerBtn {
            background: white; color: #2b6cb0; border: 1.5px solid #2b6cb0;
            border-radius: 8px; padding: 11px; font-size: 14px; font-weight: 600;
        }
        #registerBtn:hover   { background: #ebf8ff; }
        #registerBtn:pressed { background: #bee3f8; }
        #footer { color: #a0aec0; font-size: 11px; margin-top: 4px; }
        #hint   { color: #718096; font-size: 11px; }
        """)
