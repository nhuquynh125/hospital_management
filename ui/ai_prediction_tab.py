"""
Hospital Management System — AI Disease Prediction Tab
Dự đoán bệnh từ triệu chứng dùng Random Forest (scikit-learn)
Dataset: synthetic symptom-disease mapping (dễ mở rộng với Kaggle dataset)
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QCheckBox, QScrollArea, QTableWidget, QTableWidgetItem,
    QHeaderView, QAbstractItemView, QMessageBox, QProgressBar, QLineEdit, QGridLayout
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont, QColor

import json, os

try:
    import numpy as np
    import pandas as pd
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.preprocessing import LabelEncoder
    import pickle
    SKLEARN = True
except ImportError:
    SKLEARN = False


# ── Symptom / Disease dataset (compact, extensible) ──────
SYMPTOMS = [
    "sốt","ho","đau đầu","mệt mỏi","buồn nôn","nôn","tiêu chảy",
    "đau bụng","đau ngực","khó thở","chóng mặt","phát ban",
    "đau họng","sổ mũi","đau cơ","đau khớp","sưng phù",
    "mất khẩu vị","đổ mồ hôi","ớn lạnh","vàng da","đau lưng",
    "nhức mắt","nhịp tim nhanh","mất ngủ"
]

# Synthetic training data: (symptoms_active, disease)
TRAINING_DATA = [
    ([1,1,1,1,0,0,0,0,0,0,0,0,1,1,1,0,0,0,1,1,0,0,0,0,0], "Cảm cúm"),
    ([1,1,1,1,0,0,0,0,0,0,0,0,1,1,0,0,0,0,0,1,0,0,0,0,0], "Cảm lạnh"),
    ([1,0,1,1,1,1,1,1,0,0,0,0,0,0,0,0,0,1,0,0,1,0,0,0,0], "Viêm gan"),
    ([1,0,0,1,1,1,1,1,0,0,0,0,0,0,0,0,0,1,0,1,0,0,0,0,0], "Ngộ độc thực phẩm"),
    ([0,1,0,1,0,0,0,0,1,1,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0], "Viêm phổi"),
    ([0,1,0,1,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0], "Hen suyễn"),
    ([0,0,1,1,0,0,0,0,0,0,1,0,0,0,0,0,1,0,1,0,0,0,0,1,0], "Tăng huyết áp"),
    ([0,0,0,1,0,0,0,0,1,0,0,0,0,0,1,1,1,0,0,0,0,0,0,0,0], "Viêm khớp"),
    ([1,0,0,1,1,0,1,1,0,0,0,0,0,0,1,0,0,0,1,1,0,0,0,0,0], "Sốt rét"),
    ([1,0,1,1,0,0,0,0,0,0,0,1,0,0,1,1,0,0,1,1,0,0,0,0,0], "Sốt xuất huyết"),
    ([0,0,0,1,0,0,0,1,0,0,0,0,0,0,0,0,1,0,0,0,0,1,0,0,0], "Sỏi thận"),
    ([1,0,0,1,1,0,1,1,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0], "Viêm dạ dày"),
    ([0,0,1,1,0,0,0,0,0,0,1,0,0,0,0,0,0,0,1,0,0,0,1,0,1], "Thiếu máu"),
    ([0,0,0,1,0,0,0,0,1,1,0,0,0,0,0,0,1,0,1,0,0,0,0,1,0], "Suy tim"),
    ([1,0,0,1,0,0,0,0,0,0,0,0,1,0,1,0,0,0,1,1,0,0,0,0,0], "Viêm amidan"),
    ([0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,1,1,0,0,0,0,1,0,0,1], "Thoát vị đĩa đệm"),
    ([0,0,0,1,1,0,1,1,0,0,0,0,0,0,0,0,0,1,0,0,1,0,0,0,0], "Xơ gan"),
    ([0,0,0,1,0,0,0,1,0,0,0,0,0,0,0,1,1,0,0,0,0,1,0,0,0], "Ung thư dạ dày"),
    ([1,0,0,1,0,0,0,0,0,0,0,0,0,1,0,0,0,0,1,1,0,0,0,0,0], "Viêm xoang"),
    ([0,0,1,1,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,1,0,1], "Đau nửa đầu (Migraine)"),
]

MODEL_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)),
                           "utils", "disease_model.pkl")


# ── Background training thread ────────────────────────────
class TrainThread(QThread):
    finished = pyqtSignal(object)
    error    = pyqtSignal(str)

    def run(self):
        try:
            if not SKLEARN:
                self.error.emit("scikit-learn chưa được cài.\npip install scikit-learn numpy pandas")
                return
            X = np.array([d[0] for d in TRAINING_DATA], dtype=float)
            y = [d[1] for d in TRAINING_DATA]
            # Augment: add noise copies
            X_aug, y_aug = [X], y[:]
            rng = np.random.default_rng(42)
            for _ in range(15):
                noise = rng.integers(0, 2, size=X.shape)
                mask  = rng.random(X.shape) < 0.15
                X_noisy = np.clip(X + noise * mask, 0, 1)
                X_aug.append(X_noisy)
                y_aug.extend(y)
            X_final = np.vstack(X_aug)
            clf = RandomForestClassifier(n_estimators=200, max_depth=8,
                                          random_state=42, class_weight="balanced")
            clf.fit(X_final, y_aug)
            with open(MODEL_PATH, "wb") as f:
                import pickle; pickle.dump(clf, f)
            self.finished.emit(clf)
        except Exception as e:
            self.error.emit(str(e))


# ═══════════════════════════════════════════════════════════
#  AI Disease Prediction Tab
# ═══════════════════════════════════════════════════════════
class AIPredictionTab(QWidget):
    def __init__(self):
        super().__init__()
        self._model = None
        self._checkboxes = {}
        self._build_ui()
        self._apply_style()
        self._load_or_train_model()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # Header
        header = QHBoxLayout()
        title = QLabel("🔮 AI Dự đoán bệnh từ triệu chứng")
        title.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        title.setObjectName("sectionTitle")
        header.addWidget(title)
        header.addStretch()
        self.train_btn = QPushButton("🔁 Huấn luyện lại")
        self.train_btn.setObjectName("actionBtn")
        self.train_btn.clicked.connect(self._train_model)
        header.addWidget(self.train_btn)
        layout.addLayout(header)

        # Status bar
        self.status_lbl = QLabel("⏳ Đang tải mô hình AI...")
        self.status_lbl.setObjectName("statusLbl")
        layout.addWidget(self.status_lbl)

        self.progress = QProgressBar()
        self.progress.setTextVisible(False)
        self.progress.setMaximumHeight(4)
        self.progress.hide()
        layout.addWidget(self.progress)

        # Main content
        content = QHBoxLayout()
        content.setSpacing(16)

        # LEFT: symptom checkboxes
        left = QFrame()
        left.setObjectName("leftPanel")
        ll = QVBoxLayout(left)
        ll.setContentsMargins(16, 16, 16, 16)
        ll.setSpacing(8)

        ll.addWidget(QLabel("🩺 Chọn triệu chứng:"))

        # Search bar for symptoms
        self.sym_search = QLineEdit()
        self.sym_search.setPlaceholderText("Tìm triệu chứng...")
        self.sym_search.textChanged.connect(self._filter_symptoms)
        ll.addWidget(self.sym_search)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        sym_widget = QWidget()
        sym_grid = QGridLayout(sym_widget)
        sym_grid.setSpacing(6)
        sym_grid.setContentsMargins(0, 0, 0, 0)

        for i, sym in enumerate(SYMPTOMS):
            cb = QCheckBox(sym.capitalize())
            cb.setObjectName("symCheck")
            cb.stateChanged.connect(self._on_symptom_change)
            sym_grid.addWidget(cb, i // 2, i % 2)
            self._checkboxes[sym] = cb

        scroll.setWidget(sym_widget)
        ll.addWidget(scroll)

        btn_row = QHBoxLayout()
        self.predict_btn = QPushButton("🔍 Dự đoán bệnh")
        self.predict_btn.setObjectName("predictBtn")
        self.predict_btn.clicked.connect(self._predict)
        self.clear_btn = QPushButton("🗑️ Xoá chọn")
        self.clear_btn.setObjectName("clearBtn")
        self.clear_btn.clicked.connect(self._clear_symptoms)
        btn_row.addWidget(self.predict_btn)
        btn_row.addWidget(self.clear_btn)
        ll.addLayout(btn_row)

        content.addWidget(left, 2)

        # RIGHT: prediction results
        right = QFrame()
        right.setObjectName("rightPanel")
        rl = QVBoxLayout(right)
        rl.setContentsMargins(16, 16, 16, 16)
        rl.setSpacing(10)

        rl.addWidget(QLabel("📋 Kết quả dự đoán:"))

        # Top prediction card
        self.result_card = QFrame()
        self.result_card.setObjectName("resultCard")
        rcl = QVBoxLayout(self.result_card)
        rcl.setContentsMargins(16, 14, 16, 14)
        self.result_icon  = QLabel("🩺")
        self.result_icon.setFont(QFont("Segoe UI", 32))
        self.result_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.result_name  = QLabel("—")
        self.result_name.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        self.result_name.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.result_name.setObjectName("resultName")
        self.result_conf  = QLabel("Chọn triệu chứng và nhấn Dự đoán")
        self.result_conf.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.result_conf.setObjectName("resultConf")
        rcl.addWidget(self.result_icon)
        rcl.addWidget(self.result_name)
        rcl.addWidget(self.result_conf)
        rl.addWidget(self.result_card)

        # Top 5 results table
        rl.addWidget(QLabel("Top 5 bệnh khả năng cao:"))
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(3)
        self.results_table.setHorizontalHeaderLabels(["#", "Tên bệnh", "Xác suất"])
        self.results_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.results_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.results_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.results_table.setMaximumHeight(200)
        self.results_table.verticalHeader().setVisible(False)
        rl.addWidget(self.results_table)

        # Disclaimer
        disc = QLabel("⚠️ Đây chỉ là gợi ý hỗ trợ, không thay thế chẩn đoán của bác sĩ.")
        disc.setWordWrap(True)
        disc.setStyleSheet("color:#744210; background:#fffbeb; border-radius:6px; padding:8px; font-size:11px;")
        rl.addWidget(disc)
        rl.addStretch()

        content.addWidget(right, 3)
        layout.addLayout(content)

    # ── Model ────────────────────────────────────────────────────
    def _load_or_train_model(self):
        if not SKLEARN:
            self.status_lbl.setText("❌ scikit-learn chưa cài — pip install scikit-learn numpy")
            return
        if os.path.exists(MODEL_PATH):
            try:
                import pickle
                with open(MODEL_PATH, "rb") as f:
                    self._model = pickle.load(f)
                self.status_lbl.setText("✅ Mô hình AI đã sẵn sàng (Random Forest)")
                self.status_lbl.setStyleSheet("color:#276749; font-size:12px;")
                return
            except Exception:
                pass
        self._train_model()

    def _train_model(self):
        self.status_lbl.setText("⏳ Đang huấn luyện mô hình AI...")
        self.status_lbl.setStyleSheet("color:#744210; font-size:12px;")
        self.progress.setRange(0, 0)
        self.progress.show()
        self.train_btn.setEnabled(False)
        self._thread = TrainThread()
        self._thread.finished.connect(self._on_trained)
        self._thread.error.connect(self._on_train_error)
        self._thread.start()

    def _on_trained(self, model):
        self._model = model
        self.progress.hide()
        self.train_btn.setEnabled(True)
        self.status_lbl.setText("✅ Mô hình AI đã huấn luyện xong (Random Forest — 200 cây)")
        self.status_lbl.setStyleSheet("color:#276749; font-size:12px;")

    def _on_train_error(self, err):
        self.progress.hide()
        self.train_btn.setEnabled(True)
        self.status_lbl.setText(f"❌ Lỗi: {err}")
        self.status_lbl.setStyleSheet("color:#c53030; font-size:12px;")

    # ── Prediction ───────────────────────────────────────────────
    def _on_symptom_change(self):
        selected = sum(1 for cb in self._checkboxes.values() if cb.isChecked())
        self.predict_btn.setText(f"🔍 Dự đoán bệnh ({selected} triệu chứng)")

    def _filter_symptoms(self):
        query = self.sym_search.text().lower()
        for sym, cb in self._checkboxes.items():
            cb.setVisible(query in sym)

    def _clear_symptoms(self):
        for cb in self._checkboxes.values():
            cb.setChecked(False)
        self.result_name.setText("—")
        self.result_conf.setText("Chọn triệu chứng và nhấn Dự đoán")
        self.results_table.setRowCount(0)
        self.predict_btn.setText("🔍 Dự đoán bệnh")

    def _predict(self):
        if not self._model:
            QMessageBox.warning(self, "Mô hình chưa sẵn sàng",
                                "Mô hình AI chưa được huấn luyện.\nVui lòng chờ hoặc nhấn 'Huấn luyện lại'.")
            return

        vector = [1 if self._checkboxes[s].isChecked() else 0 for s in SYMPTOMS]
        if sum(vector) == 0:
            QMessageBox.information(self, "Chưa chọn triệu chứng",
                                    "Vui lòng chọn ít nhất một triệu chứng.")
            return

        import numpy as np
        proba = self._model.predict_proba([vector])[0]
        classes = self._model.classes_
        top5 = sorted(zip(classes, proba), key=lambda x: -x[1])[:5]

        # Top result
        best_disease, best_conf = top5[0]
        conf_pct = int(best_conf * 100)
        self.result_name.setText(best_disease)
        self.result_conf.setText(f"Xác suất: {conf_pct}%")

        # Color by confidence
        if conf_pct >= 70:
            color = "#c53030"; bg = "#fff5f5"
        elif conf_pct >= 40:
            color = "#744210"; bg = "#fffbeb"
        else:
            color = "#276749"; bg = "#f0fff4"
        self.result_name.setStyleSheet(f"color:{color}; background:transparent;")
        self.result_card.setStyleSheet(f"#resultCard {{ background:{bg}; border-radius:12px; border:2px solid {color}40; }}")

        # Fill table
        self.results_table.setRowCount(len(top5))
        for r, (disease, prob) in enumerate(top5):
            pct = int(prob * 100)
            self.results_table.setItem(r, 0, QTableWidgetItem(str(r+1)))
            self.results_table.setItem(r, 1, QTableWidgetItem(disease))
            pct_item = QTableWidgetItem(f"{pct}%")
            if pct >= 70:
                pct_item.setForeground(QColor("#c53030"))
                pct_item.setBackground(QColor("#fff5f5"))
            elif pct >= 40:
                pct_item.setForeground(QColor("#744210"))
            self.results_table.setItem(r, 2, pct_item)

    def _apply_style(self):
        self.setStyleSheet("""
        QWidget { background: #f7fafc; font-family: 'Segoe UI'; }
        #sectionTitle { color: #1a365d; }
        #statusLbl { font-size:12px; }
        #leftPanel, #rightPanel {
            background: white; border-radius: 10px; border: 1px solid #e2e8f0;
        }
        QLabel { font-size: 12px; color: #2d3748; }
        #symCheck { font-size: 12px; color: #2d3748; }
        QLineEdit {
            border: 1.5px solid #cbd5e0; border-radius: 6px;
            padding: 6px 10px; font-size: 12px; background: white;
        }
        #predictBtn {
            background: #553c9a; color: white; border: none;
            border-radius: 7px; padding: 9px 16px; font-weight: 600; font-size: 12px;
        }
        #predictBtn:hover { background: #44337a; }
        #clearBtn {
            background: #edf2f7; color: #4a5568; border: none;
            border-radius: 7px; padding: 9px 14px; font-size: 12px;
        }
        #actionBtn {
            background: #edf2f7; color: #2d3748; border: none;
            border-radius: 6px; padding: 7px 14px; font-size: 12px;
        }
        #resultName { font-size: 18px; font-weight: 700; }
        #resultConf { font-size: 13px; color: #718096; }
        QTableWidget { border: 1px solid #e2e8f0; font-size: 12px; }
        QHeaderView::section { background: #edf2f7; font-weight: 600; padding: 6px; border: none; }
        QProgressBar { border: none; background: #e2e8f0; border-radius: 2px; }
        QProgressBar::chunk { background: #553c9a; border-radius: 2px; }
        """)
