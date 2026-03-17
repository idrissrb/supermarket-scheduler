from PyQt6.QtGui import QPalette, QColor

def apply_dark_theme(widget):
    """Apply the project's unified dark palette and stylesheet to a widget.

    This keeps the palette + stylesheet in one place so multiple windows/dialogs
    can share the same look-and-feel.
    """
    pal = widget.palette()
    pal.setColor(QPalette.ColorRole.Window, QColor("#0f1720"))
    pal.setColor(QPalette.ColorRole.WindowText, QColor("#e6eef8"))
    pal.setColor(QPalette.ColorRole.Base, QColor("#0b1114"))
    pal.setColor(QPalette.ColorRole.AlternateBase, QColor("#0e1417"))
    pal.setColor(QPalette.ColorRole.Text, QColor("#e6eef8"))
    pal.setColor(QPalette.ColorRole.Button, QColor("#04282b"))
    pal.setColor(QPalette.ColorRole.ButtonText, QColor("#e6eef8"))
    widget.setPalette(pal)

    widget.setStyleSheet("""
        QWidget {
            font-family: "Segoe UI", Roboto, Arial, sans-serif;
            color: #E6EEF8;
            background: #0f1720;
        }
        QGroupBox {
            background: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:0, stop:0 #0b1114, stop:1 #0f1418);
            border: 1px solid #1f2a30;
            border-radius: 10px;
            margin-top: 8px;
            padding: 10px;
        }
        QGroupBox:title {
            subcontrol-origin: margin;
            subcontrol-position: top center;
            padding: 6px 12px;
            color: #9fe9ff;
            font-weight: 700;
        }
        QLabel#mainTitle {
            color: #7be0ff;
            font-size: 20px;
            font-weight: 800;
        }
        QLabel#subtitle {
            color: #9fb6c6;
            font-size: 12px;
        }
        QPushButton {
            background-color: #16a085;
            color: #eafaf6;
            padding: 8px 14px;
            border-radius: 8px;
            font-weight: 700;
            border: none;
            min-height: 34px;
        }
        QPushButton#secondary {
            background-color: #e67e22;
            color: #2b1100;
        }
        QPushButton:hover { opacity: 0.95; }
        QTextEdit {
            background: #071012;
            color: #e6eef8;
            border: 1px solid #123033;
            border-radius: 8px;
            padding: 8px;
        }
        QSpinBox, QAbstractSpinBox {
            background: #071012;
            color: #e6eef8;
            border: 1px solid #123033;
            border-radius: 6px;
            padding: 4px;
        }
    """)
