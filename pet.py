import sys
import os
import json
import base64

# ── 다국어 ───────────────────────────────────────────────────────────
CONFIG_PATH = os.path.expanduser("~/.desktop_pet_config.json")

STRINGS = {
    "ko": {
        "tabs": ["텍스트", "이미지", "파일"],
        "empty": "저장된 기록이 없어요",
        "copied": "복사되었어요!",
        "added": "추가됐어요!",
        "lock": "펫 위치 고정",
        "unlock": "펫 위치 고정 해제",
        "touch_lock": "펫 터치 잠금",
        "touch_unlock": "펫 터치 잠금 해제",
        "settings": "설정",
        "quit": "종료",
        "autostart": "로그인 시 자동 실행",
        "autostart_on": "로그인 시 자동 실행  ✓",
        "language": "언어",
        "delete_title": "삭제",
        "delete_msg": "삭제할까요?",
        "delete_ok": "삭제",
        "delete_cancel": "취소",
        "quit_title": "종료",
        "quit_msg": "기록을 저장하고 종료할까요?",
        "quit_save": "저장 후 종료",
        "quit_no": "저장 안 함",
        "quit_cancel": "취소",
        "image_copy": "  이미지 복사",
        "confirm": "확인",
        "bubble_pos": "말풍선 위치",
        "bubble_above": "펫 위",
        "bubble_below": "펫 아래",
        "history_max": "기록 개수 (탭별)",
        "pet_size": "펫 크기",
        "text_add_placeholder": "텍스트 입력...",
        "text_add_btn": "추가",
        "hide_pet": "펫 가리기",
        "show_pet": "펫 표시",
    },
    "en": {
        "tabs": ["Text", "Image", "File"],
        "empty": "No saved history",
        "copied": "Copied!",
        "added": "Added!",
        "lock": "Lock position",
        "unlock": "Unlock position",
        "touch_lock": "Lock touch",
        "touch_unlock": "Unlock touch",
        "settings": "Settings",
        "quit": "Quit",
        "autostart": "Launch at login",
        "autostart_on": "Launch at login  ✓",
        "language": "Language",
        "delete_title": "Delete",
        "delete_msg": "Delete this item?",
        "delete_ok": "Delete",
        "delete_cancel": "Cancel",
        "quit_title": "Quit",
        "quit_msg": "Save history before quitting?",
        "quit_save": "Save & Quit",
        "quit_no": "Don't Save",
        "quit_cancel": "Cancel",
        "image_copy": "  Copy image",
        "confirm": "OK",
        "bubble_pos": "Bubble position",
        "bubble_above": "Above pet",
        "bubble_below": "Below pet",
        "history_max": "History limit (per tab)",
        "pet_size": "Pet size",
        "text_add_placeholder": "Enter text...",
        "text_add_btn": "Add",
        "hide_pet": "Hide pet",
        "show_pet": "Show pet",
    },
}

def _load_config():
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return {"lang": "ko"}

def _save_config(cfg):
    with open(CONFIG_PATH, "w") as f:
        json.dump(cfg, f)

_config = _load_config()

def tr(key):
    return STRINGS.get(_config.get("lang", "ko"), STRINGS["ko"]).get(key, key)

def set_lang(lang):
    _config["lang"] = lang
    _save_config(_config)

def resource_path(filename):
    """PyInstaller 빌드 시 리소스 경로 반환"""
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, filename)

from PyQt6.QtWidgets import (
    QApplication, QWidget, QLabel, QVBoxLayout, QHBoxLayout,
    QPushButton, QMenu, QSystemTrayIcon, QMessageBox, QScrollArea, QComboBox, QLineEdit
)
from PyQt6.QtGui import QIcon, QPalette
from PyQt6.QtCore import Qt, QPoint, QTimer, QPropertyAnimation, QEasingCurve, QUrl, QMimeData
from PyQt6.QtGui import QPixmap, QAction, QColor, QPainter, QPainterPath, QImage, QDrag


def _menu_style():
    p = QApplication.palette()
    hl = p.color(QPalette.ColorRole.Highlight).name()
    hl_text = p.color(QPalette.ColorRole.HighlightedText).name()
    return f"QMenu::item {{ padding: 3px 16px; }} QMenu::item:selected {{ background: {hl}; color: {hl_text}; }}"


BTN_STYLE = """
    QPushButton {
        background: #f5f5f5;
        border: 1px solid #aaaaaa;
        border-radius: 6px;
        padding: 6px 10px;
        font-size: 12px;
        text-align: left;
        color: #333;
    }
    QPushButton:hover { background: #dddddd; }
"""

TAB_ACTIVE = """
    QPushButton {
        background: #dddddd;
        border: 1px solid #aaaaaa;
        border-radius: 6px;
        padding: 4px 10px;
        font-size: 11px;
        font-weight: bold;
        color: #111;
    }
"""

TAB_INACTIVE = """
    QPushButton {
        background: #f5f5f5;
        border: 1px solid #cccccc;
        border-radius: 6px;
        padding: 4px 10px;
        font-size: 11px;
        color: #666;
    }
    QPushButton:hover { background: #ebebeb; }
"""


