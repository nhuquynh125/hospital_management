import sys
import os

# Add project root to path so all modules resolve correctly
sys.path.insert(0, os.path.dirname(__file__))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QFont, QIcon
from database.schema import init_db
from ui.login_window import LoginWindow
from ui.main_window  import MainWindow


def main():
    # 1. Bootstrap database
    init_db()

    # 2. Launch Qt app
    app = QApplication(sys.argv)
    app.setApplicationName("Hospital Management System")
    
    # Enable High DPI scaling for icons and UI (optional but recommended)
    
    # Set application font and global icon
    app.setFont(QFont("Segoe UI", 10))
    logo_path = os.path.join(os.path.dirname(__file__), 'assets', 'logo.png')
    app.setWindowIcon(QIcon(logo_path))
    
    # For Windows taskbar icon if needed
    if os.name == 'nt':
        import ctypes
        myappid = 'hospital.management.system.1.0'
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)

    # 3. Show login
    login_win = LoginWindow()

    def on_login_success(user: dict):
        # ── First-login enforcement ──────────────────────────────────
        if user.get("must_change_password", 0):
            dlg = ForcePasswordDialog(user, parent=None)
            def _after_change():
                window = MainWindow(user)
                window.show()
            dlg.password_changed.connect(_after_change)
            dlg.exec()   # blocks until password is changed (cannot be dismissed)
        else:
            window = MainWindow(user)
            window.show()

    login_win.login_success.connect(on_login_success)
    login_win.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
