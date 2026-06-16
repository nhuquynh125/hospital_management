from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QMessageBox, QComboBox
)
from PyQt6.QtCore import Qt
import bcrypt
from database.schema import get_connection

class RegisterDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Đăng ký tài khoản")
        self.resize(380, 320)
        self._build_ui()
        self.setStyleSheet("""
            QDialog { background-color: #f0f4f8; font-family: 'Segoe UI', Arial; }
            QLabel { font-size: 13px; font-weight: 600; color: #2d3748; margin-bottom: 2px; margin-top: 6px; }
            QLineEdit, QComboBox {
                border: 1.5px solid #cbd5e0;
                border-radius: 8px;
                padding: 8px 12px;
                font-size: 13px;
                background: #f7fafc;
            }
            QLineEdit:focus, QComboBox:focus { border-color: #4299e1; background: white; }
            QPushButton {
                background: #2b6cb0; color: white; border: none;
                border-radius: 8px; padding: 10px;
                font-size: 14px; font-weight: 600;
            }
            QPushButton:hover   { background: #2c5282; }
            QPushButton:pressed { background: #1a365d; }
        """)

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(6)
        
        layout.addWidget(QLabel("Tên đăng nhập:"))
        self.user_input = QLineEdit()
        self.user_input.setPlaceholderText("Nhập tên đăng nhập...")
        layout.addWidget(self.user_input)
        
        layout.addWidget(QLabel("Mật khẩu:"))
        self.pass_input = QLineEdit()
        self.pass_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.pass_input.setPlaceholderText("Nhập mật khẩu...")
        layout.addWidget(self.pass_input)
        
        layout.addWidget(QLabel("Họ và tên:"))
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Nhập họ và tên...")
        layout.addWidget(self.name_input)
        
        layout.addWidget(QLabel("Vai trò:"))
        self.role_combo = QComboBox()
        self.role_combo.addItems([
            "Quản trị viên (admin)", "Bác sĩ (doctor)", "Y tá (nurse)",
            "Lễ tân (receptionist)", "Dược sĩ (pharmacist)", 
            "Kế toán (accountant)", "Xét nghiệm viên (lab_technician)",
            "Giám đốc (director)"
        ])
        layout.addWidget(self.role_combo)
        
        layout.addSpacing(16)
        
        self.reg_btn = QPushButton("Đăng ký")
        self.reg_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.reg_btn.clicked.connect(self._on_register)
        layout.addWidget(self.reg_btn)

    def _on_register(self):
        username = self.user_input.text().strip()
        password = self.pass_input.text()
        full_name = self.name_input.text().strip()
        
        if not username or not password or not full_name:
            QMessageBox.warning(self, "Lỗi", "Vui lòng điền đầy đủ thông tin.")
            return
            
        role_map = {
            0: 'admin', 1: 'doctor', 2: 'nurse', 3: 'receptionist',
            4: 'pharmacist', 5: 'accountant', 6: 'lab_technician', 7: 'director'
        }
        role = role_map.get(self.role_combo.currentIndex(), 'receptionist')
        
        try:
            conn = get_connection()
            exists = conn.execute("SELECT id FROM users WHERE username=?", (username,)).fetchone()
            if exists:
                QMessageBox.warning(self, "Lỗi", "Tên đăng nhập đã tồn tại.")
                conn.close()
                return
                
            hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
            conn.execute(
                "INSERT INTO users (username, password, full_name, role) VALUES (?,?,?,?)",
                (username, hashed, full_name, role)
            )
            conn.commit()
            conn.close()
            QMessageBox.information(self, "Thành công", "Đăng ký thành công! Bạn có thể đăng nhập ngay.")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"Có lỗi xảy ra: {e}")
