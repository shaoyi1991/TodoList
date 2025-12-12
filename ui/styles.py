MAIN_WINDOW_STYLE = """
    QMainWindow {
        background-color: #ffffff;
        border: 1px solid #e0e0e0;
        border-radius: 8px;
    }
    #titleBar {
        background-color: #f5f5f5;
        border-bottom: 1px solid #e0e0e0;
        border-top-left-radius: 8px;
        border-top-right-radius: 8px;
        min-height: 22px;
        max-height: 22px;
    }
    #collapseButton {
        background-color: #4CAF50;
        color: white;
        border: none;
        border-radius: 4px;
        padding: 2px 6px;
    }
    #collapseButton:hover {
        background-color: #45a049;
    }
    QLineEdit, QComboBox, QDateTimeEdit {
        background-color: white;
        border: 1px solid #e0e0e0;
        border-radius: 4px;
        padding: 2px 4px;
    }
    QPushButton {
        background-color: #4CAF50;
        color: white;
        border: none;
        border-radius: 4px;
        padding: 2px 8px;
    }
    QPushButton:hover {
        background-color: #45a049;
    }
    QTableWidget {
        background-color: transparent;
        border: none;
        gridline-color: #e0e0e0;
        margin: 0px;
        padding: 0px;
    }
    QTableWidget::item {
        background-color: rgba(255, 255, 255, 0.7);
        border-radius: 4px;
        padding: 2px;
        margin: 1px;
    }
    QHeaderView::section {
        background-color: #f5f5f5;
        padding: 2px;
        border: none;
        border-bottom: 1px solid #e0e0e0;
        font-weight: bold;
        color: #333333;
    }
    /* 设置输入区域背景透明 */
    #input_widget {
        background-color: transparent;
        margin: 0px;
        padding: 0px;
    }
"""

MENU_STYLE = """
    QMenu {
        background-color: white;
        border: 1px solid #e0e0e0;
        border-radius: 4px;
        padding: 4px;
    }
    QMenu::item {
        padding: 4px 20px 4px 10px;
        border-radius: 2px;
        color: #333;
    }
    QMenu::item:selected {
        background-color: #f5f5f5;
        color: #333;
    }
"""

CHECKBOX_STYLE = """
    QCheckBox {
        spacing: 0px;
    }
    QCheckBox::indicator {
        width: 10px;
        height: 10px;
    }
    QCheckBox::indicator:unchecked {
        border: 2px solid #4CAF50;
        border-radius: 2px;
        background-color: white;
    }
    QCheckBox::indicator:checked {
        border: 2px solid #4CAF50;
        border-radius: 2px;
        background-color: #4CAF50;
        image: url(:/resources/checked.png);
    }
    QCheckBox::indicator:unchecked:hover {
        border-color: #45a049;
        background-color: rgba(76, 175, 80, 0.1);
    }
    QCheckBox::indicator:checked:hover {
        border-color: #45a049;
        background-color: #45a049;
    }
"""

DELETE_BTN_STYLE = """
    QPushButton {
        background-color: transparent;
        border: none;
        color: #666666;
        font-size: 14px;
        font-weight: bold;
    }
    QPushButton:hover {
        color: #ff4d4d;
    }
"""

DELETE_DIALOG_STYLE = """
    #container {
        background-color: white;
        border: 1px solid #e0e0e0;
        border-radius: 8px;
    }
    QLabel {
        color: #666;
        font-size: 10px;
        padding: 5px;
    }
    QPushButton {
        background-color: #4CAF50;
        color: white;
        border: none;
        border-radius: 15px;
        font-weight: bold;
    }
    QPushButton:hover {
        background-color: #45a049;
    }
    QPushButton[text="取消"] {
        background-color: #e0e0e0;
        color: #333;
    }
    QPushButton[text="取消"]:hover {
        background-color: #d5d5d5;
    }
"""

REMINDER_DIALOG_STYLE = """
    #container {
        background-color: white;
        border: 2px solid #4CAF50;
        border-radius: 10px;
    }
    QPushButton {
        background-color: #4CAF50;
        color: white;
        border: none;
        border-radius: 15px;
        font-weight: bold;
    }
    QPushButton:hover {
        background-color: #45a049;
    }
"""

CALENDAR_STYLE = """
    QCalendarWidget {
        background-color: white;
        border: 1px solid #e0e0e0;
    }
    QCalendarWidget QToolButton {
        color: black;
        background-color: transparent;
        border: none;
    }
    QCalendarWidget QToolButton:hover {
        background-color: #f5f5f5;
    }
    QCalendarWidget QMenu {
        background-color: white;
        border: 1px solid #e0e0e0;
    }
    QCalendarWidget QSpinBox {
        border: 1px solid #e0e0e0;
        border-radius: 2px;
    }
    QCalendarWidget QTableView {
        selection-background-color: #f5f5f5;
        selection-color: black;
    }
"""
