import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QMessageBox, QFileDialog
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

import database.dao as dao


class ExportTab(QWidget):
    def __init__(self):
        super().__init__()
        self._build_ui()
        self._apply_style()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        title = QLabel("📤 Xuất báo cáo")
        title.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        title.setObjectName("sectionTitle")
        layout.addWidget(title)

        # Cards row
        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(16)

        cards = [
            ("📋 Danh sách bệnh nhân",
             "Xuất toàn bộ danh sách bệnh nhân ra file PDF hoặc Excel",
             "#2b6cb0", "#ebf8ff",
             self._export_patients_pdf, self._export_patients_excel),
            ("💊 Đơn thuốc",
             "In đơn thuốc gần nhất ra file PDF",
             "#553c9a", "#faf5ff",
             self._export_last_prescription, None),
            ("📊 Báo cáo tháng",
             "Xuất báo cáo tổng hợp tháng ra file Excel",
             "#276749", "#f0fff4",
             None, self._export_monthly_excel),
        ]

        for title_txt, desc, color, bg, pdf_fn, excel_fn in cards:
            card = QFrame()
            card.setStyleSheet(f"""
                QFrame {{
                    background: {bg}; border-radius: 12px;
                    border: 1px solid {color}30; padding: 4px;
                }}
            """)
            cl = QVBoxLayout(card)
            cl.setContentsMargins(16, 16, 16, 16)
            cl.setSpacing(8)

            t = QLabel(title_txt)
            t.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
            t.setStyleSheet(f"color: {color}; background: transparent;")
            cl.addWidget(t)

            d = QLabel(desc)
            d.setWordWrap(True)
            d.setStyleSheet("color: #4a5568; font-size: 12px; background: transparent;")
            cl.addWidget(d)

            btn_row = QHBoxLayout()
            if pdf_fn:
                pdf_btn = QPushButton("📄 Xuất PDF")
                pdf_btn.setStyleSheet(f"""
                    QPushButton {{ background: {color}; color: white; border: none;
                        border-radius: 6px; padding: 7px 14px; font-size: 12px; font-weight: 600; }}
                    QPushButton:hover {{ opacity: 0.85; }}
                """)
                pdf_btn.clicked.connect(pdf_fn)
                btn_row.addWidget(pdf_btn)
            if excel_fn:
                xl_btn = QPushButton("📊 Xuất Excel")
                xl_btn.setStyleSheet(f"""
                    QPushButton {{ background: white; color: {color};
                        border: 1.5px solid {color}; border-radius: 6px;
                        padding: 7px 14px; font-size: 12px; font-weight: 600; }}
                    QPushButton:hover {{ background: {bg}; }}
                """)
                xl_btn.clicked.connect(excel_fn)
                btn_row.addWidget(xl_btn)

            btn_row.addStretch()
            cl.addLayout(btn_row)
            cards_layout.addWidget(card)

        layout.addLayout(cards_layout)

        # Note about required packages
        note = QLabel(
            #"ℹ️  Yêu cầu: <b>pip install reportlab openpyxl</b><br>"
            "File xuất sẽ được lưu vào thư mục <b>~/Downloads/HospitalExports/</b>"
        )
        note.setStyleSheet("""
            background: #fffbeb; color: #744210;
            border: 1px solid #f6e05e; border-radius: 8px;
            padding: 12px 16px; font-size: 12px;
        """)
        layout.addWidget(note)
        layout.addStretch()

    # ── Export handlers ──────────────────────────────────────────
    def _export_patients_pdf(self):
        try:
            from utils.export import export_patients_pdf
            patients = dao.get_all_patients()
            if not patients:
                QMessageBox.information(self, "Không có dữ liệu", "Chưa có bệnh nhân nào.")
                return
            filepath = export_patients_pdf(patients)
            self._show_success(filepath)
        except ImportError as e:
            QMessageBox.warning(self, "Thiếu thư viện", str(e))
        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"Xuất PDF thất bại:\n{e}")

    def _export_patients_excel(self):
        try:
            from utils.export import export_patients_excel
            patients = dao.get_all_patients()
            if not patients:
                QMessageBox.information(self, "Không có dữ liệu", "Chưa có bệnh nhân nào.")
                return
            filepath = export_patients_excel(patients)
            self._show_success(filepath)
        except ImportError as e:
            QMessageBox.warning(self, "Thiếu thư viện", str(e))
        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"Xuất Excel thất bại:\n{e}")

    def _export_last_prescription(self):
        try:
            from utils.export import export_prescription_pdf
            prescriptions = dao.get_all_prescriptions()
            if not prescriptions:
                QMessageBox.information(self, "Không có dữ liệu", "Chưa có đơn thuốc nào.")
                return
            last = prescriptions[0]
            items = dao.get_prescription_items(last["id"])
            items_list = [dict(i) for i in items]
            filepath = export_prescription_pdf(
                dict(last), items_list,
                last["patient_name"] or "N/A",
                last["doctor_name"] or "N/A"
            )
            self._show_success(filepath)
        except ImportError as e:
            QMessageBox.warning(self, "Thiếu thư viện", str(e))
        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"Xuất PDF thất bại:\n{e}")

    def _export_monthly_excel(self):
        try:
            from utils.export import export_monthly_report_excel
            stats = dao.get_dashboard_stats()
            appointments = dao.get_all_appointments()
            filepath = export_monthly_report_excel(stats, appointments)
            self._show_success(filepath)
        except ImportError as e:
            QMessageBox.warning(self, "Thiếu thư viện", str(e))
        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"Xuất Excel thất bại:\n{e}")

    def _show_success(self, filepath: str):
        msg = QMessageBox(self)
        msg.setWindowTitle("Xuất file thành công ✅")
        msg.setText(f"File đã được lưu tại:\n<b>{filepath}</b>")
        msg.setIcon(QMessageBox.Icon.Information)
        open_btn = msg.addButton("📂 Mở thư mục", QMessageBox.ButtonRole.ActionRole)
        msg.addButton("OK", QMessageBox.ButtonRole.AcceptRole)
        msg.exec()
        if msg.clickedButton() == open_btn:
            import subprocess, sys
            folder = os.path.dirname(filepath)
            if sys.platform == "win32":
                os.startfile(folder)
            elif sys.platform == "darwin":
                subprocess.Popen(["open", folder])
            else:
                subprocess.Popen(["xdg-open", folder])

    def _apply_style(self):
        self.setStyleSheet("""
        QWidget { background: #f7fafc; font-family: 'Segoe UI'; }
        #sectionTitle { color: #1a365d; }
        """)
