"""
Hospital Management System — Main Window
8 vai trò: admin, doctor, nurse, receptionist, pharmacist, accountant, lab_technician, director
"""

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QLabel, QPushButton, QFrame, QStackedWidget, QMessageBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

import core.auth as auth
from ui.patient_tab       import PatientTab
from ui.staff_tab         import StaffTab
from ui.appointment_tab   import AppointmentTab
from ui.room_tab          import RoomTab
from ui.medicine_tab      import MedicineTab
from ui.nursing_tab       import NursingTab
from ui.lab_tab           import LabTab
from ui.billing_tab       import BillingTab
from ui.export_tab        import ExportTab
from ui.stats_tab         import StatsTab
from ui.ai_prediction_tab import AIPredictionTab
from ui.chatbot_tab       import ChatbotTab
from ui.settings_tab      import SettingsTab


class SidebarBtn(QPushButton):
    def __init__(self, icon, text, parent=None):
        super().__init__(f"  {icon}  {text}", parent)
        self.setCheckable(True)
        self.setFixedHeight(42)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFont(QFont("Segoe UI", 11))
        self.setObjectName("sidebarBtn")


class MainWindow(QMainWindow):
    def __init__(self, user: dict):
        super().__init__()
        self.user = user
        self.setWindowTitle("Hospital Management System")
        self.setMinimumSize(1150, 700)
        self._tab_widgets = {}
        self._nav_buttons = []
        self._btn_group = []
        self._factories = []  # NEW
        self._build_ui()
        self._apply_style()
        if self._nav_buttons:
            self._nav_buttons[0].setChecked(True)
            self._load_tab(0, self._factories[0]())  # CHANGED: was self._make_dashboard()
    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QHBoxLayout(central)
        root.setContentsMargins(0,0,0,0); root.setSpacing(0)

        # ── Sidebar ──────────────────────────────────────────────
        sidebar = QFrame(); sidebar.setObjectName("sidebar"); sidebar.setFixedWidth(225)
        sb = QVBoxLayout(sidebar); sb.setContentsMargins(10,14,10,14); sb.setSpacing(3)

        logo = QLabel("🏥"); logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo.setFont(QFont("Segoe UI", 28)); sb.addWidget(logo)

        app_lbl = QLabel("Hospital\nManagement")
        app_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter); app_lbl.setObjectName("sidebarAppName")
        app_lbl.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold)); sb.addWidget(app_lbl)

        sep = QFrame(); sep.setFrameShape(QFrame.Shape.HLine); sep.setObjectName("sidebarSep")
        sb.addWidget(sep); sb.addSpacing(6)

        # ── Role label badge ──────────────────────────────────────
        role_key   = self.user["role"]
        role_label = auth.get_role_label(role_key)
        role_badge = QLabel(f"● {role_label}")
        role_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        role_badge.setObjectName("roleBadge")
        sb.addWidget(role_badge)
        sb.addSpacing(4)

        # ── Navigation items: (icon, label, module, factory) ──────
        # module controls visibility per role
        nav_items = [
            ("📊","Dashboard",          "patients",        self._make_dashboard),
            ("👥","Bệnh nhân",          "patients",        lambda: PatientTab()),
            ("👨‍⚕️","Nhân viên",        "staff",           lambda: StaffTab()),
            ("🗓️","Lịch hẹn",          "appointments",    lambda: AppointmentTab()),
            ("🏠","Phòng / Giường",     "rooms",           lambda: RoomTab()),
            ("🩺","Chăm sóc ĐD",       "medical_records", lambda: NursingTab()),
            ("💊","Thuốc & Kê đơn",    "medicines",       lambda: MedicineTab()),
            ("🔬","Xét nghiệm",        "lab",             lambda: LabTab()),
            ("💰","Viện phí",           "billing",         lambda: BillingTab()),
            ("📊","Thống kê",           "reports",         lambda: StatsTab()),
            ("📤","Xuất báo cáo",       "export",          lambda: ExportTab()),
            ("🔮","AI Dự đoán",        "ai",              lambda: AIPredictionTab()),
            ("💬","Chatbot AI",        "ai",              lambda: ChatbotTab()),
        ]
        if role_key == "admin":
            nav_items.append(("⚙️","Cài đặt / Backup","settings",lambda: SettingsTab()))

        self._stack = QStackedWidget()
        for icon, label, module, factory in nav_items:
            if not auth.can_access(module):
                continue
            btn = SidebarBtn(icon, label)
            btn.clicked.connect(self._make_nav_handler(btn, factory))
            sb.addWidget(btn)
            self._nav_buttons.append(btn)
            self._btn_group.append(btn)
            self._factories.append(factory)  # NEW
            self._stack.addWidget(QWidget())  # placeholder
        sb.addStretch()

        sep2 = QFrame(); sep2.setFrameShape(QFrame.Shape.HLine); sep2.setObjectName("sidebarSep")
        sb.addWidget(sep2)

        user_lbl = QLabel(f"👤 {self.user['full_name']}\n{role_label}")
        user_lbl.setObjectName("userLabel"); user_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        user_lbl.setWordWrap(True); sb.addWidget(user_lbl)

        logout_btn = QPushButton("🚪 Đăng xuất")
        logout_btn.setObjectName("logoutBtn"); logout_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        logout_btn.clicked.connect(self._logout)
        sb.addWidget(logout_btn)

        root.addWidget(sidebar)

        # ── Content ───────────────────────────────────────────────
        content = QFrame(); content.setObjectName("contentArea")
        cl = QVBoxLayout(content); cl.setContentsMargins(0,0,0,0)
        cl.addWidget(self._stack)
        root.addWidget(content, 1)

    # ── Nav handler ──────────────────────────────────────────────
    def _make_nav_handler(self, btn, factory):
        def handler():
            for b in self._btn_group:
                b.setChecked(b is btn)
            idx = self._btn_group.index(btn)
            if idx not in self._tab_widgets:
                widget = factory()
                self._stack.removeWidget(self._stack.widget(idx))
                self._stack.insertWidget(idx, widget)
                self._tab_widgets[idx] = widget
            self._stack.setCurrentIndex(idx)
        return handler

    def _load_tab(self, idx, widget):
        self._stack.removeWidget(self._stack.widget(idx))
        self._stack.insertWidget(idx, widget)
        self._tab_widgets[idx] = widget
        self._stack.setCurrentIndex(idx)

    # ── Dashboard ────────────────────────────────────────────────
    def _make_dashboard(self):
        from database.dao import get_dashboard_stats
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(24,24,24,24); layout.setSpacing(16)

        title = QLabel("📊 Dashboard tổng quan")
        title.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        title.setStyleSheet("color:#1a365d;")
        layout.addWidget(title)

        role_label = auth.get_role_label(self.user["role"])
        greet = QLabel(f"👋 Xin chào, <b>{self.user['full_name']}</b> &nbsp;|&nbsp; Vai trò: <b>{role_label}</b>")
        greet.setStyleSheet("color:#4a5568; font-size:13px;")
        layout.addWidget(greet)

        stats = get_dashboard_stats()
        cards_data = [
            ("👥","Tổng bệnh nhân",    stats["total_patients"],         "#2b6cb0","#ebf8ff"),
            ("👨‍⚕️","Nhân viên",       stats["total_staff"],            "#276749","#f0fff4"),
            ("🗓️","Lịch hẹn hôm nay", stats["today_appointments"],     "#744210","#fffbeb"),
            ("🏠","Phòng trống",       stats["available_rooms"],        "#553c9a","#faf5ff"),
            ("⚠️","Thuốc sắp hết",    stats["low_stock_medicines"],    "#c53030","#fff5f5"),
        ]

        cards_row = QHBoxLayout(); cards_row.setSpacing(12)
        for icon, label, value, color, bg in cards_data:
            card = QFrame()
            card.setStyleSheet(f"""
                QFrame {{ background:{bg}; border-radius:12px; border:1px solid {color}30; }}
            """)
            cl = QVBoxLayout(card); cl.setContentsMargins(16,14,16,14); cl.setSpacing(2)
            il = QLabel(icon); il.setFont(QFont("Segoe UI",22))
            il.setStyleSheet("background:transparent;")
            vl = QLabel(str(value)); vl.setFont(QFont("Segoe UI",26,QFont.Weight.Bold))
            vl.setStyleSheet(f"color:{color}; background:transparent;")
            nl = QLabel(label); nl.setStyleSheet(f"color:{color}; font-size:11px; background:transparent;")
            cl.addWidget(il); cl.addWidget(vl); cl.addWidget(nl)
            cards_row.addWidget(card)
        layout.addLayout(cards_row)

        # Role-specific hint
        hints = {
            "admin":          "Bạn có toàn quyền quản lý hệ thống.",
            "doctor":         "Xem lịch hẹn, hồ sơ bệnh nhân và kê đơn thuốc.",
            "nurse":          "Ghi chú chăm sóc, dấu hiệu sinh tồn, theo dõi bệnh nhân.",
            "receptionist":   "Quản lý lịch hẹn và tiếp nhận bệnh nhân.",
            "pharmacist":     "Duyệt đơn thuốc và quản lý kho dược.",
            "accountant":     "Quản lý viện phí và thanh toán.",
            "lab_technician": "Thực hiện xét nghiệm và nhập kết quả.",
            "director":       "Xem báo cáo tổng hợp và thống kê toàn bệnh viện.",
        }
        hint_txt = hints.get(self.user["role"],"")
        if hint_txt:
            hint = QLabel(f"💡 {hint_txt}")
            hint.setStyleSheet("""
                background:#fffbeb; color:#744210; border:1px solid #f6e05e;
                border-radius:8px; padding:10px 14px; font-size:12px;
            """)
            layout.addWidget(hint)

        layout.addStretch()
        return widget

    # ── Logout ───────────────────────────────────────────────────
    def _logout(self):
        reply = QMessageBox.question(self, "Đăng xuất",
                                     "Bạn có chắc muốn đăng xuất?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            auth.logout()
            self.close()
            from ui.login_window import LoginWindow
            self._login_win = LoginWindow()
            self._login_win.login_success.connect(lambda u: MainWindow(u).show())
            self._login_win.show()

    # ── Style ────────────────────────────────────────────────────
    def _apply_style(self):
        self.setStyleSheet("""
        QMainWindow { background:#f7fafc; }
        #sidebar { background:#1a365d; }
        #sidebarAppName { color:#bee3f8; margin:4px 0; }
        #sidebarSep { color:#2c5282; background:#2c5282; }
        #roleBadge {
            color:#fefcbf; background:#2c5282; border-radius:10px;
            font-size:10px; font-weight:600; padding:3px 8px; margin:2px 8px;
        }
        #userLabel { color:#bee3f8; font-size:11px; margin:4px 0; }
        #sidebarBtn {
            background:transparent; color:#bee3f8;
            border:none; border-radius:8px; text-align:left; padding-left:8px;
        }
        #sidebarBtn:hover   { background:#2c5282; color:white; }
        #sidebarBtn:checked { background:#2b6cb0; color:white; font-weight:600; }
        #logoutBtn {
            background:transparent; color:#fc8181;
            border:1px solid #fc818140; border-radius:7px;
            padding:7px; font-size:12px; margin-top:4px;
        }
        #logoutBtn:hover { background:#742a2a20; }
        #contentArea { background:#f7fafc; }
        """)
