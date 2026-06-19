import os, shutil, glob, secrets, string
from datetime import datetime

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QMessageBox, QTableWidget, QTabWidget,
    QTableWidgetItem, QHeaderView, QAbstractItemView, QLineEdit, QGroupBox,
    QFormLayout, QComboBox, QScrollArea
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from database.schema import DB_PATH
import database.dao as dao
import core.auth as auth

BACKUP_DIR = os.path.join(os.path.dirname(os.path.dirname(DB_PATH)), "backups")
SUPPORT_STAFF_ROLES = {"security_guard", "ambulance_driver", "janitor"}

def _can(permission):
    return auth.can_access(permission)


class SettingsTab(QWidget):
    def __init__(self):
        super().__init__()
        os.makedirs(BACKUP_DIR, exist_ok=True)
        self._build_ui()
        self._apply_style()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        user = auth.get_current_user()
        role = user.get("role", "") if user else ""

        header = QFrame()
        header.setObjectName("settingsHeader")
        hl = QHBoxLayout(header)
        hl.setContentsMargins(24, 14, 24, 10)
        t = QLabel("\u2699\ufe0f  C\xe0i \u0111\u1eb7t t\xe0i kho\u1ea3n")
        t.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        t.setObjectName("sectionTitle")
        hl.addWidget(t)
        hl.addStretch()
        if user:
            badge = QLabel(f"\U0001f464 {user.get('full_name','')}  \u2022  {auth.get_role_label(role)}")
            badge.setObjectName("userBadge")
            hl.addWidget(badge)
        root.addWidget(header)

        tabs = QTabWidget()
        tabs.setObjectName("settingsTabs")
        tabs.setDocumentMode(True)
        root.addWidget(tabs)

        if _can("settings.personal_info"):
            is_support = role in SUPPORT_STAFF_ROLES
            tabs.addTab(_PersonalInfoWidget(read_only_mode=is_support), "\U0001f464  Th\xf4ng tin c\xe1 nh\xe2n")

        if _can("settings.leave"):
            tabs.addTab(_LeaveManagementWidget(), "\U0001f3d6\ufe0f  Ngh\u1ec9 ph\xe9p")

        if _can("settings.salary_config"):
            tabs.addTab(_SalaryConfigWidget(), "\U0001f4b0  L\u01b0\u01a1ng & Th\u01b0\u1edfng")
        elif _can("settings.salary_view"):
            tabs.addTab(_PayslipViewerWidget(), "\U0001f9fe  Phi\u1ebfu l\u01b0\u01a1ng")

        # Mọi tài khoản đều có quyền đổi mật khẩu
        tabs.addTab(_SecurityWidget(), "\U0001f512  B\u1ea3o m\u1eadt")

        if role == "admin" or _can("settings"):
            tabs.addTab(_BackupWidget(), "\U0001f4be  Sao l\u01b0u / Ph\u1ee5c h\u1ed3i")
            tabs.addTab(_AccountCreationWidget(), "\U0001f465  T\u1ea1o t\xe0i kho\u1ea3n")
            tabs.addTab(_SystemInfoWidget(), "\u2139\ufe0f  H\u1ec7 th\u1ed1ng")

    def _apply_style(self):
        self.setStyleSheet("""
        QWidget          { background: #f7fafc; font-family: 'Segoe UI'; }
        #settingsHeader  { background: white; border-bottom: 1px solid #e2e8f0; }
        #sectionTitle    { color: #1a365d; }
        #userBadge       { color: #4a5568; font-size: 12px; background: #edf2f7;
                           border-radius: 6px; padding: 4px 10px; }
        QTabWidget::pane { border: none; background: #f7fafc; }
        QTabBar::tab     { background: #edf2f7; color: #4a5568; padding: 9px 18px;
                           border-bottom: 2px solid transparent;
                           font-size: 12px; font-weight: 600; }
        QTabBar::tab:selected { background: #f7fafc; color: #1a365d;
                                border-bottom: 2px solid #2b6cb0; }
        QTabBar::tab:hover    { background: #e2e8f0; }
        #groupBox { border: 1px solid #e2e8f0; border-radius: 10px;
                    background: white; font-weight: 600; font-size: 12px; padding: 8px; }
        #groupBox::title { subcontrol-origin: margin; left: 12px;
                           padding: 0 6px; color: #2d3748; }
        #infoLbl  { color: #4a5568; font-size: 12px; background: #f7fafc;
                    border-radius: 6px; padding: 8px; }
        #roValue  { color: #2d3748; font-size: 12px; font-weight: 600; }
        #fieldLabel { font-weight: 600; color: #4a5568; font-size: 12px; }
        #authInput  { border: 1.5px solid #cbd5e0; border-radius: 6px;
                      padding: 8px 10px; font-size: 12px; background: white; }
        #authInput:focus { border-color: #4299e1; }
        #readOnlyInput   { background: #f7fafc; color: #718096; }
        #primaryBtn  { background: #276749; color: white; border: none;
                       border-radius: 7px; padding: 9px 18px;
                       font-weight: 600; font-size: 12px; }
        #primaryBtn:hover   { background: #22543d; }
        #primaryBtn:pressed { background: #1c4532; }
        #backupBtn  { background: #2b6cb0; color: white; border: none;
                      border-radius: 7px; padding: 9px; font-weight: 600; }
        #backupBtn:hover { background: #2c5282; }
        #restoreBtn { background: #744210; color: white; border: none;
                      border-radius: 7px; padding: 9px; font-weight: 600; }
        #restoreBtn:hover { background: #5c3209; }
        #actionBtn  { background: #edf2f7; color: #2d3748; border: 1px solid #e2e8f0;
                      border-radius: 6px; padding: 7px 12px; font-size: 12px; }
        #actionBtn:hover { background: #e2e8f0; }
        QTableWidget { border: 1px solid #e2e8f0; font-size: 12px; }
        QHeaderView::section { background: #edf2f7; font-weight: 600;
                               padding: 6px; border: none; }
        QScrollArea { border: none; }
        #payslipCard { background: white; border-radius: 12px;
                       border: 1.5px solid #e2e8f0; }
        #payslipMonth { color: #1a365d; }
        #psLabel  { color: #4a5568; font-size: 13px; }
        #psValue  { color: #2d3748; font-size: 13px; font-weight: 600; }
        #psValueHighlight { color: #276749; font-size: 15px; font-weight: 700; }
        #payslipNote { color: #718096; font-size: 11px; }
        """)


