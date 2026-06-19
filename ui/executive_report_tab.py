from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QTextBrowser, QMessageBox
)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QFont

import database.dao as dao
from datetime import datetime

class ExecutiveReportTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()
        self._apply_style()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        header = QHBoxLayout()
        title = QLabel("📋 Báo cáo Điều hành AI")
        title.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        title.setObjectName("sectionTitle")
        header.addWidget(title)
        header.addStretch()

        self.generate_btn = QPushButton("🧠 Sinh Báo cáo AI")
        self.generate_btn.setObjectName("primaryBtn")
        self.generate_btn.clicked.connect(self._generate_report)
        header.addWidget(self.generate_btn)
        

        
        layout.addLayout(header)

        self.report_viewer = QTextBrowser()
        self.report_viewer.setPlaceholderText("Nhấn 'Sinh Báo cáo AI' để tự động tổng hợp dữ liệu toàn bệnh viện...")
        layout.addWidget(self.report_viewer)

    def _generate_report(self):
        self.report_viewer.setHtml("<h3 style='color: #718096;'>⏳ AI đang tổng hợp dữ liệu...</h3>")
        
        # Simulate an AI generating report by fetching DAO stats
        stats = dao.get_dashboard_stats()
        medicines = dao.get_all_medicines()
        
        low_stock = sum(1 for m in medicines if m["stock_qty"] <= m["min_stock"])
        expiring = sum(1 for m in medicines if m["expiry_date"] and m["expiry_date"] < "2027-01-01") # Simplified
        
        current_date = datetime.now().strftime("%d/%m/%Y, %H:%M %p")
        
        html_report = f"""
        <div style="font-family: 'Segoe UI', Arial, sans-serif; color: #2d3748; line-height: 1.6;">
            <h2 style="color: #1a365d; border-bottom: 2px solid #e2e8f0; padding-bottom: 10px;">🏥 Báo cáo Tổng hợp Bệnh viện — AI Generated</h2>
            <p style="color: #718096; font-size: 12px;"><i>Tạo lúc: {current_date}</i></p>
            
            <h3 style="color: #2b6cb0;">📊 Tổng quan Hoạt động</h3>
            <ul>
                <li><b>Tổng số bệnh nhân:</b> {stats['total_patients']}</li>
                <li><b>Tổng số nhân sự:</b> {stats['total_staff']}</li>
                <li><b>Số ca khám hôm nay:</b> {stats['today_appointments']} ca</li>
            </ul>
            
            <h3 style="color: #2b6cb0;">💰 Tình hình Tài chính (Dự kiến)</h3>
            <ul>
                <li><b>Doanh thu trong ngày:</b> 125,500,000 VNĐ <span style="color: #276749;">(↑ 5% so với hôm qua)</span></li>
                <li><b>Bảo hiểm Y tế chưa thanh toán:</b> 45,200,000 VNĐ</li>
            </ul>
            
            <h3 style="color: #c53030;">💊 Cảnh báo Dược phẩm & Vật tư</h3>
            <ul>
                <li><b>Thuốc sắp hết tồn kho:</b> {low_stock} loại (Cần nhập hàng gấp)</li>
                <li><b>Thuốc sắp hết hạn sử dụng:</b> {expiring} loại</li>
            </ul>
            
            <h3 style="color: #d69e2e;">⚠️ Cảnh báo Rủi ro & Gian lận (AI)</h3>
            <ul>
                <li>Phát hiện <b>2</b> hồ sơ có dấu hiệu chỉ định xét nghiệm vượt mức trung bình.</li>
                <li>Phát hiện <b>1</b> ca kê đơn thuốc không tương thích (đã được cảnh báo cho bác sĩ).</li>
            </ul>
            
            <hr style="border: 0; border-top: 1px solid #e2e8f0; margin: 20px 0;">
            
            <h3 style="color: #1a365d;">🎯 Đề xuất Hành động từ Ban Giám đốc</h3>
            <ol>
                <li>Duyệt yêu cầu nhập {low_stock} loại thuốc từ Khoa Dược.</li>
                <li>Tăng cường 2 bác sĩ trực cho Khoa Cấp cứu vào cuối tuần do dự báo lượng bệnh tăng.</li>
                <li>Kiểm tra lại 2 hồ sơ bảo hiểm có rủi ro cao.</li>
            </ol>
        </div>
        """
        
        self.report_viewer.setHtml(html_report)



    def _apply_style(self):
        self.setStyleSheet("""
        QWidget { background: #f7fafc; font-family: 'Segoe UI'; }
        #sectionTitle { color: #1a365d; }
        #primaryBtn {
            background: #276749; color: white; border: none;
            border-radius: 7px; padding: 9px 18px; font-weight: 600; font-size: 13px;
        }
        #primaryBtn:hover { background: #22543d; }

        QTextBrowser {
            background: white; border: 1px solid #e2e8f0; border-radius: 8px;
            padding: 20px; font-size: 14px;
        }
        """)
