import sys, os
import sqlite3
import random
from datetime import datetime, date, timedelta
import json

# Thêm đường dẫn project vào sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from database.schema import get_connection, init_db

def generate_data():
    conn = get_connection()
    cur = conn.cursor()

    # Xóa dữ liệu cũ trong các bảng giao dịch để tạo mới sạch sẽ (tuỳ chọn, nhưng nên làm để tránh lặp)
    tables_to_clear = [
        "bill_items", "bills", "lab_tests", "prescription_items", "prescriptions", 
        "nursing_notes", "medical_orders", "medical_records", "appointments", 
        "leave_requests"
    ]
    for t in tables_to_clear:
        cur.execute(f"DELETE FROM {t}")
        cur.execute(f"DELETE FROM sqlite_sequence WHERE name='{t}'") # Reset AUTOINCREMENT
    

    # Lấy danh sách nhân viên, bệnh nhân, thuốc...
    doctors = [r['id'] for r in cur.execute("SELECT id FROM staff WHERE position='Bác sĩ'").fetchall()]
    nurses = [r['id'] for r in cur.execute("SELECT id FROM staff WHERE position='Y tá / Điều dưỡng'").fetchall()]
    accountants = [r['id'] for r in cur.execute("SELECT id FROM staff WHERE position='Kế toán'").fetchall()]
    techs = [r['id'] for r in cur.execute("SELECT id FROM staff WHERE position='Xét nghiệm viên'").fetchall()]
    staff_ids = [r['id'] for r in cur.execute("SELECT id FROM staff").fetchall()]
    
    patients = [r['id'] for r in cur.execute("SELECT id FROM patients").fetchall()]
    

    
    meds = [r['id'] for r in cur.execute("SELECT id FROM medicines").fetchall()]
    
    # Tạo thêm bệnh nhân nếu ít quá (để dữ liệu phong phú)
    if len(patients) < 50:
        new_patients = []
        for i in range(7, 57):
            new_patients.append((
                f"BN{i:04d}", f"Bệnh nhân {i}", "1990-01-01", random.choice(["Nam", "Nữ"]),
                f"079090{i:06d}", f"0912{i:06d}", "Đà Nẵng", "A+", "", "", "", ""
            ))
        cur.executemany("""
            INSERT INTO patients (patient_code, full_name, birth_date, gender, id_card, phone, address, blood_type, insurance_id, insurance_exp, emergency_contact, allergies)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
        """, new_patients)
        patients = [r['id'] for r in cur.execute("SELECT id FROM patients").fetchall()]
    
    # 2. TẠO DỮ LIỆU THÁNG 4, 5, 6 (Đến hôm nay 17/06/2026)
    start_date = date(2026, 4, 1)
    end_date = date(2026, 6, 17)
    delta = end_date - start_date
    
    reasons = ["Khám tổng quát", "Sốt, ho, đau họng", "Đau dạ dày", "Tái khám đái tháo đường", "Tăng huyết áp", "Khám da liễu", "Đau nhức xương khớp", "Khám tim mạch", "Chóng mặt, buồn nôn"]
    diagnoses = ["Viêm họng cấp", "Viêm dạ dày", "Đái tháo đường type 2", "Tăng huyết áp", "Dị ứng da", "Thoái hóa khớp", "Rối loạn tiền đình", "Sốt siêu vi", "Bình thường"]
    test_types = ["Công thức máu", "Sinh hoá máu", "X-quang ngực", "Siêu âm bụng", "Đường huyết", "Nước tiểu", "Điện tâm đồ"]
    care_notes = ["Thay băng, rửa vết thương", "Cho uống thuốc theo đơn", "Đo sinh hiệu", "Truyền dịch", "Tiêm thuốc"]
    
    for i in range(delta.days + 1):
        current_date = start_date + timedelta(days=i)
        date_str = current_date.strftime("%Y-%m-%d")
        
        # Mỗi ngày tạo 10-30 cuộc hẹn
        num_appts = random.randint(10, 30)
        for _ in range(num_appts):
            p_id = random.choice(patients)
            d_id = random.choice(doctors) if doctors else None

            time_str = f"{random.randint(7, 16):02d}:{random.choice(['00', '15', '30', '45'])}"
            reason = random.choice(reasons)
            status = "Hoàn thành" if current_date < end_date else random.choice(["Chờ", "Đang khám", "Hoàn thành"])
            
            cur.execute("""
                INSERT INTO appointments (patient_id, doctor_id, appointment_date, appointment_time, reason, status)
                VALUES (?,?,?,?,?,?)
            """, (p_id, d_id, date_str, time_str, reason, status))
            
            if status == "Hoàn thành":
                # Tạo Medical Record
                diagnosis = random.choice(diagnoses)
                treatment = "Điều trị ngoại trú, dùng thuốc theo đơn"
                cur.execute("""
                    INSERT INTO medical_records (patient_id, doctor_id, visit_date, symptoms, diagnosis, treatment_plan)
                    VALUES (?,?,?,?,?,?)
                """, (p_id, d_id, date_str, reason, diagnosis, treatment))
                med_record_id = cur.lastrowid
                
                # Tạo Đơn thuốc
                if meds and random.random() > 0.3: # 70% có đơn thuốc
                    cur.execute("INSERT INTO prescriptions (medical_record_id, doctor_id, issue_date, status) VALUES (?,?,?,'Đã duyệt')", (med_record_id, d_id, date_str))
                    presc_id = cur.lastrowid
                    num_meds = random.randint(1, 4)
                    for _ in range(num_meds):
                        m_id = random.choice(meds)
                        qty = random.randint(10, 30)
                        cur.execute("INSERT INTO prescription_items (prescription_id, medicine_id, quantity, dosage, duration_days) VALUES (?,?,?,?,?)",
                                    (presc_id, m_id, qty, "1 viên/lần x 2 lần/ngày", qty//2))
                
                # Tạo Xét nghiệm
                if techs and random.random() > 0.5: # 50% có xét nghiệm
                    t_id = random.choice(techs)
                    test = random.choice(test_types)
                    cur.execute("""
                        INSERT INTO lab_tests (patient_id, doctor_id, technician_id, test_type, ordered_date, result_date, result, status)
                        VALUES (?,?,?,?,?,?,?,?)
                    """, (p_id, d_id, t_id, test, f"{date_str} {time_str}", f"{date_str} 17:00", "Kết quả bình thường", "Có kết quả"))
                    
                # Tạo Y lệnh
                if nurses and random.random() > 0.7:
                    n_id = random.choice(nurses)
                    cur.execute("""
                        INSERT INTO medical_orders (medical_record_id, patient_id, doctor_id, order_type, description, order_time, status, nurse_id)
                        VALUES (?,?,?,?,?,?,?,?)
                    """, (med_record_id, p_id, d_id, "Tiêm thuốc", "Tiêm 1 ống kháng sinh", f"{date_str} {time_str}", "Done", n_id))
                    
                # Tạo Nursing Notes
                if nurses and random.random() > 0.8:
                    n_id = random.choice(nurses)
                    vital = json.dumps({"temp": random.uniform(36.5, 39.0), "bp": f"{random.randint(100,140)}/{random.randint(60,90)}", "pulse": random.randint(60,100), "spo2": random.randint(95,100)})
                    care = random.choice(care_notes)
                    cur.execute("""
                        INSERT INTO nursing_notes (patient_id, nurse_id, note_date, vital_signs, care_given, patient_status)
                        VALUES (?,?,?,?,?,?)
                    """, (p_id, n_id, f"{date_str} {time_str}", vital, care, "Ổn định"))
                
                # Tạo Hóa đơn
                if accountants:
                    a_id = random.choice(accountants)
                    total = random.randint(100, 1000) * 1000
                    cur.execute("""
                        INSERT INTO bills (patient_id, accountant_id, bill_date, total_amount, paid_amount, payment_method, status)
                        VALUES (?,?,?,?,?,?,?)
                    """, (p_id, a_id, f"{date_str} 17:00", total, total, random.choice(["Tiền mặt", "Chuyển khoản", "Thẻ"]), "Đã thanh toán"))
                    bill_id = cur.lastrowid
                    
                    cur.execute("INSERT INTO bill_items (bill_id, item_type, description, quantity, unit_price, total) VALUES (?,?,?,?,?,?)",
                                (bill_id, "Khám", "Phí khám bệnh", 1, 150000, 150000))
                    if total > 150000:
                        cur.execute("INSERT INTO bill_items (bill_id, item_type, description, quantity, unit_price, total) VALUES (?,?,?,?,?,?)",
                                    (bill_id, "Thuốc", "Tiền thuốc", 1, total-150000, total-150000))
                                    
        # Tạo Leave Requests (Đơn xin nghỉ ngơi) ngẫu nhiên mỗi tuần
        if current_date.weekday() == 0 and random.random() > 0.5:
            s_id = random.choice(staff_ids)
            leave_start = current_date
            leave_end = current_date + timedelta(days=random.randint(1, 3))
            cur.execute("""
                INSERT INTO leave_requests (staff_id, leave_type, start_date, end_date, reason, status)
                VALUES (?,?,?,?,?,?)
            """, (s_id, random.choice(["Nghỉ phép năm", "Nghỉ ốm"]), leave_start.strftime("%Y-%m-%d"), leave_end.strftime("%Y-%m-%d"), "Việc cá nhân", "Đã duyệt"))

    conn.commit()
    conn.close()
    print("✅ Đã tạo thành công dữ liệu khổng lồ (tháng 4, 5, 6 năm 2026).")


if __name__ == "__main__":
    generate_data()