class _scroll(QScrollArea):
    def __init__(self):
        super().__init__()
        self.setWidgetResizable(True)
        self.setFrameShape(QFrame.Shape.NoFrame)
        inner = QWidget()
        self.setWidget(inner)
        self.lay = QVBoxLayout(inner)
        self.lay.setContentsMargins(24, 20, 24, 20)
        self.lay.setSpacing(16)


class _PersonalInfoWidget(_scroll):
    def __init__(self, read_only_mode=False):
        super().__init__()
        self._ro = read_only_mode
        user  = auth.get_current_user() or {}
        staff_row = dao.get_staff_profile(user.get("id"))
        staff = dict(staff_row) if staff_row else {}
        self._staff = staff; self._user = user

        title = QLabel("\U0001f464  Th\xf4ng tin c\xe1 nh\xe2n")
        title.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        title.setObjectName("sectionTitle")
        self.lay.addWidget(title)

        grp = QGroupBox(); grp.setObjectName("groupBox")
        form = QFormLayout(grp); form.setSpacing(10)

        def _f(val, editable=True):
            w = QLineEdit(str(val) if val else "")
            w.setObjectName("readOnlyInput" if not editable else "authInput")
            if not editable: w.setReadOnly(True)
            return w

        self._full_name = _f(staff.get("full_name") or user.get("full_name"), not read_only_mode)
        self._phone     = _f(staff.get("phone"), True)
        self._email     = _f(staff.get("email"), not read_only_mode)
        self._address   = _f(staff.get("address"), not read_only_mode)

        form.addRow("H\u1ecd v\xe0 t\xean:", self._full_name)
        form.addRow("\u0110i\u1ec7n tho\u1ea1i:", self._phone)
        if not read_only_mode:
            form.addRow("Email:", self._email)
            form.addRow("\u0110\u1ecba ch\u1ec9:", self._address)

        def _ro(lbl, val):
            v = QLabel(str(val) if val else "\u2014"); v.setObjectName("roValue")
            form.addRow(lbl, v)

        _ro("M\xe3 nh\xe2n vi\xean:", staff.get("staff_code"))
        _ro("Ch\u1ee9c v\u1ee5:", staff.get("position"))
        _ro("Ng\xe0y v\xe0o l\xe0m:", staff.get("hire_date"))

        self.lay.addWidget(grp)

        if not read_only_mode:
            save_btn = QPushButton("\U0001f4be  L\u01b0u thay \u0111\u1ed5i")
            save_btn.setObjectName("primaryBtn")
            save_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            save_btn.clicked.connect(self._save)
            self.lay.addWidget(save_btn, alignment=Qt.AlignmentFlag.AlignLeft)
        self.lay.addStretch()

    def _save(self):
        sid = self._staff.get("id")
        if not sid:
            QMessageBox.warning(self, "L\u1ed7i", "Kh\xf4ng c\xf3 h\u1ed3 s\u01a1 nh\xe2n vi\xean li\xean k\u1ebft.")
            return
        from database.schema import get_connection
        conn = get_connection()
        conn.execute(
            "UPDATE staff SET full_name=?, phone=?, email=?, address=? WHERE id=?",
            (self._full_name.text().strip(), self._phone.text().strip(),
             self._email.text().strip(), self._address.text().strip(), sid)
        )
        conn.commit(); conn.close()
        dao.log_action(self._user.get("id"), "UPDATE_PROFILE", "staff", sid,
                       detail="User updated own profile")
        QMessageBox.information(self, "\u2705 Th\xe0nh c\xf4ng", "Th\xf4ng tin \u0111\xe3 \u0111\u01b0\u1ee3c c\u1eadp nh\u1eadt.")