class DraggableButton(QPushButton):
    """드래그로 클립보드 항목을 꺼낼 수 있는 버튼"""

    def __init__(self, label, entry, parent=None):
        super().__init__(label, parent)
        self._entry = entry
        self._drag_start = QPoint()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_start = event.position().toPoint()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton:
            delta = event.position().toPoint() - self._drag_start
            if delta.manhattanLength() > 8:
                self._start_drag()
                return
        super().mouseMoveEvent(event)

    def _start_drag(self):
        mime = QMimeData()
        entry = self._entry

        if entry["type"] == "text":
            mime.setText(entry["data"])
        elif entry["type"] == "image":
            mime.setImageData(entry["data"])
        elif entry["type"] == "file":
            mime.setUrls([QUrl(u) for u in entry["data"]])

        drag = QDrag(self)
        drag.setMimeData(mime)

        if entry["type"] == "image":
            thumb = QPixmap.fromImage(entry["data"]).scaled(
                60, 60, Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            drag.setPixmap(thumb)

        drag.exec(Qt.DropAction.CopyAction)


class ToastBubble(QWidget):
    """'복사되었어요!' 같은 짧은 알림 말풍선"""

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 10, 14, 22)
        self._label = QLabel()
        self._label.setStyleSheet("font-size: 12px; color: #333;")
        self._label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._label)

    def set_message(self, msg):
        self._label.setText(msg)
        self.adjustSize()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        tail, r = 12, 12

        path = QPainterPath()
        path.addRoundedRect(0, 0, w, h - tail, r, r)
        cx = w / 2
        path.moveTo(cx - 10, h - tail)
        path.lineTo(cx, h)
        path.lineTo(cx + 10, h - tail)
        path.closeSubpath()

        painter.setBrush(QColor(245, 245, 245))
        painter.setPen(QColor(170, 170, 170))
        painter.drawPath(path)


