from PyQt6.QtWidgets import QDialog, QVBoxLayout, QWidget, QLabel, QPushButton, QHBoxLayout, QApplication
from PyQt6.QtCore import Qt, QTimer
from .styles import DELETE_DIALOG_STYLE, REMINDER_DIALOG_STYLE

class DeleteConfirmDialog(QDialog):
    """删除确认对话框"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setup_ui()

    def setup_ui(self):
        # 设置对话框大小 (与 ReminderDialog 保持一致)
        self.setFixedSize(300, 180)
        
        # 创建主布局
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 创建白色背景容器
        container = QWidget(self)
        container.setObjectName("container")
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(20, 20, 20, 20)
        container_layout.setSpacing(15)
        
        # 添加标题 (保持与 ReminderDialog 风格一致)
        title = QLabel("⚠️ 删除确认")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #4CAF50;")
        container_layout.addWidget(title)
        
        # 添加提示文本
        message = QLabel("确定要删除这条待办任务吗？")
        message.setAlignment(Qt.AlignmentFlag.AlignCenter)
        message.setWordWrap(True)
        message.setStyleSheet("font-size: 14px; color: #333;")
        container_layout.addWidget(message)
        
        # 添加按钮容器
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(20)
        btn_layout.addStretch()
        
        # 创建按钮
        confirm_btn = QPushButton("确认删除")
        cancel_btn = QPushButton("取消")
        confirm_btn.setFixedSize(100, 30)
        cancel_btn.setFixedSize(100, 30)
        
        # 连接按钮信号
        confirm_btn.clicked.connect(self.accept)
        cancel_btn.clicked.connect(self.reject)
        
        # 添加按钮到布局
        btn_layout.addWidget(confirm_btn)
        btn_layout.addWidget(cancel_btn)
        btn_layout.addStretch()
        
        container_layout.addLayout(btn_layout)
        layout.addWidget(container)
        
        # 设置样式
        self.setStyleSheet(DELETE_DIALOG_STYLE)

class ReminderDialog(QDialog):
    """强提醒对话框"""
    def __init__(self, task_text, parent=None):
        super().__init__(parent)
        self.task_text = task_text
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setup_ui()
        
        # 初始化闹铃计数器
        self.alarm_cycle_count = 0  # 当前轮数（0-4，共5轮）
        self.alarm_beep_count = 0   # 当前轮已响次数（0-14，共15次）

        # 持续闹铃定时器
        self.alarm_timer = QTimer(self)
        self.alarm_timer.timeout.connect(self.play_alarm)
        self.alarm_timer.start(2000)  # 每2秒响一次
        self.play_alarm()  # 立即响一次

    def setup_ui(self):
        self.setFixedSize(300, 180)
        
        # 主布局
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 容器
        container = QWidget(self)
        container.setObjectName("container")
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(20, 20, 20, 20)
        container_layout.setSpacing(15)
        
        # 标题
        title = QLabel("☕ 休息提醒")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #4CAF50;")
        container_layout.addWidget(title)
        
        # 内容
        self.content_label = QLabel(self.task_text)
        self.content_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.content_label.setWordWrap(True)
        self.content_label.setStyleSheet("font-size: 14px; color: #333;")
        container_layout.addWidget(self.content_label)
        
        # 按钮
        confirm_btn = QPushButton("我知道了")
        confirm_btn.setFixedSize(100, 30)
        confirm_btn.clicked.connect(self.accept)
        
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(confirm_btn)
        btn_layout.addStretch()
        container_layout.addLayout(btn_layout)
        
        layout.addWidget(container)
        
        # 样式
        self.setStyleSheet(REMINDER_DIALOG_STYLE)

    def play_alarm(self):
        """播放系统提示音并处理循环逻辑"""
        # 如果已经执行了1轮，不再播放
        if self.alarm_cycle_count >= 1:
            self.alarm_timer.stop()
            return

        # 播放系统提示音
        QApplication.beep()
        
        # 增加当前轮的响铃次数
        self.alarm_beep_count += 1

        # 检查是否完成一轮（15次）
        if self.alarm_beep_count >= 15:
            # 增加轮数计数
            self.alarm_cycle_count += 1
            # 重置当前轮响铃次数
            self.alarm_beep_count = 0
            
            # 达到1轮，彻底停止
            self.alarm_timer.stop()

    def resume_alarm(self):
        """暂停结束后恢复闹铃"""
        # 确保窗口还在显示（未被关闭）
        if self.isVisible():
            self.alarm_timer.start(2000)  # 恢复2秒间隔
            self.play_alarm()  # 立即响一次开始新的一轮

    def update_task(self, new_text):
        """更新任务内容（覆盖旧提醒）"""
        self.task_text = new_text
        self.content_label.setText(new_text)
        # 重置所有计数器和定时器，重新开始
        self.alarm_cycle_count = 0
        self.alarm_beep_count = 0
        self.alarm_timer.stop() # 停止可能正在运行的定时器
        self.alarm_timer.start(2000) # 重新开始2秒定时器
        self.play_alarm() # 立即响一次
