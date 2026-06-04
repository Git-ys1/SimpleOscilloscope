from __future__ import annotations

BACKGROUND = "#0b1020"
SURFACE = "#101624"
SURFACE_ALT = "#151d2f"
BORDER = "#29344f"
GRID_MAJOR = "#34405f"
GRID_MINOR = "#1b2740"
CH1 = "#50e3a4"
TRIGGER = "#ffcc66"
TEXT = "#d9e2f2"
TEXT_MUTED = "#8ea1c4"
RUN = "#50e3a4"
STOP = "#ff6b6b"
WAIT = "#ffcc66"
ERROR = "#ff5c8a"

PRIMARY_FONT = "Microsoft YaHei UI"
FONT_FAMILY = '"Microsoft YaHei UI", "Microsoft YaHei", SimHei, "Segoe UI", sans-serif'
CONTROL_RADIUS = 5
PANEL_SPACING = 10


def app_stylesheet() -> str:
    return f"""
    QMainWindow, QWidget {{
        background: {SURFACE};
        color: {TEXT};
        font-family: {FONT_FAMILY};
        font-size: 10pt;
    }}
    QToolBar {{
        background: {BACKGROUND};
        border-bottom: 1px solid {BORDER};
        spacing: 6px;
        padding: 6px 8px;
    }}
    QToolButton, QPushButton {{
        background: #1d2a44;
        border: 1px solid #415477;
        border-radius: {CONTROL_RADIUS}px;
        padding: 6px 10px;
    }}
    QToolButton:hover, QPushButton:hover {{
        background: #253858;
    }}
    QPushButton#primaryButton, QToolButton#primaryButton {{
        background: #143b31;
        border-color: {CH1};
        color: #eafff6;
    }}
    QDockWidget {{
        titlebar-close-icon: none;
        titlebar-normal-icon: none;
    }}
    QDockWidget::title {{
        background: {BACKGROUND};
        border-left: 1px solid {BORDER};
        border-bottom: 1px solid {BORDER};
        padding: 6px 8px;
        font-weight: 600;
    }}
    QGroupBox {{
        border: 1px solid {BORDER};
        border-radius: 6px;
        margin-top: 10px;
        padding: 8px;
        font-weight: 600;
    }}
    QGroupBox::title {{
        subcontrol-origin: margin;
        left: 8px;
        padding: 0 4px;
    }}
    QLabel#qualityHint {{
        background: #3a2f12;
        color: {WAIT};
        border-top: 1px solid #6d5520;
        border-bottom: 1px solid #6d5520;
        padding: 6px 10px;
        font-weight: 600;
    }}
    QTabWidget::pane {{
        border: 1px solid {BORDER};
        border-radius: 4px;
    }}
    QTabBar::tab {{
        background: {BACKGROUND};
        border: 1px solid {BORDER};
        padding: 6px 8px;
        margin-right: 2px;
    }}
    QTabBar::tab:selected {{
        background: #1d2a44;
        color: #eafff6;
    }}
    QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox {{
        background: {BACKGROUND};
        border: 1px solid #34405f;
        border-radius: 4px;
        padding: 4px 6px;
        min-height: 22px;
    }}
    QCheckBox {{
        spacing: 8px;
    }}
    QStatusBar {{
        background: {BACKGROUND};
        border-top: 1px solid {BORDER};
    }}
    QScrollArea {{
        border: 0;
    }}
    """
