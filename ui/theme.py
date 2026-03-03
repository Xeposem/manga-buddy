STYLESHEET = """
/* ── Global ── */
QWidget {
    font-family: "Segoe UI", Arial, sans-serif;
    font-size: 13px;
}

/* ── Main Window ── */
QWidget#MainWindow {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 #1a1a2e, stop:0.5 #16213e, stop:1 #0f3460);
    border-radius: 12px;
}

QLabel#TitleLabel {
    color: #e94560;
    font-size: 22px;
    font-weight: bold;
    letter-spacing: 1px;
}

QLabel#SubtitleLabel {
    color: #a8a8b3;
    font-size: 11px;
}

QLabel#StatusLabel {
    color: #53d769;
    font-size: 12px;
    font-weight: 600;
    padding: 6px 12px;
    background: rgba(83, 215, 105, 0.08);
    border: 1px solid rgba(83, 215, 105, 0.2);
    border-radius: 8px;
}

QLabel#StatusLabel[status="error"] {
    color: #e94560;
    background: rgba(233, 69, 96, 0.08);
    border-color: rgba(233, 69, 96, 0.2);
}

QLabel#StatusLabel[status="processing"] {
    color: #f5a623;
    background: rgba(245, 166, 35, 0.08);
    border-color: rgba(245, 166, 35, 0.2);
}

/* ── Buttons ── */
QPushButton#CaptureButton {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #e94560, stop:1 #c23152);
    color: white;
    font-size: 15px;
    font-weight: bold;
    padding: 12px 32px;
    border: none;
    border-radius: 10px;
    min-width: 160px;
}
QPushButton#CaptureButton:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #ff5a7a, stop:1 #e94560);
}
QPushButton#CaptureButton:pressed {
    background: #a32845;
}
QPushButton#CaptureButton:disabled {
    background: #555;
    color: #888;
}

QPushButton#QuitButton {
    background: rgba(255, 255, 255, 0.06);
    color: #a8a8b3;
    font-size: 12px;
    padding: 8px 20px;
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 8px;
}
QPushButton#QuitButton:hover {
    background: rgba(233, 69, 96, 0.15);
    color: #e94560;
    border-color: rgba(233, 69, 96, 0.3);
}

/* ── ComboBox ── */
QComboBox#ModeCombo {
    background: rgba(255, 255, 255, 0.08);
    color: #ffffff;
    padding: 8px 14px;
    border: 1px solid rgba(255, 255, 255, 0.15);
    border-radius: 8px;
    min-width: 140px;
    font-weight: 600;
}
QComboBox#ModeCombo:hover {
    border-color: #e94560;
}
QComboBox#ModeCombo::drop-down {
    border: none;
    width: 28px;
}
QComboBox#ModeCombo::down-arrow {
    image: none;
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-top: 6px solid #e94560;
    margin-right: 8px;
}
QComboBox QAbstractItemView {
    background: #16213e;
    color: #ffffff;
    selection-background-color: #e94560;
    border: 1px solid rgba(255, 255, 255, 0.15);
    border-radius: 4px;
    padding: 4px;
}

/* ── Overlay close button ── */
QPushButton#OverlayClose {
    background: rgba(233, 69, 96, 0.85);
    color: white;
    border: 2px solid rgba(255, 255, 255, 0.3);
    border-radius: 14px;
    font-size: 14px;
    font-weight: bold;
}
QPushButton#OverlayClose:hover {
    background: #ff5a7a;
    border-color: white;
}
"""
