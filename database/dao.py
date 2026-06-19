import sqlite3
from database.schema import get_connection
from datetime import datetime


# ═══════════════════════════════════════════════════════════
#  AUTH
# ═══════════════════════════════════════════════════════════
def get_user_by_username(username: str):
    conn = get_connection()
    row = conn.execute("""
        SELECT u.*, r.role_name AS role
        FROM users u
        LEFT JOIN roles r ON u.role_id = r.id
        WHERE u.username=? AND u.is_active=1
    """, (username,)).fetchone()
    conn.close()
    return row


def get_staff_id_by_user_id(user_id: int):
    """Map a users.id -> staff.id. Returns None if no linked staff row found."""
    if user_id is None:
        return None
    conn = get_connection()
    row = conn.execute(
        "SELECT id FROM staff WHERE user_id=? AND is_active=1 LIMIT 1", (user_id,)
    ).fetchone()
    conn.close()
    return row["id"] if row else None


def log_action(user_id, action, table_name=None, record_id=None, old_value=None, new_value=None, detail=None):
    conn = get_connection()
    conn.execute("""
        INSERT INTO audit_log (user_id, action, table_name, record_id, old_value, new_value, detail)
        VALUES (?,?,?,?,?,?,?)
    """, (user_id, action, table_name, record_id, old_value, new_value, detail))
    conn.commit()
    conn.close()


# ═══════════════════════════════════════════════════════════
#  USERS & ACCOUNT MANAGEMENT
# ═══════════════════════════════════════════════════════════
def get_staff_without_accounts():
    conn = get_connection()
    rows = conn.execute("""
        SELECT s.id, s.staff_code, s.full_name, s.position
        FROM staff s
        WHERE s.user_id IS NULL AND s.is_active=1
    """).fetchall()
    conn.close()
    return rows

def create_user_for_staff(staff_id: int, username: str, password_hash: str, role_id: int, must_change_password: int = 1):
    conn = get_connection()
    try:
        # Check if username exists
        if conn.execute("SELECT id FROM users WHERE username=?", (username,)).fetchone():
            raise ValueError("Tên đăng nhập đã tồn tại")
        
        staff = conn.execute("SELECT full_name FROM staff WHERE id=?", (staff_id,)).fetchone()
        
        cur = conn.execute("""
            INSERT INTO users (username, password, full_name, role_id, must_change_password)
            VALUES (?, ?, ?, ?, ?)
        """, (username, password_hash, staff["full_name"], role_id, must_change_password))
        
        new_user_id = cur.lastrowid
        
        conn.execute("UPDATE staff SET user_id=? WHERE id=?", (new_user_id, staff_id))
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()


def update_user_password(user_id: int, new_hash: str, clear_force_change: bool = True):
    """Update a user's password hash. Optionally clear the must_change_password flag."""
    conn = get_connection()
    try:
        if clear_force_change:
            conn.execute(
                "UPDATE users SET password=?, must_change_password=0 WHERE id=?",
                (new_hash, user_id)
            )
        else:
            conn.execute("UPDATE users SET password=? WHERE id=?", (new_hash, user_id))
        conn.commit()
    finally:
        conn.close()


def get_staff_profile(user_id: int):
    """Return the staff row linked to a user account, or None."""
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM staff WHERE user_id=? AND is_active=1 LIMIT 1", (user_id,)
    ).fetchone()
    conn.close()
    return row


def get_all_roles():
    conn = get_connection()
    rows = conn.execute("SELECT * FROM roles ORDER BY id").fetchall()
    conn.close()
    return rows

# ═══════════════════════════════════════════════════════════
#  PATIENTS
# ═══════════════════════════════════════════════════════════
def _next_patient_code():
    conn = get_connection()
    row = conn.execute(
        "SELECT patient_code FROM patients ORDER BY id DESC LIMIT 1"
    ).fetchone()
    conn.close()
    if row:
        num = int(row["patient_code"].replace("BN", "")) + 1
    else:
        num = 1
    return f"BN{num:04d}"


def get_all_patients(search="", gender_filter="", blood_filter=""):
    conn = get_connection()
    query = """
        SELECT id, patient_code, full_name, birth_date, gender,
               phone, blood_type, insurance_id, created_at
        FROM patients WHERE 1=1
    """
    params = []
    if search:
        query += """ AND (
            full_name LIKE ? OR patient_code LIKE ?
            OR phone LIKE ? OR birth_date LIKE ?
        )"""
        like = f"%{search}%"
        params += [like, like, like, like]
    if gender_filter:
        query += " AND gender=?"
        params.append(gender_filter)
    if blood_filter:
        query += " AND blood_type=?"
        params.append(blood_filter)
    query += " ORDER BY id DESC"
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return rows


def get_patient_by_id(patient_id: int):
    conn = get_connection()
    row = conn.execute("SELECT * FROM patients WHERE id=?", (patient_id,)).fetchone()
    conn.close()
    return row


