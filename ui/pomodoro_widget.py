from PyQt6.QtWidgets import (QWidget, QHBoxLayout, QPushButton, QLabel, 
                            QDialog, QVBoxLayout, QApplication, QSizePolicy)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QCursor
from core.pomodoro import PomodoroManager
from .dialogs import ReminderDialog

class HistoryDialog(QDialog):
    def __init__(self, history_data, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.Popup | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setup_ui(history_data)
        
    def setup_ui(self, history_data):
        self.setFixedWidth(280)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        container = QWidget()
        container.setStyleSheet("""
            QWidget {
                background-color: white;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
            }
            QLabel {
                color: #333;
                font-family: "Segoe UI", sans-serif;
            }
        """)
        c_layout = QVBoxLayout(container)
        c_layout.setSpacing(8)
        c_layout.setContentsMargins(15, 15, 15, 15)
        
        title = QLabel("🍅 近7天专注统计")
        title.setStyleSheet("font-weight: bold; font-size: 14px; color: #d32f2f; margin-bottom: 5px;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        c_layout.addWidget(title)
        
        if not history_data:
            empty = QLabel("暂无数据")
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty.setStyleSheet("color: #999;")
            c_layout.addWidget(empty)
        else:
            # Calculate max count for relative scaling
            max_count = max(count for _, count in history_data) if history_data else 0
            MAX_ICONS = 10
            
            for date_str, count in history_data:
                # Format: MM-DD: 🍅🍅🍅 (3)
                try:
                    d_obj = date_str.split('-')
                    # Ensure zero-padding for display consistency (e.g. 12-07)
                    month = int(d_obj[1])
                    day = int(d_obj[2])
                    short_date = f"{month:02d}-{day:02d}"
                except:
                    short_date = date_str
                    
                # Calculate number of emojis based on relative scale
                if max_count <= MAX_ICONS:
                    display_count = count
                else:
                    # Scale to fit MAX_ICONS
                    display_count = int((count / max_count) * MAX_ICONS)
                    # Ensure at least 1 icon if count > 0
                    if count > 0 and display_count == 0:
                        display_count = 1
                    
                emojis = "🍅" * display_count
                    
                row_text = f"{short_date}: {emojis} ({count})"
                row_label = QLabel(row_text)
                row_label.setStyleSheet("font-size: 12px;")
                c_layout.addWidget(row_label)
                
        layout.addWidget(container)
        
    def focusOutEvent(self, event):
        self.close()

class PomodoroWidget(QWidget):
    def __init__(self, task_manager, parent=None):
        super().__init__(parent)
        self.manager = PomodoroManager(task_manager)
        self.setup_ui()
        self.connect_signals()
        
    def setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 0, 10, 0)
        layout.setSpacing(15)
        
        # Style
        self.setStyleSheet("""
            QWidget#PomodoroWidget {
                background-color: #fff0f0;
                border-radius: 5px;
                border: 1px solid #ffcdd2;
            }
            QLabel {
                color: #d32f2f;
                font-weight: bold;
            }
            QPushButton {
                background-color: transparent;
                border: 1px solid #d32f2f;
                border-radius: 4px;
                color: #d32f2f;
                padding: 2px 8px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #ffebee;
            }
            QPushButton:disabled {
                border-color: #ffcdd2;
                color: #ef9a9a;
            }
        """)
        self.setObjectName("PomodoroWidget")
        self.setFixedHeight(30)  # Minimized height
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        
        # Timer Display
        self.time_label = QLabel("25:00")
        self.time_label.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        layout.addWidget(self.time_label)
        
        # Controls
        self.start_btn = QPushButton("开始")
        self.start_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.start_btn.clicked.connect(self.toggle_timer)
        layout.addWidget(self.start_btn)
        
        self.reset_btn = QPushButton("重置")
        self.reset_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.reset_btn.clicked.connect(self.manager.reset_timer)
        layout.addWidget(self.reset_btn)
        
        layout.addStretch()
        
        # Count Display
        self.count_label = QLabel(f"今日: 🍅 × {self.manager.get_today_count()}")
        self.count_label.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.count_label.setToolTip("点击查看历史趋势")
        self.count_label.mousePressEvent = self.show_history
        layout.addWidget(self.count_label)
        
    def connect_signals(self):
        self.manager.timer_updated.connect(self.time_label.setText)
        self.manager.state_changed.connect(self.update_buttons)
        self.manager.pomodoro_completed.connect(self.on_completed)
        
    def toggle_timer(self):
        if self.manager.is_running:
            self.manager.pause_timer()
        else:
            self.manager.start_timer()
            
    def update_buttons(self, is_running):
        self.start_btn.setText("暂停" if is_running else "开始")
        self.reset_btn.setEnabled(not is_running)
        
    def on_completed(self, count):
        self.count_label.setText(f"今日: 🍅 × {count}")
        self.start_btn.setText("开始")
        self.reset_btn.setEnabled(True)
        
        alert = ReminderDialog("🎉 恭喜完成一个番茄钟！\n休息一下吧！", self.window())
        alert.exec()
        
    def show_history(self, event):
        data = self.manager.get_history()
        dialog = HistoryDialog(data, self)
        # Position near the label
        global_pos = self.count_label.mapToGlobal(self.count_label.rect().bottomRight())
        dialog.move(global_pos.x() - dialog.width(), global_pos.y() + 5)
        dialog.exec()
