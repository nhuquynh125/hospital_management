# 🏥 Hospital Management System — FULL PROJECT

## Cấu trúc dự án đầy đủ

```
hospital_management/
├── main.py                        # ▶ Entry point — Chạy file này
├── requirements.txt               # Tất cả thư viện cần cài
├── hospital.db                    # SQLite DB (tự tạo khi chạy lần đầu)
│
├── database/
│   ├── schema.py                  # Khởi tạo 10 bảng + seed data mẫu
│   └── dao.py                     # Tất cả SQL queries (Data Access Layer)
│
├── core/
│   └── auth.py                    # Đăng nhập, phân quyền, bcrypt
│
├── utils/
│   └── search.py                  # Tìm kiếm NLP fuzzy (rapidfuzz)
├── ui/
│   ├── login_window.py            # Màn hình đăng nhập
│   ├── main_window.py             # Cửa sổ chính + sidebar navigation
│   ├── patient_tab.py             # 👥 Quản lý bệnh nhân
│   ├── staff_tab.py               # 👨‍⚕️ Quản lý nhân viên
│   ├── appointment_tab.py         # 🗓️ Quản lý lịch hẹn & tái khám
│   ├── room_tab.py                # 🏠 Quản lý phòng/giường bệnh
│   ├── medicine_tab.py            # 💊 Thuốc, kê đơn
│
│   └── settings_tab.py            # ⚙️ Cài đặt, Backup/Restore, Đổi mật khẩu
│
└── backups/                       # Thư mục backup database
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
| admin       | admin123    | Quản trị viên   |
| bacsi01     | doctor123   | Bác sĩ          |
| nurse01     | nurse123    | Y tá / Điều dưỡng|
| letan01     | recept123   | Lễ tân          |
| duocsi01    | pharma123   | Dược sĩ         |
| ketoan01    | acc123      | Kế toán         |
| xetnghiem01 | lab123      | Xét nghiệm viên |
| giamdoc     | director123 | Giám đốc        |
| thungan01   | cashier123  | Thu ngân        |
| truongkhoa01| head123     | Trưởng khoa     |
| nhansu01    | hr123       | Quản lý nhân sự |
| baove01     | guard123    | Bảo vệ          |
| laixe01     | driver123   | Lái xe cứu thương|
| vesinh01    | janitor123  | Nhân viên vệ sinh|

---

## 👥 Danh sách các Vai trò và Chức năng chi tiết

Hệ thống phân quyền chặt chẽ (RBAC) với 14 vai trò. Mỗi vai trò chỉ thấy các chức năng được cho phép:

1. **Quản trị viên (Admin)**
   - Quản lý Nhân viên (Hồ sơ, chức vụ)
   - Viện phí (Xem thống kê lỗi/xử lý)
   - Lịch sử Hoạt động (Audit Trail - Theo dõi mọi thay đổi trong hệ thống)
   - Cài đặt & Hệ thống (Backup/Restore, Cấu hình Lương, Phân quyền)
   
2. **Giám đốc (Director)**
   - Quản lý Bệnh nhân & Nhân viên
   - Quản lý Lịch hẹn & Phòng/Giường bệnh
   - Viện phí & Thống kê tài chính
   - Báo cáo Điều hành (Dashboard đặc biệt cho Giám đốc)
   - Dự báo Lượng bệnh (AI Predictive Analytics)

3. **Bác sĩ (Doctor)**
   - Quản lý Bệnh nhân & Xem lịch sử khám
   - Quản lý Lịch hẹn
   - Bệnh án / Khám bệnh (Chẩn đoán, Y lệnh)
   - Thuốc & Kê đơn
   - Xem kết quả Xét nghiệm
   - Thống kê

4. **Y tá / Điều dưỡng (Nurse)**
   - Quản lý Bệnh nhân & Lịch hẹn
   - Bệnh án (Ghi nhận sinh hiệu, Chăm sóc điều dưỡng)
   - Xem Y lệnh từ bác sĩ
   - Quản lý Phòng / Giường bệnh
   - Thống kê

5. **Trưởng khoa (Department Head)**
   - Quản lý Nhân viên trong khoa, Lịch trực (Shift Schedule)
   - Quản lý Bệnh nhân, Lịch hẹn
   - Bệnh án, Thuốc & Kê đơn, Xét nghiệm
   - Thống kê

6. **Lễ tân (Receptionist)**
   - Quản lý Bệnh nhân (Tiếp nhận, đăng ký mới)
   - Quản lý Lịch hẹn
   - Quản lý Phòng / Giường (Phân phòng)
   - Viện phí (Xem thông tin), Thống kê cơ bản

7. **Dược sĩ (Pharmacist)**
   - Quản lý Kho Thuốc (Nhập/Xuất, Kho thông minh)
   - Duyệt đơn thuốc & Cấp phát thuốc
   - Thống kê kho thuốc

8. **Xét nghiệm viên (Lab Technician)**
   - Nhận yêu cầu và cập nhật kết quả Xét nghiệm
   - Thống kê Xét nghiệm

9. **Kế toán (Accountant)**
   - Quản lý Viện phí & Thanh toán
   - Thống kê doanh thu

10. **Thu ngân (Cashier)**
    - Xử lý Thanh toán viện phí & In hóa đơn

11. **Quản lý nhân sự (HR Manager)**
    - Quản lý Hồ sơ nhân viên
    - Quản lý Lịch làm việc/Ca trực (Shift Schedule)
    - Cài đặt & Cấu hình Lương (Salary Config), Xin/Duyệt nghỉ phép

12. **Bảo vệ / Lái xe cứu thương / Nhân viên vệ sinh**
    - Nhóm hỗ trợ nội bộ.
    - Chức năng: Xem thông tin cá nhân, Đổi mật khẩu, Xem phiếu lương, Gửi yêu cầu Xin nghỉ phép.

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
| Cài đặt Hệ thống & Cá nhân | Quản lý hồ sơ, đổi mật khẩu an toàn, xin nghỉ phép, xem phiếu lương. | Bắt buộc |
| Quản lý Nhân sự & Lương | Thêm mới nhân sự, cấu hình bảng lương gốc, duyệt đơn xin nghỉ phép. | Nâng cao |
| Lịch trực (Shift Schedule) | Giao diện xếp ca trực, ca làm việc linh hoạt cho đội ngũ y bác sĩ. | Nâng cao |
| Tìm kiếm thông minh (NLP) | Thuật toán Rapidfuzz cho phép tìm kiếm nhanh, gõ tiếng Việt không dấu. | Nâng cao |
| Backup & Restore DB | Giao diện sao lưu cơ sở dữ liệu an toàn, chống mất mát dữ liệu. | Nâng cao |

### 🗓️ Phần 2 — Quản lý Nghiệp vụ Y tế
| Tính năng | Mô tả | Loại |
|-----------|-------|------|
| Bệnh nhân & Lịch hẹn | Quản lý hồ sơ, BHYT, theo dõi trạng thái cuộc hẹn trực quan. | Bắt buộc |
| Bệnh án & Y lệnh (Medical Orders)| Bác sĩ chẩn đoán, ra y lệnh. Y tá nhận lệnh, đo sinh hiệu và thực thi. | Nâng cao |
| Kho Thuốc & Kê đơn | Cảnh báo tồn kho, hạn sử dụng. Kê đơn điện tử liên thông kho dược. | Nâng cao |
| Xét nghiệm (Lab Tests) | Chỉ định cận lâm sàng, nhập kết quả dạng text hoặc đính kèm file ảnh/PDF.| Nâng cao |
| Quản lý Phòng/Giường bệnh | Lưới hiển thị dạng Card (thẻ), đổi trạng thái phòng (trống, bảo trì) bằng 1 click.| Nâng cao |
| Viện phí & Thanh toán | Tính toán chi phí khám/thuốc/dịch vụ tự động, in hóa đơn nhanh chóng. | Nâng cao |

### 🤖 Phần 3 — Trí tuệ Nhân tạo (AI) & Báo cáo
| Tính năng | Mô tả | Loại |
|-----------|-------|------|
| Dashboard Báo cáo Điều hành | Hệ thống biểu đồ trực quan (Matplotlib) theo dõi doanh thu và KPI bệnh viện. | Nâng cao |
| AI Dự báo Lượng bệnh nhân | Phân tích xu hướng để dự báo lượng bệnh trong tương lai giúp sắp xếp nhân sự. | AI |

---



## 📦 Yêu cầu hệ thống
- Python 3.9+
- Windows / macOS / Linux
- RAM: ~256 MB (khi chạy với AI)

