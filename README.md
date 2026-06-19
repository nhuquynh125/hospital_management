# 🏥 Hospital Management System — FULL PROJECT

## Cấu trúc dự án đầy đủ

```
hospital_management/
├── main.py                        # ▶ Entry point — Chạy file này
├── requirements.txt               # Tất cả thư viện cần cài
├── hospital.db                    # SQLite DB (tự tạo khi chạy lần đầu)
│
├── database/
│   ├── schema.py                  # Khởi tạo các bảng trong CSDL
│   ├── dao.py                     # Tất cả SQL queries (Data Access Layer)
│   └── generate_massive_data.py   # Script tạo dữ liệu mẫu (bệnh nhân, nhân sự, lịch hẹn...)
│
├── core/
│   └── auth.py                    # Đăng nhập, phân quyền, mã hóa mật khẩu bcrypt
│
├── utils/
│   └── search.py                  # Tìm kiếm NLP fuzzy (rapidfuzz)
│
├── ui/                            # Giao diện người dùng (PyQt6)
│   ├── appointment_tab.py         # 🗓️ Quản lý lịch hẹn
│   ├── audit_log_tab.py           # 📝 Lịch sử hoạt động hệ thống (Audit Trail)
│   ├── billing_tab.py             # 💰 Viện phí & Thanh toán
│   ├── examination_dialog.py      # 🩺 Cửa sổ khám bệnh & chẩn đoán
│   ├── force_password_dialog.py   # 🔐 Cửa sổ yêu cầu đổi mật khẩu lần đầu
│   ├── lab_tab.py                 # 🔬 Quản lý xét nghiệm cận lâm sàng
│   ├── leave_management_tab.py    # 🌴 Quản lý & duyệt đơn nghỉ phép
│   ├── login_window.py            # 🔑 Màn hình đăng nhập
│   ├── main_window.py             # 🪟 Cửa sổ chính + sidebar navigation
│   ├── medical_order_tab.py       # 📋 Quản lý y lệnh
│   ├── medicine_tab.py            # 💊 Kho thuốc & Kê đơn
│   ├── nursing_tab.py             # 👩‍⚕️ Chăm sóc điều dưỡng & đo sinh hiệu
│   ├── patient_tab.py             # 👥 Quản lý bệnh nhân
│   ├── register_dialog.py         # 📝 Cửa sổ đăng ký mới
│   ├── settings_tab.py            # ⚙️ Cài đặt, Backup/Restore, Đổi mật khẩu
│   ├── shift_schedule_tab.py      # 🕒 Quản lý ca trực / lịch làm việc
│   └── staff_tab.py               # 👨‍⚕️ Quản lý hồ sơ nhân viên
│
└── backups/                       # Thư mục backup database tự động
```

---

## ⚡ Cài đặt & Chạy

### Bước 1 — Cài thư viện
```bash
pip install -r requirements.txt
```

### Bước 2 — Chạy ứng dụng
```bash
python main.py
```

### Bước 3 — Đăng nhập demo
| Username    | Password    | Vai trò         |
|-------------|-------------|-----------------|
| admin       | 123456      | Quản trị viên   |
| bacsi01     | 123456      | Bác sĩ          |
| nurse01     | 123456      | Y tá / Điều dưỡng|
| letan01     | 123456      | Lễ tân          |
| duocsi01    | 123456      | Dược sĩ         |
| ketoan01    | 123456      | Kế toán         |
| xetnghiem01 | 123456      | Xét nghiệm viên |
| giamdoc     | 123456      | Giám đốc        |
| thungan01   | 123456      | Thu ngân        |
| truongkhoa01| 123456      | Trưởng khoa     |
| nhansu01    | 123456      | Quản lý nhân sự |
| baove01     | 123456      | Bảo vệ          |
| laixe01     | 123456      | Lái xe cứu thương|
| vesinh01    | 123456      | Nhân viên vệ sinh|

---

## 👥 Danh sách các Vai trò và Chức năng chi tiết

Hệ thống phân quyền chặt chẽ (RBAC) với 14 vai trò. Mỗi vai trò chỉ thấy các chức năng được cho phép:

1. **Quản trị viên (Admin)**
   - Quản lý Nhân viên (Hồ sơ, chức vụ)
   - Viện phí (Xem thống kê lỗi/xử lý)
   - Lịch sử Hoạt động (Audit Trail - Theo dõi mọi thay đổi trong hệ thống)
   - Cài đặt & Hệ thống (Backup/Restore, Cấu hình Lương, Phân quyền)
   
2. **Giám đốc (Director)**
   - Toàn quyền xem và điều hành: Quản lý Bệnh nhân & Nhân viên, Lịch hẹn, Viện phí, Bệnh án, Y lệnh, Thuốc, Cài đặt... (Kế thừa quyền Bác sĩ và xem doanh thu).

3. **Bác sĩ (Doctor)**
   - Quản lý Bệnh nhân & Xem lịch sử khám
   - Quản lý Lịch hẹn
   - Bệnh án / Khám bệnh (Chẩn đoán)
   - Ra Y lệnh (Medical Orders)
   - Thuốc & Kê đơn
   - Xem kết quả Xét nghiệm

4. **Y tá / Điều dưỡng (Nurse)**
   - Quản lý Bệnh nhân
   - Bệnh án (Ghi nhận sinh hiệu, Chăm sóc điều dưỡng)
   - Xem và Cập nhật trạng thái Y lệnh từ bác sĩ