class _LeaveManagementWidget(_scroll):
    def __init__(self):
        super().__init__()
        user  = auth.get_current_user() or {}
        staff_row = dao.get_staff_profile(user.get("id"))
        self._staff = dict(staff_row) if staff_row else {}

        title = QLabel("\U0001f3d6\ufe0f  Qu\u1ea3n l\xfd ngh\u1ec9 ph\xe9p")
        title.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        title.setObjectName("sectionTitle")
        self.lay.addWidget(title)

        # ── Form Request ──
        req_grp = QGroupBox("T\u1ea1o \u0111\u01a1n xin ngh\u1ec9"); req_grp.setObjectName("groupBox")
        form = QFormLayout(req_grp); form.setSpacing(10)

        self.cb_type = QComboBox(); self.cb_type.setObjectName("authInput")
        self.cb_type.addItems(["Ngh\u1ec9 \u1ed1m", "Ngh\u1ec9 ph\xe9p n\u0103m", "Ngh\u1ec9 kh\xf4ng l\u01b0\u01a1ng", "Kh\xe1c"])
        self.txt_start = QLineEdit(); self.txt_start.setPlaceholderText("YYYY-MM-DD"); self.txt_start.setObjectName("authInput")
        self.txt_end = QLineEdit(); self.txt_end.setPlaceholderText("YYYY-MM-DD"); self.txt_end.setObjectName("authInput")
        self.txt_reason = QLineEdit(); self.txt_reason.setObjectName("authInput")

        form.addRow("Lo\u1ea1i ngh\u1ec9:", self.cb_type)
        form.addRow("T\u1eeb ng\xe0y:", self.txt_start)
        form.addRow("\u0110\u1ebfn ng\xe0y:", self.txt_end)
        form.addRow("L\xfd do:", self.txt_reason)

        btn_submit = QPushButton("\u2705  G\u1eedi \u0111\u01a1n")
        btn_submit.setObjectName("primaryBtn"); btn_submit.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_submit.clicked.connect(self._submit_request)
        form.addRow("", btn_submit)
        self.lay.addWidget(req_grp)

        # ── History ──
        hist_grp = QGroupBox("L\u1ecbch s\u1eed \u0111\u01a1n"); hist_grp.setObjectName("groupBox")
        hl = QVBoxLayout(hist_grp)
        self.table = QTableWidget()
        cols = ["Lo\u1ea1i", "T\u1eeb", "\u0110\u1ebfn", "L\xfd do", "Tr\u1ea1ng th\xe1i"]
        self.table.setColumnCount(len(cols))
        self.table.setHorizontalHeaderLabels(cols)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setMinimumHeight(200)
        self.table.verticalHeader().setVisible(False)
        hl.addWidget(self.table)
        
        self.lay.addWidget(hist_grp)
        self.lay.addStretch()
        self._load_history()

    def _submit_request(self):
        sid = self._staff.get("id")
        if not sid:
            QMessageBox.warning(self, "L\u1ed7i", "Kh\xf4ng c\xf3 h\u1ed3 s\u01a1 nh\xe2n vi\xean.")
            return
        st = self.txt_start.text().strip(); en = self.txt_end.text().strip(); rea = self.txt_reason.text().strip()
        if not st or not en or not rea:
            QMessageBox.warning(self, "L\u1ed7i", "Vui l\xf2ng nh\u1eadp \u0111\u1ee7 th\xf4ng tin.")
            return
        dao.create_leave_request(sid, self.cb_type.currentText(), st, en, rea)
        QMessageBox.information(self, "\u2705", "\u0110\xe3 g\u1eedi \u0111\u01a1n th\xe0nh c\xf4ng.")
        self.txt_reason.clear()
        self._load_history()

    def _load_history(self):
        reqs = dao.get_leave_requests_for_staff(self._staff.get("id", 0))
        self.table.setRowCount(len(reqs))
        for r, d in enumerate(reqs):
            vals = [d["leave_type"], d["start_date"], d["end_date"], d["reason"], d["status"]]
            for c, v in enumerate(vals):
                it = QTableWidgetItem(str(v))
                if c == 4:
                    if v == 'Đã duyệt': it.setForeground(Qt.GlobalColor.darkGreen)
                    elif v == 'Từ chối': it.setForeground(Qt.GlobalColor.darkRed)
                it.setData(Qt.ItemDataRole.UserRole, d["id"])
                self.table.setItem(r, c, it)


