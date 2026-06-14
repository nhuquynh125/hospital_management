"""
Hospital Management System — Seed Sample Data Script
Chạy file này 1 lần để thêm dữ liệu mẫu vào tất cả các module còn trống:
  - Lịch hẹn (hôm nay + sắp tới)
  - Hồ sơ bệnh án + chẩn đoán (để biểu đồ thống kê có dữ liệu)
  - Chăm sóc điều dưỡng
  - Xét nghiệm
  - Viện phí
  - Đơn thuốc mẫu

Chạy: python database/seed_sample_data.py
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from database.schema import get_connection, init_db
from datetime import datetime, date, timedelta

TODAY     = date.today().strftime("%Y-%m-%d")
TOMORROW  = (date.today() + timedelta(days=1)).strftime("%Y-%m-%d")
DAY3      = (date.today() + timedelta(days=3)).strftime("%Y-%m-%d")
LAST_WEEK = (date.today() - timedelta(days=7)).strftime("%Y-%m-%d")
LAST_MON  = (date.today() - timedelta(days=30)).strftime("%Y-%m-%d")
NOW       = datetime.now().strftime("%Y-%m-%d %H:%M")


def seed(conn):
    cur = conn.cursor()

    # ── Kiểm tra staff & patient IDs thực tế ─────────────────────
    doctors  = cur.execute(
        "SELECT id FROM staff WHERE position='Bác sĩ' AND is_active=1 LIMIT 3"
    ).fetchall()
    nurses   = cur.execute(
        "SELECT id FROM staff WHERE position='Y tá / Điều dưỡng' AND is_active=1 LIMIT 2"
    ).fetchall()
    patients = cur.execute(
        "SELECT id FROM patients LIMIT 6"
    ).fetchall()
    rooms    = cur.execute(
        "SELECT id FROM rooms WHERE room_type='Khám' LIMIT 2"
    ).fetchall()
    meds     = cur.execute(
        "SELECT id, name FROM medicines LIMIT 5"
    ).fetchall()

    if not doctors or not patients:
        print("❌ Chưa có bác sĩ hoặc bệnh nhân. Chạy python main.py trước để seed cơ bản.")
        return

    doc_id   = doctors[0]["id"]
    doc2_id  = doctors[1]["id"] if len(doctors) > 1 else doc_id
    nurse_id = nurses[0]["id"] if nurses else None
    room_id  = rooms[0]["id"]  if rooms  else None
    p_ids    = [p["id"] for p in patients]

    # ══════════════════════════════════════════════════════════════
    #  1. LỊCH HẸN — hôm nay + sắp tới + đã qua
    # ══════════════════════════════════════════════════════════════
    cur.execute("SELECT COUNT(*) FROM appointments").fetchone()
    appt_count = cur.execute("SELECT COUNT(*) FROM appointments").fetchone()[0]
    if appt_count == 0:
        appointments = [
            # Hôm nay
            (p_ids[0], doc_id,  room_id, TODAY,    "08:00", "Khám định kỳ",    "Chờ",        0),
            (p_ids[1], doc_id,  room_id, TODAY,    "09:00", "Đau đầu, chóng mặt", "Đang khám", 0),
            (p_ids[2], doc2_id, room_id, TODAY,    "10:00", "Ho kéo dài",       "Chờ",        0),
            (p_ids[3], doc_id,  room_id, TODAY,    "14:00", "Kiểm tra huyết áp","Chờ",        0),
            (p_ids[4] if len(p_ids)>4 else p_ids[0],
                       doc2_id, room_id, TODAY,    "15:30", "Đái tháo đường",   "Hoàn thành", 0),
            # Ngày mai
            (p_ids[0], doc_id,  room_id, TOMORROW, "08:30", "Tái khám sau điều trị", "Chờ",  1),
            (p_ids[1], doc2_id, room_id, TOMORROW, "10:00", "Đau khớp gối",     "Chờ",        0),
            # 3 ngày sau
            (p_ids[2], doc_id,  room_id, DAY3,     "09:00", "Kiểm tra tổng quát","Chờ",       0),
            # Tuần trước (đã hoàn thành)
            (p_ids[3], doc_id,  room_id, LAST_WEEK,"08:00", "Cảm cúm",          "Hoàn thành", 0),
            (p_ids[4] if len(p_ids)>4 else p_ids[0],
                       doc2_id, room_id, LAST_WEEK,"14:00", "Viêm họng",        "Hoàn thành", 0),
            # Tháng trước
            (p_ids[0], doc_id,  room_id, LAST_MON, "09:30", "Đau bụng",         "Hoàn thành", 0),
            (p_ids[1], doc2_id, room_id, LAST_MON, "11:00", "Khám da liễu",     "Hoàn thành", 0),
        ]
        cur.executemany("""
            INSERT INTO appointments
                (patient_id, doctor_id, room_id, appointment_date, appointment_time,
                 reason, status, is_followup)
            VALUES (?,?,?,?,?,?,?,?)
        """, appointments)
        print(f"✅ Thêm {len(appointments)} lịch hẹn")

    # ══════════════════════════════════════════════════════════════
    #  2. HỒ SƠ BỆNH ÁN + CHẨN ĐOÁN (cho biểu đồ thống kê)
    # ══════════════════════════════════════════════════════════════
    rec_count = cur.execute("SELECT COUNT(*) FROM medical_records").fetchone()[0]
    if rec_count == 0:
        records = [
            (p_ids[0], doc_id,  LAST_MON,  "Sốt 38.5°C, ho khan, đau họng",     "Viêm đường hô hấp trên", "Nghỉ ngơi, uống nhiều nước, dùng thuốc theo đơn", TODAY),
            (p_ids[1], doc_id,  LAST_MON,  "Đau đầu, buồn nôn, chóng mặt",       "Tăng huyết áp",          "Dùng thuốc hạ áp, theo dõi HA hàng ngày",         TOMORROW),
            (p_ids[2], doc2_id, LAST_WEEK, "Ho kéo dài >2 tuần, khó thở nhẹ",   "Viêm phế quản cấp",      "Kháng sinh 7 ngày, khí dung nếu cần",              DAY3),
            (p_ids[3], doc_id,  LAST_WEEK, "Đau thượng vị, buồn nôn sau ăn",    "Viêm dạ dày cấp",        "Omeprazole 20mg, kiêng đồ cay nóng",               None),
            (p_ids[4] if len(p_ids)>4 else p_ids[0],
                       doc2_id, TODAY,     "Khát nước nhiều, tiểu nhiều, mệt",   "Đái tháo đường type 2",  "Metformin 500mg, chế độ ăn kiêng đường",           DAY3),
            (p_ids[5] if len(p_ids)>5 else p_ids[1],
                       doc_id,  TODAY,     "Nổi mẩn đỏ, ngứa toàn thân",        "Dị ứng da",              "Kháng histamine, tránh tác nhân gây dị ứng",       None),
            (p_ids[0], doc_id,  LAST_WEEK, "Sốt, phát ban, đau cơ",             "Sốt xuất huyết",         "Bù nước, hạ sốt Paracetamol, theo dõi tiểu cầu",   TODAY),
            (p_ids[1], doc2_id, LAST_MON,  "Đau ngực khi gắng sức, khó thở",    "Thiếu máu cơ tim",       "Aspirin 81mg, tái khám tim mạch",                  TOMORROW),
        ]
        inserted_ids = []
        for r in records:
            cur.execute("""
                INSERT INTO medical_records
                    (patient_id, doctor_id, visit_date, symptoms, diagnosis, treatment_plan, follow_up_date)
                VALUES (?,?,?,?,?,?,?)
            """, r)
            inserted_ids.append(cur.lastrowid)
        print(f"✅ Thêm {len(records)} hồ sơ bệnh án")

        # ── Đơn thuốc mẫu (kèm hồ sơ bệnh án) ───────────────────
        if meds and inserted_ids:
            cur.execute("""
                INSERT INTO prescriptions (medical_record_id, doctor_id, status)
                VALUES (?,?,'Đã duyệt')
            """, (inserted_ids[0], doc_id))
            presc_id = cur.lastrowid
            cur.executemany("""
                INSERT INTO prescription_items
                    (prescription_id, medicine_id, quantity, dosage, duration_days)
                VALUES (?,?,?,?,?)
            """, [
                (presc_id, meds[0]["id"], 20, "1 viên x 3 lần/ngày sau ăn", 7),
                (presc_id, meds[2]["id"] if len(meds)>2 else meds[0]["id"],
                 10, "1 viên x 2 lần/ngày", 5),
            ])
            # Trừ tồn kho
            cur.execute("UPDATE medicines SET stock_qty = stock_qty - 20 WHERE id=?", (meds[0]["id"],))

            cur.execute("""
                INSERT INTO prescriptions (medical_record_id, doctor_id, status)
                VALUES (?,?,'Chờ duyệt')
            """, (inserted_ids[1], doc_id))
            presc_id2 = cur.lastrowid
            cur.executemany("""
                INSERT INTO prescription_items
                    (prescription_id, medicine_id, quantity, dosage, duration_days)
                VALUES (?,?,?,?,?)
            """, [
                (presc_id2, meds[4]["id"] if len(meds)>4 else meds[0]["id"],
                 30, "1 viên/ngày buổi sáng", 30),
            ])
            print("✅ Thêm 2 đơn thuốc mẫu")

    # ══════════════════════════════════════════════════════════════
    #  3. CHĂM SÓC ĐIỀU DƯỠNG
    # ══════════════════════════════════════════════════════════════
    import json
    nurse_count = cur.execute("SELECT COUNT(*) FROM nursing_notes").fetchone()[0]
    if nurse_count == 0 and nurse_id:
        notes = [
            (p_ids[0], nurse_id, f"{TODAY} 07:30",
             json.dumps({"temp":37.2,"bp":"118/76","pulse":78,"spo2":98,"resp":18}),
             "Thay băng vết thương, cho uống thuốc buổi sáng", "Ổn định"),
            (p_ids[1], nurse_id, f"{TODAY} 08:00",
             json.dumps({"temp":37.8,"bp":"145/92","pulse":88,"spo2":97,"resp":20}),
             "Đo huyết áp 2 lần, báo cáo BS về HA cao", "Cần theo dõi"),
            (p_ids[2], nurse_id, f"{TODAY} 09:00",
             json.dumps({"temp":38.5,"bp":"110/70","pulse":95,"spo2":96,"resp":22}),
             "Hạ sốt bằng Paracetamol, chườm mát", "Cần theo dõi"),
            (p_ids[3], nurse_id, f"{LAST_WEEK} 14:00",
             json.dumps({"temp":36.8,"bp":"120/80","pulse":72,"spo2":99,"resp":16}),
             "Truyền dịch Glucose 5%, theo dõi mạch", "Ổn định"),
            (p_ids[0], nurse_id, f"{LAST_WEEK} 07:30",
             json.dumps({"temp":39.1,"bp":"100/65","pulse":105,"spo2":95,"resp":24}),
             "Hạ sốt, bù nước, theo dõi tiểu cầu mỗi 6h", "Nặng"),
        ]
        cur.executemany("""
            INSERT INTO nursing_notes
                (patient_id, nurse_id, note_date, vital_signs, care_given, patient_status)
            VALUES (?,?,?,?,?,?)
        """, notes)
        print(f"✅ Thêm {len(notes)} ghi chú chăm sóc điều dưỡng")
    elif not nurse_id:
        print("⚠️  Không tìm thấy y tá — bỏ qua seed Chăm sóc ĐD")

    # ══════════════════════════════════════════════════════════════
    #  4. XÉT NGHIỆM
    # ══════════════════════════════════════════════════════════════
    lab_technician = cur.execute(
        "SELECT id FROM staff WHERE position='Xét nghiệm viên' LIMIT 1"
    ).fetchone()
    tech_id = lab_technician["id"] if lab_technician else None

    lab_count = cur.execute("SELECT COUNT(*) FROM lab_tests").fetchone()[0]
    if lab_count == 0:
        labs = [
            (p_ids[0], doc_id,  tech_id, "Công thức máu toàn phần (CBC)",
             f"{TODAY} 08:30",    f"{TODAY} 10:00",
             "Hb: 12.5 g/dL ↓\nWBC: 11.2 x10³/μL ↑\nPLT: 98 x10³/μL ↓\n→ Nghi ngờ sốt xuất huyết",
             "Có kết quả"),
            (p_ids[1], doc_id,  tech_id, "Sinh hoá máu",
             f"{TODAY} 09:00",    None,
             None, "Đang xét nghiệm"),
            (p_ids[2], doc2_id, tech_id, "X-quang ngực",
             f"{TODAY} 09:30",    None,
             None, "Chờ"),
            (p_ids[3], doc_id,  tech_id, "Đường huyết",
             f"{LAST_WEEK} 08:00", f"{LAST_WEEK} 09:00",
             "Glucose: 11.2 mmol/L ↑ (BT: 3.9-6.1)\nHbA1c: 8.3% ↑\n→ Đái tháo đường type 2 kiểm soát kém",
             "Có kết quả"),
            (p_ids[4] if len(p_ids)>4 else p_ids[0],
             doc2_id, tech_id, "Chức năng gan (AST/ALT/GGT)",
             f"{LAST_WEEK} 14:00", f"{LAST_WEEK} 16:00",
             "AST: 45 U/L (BT<40) ↑\nALT: 52 U/L (BT<41) ↑\nGGT: 38 U/L (BT)\n→ Tổn thương gan nhẹ",
             "Có kết quả"),
            (p_ids[0], doc_id,  tech_id, "Nước tiểu tổng quát",
             f"{LAST_MON} 08:00",  f"{LAST_MON} 09:30",
             "Protein: âm tính\nGlucose: âm tính\nBạch cầu: 2-3/vi trường\n→ Bình thường",
             "Có kết quả"),
        ]
        cur.executemany("""
            INSERT INTO lab_tests
                (patient_id, doctor_id, technician_id, test_type,
                 ordered_date, result_date, result, status)
            VALUES (?,?,?,?,?,?,?,?)
        """, labs)
        print(f"✅ Thêm {len(labs)} phiếu xét nghiệm")

    # ══════════════════════════════════════════════════════════════
    #  5. VIỆN PHÍ
    # ══════════════════════════════════════════════════════════════
    accountant = cur.execute(
        "SELECT id FROM staff WHERE position='Kế toán' LIMIT 1"
    ).fetchone()
    acc_id = accountant["id"] if accountant else None

    bill_count = cur.execute("SELECT COUNT(*) FROM bills").fetchone()[0]
    if bill_count == 0:
        bills = [
            # Đã thanh toán
            (p_ids[0], acc_id, f"{LAST_WEEK} 11:00", 450000, 450000,  0,      0,      "Tiền mặt",    "Đã thanh toán"),
            (p_ids[1], acc_id, f"{LAST_WEEK} 15:00", 850000, 680000,  0,      170000, "BHYT",        "Đã thanh toán"),
            (p_ids[3], acc_id, f"{LAST_MON} 16:00",  320000, 320000,  10,     0,      "Chuyển khoản","Đã thanh toán"),
            # Chưa thanh toán
            (p_ids[2], acc_id, f"{TODAY} 11:30",    1200000, 0,       0,      0,      "Tiền mặt",    "Chưa thanh toán"),
            (p_ids[4] if len(p_ids)>4 else p_ids[0],
             acc_id, f"{TODAY} 10:00", 560000, 280000, 0, 0, "Thẻ", "Một phần"),
        ]
        bill_ids = []
        for b in bills:
            cur.execute("""
                INSERT INTO bills
                    (patient_id, accountant_id, bill_date, total_amount, paid_amount,
                     discount, insurance_cover, payment_method, status)
                VALUES (?,?,?,?,?,?,?,?,?)
            """, b)
            bill_ids.append(cur.lastrowid)

        # Chi tiết hoá đơn
        bill_items = [
            # Bill 1
            (bill_ids[0], "Khám",      "Phí khám bệnh",           1, 150000, 150000),
            (bill_ids[0], "Thuốc",     "Paracetamol 500mg x20v",  1, 200000, 200000),
            (bill_ids[0], "Xét nghiệm","Công thức máu toàn phần", 1, 100000, 100000),
            # Bill 2
            (bill_ids[1], "Khám",      "Phí khám chuyên khoa",    1, 200000, 200000),
            (bill_ids[1], "Thuốc",     "Amlodipine 5mg x30v",     1, 250000, 250000),
            (bill_ids[1], "Xét nghiệm","Sinh hoá máu",            1, 400000, 400000),
            # Bill 3
            (bill_ids[2], "Khám",      "Phí khám bệnh",           1, 150000, 150000),
            (bill_ids[2], "Thuốc",     "Omeprazole 20mg x14v",    1, 170000, 170000),
            # Bill 4 (chưa TT)
            (bill_ids[3], "Khám",      "Phí khám bệnh",           1, 150000, 150000),
            (bill_ids[3], "Xét nghiệm","X-quang ngực thẳng",      1, 350000, 350000),
            (bill_ids[3], "Thuốc",     "Amoxicillin 500mg x21v",  1, 350000, 350000),
            (bill_ids[3], "Dịch vụ",   "Phí buồng khám",          1, 350000, 350000),
            # Bill 5 (một phần)
            (bill_ids[4], "Khám",      "Phí khám đái tháo đường", 1, 200000, 200000),
            (bill_ids[4], "Thuốc",     "Metformin 500mg x30v",    1, 360000, 360000),
        ]
        cur.executemany("""
            INSERT INTO bill_items (bill_id, item_type, description, quantity, unit_price, total)
            VALUES (?,?,?,?,?,?)
        """, bill_items)
        print(f"✅ Thêm {len(bills)} hoá đơn viện phí")

    conn.commit()
    print("\n🎉 Seed dữ liệu mẫu hoàn tất!")
    print("   Khởi động lại app để thấy dữ liệu mới.")


if __name__ == "__main__":
    init_db()   # đảm bảo DB tồn tại
    conn = get_connection()
    seed(conn)
    conn.close()
