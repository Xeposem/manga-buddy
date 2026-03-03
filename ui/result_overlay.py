from PyQt5.QtCore import Qt, QRect, pyqtSignal
from PyQt5.QtGui import QPixmap, QPainter, QColor, QPen
from PyQt5.QtWidgets import (
    QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout,
    QGraphicsDropShadowEffect,
)


class ResultOverlay(QWidget):
    closed = pyqtSignal()

    def __init__(self, pixmap: QPixmap, screen_rect: QRect, parent=None):
        super().__init__(parent)
        self.setWindowFlags(
            Qt.FramelessWindowHint
            | Qt.WindowStaysOnTopHint
            | Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setGeometry(
            screen_rect.x() - 4,
            screen_rect.y() - 32,
            screen_rect.width() + 8,
            screen_rect.height() + 40,
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(0)

        # Top bar with title and close button
        top_bar = QHBoxLayout()
        top_bar.setContentsMargins(8, 2, 4, 2)

        title = QLabel("Manga Buddy")
        title.setStyleSheet(
            "color: rgba(255,255,255,0.9); font-size: 11px; font-weight: bold;"
        )
        top_bar.addWidget(title)
        top_bar.addStretch()

        close_btn = QPushButton("✕")
        close_btn.setObjectName("OverlayClose")
        close_btn.setFixedSize(28, 28)
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.clicked.connect(self._on_close)
        top_bar.addWidget(close_btn)

        layout.addLayout(top_bar)

        # Image display
        self._label = QLabel()
        self._label.setPixmap(pixmap)
        self._label.setStyleSheet(
            "border: 2px solid rgba(233, 69, 96, 0.6); border-radius: 4px;"
        )
        layout.addWidget(self._label)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setBrush(QColor(16, 21, 38, 220))
        painter.setPen(QPen(QColor(233, 69, 96, 120), 1))
        painter.drawRoundedRect(self.rect().adjusted(1, 1, -1, -1), 8, 8)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self._on_close()

    def _on_close(self):
        self.close()
        self.closed.emit()
