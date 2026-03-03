from PyQt5.QtCore import Qt, QRect, QThread, pyqtSignal, QObject, QSize
from PyQt5.QtGui import QPixmap, QImage, QIcon, QFont
from PyQt5.QtWidgets import (
    QWidget, QPushButton, QComboBox, QLabel,
    QVBoxLayout, QHBoxLayout, QMessageBox, QGraphicsDropShadowEffect,
)
from PIL import ImageGrab

from ui.region_selector import RegionSelector
from ui.result_overlay import ResultOverlay
from core.ocr_engine import OcrEngine
from core.translator import Translator
from core.pinyin_converter import PinyinConverter
from core.text_placer import TextPlacer
from core.image_renderer import ImageRenderer


class PipelineWorker(QObject):
    finished = pyqtSignal(object, object)
    error = pyqtSignal(str)

    def __init__(self, image, mode, overlay_mode, ocr, translator, pinyin_conv, renderer):
        super().__init__()
        self.image = image
        self.mode = mode
        self.overlay_mode = overlay_mode
        self.ocr = ocr
        self.translator = translator
        self.pinyin_conv = pinyin_conv
        self.renderer = renderer

    def run(self):
        try:
            regions = self.ocr.detect(self.image)
            if not regions:
                self.error.emit("No text detected in the selected region.")
                return

            if self.mode == "Translation":
                self.translator.translate_batch(regions)
            else:
                self.pinyin_conv.convert_batch(regions)

            placer = TextPlacer(self.image.width, self.image.height)
            mode_key = "translation" if self.mode == "Translation" else "pinyin"
            placements = placer.compute_placements(
                regions, mode_key, overlay=self.overlay_mode,
            )

            # For renderer: always replace when "always", never when "never",
            # and for "auto" check if the placer actually used overlay
            render_overlay = self.overlay_mode == "always" or (
                self.overlay_mode == "auto" and placer.used_overlay
            )

            result_image = self.renderer.render(
                self.image, placements,
                regions=regions, overlay=render_overlay,
            )
            self.finished.emit(result_image, regions)
        except Exception as e:
            self.error.emit(str(e))


