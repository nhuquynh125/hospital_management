import os
import datetime

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QScrollArea, QTextEdit, QSizePolicy,
    QMessageBox
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QFont

# ── Load biến môi trường từ file .env ở thư mục gốc dự án ─────
try:
    from dotenv import load_dotenv
    _ENV_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
    load_dotenv(_ENV_PATH)
except ImportError:
    pass

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "").strip()
GEMINI_MODEL   = os.environ.get("GEMINI_MODEL", "gemini-2.0-flash").strip()

try:
    import warnings
    warnings.filterwarnings("ignore", category=FutureWarning, module="google.generativeai")
    import google.generativeai as genai
    GEMINI = True
    if GEMINI_API_KEY:
        genai.configure(api_key=GEMINI_API_KEY)
except ImportError:
    GEMINI = False


def _check_gemini_key_or_warn(parent_widget=None) -> bool:
    """Return True if key present, else show QMessageBox and return False."""
    if GEMINI_API_KEY:
        return True
    from PyQt6.QtWidgets import QMessageBox
    msg = QMessageBox(parent_widget)
    msg.setIcon(QMessageBox.Icon.Warning)
    msg.setWindowTitle("Thiếu API Key")
    msg.setText(
        "<b>GEMINI_API_KEY chưa được cấu hình.</b><br><br>"
        "Vui lòng tạo file <code>.env</code> ở thư mục gốc dự án với nội dung:<br>"
        "<pre>GEMINI_API_KEY=your_key_here</pre>"
        "Lấy key miễn phí tại: "
        "<a href=\"https://aistudio.google.com/app/apikey\">Google AI Studio</a>"
    )
    msg.setTextFormat(Qt.TextFormat.RichText)
    msg.exec()
    return False


SYSTEM_PROMPT = """Bạn là trợ lý AI y tế của Hệ thống Quản lý Bệnh viện.
Nhiệm vụ của bạn là hỗ trợ nhân viên y tế tra cứu thông tin về:
- Thuốc: công dụng, liều dùng, chống chỉ định
- Bệnh lý: triệu chứng, nguyên nhân, phác đồ điều trị, phòng ngừa
- Quy trình y tế: thủ tục khám bệnh, xét nghiệm, phẫu thuật
- Chăm sóc bệnh nhân: dinh dưỡng, phục hồi chức năng
- Tra cứu ICD-10, phác đồ điều trị chuẩn của Bộ Y tế Việt Nam

Trả lời bằng tiếng Việt, ngắn gọn, chính xác và chuyên nghiệp.
Luôn khuyến nghị tham khảo bác sĩ chuyên khoa cho các quyết định lâm sàng.
KHÔNG đưa ra chẩn đoán cụ thể cho bệnh nhân cụ thể."""

QUICK_QUESTIONS = [
    "Liều dùng Paracetamol cho người lớn?",
    "Triệu chứng viêm ruột thừa cấp?",
    "Biến chứng của bệnh tiểu đường?",
    "Phác đồ điều trị tăng huyết áp?",
    "Chăm sóc bệnh nhân sau phẫu thuật?",
    "Chỉ định xét nghiệm công thức máu?",
]


# ── Chat worker thread ────────────────────────────────────
class ChatWorker(QThread):
    response_ready = pyqtSignal(str)
    error_signal   = pyqtSignal(str)

    def __init__(self, messages: list):
        super().__init__()
        self.messages = messages  # [{"role": "user"/"assistant", "content": str}, ...]

    def run(self):
        try:
            model = genai.GenerativeModel(
                model_name=GEMINI_MODEL,
                system_instruction=SYSTEM_PROMPT,
            )

            # Gemini dùng role "user" / "model" và key "parts"
            history = []
            for m in self.messages[:-1]:
                role = "user" if m["role"] == "user" else "model"
                history.append({"role": role, "parts": [m["content"]]})

            chat = model.start_chat(history=history)
            resp = chat.send_message(self.messages[-1]["content"])
            self.response_ready.emit(resp.text)
        except Exception as e:
            self.error_signal.emit(str(e))


