import sys
from PyQt6.QtWidgets import (
    QApplication, QWidget, QLabel, QVBoxLayout, QHBoxLayout,
    QPushButton, QMenu, QSizePolicy, QSystemTrayIcon
)
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import Qt, QPoint, QTimer, QPropertyAnimation, QEasingCurve, QUrl, QMimeData
from PyQt6.QtGui import QPixmap, QAction, QColor, QPainter, QPainterPath, QImage, QDrag


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
    TABS = ["텍스트", "이미지", "파일"]

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
        outer.setContentsMargins(14, t, 14, b)
        outer.setSpacing(10)

        # 탭 버튼 행
        tab_row = QHBoxLayout()
        tab_row.setSpacing(4)
        self._tab_btns = []
        for i, label in enumerate(self.TABS):
            btn = QPushButton(label)
            btn.setFixedHeight(26)
            btn.clicked.connect(lambda _, idx=i: self._switch_tab(idx))
            tab_row.addWidget(btn)
            self._tab_btns.append(btn)
        outer.addLayout(tab_row)

        # 아이템 영역
        self._content = QVBoxLayout()
        self._content.setSpacing(4)
        outer.addLayout(self._content)

        self._refresh_tabs()

    def set_history(self, history, on_select):
        self._history = history
        self._on_select = on_select
        self._refresh_content()

    def _switch_tab(self, idx):
        self._current_tab = idx
        self._refresh_tabs()
        self._refresh_content()
        QTimer.singleShot(0, self._relayout_parent)

    def _relayout_parent(self):
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
        for i, btn in enumerate(self._tab_btns):
            btn.setStyleSheet(TAB_ACTIVE if i == self._current_tab else TAB_INACTIVE)

    def _refresh_content(self):
        while self._content.count():
            item = self._content.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        tab_key = ["text", "image", "file"][self._current_tab]
        items = list(reversed(self._history.get(tab_key, [])))

        if not items:
            empty = QLabel("저장된 기록이 없어요")
            empty.setStyleSheet("color: #888; font-size: 12px;")
            self._content.addWidget(empty)
        elif tab_key == "text":
            for entry in items:
                e = {"type": "text", "data": entry}
                btn = DraggableButton(entry[:40] + ("…" if len(entry) > 40 else ""), e)
                btn.setToolTip(entry)
                btn.setFixedWidth(self.BUBBLE_W - 28)
                btn.setCursor(Qt.CursorShape.PointingHandCursor)
                btn.setStyleSheet(BTN_STYLE)
                btn.clicked.connect(lambda _, ev=e: self._select(ev))
                self._content.addWidget(btn)
        elif tab_key == "image":
            for entry in items:
                thumb = entry["data"].scaled(
                    self.BUBBLE_W - 28, 60,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
                btn = DraggableButton("  이미지 복사", entry)
                btn.setIcon(QIcon(QPixmap.fromImage(thumb)) if not thumb.isNull() else QIcon())
                btn.setIconSize(thumb.size())
                btn.setFixedWidth(self.BUBBLE_W - 28)
                btn.setCursor(Qt.CursorShape.PointingHandCursor)
                btn.setStyleSheet(BTN_STYLE)
                btn.clicked.connect(lambda _, e=entry: self._select(e))
                self._content.addWidget(btn)
        elif tab_key == "file":
            for entry in items:
                names = [QUrl(u).fileName() for u in entry["data"]]
                label = ", ".join(names)[:40] + ("…" if len(", ".join(names)) > 40 else "")
                btn = DraggableButton("📄 " + label, entry)
                btn.setToolTip("\n".join(entry["data"]))
                btn.setFixedWidth(self.BUBBLE_W - 28)
                btn.setCursor(Qt.CursorShape.PointingHandCursor)
                btn.setStyleSheet(BTN_STYLE)
                btn.clicked.connect(lambda _, e=entry: self._select(e))
                self._content.addWidget(btn)

        self.adjustSize()

    def _select(self, entry):
        if self._on_select:
            self._on_select(entry)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        tail, r = 12, 12
        cx = w / 2

        path = QPainterPath()
        if self._tail_top:
            path.addRoundedRect(0, tail, w, h - tail, r, r)
            path.moveTo(cx - 10, tail)
            path.lineTo(cx, 0)
            path.lineTo(cx + 10, tail)
        else:
            path.addRoundedRect(0, 0, w, h - tail, r, r)
            path.moveTo(cx - 10, h - tail)
            path.lineTo(cx, h)
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

        pixmap = QPixmap("pet.png")
        if pixmap.isNull():
            print("오류: pet.png 파일을 찾을 수 없습니다.")
            sys.exit(1)
        pixmap = pixmap.scaled(100, 100, Qt.AspectRatioMode.KeepAspectRatio,
                               Qt.TransformationMode.SmoothTransformation)
        self._pet_w = pixmap.width()
        self._pet_h = pixmap.height()

        self._pet_label = QLabel(self)
        self._pet_label.setPixmap(pixmap)
        self._pet_label.resize(self._pet_w, self._pet_h)

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

        self.setAcceptDrops(True)

        # 타입별 히스토리
        self.history = {"text": [], "image": [], "file": []}
        self._clipboard = QApplication.clipboard()
        self._last_text = self._clipboard.text()
        self._last_image_key = None

        self._clipboard_timer = QTimer(self)
        self._clipboard_timer.timeout.connect(self._check_clipboard)
        self._clipboard_timer.start(500)

        self._jump_anim = QPropertyAnimation(self, b"pos")
        self._jump_anim.setEasingCurve(QEasingCurve.Type.OutBounce)
        self._jump_anim.setDuration(500)

        self._apply_layout()

        screen = QApplication.primaryScreen().geometry()
        self.move(
            (screen.width() - self.width()) // 2,
            (screen.height() - self.height()) // 2
        )
        self.show()

    # ── 레이아웃 ────────────────────────────────────────────────────
    def _apply_layout(self):
        if self._bubble.isVisible():
            self._bubble.layout().activate()
            self._bubble.adjustSize()
            bw = self._bubble.width()
            bh = self._bubble.height()

            total_w = max(self._pet_w, bw)
            total_h = bh + self._pet_h
            self.resize(total_w, total_h)
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
            if not self.history["file"] or tuple(self.history["file"][-1]["data"]) != key:
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

    def _add_history(self, kind, entry):
        self.history[kind].append(entry)
        if len(self.history[kind]) > 5:
            self.history[kind].pop(0)

    # ── 점프 애니메이션 ─────────────────────────────────────────────
    def _jump(self):
        start = self.pos()
        self._jump_anim.setStartValue(QPoint(start.x(), start.y() - 30))
        self._jump_anim.setEndValue(start)
        self._jump_anim.start()

    # ── 말풍선 토글 ─────────────────────────────────────────────────
    def _show_bubble(self):
        if self._bubble.isVisible():
            self._close_bubble()
            return
        pet_screen = self.pos() + self._pet_label.pos()
        self._bubble.set_history(self.history, self._copy_from_history)
        self._bubble.show()
        QApplication.processEvents()
        self._apply_layout()
        self.move(pet_screen - self._pet_label.pos())

    def _close_bubble(self):
        if not self._bubble.isVisible():
            return
        pet_screen = self.pos() + self._pet_label.pos()
        self._bubble.hide()
        self._apply_layout()
        self.move(pet_screen - self._pet_label.pos())

    def _copy_from_history(self, entry):
        if entry["type"] == "text":
            self._clipboard.setText(entry["data"])
            self._last_text = entry["data"]
        elif entry["type"] == "image":
            self._clipboard.setImage(entry["data"])
            self._last_image_key = None
        elif entry["type"] == "file":
            mime = self._clipboard.mimeData().__class__()
            from PyQt6.QtCore import QMimeData
            md = QMimeData()
            md.setUrls([QUrl(u) for u in entry["data"]])
            self._clipboard.setMimeData(md)
        self._close_bubble()
        self._show_toast()
        self._jump()

    def _show_toast(self, msg="복사되었어요!"):
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
        pet_screen = self.pos()
        self.resize(total_w, th + self._pet_h)
        self._toast.move((total_w - tw) // 2, 0)
        self._pet_label.move((total_w - self._pet_w) // 2, th)
        self.move(pet_screen.x() - (total_w - self._pet_w) // 2, pet_screen.y() - th)

        self._toast.show()
        self._toast.raise_()
        self._toast_timer.start(1500)

    def _hide_toast(self):
        pet_screen = self.pos() + self._pet_label.pos()
        self._toast.hide()
        self.resize(self._pet_w, self._pet_h)
        self._pet_label.move(0, 0)
        self.move(pet_screen)

    # ── 마우스 이벤트 ───────────────────────────────────────────────
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_offset = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            self._press_pos = event.globalPosition().toPoint()
            self._drag_moved = False

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
                self._show_bubble()
            self._drag_moved = False

    def contextMenuEvent(self, event):
        menu = QMenu(self)
        lock_action = QAction("펫 고정 해제" if self._locked else "펫 고정", self)
        lock_action.triggered.connect(self._toggle_lock)
        menu.addAction(lock_action)
        menu.addSeparator()
        quit_action = QAction("종료", self)
        quit_action.triggered.connect(QApplication.quit)
        menu.addAction(quit_action)
        menu.exec(event.globalPos())

    def _toggle_lock(self):
        self._locked = not self._locked

    # ── 드래그앤드롭 ────────────────────────────────────────────────
    def dragEnterEvent(self, event):
        mime = event.mimeData()
        if mime.hasUrls() or mime.hasImage() or mime.hasText():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event):
        mime = event.mimeData()

        if mime.hasImage():
            img = mime.imageData()
            if img and not img.isNull():
                self._add_history("image", {"type": "image", "data": img})
                event.acceptProposedAction()
                self._show_toast("추가됐어요!")
                return

        if mime.hasUrls():
            image_exts = {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp", ".tiff"}
            image_urls, file_urls = [], []
            for url in mime.urls():
                ext = url.toLocalFile().lower()
                if any(ext.endswith(e) for e in image_exts):
                    img = QImage(url.toLocalFile())
                    if not img.isNull():
                        image_urls.append(("image", {"type": "image", "data": img}))
                    else:
                        file_urls.append(url.toString())
                else:
                    file_urls.append(url.toString())

            for kind, entry in image_urls:
                self._add_history(kind, entry)
            if file_urls:
                self._add_history("file", {"type": "file", "data": file_urls})

            event.acceptProposedAction()
            self._show_toast("추가됐어요!")
            return

        if mime.hasText():
            text = mime.text().strip()
            if text and text != self._last_text:
                self._add_history("text", text)
                self._last_text = text
            event.acceptProposedAction()
            self._show_toast("추가됐어요!")


class TrayPopup(QWidget):
    """메뉴바 아이콘 아래 말풍선 팝업 — BubbleWidget 재사용"""

    def __init__(self, pet):
        super().__init__(None, Qt.WindowType.FramelessWindowHint |
                         Qt.WindowType.WindowStaysOnTopHint |
                         Qt.WindowType.Popup)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self._bubble = BubbleWidget(self, on_relayout=self._relayout, tail_top=True)
        self._bubble.set_history(pet.history, lambda e: (pet._copy_from_history(e), self.close()))
        layout.addWidget(self._bubble)
        self.adjustSize()

    def _relayout(self):
        self.adjustSize()

    def show_at(self, x, y):
        self.adjustSize()
        screen = QApplication.primaryScreen().geometry()
        px = max(4, min(x - self.width() // 2, screen.width() - self.width() - 4))
        self.move(px, y)
        self.show()


class TrayIcon(QSystemTrayIcon):
    def __init__(self, pet):
        icon_pixmap = QPixmap("pet.png").scaled(
            64, 64, Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        super().__init__(QIcon(icon_pixmap))
        self._pet = pet
        self._popup = None
        self.setToolTip("Desktop Pet")
        self.activated.connect(self._on_activated)
        self.show()

    def _on_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            if self._popup and self._popup.isVisible():
                self._popup.close()
                return
            pos = self.geometry()
            self._popup = TrayPopup(self._pet)
            # 아이콘 아래, 중앙 정렬
            self._popup.show_at(pos.x() + pos.width() // 2, pos.y() + pos.height())


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)  # 트레이만 남아도 종료 안 됨
    pet = DesktopPet()
    tray = TrayIcon(pet)
    sys.exit(app.exec())