class MainWindow(QWidget):
    def __init__(self, ocr: OcrEngine, translator: Translator, pinyin_conv: PinyinConverter):
        super().__init__()
        self.ocr = ocr
        self.translator = translator
        self.pinyin_conv = pinyin_conv
        self.renderer = ImageRenderer()

        self._selector = None
        self._overlay_win = None
        self._thread = None

        self._init_ui()

    def _init_ui(self):
        self.setObjectName("MainWindow")
        self.setWindowTitle("Manga Buddy")
        self.setFixedSize(460, 400)
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)

        container = QWidget()
        container.setObjectName("MainWindow")
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(28, 24, 28, 24)
        container_layout.setSpacing(16)

        # ── Title bar ──
        title_bar = QHBoxLayout()
        title_col = QVBoxLayout()
        title_col.setSpacing(4)

        title = QLabel("MANGA BUDDY")
        title.setObjectName("TitleLabel")
        title_col.addWidget(title)

        subtitle = QLabel("Select a region to translate or annotate")
        subtitle.setObjectName("SubtitleLabel")
        title_col.addWidget(subtitle)

        title_bar.addLayout(title_col)
        title_bar.addStretch()

        minimize_btn = QPushButton("—")
        minimize_btn.setFixedSize(32, 32)
        minimize_btn.setStyleSheet(
            "QPushButton { background: rgba(255,255,255,0.06); color: #a8a8b3; "
            "border: none; border-radius: 16px; font-size: 13px; }"
            "QPushButton:hover { background: rgba(255,255,255,0.12); color: white; }"
        )
        minimize_btn.clicked.connect(self.showMinimized)
        title_bar.addWidget(minimize_btn)

        close_btn = QPushButton("✕")
        close_btn.setFixedSize(32, 32)
        close_btn.setStyleSheet(
            "QPushButton { background: rgba(255,255,255,0.06); color: #a8a8b3; "
            "border: none; border-radius: 16px; font-size: 13px; }"
            "QPushButton:hover { background: rgba(233,69,96,0.8); color: white; }"
        )
        close_btn.clicked.connect(self.close)
        title_bar.addWidget(close_btn)

        container_layout.addLayout(title_bar)

        # ── Status ──
        self._status = QLabel("Ready — click Capture to start")
        self._status.setObjectName("StatusLabel")
        self._status.setAlignment(Qt.AlignCenter)
        container_layout.addWidget(self._status)

        # ── Settings rows ──
        settings = QVBoxLayout()
        settings.setSpacing(12)

        # Mode selector
        mode_row = QHBoxLayout()
        mode_label = QLabel("Mode")
        mode_label.setStyleSheet("color: #a8a8b3; font-weight: 600; font-size: 13px;")
        mode_row.addWidget(mode_label)
        mode_row.addStretch()
        self._mode = QComboBox()
        self._mode.setObjectName("ModeCombo")
        self._mode.addItems(["Translation", "Pinyin"])
        mode_row.addWidget(self._mode)
        settings.addLayout(mode_row)

        # Overlay mode selector
        overlay_row = QHBoxLayout()
        overlay_label = QLabel("Text replacement")
        overlay_label.setStyleSheet("color: #a8a8b3; font-weight: 600; font-size: 13px;")
        overlay_row.addWidget(overlay_label)
        overlay_row.addStretch()
        self._overlay_mode = QComboBox()
        self._overlay_mode.setObjectName("ModeCombo")
        self._overlay_mode.addItems(["Never replace", "Replace if needed", "Always replace"])
        self._overlay_mode.setCurrentIndex(1)
        overlay_row.addWidget(self._overlay_mode)
        settings.addLayout(overlay_row)

        container_layout.addLayout(settings)

        # ── Spacer ──
        container_layout.addStretch()

        # ── Capture button ──
        self._capture_btn = QPushButton("  Capture Region")
        self._capture_btn.setObjectName("CaptureButton")
        self._capture_btn.setCursor(Qt.PointingHandCursor)
        self._capture_btn.clicked.connect(self._start_capture)

        glow = QGraphicsDropShadowEffect()
        glow.setColor(Qt.red)
        glow.setBlurRadius(24)
        glow.setOffset(0, 4)
        self._capture_btn.setGraphicsEffect(glow)

        container_layout.addWidget(self._capture_btn, alignment=Qt.AlignCenter)

        # ── Quit ──
        quit_btn = QPushButton("Quit")
        quit_btn.setObjectName("QuitButton")
        quit_btn.setCursor(Qt.PointingHandCursor)
        quit_btn.clicked.connect(self.close)
        container_layout.addWidget(quit_btn, alignment=Qt.AlignCenter)

        # ── Main layout ──
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(12, 12, 12, 12)

        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(30)
        shadow.setOffset(0, 8)
        shadow.setColor(Qt.black)
        container.setGraphicsEffect(shadow)

        main_layout.addWidget(container)

        self._drag_pos = None

    # ── Window dragging ──
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_pos = event.globalPos() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, event):
        if self._drag_pos is not None:
            self.move(event.globalPos() - self._drag_pos)

    def mouseReleaseEvent(self, event):
        self._drag_pos = None

    # ── Capture flow ──
    def _start_capture(self):
        self.hide()
        self._selector = RegionSelector()
        self._selector.region_selected.connect(self._on_region_selected)
        self._selector.cancelled.connect(self._on_capture_cancelled)
        self._selector.show()

    def _on_capture_cancelled(self):
        self._selector = None
        self.show()

    def _get_overlay_mode(self) -> str:
        idx = self._overlay_mode.currentIndex()
        return ["never", "auto", "always"][idx]

    def _on_region_selected(self, rect: QRect):
        self._selector = None
        self._screen_rect = rect
        bbox = (rect.x(), rect.y(), rect.x() + rect.width(), rect.y() + rect.height())
        image = ImageGrab.grab(bbox)

        self._set_status("processing", "Processing... please wait")
        self._capture_btn.setEnabled(False)
        self.show()

        self._run_pipeline(image)

    def _set_status(self, status_type, text):
        self._status.setText(text)
        self._status.setProperty("status", status_type)
        self._status.style().unpolish(self._status)
        self._status.style().polish(self._status)

    def _run_pipeline(self, image):
        self._thread = QThread()
        self._worker = PipelineWorker(
            image, self._mode.currentText(),
            self._get_overlay_mode(),
            self.ocr, self.translator, self.pinyin_conv, self.renderer,
        )
        self._worker.moveToThread(self._thread)
        self._thread.started.connect(self._worker.run)
        self._worker.finished.connect(self._on_pipeline_done)
        self._worker.error.connect(self._on_pipeline_error)
        self._worker.finished.connect(self._thread.quit)
        self._worker.error.connect(self._thread.quit)
        self._thread.start()

    def _on_pipeline_done(self, result_image, regions):
        self._set_status("ready", f"Found {len(regions)} text region(s)")
        self._capture_btn.setEnabled(True)

        result_image = result_image.convert("RGBA")
        data = result_image.tobytes("raw", "RGBA")
        qimage = QImage(data, result_image.width, result_image.height, QImage.Format_RGBA8888)
        pixmap = QPixmap.fromImage(qimage)

        self.hide()
        self._overlay_win = ResultOverlay(pixmap, self._screen_rect)
        self._overlay_win.closed.connect(self._on_overlay_closed)
        self._overlay_win.show()

    def _on_pipeline_error(self, msg):
        self._set_status("error", "Error — see details")
        self._capture_btn.setEnabled(True)
        QMessageBox.warning(self, "Pipeline Error", msg)
        self._set_status("ready", "Ready — click Capture to start")

    def _on_overlay_closed(self):
        self._overlay_win = None
        self.show()