# ── Chat bubble widget ────────────────────────────────────
class ChatBubble(QFrame):
    def __init__(self, text: str, is_user: bool, timestamp: str = ""):
        super().__init__()
        self.setObjectName("userBubble" if is_user else "botBubble")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(3)

        if not is_user:
            name = QLabel("🤖 Trợ lý AI")
            name.setStyleSheet("color:#553c9a; font-size:10px; font-weight:600; background:transparent;")
            layout.addWidget(name)

        msg = QLabel(text)
        msg.setWordWrap(True)
        msg.setTextFormat(Qt.TextFormat.RichText)
        msg.setOpenExternalLinks(True)
        msg.setStyleSheet("background:transparent; font-size:13px; line-height:1.5;")
        layout.addWidget(msg)

        if timestamp:
            ts = QLabel(timestamp)
            ts.setStyleSheet("color:#a0aec0; font-size:10px; background:transparent;")
            ts.setAlignment(Qt.AlignmentFlag.AlignRight if is_user else Qt.AlignmentFlag.AlignLeft)
            layout.addWidget(ts)

        bg = "#2b6cb0" if is_user else "white"
        fg = "white"   if is_user else "#2d3748"
        radius_side = "border-bottom-right-radius:4px;" if is_user else "border-bottom-left-radius:4px;"
        self.setStyleSheet(f"""
            QFrame {{
                background: {bg}; color: {fg}; border-radius: 12px;
                {radius_side}
                border: {"none" if is_user else "1px solid #e2e8f0"};
            }}
        """)
        msg.setStyleSheet(f"background:transparent; color:{fg}; font-size:13px;")