class _PayslipViewerWidget(_scroll):
    def __init__(self):
        super().__init__()
        user  = auth.get_current_user() or {}
        staff_row = dao.get_staff_profile(user.get("id"))
        staff = dict(staff_row) if staff_row else {}

        title = QLabel("\U0001f9fe  Phi\u1ebfu l\u01b0\u01a1ng c\u1ee7a t\xf4i")
        title.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        title.setObjectName("sectionTitle")
        self.lay.addWidget(title)

        card = QFrame(); card.setObjectName("payslipCard")
        cl = QVBoxLayout(card); cl.setContentsMargins(24, 20, 24, 20); cl.setSpacing(12)

        month_lbl = QLabel(f"\U0001f4c5  Th\xe1ng {datetime.now().month}/{datetime.now().year}")
        month_lbl.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        month_lbl.setObjectName("payslipMonth")
        cl.addWidget(month_lbl)

        sep = QFrame(); sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("color: #e2e8f0;")
        cl.addWidget(sep)

        salary = staff.get("salary", 0) or 0
        bonus  = staff.get("bonus",  0) or 0
        total  = salary + bonus

        for label, value, hi in [
            ("L\u01b0\u01a1ng c\u01a1 b\u1ea3n:", salary, False),
            ("Ph\u1ee5 c\u1ea5p / Th\u01b0\u1edfng:", bonus, False),
        ]:
            row = QHBoxLayout()
            l = QLabel(label); l.setObjectName("psLabel")
            v = QLabel(f"{value:,.0f} \u20ab"); v.setObjectName("psValue")
            v.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            row.addWidget(l); row.addStretch(); row.addWidget(v)
            cl.addLayout(row)

        sep2 = QFrame(); sep2.setFrameShape(QFrame.Shape.HLine)
        sep2.setStyleSheet("color: #e2e8f0;")
        cl.addWidget(sep2)

        row = QHBoxLayout()
        l = QLabel("\U0001f4b0  T\u1ed5ng l\u01b0\u01a1ng:"); l.setObjectName("psLabel")
        l.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        v = QLabel(f"{total:,.0f} \u20ab"); v.setObjectName("psValueHighlight")
        v.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        row.addWidget(l); row.addStretch(); row.addWidget(v)
        cl.addLayout(row)

        note = QLabel("\u26a0\ufe0f  S\u1ed1 li\u1ec7u mang t\xednh tham kh\u1ea3o. Li\xean h\u1ec7 HR \u0111\u1ec3 bi\u1ebft chi ti\u1ebft.")
        note.setWordWrap(True); note.setObjectName("payslipNote")
        cl.addWidget(note)

        self.lay.addWidget(card)
        self.lay.addStretch()


