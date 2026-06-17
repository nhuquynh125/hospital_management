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
from ui.drug_interaction_tab import DrugInteractionTab
from ui.executive_report_tab import ExecutiveReportTab
from ui.fraud_detection_tab import FraudDetectionTab
from ui.predictive_analytics_tab import PredictiveAnalyticsTab
from ui.chatbot_tab       import ChatbotTab
from ui.settings_tab      import SettingsTab
from ui.audit_log_tab     import AuditLogTab
from ui.shift_schedule_tab import ShiftScheduleTab


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
            ("👥","Bệnh nhân",          "patients",        lambda: PatientTab()),
            ("👨‍⚕️","Nhân viên",        "staff",           lambda: StaffTab()),
            ("🗓️","Lịch hẹn",          "appointments",    lambda: AppointmentTab()),
            ("🏠","Phòng / Giường",     "rooms",           lambda: RoomTab()),
            ("🩺","Chăm sóc ĐD",       "medical_records", lambda: NursingTab()),
            ("💊","Thuốc & Kê đơn",    "medicines",       lambda: MedicineTab()),
            ("🔬","Xét nghiệm",        "lab",             lambda: LabTab()),
            ("💰","Viện phí",           "billing",         lambda: BillingTab()),
            ("📊","Thống kê",           "reports",         lambda: StatsTab(role=role_key)),
            ("📋","Báo cáo Điều hành",  "reports",         lambda: ExecutiveReportTab()),
            ("🔮","Dự báo Lượng bệnh",  "reports",         lambda: PredictiveAnalyticsTab()),
            ("📤","Xuất báo cáo",       "export",          lambda: ExportTab()),
            ("💬","Chatbot AI",        "ai",              lambda: ChatbotTab()),
            ("💊","Canh bao Tuong tac",  "drug_interaction", lambda: DrugInteractionTab()),
            ("🛡️","Audit Trail",       "audit_logs",      lambda: AuditLogTab()),
        ]

        excluded_shifts_roles = ("admin", "director", "accountant", "department_head", "hr_manager")
        if role_key not in excluded_shifts_roles:
            nav_items.insert(2, ("📅", "Lịch trực", None, lambda: ShiftScheduleTab()))

        if role_key == "doctor":
            lich_hen_idx = next((i for i, item in enumerate(nav_items) if item[1] == "Lịch hẹn"), -1)
            if lich_hen_idx != -1:
                lich_hen_item = nav_items.pop(lich_hen_idx)
                nav_items.insert(0, lich_hen_item)

        if role_key in ("admin", "director"):
            nav_items.append(("⚙️","Cài đặt / Backup","settings",lambda: SettingsTab()))

        if role_key != "director":
            nav_items = [item for item in nav_items if item[1] not in ("Báo cáo Điều hành", "Dự báo Lượng bệnh")]

        self._stack = QStackedWidget()
        for icon, label, module, factory in nav_items:
            if module is not None and not auth.can_access(module):
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

            # Keep a module-level reference so the GC never reclaims the new
            # MainWindow before it is fully visible (classic PyQt GC crash).
            import ui.main_window as _mw_module

            def _on_login_success(user):
                win = MainWindow(user)
                _mw_module._active_main_window = win   # persistent ref
                win.show()

            self._login_win.login_success.connect(_on_login_success)
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