# ═══════════════════════════════════════════════════════════
#  Chatbot Tab
# ═══════════════════════════════════════════════════════════
class ChatbotTab(QWidget):
    def __init__(self):
        super().__init__()
        self._conversation = []   # [{role, content}, ...]
        self._worker  = None
        self._key_warned = False  # prevent repeat QMessageBox warnings
        self._build_ui()
        self._apply_style()

    def showEvent(self, event):
        """Show a QMessageBox the first time this tab is displayed without a key."""
        super().showEvent(event)
        if not self._key_warned and GEMINI and not GEMINI_API_KEY:
            self._key_warned = True
            QTimer.singleShot(300, lambda: _check_gemini_key_or_warn(self))

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        # Header
        header = QHBoxLayout()
        title = QLabel("💬 Chatbot Hỗ trợ Y tế (AI)")
        title.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        title.setObjectName("sectionTitle")
        header.addWidget(title)
        header.addStretch()

        # Trạng thái cấu hình — KHÔNG hiển thị / nhập API key trên UI
        self.status_badge = QLabel(self._status_text())
        self.status_badge.setObjectName("statusBadge")
        header.addWidget(self.status_badge)
        layout.addLayout(header)

        # Thông báo thiếu thư viện / chưa cấu hình key
        if not GEMINI:
            warn = QLabel(
                "⚠️  Thư viện <b>google-generativeai</b> chưa được cài.<br>"
                "Chạy: <code>pip install google-generativeai python-dotenv</code>"
            )
            warn.setStyleSheet("color:#744210; background:#fffbeb; border-radius:8px; padding:10px; font-size:12px;")
            layout.addWidget(warn)
        elif not GEMINI_API_KEY:
            warn = QLabel(
                "⚠️  Chưa cấu hình <b>GEMINI_API_KEY</b>.<br>"
                "Tạo file <code>.env</code> ở thư mục gốc dự án (copy từ <code>.env.example</code>) "
                "và điền API key lấy tại "
                "<a href='https://aistudio.google.com/app/apikey'>aistudio.google.com</a>."
            )
            warn.setWordWrap(True)
            warn.setOpenExternalLinks(True)
            warn.setStyleSheet("color:#744210; background:#fffbeb; border-radius:8px; padding:10px; font-size:12px;")
            layout.addWidget(warn)

        # Quick question chips
        chips_label = QLabel("Câu hỏi nhanh:")
        chips_label.setStyleSheet("color:#718096; font-size:11px;")
        layout.addWidget(chips_label)
        chips_row = QHBoxLayout(); chips_row.setSpacing(6)
        for q in QUICK_QUESTIONS:
            btn = QPushButton(q)
            btn.setObjectName("chipBtn")
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda _, t=q: self._send_message(t))
            chips_row.addWidget(btn)
        chips_row.addStretch()
        layout.addLayout(chips_row)

        # Chat area
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll_area.setObjectName("chatScroll")

        self.chat_container = QWidget()
        self.chat_layout = QVBoxLayout(self.chat_container)
        self.chat_layout.setContentsMargins(8, 8, 8, 8)
        self.chat_layout.setSpacing(8)
        self.chat_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # Welcome message
        self._add_bot_bubble(
            "👋 Xin chào! Tôi là Trợ lý AI Y tế (Gemini).<br>"
            "Tôi có thể hỗ trợ tra cứu thông tin về <b>thuốc</b>, "
            "<b>bệnh lý</b>, <b>quy trình y tế</b> và <b>chăm sóc bệnh nhân</b>.<br>"
            "Hãy nhập câu hỏi của bạn hoặc chọn câu hỏi nhanh ở trên."
        )

        self.scroll_area.setWidget(self.chat_container)
        layout.addWidget(self.scroll_area)

        # Typing indicator
        self.typing_lbl = QLabel("🤖 Đang trả lời...")
        self.typing_lbl.setStyleSheet("color:#718096; font-size:12px; padding:4px 8px;")
        self.typing_lbl.hide()
        layout.addWidget(self.typing_lbl)

        # Input row
        input_row = QHBoxLayout()
        self.input_box = QTextEdit()
        self.input_box.setPlaceholderText("Nhập câu hỏi về thuốc, bệnh, quy trình y tế... (Enter để gửi)")
        self.input_box.setMaximumHeight(80)
        self.input_box.setObjectName("inputBox")
        self.input_box.installEventFilter(self)

        self.send_btn = QPushButton("Gửi ➤")
        self.send_btn.setObjectName("sendBtn")
        self.send_btn.setFixedWidth(80)
        self.send_btn.clicked.connect(self._on_send)

        self.clear_btn = QPushButton("🗑️")
        self.clear_btn.setObjectName("clearChatBtn")
        self.clear_btn.setFixedWidth(40)
        self.clear_btn.setToolTip("Xoá lịch sử chat")
        self.clear_btn.clicked.connect(self._clear_chat)

        input_row.addWidget(self.input_box)
        input_row.addWidget(self.send_btn)
        input_row.addWidget(self.clear_btn)
        layout.addLayout(input_row)

    def _status_text(self) -> str:
        if not GEMINI:
            return "⚪ Chưa cài thư viện"
        if not GEMINI_API_KEY:
            return "🔴 Chưa cấu hình key (.env)"
        return f"🟢 Gemini sẵn sàng ({GEMINI_MODEL})"

    def eventFilter(self, obj, event):
        from PyQt6.QtCore import QEvent
        if obj is self.input_box and event.type() == QEvent.Type.KeyPress:
            key = event.key()
            mods = event.modifiers()
            if key == Qt.Key.Key_Return and not (mods & Qt.KeyboardModifier.ShiftModifier):
                self._on_send()
                return True
        return super().eventFilter(obj, event)

    # ── Chat logic ───────────────────────────────────────────────
    def _on_send(self):
        text = self.input_box.toPlainText().strip()
        if not text:
            return
        self.input_box.clear()
        self._send_message(text)

    def _send_message(self, text: str):
        if not GEMINI:
            self._add_bot_bubble(
                "❌ Thư viện <b>google-generativeai</b> chưa được cài.<br>"
                "Chạy: <code>pip install google-generativeai python-dotenv</code>"
            )
            return
        if not GEMINI_API_KEY:
            self._add_bot_bubble(
                "🔑 Chưa cấu hình <b>GEMINI_API_KEY</b>.<br>"
                "Tạo file <code>.env</code> ở thư mục gốc dự án và thêm dòng:<br>"
                "<code>GEMINI_API_KEY=your_key_here</code>"
            )
            return
        if self._worker and self._worker.isRunning():
            return

        # Add user bubble
        ts = datetime.datetime.now().strftime("%H:%M")
        self._add_user_bubble(text, ts)
        self._conversation.append({"role": "user", "content": text})

        # Show typing indicator
        self.typing_lbl.show()
        self.send_btn.setEnabled(False)

        # Send to API
        self._worker = ChatWorker(list(self._conversation))
        self._worker.response_ready.connect(self._on_response)
        self._worker.error_signal.connect(self._on_error)
        self._worker.start()

    def _on_response(self, text: str):
        self.typing_lbl.hide()
        self.send_btn.setEnabled(True)
        ts = datetime.datetime.now().strftime("%H:%M")
        self._conversation.append({"role": "assistant", "content": text})
        # Convert markdown-like bold to HTML
        html = text.replace("**", "<b>", 1)
        while "**" in html:
            html = html.replace("**", "</b>", 1)
            if "**" in html:
                html = html.replace("**", "<b>", 1)
        html = html.replace("\n", "<br>")
        self._add_bot_bubble(html, ts)

    def _on_error(self, err: str):
        self.typing_lbl.hide()
        self.send_btn.setEnabled(True)
        low = err.lower()
        if "api_key_invalid" in low or "api key not valid" in low or "permission_denied" in low:
            msg = "❌ <b>GEMINI_API_KEY</b> không hợp lệ. Vui lòng kiểm tra lại trong file .env."
        elif "resource_exhausted" in low or "quota" in low or "429" in low:
            msg = "⏳ Đã vượt giới hạn rate limit / quota. Vui lòng thử lại sau."
        else:
            msg = f"❌ Lỗi kết nối: {err}"
        self._add_bot_bubble(msg)

    def _add_user_bubble(self, text: str, ts: str = ""):
        bubble = ChatBubble(text, is_user=True, timestamp=ts)
        row = QHBoxLayout()
        row.addStretch()
        row.addWidget(bubble)
        bubble.setMaximumWidth(500)
        self.chat_layout.addLayout(row)
        self._scroll_to_bottom()

    def _add_bot_bubble(self, text: str, ts: str = ""):
        bubble = ChatBubble(text, is_user=False, timestamp=ts)
        row = QHBoxLayout()
        row.addWidget(bubble)
        bubble.setMaximumWidth(550)
        row.addStretch()
        self.chat_layout.addLayout(row)
        self._scroll_to_bottom()

    def _clear_chat(self):
        self._conversation.clear()
        # Remove all bubbles
        for i in reversed(range(self.chat_layout.count())):
            item = self.chat_layout.itemAt(i)
            if item:
                w = item.widget()
                if w:
                    w.deleteLater()
                elif item.layout():
                    while item.layout().count():
                        child = item.layout().takeAt(0)
                        if child.widget():
                            child.widget().deleteLater()
                    self.chat_layout.removeItem(item)
        self._add_bot_bubble("🗑️ Lịch sử chat đã được xoá. Bắt đầu cuộc trò chuyện mới!")

    def _scroll_to_bottom(self):
        QTimer.singleShot(100, lambda: self.scroll_area.verticalScrollBar().setValue(
            self.scroll_area.verticalScrollBar().maximum()
        ))

    def _apply_style(self):
        self.setStyleSheet("""
        QWidget { background: #f7fafc; font-family: 'Segoe UI'; }
        #sectionTitle { color: #1a365d; }
        #chatScroll { background: white; border-radius: 10px; border: 1px solid #e2e8f0; }
        #statusBadge {
            color: #4a5568; background: #edf2f7; border-radius: 12px;
            padding: 6px 12px; font-size: 11px; font-weight: 600;
        }
        #inputBox {
            border: 1.5px solid #cbd5e0; border-radius: 8px;
            padding: 8px; font-size: 13px; background: white;
        }
        #inputBox:focus { border-color: #553c9a; }
        #sendBtn {
            background: #553c9a; color: white; border: none;
            border-radius: 8px; padding: 8px; font-weight: 600; font-size: 13px;
        }
        #sendBtn:hover { background: #44337a; }
        #sendBtn:disabled { background: #a0aec0; }
        #clearChatBtn {
            background: #fff5f5; color: #c53030; border: 1px solid #fed7d7;
            border-radius: 8px; font-size: 14px;
        }
        #clearChatBtn:hover { background: #fed7d7; }
        #chipBtn {
            background: #edf2f7; color: #4a5568; border: 1px solid #e2e8f0;
            border-radius: 14px; padding: 4px 10px; font-size: 11px;
        }
        #chipBtn:hover { background: #e9d8fd; color: #553c9a; border-color: #9f7aea; }
        """)