class _SalaryConfigWidget(_scroll):
    def __init__(self):
        super().__init__()
        user  = auth.get_current_user() or {}
        staff_row = dao.get_staff_profile(user.get("id"))
        staff = dict(staff_row) if staff_row else {}

        title = QLabel("\U0001f4b0  L\u01b0\u01a1ng & Th\u01b0\u1edfng")
        title.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        title.setObjectName("sectionTitle")
        self.lay.addWidget(title)

        grp = QGroupBox("Th\xf4ng tin l\u01b0\u01a1ng hi\u1ec7n t\u1ea1i"); grp.setObjectName("groupBox")
        form = QFormLayout(grp); form.setSpacing(10)

        def _ro(val):
            l = QLabel(f"{val:,.0f} \u20ab" if isinstance(val,(int,float)) else (str(val) if val else "\u2014"))
            l.setObjectName("roValue"); return l

        salary = staff.get("salary", 0) or 0
        bonus  = staff.get("bonus",  0) or 0
        form.addRow("L\u01b0\u01a1ng c\u01a1 b\u1ea3n:", _ro(salary))
        form.addRow("Th\u01b0\u1edfng / Ph\u1ee5 c\u1ea5p:", _ro(bonus))
        form.addRow("T\u1ed5ng thu nh\u1eadp:", _ro(salary + bonus))
        form.addRow("Ng\xe2n h\xe0ng:", _ro(None))
        form.addRow("S\u1ed1 t\xe0i kho\u1ea3n:", _ro(None))
        self.lay.addWidget(grp)

        note = QLabel("\u2139\ufe0f  M\u1ecdi thay \u0111\u1ed5i v\u1ec1 l\u01b0\u01a1ng ph\u1ea3i \u0111\u01b0\u1ee3c th\u1ef1c hi\u1ec7n qua ph\xf2ng Nh\xe2n s\u1ef1.")
        note.setWordWrap(True)
        note.setStyleSheet("color: #718096; font-size: 11px;")
        self.lay.addWidget(note)

        hist_grp = QGroupBox("L\u1ecbch s\u1eed phi\u1ebfu l\u01b0\u01a1ng"); hist_grp.setObjectName("groupBox")
        hl2 = QVBoxLayout(hist_grp)
        ph = QLabel("\U0001f4c4  Ch\u1ee9c n\u0103ng xu\u1ea5t phi\u1ebfu l\u01b0\u01a1ng \u0111ang \u0111\u01b0\u1ee3c ph\xe1t tri\u1ec3n.")
        ph.setStyleSheet("color:#718096; font-size:12px; padding:12px;")
        hl2.addWidget(ph)
        self.lay.addWidget(hist_grp)
        self.lay.addStretch()


class _SecurityWidget(_scroll):
    def __init__(self):
        super().__init__()
        title = QLabel("\U0001f512  B\u1ea3o m\u1eadt t\xe0i kho\u1ea3n")
        title.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        title.setObjectName("sectionTitle")
        self.lay.addWidget(title)

        grp = QGroupBox("\u0110\u1ed5i m\u1eadt kh\u1ea9u"); grp.setObjectName("groupBox")
        pl = QFormLayout(grp); pl.setSpacing(10)

        self.old_pass  = self._inp("M\u1eadt kh\u1ea9u hi\u1ec7n t\u1ea1i")
        self.new_pass  = self._inp("M\u1eadt kh\u1ea9u m\u1edbi (t\u1ed1i thi\u1ec3u 8 k\xfd t\u1ef1)")
        self.conf_pass = self._inp("X\xe1c nh\u1eadn m\u1eadt kh\u1ea9u m\u1edbi")

        pl.addRow("M\u1eadt kh\u1ea9u c\u0169:", self.old_pass)
        pl.addRow("M\u1eadt kh\u1ea9u m\u1edbi:", self.new_pass)
        pl.addRow("X\xe1c nh\u1eadn:", self.conf_pass)

        btn = QPushButton("\U0001f511  \u0110\u1ed5i m\u1eadt kh\u1ea9u")
        btn.setObjectName("primaryBtn"); btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.clicked.connect(self._change_password)
        pl.addRow("", btn)
        self.lay.addWidget(grp); self.lay.addStretch()

    def _inp(self, placeholder):
        w = QLineEdit(); w.setEchoMode(QLineEdit.EchoMode.Password)
        w.setPlaceholderText(placeholder); w.setObjectName("authInput")
        return w

    def _change_password(self):
        import bcrypt
        user = auth.get_current_user()
        if not user: return
        old = self.old_pass.text(); new = self.new_pass.text(); conf = self.conf_pass.text()
        row = dao.get_user_by_username(user["username"])
        if not bcrypt.checkpw(old.encode(), row["password"].encode()):
            QMessageBox.warning(self, "Sai m\u1eadt kh\u1ea9u", "M\u1eadt kh\u1ea9u hi\u1ec7n t\u1ea1i kh\xf4ng \u0111\xfang."); return
        if len(new) < 8:
            QMessageBox.warning(self, "M\u1eadt kh\u1ea9u y\u1ebfu", "M\u1eadt kh\u1ea9u m\u1edbi ph\u1ea3i c\xf3 \xedt nh\u1ea5t 8 k\xfd t\u1ef1."); return
        if new != conf:
            QMessageBox.warning(self, "Kh\xf4ng kh\u1edbp", "M\u1eadt kh\u1ea9u m\u1edbi v\xe0 x\xe1c nh\u1eadn kh\xf4ng kh\u1edbp."); return
        hashed = bcrypt.hashpw(new.encode(), bcrypt.gensalt()).decode()
        dao.update_user_password(user["id"], hashed, clear_force_change=False)
        self.old_pass.clear(); self.new_pass.clear(); self.conf_pass.clear()
        QMessageBox.information(self, "\u2705 Th\xe0nh c\xf4ng", "M\u1eadt kh\u1ea9u \u0111\xe3 \u0111\u01b0\u1ee3c \u0111\u1ed5i th\xe0nh c\xf4ng.")