class BubbleWidget(QWidget):
    BUBBLE_W = 240

    def __init__(self, parent=None, on_relayout=None, tail_top=False):
        super().__init__(parent)
        self._on_select = None
        self._on_relayout = on_relayout
        self._tail_top = tail_top
        self._current_tab = 0
        self._history = {"text": [], "image": [], "file": []}

        self.setFixedWidth(self.BUBBLE_W)

        outer = QVBoxLayout(self)
        t = 28 if self._tail_top else 16
        b = 16 if self._tail_top else 28
        outer.setContentsMargins(10, t, 10, b)
        outer.setSpacing(10)

        # 탭 버튼 행
        tab_row = QHBoxLayout()
        tab_row.setSpacing(4)
        self._tab_btns = []
        for i, label in enumerate(tr("tabs")):
            btn = QPushButton(label)
            btn.setFixedHeight(26)
            btn.clicked.connect(lambda _, idx=i: self._switch_tab(idx))
            tab_row.addWidget(btn)
            self._tab_btns.append(btn)
        outer.addLayout(tab_row)

        # 아이템 영역 (스크롤)
        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setMaximumHeight(200)
        self._scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._scroll.setStyleSheet("QScrollArea { border: none; background: #f5f5f5; } QWidget { background: #f5f5f5; }")
        scroll_inner = QWidget()
        self._content = QVBoxLayout(scroll_inner)
        self._content.setSpacing(4)
        self._content.setContentsMargins(0, 0, 0, 0)
        self._content.addStretch()
        self._scroll.setWidget(scroll_inner)
        outer.addWidget(self._scroll)

        # 텍스트 직접 입력 행 (텍스트 탭 전용)
        self._input_row = QWidget()
        input_hl = QHBoxLayout(self._input_row)
        input_hl.setContentsMargins(0, 0, 0, 0)
        input_hl.setSpacing(4)
        self._text_input = QLineEdit()
        self._text_input.setPlaceholderText(tr("text_add_placeholder"))
        self._text_input.setStyleSheet(
            "QLineEdit { border: 1px solid #ccc; border-radius: 6px;"
            " padding: 3px 6px; font-size: 12px; background: white; color: #333; }"
        )
        self._text_input.returnPressed.connect(self._add_text)
        input_hl.addWidget(self._text_input)
        self._add_btn = QPushButton(tr("text_add_btn"))
        self._add_btn.setFixedWidth(36)
        self._add_btn.setFixedHeight(26)
        self._add_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._add_btn.setStyleSheet(
            "QPushButton { background: #888; color: white; border-radius: 6px;"
            " font-size: 11px; } QPushButton:hover { background: #666; }"
        )
        self._add_btn.clicked.connect(self._add_text)
        input_hl.addWidget(self._add_btn)
        outer.addWidget(self._input_row)
        self._input_row.hide()

        self._refresh_tabs()

    def set_history(self, history, on_select):
        self._history = history
        self._on_select = on_select
        self._refresh_content()

    def _switch_tab(self, idx):
        self._current_tab = idx
        self._refresh_tabs()
        self._refresh_content()
        self._input_row.setVisible(idx == 0)
        QTimer.singleShot(0, self._relayout_parent)

    def _relayout_parent(self):
        self._scroll.widget().adjustSize()
        content_h = self._scroll.widget().sizeHint().height()
        self._scroll.setFixedHeight(min(content_h, 200))
        self.layout().activate()
        self.adjustSize()
        if self._on_relayout:
            self._on_relayout()
        else:
            p = self.parent()
            if p and hasattr(p, '_apply_layout'):
                pet_screen = p.pos() + p._pet_label.pos()
                p._apply_layout()
                p.move(pet_screen - p._pet_label.pos())

    def _refresh_tabs(self):
        for i, (btn, label) in enumerate(zip(self._tab_btns, tr("tabs"))):
            btn.setText(label)
            btn.setStyleSheet(TAB_ACTIVE if i == self._current_tab else TAB_INACTIVE)

    def _refresh_content(self):
        self._refresh_tabs()
        self._input_row.setVisible(self._current_tab == 0)
        self._text_input.setPlaceholderText(tr("text_add_placeholder"))
        self._add_btn.setText(tr("text_add_btn"))
        while self._content.count():
            item = self._content.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        tab_key = ["text", "image", "file"][self._current_tab]
        items = list(reversed(self._history.get(tab_key, [])))

        DEL_STYLE = """
            QPushButton {
                background: transparent;
                border: none;
                color: #aaaaaa;
                font-size: 15px;
                padding: 0 0px;
            }
            QPushButton:hover { color: #cc3333; }
        """

        def make_row(btn, raw_entry, tab_key):
            row = QWidget()
            row.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
            hl = QHBoxLayout(row)
            hl.setContentsMargins(0, 0, 0, 0)
            hl.setSpacing(4)
            hl.addWidget(btn)
            del_btn = QPushButton("✕")
            del_btn.setFixedSize(26, 28)
            del_btn.setStyleSheet(DEL_STYLE)
            del_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            del_btn.clicked.connect(lambda _, e=raw_entry, k=tab_key: self._delete(e, k))
            hl.addWidget(del_btn)
            return row

        if not items:
            empty = QLabel(tr("empty"))
            empty.setStyleSheet("color: #888; font-size: 12px;")
            self._content.addWidget(empty)
        elif tab_key == "text":
            for entry in items:
                e = {"type": "text", "data": entry}
                btn = DraggableButton(entry[:36] + ("…" if len(entry) > 36 else ""), e)
                btn.setToolTip(entry)
                btn.setFixedWidth(self.BUBBLE_W - 46)
                btn.setCursor(Qt.CursorShape.PointingHandCursor)
                btn.setStyleSheet(BTN_STYLE)
                btn.clicked.connect(lambda _, ev=e: self._select(ev))
                self._content.addWidget(make_row(btn, entry, tab_key))
        elif tab_key == "image":
            for entry in items:
                thumb = entry["data"].scaled(
                    self.BUBBLE_W - 56, 60,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
                img_label = os.path.basename(entry["path"]) if entry.get("path") else tr("image_copy")
                btn = DraggableButton(img_label, entry)
                btn.setIcon(QIcon(QPixmap.fromImage(thumb)) if not thumb.isNull() else QIcon())
                btn.setIconSize(thumb.size())
                btn.setFixedWidth(self.BUBBLE_W - 46)
                btn.setCursor(Qt.CursorShape.PointingHandCursor)
                btn.setStyleSheet(BTN_STYLE)
                btn.clicked.connect(lambda _, e=entry: self._select(e))
                self._content.addWidget(make_row(btn, entry, tab_key))
        elif tab_key == "file":
            for entry in items:
                names = [QUrl(u).fileName() for u in entry["data"]]
                label = ", ".join(names)[:36] + ("…" if len(", ".join(names)) > 36 else "")
                btn = DraggableButton("📄 " + label, entry)
                btn.setToolTip("\n".join(entry["data"]))
                btn.setFixedWidth(self.BUBBLE_W - 46)
                btn.setCursor(Qt.CursorShape.PointingHandCursor)
                btn.setStyleSheet(BTN_STYLE)
                btn.clicked.connect(lambda _, e=entry: self._select(e))
                self._content.addWidget(make_row(btn, entry, tab_key))
        self._content.addStretch()

        self._scroll.widget().adjustSize()
        content_h = self._scroll.widget().sizeHint().height()
        self._scroll.setFixedHeight(min(content_h, 200))

        self.adjustSize()

    def _delete(self, raw_entry, tab_key):
        msg = QMessageBox()
        msg.setWindowTitle(tr("delete_title"))
        msg.setText(tr("delete_msg"))
        msg.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        msg.setDefaultButton(QMessageBox.StandardButton.No)
        msg.button(QMessageBox.StandardButton.Yes).setText(tr("delete_ok"))
        msg.button(QMessageBox.StandardButton.No).setText(tr("delete_cancel"))
        if msg.exec() != QMessageBox.StandardButton.Yes:
            return
        lst = self._history.get(tab_key, [])
        if raw_entry in lst:
            lst.remove(raw_entry)
        self._refresh_content()
        QTimer.singleShot(0, self._relayout_parent)

    def _add_text(self):
        text = self._text_input.text().strip()
        if not text:
            return
        lst = self._history.setdefault("text", [])
        if text in lst:
            lst.remove(text)
        lst.append(text)
        max_n = _config.get("history_max", 10)
        while len(lst) > max_n:
            lst.pop(0)
        self._text_input.clear()
        self._refresh_content()
        QTimer.singleShot(0, self._relayout_parent)

    def _select(self, entry):
        if self._on_select:
            self._on_select(entry)

    def set_tail_top(self, val: bool):
        if self._tail_top == val:
            return
        self._tail_top = val
        t = 28 if val else 16
        b = 16 if val else 28
        self.layout().setContentsMargins(10, t, 10, b)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        tail, r = 12, 12
        cx = w / 2

        path = QPainterPath()
        if self._tail_top:
            # 꼬리가 위 — 단일 연속 패스
            path.moveTo(cx, 0)
            path.lineTo(cx + 10, tail)
            path.lineTo(w - r, tail)
            path.arcTo(w - r * 2, tail, r * 2, r * 2, 90, -90)
            path.lineTo(w, h - r)
            path.arcTo(w - r * 2, h - r * 2, r * 2, r * 2, 0, -90)
            path.lineTo(r, h)
            path.arcTo(0, h - r * 2, r * 2, r * 2, 270, -90)
            path.lineTo(0, tail + r)
            path.arcTo(0, tail, r * 2, r * 2, 180, -90)
            path.lineTo(cx - 10, tail)
        else:
            # 꼬리가 아래 — 단일 연속 패스
            path.moveTo(cx, h)
            path.lineTo(cx - 10, h - tail)
            path.lineTo(r, h - tail)
            path.arcTo(0, h - tail - r * 2, r * 2, r * 2, 270, -90)
            path.lineTo(0, r)
            path.arcTo(0, 0, r * 2, r * 2, 180, -90)
            path.lineTo(w - r, 0)
            path.arcTo(w - r * 2, 0, r * 2, r * 2, 90, -90)
            path.lineTo(w, h - tail - r)
            path.arcTo(w - r * 2, h - tail - r * 2, r * 2, r * 2, 0, -90)
            path.lineTo(cx + 10, h - tail)
        path.closeSubpath()

        painter.setBrush(QColor(245, 245, 245))
        painter.setPen(QColor(170, 170, 170))
        painter.drawPath(path)


class DesktopPet(QWidget):
    BUBBLE_W = 240

    def __init__(self):
        super().__init__()
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        sz = round(70 * _config.get("pet_size", 1.0))
        pixmap = QPixmap(resource_path("pets/cat/cat_defalt.png"))
        if pixmap.isNull():
            print("오류: cat_defalt.png 파일을 찾을 수 없습니다.")
            sys.exit(1)
        pixmap = pixmap.scaled(sz, sz, Qt.AspectRatioMode.KeepAspectRatio,
                               Qt.TransformationMode.SmoothTransformation)
        self._pet_w = sz
        self._pet_h = sz

        self._pet_label = QLabel(self)
        self._pet_label.setFixedSize(sz, sz)
        self._pet_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._pet_label.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self._pet_label.setStyleSheet("background: transparent;")
        self._pet_label.setPixmap(pixmap)

        self._bubble = BubbleWidget(self)
        self._bubble.hide()

        self._toast = ToastBubble(self)
        self._toast.hide()
        self._toast_timer = QTimer(self)
        self._toast_timer.setSingleShot(True)
        self._toast_timer.timeout.connect(self._hide_toast)

        self._drag_offset = QPoint()
        self._press_pos = QPoint()
        self._drag_moved = False
        self._locked = False
        self._touch_locked = False

        self.setAcceptDrops(True)

        # 타입별 히스토리
        self.history = {"text": [], "image": [], "file": []}
        self._clipboard = QApplication.clipboard()
        self._last_text = None
        self._last_image_key = None
        self._last_file_key = None

        self._clipboard_timer = QTimer(self)
        self._clipboard_timer.timeout.connect(self._check_clipboard)
        self._clipboard_timer.start(500)

        self._jump_anim = QPropertyAnimation(self, b"pos")
        self._jump_anim.setEasingCurve(QEasingCurve.Type.OutBounce)
        self._jump_anim.setDuration(500)

        self._idle = False
        self._just_woke = False
        self._idle_timer = QTimer(self)
        self._idle_timer.setSingleShot(True)
        self._idle_timer.timeout.connect(self._on_idle)
        self._idle_timer.start(60000)

        self._load_history()
        self._apply_layout()

        screen = QApplication.primaryScreen().geometry()
        self.move(
            (screen.width() - self.width()) // 2,
            (screen.height() - self.height()) // 2
        )
        self.show()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Source)
        painter.fillRect(self.rect(), QColor(0, 0, 0, 0))

    # ── 레이아웃 ────────────────────────────────────────────────────
    def _apply_layout(self):
        if self._bubble.isVisible():
            self._bubble.layout().activate()
            hint = self._bubble.sizeHint()
            bw = max(hint.width(), self.BUBBLE_W)
            bh = hint.height()
            self._bubble.resize(bw, bh)

            total_w = max(self._pet_w, bw)
            total_h = bh + self._pet_h
            self.resize(total_w, total_h)

            bubble_below = _config.get("bubble_pos", "above") == "below"
            self._bubble.set_tail_top(bubble_below)
            if bubble_below:
                self._pet_label.move((total_w - self._pet_w) // 2, 0)
                self._bubble.move((total_w - bw) // 2, self._pet_h)
            else:
                self._bubble.move((total_w - bw) // 2, 0)
                self._pet_label.move((total_w - self._pet_w) // 2, bh)
        else:
            self.resize(self._pet_w, self._pet_h)
            self._pet_label.move(0, 0)

    # ── 클립보드 감시 ───────────────────────────────────────────────
    def _check_clipboard(self):
        mime = self._clipboard.mimeData()

        # 파일
        if mime.hasUrls():
            urls = [u.toString() for u in mime.urls()]
            key = tuple(urls)
            if key != self._last_file_key:
                self._last_file_key = key
                self._add_history("file", {"type": "file", "data": urls})
            return

        # 이미지
        if mime.hasImage():
            img = self._clipboard.image()
            if not img.isNull():
                key = (img.width(), img.height(), img.pixel(0, 0))
                if key != self._last_image_key:
                    self._last_image_key = key
                    self._add_history("image", {"type": "image", "data": img})
            return

        # 텍스트
        text = self._clipboard.text()
        if text and text != self._last_text:
            self._last_text = text
            self._add_history("text", text)

    @property
    def HISTORY_MAX(self):
        n = _config.get("history_max", 10)
        return {"text": n, "image": n, "file": n}

    def _add_history(self, kind, entry):
        lst = self.history[kind]
        # 텍스트/파일은 data 값으로 중복 비교, 이미지는 크기+픽셀로 비교
        if kind == "text":
            if entry in lst:
                lst.remove(entry)
        elif kind == "file":
            key = tuple(entry["data"])
            for existing in lst:
                if tuple(existing["data"]) == key:
                    lst.remove(existing)
                    break
        lst.append(entry)
        if len(lst) > self.HISTORY_MAX[kind]:
            lst.pop(0)

    # ── 점프 애니메이션 ─────────────────────────────────────────────
    def _rest_pos(self):
        """점프 중이면 목표 위치, 아니면 현재 위치 반환"""
        if self._jump_anim.state() == QPropertyAnimation.State.Running:
            return self._jump_anim.endValue()
        return self.pos()

    def _ns_redraw(self):
        """macOS 창 합성 캐시 강제 무효화 — 잔상 제거"""
        try:
            import ctypes, objc
            ns_view = objc.objc_object(c_void_p=ctypes.c_void_p(int(self.winId())))
            ns_win = ns_view.window()
            if ns_win:
                ns_win.invalidateShadow()  # 그림자 재계산 → 창 전체 재합성 트리거
        except Exception:
            pass

    def _jump(self):
        start = self._rest_pos()
        self._jump_anim.setStartValue(QPoint(start.x(), start.y() - 20))
        self._jump_anim.setEndValue(start)
        try:
            self._jump_anim.finished.disconnect()
        except TypeError:
            pass
        self._jump_anim.finished.connect(self._ns_redraw)
        self._jump_anim.start()

    # ── 말풍선 토글 ─────────────────────────────────────────────────
    def _stop_jump(self):
        """점프 중이면 즉시 중단하고 목표 위치로 스냅"""
        if self._jump_anim.state() == QPropertyAnimation.State.Running:
            end = self._jump_anim.endValue()
            self._jump_anim.stop()
            self.move(end)

    def _show_bubble(self):
        if self._bubble.isVisible():
            self._close_bubble()
            return
        pet_screen = self._rest_pos() + self._pet_label.pos()
        self._bubble.set_history(self.history, self._copy_from_history)
        self._bubble.show()
        self._apply_layout()
        self.move(pet_screen - self._pet_label.pos())

    def _close_bubble(self):
        if not self._bubble.isVisible():
            return
        pet_screen = self._rest_pos() + self._pet_label.pos()
        self._bubble.hide()
        self._apply_layout()
        self.move(pet_screen - self._pet_label.pos())

    def _copy_from_history(self, entry):
        self._reset_idle()
        if entry["type"] == "text":
            self._clipboard.setText(entry["data"])
            self._last_text = entry["data"]
        elif entry["type"] == "image":
            self._clipboard.setImage(entry["data"])
            self._last_image_key = None
        elif entry["type"] == "file":
            md = QMimeData()
            md.setUrls([QUrl(u) for u in entry["data"]])
            self._clipboard.setMimeData(md)
        self._close_bubble()
        self._show_toast()
        self._jump()

    def _show_toast(self, msg=None):
        if msg is None:
            msg = tr("copied")
        # 버블/토스트가 열려있으면 먼저 정리
        if self._bubble.isVisible():
            self._close_bubble()
        if self._toast.isVisible():
            self._toast_timer.stop()
            self._hide_toast()

        self._toast.set_message(msg)
        tw = self._toast.width()
        th = self._toast.height()
        total_w = max(self._pet_w, tw)

        # pet_label이 항상 (0,0)에 있는 상태에서 호출됨
        pet_screen = self._rest_pos()
        self.resize(total_w, th + self._pet_h)
        self._toast.move((total_w - tw) // 2, 0)
        self._pet_label.move((total_w - self._pet_w) // 2, th)
        self.move(pet_screen.x() - (total_w - self._pet_w) // 2, pet_screen.y() - th)

        self._toast.show()
        self._toast.raise_()
        self._toast_timer.start(800)

    def _hide_toast(self):
        pet_screen = self._rest_pos() + self._pet_label.pos()
        self._toast.hide()
        self.resize(self._pet_w, self._pet_h)
        self._pet_label.move(0, 0)
        self.move(pet_screen)

    # ── 마우스 이벤트 ───────────────────────────────────────────────
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            # _reset_idle()보다 먼저 계산 — start()가 즉시 pos를 y-20으로 바꿔버려서
            # 그 이후에 계산하면 drag_offset이 틀어짐
            self._drag_offset = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            self._press_pos = event.globalPosition().toPoint()
            self._drag_moved = False
            self._reset_idle()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton and not self._locked:
            delta = event.globalPosition().toPoint() - self._press_pos
            if delta.manhattanLength() > 6:
                self._drag_moved = True
            if self._drag_moved:
                self.move(event.globalPosition().toPoint() - self._drag_offset)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            local = event.position().toPoint()
            if not self._drag_moved and self._pet_label.geometry().contains(local):
                if not self._toast.isVisible() and not self._touch_locked:
                    if self._just_woke:
                        self._just_woke = False  # 깨운 터치 → 말풍선 스킵
                    else:
                        self._show_bubble()
            else:
                self._just_woke = False  # 드래그나 영역 밖 클릭 시에도 플래그 초기화
            self._drag_moved = False

    def contextMenuEvent(self, event):
        menu = QMenu(self)
        menu.setStyleSheet(_menu_style())
        hide_action = QAction(tr("hide_pet"), self)
        hide_action.triggered.connect(self.hide)
        menu.addAction(hide_action)
        lock_action = QAction(tr("unlock") if self._locked else tr("lock"), self)
        lock_action.triggered.connect(self._toggle_lock)
        menu.addAction(lock_action)
        touch_action = QAction(tr("touch_unlock") if self._touch_locked else tr("touch_lock"), self)
        touch_action.triggered.connect(self._toggle_touch_lock)
        menu.addAction(touch_action)
        settings_action = QAction(tr("settings"), self)
        settings_action.triggered.connect(self._open_settings)
        menu.addAction(settings_action)
        menu.addSeparator()
        quit_action = QAction(tr("quit"), self)
        quit_action.triggered.connect(self._quit)
        menu.addAction(quit_action)
        menu.exec(event.globalPos())

    def _open_settings(self):
        self._settings_win = SettingsWindow(pet=self)
        self._settings_win.show()
        self._settings_win.raise_()

    def _toggle_lock(self):
        self._locked = not self._locked
        self._set_pet_image("pets/cat/cat_box.png" if self._locked else "pets/cat/cat_defalt.png")

    def _toggle_touch_lock(self):
        self._touch_locked = not self._touch_locked

    # ── 저장 / 불러오기 ─────────────────────────────────────────────
    SAVE_PATH = os.path.expanduser("~/.desktop_pet_history.json")

    def _save_history(self):
        data = {"text": self.history["text"], "file": self.history["file"], "image": []}
        for entry in self.history["image"]:
            buf = entry["data"]
            ba = buf.bits().asarray(buf.sizeInBytes())
            b64 = base64.b64encode(bytes(ba)).decode()
            data["image"].append({
                "type": "image", "w": buf.width(), "h": buf.height(),
                "fmt": int(buf.format()), "data": b64
            })
        with open(self.SAVE_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False)

    def _load_history(self):
        if not os.path.exists(self.SAVE_PATH):
            return
        try:
            with open(self.SAVE_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.history["text"] = data.get("text", [])
            self.history["file"] = data.get("file", [])
            for entry in data.get("image", []):
                raw = base64.b64decode(entry["data"])
                img = QImage(entry["w"], entry["h"], QImage.Format(entry["fmt"]))
                img.bits().setsize(len(raw))
                for i, b in enumerate(raw):
                    img.bits()[i] = b
                self.history["image"].append({"type": "image", "data": img})
        except Exception:
            pass
        finally:
            os.remove(self.SAVE_PATH)

    def _quit(self):
        msg = QMessageBox()
        msg.setWindowTitle(tr("quit_title"))
        msg.setText(tr("quit_msg"))
        msg.setStandardButtons(
            QMessageBox.StandardButton.Yes |
            QMessageBox.StandardButton.No |
            QMessageBox.StandardButton.Cancel
        )
        msg.button(QMessageBox.StandardButton.Yes).setText(tr("quit_save"))
        msg.button(QMessageBox.StandardButton.No).setText(tr("quit_no"))
        msg.button(QMessageBox.StandardButton.Cancel).setText(tr("quit_cancel"))
        msg.setDefaultButton(QMessageBox.StandardButton.Yes)
        result = msg.exec()
        if result == QMessageBox.StandardButton.Cancel:
            return
        if result == QMessageBox.StandardButton.Yes:
            self._save_history()
        QApplication.quit()

    # ── 유휴 상태 ───────────────────────────────────────────────────
    def _on_idle(self):
        self._idle = True
        self._set_pet_image("pets/cat/cat_zz.png")

    def _reset_idle(self, jump=True):
        self._idle_timer.start(60000)
        if self._idle:
            self._idle = False
            self._just_woke = True
            img = "pets/cat/cat_box.png" if self._locked else "pets/cat/cat_defalt.png"
            self._set_pet_image(img)
            if jump:
                self._jump()

    # ── 펫 이미지 전환 ──────────────────────────────────────────────
    def _set_pet_image(self, filename):
        src = QPixmap(resource_path(filename))
        sz = self._pet_w
        if not src.isNull():
            scaled = src.scaled(sz, sz, Qt.AspectRatioMode.KeepAspectRatio,
                                Qt.TransformationMode.SmoothTransformation)
            canvas = QPixmap(sz, sz)
            canvas.fill(Qt.GlobalColor.transparent)
            painter = QPainter(canvas)
            painter.drawPixmap((sz - scaled.width()) // 2,
                               (sz - scaled.height()) // 2, scaled)
            painter.end()
            self._pet_label.clear()
            self._pet_label.setPixmap(canvas)
            self.repaint()
            QTimer.singleShot(0, self._ns_redraw)

    def apply_pet_size(self, scale):
        """설정에서 크기 변경 시 호출"""
        sz = round(70 * scale)
        self._pet_w = sz
        self._pet_h = sz
        self._pet_label.setFixedSize(sz, sz)
        img = "pets/cat/cat_box.png" if self._locked else \
              "pets/cat/cat_zz.png" if self._idle else "pets/cat/cat_defalt.png"
        self._set_pet_image(img)
        self._apply_layout()

    # ── 드래그앤드롭 ────────────────────────────────────────────────
    def dragEnterEvent(self, event):
        mime = event.mimeData()
        if mime.hasUrls() or mime.hasImage() or mime.hasText():
            img = "pets/cat/cat_box_ahh.png" if self._locked else "pets/cat/cat_ahh.png"
            self._set_pet_image(img)
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragLeaveEvent(self, event):
        img = "pets/cat/cat_box.png" if self._locked else "pets/cat/cat_defalt.png"
        self._set_pet_image(img)

    def dropEvent(self, event):
        self._reset_idle(jump=False)
        img = "pets/cat/cat_box.png" if self._locked else "pets/cat/cat_defalt.png"
        self._set_pet_image(img)
        mime = event.mimeData()

        if mime.hasImage():
            img = mime.imageData()
            if img and not img.isNull():
                self._add_history("image", {"type": "image", "data": img})
                event.acceptProposedAction()
                self._show_toast(tr("added"))
                self._jump()
                return

        if mime.hasUrls():
            image_exts = {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp", ".tiff"}
            image_urls, file_urls = [], []
            for url in mime.urls():
                ext = url.toLocalFile().lower()
                if any(ext.endswith(e) for e in image_exts):
                    img = QImage(url.toLocalFile())
                    if not img.isNull():
                        image_urls.append(("image", {"type": "image", "data": img, "path": url.toLocalFile()}))
                    else:
                        file_urls.append(url.toString())
                else:
                    file_urls.append(url.toString())

            for kind, entry in image_urls:
                self._add_history(kind, entry)
            if file_urls:
                self._add_history("file", {"type": "file", "data": file_urls})

            # 드롭 후 클립보드 현재 파일키로 동기화 (중복 방지)
            cb_mime = self._clipboard.mimeData()
            if cb_mime.hasUrls():
                self._last_file_key = tuple(u.toString() for u in cb_mime.urls())
            elif file_urls:
                self._last_file_key = tuple(file_urls)

            event.acceptProposedAction()
            self._show_toast(tr("added"))
            self._jump()
            return

        if mime.hasText():
            text = mime.text().strip()
            if text and text != self._last_text:
                self._add_history("text", text)
                self._last_text = text
            event.acceptProposedAction()
            self._show_toast(tr("added"))
            self._jump()


class SettingsWindow(QWidget):
    """설정 창"""
    PLIST_PATH = os.path.expanduser("~/Library/LaunchAgents/com.desktoppet.plist")

    def __init__(self, parent=None, pet=None):
        super().__init__(parent, Qt.WindowType.Window)
        self._pet = pet
        self.setWindowTitle(tr("settings"))
        self.setFixedWidth(280)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        def make_section(label_widget, combo_widget):
            box = QVBoxLayout()
            box.setSpacing(3)
            box.addWidget(label_widget)
            box.addWidget(combo_widget)
            return box

        # 언어 선택
        lang_label = QLabel(tr("language"))
        lang_label.setStyleSheet("font-size: 12px; color: #555;")
        self._lang_combo = QComboBox()
        self._lang_combo.addItem("한국어", "ko")
        self._lang_combo.addItem("English", "en")
        cur = _config.get("lang", "ko")
        self._lang_combo.setCurrentIndex(0 if cur == "ko" else 1)
        self._lang_combo.currentIndexChanged.connect(
            lambda: self._set_lang(self._lang_combo.currentData())
        )
        layout.addLayout(make_section(lang_label, self._lang_combo))

        # 말풍선 위치
        self._bubble_pos_label = QLabel(tr("bubble_pos"))
        self._bubble_pos_label.setStyleSheet("font-size: 12px; color: #555;")
        self._bubble_pos_combo = QComboBox()
        self._bubble_pos_combo.addItem(tr("bubble_above"), "above")
        self._bubble_pos_combo.addItem(tr("bubble_below"), "below")
        cur_pos = _config.get("bubble_pos", "above")
        self._bubble_pos_combo.setCurrentIndex(0 if cur_pos == "above" else 1)
        self._bubble_pos_combo.currentIndexChanged.connect(self._set_bubble_pos)
        layout.addLayout(make_section(self._bubble_pos_label, self._bubble_pos_combo))

        # 기록 개수
        self._history_max_label = QLabel(tr("history_max"))
        self._history_max_label.setStyleSheet("font-size: 12px; color: #555;")
        self._history_max_combo = QComboBox()
        for n in (5, 10, 15, 20):
            self._history_max_combo.addItem(f"{n}", n)
        cur_max = _config.get("history_max", 10)
        idx = {5: 0, 10: 1, 15: 2, 20: 3}.get(cur_max, 1)
        self._history_max_combo.setCurrentIndex(idx)
        self._history_max_combo.currentIndexChanged.connect(self._set_history_max)
        layout.addLayout(make_section(self._history_max_label, self._history_max_combo))

        # 펫 크기
        self._pet_size_label = QLabel(tr("pet_size"))
        self._pet_size_label.setStyleSheet("font-size: 12px; color: #555;")
        _size_options = [0.5, 0.75, 1.0, 1.25, 1.5, 1.75, 2.0]
        self._pet_size_combo = QComboBox()
        for s in _size_options:
            self._pet_size_combo.addItem(f"{s}x", s)
        cur_scale = _config.get("pet_size", 1.0)
        best = min(range(len(_size_options)), key=lambda i: abs(_size_options[i] - cur_scale))
        self._pet_size_combo.setCurrentIndex(best)
        self._pet_size_combo.currentIndexChanged.connect(self._set_pet_size)
        layout.addLayout(make_section(self._pet_size_label, self._pet_size_combo))

        # 자동 실행
        self._autostart_btn = QPushButton()
        self._autostart_btn.setCheckable(True)
        self._autostart_btn.setChecked(self._is_autostart())
        self._autostart_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._autostart_btn.clicked.connect(self._toggle_autostart)
        self._update_label()
        layout.addWidget(self._autostart_btn)
        layout.addStretch()

        self._confirm_btn = QPushButton(tr("confirm"))
        self._confirm_btn.setFixedWidth(80)
        self._confirm_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._confirm_btn.clicked.connect(self.close)
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        btn_row.addWidget(self._confirm_btn)
        btn_row.addStretch()
        layout.addLayout(btn_row)
        self.adjustSize()

    def _set_lang(self, lang):
        set_lang(lang)
        self._update_label()
        self.setWindowTitle(tr("settings"))
        self._confirm_btn.setText(tr("confirm"))
        self._bubble_pos_label.setText(tr("bubble_pos"))
        self._history_max_label.setText(tr("history_max"))
        self._pet_size_label.setText(tr("pet_size"))
        cur = self._bubble_pos_combo.currentIndex()
        self._bubble_pos_combo.blockSignals(True)
        self._bubble_pos_combo.clear()
        self._bubble_pos_combo.addItem(tr("bubble_above"), "above")
        self._bubble_pos_combo.addItem(tr("bubble_below"), "below")
        self._bubble_pos_combo.setCurrentIndex(cur)
        self._bubble_pos_combo.blockSignals(False)

    def _set_bubble_pos(self):
        _config["bubble_pos"] = self._bubble_pos_combo.currentData()
        _save_config(_config)

    def _set_history_max(self):
        _config["history_max"] = self._history_max_combo.currentData()
        _save_config(_config)

    def _set_pet_size(self):
        scale = self._pet_size_combo.currentData()
        _config["pet_size"] = scale
        _save_config(_config)
        if self._pet:
            self._pet.apply_pet_size(scale)

    def _is_autostart(self):
        return os.path.exists(self.PLIST_PATH)

    def _update_label(self):
        if self._is_autostart():
            self._autostart_btn.setText(tr("autostart_on"))
        else:
            self._autostart_btn.setText(tr("autostart"))

    def _toggle_autostart(self):
        if self._is_autostart():
            os.remove(self.PLIST_PATH)
        else:
            script = os.path.abspath(resource_path("pet.py"))
            python = sys.executable
            plist = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.desktoppet</string>
    <key>ProgramArguments</key>
    <array>
        <string>{python}</string>
        <string>{script}</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
</dict>
</plist>"""
            os.makedirs(os.path.dirname(self.PLIST_PATH), exist_ok=True)
            with open(self.PLIST_PATH, "w") as f:
                f.write(plist)
        self._update_label()


class TrayPopup(QWidget):
    """메뉴바 아이콘 아래 말풍선 팝업 — BubbleWidget 재사용"""

    def __init__(self, pet):
        super().__init__(None, Qt.WindowType.FramelessWindowHint |
                         Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self._bubble = BubbleWidget(self, on_relayout=self._relayout, tail_top=True)
        self._bubble.set_history(pet.history, lambda e: (pet._copy_from_history(e), self.close()))
        layout.addWidget(self._bubble)
        self.adjustSize()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Source)
        painter.fillRect(self.rect(), QColor(0, 0, 0, 0))

    def _relayout(self):
        self.adjustSize()

    def show_at(self, x, y):
        self.adjustSize()
        screen = QApplication.primaryScreen().geometry()
        px = max(4, min(x - self.width() // 2, screen.width() - self.width() - 4))
        self.move(px, y)
        self.show()
        self.raise_()
        try:
            from AppKit import NSApplication
            NSApplication.sharedApplication().activateIgnoringOtherApps_(True)
        except Exception:
            pass


class TrayIcon(QSystemTrayIcon):
    def __init__(self, pet):
        icon_pixmap = QPixmap(resource_path("pets/cat/cat_defalt.png")).scaled(
            64, 64, Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        super().__init__(QIcon(icon_pixmap))
        self._pet = pet
        self._popup = None
        self.setToolTip("Desktop Pet")
        self._menu = QMenu()
        self._menu.setStyleSheet(_menu_style())
        self._hide_action = QAction(tr("hide_pet"), self._menu)
        self._hide_action.triggered.connect(self._toggle_visibility)
        self._menu.addAction(self._hide_action)
        self._lock_action = QAction("", self._menu)
        self._lock_action.triggered.connect(self._toggle_lock)
        self._menu.addAction(self._lock_action)
        self._touch_action = QAction("", self._menu)
        self._touch_action.triggered.connect(self._toggle_touch_lock)
        self._menu.addAction(self._touch_action)
        self._settings_action = QAction(tr("settings"), self._menu)
        self._settings_action.triggered.connect(self._pet._open_settings)
        self._menu.addAction(self._settings_action)
        self._menu.addSeparator()
        self._quit_action = QAction(tr("quit"), self._menu)
        self._quit_action.triggered.connect(self._pet._quit)
        self._menu.addAction(self._quit_action)
        self.activated.connect(self._on_activated)
        self.show()

    def _toggle_lock(self):
        self._pet._toggle_lock()
        self._lock_action.setText(tr("unlock") if self._pet._locked else tr("lock"))

    def _toggle_touch_lock(self):
        self._pet._toggle_touch_lock()
        self._touch_action.setText(tr("touch_unlock") if self._pet._touch_locked else tr("touch_lock"))

    def _toggle_visibility(self):
        if self._pet.isVisible():
            self._pet.hide()
        else:
            self._pet.show()
            self._pet.raise_()

    def _on_activated(self, reason):
        if reason != QSystemTrayIcon.ActivationReason.Context:
            # macOS에서 Trigger 외 다른 reason으로 올 수 있어서 Context 아닌 모든 클릭 처리
            if self._popup and self._popup.isVisible():
                self._popup.close()
                self._popup.deleteLater()
                self._popup = None
                return
            if self._popup:
                self._popup.deleteLater()
                self._popup = None
            from PyQt6.QtGui import QCursor
            cursor = QCursor.pos()
            menu_bar_bottom = QApplication.primaryScreen().availableGeometry().y()
            self._popup = TrayPopup(self._pet)
            self._popup.show_at(cursor.x(), menu_bar_bottom)
        elif reason == QSystemTrayIcon.ActivationReason.Context:
            self._lock_action.setText(tr("unlock") if self._pet._locked else tr("lock"))
            self._touch_action.setText(tr("touch_unlock") if self._pet._touch_locked else tr("touch_lock"))
            self._settings_action.setText(tr("settings"))
            self._hide_action.setText(tr("show_pet") if not self._pet.isVisible() else tr("hide_pet"))
            self._quit_action.setText(tr("quit"))
            from PyQt6.QtGui import QCursor
            self._menu.exec(QCursor.pos())


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)  # 트레이만 남아도 종료 안 됨

    try:
        from AppKit import NSApplication, NSApplicationActivationPolicy
        NSApplication.sharedApplication().setActivationPolicy_(
            NSApplicationActivationPolicy.NSApplicationActivationPolicyAccessory
        )
    except Exception:
        pass

    pet = DesktopPet()
    tray = TrayIcon(pet)
    sys.exit(app.exec())
