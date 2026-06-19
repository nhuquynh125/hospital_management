import sys, os
import sqlite3
import random
import bcrypt
from datetime import datetime, date, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from database.schema import get_connection

def generate_500_staff():
    conn = get_connection()
    cur = conn.cursor()

    # Get current staff count
    cur.execute("SELECT count(*) FROM staff")
    current_count = cur.fetchone()[0]

    if current_count >= 500:
        print(f"Already have {current_count} staff members.")
        return

    needed = 500 - current_count
    print(f"Generating {needed} new staff members...")

    # Get roles
    cur.execute("SELECT id, role_name FROM roles")
    roles = {row['role_name']: row['id'] for row in cur.fetchall()}

    # Get departments
    cur.execute("SELECT id, name FROM departments")
    departments = {row['name']: row['id'] for row in cur.fetchall()}
    dept_names = list(departments.keys())

    # Get max staff code to continue numbering
    cur.execute("SELECT staff_code FROM staff")
    codes = [row['staff_code'] for row in cur.fetchall()]
    
    # We will generate different types of roles with some distribution
    # Doctors: 20%, Nurses: 40%, Others: 40%
    
    role_distribution = [
        ("doctor", "Bác sĩ", 0.20),
        ("nurse", "Y tá / Điều dưỡng", 0.40),
        ("receptionist", "Lễ tân", 0.05),
        ("pharmacist", "Dược sĩ", 0.05),
        ("accountant", "Kế toán", 0.05),
        ("lab_technician", "Xét nghiệm viên", 0.05),
        ("security_guard", "Bảo vệ", 0.05),
        ("janitor", "Nhân viên vệ sinh", 0.10),
        ("ambulance_driver", "Lái xe cứu thương", 0.05),
    ]

    surnames = ["Nguyễn", "Trần", "Lê", "Phạm", "Hoàng", "Huỳnh", "Phan", "Vũ", "Võ", "Đặng", "Bùi", "Đỗ", "Hồ", "Ngô", "Dương", "Lý"]
    middle_names_m = ["Văn", "Hữu", "Đức", "Công", "Minh", "Quang", "Thái", "Đình", "Xuân", "Ngọc", "Hoàng"]
    middle_names_f = ["Thị", "Ngọc", "Thu", "Phương", "Mai", "Hồng", "Kim", "Thanh", "Bích", "Tuyết"]
    first_names_m = ["An", "Bình", "Cường", "Dũng", "Em", "Phong", "Giang", "Hải", "Hùng", "Khoa", "Long", "Nam", "Phát", "Quân", "Sơn", "Tuấn", "Thắng", "Việt"]
    first_names_f = ["An", "Bình", "Châu", "Dung", "Hoa", "Lan", "Mai", "Nga", "Oanh", "Phương", "Quyên", "Trang", "Uyên", "Vy", "Yến"]

    hashed_pw = bcrypt.hashpw("123456".encode(), bcrypt.gensalt()).decode()

    def generate_name(gender):
        if gender == "Nam":
            return f"{random.choice(surnames)} {random.choice(middle_names_m)} {random.choice(first_names_m)}"
        else:
            return f"{random.choice(surnames)} {random.choice(middle_names_f)} {random.choice(first_names_f)}"

    def random_date(start_year, end_year):
        start = date(start_year, 1, 1)
        end = date(end_year, 12, 31)
        return start + timedelta(days=random.randint(0, (end - start).days))

    users_data = []
    staff_data = []

    # Get max user id
    cur.execute("SELECT max(id) FROM users")
    max_user_id = cur.fetchone()[0] or 0
    next_user_id = max_user_id + 1

    count = 1
    for role_key, position, ratio in role_distribution:
        num_to_gen = int(needed * ratio)
        for i in range(num_to_gen):
            gender = random.choice(["Nam", "Nữ"])
            full_name = generate_name(gender)
            username = f"staff_{next_user_id}"
            role_id = roles.get(role_key, 1) # fallback to admin id if missing? No, should be fine
            
            # Create user
            users_data.append((next_user_id, username, hashed_pw, full_name, role_id))

            # Create staff
            prefix = position.split()[0][:2].upper()
            staff_code = f"{prefix}{count:04d}_{next_user_id}"
            
            birth_date = random_date(1970, 2000).strftime("%Y-%m-%d")
            id_card = f"079{random.randint(100000000, 999999999)}"
            phone = f"09{random.randint(10000000, 99999999)}"
            email = f"{username}@hospital.vn"
            address = random.choice(["Đà Nẵng", "Hà Nội", "Hồ Chí Minh", "Quảng Nam", "Huế"])
            
            dept_id = None
            specialization = None
            medical_depts = [d for d in dept_names if d not in ["Dược", "Xét nghiệm", "Kế toán"]]
            if role_key == "doctor":
                dept_name = random.choice(medical_depts)
                dept_id = departments[dept_name]
                specialization = dept_name
            elif role_key == "nurse":
                dept_name = random.choice(medical_depts)
                dept_id = departments[dept_name]
            elif role_key == "pharmacist":
                dept_id = departments.get("Dược")
            elif role_key == "lab_technician":
                dept_id = departments.get("Xét nghiệm")
            elif role_key == "accountant":
                dept_id = departments.get("Kế toán")

            hire_date = random_date(2010, 2025).strftime("%Y-%m-%d")
            salary = random.randint(7, 30) * 1000000
            bonus = random.randint(1, 5) * 1000000

            staff_data.append((
                next_user_id, staff_code, full_name, gender, birth_date, id_card, phone, email, address,
                position, specialization, dept_id, hire_date, salary, bonus
            ))

            next_user_id += 1
            count += 1

    # Fill remaining if rounding caused mismatch
    while len(staff_data) < needed:
        gender = random.choice(["Nam", "Nữ"])
        full_name = generate_name(gender)
        username = f"staff_{next_user_id}"
        role_key, position = "nurse", "Y tá / Điều dưỡng"
        role_id = roles.get(role_key)

        users_data.append((next_user_id, username, hashed_pw, full_name, role_id))

        staff_code = f"NV{count:04d}_{next_user_id}"
        birth_date = random_date(1970, 2000).strftime("%Y-%m-%d")
        id_card = f"079{random.randint(100000000, 999999999)}"
        phone = f"09{random.randint(10000000, 99999999)}"
        email = f"{username}@hospital.vn"
        address = "Đà Nẵng"
        dept_id = departments.get(random.choice(dept_names))
        hire_date = random_date(2010, 2025).strftime("%Y-%m-%d")
        salary = 10000000
        bonus = 1000000

        staff_data.append((
            next_user_id, staff_code, full_name, gender, birth_date, id_card, phone, email, address,
            position, None, dept_id, hire_date, salary, bonus
        ))

        next_user_id += 1
        count += 1

    print(f"Inserting {len(users_data)} users and {len(staff_data)} staff...")
    cur.executemany("""
        INSERT INTO users (id, username, password, full_name, role_id)
        VALUES (?,?,?,?,?)
    """, users_data)

    cur.executemany("""
        INSERT INTO staff (user_id, staff_code, full_name, gender, birth_date, id_card,
            phone, email, address, position, specialization, department_id,
            hire_date, salary, bonus)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    """, staff_data)

    conn.commit()
    conn.close()
    print("Done! We now have 500 staff members.")

if __name__ == "__main__":
    generate_500_staff()
