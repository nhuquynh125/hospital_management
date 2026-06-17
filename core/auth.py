import bcrypt
from database.dao import get_user_by_username, log_action
from database.schema import get_connection

# ── Singleton: current logged-in user ──────────────────────
_current_user = None
_current_permissions = set()

# ── Role definitions ────────────────────────────────────────
ROLES = {
    "admin":          "Quản trị viên",
    "doctor":         "Bác sĩ",
    "nurse":          "Y tá / Điều dưỡng",
    "receptionist":   "Lễ tân",
    "pharmacist":     "Dược sĩ",
    "accountant":     "Kế toán",
    "lab_technician": "Xét nghiệm viên",
    "director":       "Giám đốc",
    "cashier":        "Thu ngân",
    "department_head":"Trưởng khoa",
    "hr_manager":     "Quản lý nhân sự",
    "security_guard":  "Bảo vệ",
    "ambulance_driver":"Lái xe cứu thương",
    "janitor":         "Nhân viên vệ sinh",

}

ROLE_LABELS = {v: k for k, v in ROLES.items()}  # reverse lookup


def load_user_permissions(role_id):
    conn = get_connection()
    rows = conn.execute("""
        SELECT p.permission_name
        FROM role_permissions rp
        JOIN permissions p ON rp.permission_id = p.id
        WHERE rp.role_id = ?
    """, (role_id,)).fetchall()
    conn.close()
    return {row["permission_name"] for row in rows}


def login(username: str, password: str):
    global _current_user, _current_permissions
    row = get_user_by_username(username.strip())
    if not row:
        return None
    stored_hash = row["password"].encode()
    if bcrypt.checkpw(password.encode(), stored_hash):
        _current_user = dict(row)
        _current_permissions = load_user_permissions(_current_user["role_id"])
        log_action(row["id"], "LOGIN", detail=f"User '{username}' logged in")
        return _current_user
    return None


def logout():
    global _current_user, _current_permissions
    if _current_user:
        log_action(_current_user["id"], "LOGOUT",
                   detail=f"User '{_current_user['username']}' logged out")
    _current_user = None
    _current_permissions = set()


def get_current_user():
    return _current_user


def get_role_label(role_key: str) -> str:
    return ROLES.get(role_key, role_key)


def can_access(module: str) -> bool:
    if not _current_user:
        return False
    return module in _current_permissions


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