class _AccountCreationWidget(_scroll):
    def __init__(self):
        super().__init__()
        title = QLabel("\U0001f465  C\u1ea5p t\xe0i kho\u1ea3n nh\xe2n vi\xean")
        title.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        title.setObjectName("sectionTitle")
        self.lay.addWidget(title)

        grp = QGroupBox("T\u1ea1o t\xe0i kho\u1ea3n m\u1edbi"); grp.setObjectName("groupBox")
        al = QFormLayout(grp); al.setSpacing(10)

        self.staff_cb = QComboBox(); self.staff_cb.setObjectName("authInput")
        self._load_staff()
        self.role_cb = QComboBox(); self.role_cb.setObjectName("authInput")
        for r in dao.get_all_roles():
            self.role_cb.addItem(r["role_name"], r["id"])

        self.new_username = QLineEdit()
        self.new_username.setPlaceholderText("T\xean \u0111\u0103ng nh\u1eadp")
        self.new_username.setObjectName("authInput")

        self.new_user_pass = QLineEdit()
        self.new_user_pass.setEchoMode(QLineEdit.EchoMode.Password)
        self.new_user_pass.setPlaceholderText("M\u1eadt kh\u1ea9u t\u1ea1m th\u1eddi")
        self.new_user_pass.setObjectName("authInput")

        gen_btn = QPushButton("\U0001f3b2 T\u1ef1 \u0111\u1ed9ng")
        gen_btn.setObjectName("actionBtn"); gen_btn.setFixedWidth(90)
        gen_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        gen_btn.setToolTip("T\u1ea1o m\u1eadt kh\u1ea9u ng\u1eabu nhi\xean 12 k\xfd t\u1ef1")
        gen_btn.clicked.connect(self._auto_generate_password)

        show_btn = QPushButton("\U0001f441")
        show_btn.setFixedSize(32, 32); show_btn.setObjectName("actionBtn")
        show_btn.clicked.connect(lambda: (
            self.new_user_pass.setEchoMode(QLineEdit.EchoMode.Normal)
            if self.new_user_pass.echoMode() == QLineEdit.EchoMode.Password
            else self.new_user_pass.setEchoMode(QLineEdit.EchoMode.Password)
        ))

        pw_row = QHBoxLayout()
        pw_row.addWidget(self.new_user_pass)
        pw_row.addWidget(gen_btn); pw_row.addWidget(show_btn)

        al.addRow("Nh\xe2n vi\xean:", self.staff_cb)
        al.addRow("Vai tr\xf2:", self.role_cb)
        al.addRow("T\xe0i kho\u1ea3n:", self.new_username)
        al.addRow("M\u1eadt kh\u1ea9u:", pw_row)

        info = QLabel("\u2139\ufe0f  Nh\xe2n vi\xean s\u1ebd b\u1ecb y\xeau c\u1ea7u \u0111\u1ed5i m\u1eadt kh\u1ea9u \u1edf l\u1ea7n \u0111\u0103ng nh\u1eadp \u0111\u1ea7u ti\xean.")
        info.setWordWrap(True)
        info.setStyleSheet("color: #2b6cb0; font-size: 11px; background: #ebf8ff; padding: 8px; border-radius: 6px;")
        al.addRow("", info)

        create_btn = QPushButton("\u2705  T\u1ea1o t\xe0i kho\u1ea3n")
        create_btn.setObjectName("primaryBtn"); create_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        create_btn.clicked.connect(self._create_account)
        al.addRow("", create_btn)

        self.lay.addWidget(grp); self.lay.addStretch()

    def _load_staff(self):
        self.staff_cb.clear()
        self.staff_cb.addItem("-- Ch\u1ecdn nh\xe2n vi\xean --", None)
        for s in dao.get_staff_without_accounts():
            self.staff_cb.addItem(f"{s['staff_code']} - {s['full_name']} ({s['position']})", s["id"])

    def _auto_generate_password(self):
        alphabet = string.ascii_letters + string.digits + "!@#$%"
        pwd = "".join(secrets.choice(alphabet) for _ in range(12))
        self.new_user_pass.setText(pwd)
        self.new_user_pass.setEchoMode(QLineEdit.EchoMode.Normal)
        QMessageBox.information(self, "\U0001f3b2 M\u1eadt kh\u1ea9u \u0111\xe3 t\u1ea1o",
            f"M\u1eadt kh\u1ea9u t\u1ea1m th\u1eddi:\n\n  {pwd}\n\n"
            "H\xe3y ghi l\u1ea1i v\xe0 trao cho nh\xe2n vi\xean m\u1ed9t c\xe1ch b\u1ea3o m\u1eadt.\n"
            "Nh\xe2n vi\xean s\u1ebd ph\u1ea3i \u0111\u1ed5i m\u1eadt kh\u1ea9u \u1edf l\u1ea7n \u0111\u0103ng nh\u1eadp \u0111\u1ea7u ti\xean.")

    def _create_account(self):
        import bcrypt
        staff_id = self.staff_cb.currentData()
        role_id  = self.role_cb.currentData()
        username = self.new_username.text().strip()
        password = self.new_user_pass.text()
        if not staff_id:
            QMessageBox.warning(self, "L\u1ed7i", "Vui l\xf2ng ch\u1ecdn nh\xe2n vi\xean."); return
        if not username or not password:
            QMessageBox.warning(self, "L\u1ed7i", "Vui l\xf2ng nh\u1eadp t\xean \u0111\u0103ng nh\u1eadp v\xe0 m\u1eadt kh\u1ea9u."); return
        if len(password) < 6:
            QMessageBox.warning(self, "L\u1ed7i", "M\u1eadt kh\u1ea9u ph\u1ea3i c\xf3 \xedt nh\u1ea5t 6 k\xfd t\u1ef1."); return
        hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
        try:
            dao.create_user_for_staff(staff_id, username, hashed, role_id, must_change_password=1)
            hr = auth.get_current_user()
            if hr:
                dao.log_action(hr["id"], "CREATE_USER_ACCOUNT", "users", None,
                               detail=f"HR created account '{username}' for staff_id={staff_id}")
            QMessageBox.information(self, "\u2705 Th\xe0nh c\xf4ng",
                f"\u0110\xe3 t\u1ea1o t\xe0i kho\u1ea3n '{username}'.\n\n"
                "Nh\xe2n vi\xean s\u1ebd \u0111\u01b0\u1ee3c y\xeau c\u1ea7u \u0111\u1ed5i m\u1eadt kh\u1ea9u \u1edf l\u1ea7n \u0111\u0103ng nh\u1eadp \u0111\u1ea7u ti\xean.")
            self.new_username.clear(); self.new_user_pass.clear(); self._load_staff()
        except ValueError as e:
            QMessageBox.warning(self, "L\u1ed7i", str(e))
        except Exception as e:
            QMessageBox.critical(self, "L\u1ed7i", f"C\xf3 l\u1ed7i x\u1ea3y ra: {e}")


