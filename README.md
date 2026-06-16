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
│   ├── search.py                  # Tìm kiếm NLP fuzzy (rapidfuzz)
│   ├── export.py                  # Xuất PDF (reportlab) + Excel (openpyxl)
│   └── disease_model.pkl          # Model AI (tự tạo lần đầu chạy)
│
├── ui/
│   ├── login_window.py            # Màn hình đăng nhập
│   ├── main_window.py             # Cửa sổ chính + sidebar navigation
│   ├── patient_tab.py             # 👥 Quản lý bệnh nhân
│   ├── staff_tab.py               # 👨‍⚕️ Quản lý nhân viên
│   ├── appointment_tab.py         # 🗓️ Quản lý lịch hẹn & tái khám
│   ├── room_tab.py                # 🏠 Quản lý phòng/giường bệnh
│   ├── medicine_tab.py            # 💊 Thuốc, kê đơn, tương tác thuốc
│   ├── export_tab.py              # 📤 Xuất báo cáo PDF/Excel
│   ├── stats_tab.py               # 📊 Biểu đồ thống kê (Matplotlib)
│   ├── ai_prediction_tab.py       # 🔮 AI dự đoán bệnh (scikit-learn)
│   ├── chatbot_tab.py             # 💬 Chatbot AI (Google Gemini API)
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
| Username  | Password    | Vai trò        | Quyền truy cập                        |
|-----------|-------------|----------------|---------------------------------------|
| admin     | admin123    | Quản trị viên  | Toàn bộ tính năng                     |
| bacsi01   | doctor123   | Bác sĩ         | Bệnh nhân, Lịch hẹn, Thuốc, Thống kê |
| letan01   | recept123   | Lễ tân         | Bệnh nhân, Lịch hẹn, Báo cáo         |

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

### 🏥 Phần 1 — Nền tảng
| Tính năng | Mô tả | Loại |
|-----------|-------|------|
| Đăng nhập & phân quyền | 3 vai trò, bcrypt, audit log | Bắt buộc |
| CRUD bệnh nhân | Form đầy đủ, lịch sử khám | Bắt buộc |
| Tìm kiếm NLP | Gõ không dấu vẫn tìm được | Nâng cao |
| Quản lý nhân viên | Lương, thưởng, lịch làm việc | Nâng cao |

### 🗓️ Phần 2 — Nghiệp vụ
| Tính năng | Mô tả | Loại |
|-----------|-------|------|
| Lịch hẹn & tái khám | Trạng thái trực quan, lọc đa chiều | Nâng cao |
| Phòng/Giường bệnh | Card grid, đổi trạng thái 1 click | Nâng cao |
| Kho thuốc | Cảnh báo sắp hết, sắp hết hạn | Nâng cao |
| Kê đơn thuốc | Cảnh báo tương tác thuốc real-time | AI |
| Xuất PDF/Excel | reportlab + openpyxl | Nâng cao |

### 🤖 Phần 3 — AI & Dashboard
| Tính năng | Mô tả | Loại |
|-----------|-------|------|
| Dashboard biểu đồ | Bar, Pie, Horizontal bar (Matplotlib) | Nâng cao |
| AI dự đoán bệnh | Random Forest 200 cây, 25 triệu chứng | AI |
| Chatbot y tế | Google Gemini API (`gemini-2.0-flash`) | AI |
| Backup/Restore | Timestamp, auto-backup trước restore | Nâng cao |
| Đổi mật khẩu | bcrypt verify + rehash | Nâng cao |

---

## 💬 Cấu hình Chatbot AI

1. Lấy API Key miễn phí tại [aistudio.google.com](https://aistudio.google.com/app/apikey)
2. Tạo file `.env` ở thư mục gốc dự án với nội dung:
   ```
   GEMINI_API_KEY=your_key_here
   GEMINI_MODEL=gemini-2.0-flash   # tuỳ chọn
   ```
3. Chạy lại ứng dụng — Chatbot tự động đọc key từ `.env`.
4. Bắt đầu đặt câu hỏi về thuốc, bệnh, quy trình y tế!

---

## 📦 Yêu cầu hệ thống
- Python 3.9+
- Windows / macOS / Linux
- RAM: ~256 MB (khi chạy với AI)