def add_patient(data: dict) -> int:
    conn = get_connection()
    try:
        code = _next_patient_code()
        cur = conn.execute("""
            INSERT INTO patients
                (patient_code, full_name, birth_date, gender, id_card, phone, address,
                 blood_type, insurance_id, insurance_exp, emergency_contact, allergies, notes)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (code, data["full_name"], data.get("birth_date"), data.get("gender"),
              data.get("id_card"), data.get("phone"), data.get("address"),
              data.get("blood_type"), data.get("insurance_id"), data.get("insurance_exp"),
              data.get("emergency_contact"), data.get("allergies"), data.get("notes")))
        conn.commit()
        return cur.lastrowid
    except sqlite3.IntegrityError as e:
        conn.rollback()
        raise ValueError(f"Không thể lưu bệnh nhân — dữ liệu không hợp lệ hoặc bị trùng (CMND/CCCD?): {e}") from e
    finally:
        conn.close()


def update_patient(patient_id: int, data: dict):
    conn = get_connection()
    try:
        conn.execute("""
            UPDATE patients SET
                full_name=?, birth_date=?, gender=?, id_card=?, phone=?, address=?,
                blood_type=?, insurance_id=?, insurance_exp=?, emergency_contact=?,
                allergies=?, notes=?, updated_at=datetime('now','localtime')
            WHERE id=?
        """, (data["full_name"], data.get("birth_date"), data.get("gender"),
              data.get("id_card"), data.get("phone"), data.get("address"),
              data.get("blood_type"), data.get("insurance_id"), data.get("insurance_exp"),
              data.get("emergency_contact"), data.get("allergies"), data.get("notes"),
              patient_id))
        conn.commit()
    except sqlite3.IntegrityError as e:
        conn.rollback()
        raise ValueError(f"Không thể cập nhật bệnh nhân — dữ liệu không hợp lệ hoặc bị trùng (CMND/CCCD?): {e}") from e
    finally:
        conn.close()

def delete_patient(patient_id: int):
    conn = get_connection()
    conn.execute("DELETE FROM patients WHERE id=?", (patient_id,))
    conn.commit()
    conn.close()


def get_patient_medical_history(patient_id: int):
    conn = get_connection()
    rows = conn.execute("""
        SELECT mr.*, s.full_name AS doctor_name
        FROM medical_records mr
        LEFT JOIN staff s ON mr.doctor_id = s.id
        WHERE mr.patient_id=?
        ORDER BY mr.visit_date DESC
    """, (patient_id,)).fetchall()
    conn.close()
    return rows


def add_medical_record(data: dict) -> int:
    conn = get_connection()
    cur = conn.execute("""
        INSERT INTO medical_records
            (patient_id, doctor_id, visit_date, symptoms, diagnosis,
             treatment_plan, notes, follow_up_date,
             height, weight, blood_pressure, heart_rate, temperature, spo2,
             medical_history, conclusion)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    """, (data["patient_id"], data.get("doctor_id"),
          data.get("visit_date", datetime.now().strftime("%Y-%m-%d %H:%M")),
          data.get("symptoms"), data.get("diagnosis"),
          data.get("treatment_plan"), data.get("notes"), data.get("follow_up_date"),
          data.get("height"), data.get("weight"), data.get("blood_pressure"),
          data.get("heart_rate"), data.get("temperature"), data.get("spo2"),
          data.get("medical_history"), data.get("conclusion")))
    conn.commit()
    rid = cur.lastrowid
    conn.close()
    return rid

def delete_medical_record(record_id: int):
    """Compensating action: undo a freshly written medical_records row.
    Called when save_prescription() raises ValueError (stock failure) so the DB
    is not left with an orphaned medical_records row that has no prescription.
    """
    conn = get_connection()
    try:
        conn.execute("DELETE FROM medical_records WHERE id=?", (record_id,))
        conn.commit()
    finally:
        conn.close()


# ═══════════════════════════════════════════════════════════
#  STAFF
# ═══════════════════════════════════════════════════════════
def _next_staff_code(position: str):
    prefix_map = {
        "B\u00e1c s\u0129": "BS", "Y t\u00e1 / \u0110i\u1ec1u d\u01b0\u1ee1ng": "YT", "L\u1ec5 t\u00e2n": "LT",
        "D\u01b0\u1ee3c s\u0129": "DS", "K\u1ebf to\u00e1n": "KT", "X\u00e9t nghi\u1ec7m vi\u00ean": "XN", "Gi\u00e1m \u0111\u1ed1c": "GD", "Qu\u1ea3n tr\u1ecb vi\u00ean": "QT"
    }
    prefix = prefix_map.get(position, "NV")
    conn = get_connection()
    row = conn.execute(
        "SELECT staff_code FROM staff WHERE staff_code LIKE ? ORDER BY id DESC LIMIT 1",
        (f"{prefix}%",)
    ).fetchone()
    conn.close()
    if row:
        num = int(row["staff_code"].replace(prefix, "")) + 1
    else:
        num = 1
    return f"{prefix}{num:03d}"


def get_all_staff(search="", position_filter="", dept_filter=None):
    conn = get_connection()
    query = """
        SELECT s.*, d.name AS dept_name
        FROM staff s
        LEFT JOIN departments d ON s.department_id = d.id
        WHERE s.is_active=1
    """
    params = []
    if search:
        query += " AND (s.full_name LIKE ? OR s.staff_code LIKE ? OR s.phone LIKE ?)"
        like = f"%{search}%"
        params += [like, like, like]
    if position_filter:
        query += " AND s.position=?"
        params.append(position_filter)
    if dept_filter:
        query += " AND s.department_id=?"
        params.append(dept_filter)
    query += " ORDER BY s.id DESC"
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return rows


def get_staff_by_id(staff_id: int):
    conn = get_connection()
    row = conn.execute("""
        SELECT s.*, d.name AS dept_name
        FROM staff s LEFT JOIN departments d ON s.department_id=d.id
        WHERE s.id=?
    """, (staff_id,)).fetchone()
    conn.close()
    return row


def get_doctors():
    conn = get_connection()
    rows = conn.execute("""
        SELECT id, full_name, specialization FROM staff
        WHERE position IN ('Bác sĩ', 'Giám đốc', 'Trưởng khoa') AND is_active=1 ORDER BY full_name
    """).fetchall()
    conn.close()
    return rows


def add_staff(data: dict) -> int:
    conn = get_connection()
    code = _next_staff_code(data.get("position", ""))
    cur = conn.execute("""
        INSERT INTO staff (user_id, staff_code, full_name, gender, birth_date, id_card,
            phone, email, address, position, specialization, department_id,
            hire_date, salary, bonus, work_schedule, notes)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    """, (data.get("user_id"), code, data["full_name"], data.get("gender"),
          data.get("birth_date"), data.get("id_card"), data.get("phone"),
          data.get("email"), data.get("address"), data.get("position"),
          data.get("specialization"), data.get("department_id"),
          data.get("hire_date"), data.get("salary", 0), data.get("bonus", 0),
          data.get("work_schedule"), data.get("notes")))
    conn.commit()
    sid = cur.lastrowid
    conn.close()
    return sid


def update_staff(staff_id: int, data: dict):
    conn = get_connection()
    conn.execute("""
        UPDATE staff SET full_name=?, gender=?, birth_date=?, id_card=?,
            phone=?, email=?, address=?, position=?, specialization=?,
            department_id=?, hire_date=?, salary=?, bonus=?, work_schedule=?,
            notes=?
        WHERE id=?
    """, (data["full_name"], data.get("gender"), data.get("birth_date"),
          data.get("id_card"), data.get("phone"), data.get("email"),
          data.get("address"), data.get("position"), data.get("specialization"),
          data.get("department_id"), data.get("hire_date"),
          data.get("salary", 0), data.get("bonus", 0),
          data.get("work_schedule"), data.get("notes"), staff_id))
    conn.commit()
    conn.close()


def delete_staff(staff_id: int):
    conn = get_connection()
    conn.execute("UPDATE staff SET is_active=0 WHERE id=?", (staff_id,))
    conn.commit()
    conn.close()


def get_departments():
    conn = get_connection()
    rows = conn.execute("SELECT * FROM departments ORDER BY name").fetchall()
    conn.close()
    return rows


# ═══════════════════════════════════════════════════════════
#  DASHBOARD STATS
# ═══════════════════════════════════════════════════════════
def get_dashboard_stats():
    conn = get_connection()
    today = datetime.now().strftime("%Y-%m-%d")
    stats = {
        "total_patients": conn.execute("SELECT COUNT(*) FROM patients").fetchone()[0],
        "total_staff":    conn.execute("SELECT COUNT(*) FROM staff WHERE is_active=1").fetchone()[0],
        "today_appointments": conn.execute(
            "SELECT COUNT(*) FROM appointments WHERE appointment_date=? AND status!='Huỷ'",
            (today,)
        ).fetchone()[0],
        "low_stock_medicines": conn.execute(
            "SELECT COUNT(*) FROM medicines WHERE stock_qty <= min_stock AND is_active=1"
        ).fetchone()[0],
    }
    conn.close()
    return stats


# ═══════════════════════════════════════════════════════════
#  APPOINTMENTS
# ═══════════════════════════════════════════════════════════
def get_all_appointments(search="", status_filter="", date_filter=None):
    conn = get_connection()
    query = """
        SELECT a.*,
               p.full_name  AS patient_name,
               p.patient_code,
               s.full_name  AS doctor_name
        FROM appointments a
        LEFT JOIN patients p ON a.patient_id = p.id
        LEFT JOIN staff    s ON a.doctor_id  = s.id
        WHERE 1=1
    """
    params = []
    if search:
        query += " AND (p.full_name LIKE ? OR s.full_name LIKE ?)"
        like = f"%{search}%"
        params += [like, like]
    if status_filter:
        query += " AND a.status=?"
        params.append(status_filter)
    if date_filter:
        query += " AND a.appointment_date=?"
        params.append(date_filter)
    query += " ORDER BY a.appointment_date DESC, a.appointment_time"
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return rows


def get_appointment_by_id(appt_id: int):
    conn = get_connection()
    row = conn.execute("""
        SELECT a.*, p.full_name AS patient_name, s.full_name AS doctor_name
        FROM appointments a
        LEFT JOIN patients p ON a.patient_id=p.id
        LEFT JOIN staff    s ON a.doctor_id =s.id
        WHERE a.id=?
    """, (appt_id,)).fetchone()
    conn.close()
    return row


def add_appointment(data: dict) -> int:
    conn = get_connection()
    cur = conn.execute("""
        INSERT INTO appointments
            (patient_id, doctor_id, appointment_date, appointment_time,
             reason, status, is_followup, parent_appointment_id, notes)
        VALUES (?,?,?,?,?,?,?,?,?)
    """, (data["patient_id"], data["doctor_id"],
          data["appointment_date"], data["appointment_time"],
          data.get("reason"), data.get("status", "Chờ"),
          data.get("is_followup", 0), data.get("parent_appointment_id"),
          data.get("notes")))
    conn.commit()
    aid = cur.lastrowid
    conn.close()
    return aid


def update_appointment(appt_id: int, data: dict):
    conn = get_connection()
    conn.execute("""
        UPDATE appointments SET
            patient_id=?, doctor_id=?, appointment_date=?,
            appointment_time=?, reason=?, status=?, notes=?
        WHERE id=?
    """, (data["patient_id"], data["doctor_id"],
          data["appointment_date"], data["appointment_time"],
          data.get("reason"), data.get("status"), data.get("notes"), appt_id))
    conn.commit()
    conn.close()


def update_appointment_status(appt_id: int, status: str):
    conn = get_connection()
    conn.execute("UPDATE appointments SET status=? WHERE id=?", (status, appt_id))
    conn.commit()
    conn.close()

def auto_reschedule_missed_appointments():
    from datetime import date
    conn = get_connection()
    cur = conn.cursor()
    today_str = date.today().isoformat()
    
    query = """
        UPDATE appointments
        SET appointment_date = ?
        WHERE status IN ('Chờ', 'Đang khám')
          AND appointment_date < ?
    """
    cur.execute(query, (today_str, today_str))
    conn.commit()
    conn.close()


# ═══════════════════════════════════════════════════════════
#  MEDICINES
# ═══════════════════════════════════════════════════════════
def _next_medicine_code():
    conn = get_connection()
    row = conn.execute(
        "SELECT medicine_code FROM medicines ORDER BY id DESC LIMIT 1"
    ).fetchone()
    conn.close()
    if row:
        num = int(row["medicine_code"].replace("MED", "")) + 1
    else:
        num = 1
    return f"MED{num:04d}"


def get_all_medicines(search="", category="", low_stock=False, near_expiry=False):
    conn = get_connection()
    from datetime import datetime, timedelta
    query = "SELECT * FROM medicines WHERE is_active=1"
    params = []
    if search:
        query += " AND (name LIKE ? OR generic_name LIKE ?)"
        like = f"%{search}%"
        params += [like, like]
    if category:
        query += " AND category=?"
        params.append(category)
    if low_stock:
        query += " AND stock_qty <= min_stock"
    if near_expiry:
        cutoff = (datetime.now() + timedelta(days=90)).strftime("%Y-%m-%d")
        query += " AND expiry_date <= ?"
        params.append(cutoff)
    query += " ORDER BY name"
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return rows


def get_medicine_by_id(med_id: int):
    conn = get_connection()
    row = conn.execute("SELECT * FROM medicines WHERE id=?", (med_id,)).fetchone()
    conn.close()
    return row


def add_medicine(data: dict) -> int:
    conn = get_connection()
    code = _next_medicine_code()
    cur = conn.execute("""
        INSERT INTO medicines
            (medicine_code, name, generic_name, category, unit, stock_qty,
             min_stock, price, expiry_date, supplier, description)
        VALUES (?,?,?,?,?,?,?,?,?,?,?)
    """, (code, data["name"], data.get("generic_name"), data.get("category"),
          data.get("unit"), data.get("stock_qty", 0), data.get("min_stock", 10),
          data.get("price", 0), data.get("expiry_date"), data.get("supplier"),
          data.get("description")))
    conn.commit()
    mid = cur.lastrowid
    conn.close()
    return mid


def update_medicine(med_id: int, data: dict):
    conn = get_connection()
    conn.execute("""
        UPDATE medicines SET name=?, generic_name=?, category=?, unit=?,
            stock_qty=?, min_stock=?, price=?, expiry_date=?, supplier=?,
            description=?, updated_at=datetime('now','localtime')
        WHERE id=?
    """, (data["name"], data.get("generic_name"), data.get("category"),
          data.get("unit"), data.get("stock_qty", 0), data.get("min_stock", 10),
          data.get("price", 0), data.get("expiry_date"), data.get("supplier"),
          data.get("description"), med_id))
    conn.commit()
    conn.close()


def delete_medicine(med_id: int):
    conn = get_connection()
    conn.execute("UPDATE medicines SET is_active=0 WHERE id=?", (med_id,))
    conn.commit()
    conn.close()


# ═══════════════════════════════════════════════════════════
#  PRESCRIPTIONS
# ═══════════════════════════════════════════════════════════
def save_prescription(data: dict) -> int:
    """
    Save a prescription inside a single transaction.
    Raises ValueError for any medicine whose stock_qty < quantity requested,
    so the caller can surface a meaningful error instead of silently undershooting.
    """
    conn = get_connection()
    try:
        # BEGIN IMMEDIATE locks the DB for writing immediately, so no concurrent
        # writer can change stock_qty between our pre-flight SELECT and the UPDATE.
        conn.execute("BEGIN IMMEDIATE")
        # Pre-flight: verify stock for every line item BEFORE writing anything
        out_of_stock = []
        for item in data.get("items", []):
            row = conn.execute(
                "SELECT name, stock_qty FROM medicines WHERE id=?",
                (item["medicine_id"],)
            ).fetchone()
            if row is None:
                out_of_stock.append(f"ID {item['medicine_id']}: thuoc khong ton tai")
            elif row["stock_qty"] < item["quantity"]:
                out_of_stock.append(
                    f"{row['name']}: yeu cau {item['quantity']}, ton kho {row['stock_qty']}"
                )
        if out_of_stock:
            raise ValueError(
                "Khong du ton kho cho cac thuoc sau:\n" + "\n".join(out_of_stock)
            )

        # All stock checks passed -> write prescription header
        cur = conn.execute("""
            INSERT INTO prescriptions (medical_record_id, doctor_id, notes)
            VALUES (?,?,?)
        """, (data.get("medical_record_id"), data.get("doctor_id"), data.get("notes")))
        presc_id = cur.lastrowid

        for item in data.get("items", []):
            conn.execute("""
                INSERT INTO prescription_items
                    (prescription_id, medicine_id, quantity, dosage, duration_days, notes)
                VALUES (?,?,?,?,?,?)
            """, (presc_id, item["medicine_id"], item["quantity"],
                  item.get("dosage"), item.get("duration_days"), item.get("notes")))

            # Deduct stock (guaranteed to succeed after pre-flight)
            rows_affected = conn.execute("""
                UPDATE medicines SET stock_qty = stock_qty - ?
                WHERE id=? AND stock_qty >= ?
            """, (item["quantity"], item["medicine_id"], item["quantity"])).rowcount

            # Belt-and-suspenders: if a concurrent write beat us, rollback
            if rows_affected == 0:
                raise ValueError(
                    f"Ton kho thay doi trong khi luu don thuoc. Vui long thu lai."
                )

        conn.commit()
        return presc_id
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def get_all_prescriptions():
    conn = get_connection()
    rows = conn.execute("""
        SELECT pr.id, pr.issue_date, pr.notes, pr.status,
               p.full_name AS patient_name,
               s.full_name AS doctor_name,
               COUNT(pi.id) AS item_count
        FROM prescriptions pr
        LEFT JOIN medical_records mr ON pr.medical_record_id = mr.id
        LEFT JOIN patients p ON mr.patient_id = p.id
        LEFT JOIN staff    s ON pr.doctor_id = s.id
        LEFT JOIN prescription_items pi ON pr.id = pi.prescription_id
        GROUP BY pr.id
        ORDER BY pr.issue_date DESC
    """).fetchall()
    conn.close()
    return rows

def get_prescription_by_id(presc_id: int):
    conn = get_connection()
    row = conn.execute("""
        SELECT pr.*, mr.patient_id
        FROM prescriptions pr
        LEFT JOIN medical_records mr ON pr.medical_record_id = mr.id
        WHERE pr.id = ?
    """, (presc_id,)).fetchone()
    conn.close()
    return row

def dispense_prescription(presc_id: int, pharmacist_id: int):
    conn = get_connection()
    from datetime import datetime
    conn.execute("""
        UPDATE prescriptions SET status='Đã phát', pharmacist_id=?, dispensed_date=?
        WHERE id=?
    """, (pharmacist_id, datetime.now().strftime("%Y-%m-%d %H:%M"), presc_id))
    conn.commit()
    conn.close()


def get_prescription_items(presc_id: int):
    conn = get_connection()
    rows = conn.execute("""
        SELECT pi.*, m.name, m.unit
        FROM prescription_items pi
        JOIN medicines m ON pi.medicine_id = m.id
        WHERE pi.prescription_id=?
    """, (presc_id,)).fetchall()
    conn.close()
    return rows


# ═══════════════════════════════════════════════════════════
#  STATISTICS QUERIES (for charts)
# ═══════════════════════════════════════════════════════════
def get_patients_by_month(months: int = 12):
    """Return (month_label, count) for last N months."""
    conn = get_connection()
    rows = conn.execute("""
        SELECT strftime('%m/%Y', created_at) AS month,
               COUNT(*) AS cnt
        FROM patients
        WHERE created_at >= date('now', ?)
        GROUP BY month
        ORDER BY created_at
    """, (f"-{months} months",)).fetchall()
    conn.close()
    return [(r["month"], r["cnt"]) for r in rows]


def get_top_diagnoses(month: int = None, year: int = None, limit: int = 8):
    """Return (diagnosis, count) top N diagnoses."""
    conn = get_connection()
    query = """
        SELECT diagnosis, COUNT(*) AS cnt
        FROM medical_records
        WHERE diagnosis IS NOT NULL AND diagnosis != ''
    """
    params = []
    if month and year:
        query += " AND strftime('%m', visit_date) = ? AND strftime('%Y', visit_date) = ?"
        params.extend([f"{int(month):02d}", str(year)])
        
    query += " GROUP BY diagnosis ORDER BY cnt DESC LIMIT ?"
    params.append(limit)
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [(r["diagnosis"], r["cnt"]) for r in rows]


def get_appointments_by_doctor(filter_type=None, month=None, year=None, week_str=None):
    """Return (doctor_name, count) of appointments per doctor."""
    conn = get_connection()
    query = """
        SELECT s.full_name, COUNT(a.id) AS cnt
        FROM appointments a
        JOIN staff s ON a.doctor_id = s.id
        WHERE a.status != 'Huỷ'
    """
    params = []
    if filter_type == "month" and month and year:
        query += " AND strftime('%m', a.appointment_date) = ? AND strftime('%Y', a.appointment_date) = ?"
        params.extend([f"{int(month):02d}", str(year)])
    elif filter_type == "week" and week_str:
        query += " AND strftime('%Y-%W', a.appointment_date) = ?"
        params.append(week_str)

    query += " GROUP BY a.doctor_id ORDER BY cnt DESC LIMIT 8"
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [(r["full_name"], r["cnt"]) for r in rows]


def get_appointment_status_stats(filter_type="month", month=None, year=None, week_str=None):
    """Return (status, count) for the selected month or week."""
    conn = get_connection()
    query = """
        SELECT status, COUNT(id) AS cnt
        FROM appointments
        WHERE 1=1
    """
    params = []
    if filter_type == "month" and month and year:
        query += " AND strftime('%m', appointment_date) = ? AND strftime('%Y', appointment_date) = ?"
        params.extend([f"{int(month):02d}", str(year)])
    elif filter_type == "week" and week_str:
        query += " AND strftime('%Y-%W', appointment_date) = ?"
        params.append(week_str)

    query += " GROUP BY status ORDER BY cnt DESC"
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [(r["status"] or "Chờ", r["cnt"]) for r in rows]


def get_appointment_monthly_counts(year: int):
    """Return (month_label, count) for each month in the selected year."""
    conn = get_connection()
    query = """
        SELECT strftime('%m', appointment_date) AS month, COUNT(id) AS cnt
        FROM appointments
        WHERE strftime('%Y', appointment_date) = ? AND status != 'Huỷ'
        GROUP BY month
        ORDER BY month
    """
    rows = conn.execute(query, (str(year),)).fetchall()
    conn.close()
    
    # Initialize all 12 months with 0
    results_dict = {f"{m:02d}": 0 for m in range(1, 13)}
    for r in rows:
        if r["month"]:
            results_dict[r["month"]] = r["cnt"]
            
    return [(f"Tháng {int(m)}", cnt) for m, cnt in results_dict.items()]


def get_revenue_by_time(filter_type="month", month=None, year=None, week_str=None):
    """Return (day_label, revenue) for the selected month or week."""
    conn = get_connection()
    query = """
        SELECT bill_date AS full_date,
               SUM(paid_amount) AS total_rev
        FROM bills
        WHERE status != 'Huỷ'
    """
    params = []
    if filter_type == "month" and month and year:
        query += " AND strftime('%m', bill_date) = ? AND strftime('%Y', bill_date) = ?"
        params.extend([f"{int(month):02d}", str(year)])
    elif filter_type == "week" and week_str:
        query += " AND strftime('%Y-%W', bill_date) = ?"
        params.append(week_str)
    else:
        from datetime import datetime
        now = datetime.now()
        query += " AND strftime('%m', bill_date) = ? AND strftime('%Y', bill_date) = ?"
        params.extend([f"{now.month:02d}", str(now.year)])

    query += " GROUP BY strftime('%Y-%m-%d', bill_date) ORDER BY full_date"
    rows = conn.execute(query, params).fetchall()
    conn.close()
    results = []
    for r in rows:
        dt = r["full_date"][:10]
        rev = r["total_rev"] or 0
        dt_formatted = dt[8:10] + "/" + dt[5:7]
        results.append((dt_formatted, rev))
    return results


# ═══════════════════════════════════════════════════════════
#  NURSING NOTES
# ═══════════════════════════════════════════════════════════
def get_latest_nursing_note_for_patient_today(patient_id: int):
    conn = get_connection()
    from datetime import datetime
    today = datetime.now().strftime("%Y-%m-%d")
    row = conn.execute("""
        SELECT * FROM nursing_notes 
        WHERE patient_id=? AND date(note_date)=? 
        ORDER BY note_date DESC LIMIT 1
    """, (patient_id, today)).fetchone()
    conn.close()
    return dict(row) if row else None

def get_nursing_notes(search="", status_filter=""):
    conn = get_connection()
    query = """
        SELECT nn.*, p.full_name AS patient_name, s.full_name AS nurse_name
        FROM nursing_notes nn
        LEFT JOIN patients p ON nn.patient_id = p.id
        LEFT JOIN staff    s ON nn.nurse_id   = s.id
        WHERE 1=1
    """
    params = []
    if search:
        query += " AND p.full_name LIKE ?"
        params.append(f"%{search}%")
    if status_filter:
        query += " AND nn.patient_status=?"
        params.append(status_filter)
    query += " ORDER BY nn.note_date DESC"
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return rows

def get_nursing_note_by_id(nid):
    conn = get_connection()
    row = conn.execute("SELECT * FROM nursing_notes WHERE id=?", (nid,)).fetchone()
    conn.close()
    return row

def add_nursing_note(data: dict) -> int:
    conn = get_connection()
    cur = conn.execute("""
        INSERT INTO nursing_notes (patient_id, nurse_id, note_date, vital_signs,
            care_given, patient_status, notes)
        VALUES (?,?,?,?,?,?,?)
    """, (data["patient_id"], data.get("nurse_id"), data.get("note_date"),
          data.get("vital_signs"), data.get("care_given"),
          data.get("patient_status"), data.get("notes")))
    conn.commit(); nid = cur.lastrowid; conn.close()
    return nid

def update_nursing_note(nid: int, data: dict):
    conn = get_connection()
    conn.execute("""
        UPDATE nursing_notes SET vital_signs=?, care_given=?, patient_status=?, notes=?
        WHERE id=?
    """, (data.get("vital_signs"), data.get("care_given"),
          data.get("patient_status"), data.get("notes"), nid))
    conn.commit(); conn.close()


# ═══════════════════════════════════════════════════════════
#  LAB TESTS
# ═══════════════════════════════════════════════════════════
def get_all_lab_tests(search="", status_filter=""):
    conn = get_connection()
    query = """
        SELECT lt.*,
               p.full_name AS patient_name,
               d.full_name AS doctor_name,
               t.full_name AS technician_name
        FROM lab_tests lt
        LEFT JOIN patients p ON lt.patient_id    = p.id
        LEFT JOIN staff    d ON lt.doctor_id     = d.id
        LEFT JOIN staff    t ON lt.technician_id = t.id
        WHERE 1=1
    """
    params = []
    if search:
        query += " AND (p.full_name LIKE ? OR lt.test_type LIKE ?)"
        like = f"%{search}%"; params += [like, like]
    if status_filter:
        query += " AND lt.status=?"; params.append(status_filter)
    query += " ORDER BY lt.ordered_date DESC"
    rows = conn.execute(query, params).fetchall()
    conn.close(); return rows

def get_lab_test_by_id(tid):
    conn = get_connection()
    row = conn.execute("SELECT * FROM lab_tests WHERE id=?", (tid,)).fetchone()
    conn.close(); return row

def add_lab_test(data: dict) -> int:
    conn = get_connection()
    cur = conn.execute("""
        INSERT INTO lab_tests (patient_id, doctor_id, technician_id, test_type,
            ordered_date, result_date, result, status, notes)
        VALUES (?,?,?,?,?,?,?,?,?)
    """, (data.get("patient_id"), data.get("doctor_id"), data.get("technician_id"),
          data.get("test_type"), data.get("ordered_date"), data.get("result_date"),
          data.get("result"), data.get("status","Chờ"), data.get("notes")))
    conn.commit(); tid = cur.lastrowid; conn.close(); return tid

def update_lab_test(tid: int, data: dict):
    conn = get_connection()
    conn.execute("""
        UPDATE lab_tests SET technician_id=?, result_date=?, result=?, status=?, notes=?
        WHERE id=?
    """, (data.get("technician_id"), data.get("result_date"), data.get("result"),
          data.get("status"), data.get("notes"), tid))
    conn.commit(); conn.close()


# ═══════════════════════════════════════════════════════════
#  BILLING
# ═══════════════════════════════════════════════════════════
def get_all_bills(search="", status_filter=""):
    conn = get_connection()
    query = """
        SELECT b.*, p.full_name AS patient_name
        FROM bills b LEFT JOIN patients p ON b.patient_id=p.id
        WHERE 1=1
    """
    params = []
    if search:
        query += " AND p.full_name LIKE ?"; params.append(f"%{search}%")
    if status_filter:
        query += " AND b.status=?"; params.append(status_filter)
    query += " ORDER BY b.bill_date DESC"
    rows = conn.execute(query, params).fetchall()
    conn.close(); return rows

def get_bill_by_id(bid):
    conn = get_connection()
    row = conn.execute("SELECT * FROM bills WHERE id=?", (bid,)).fetchone()
    conn.close(); return row

def get_bill_items(bid):
    conn = get_connection()
    rows = conn.execute("SELECT * FROM bill_items WHERE bill_id=?", (bid,)).fetchall()
    conn.close(); return rows

def add_bill(data: dict) -> int:
    conn = get_connection()
    cur = conn.execute("""
        INSERT INTO bills (patient_id, accountant_id, total_amount, paid_amount,
            discount, insurance_cover, payment_method, status, notes)
        VALUES (?,?,?,?,?,?,?,?,?)
    """, (data["patient_id"], data.get("accountant_id"), data.get("total_amount",0),
          data.get("paid_amount",0), data.get("discount",0),
          data.get("insurance_cover",0), data.get("payment_method"),
          data.get("status","Chưa thanh toán"), data.get("notes")))
    bid = cur.lastrowid
    for item in data.get("items",[]):
        conn.execute("""
            INSERT INTO bill_items (bill_id, item_type, description, quantity, unit_price, total)
            VALUES (?,?,?,?,?,?)
        """, (bid, item["item_type"], item["description"],
              item["quantity"], item["unit_price"], item["total"]))
    conn.commit(); conn.close(); return bid

def update_bill(bid: int, data: dict):
    """Update bill header AND fully sync its bill_items in one transaction."""
    conn = get_connection()
    try:
        conn.execute("""
            UPDATE bills SET total_amount=?, paid_amount=?, discount=?,
                insurance_cover=?, payment_method=?, status=?, notes=?
            WHERE id=?
        """, (data.get("total_amount", 0), data.get("paid_amount", 0),
              data.get("discount", 0), data.get("insurance_cover", 0),
              data.get("payment_method"), data.get("status"),
              data.get("notes"), bid))

        # Sync items: delete all old rows, re-insert current list
        conn.execute("DELETE FROM bill_items WHERE bill_id=?", (bid,))
        for item in data.get("items", []):
            conn.execute("""
                INSERT INTO bill_items (bill_id, item_type, description, quantity, unit_price, total)
                VALUES (?,?,?,?,?,?)
            """, (bid, item["item_type"], item["description"],
                  item["quantity"], item["unit_price"], item["total"]))

        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def get_monthly_revenue(months=6):
    """Return (month_label, revenue) for last N months based on paid bills."""
    conn = get_connection()
    rows = conn.execute("""
        SELECT strftime('%m/%Y', bill_date) AS month,
               SUM(paid_amount) AS total_rev
        FROM bills
        WHERE status != 'Huỷ' AND bill_date >= date('now', ?)
        GROUP BY month
        ORDER BY bill_date
    """, (f"-{months} months",)).fetchall()
    conn.close()
    return [(r["month"], r["total_rev"] or 0) for r in rows]


# ═══════════════════════════════════════════════════════════
#  NURSING NOTES
# ═══════════════════════════════════════════════════════════
def get_nursing_notes(search="", status_filter=""):
    conn = get_connection()
    query = """
        SELECT nn.*, p.full_name AS patient_name, s.full_name AS nurse_name
        FROM nursing_notes nn
        LEFT JOIN patients p ON nn.patient_id = p.id
        LEFT JOIN staff    s ON nn.nurse_id   = s.id
        WHERE 1=1
    """
    params = []
    if search:
        query += " AND p.full_name LIKE ?"
        params.append(f"%{search}%")
    if status_filter:
        query += " AND nn.patient_status=?"
        params.append(status_filter)
    query += " ORDER BY nn.note_date DESC"
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return rows

def get_nursing_note_by_id(nid):
    conn = get_connection()
    row = conn.execute("SELECT * FROM nursing_notes WHERE id=?", (nid,)).fetchone()
    conn.close()
    return row

def add_nursing_note(data: dict) -> int:
    conn = get_connection()
    cur = conn.execute("""
        INSERT INTO nursing_notes (patient_id, nurse_id, note_date, vital_signs,
            care_given, patient_status, notes)
        VALUES (?,?,?,?,?,?,?)
    """, (data["patient_id"], data.get("nurse_id"), data.get("note_date"),
          data.get("vital_signs"), data.get("care_given"),
          data.get("patient_status"), data.get("notes")))
    conn.commit(); nid = cur.lastrowid; conn.close()
    return nid

def update_nursing_note(nid: int, data: dict):
    conn = get_connection()
    conn.execute("""
        UPDATE nursing_notes SET vital_signs=?, care_given=?, patient_status=?, notes=?
        WHERE id=?
    """, (data.get("vital_signs"), data.get("care_given"),
          data.get("patient_status"), data.get("notes"), nid))
    conn.commit(); conn.close()


# ═══════════════════════════════════════════════════════════
#  MEDICAL ORDERS (Y lệnh)
# ═══════════════════════════════════════════════════════════
def get_medical_orders(search="", status_filter=""):
    conn = get_connection()
    query = """
        SELECT mo.*, p.full_name AS patient_name, d.full_name AS doctor_name, n.full_name AS nurse_name, p.patient_code
        FROM medical_orders mo
        LEFT JOIN patients p ON mo.patient_id = p.id
        LEFT JOIN staff d ON mo.doctor_id = d.id
        LEFT JOIN staff n ON mo.nurse_id = n.id
        WHERE 1=1
    """
    params = []
    if search:
        query += " AND p.full_name LIKE ?"
        params.append(f"%{search}%")
    if status_filter:
        query += " AND mo.status=?"
        params.append(status_filter)
    query += " ORDER BY mo.order_time DESC"
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return rows

def update_medical_order_status(order_id: int, status: str, nurse_id: int = None, notes: str = None):
    conn = get_connection()
    from datetime import datetime
    conn.execute("""
        UPDATE medical_orders SET status=?, nurse_id=?, execution_time=?, notes=?
        WHERE id=?
    """, (status, nurse_id, datetime.now().strftime("%Y-%m-%d %H:%M") if status == 'Done' else None, notes, order_id))
    conn.commit()
    conn.close()

def add_medical_order(data: dict) -> int:
    conn = get_connection()
    mr_id = data.get("medical_record_id")
    if not mr_id:
        row = conn.execute("SELECT id FROM medical_records WHERE patient_id=? ORDER BY visit_date DESC LIMIT 1", (data["patient_id"],)).fetchone()
        if row:
            mr_id = row["id"]
        else:
            cur = conn.execute("INSERT INTO medical_records (patient_id, doctor_id) VALUES (?, ?)", (data["patient_id"], data.get("doctor_id")))
            mr_id = cur.lastrowid
            
    cur = conn.execute("""
        INSERT INTO medical_orders (medical_record_id, patient_id, doctor_id, order_type, description, status)
        VALUES (?,?,?,?,?,?)
    """, (mr_id, data["patient_id"], data.get("doctor_id"),
          data["order_type"], data["description"], data.get("status", "Pending")))
    conn.commit()
    oid = cur.lastrowid
    conn.close()
    return oid

def get_medical_order_by_id(oid: int):
    conn = get_connection()
    row = conn.execute("SELECT * FROM medical_orders WHERE id=?", (oid,)).fetchone()
    conn.close()
    return dict(row) if row else None

def update_medical_order(oid: int, data: dict):
    conn = get_connection()
    conn.execute("""
        UPDATE medical_orders SET patient_id=?, doctor_id=?, order_type=?, description=?, status=?
        WHERE id=?
    """, (data["patient_id"], data.get("doctor_id"),
          data["order_type"], data["description"], data.get("status", "Pending"), oid))
    conn.commit()
    conn.close()



# ═══════════════════════════════════════════════════════════
#  LAB TESTS
# ═══════════════════════════════════════════════════════════
def get_all_lab_tests(search="", status_filter=""):
    conn = get_connection()
    query = """
        SELECT lt.*,
               p.full_name AS patient_name,
               d.full_name AS doctor_name,
               t.full_name AS technician_name
        FROM lab_tests lt
        LEFT JOIN patients p ON lt.patient_id    = p.id
        LEFT JOIN staff    d ON lt.doctor_id     = d.id
        LEFT JOIN staff    t ON lt.technician_id = t.id
        WHERE 1=1
    """
    params = []
    if search:
        query += " AND (p.full_name LIKE ? OR lt.test_type LIKE ?)"
        like = f"%{search}%"; params += [like, like]
    if status_filter:
        query += " AND lt.status=?"; params.append(status_filter)
    query += " ORDER BY lt.ordered_date DESC"
    rows = conn.execute(query, params).fetchall()
    conn.close(); return rows

def get_lab_test_by_id(tid):
    conn = get_connection()
    row = conn.execute("SELECT * FROM lab_tests WHERE id=?", (tid,)).fetchone()
    conn.close(); return row

def add_lab_test(data: dict) -> int:
    conn = get_connection()
    cur = conn.execute("""
        INSERT INTO lab_tests (patient_id, doctor_id, technician_id, test_type,
            ordered_date, result_date, result, status, notes)
        VALUES (?,?,?,?,?,?,?,?,?)
    """, (data.get("patient_id"), data.get("doctor_id"), data.get("technician_id"),
          data.get("test_type"), data.get("ordered_date"), data.get("result_date"),
          data.get("result"), data.get("status","Chờ"), data.get("notes")))
    conn.commit(); tid = cur.lastrowid; conn.close(); return tid

def update_lab_test(tid: int, data: dict):
    conn = get_connection()
    conn.execute("""
        UPDATE lab_tests SET technician_id=?, result_date=?, result=?, status=?, notes=?
        WHERE id=?
    """, (data.get("technician_id"), data.get("result_date"), data.get("result"),
          data.get("status"), data.get("notes"), tid))
    conn.commit(); conn.close()


# ═══════════════════════════════════════════════════════════
#  BILLING
# ═══════════════════════════════════════════════════════════
def get_all_bills(search="", status_filter=""):
    conn = get_connection()
    query = """
        SELECT b.*, p.full_name AS patient_name
        FROM bills b LEFT JOIN patients p ON b.patient_id=p.id
        WHERE 1=1
    """
    params = []
    if search:
        query += " AND p.full_name LIKE ?"; params.append(f"%{search}%")
    if status_filter:
        query += " AND b.status=?"; params.append(status_filter)
    query += " ORDER BY b.bill_date DESC"
    rows = conn.execute(query, params).fetchall()
    conn.close(); return rows

def get_bill_by_id(bid):
    conn = get_connection()
    row = conn.execute("SELECT * FROM bills WHERE id=?", (bid,)).fetchone()
    conn.close(); return row

def get_bill_items(bid):
    conn = get_connection()
    rows = conn.execute("SELECT * FROM bill_items WHERE bill_id=?", (bid,)).fetchall()
    conn.close(); return rows

def add_bill(data: dict) -> int:
    conn = get_connection()
    cur = conn.execute("""
        INSERT INTO bills (patient_id, accountant_id, total_amount, paid_amount,
            discount, insurance_cover, payment_method, status, notes)
        VALUES (?,?,?,?,?,?,?,?,?)
    """, (data["patient_id"], data.get("accountant_id"), data.get("total_amount",0),
          data.get("paid_amount",0), data.get("discount",0),
          data.get("insurance_cover",0), data.get("payment_method"),
          data.get("status","Chưa thanh toán"), data.get("notes")))
    bid = cur.lastrowid
    for item in data.get("items",[]):
        conn.execute("""
            INSERT INTO bill_items (bill_id, item_type, description, quantity, unit_price, total)
            VALUES (?,?,?,?,?,?)
        """, (bid, item["item_type"], item["description"],
              item["quantity"], item["unit_price"], item["total"]))
    conn.commit(); conn.close(); return bid

def update_bill(bid: int, data: dict):
    """Update bill header AND fully sync its bill_items in one transaction."""
    conn = get_connection()
    try:
        conn.execute("""
            UPDATE bills SET total_amount=?, paid_amount=?, discount=?,
                insurance_cover=?, payment_method=?, status=?, notes=?
            WHERE id=?
        """, (data.get("total_amount", 0), data.get("paid_amount", 0),
              data.get("discount", 0), data.get("insurance_cover", 0),
              data.get("payment_method"), data.get("status"),
              data.get("notes"), bid))

        # Sync items: delete all old rows, re-insert current list
        conn.execute("DELETE FROM bill_items WHERE bill_id=?", (bid,))
        for item in data.get("items", []):
            conn.execute("""
                INSERT INTO bill_items (bill_id, item_type, description, quantity, unit_price, total)
                VALUES (?,?,?,?,?,?)
            """, (bid, item["item_type"], item["description"],
                  item["quantity"], item["unit_price"], item["total"]))

        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def update_bill_status(bid: int, status: str):
    conn = get_connection()
    conn.execute("UPDATE bills SET status=? WHERE id=?", (status, bid))
    conn.commit(); conn.close()


def get_audit_logs(limit=100):
    conn = get_connection()
    rows = conn.execute('''SELECT al.*, u.username FROM audit_log al LEFT JOIN users u ON al.user_id = u.id ORDER BY al.timestamp DESC LIMIT ?''', (limit,)).fetchall()
    conn.close()
    return rows

def get_patient_allergies(patient_id: int) -> str:
    """Return the allergies text for a patient (empty string if none)."""
    conn = get_connection()
    row = conn.execute(
        "SELECT allergies FROM patients WHERE id=?", (patient_id,)
    ).fetchone()
    conn.close()
    return (row["allergies"] or "") if row else ""


def get_patient_prescriptions_active(patient_id: int) -> list:
    """Return active (approved/dispensed) prescription items for a patient."""
    conn = get_connection()
    rows = conn.execute("""
        SELECT pi.medicine_id, m.name AS medicine_name,
               pi.dosage, pi.duration_days,
               p.issue_date, p.status
        FROM prescriptions p
        JOIN medical_records mr ON p.medical_record_id = mr.id
        JOIN prescription_items pi ON pi.prescription_id = p.id
        JOIN medicines m ON m.id = pi.medicine_id
        WHERE mr.patient_id = ?
          AND p.status IN ('Đã duyệt', 'Đã phát')
        ORDER BY p.issue_date DESC
    """, (patient_id,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ═══════════════════════════════════════════════════════════
#  LEAVE MANAGEMENT (TIME-OFF)
# ═══════════════════════════════════════════════════════════
def create_leave_request(staff_id: int, leave_type: str, start_date: str, end_date: str, reason: str) -> int:
    conn = get_connection()
    cur = conn.execute("""
        INSERT INTO leave_requests (staff_id, leave_type, start_date, end_date, reason)
        VALUES (?, ?, ?, ?, ?)
    """, (staff_id, leave_type, start_date, end_date, reason))
    conn.commit()
    new_id = cur.lastrowid
    conn.close()
    return new_id

def get_leave_requests_for_staff(staff_id: int):
    conn = get_connection()
    rows = conn.execute("""
        SELECT * FROM leave_requests
        WHERE staff_id = ?
        ORDER BY created_at DESC
    """, (staff_id,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_all_leave_requests():
    conn = get_connection()
    rows = conn.execute("""
        SELECT lr.*, s.full_name as staff_name, s.position
        FROM leave_requests lr
        JOIN staff s ON lr.staff_id = s.id
        ORDER BY lr.created_at DESC
    """).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def update_leave_request_status(request_id: int, status: str):
    conn = get_connection()
    conn.execute("UPDATE leave_requests SET status = ? WHERE id = ?", (status, request_id))
    conn.commit()
    conn.close()

# ═══════════════════════════════════════════════════════════
#  SHIFT SCHEDULES
# ═══════════════════════════════════════════════════════════
def get_shift_schedules_for_staff(staff_id: int):
    conn = get_connection()
    rows = conn.execute("""
        SELECT * FROM shift_schedules
        WHERE staff_id = ?
        ORDER BY shift_date ASC
    """, (staff_id,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def create_shift_schedule(staff_id: int, shift_date: str, shift_type: str, notes: str) -> int:
    conn = get_connection()
    cur = conn.execute("""
        INSERT INTO shift_schedules (staff_id, shift_date, shift_type, notes)
        VALUES (?, ?, ?, ?)
    """, (staff_id, shift_date, shift_type, notes))
    conn.commit()
    new_id = cur.lastrowid
    conn.close()
    return new_id

def update_shift_schedule(schedule_id: int, shift_date: str, shift_type: str, notes: str):
    conn = get_connection()
    conn.execute("""
        UPDATE shift_schedules
        SET shift_date = ?, shift_type = ?, notes = ?
        WHERE id = ?
    """, (shift_date, shift_type, notes, schedule_id))
    conn.commit()
    conn.close()

def delete_shift_schedule(schedule_id: int):
    conn = get_connection()
    conn.execute("DELETE FROM shift_schedules WHERE id = ?", (schedule_id,))
    conn.commit()
    conn.close()