class _BackupWidget(_scroll):
    def __init__(self):
        super().__init__()
        title = QLabel("\U0001f4be  Sao l\u01b0u & Ph\u1ee5c h\u1ed3i Database")
        title.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        title.setObjectName("sectionTitle"); self.lay.addWidget(title)

        grp = QGroupBox("Qu\u1ea3n l\xfd Backup"); grp.setObjectName("groupBox")
        bl = QVBoxLayout(grp); bl.setSpacing(10)

        db_info = QLabel(f"\U0001f4c1  Database: {os.path.basename(DB_PATH)}\n\U0001f4c2  Backup folder: {BACKUP_DIR}")
        db_info.setObjectName("infoLbl"); bl.addWidget(db_info)

        btn_row = QHBoxLayout()
        bk = QPushButton("\U0001f4e6  T\u1ea1o Backup ngay"); bk.setObjectName("backupBtn")
        bk.setCursor(Qt.CursorShape.PointingHandCursor); bk.clicked.connect(self._do_backup)
        od = QPushButton("\U0001f4c2  M\u1edf th\u01b0 m\u1ee5c"); od.setObjectName("actionBtn")
        od.setCursor(Qt.CursorShape.PointingHandCursor); od.clicked.connect(self._open_dir)
        btn_row.addWidget(bk); btn_row.addWidget(od); btn_row.addStretch()
        bl.addLayout(btn_row)

        bl.addWidget(QLabel("\U0001f4cb  Danh s\xe1ch backup:"))
        self.backup_table = QTableWidget()
        self.backup_table.setColumnCount(3)
        self.backup_table.setHorizontalHeaderLabels(["T\xean file","K\xedch th\u01b0\u1edbc","Th\u1eddi gian"])
        self.backup_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.backup_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.backup_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.backup_table.setMaximumHeight(220)
        self.backup_table.verticalHeader().setVisible(False)
        bl.addWidget(self.backup_table)

        rs = QPushButton("\U0001f504  Ph\u1ee5c h\u1ed3i t\u1eeb backup \u0111\xe3 ch\u1ecdn"); rs.setObjectName("restoreBtn")
        rs.setCursor(Qt.CursorShape.PointingHandCursor); rs.clicked.connect(self._do_restore)
        bl.addWidget(rs)

        self.lay.addWidget(grp); self.lay.addStretch()
        self._load_backups()

    def _load_backups(self):
        backups = sorted(glob.glob(os.path.join(BACKUP_DIR,"*.db")), reverse=True)
        self.backup_table.setRowCount(len(backups))
        for r,p in enumerate(backups):
            name  = os.path.basename(p)
            size  = f"{os.path.getsize(p)/1024:.1f} KB"
            mtime = datetime.fromtimestamp(os.path.getmtime(p)).strftime("%d/%m/%Y %H:%M")
            for c,v in enumerate([name,size,mtime]):
                self.backup_table.setItem(r,c,QTableWidgetItem(v))

    def _do_backup(self):
        if not os.path.exists(DB_PATH):
            QMessageBox.warning(self,"L\u1ed7i","Kh\xf4ng t\xecm th\u1ea5y file database."); return
        ts   = datetime.now().strftime("%Y%m%d_%H%M%S")
        dest = os.path.join(BACKUP_DIR,f"hospital_backup_{ts}.db")
        shutil.copy2(DB_PATH, dest); self._load_backups()
        QMessageBox.information(self,"\u2705 Backup th\xe0nh c\xf4ng",f"File:\n{os.path.basename(dest)}")

    def _do_restore(self):
        row = self.backup_table.currentRow()
        if row < 0:
            QMessageBox.information(self,"Ch\u01b0a ch\u1ecdn","Vui l\xf2ng ch\u1ecdn m\u1ed9t file backup."); return
        fn  = self.backup_table.item(row,0).text()
        src = os.path.join(BACKUP_DIR, fn)
        reply = QMessageBox.warning(self,"\u26a0\ufe0f  X\xe1c nh\u1eadn ph\u1ee5c h\u1ed3i",
            f"B\u1ea1n c\xf3 ch\u1eafc mu\u1ed1n ph\u1ee5c h\u1ed3i database t\u1eeb:\n{fn}?\n\nD\u1eef li\u1ec7u hi\u1ec7n t\u1ea1i s\u1ebd b\u1ecb GHI \u0110\u00c8.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel)
        if reply == QMessageBox.StandardButton.Yes:
            ts   = datetime.now().strftime("%Y%m%d_%H%M%S")
            auto = os.path.join(BACKUP_DIR, f"hospital_auto_before_restore_{ts}.db")
            if os.path.exists(DB_PATH): shutil.copy2(DB_PATH, auto)
            shutil.copy2(src, DB_PATH)
            QMessageBox.information(self,"\u2705 Ph\u1ee5c h\u1ed3i th\xe0nh c\xf4ng",
                "Database \u0111\xe3 \u0111\u01b0\u1ee3c ph\u1ee5c h\u1ed3i.\nVui l\xf2ng kh\u1edfi \u0111\u1ed9ng l\u1ea1i \u1ee9ng d\u1ee5ng.")

    def _open_dir(self):
        import subprocess, sys
        if sys.platform=="win32": os.startfile(BACKUP_DIR)
        elif sys.platform=="darwin": subprocess.Popen(["open",BACKUP_DIR])
        else: subprocess.Popen(["xdg-open",BACKUP_DIR])


class _SystemInfoWidget(_scroll):
    def __init__(self):
        super().__init__()
        title = QLabel("\u2139\ufe0f  Th\xf4ng tin h\u1ec7 th\u1ed1ng")
        title.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        title.setObjectName("sectionTitle"); self.lay.addWidget(title)

        grp = QGroupBox("Th\u1ed1ng k\xea & M\xf4i tr\u01b0\u1eddng"); grp.setObjectName("groupBox")
        il = QFormLayout(grp); il.setSpacing(8)

        stats = dao.get_dashboard_stats()
        def _add(lbl, val):
            l = QLabel(lbl); l.setObjectName("fieldLabel")
            v = QLabel(str(val)); v.setObjectName("roValue")
            il.addRow(l, v)

        _add("T\u1ed5ng b\u1ec7nh nh\xe2n:", stats.get("total_patients","—"))
        _add("T\u1ed5ng nh\xe2n vi\xean:", stats.get("total_staff","—"))
        _add("Database size:", f"{os.path.getsize(DB_PATH)/1024:.1f} KB" if os.path.exists(DB_PATH) else "N/A")

        import sys
        _add("Python:", f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
        try:
            from PyQt6.QtCore import PYQT_VERSION_STR
            _add("PyQt6:", PYQT_VERSION_STR)
        except: pass
        _add("DB path:", DB_PATH)

        self.lay.addWidget(grp); self.lay.addStretch()
