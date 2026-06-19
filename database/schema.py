import sqlite3
import os
import bcrypt
import json

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "hospital.db")


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    conn = get_connection()
    cur = conn.cursor()

    # ── Roles & Permissions (RBAC) ────────────────────────────────
    cur.execute("""
    CREATE TABLE IF NOT EXISTS roles (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        role_name   TEXT UNIQUE NOT NULL,
        description TEXT
    )""")

    cur.execute("""
    CREATE TABLE IF NOT EXISTS permissions (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        permission_name TEXT UNIQUE NOT NULL,
        description     TEXT
    )""")

    cur.execute("""
    CREATE TABLE IF NOT EXISTS role_permissions (
        role_id       INTEGER REFERENCES roles(id) ON DELETE CASCADE,
        permission_id INTEGER REFERENCES permissions(id) ON DELETE CASCADE,
        PRIMARY KEY (role_id, permission_id)
    )""")

    # ── Users / Auth ──────────────────────────────────────────────
    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        username    TEXT UNIQUE NOT NULL,
        password    TEXT NOT NULL,
        full_name   TEXT NOT NULL,
        role_id     INTEGER REFERENCES roles(id),
        is_active              INTEGER DEFAULT 1,
        must_change_password   INTEGER DEFAULT 0,
        created_at  TEXT DEFAULT (datetime('now','localtime'))
    )""")

    # ── Departments ───────────────────────────────────────────────
    cur.execute("""
    CREATE TABLE IF NOT EXISTS departments (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        name        TEXT UNIQUE NOT NULL,
        description TEXT
    )""")

    # ── Staff ─────────────────────────────────────────────────────
    cur.execute("""
    CREATE TABLE IF NOT EXISTS staff (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id         INTEGER REFERENCES users(id) ON DELETE SET NULL,
        staff_code      TEXT UNIQUE NOT NULL,
        full_name       TEXT NOT NULL,
        gender          TEXT CHECK(gender IN ('Nam','Nữ','Khác')),
        birth_date      TEXT,
        id_card         TEXT UNIQUE,
        phone           TEXT,
        email           TEXT,
        address         TEXT,
        position        TEXT NOT NULL,
        specialization  TEXT,
        department_id   INTEGER REFERENCES departments(id),
        hire_date       TEXT,
        salary          REAL DEFAULT 0,
        bonus           REAL DEFAULT 0,
        work_schedule   TEXT,
        is_active       INTEGER DEFAULT 1,
        notes           TEXT,
        created_at      TEXT DEFAULT (datetime('now','localtime'))
    )""")

    # ── Patients ──────────────────────────────────────────────────
    cur.execute("""
    CREATE TABLE IF NOT EXISTS patients (
        id                INTEGER PRIMARY KEY AUTOINCREMENT,
        patient_code      TEXT UNIQUE NOT NULL,
        full_name         TEXT NOT NULL,
        birth_date        TEXT,
        gender            TEXT CHECK(gender IN ('Nam','Nữ','Khác')),
        id_card           TEXT,
        phone             TEXT,
        address           TEXT,
        blood_type        TEXT,
        insurance_id      TEXT,
        insurance_exp     TEXT,
        emergency_contact TEXT,
        allergies         TEXT,
        notes             TEXT,
        created_at        TEXT DEFAULT (datetime('now','localtime')),
        updated_at        TEXT DEFAULT (datetime('now','localtime'))
    )""")

    # ── Medical Records ───────────────────────────────────────────
    cur.execute("""
    CREATE TABLE IF NOT EXISTS medical_records (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        patient_id      INTEGER NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
        doctor_id       INTEGER REFERENCES staff(id),
        nurse_id        INTEGER REFERENCES staff(id),
        visit_date      TEXT DEFAULT (datetime('now','localtime')),
        symptoms        TEXT,
        diagnosis       TEXT,
        treatment_plan  TEXT,
        notes           TEXT,
        follow_up_date  TEXT,
        created_at      TEXT DEFAULT (datetime('now','localtime'))
    )""")

    # ── Medical Orders (Y lệnh cho Y tá) ──────────────────────────
    cur.execute("""
    CREATE TABLE IF NOT EXISTS medical_orders (
        id                INTEGER PRIMARY KEY AUTOINCREMENT,
        medical_record_id INTEGER NOT NULL REFERENCES medical_records(id) ON DELETE CASCADE,
        patient_id        INTEGER NOT NULL REFERENCES patients(id),
        doctor_id         INTEGER REFERENCES staff(id),
        order_type        TEXT NOT NULL,
        description       TEXT NOT NULL,
        order_time        TEXT DEFAULT (datetime('now','localtime')),
        status            TEXT DEFAULT 'Pending' CHECK(status IN ('Pending','Done','Cancelled')),
        nurse_id          INTEGER REFERENCES staff(id),
        execution_time    TEXT,
        notes             TEXT
    )""")

    # ── Nursing Care Notes (Y tá / Điều dưỡng) ───────────────────
    cur.execute("""
    CREATE TABLE IF NOT EXISTS nursing_notes (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        patient_id      INTEGER NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
        nurse_id        INTEGER NOT NULL REFERENCES staff(id),
        note_date       TEXT DEFAULT (datetime('now','localtime')),
        vital_signs     TEXT,   -- JSON: {"temp":37.5,"bp":"120/80","pulse":72,"spo2":98}
        care_given      TEXT,
        patient_status  TEXT,
        notes           TEXT
    )""")

    # ── Rooms ─────────────────────────────────────────────────────
    cur.execute("""
    CREATE TABLE IF NOT EXISTS rooms (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        room_number TEXT UNIQUE NOT NULL,
        room_type   TEXT NOT NULL CHECK(room_type IN ('Thường','VIP','ICU','Phẫu thuật','Khám')),
        capacity    INTEGER DEFAULT 1,
        floor       INTEGER DEFAULT 1,
        status      TEXT DEFAULT 'Trống' CHECK(status IN ('Trống','Đang dùng','Bảo trì')),
        notes       TEXT
    )""")

    # ── Appointments ──────────────────────────────────────────────
    cur.execute("""
    CREATE TABLE IF NOT EXISTS appointments (
        id                    INTEGER PRIMARY KEY AUTOINCREMENT,
        patient_id            INTEGER NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
        doctor_id             INTEGER NOT NULL REFERENCES staff(id),
        room_id               INTEGER REFERENCES rooms(id),
        appointment_date      TEXT NOT NULL,
        appointment_time      TEXT NOT NULL,
        reason                TEXT,
        status                TEXT DEFAULT 'Chờ'
                              CHECK(status IN ('Chờ','Đang khám','Hoàn thành','Huỷ')),
        is_followup           INTEGER DEFAULT 0,
        parent_appointment_id INTEGER REFERENCES appointments(id),
        notes                 TEXT,
        created_at            TEXT DEFAULT (datetime('now','localtime'))
    )""")

    # ── Medicines ─────────────────────────────────────────────────
    cur.execute("""
    CREATE TABLE IF NOT EXISTS medicines (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        medicine_code   TEXT UNIQUE NOT NULL,
        name            TEXT NOT NULL,
        generic_name    TEXT,
        category        TEXT,
        unit            TEXT,
        stock_qty       INTEGER DEFAULT 0,
        min_stock       INTEGER DEFAULT 10,
        price           REAL DEFAULT 0,
        expiry_date     TEXT,
        supplier        TEXT,
        description     TEXT,
        is_active       INTEGER DEFAULT 1,
        updated_at      TEXT DEFAULT (datetime('now','localtime'))
    )""")



    # ── Prescriptions ─────────────────────────────────────────────
    cur.execute("""
    CREATE TABLE IF NOT EXISTS prescriptions (
        id                INTEGER PRIMARY KEY AUTOINCREMENT,
        medical_record_id INTEGER REFERENCES medical_records(id) ON DELETE CASCADE,
        doctor_id         INTEGER REFERENCES staff(id),
        pharmacist_id     INTEGER REFERENCES staff(id),  -- dược sĩ duyệt đơn
        issue_date        TEXT DEFAULT (datetime('now','localtime')),
        dispensed_date    TEXT,   -- ngày phát thuốc
        status            TEXT DEFAULT 'Chờ duyệt'
                          CHECK(status IN ('Chờ duyệt','Đã duyệt','Đã phát','Huỷ')),
        notes             TEXT
    )""")

    cur.execute("""
    CREATE TABLE IF NOT EXISTS prescription_items (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        prescription_id INTEGER NOT NULL REFERENCES prescriptions(id) ON DELETE CASCADE,
        medicine_id     INTEGER NOT NULL REFERENCES medicines(id),
        quantity        INTEGER NOT NULL,
        dosage          TEXT,
        duration_days   INTEGER,
        notes           TEXT
    )""")

    # ── Lab Tests (Xét nghiệm) ────────────────────────────────────
    cur.execute("""
    CREATE TABLE IF NOT EXISTS lab_tests (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        patient_id      INTEGER NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
        doctor_id       INTEGER REFERENCES staff(id),   -- bác sĩ chỉ định
        technician_id   INTEGER REFERENCES staff(id),   -- xét nghiệm viên thực hiện
        test_type       TEXT NOT NULL,   -- Công thức máu, Sinh hoá, Nước tiểu,...
        ordered_date    TEXT DEFAULT (datetime('now','localtime')),
        result_date     TEXT,
        result          TEXT,            -- JSON hoặc text mô tả
        result_file     TEXT,            -- đường dẫn file kết quả
        status          TEXT DEFAULT 'Chờ'
                        CHECK(status IN ('Chờ','Đang xét nghiệm','Có kết quả','Huỷ')),
        notes           TEXT
    )""")

    # ── Billing / Viện phí ────────────────────────────────────────
    cur.execute("""
    CREATE TABLE IF NOT EXISTS bills (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        patient_id      INTEGER NOT NULL REFERENCES patients(id),
        accountant_id   INTEGER REFERENCES staff(id),
        bill_date       TEXT DEFAULT (datetime('now','localtime')),
        total_amount    REAL DEFAULT 0,
        paid_amount     REAL DEFAULT 0,
        discount        REAL DEFAULT 0,
        insurance_cover REAL DEFAULT 0,
        payment_method  TEXT CHECK(payment_method IN ('Tiền mặt','Chuyển khoản','BHYT','Thẻ')),
        status          TEXT DEFAULT 'Chưa thanh toán'
                        CHECK(status IN ('Chưa thanh toán','Đã thanh toán','Một phần','Huỷ')),
        notes           TEXT
    )""")

    cur.execute("""
    CREATE TABLE IF NOT EXISTS bill_items (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        bill_id     INTEGER NOT NULL REFERENCES bills(id) ON DELETE CASCADE,
        item_type   TEXT NOT NULL CHECK(item_type IN ('Khám','Thuốc','Xét nghiệm','Phòng','Dịch vụ')),
        description TEXT NOT NULL,
        quantity    INTEGER DEFAULT 1,
        unit_price  REAL DEFAULT 0,
        total       REAL DEFAULT 0
    )""")

    # ── Audit Log ─────────────────────────────────────────────────
    cur.execute("""
    CREATE TABLE IF NOT EXISTS audit_log (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id     INTEGER REFERENCES users(id),
        action      TEXT NOT NULL,
        table_name  TEXT,
        record_id   INTEGER,
        old_value   TEXT,
        new_value   TEXT,
        detail      TEXT,
        timestamp   TEXT DEFAULT (datetime('now','localtime'))
    )""")

    # ── Leave Requests ────────────────────────────────────────────
    cur.execute("""
    CREATE TABLE IF NOT EXISTS leave_requests (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        staff_id    INTEGER NOT NULL REFERENCES staff(id) ON DELETE CASCADE,
        leave_type  TEXT NOT NULL CHECK(leave_type IN ('Nghỉ ốm', 'Nghỉ phép năm', 'Nghỉ không lương', 'Khác')),
        start_date  TEXT NOT NULL,
        end_date    TEXT NOT NULL,
        reason      TEXT NOT NULL,
        status      TEXT DEFAULT 'Chờ duyệt' CHECK(status IN ('Chờ duyệt', 'Đã duyệt', 'Từ chối')),
        created_at  TEXT DEFAULT (datetime('now','localtime'))
    )""")

    # ── Shift Schedules ────────────────────────────────────────────
    cur.execute("""
    CREATE TABLE IF NOT EXISTS shift_schedules (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        staff_id    INTEGER NOT NULL REFERENCES staff(id) ON DELETE CASCADE,
        shift_date  TEXT NOT NULL,
        shift_type  TEXT NOT NULL CHECK(shift_type IN ('Sáng', 'Chiều', 'Đêm')),
        notes       TEXT,
        created_at  TEXT DEFAULT (datetime('now','localtime'))
    )""")

    conn.commit()
    # ── Live migrations for existing databases ──────────────────────────────
    _migrate_db(conn, cur)
    # ───────────────────────────────────────────────────────────────────────
    _seed_rbac(cur, conn)
    _seed_users(cur, conn)
    _seed_data(cur, conn)
    conn.close()
    try:
        print(f"[DB] Database initialized -> {DB_PATH}")
    except UnicodeEncodeError:
        print("[DB] Database initialized -> (path contains unicode)")



def _migrate_db(conn, cur):
    """Apply incremental schema changes to existing databases safely."""
    # must_change_password column (v2 addition)
    cols = [row[1] for row in cur.execute("PRAGMA table_info(users)").fetchall()]
    if "must_change_password" not in cols:
        cur.execute("ALTER TABLE users ADD COLUMN must_change_password INTEGER DEFAULT 0")
        conn.commit()

    # leave_requests table (v3 addition)
    tables = [row[0] for row in cur.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
    if "leave_requests" not in tables:
        cur.execute("""
        CREATE TABLE IF NOT EXISTS leave_requests (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            staff_id    INTEGER NOT NULL REFERENCES staff(id) ON DELETE CASCADE,
            leave_type  TEXT NOT NULL CHECK(leave_type IN ('Nghỉ ốm', 'Nghỉ phép năm', 'Nghỉ không lương', 'Khác')),
            start_date  TEXT NOT NULL,
            end_date    TEXT NOT NULL,
            reason      TEXT NOT NULL,
            status      TEXT DEFAULT 'Chờ duyệt' CHECK(status IN ('Chờ duyệt', 'Đã duyệt', 'Từ chối')),
            created_at  TEXT DEFAULT (datetime('now','localtime'))
        )""")
        conn.commit()

    if "shift_schedules" not in tables:
        cur.execute("""
        CREATE TABLE IF NOT EXISTS shift_schedules (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            staff_id    INTEGER NOT NULL REFERENCES staff(id) ON DELETE CASCADE,
            shift_date  TEXT NOT NULL,
            shift_type  TEXT NOT NULL CHECK(shift_type IN ('Sáng', 'Chiều', 'Đêm')),
            notes       TEXT,
            created_at  TEXT DEFAULT (datetime('now','localtime'))
        )""")
        conn.commit()

    # Grant settings.leave to minor roles that were missing it (v4 fix)
    try:
        minor_roles = ("security_guard", "ambulance_driver", "janitor")
        for role_name in minor_roles:
            row = cur.execute("SELECT id FROM roles WHERE role_name=?", (role_name,)).fetchone()
            perm = cur.execute("SELECT id FROM permissions WHERE permission_name='settings.leave'").fetchone()
            if row and perm:
                cur.execute(
                    "INSERT OR IGNORE INTO role_permissions (role_id, permission_id) VALUES (?, ?)",
                    (row[0], perm[0])
                )
        conn.commit()
    except Exception:
        pass

    # Give 'settings' permission to director
    try:
        cur.execute("SELECT id FROM roles WHERE role_name='director'")
        director_role = cur.fetchone()
        if director_role:
            role_id = director_role[0]
            cur.execute("SELECT id FROM permissions WHERE permission_name='settings'")
            perm_id = cur.fetchone()
            if perm_id:
                cur.execute("INSERT OR IGNORE INTO role_permissions (role_id, permission_id) VALUES (?, ?)", (role_id, perm_id[0]))
                conn.commit()
    except Exception as e:
        pass


def _seed_rbac(cur, conn):
    # Check if roles exist
    cur.execute("SELECT COUNT(*) FROM roles")
    if cur.fetchone()[0] > 0:
        return

    roles = [
        ("admin", "Quản trị viên"),
        ("doctor", "Bác sĩ"),
        ("nurse", "Y tá / Điều dưỡng"),
        ("receptionist", "Lễ tân"),
        ("pharmacist", "Dược sĩ"),
        ("accountant", "Kế toán"),
        ("lab_technician", "Xét nghiệm viên"),
        ("director", "Giám đốc"),
        ("cashier", "Thu ngân"),
        ("department_head", "Trưởng khoa"),
        ("hr_manager", "Quản lý nhân sự"),
            ("security_guard",   "Bao ve"),
        ("ambulance_driver", "Lai xe cuu thuong"),
        ("janitor",          "Nhan vien ve sinh"),
    ]
    cur.executemany("INSERT INTO roles (role_name, description) VALUES (?,?)", roles)

    permissions = [
        "patients", "staff", "appointments", "medical_records", "medical_orders",
        "medicines", "pharmacy", "rooms", "billing", "lab", "reports",
        "settings", "ai", "audit_logs",
        "settings.personal_info", "settings.leave", "settings.salary_view",
        "settings.salary_config", "settings.security"
    ]
    cur.executemany("INSERT INTO permissions (permission_name) VALUES (?)", [(p,) for p in permissions])

    # Mapping roles to permissions
    role_perms = {
        "admin": ["staff", "settings", "audit_logs", "billing"], # Billing just to see issues, no medical records
        "doctor": ["patients", "appointments", "medical_records", "medicines", "lab", "reports", "ai"],
        "nurse": ["patients", "appointments", "medical_records", "medical_orders", "rooms", "reports", "ai"],
        "receptionist": ["patients", "appointments", "rooms", "billing", "reports"],
        "pharmacist": ["medicines", "pharmacy", "reports", "ai"],
        "accountant": ["billing", "reports"],
        "lab_technician": ["lab", "reports", "ai"],
        "director": ["patients", "staff", "appointments", "rooms", "reports", "ai", "billing"],
        "cashier": ["billing"],
        "department_head": ["patients", "appointments", "medical_records", "medicines", "lab", "reports", "ai", "staff"],
        "hr_manager": ["staff",
                       "settings.personal_info", "settings.leave",
                       "settings.salary_view", "settings.salary_config", "settings.security"],
        # ── Support staff: limited settings only ──
        "security_guard":   ["settings.personal_info", "settings.leave", "settings.salary_view", "settings.security"],
        "ambulance_driver": ["settings.personal_info", "settings.leave", "settings.salary_view", "settings.security"],
        "janitor":          ["settings.personal_info", "settings.leave", "settings.salary_view", "settings.security"],
    }

    # ── Full-access roles get all settings sections ──
    roles_with_settings = ["doctor", "nurse", "receptionist", "pharmacist", "accountant",
                           "cashier", "lab_technician", "director", "department_head"]
    settings_perms = ["settings.personal_info", "settings.leave",
                      "settings.salary_view", "settings.salary_config", "settings.security"]
    for role in roles_with_settings:
        if role not in role_perms:
            role_perms[role] = []
        for perm in settings_perms:
            if perm not in role_perms[role]:
                role_perms[role].append(perm)

    # Fetch IDs
    cur.execute("SELECT id, role_name FROM roles")
    role_map = {row['role_name']: row['id'] for row in cur.fetchall()}
    cur.execute("SELECT id, permission_name FROM permissions")
    perm_map = {row['permission_name']: row['id'] for row in cur.fetchall()}

    for role_name, perms in role_perms.items():
        role_id = role_map[role_name]
        for p in perms:
            perm_id = perm_map[p]
            cur.execute("INSERT INTO role_permissions (role_id, permission_id) VALUES (?,?)", (role_id, perm_id))
    
    conn.commit()


def _seed_users(cur, conn):
    cur.execute("SELECT id FROM users WHERE username='admin'")
    if cur.fetchone():
        return

    cur.execute("SELECT id, role_name FROM roles")
    role_map = {row['role_name']: row['id'] for row in cur.fetchall()}

    demo_accounts = [
        ("admin",        "admin123",   "Quản trị viên",         "admin"),
        ("bacsi01",      "doctor123",  "BS. Nguyễn Văn An",     "doctor"),
        ("nurse01",      "nurse123",   "ĐD. Trần Thị Bình",     "nurse"),
        ("letan01",      "recept123",  "Lễ tân Lê Văn Cường",   "receptionist"),
        ("duocsi01",     "pharma123",  "DS. Phạm Thị Dung",     "pharmacist"),
        ("ketoan01",     "acc123",     "KT. Ngô Văn Em",        "accountant"),
        ("xetnghiem01",  "lab123",     "KTV. Hoàng Thị Phương", "lab_technician"),
        ("giamdoc",      "director123","GĐ. Vũ Đình Quang",     "director"),
        ("thungan01",    "cashier123", "TN. Nguyễn Thị Lệ",     "cashier"),
        ("truongkhoa01", "head123",    "TK. Phạm Văn B",        "department_head"),
        ("nhansu01",     "hr123",      "HR. Lê Thị C",          "hr_manager"),
        ("baove01",      "guard123",   "BV. Lê Văn Tuấn",       "security_guard"),
        ("laixe01",      "driver123",  "LX. Trần Hữu Đức",      "ambulance_driver"),
        ("vesinh01",     "janitor123", "VS. Nguyễn Thị Hạnh",   "janitor"),
    ]
    for username, password, full_name, role_name in demo_accounts:
        hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
        role_id = role_map[role_name]
        cur.execute("""
            INSERT INTO users (username, password, full_name, role_id)
            VALUES (?,?,?,?)
        """, (username, hashed, full_name, role_id))
    conn.commit()


def _seed_data(cur, conn):
    cur.execute("SELECT COUNT(*) FROM departments")
    if cur.fetchone()[0] > 0:
        return

    # Departments
    depts = [
        ("Nội khoa",   "Khoa Nội tổng quát"),
        ("Ngoại khoa", "Khoa Ngoại tổng quát"),
        ("Nhi khoa",   "Khoa Nhi"),
        ("Tim mạch",   "Khoa Tim mạch"),
        ("Thần kinh",  "Khoa Thần kinh"),
        ("Da liễu",    "Khoa Da liễu"),
        ("Xét nghiệm", "Khoa Xét nghiệm & Cận lâm sàng"),
        ("Dược",       "Khoa Dược"),
        ("Kế toán",    "Phòng Kế toán - Tài chính"),
    ]
    cur.executemany("INSERT INTO departments (name, description) VALUES (?,?)", depts)

    # Staff (linked to users 2-8)
    staff_rows = [
        (2,"BS001","BS. Nguyễn Văn An",   "Nam","1980-05-10","079080012345","0901234567","an.nv@hospital.vn",   "Đà Nẵng","Bác sĩ",          "Nội khoa",    1, "2010-01-15",25000000,5000000),
        (3,"DD001","ĐD. Trần Thị Bình",   "Nữ", "1995-08-20","079095056789","0987654321","binh.tt@hospital.vn", "Đà Nẵng","Y tá / Điều dưỡng","Nội khoa",   1, "2018-06-01",14000000,1500000),
        (4,"LT001","Lê Văn Cường",        "Nam","1993-03-12","079093011111","0912111222","cuong.lv@hospital.vn","Đà Nẵng","Lễ tân",           None,          None,"2020-03-01",12000000,1000000),
        (5,"DS001","DS. Phạm Thị Dung",   "Nữ", "1988-11-25","079088022222","0934222333","dung.pt@hospital.vn", "Đà Nẵng","Dược sĩ",          "Dược",        8, "2015-09-01",18000000,2000000),
        (6,"KT001","Ngô Văn Em",          "Nam","1990-07-08","079090033333","0945333444","em.nv@hospital.vn",   "Đà Nẵng","Kế toán",          "Kế toán",     9, "2019-01-15",15000000,1500000),
        (7,"XN001","KTV. Hoàng Thị Phương","Nữ","1992-04-17","079092044444","0956444555","phuong.ht@hospital.vn","Đà Nẵng","Xét nghiệm viên", "Xét nghiệm",  7, "2017-07-01",16000000,1800000),
        (8,"GD001","GĐ. Vũ Đình Quang",   "Nam","1970-09-30","079070055555","0967555666","quang.vd@hospital.vn","Đà Nẵng","Giám đốc",         "Nội khoa",    1, "2005-01-01",50000000,10000000),
        (12,"BV001","BV. Lê Văn Tuấn",    "Nam","1985-02-15","079085021111","0988111222",None,                 "Đà Nẵng","Bảo vệ",           None,          None,"2022-01-10",8000000,500000),
        (13,"LX001","LX. Trần Hữu Đức",   "Nam","1990-10-20","079090102222","0977222333",None,                 "Đà Nẵng","Lái xe cứu thương",None,          None,"2021-05-15",10000000,800000),
        (14,"VS001","VS. Nguyễn Thị Hạnh","Nữ", "1975-06-05","079075063333","0966333444",None,                 "Đà Nẵng","Nhân viên vệ sinh",None,          None,"2023-03-01",7000000,300000),
    ]
    cur.executemany("""
        INSERT INTO staff (user_id, staff_code, full_name, gender, birth_date, id_card,
            phone, email, address, position, specialization, department_id,
            hire_date, salary, bonus)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    """, staff_rows)

    # Patients
    patients = [
        ("BN0001","Trần Thị Mai",   "1990-03-15","Nữ", "079090034567","0912345678","Đà Nẵng","A+","BH1234567","2025-12-31","0911000001","Không có"),
        ("BN0002","Phạm Văn Hùng",  "1985-07-22","Nam","079085078901","0923456789","Quảng Nam","B+","BH2345678","2025-06-30","0922000002","Penicillin"),
        ("BN0003","Nguyễn Thị Lan", "2000-11-08","Nữ", "079000012345","0934567890","Huế",     "O-","","",          "",""),
        ("BN0004","Lê Văn Đức",     "1975-01-30","Nam","079075056789","0945678901","Đà Nẵng","AB+","BH3456789","2026-03-31","0944000004",""),
        ("BN0005","Ngô Thị Hương",  "1995-05-20","Nữ", "079095011111","0956789012","Đà Nẵng","A-","BH4567890","2026-09-30","",""),
        ("BN0006","Đặng Văn Minh",  "1968-12-03","Nam","079068022222","0967890123","Quảng Ngãi","B-","","",       "0967000006","Sulfa"),
    ]
    cur.executemany("""
        INSERT INTO patients (patient_code, full_name, birth_date, gender, id_card,
            phone, address, blood_type, insurance_id, insurance_exp, emergency_contact, allergies)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
    """, patients)

    # Rooms
    rooms = [
        ("P101","Khám",      4,1,"Trống"), ("P102","Khám",      4,1,"Trống"),
        ("P201","Thường",    2,2,"Đang dùng"), ("P202","Thường",2,2,"Trống"),
        ("V301","VIP",       1,3,"Trống"), ("ICU01","ICU",      2,1,"Đang dùng"),
        ("PT01","Phẫu thuật",1,1,"Trống"),
    ]
    cur.executemany("""
        INSERT INTO rooms (room_number, room_type, capacity, floor, status)
        VALUES (?,?,?,?,?)
    """, rooms)

    # Medicines
    meds = [
        ("MED0001","Paracetamol 500mg",  "Paracetamol",  "Giảm đau / Hạ sốt","viên",500,50,1500,"2026-12-31","Dược Hậu Giang"),
        ("MED0002","Amoxicillin 500mg",  "Amoxicillin",  "Kháng sinh",        "viên",200,30,5000,"2026-06-30","Pymepharco"),
        ("MED0003","Ibuprofen 400mg",    "Ibuprofen",    "Giảm đau / Hạ sốt","viên",300,30,3000,"2026-08-31","Imexpharm"),
        ("MED0004","Metformin 500mg",    "Metformin",    "Nội tiết",          "viên",150,20,4000,"2026-10-31","Stada"),
        ("MED0005","Amlodipine 5mg",     "Amlodipine",   "Tim mạch",          "viên", 80,20,8000,"2026-04-30","Sanofi"),
        ("MED0006","Omeprazole 20mg",    "Omeprazole",   "Tiêu hóa",          "viên",250,30,4500,"2026-11-30","DHG Pharma"),
        ("MED0007","Aspirin 81mg",       "Aspirin",      "Tim mạch",          "viên",400,50,2000,"2027-01-31","Bayer"),
        ("MED0008","Warfarin 5mg",       "Warfarin",     "Tim mạch",          "viên", 40,10,12000,"2026-05-31","Orion"),
        ("MED0009","Ciprofloxacin 500mg","Ciprofloxacin","Kháng sinh",        "viên",120,20,9000,"2026-07-31","Mekophar"),
        ("MED0010","Vitamin C 500mg",    "Ascorbic acid","Vitamin & Khoáng chất","viên",600,100,1000,"2027-06-30","DHG Pharma"),
    ]
    cur.executemany("""
        INSERT INTO medicines (medicine_code, name, generic_name, category, unit,
            stock_qty, min_stock, price, expiry_date, supplier)
        VALUES (?,?,?,?,?,?,?,?,?,?)
    """, meds)



    conn.commit()


if __name__ == "__main__":
    init_db()
