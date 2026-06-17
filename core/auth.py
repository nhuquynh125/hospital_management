import bcrypt
from database.dao import get_user_by_username, log_action

# ── Singleton: current logged-in user ──────────────────────
_current_user = None

# ── Role definitions ────────────────────────────────────────
ROLES = {
    "admin":          "Quản trị viên",
    "doctor":         "Bác sĩ",
    "nurse":          "Y tá / Điều dưỡng",
    "receptionist":   "Lễ tân",
    "pharmacist":     "Dược sĩ",
    "accountant":     "Kế toán",
    "lab_technician": "Xét nghiệm viên",
    "director":       "Giám đốc / Trưởng khoa",
}

ROLE_LABELS = {v: k for k, v in ROLES.items()}  # reverse lookup

# ── Permission map ──────────────────────────────────────────
# module → set of roles that can access
PERMISSIONS = {
    # Xem & quản lý bệnh nhân
    "patients":        {"admin", "doctor", "nurse", "receptionist", "director"},
    # Quản lý nhân viên
    "staff":           {"admin", "director"},
    # Lịch hẹn
    "appointments":    {"admin", "doctor", "nurse", "receptionist", "director"},
    # Hồ sơ bệnh án / Medical records
    "medical_records": {"admin", "doctor", "nurse"},
    # Thuốc & kê đơn
    "medicines":       {"admin", "doctor", "pharmacist"},
    # Kho thuốc (chỉ dược sĩ + admin quản lý tồn kho)
    "pharmacy":        {"admin", "pharmacist"},
    # Phòng / Giường bệnh
    "rooms":           {"admin", "nurse", "receptionist", "director"},
    # Viện phí / Thanh toán
    "billing":         {"admin", "accountant", "receptionist"},
    # Xét nghiệm
    "lab":             {"admin", "doctor", "lab_technician"},
    # Báo cáo / Thống kê (chỉ xem)
    "reports":         {"admin", "director", "doctor", "accountant",
                        "pharmacist", "lab_technician", "nurse", "receptionist"},
    # Xuất file
    "export":          {"admin", "director", "accountant", "doctor"},
    # Cài đặt & backup
    "settings":        {"admin"},
    # Chatbot AI
    "ai":              {"admin", "doctor", "nurse", "pharmacist", "lab_technician", "director"},
}


def login(username: str, password: str):
    global _current_user
    row = get_user_by_username(username.strip())
    if not row:
        return None
    stored_hash = row["password"].encode()
    if bcrypt.checkpw(password.encode(), stored_hash):
        _current_user = dict(row)
        log_action(row["id"], "LOGIN", detail=f"User '{username}' logged in")
        return _current_user
    return None


def logout():
    global _current_user
    if _current_user:
        log_action(_current_user["id"], "LOGOUT",
                   detail=f"User '{_current_user['username']}' logged out")
    _current_user = None


def get_current_user():
    return _current_user


def get_role_label(role_key: str) -> str:
    return ROLES.get(role_key, role_key)


def can_access(module: str) -> bool:
    user = get_current_user()
    if not user:
        return False
    return user["role"] in PERMISSIONS.get(module, set())


def require_role(*roles):
    user = get_current_user()
    if user is None:
        raise PermissionError("Chưa đăng nhập.")
    if user["role"] not in roles:
        raise PermissionError(
            f"Bạn không có quyền thực hiện thao tác này.\n"
            f"Yêu cầu vai trò: {', '.join(ROLES.get(r, r) for r in roles)}"
        )
    return user
