import sys
import os
from PyQt5.QtWidgets import QApplication, QLabel
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QObject, QTimer
from PyQt5.QtGui import QFont, QColor

os.environ["PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK"] = "True"


class ModelLoader(QObject):
    finished = pyqtSignal(object, object, object)
    status = pyqtSignal(str)
    error = pyqtSignal(str)

    def run(self):
        try:
            self.status.emit("Loading OCR engine...")
            from core.ocr_engine import OcrEngine
            ocr = OcrEngine()

            self.status.emit("Loading translator...")
            from core.translator import Translator
            translator = Translator()

            self.status.emit("Loading pinyin converter...")
            from core.pinyin_converter import PinyinConverter
            pinyin_conv = PinyinConverter()

            self.finished.emit(ocr, translator, pinyin_conv)
        except Exception as e:
            self.error.emit(str(e))


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    from ui.theme import STYLESHEET
    app.setStyleSheet(STYLESHEET)

    # Splash screen
    splash = QLabel()
    splash.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
    splash.setAttribute(Qt.WA_TranslucentBackground, False)
    splash.setAlignment(Qt.AlignCenter)
    splash.setFixedSize(420, 100)
    splash.setFont(QFont("Segoe UI", 13, QFont.Bold))
    splash.setStyleSheet(
        "background: qlineargradient(x1:0, y1:0, x2:1, y2:0, "
        "stop:0 #1a1a2e, stop:1 #16213e);"
        "color: #e94560; border: 2px solid #e94560; border-radius: 12px;"
        "padding: 10px;"
    )
    splash.setText("Loading models, please wait...")
    splash.show()
    app.processEvents()

    thread = QThread()
    loader = ModelLoader()
    loader.moveToThread(thread)

    def on_status(msg):
        splash.setText(msg)
        app.processEvents()

    def on_finished(ocr, translator, pinyin_conv):
        splash.close()
        from ui.main_window import MainWindow
        window = MainWindow(ocr, translator, pinyin_conv)
        window.show()
        app._main_window = window

    def on_error(msg):
        splash.close()
        from PyQt5.QtWidgets import QMessageBox
        QMessageBox.critical(None, "Startup Error", f"Failed to load models:\n{msg}")
        app.quit()

    loader.status.connect(on_status)
    loader.finished.connect(on_finished)
    loader.error.connect(on_error)
    loader.finished.connect(thread.quit)
    loader.error.connect(thread.quit)
    thread.started.connect(loader.run)
    thread.start()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
