from PyQt5.QtCore import Qt, QRect, QPoint, pyqtSignal
from PyQt5.QtGui import QPainter, QColor, QPen, QFont
from PyQt5.QtWidgets import QWidget, QApplication


class RegionSelector(QWidget):
    region_selected = pyqtSignal(QRect)
    cancelled = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setCursor(Qt.CrossCursor)

        screen = QApplication.primaryScreen().geometry()
        self.setGeometry(screen)

        self._origin = QPoint()
        self._current = QPoint()
        self._selecting = False

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Dim background
        painter.fillRect(self.rect(), QColor(10, 10, 30, 120))

        if self._selecting:
            rect = QRect(self._origin, self._current).normalized()

            # Clear selected area
            painter.setCompositionMode(QPainter.CompositionMode_Clear)
            painter.fillRect(rect, Qt.transparent)
            painter.setCompositionMode(QPainter.CompositionMode_SourceOver)

            # Selection border — gradient-like double border
            outer_pen = QPen(QColor(233, 69, 96, 180), 3)
            painter.setPen(outer_pen)
            painter.drawRect(rect.adjusted(-2, -2, 2, 2))

            inner_pen = QPen(QColor(255, 255, 255, 200), 1)
            painter.setPen(inner_pen)
            painter.drawRect(rect)

            # Corner handles
            handle_color = QColor(233, 69, 96)
            painter.setBrush(handle_color)
            painter.setPen(Qt.NoPen)
            hs = 6
            for cx, cy in [
                (rect.left(), rect.top()),
                (rect.right(), rect.top()),
                (rect.left(), rect.bottom()),
                (rect.right(), rect.bottom()),
            ]:
                painter.drawEllipse(cx - hs, cy - hs, hs * 2, hs * 2)

            # Size label
            label = f"{rect.width()} × {rect.height()}"
            painter.setFont(QFont("Segoe UI", 10, QFont.Bold))
            lx = rect.center().x() - 40
            ly = rect.bottom() + 22
            painter.setBrush(QColor(233, 69, 96, 200))
            painter.setPen(Qt.NoPen)
            painter.drawRoundedRect(lx - 6, ly - 14, 92, 22, 6, 6)
            painter.setPen(QColor(255, 255, 255))
            painter.drawText(lx, ly, label)
        else:
            # Hint text
            painter.setPen(QColor(255, 255, 255, 180))
            painter.setFont(QFont("Segoe UI", 14))
            painter.drawText(self.rect(), Qt.AlignCenter,
                             "Click and drag to select a region  ·  Esc to cancel")

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._origin = event.pos()
            self._current = event.pos()
            self._selecting = True
            self.update()

    def mouseMoveEvent(self, event):
        if self._selecting:
            self._current = event.pos()
            self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and self._selecting:
            self._selecting = False
            rect = QRect(self._origin, event.pos()).normalized()
            self.close()
            if rect.width() > 10 and rect.height() > 10:
                self.region_selected.emit(rect)
            else:
                self.cancelled.emit()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self._selecting = False
            self.close()
            self.cancelled.emit()