5. **Trưởng khoa (Department Head)**
   - Quản lý Nhân viên trong khoa, Lịch trực (Shift Schedule), Duyệt nghỉ phép
   - Quản lý Bệnh nhân, Lịch hẹn
   - Bệnh án, Thuốc & Kê đơn, Xét nghiệm

6. **Lễ tân (Receptionist)**
   - Quản lý Bệnh nhân (Tiếp nhận, đăng ký mới)
   - Quản lý Lịch hẹn (Thêm, sửa trạng thái - Không được xóa)
   - Xem Viện phí

7. **Dược sĩ (Pharmacist)**
   - Quản lý Kho Thuốc (Nhập/Xuất)
   - Duyệt đơn thuốc & Cấp phát thuốc

8. **Xét nghiệm viên (Lab Technician)**
   - Nhận chỉ định xét nghiệm và cập nhật kết quả/file đính kèm

9. **Kế toán (Accountant)**
   - Quản lý Viện phí & Danh sách hóa đơn (Xem)

10. **Thu ngân (Cashier)**
    - Xử lý Thanh toán viện phí, In hóa đơn (Tạo hóa đơn, Cập nhật trạng thái: Chưa thanh toán, Một phần, Đã thanh toán)

11. **Quản lý nhân sự (HR Manager)**
    - Quản lý Hồ sơ nhân viên
    - Quản lý Lịch làm việc/Ca trực (Shift Schedule)
    - Xin/Duyệt nghỉ phép

12. **Bảo vệ / Lái xe cứu thương / Nhân viên vệ sinh**
    - Nhóm hỗ trợ nội bộ.
    - Chức năng: Xem thông tin cá nhân, Đổi mật khẩu, Gửi yêu cầu Xin nghỉ phép.

---

## 🔌 Mở trong PyCharm

1. **File → Open** → chọn thư mục `hospital_management`
2. **File → Settings → Project → Python Interpreter** → Tạo Virtual Environment mới
3. Mở **Terminal** trong PyCharm:
   ```bash
   pip install -r requirements.txt
   ```
4. Chuột phải `main.py` → **Run 'main'**

---

## 🗄️ Kết nối DBeaver

1. Chạy app ít nhất 1 lần → file `hospital.db` được tạo
2. Mở DBeaver → **Database → New Database Connection → SQLite**
3. **Path**: trỏ đến file `hospital.db` trong thư mục dự án
4. Click **Test Connection** → **Finish**

---

## ✅ Tổng hợp tính năng

### 🏥 Phần 1 — Hệ thống Nền tảng
| Tính năng | Mô tả | Loại |
|-----------|-------|------|
| RBAC (Đăng nhập & Phân quyền) | Quản lý bảo mật phân tầng 14 vai trò, mã hóa mật khẩu bằng bcrypt. | Bắt buộc |
| Audit Trail (Lịch sử hoạt động) | Lưu vết mọi thay đổi dữ liệu trong hệ thống (ai làm, khi nào, sửa gì). | Bắt buộc |
| Cài đặt Hệ thống & Cá nhân | Quản lý hồ sơ, đổi mật khẩu an toàn, xin nghỉ phép. | Bắt buộc |
| Quản lý Nhân sự | Thêm mới nhân sự, phân quyền, duyệt đơn xin nghỉ phép. | Nâng cao |
| Lịch trực (Shift Schedule) | Giao diện xếp ca trực, ca làm việc linh hoạt cho đội ngũ. | Nâng cao |
| Tìm kiếm thông minh (NLP) | Thuật toán Rapidfuzz cho phép tìm kiếm nhanh, gõ tiếng Việt không dấu. | Nâng cao |
| Backup & Restore DB | Giao diện sao lưu cơ sở dữ liệu an toàn, chống mất mát dữ liệu. | Nâng cao |

### 🗓️ Phần 2 — Quản lý Nghiệp vụ Y tế
| Tính năng | Mô tả | Loại |
|-----------|-------|------|
| Bệnh nhân & Lịch hẹn | Quản lý hồ sơ, BHYT, theo dõi trạng thái cuộc hẹn trực quan. | Bắt buộc |
| Khám bệnh & Y lệnh | Bác sĩ chẩn đoán, ra y lệnh. Y tá nhận lệnh, đo sinh hiệu và thực thi, cập nhật thời gian thực. | Nâng cao |
| Kho Thuốc & Kê đơn | Cảnh báo tồn kho, hạn sử dụng. Kê đơn điện tử liên thông kho dược, duyệt phát thuốc. | Nâng cao |
| Xét nghiệm (Lab Tests) | Bác sĩ chỉ định, xét nghiệm viên nhập kết quả hoặc đính kèm file. | Nâng cao |
| Viện phí & Thanh toán | Theo dõi hóa đơn, trạng thái thanh toán (Chưa thanh toán, Một phần, Đã thanh toán), xuất PDF. | Nâng cao |
| Ghi chú chăm sóc | Y tá lưu ghi chú về tình trạng chăm sóc hàng ngày của bệnh nhân. | Nâng cao |

---

## 📦 Yêu cầu hệ thống
- Python 3.9+
- Windows / macOS / Linux
- Thư viện PyQt6, SQLite3, reportlab, rapidfuzz...
