import sys
from datetime import datetime
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QPushButton, QLineEdit, QComboBox, 
                            QDateTimeEdit, QLabel, QTableWidget, QTableWidgetItem,
                            QHeaderView, QSizePolicy, QDialog, QMenu, QCheckBox, QGraphicsOpacityEffect)
from PyQt6.QtCore import Qt, QDateTime, QPoint, QRect, QTimer, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QColor, QPainter
from PyQt6.QtCore import QDate
import json
import os
import winreg
import win32com.client
from pathlib import Path
import uuid

class TaskItem:
    def __init__(self, seq, text, priority, deadline):
        self.seq = seq
        self.text = text
        self.priority = priority
        self.deadline = deadline

class DeleteConfirmDialog(QDialog):
    """删除确认对话框"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)  # 无边框窗口
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)  # 透明背景
        self.setup_ui()

    def setup_ui(self):
        # 设置对话框大小
        self.setFixedSize(200, 100)
        
        # 创建主布局
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # 创建白色背景容器
        container = QWidget(self)
        container.setObjectName("container")
        container_layout = QVBoxLayout(container)
        
        # 添加提示文本
        message = QLabel("确认删除？")
        message.setAlignment(Qt.AlignmentFlag.AlignCenter)
        container_layout.addWidget(message)
        
        # 添加按钮容器
        button_widget = QWidget()
        button_layout = QHBoxLayout(button_widget)
        button_layout.setContentsMargins(0, 0, 0, 0)
        button_layout.setSpacing(10)
        
        # 创建按钮
        confirm_btn = QPushButton("确认")
        cancel_btn = QPushButton("取消")
        confirm_btn.setFixedWidth(60)
        cancel_btn.setFixedWidth(60)
        
        # 连接按钮信号
        confirm_btn.clicked.connect(self.accept)
        cancel_btn.clicked.connect(self.reject)
        
        # 添加按钮到布局
        button_layout.addWidget(confirm_btn)
        button_layout.addWidget(cancel_btn)
        container_layout.addWidget(button_widget)
        
        # 添加容器到主布局
        layout.addWidget(container)
        
        # 设置样式
        self.setStyleSheet("""
            #container {
                background-color: white;
                border: 1px solid #ffccd5;
                border-radius: 8px;
            }
            QLabel {
                color: #666;
                font-size: 10px;
                padding: 5px;
            }
            QPushButton {
                background-color: #ff8ba7;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 2px 5px;
                font-size: 8px;
            }
            QPushButton:hover {
                background-color: #ff7096;
            }
            QPushButton[text="取消"] {
                background-color: #ffccd5;
            }
            QPushButton[text="取消"]:hover {
                background-color: #ffb3bf;
            }
        """)

class TodoWidget(QMainWindow):
    def __init__(self):
        super().__init__()
        self.task_count = 0  # 用于跟踪序号
        self.tasks = []  # 存储任务数据
        # 修改优先级定义和映射
        self.priority_values = {'低': 0, '中': 1, '高': 2, '紧急': 3}
        self.sort_order = {'priority': Qt.SortOrder.AscendingOrder, 'deadline': Qt.SortOrder.AscendingOrder}
        self.data_file = 'todo_data.json'  # 数据文件路径
        # 移除系统默认的标题栏
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        
        # 初始化拖拽相关变量
        self.dragging = False
        self.resizing = False
        self.offset = QPoint()
        self.resize_edge = None
        self.resize_margin = 5  # 调整大小的边缘宽度
        self.bottom_margin = 20     # 增大底部边缘检测范围到20像素

        # 移除最小高度限制
        self.setMinimumHeight(0)
        
        # 设置最小宽度
        self.setMinimumWidth(300)

        # 确保数据文件存在
        if not os.path.exists(self.data_file):
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump([], f, ensure_ascii=False)
        
        # 初始化UI
        self.initUI()
        
        # 加载任务数据
        self.load_tasks()
        
        # 添加自启动设方法
        self.setup_autostart()
    
    def setup_autostart(self):
        """设置开机自启动"""
        # 获取启动文件夹路径
        startup_path = os.path.join(
            os.getenv('APPDATA'),
            r'Microsoft\Windows\Start Menu\Programs\Startup'
        )
        
        # 获取当前执行文件路径
        app_path = sys.executable if getattr(sys, 'frozen', False) else os.path.abspath(__file__)
        
        # 快捷方式路径
        shortcut_path = os.path.join(startup_path, 'TodoList.lnk')
        
        try:
            # 创建快捷方式
            shell = win32com.client.Dispatch("WScript.Shell")
            shortcut = shell.CreateShortCut(shortcut_path)
            shortcut.Targetpath = app_path
            shortcut.WorkingDirectory = os.path.dirname(app_path)
            shortcut.save()
            print(f"Autostart shortcut created: {shortcut_path}")
        except Exception as e:
            print(f"Failed to create autostart shortcut: {e}")

    def remove_autostart(self):
        """移除开机自启动"""
        startup_path = os.path.join(
            os.getenv('APPDATA'),
            r'Microsoft\Windows\Start Menu\Programs\Startup'
        )
        shortcut_path = os.path.join(startup_path, 'TodoList.lnk')
        
        try:
            if os.path.exists(shortcut_path):
                os.remove(shortcut_path)
                print("Autostart shortcut removed")
        except Exception as e:
            print(f"Failed to remove autostart shortcut: {e}")

    def initUI(self):
        # 设置窗口位置和初始大小
        self.setGeometry(50, 50, 320, 350)
        
        # 设置窗口最小尺寸
        self.setMinimumSize(250, 300)  # 设置最小宽度和高度
        
        # 创建主窗口部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(0, 0, 0, 0)  # 移除主布局边距
        layout.setSpacing(20)  # 移除布局间距
        
        # 自定义标题栏
        title_bar = QWidget()
        title_bar_layout = QHBoxLayout(title_bar)
        title_bar_layout.setContentsMargins(8, 0, 0, 0)
        title_bar_layout.setSpacing(4)  # 增加一点间距
        title_bar.setFixedHeight(22)
        title_bar.setObjectName("titleBar")
        
        # 添加小标
        icon_label = QLabel('🐱')  # 使用猫咪表情
        icon_label.setObjectName("iconLabel")
        title_bar_layout.addWidget(icon_label)
        
        # 修改标题文本
        title_label = QLabel('待办清单-日事日毕，日清日高')
        title_label.setObjectName("titleLabel")
        title_bar_layout.addWidget(title_label)
        title_bar_layout.addStretch()
        
        # 最小化和关闭按钮
        min_button = QPushButton('－')
        min_button.setFixedSize(22, 22)  # 按钮大小与标题栏等高
        min_button.setObjectName("minButton")
        min_button.clicked.connect(self.showMinimized)
        
        close_button = QPushButton('×')
        close_button.setFixedSize(22, 22)  # 按钮大小与标题栏等高
        close_button.setObjectName("closeButton")
        close_button.clicked.connect(self.close)
        
        title_bar_layout.addWidget(min_button)
        title_bar_layout.addWidget(close_button)
        
        # 保存标题栏引用用于拖动
        self.title_bar = title_bar
        
        # 主布局
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(1, 0, 3, 5)  # 设置主布局边距
        layout.setSpacing(0)  # 移除布局间距
        
        # 添加标题栏和其他部件
        layout.addWidget(title_bar)
        
        # 创建输入区域
        input_widget = QWidget()
        input_layout = QHBoxLayout(input_widget)
        input_layout.setContentsMargins(8, 4, 8, 4)  # 减小上下边距
        input_layout.setSpacing(4)
        
        # 修复输入控件高度
        self.task_input = QLineEdit()
        self.task_input.setPlaceholderText('输入待办事项...')
        self.task_input.setFixedHeight(24)  # 固定高度
        
        self.priority_combo = QComboBox()
        self.priority_combo.addItems(['紧急', '高', '中', '低'])
        self.priority_combo.setCurrentText('中')
        self.priority_combo.setFixedSize(50, 24)  # 固定大小
        
        self.deadline_edit = QDateTimeEdit(QDateTime.currentDateTime())
        self.deadline_edit.setDisplayFormat("MM-dd")
        self.deadline_edit.setCalendarPopup(True)
        self.deadline_edit.setFixedSize(70, 24)  # 固定大小
        
        add_button = QPushButton('添加')
        add_button.setFixedSize(50, 24)  # 固定大小
        add_button.clicked.connect(self.add_task)
        
        input_layout.addWidget(self.task_input)
        input_layout.addWidget(self.priority_combo)
        input_layout.addWidget(self.deadline_edit)
        input_layout.addWidget(add_button)
        
        layout.addWidget(input_widget)
        
        # 表格设置
        self.task_table = QTableWidget()
        self.task_table.setColumnCount(4)
        self.task_table.setHorizontalHeaderLabels(['待办事项', '优先级 ↕', '日期 ↕', '完成'])
        
        # 设置表格行高
        self.task_table.verticalHeader().setDefaultSectionSize(24)
        self.task_table.verticalHeader().setMinimumSectionSize(24)
        
        # 禁用垂直滚动条
        self.task_table.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        # 设置表头点击信号
        header = self.task_table.horizontalHeader()
        header.sectionClicked.connect(self.on_header_clicked)
        
        # 禁用所有自动调整
        header.setStretchLastSection(False)
        header.setMinimumSectionSize(45)
        header.setDefaultSectionSize(45)
        
        # 禁用水平滚动条
        self.task_table.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        # 禁用列调整和移动
        header.setSectionsMovable(False)
        
        # 所有列都设置为固定宽度
        for i in range(4):
            header.setSectionResizeMode(i, QHeaderView.ResizeMode.Fixed)
        
        # 使用 QTimer 确保在布局完成后设置列宽
        QTimer.singleShot(0, self.initial_column_setup)

        layout.addWidget(self.task_table)

        # 创建一个背景widget来显示水印
        self.background_widget = QWidget(self)
        self.background_widget.setObjectName("backgroundWidget")
        self.background_widget.lower()  # 确保背景widget在最底层
        self.background_widget.setGeometry(0, 0, self.width(), self.height())

        # 调整窗口大小以适应内容
        self.adjustSize()

        # 确保表格可以自适应窗口大小变化
        self.task_table.horizontalHeader().setStretchLastSection(True)
        self.task_table.verticalHeader().setStretchLastSection(False)

        # 在设置完表格后立即验证列宽
        self.verify_column_widths()

        # 初始调整高度
        QTimer.singleShot(0, self.adjust_window_height)

    def initial_column_setup(self):
        """初始化列宽设置"""
        # 设置表格的固定总宽度
        content_width = self.width() - 5
        self.task_table.setFixedWidth(content_width)
        
        # 计算列宽
        fixed_width = 55 * 3
        first_column_width = content_width - fixed_width-10 # 减去10像素，防止表格内容溢      
        
        # 设置列宽
        self.task_table.setColumnWidth(0, first_column_width)
        self.task_table.setColumnWidth(1, 55)
        self.task_table.setColumnWidth(2, 55)
        self.task_table.setColumnWidth(3, 55)
        
        # 强制更新布局
        self.task_table.horizontalHeader().updateGeometry()
        self.task_table.updateGeometry()
        
        # 打印调试信息
        print(f"Initial setup - Content width: {content_width}")
        print(f"Initial setup - Column widths: {[self.task_table.columnWidth(i) for i in range(4)]}")

    def resizeEvent(self, event):
        """窗口大小改变时重新计算列宽"""
        super().resizeEvent(event)
        if hasattr(self, 'task_table'):
            content_width = self.width() - 5
            self.task_table.setFixedWidth(content_width)
            
            # 重新计算列宽
            fixed_width = 55 * 3
            first_column_width = content_width - fixed_width-10 # 减去10像素，防止表格内容溢出  
            
            # 设置列宽
            self.task_table.setColumnWidth(0, first_column_width)
            self.task_table.setColumnWidth(1, 55)
            self.task_table.setColumnWidth(2, 55)
            self.task_table.setColumnWidth(3, 55)
            
            # 强制更新布局
            self.task_table.horizontalHeader().updateGeometry()
            self.task_table.updateGeometry()

    def add_task(self):
        """添加任务"""
        task_text = self.task_input.text().strip()
        if not task_text:
            return
        
        priority = self.priority_combo.currentText()
        deadline = self.deadline_edit.dateTime().toString('yyyy-MM-dd HH:mm:ss')
        
        task = {
            'id': str(uuid.uuid4()),
            'text': task_text,
            'priority': priority,
            'deadline': deadline,
            'completed': False
        }
        
        self.tasks.append(task)
        self.save_tasks()  # 存到文件
        self.task_input.clear()
        self.refresh_table()
        self.adjust_window_height()

    def delete_task(self, task):
        """删除任务"""
        if task in self.tasks:
            self.tasks.remove(task)
            self.save_tasks()
            self.refresh_table()
            self.adjust_window_height()

    def save_tasks(self):
        """保存任务到文件"""
        try:
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(self.tasks, f, ensure_ascii=False, indent=2)
            print(f"成功保存任务数据: {len(self.tasks)} 条记录")
        except Exception as e:
            print(f"保存任务失败: {e}")

    def load_tasks(self):
        """加载任务"""
        try:
            if os.path.exists(self.data_file):
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                    if content:  # 确保文件不为空
                        self.tasks = json.loads(content)
                        print(f"成功加载任务数据: {len(self.tasks)} 条记录")
                    else:
                        self.tasks = []
                        print("数据文件为空，初始化任务列表")
            else:
                self.tasks = []
                print("数据文件不存在，初始化空任务列表")
            
            # 刷新表格显示
            self.refresh_table()
            
        except Exception as e:
            print(f"加载任务失败: {e}")
            # 如果加载失败，初始化空任务列表
            self.tasks = []
            # 创建新的数据文件
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump([], f, ensure_ascii=False)
            self.refresh_table()

    def refresh_table(self):
        """刷新表格显示"""
        # 清表格
        self.task_table.setRowCount(0)
        
        # 分离已完成和未完成的任务
        incomplete_tasks = [t for t in self.tasks if not t.get('completed', False)]
        completed_tasks = [t for t in self.tasks if t.get('completed', False)]
        
        # 添加未完成的任务
        for task in incomplete_tasks:
            self._add_task_to_table(task)
            
        # 添加已完成的任务
        for task in completed_tasks:
            self._add_task_to_table(task)
        
        # 调整窗口高度
        self.adjust_window_height()

    def _add_task_to_table(self, task):
        """添加任务到表格"""
        current_row = self.task_table.rowCount()
        self.task_table.insertRow(current_row)
        
        # 待办事项
        task_text = task['text']
        if len(task_text) > 20:
            task_text = task_text[:20] + '...'
        task_item = QTableWidgetItem(task_text)
        task_item.setToolTip(task['text'])
        
        # 如果任务已完成，添加删除线
        if task.get('completed', False):
            font = task_item.font()
            font.setStrikeOut(True)
            task_item.setFont(font)
            task_item.setForeground(QColor('#999999'))
        
        self.task_table.setItem(current_row, 0, task_item)
        
        # 优先级
        priority_item = QTableWidgetItem(task['priority'])
        priority_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        if task.get('completed', False):
            priority_item.setForeground(QColor('#999999'))
            font = priority_item.font()
            font.setStrikeOut(True)
            priority_item.setFont(font)
        elif task['priority'] == '紧急':
            priority_item.setForeground(QColor('red'))
        elif task['priority'] == '高':
            priority_item.setForeground(QColor('#fd7e14'))
        self.task_table.setItem(current_row, 1, priority_item)
        
        # 截止时间
        deadline = QDateTime.fromString(task['deadline'], 'yyyy-MM-dd HH:mm:ss')
        deadline_str = deadline.toString('MM-dd')
        deadline_item = QTableWidgetItem(deadline_str)
        deadline_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        if task.get('completed', False):
            deadline_item.setForeground(QColor('#999999'))
            font = deadline_item.font()
            font.setStrikeOut(True)
            deadline_item.setFont(font)
        else:
            # 只比较日期部分
            deadline_date = deadline.date()
            current_date = QDate.currentDate()
            if deadline_date < current_date:
                deadline_item.setForeground(QColor('red'))
        self.task_table.setItem(current_row, 2, deadline_item)
        
        # 操作列：包含复选框和删除按钮
        operation_widget = QWidget()
        operation_layout = QHBoxLayout(operation_widget)
        operation_layout.setContentsMargins(0, 0, 0, 0)
        operation_layout.setSpacing(5)  # 设置按钮之间的间距
        operation_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # 复选框
        checkbox = QCheckBox()
        checkbox.setChecked(task.get('completed', False))
        checkbox.setStyleSheet("""
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
                border: 2px solid #ff8ba7;
                border-radius: 2px;
                background-color: #ff8ba7;
                image: url(data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='8' height='8' viewBox='0 0 24 24' fill='none' stroke='white' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpolyline points='20 6 9 17 4 12'%3E%3C/polyline%3E%3C/svg%3E);
            }
            QCheckBox::indicator:unchecked:hover {
                border-color: #45a049;
                background-color: rgba(76, 175, 80, 0.1);
            }
            QCheckBox::indicator:checked:hover {
                border-color: #ff7096;
                background-color: #ff7096;
            }
        """)
        checkbox.stateChanged.connect(lambda state, t=task: self.toggle_task_completion(t, state))
        
        # 删除按钮
        delete_btn = QPushButton("×")
        delete_btn.setFixedSize(16, 16)
        delete_btn.setStyleSheet("""
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
        """)
        delete_btn.clicked.connect(lambda _, t=task: self.confirm_delete_task(t))
        
        # 添加到布局
        operation_layout.addWidget(checkbox)
        operation_layout.addWidget(delete_btn)
        
        self.task_table.setCellWidget(current_row, 3, operation_widget)
        
        # 设置行高
        self.task_table.setRowHeight(current_row, 24)

    def on_header_clicked(self, logical_index):
        """处理表头点击事件"""
        if logical_index == 1:  # 优先级列
            self.sort_by_priority()
        elif logical_index == 2:  # 日期列
            self.sort_by_deadline()

    def sort_by_priority(self):
        """按优先级排序"""
        # 切换排序顺序
        self.sort_order['priority'] = (Qt.SortOrder.DescendingOrder 
            if self.sort_order['priority'] == Qt.SortOrder.AscendingOrder 
            else Qt.SortOrder.AscendingOrder)
        
        # 分别对未完成和已完成的任务进行排序
        incomplete_tasks = [t for t in self.tasks if not t.get('completed', False)]
        completed_tasks = [t for t in self.tasks if t.get('completed', False)]
        
        # 排序未完成的任务
        incomplete_tasks.sort(
            key=lambda x: self.priority_values[x['priority']],
            reverse=(self.sort_order['priority'] == Qt.SortOrder.DescendingOrder)
        )
        
        # 排序已完成的任务
        completed_tasks.sort(
            key=lambda x: self.priority_values[x['priority']],
            reverse=(self.sort_order['priority'] == Qt.SortOrder.DescendingOrder)
        )
        
        # 合并任务列表，已完成的任务始终在后面
        self.tasks = incomplete_tasks + completed_tasks
        
        # 更新表格显示
        self.refresh_table()
        
        # 更新表头显示
        arrow = '↓' if self.sort_order['priority'] == Qt.SortOrder.DescendingOrder else '↑'
        headers = ['待办事项', f'优先级 {arrow}', '日期 ↕', '完成']
        self.task_table.setHorizontalHeaderLabels(headers)

    def sort_by_deadline(self):
        """按截止日期排序"""
        # 切换排序顺序
        self.sort_order['deadline'] = (Qt.SortOrder.DescendingOrder 
            if self.sort_order['deadline'] == Qt.SortOrder.AscendingOrder 
            else Qt.SortOrder.AscendingOrder)
        
        # 分别对未完成和已完成的任务进行排序
        incomplete_tasks = [t for t in self.tasks if not t.get('completed', False)]
        completed_tasks = [t for t in self.tasks if t.get('completed', False)]
        
        # 排序未完成的任务
        incomplete_tasks.sort(
            key=lambda x: QDateTime.fromString(x['deadline'], 'yyyy-MM-dd HH:mm:ss'),
            reverse=(self.sort_order['deadline'] == Qt.SortOrder.DescendingOrder)
        )
        
        # 排序已完成的任务
        completed_tasks.sort(
            key=lambda x: QDateTime.fromString(x['deadline'], 'yyyy-MM-dd HH:mm:ss'),
            reverse=(self.sort_order['deadline'] == Qt.SortOrder.DescendingOrder)
        )
        
        # 合并任务列表，已完成的任务始终在后面
        self.tasks = incomplete_tasks + completed_tasks
        
        # 更新表格显示
        self.refresh_table()
        
        # 更新表头显示
        arrow = '↓' if self.sort_order['deadline'] == Qt.SortOrder.DescendingOrder else '↑'
        headers = ['待办事项', '优先级 ↕', f'日期 {arrow}', '操作']
        self.task_table.setHorizontalHeaderLabels(headers)

    def mousePressEvent(self, event):
        """鼠标按下事件"""
        if event.button() == Qt.MouseButton.LeftButton:
            if self.is_on_edge(event.pos()):
                self.resizing = True
                self.resize_edge = self.get_resize_edge(event.pos())
            elif self.title_bar.geometry().contains(event.pos()):
                self.dragging = True
                self.offset = event.pos()

    def mouseReleaseEvent(self, event):
        """鼠标释放事件"""
        self.dragging = False
        self.resizing = False
        self.resize_edge = None
        self.unsetCursor()

    def mouseMoveEvent(self, event):
        """鼠标移动事件"""
        if self.dragging:
            # 处理窗口拖动
            self.move(self.mapToGlobal(event.pos() - self.offset))
        elif self.resizing:
            # 处理窗口大小调整
            global_pos = self.mapToGlobal(event.pos())
            if 'right' in self.resize_edge:
                width = global_pos.x() - self.frameGeometry().left()
                width = max(self.minimumWidth(), width)
                self.resize(width, self.height())
            if 'bottom' in self.resize_edge:
                height = global_pos.y() - self.frameGeometry().top()
                height = max(self.minimumHeight(), height)
                self.resize(self.width(), height)
        else:
            # 更新鼠标样式
            if self.is_on_edge(event.pos()):
                edge = self.get_resize_edge(event.pos())
                if 'right bottom' in edge:
                    self.setCursor(Qt.CursorShape.SizeFDiagCursor)
                elif 'right' in edge:
                    self.setCursor(Qt.CursorShape.SizeHorCursor)
                elif 'bottom' in edge:
                    self.setCursor(Qt.CursorShape.SizeVerCursor)
            else:
                self.unsetCursor()

    def is_on_edge(self, pos):
        """判断是否在窗口边缘"""
        rect = self.rect()
        # 检查是否在右边缘或底部边缘
        on_right = pos.x() >= rect.right() - self.resize_margin
        on_bottom = pos.y() >= rect.bottom() - self.bottom_margin
        
        # 如果在右下角，返回True
        if on_right and pos.y() >= rect.bottom() - self.resize_margin:
            return True
        
        # 如果在底部边缘的任何位置，返回True
        if on_bottom:
            return True
            
        # 如果在右边缘，返回True
        return on_right

    def get_resize_edge(self, pos):
        """获取调整大小的边缘类型"""
        rect = self.rect()
        edge = []
        
        # 检查右边缘
        if pos.x() >= rect.right() - self.resize_margin:
            edge.append('right')
            
        # 检查底部边缘（整个底部区域）
        if pos.y() >= rect.bottom() - self.bottom_margin:
            edge.append('bottom')
            
        return ' '.join(edge)

    def apply_styles(self):
        self.setStyleSheet("""
            QMainWindow {
                background-color: #fff6f6;
                border: 1px solid #ffccd5;
                border-radius: 8px;
            }
            #titleBar {
                background-color: #ffecef;
                border-bottom: 1px solid #ffccd5;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                min-height: 22px;
                max-height: 22px;
            }
            QLineEdit, QComboBox, QDateTimeEdit {
                background-color: white;
                border: 1px solid #ffccd5;
                border-radius: 4px;
                padding: 2px 4px;
            }
            QPushButton {
                background-color: #ff8ba7;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 2px 8px;
            }
            QPushButton:hover {
                background-color: #ff7096;
            }
            QTableWidget {
                background-color: transparent;
                border: none;
                gridline-color: #ffccd5;
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
                background-color: #ffecef;
                padding: 2px;
                border: none;
                border-bottom: 1px solid #ffccd5;
                font-weight: bold;
                color: #ff8ba7;
            }
            /* 设置输入区域背景透明 */
            #input_widget {
                background-color: transparent;
                margin: 0px;
                padding: 0px;
            }
        """)

    def verify_column_widths(self):
        """验证并强制设置列宽"""
        print("Initial column widths:", [self.task_table.columnWidth(i) for i in range(4)])
        
        # 再次强制设置列宽
        self.task_table.setColumnWidth(1, 45)
        self.task_table.setColumnWidth(2, 45)
        self.task_table.setColumnWidth(3, 45)
        
        print("Final column widths:", [self.task_table.columnWidth(i) for i in range(4)])

    def create_settings_menu(self):
        """创建设置菜单"""
        settings_menu = QMenu(self)
        
        # 添加自启动选项
        autostart_action = QAction("开机自启动", self)
        autostart_action.setCheckable(True)
        
        # 检查是否已设置自启动
        startup_path = os.path.join(
            os.getenv('APPDATA'),
            r'Microsoft\Windows\Start Menu\Programs\Startup',
            'TodoList.lnk'
        )
        autostart_action.setChecked(os.path.exists(startup_path))
        
        # 连接信号
        autostart_action.triggered.connect(self.toggle_autostart)
        
        settings_menu.addAction(autostart_action)
        return settings_menu

    def toggle_autostart(self, checked):
        """切换自启动状态"""
        if checked:
            self.setup_autostart()
        else:
            self.remove_autostart()

    def toggle_task_completion(self, task, state):
        """切换任务完成状态"""
        is_completed = state == Qt.CheckState.Checked.value
        
        # 获取当前行
        current_row = None
        for row in range(self.task_table.rowCount()):
            if self.tasks[row] == task:
                current_row = row
                break
        
        if current_row is not None:
            # 创建动画效果
            self.animate_row_completion(current_row, is_completed)

    def animate_row_completion(self, row, is_completed):
        """行完成动画"""
        # 创建一个半透明的遮罩效果
        def update_opacity(value):
            for col in range(self.task_table.columnCount()):
                item = self.task_table.item(row, col)
                if item:
                    color = item.foreground().color()
                    color.setAlpha(int(255 * (1 - value)))
                    item.setForeground(color)
                    
                    # 如果是完成状态，添加删除线
                    font = item.font()
                    font.setStrikeOut(value == 1.0 and is_completed)
                    item.setFont(font)
            self.task_table.viewport().update()
        
        # 使用 QTimer 创建帧动画
        duration = 500  # 动画持续时间（毫秒）
        frames = 20     # 动画帧数
        current_frame = 0
        
        def animate_frame():
            nonlocal current_frame
            if current_frame <= frames:
                progress = current_frame / frames
                update_opacity(progress)
                current_frame += 1
            else:
                timer.stop()
                # 动画完成后更新任务状态
                self.update_task_status(self.tasks[row], is_completed)
        
        timer = QTimer(self)
        timer.timeout.connect(animate_frame)
        timer.start(duration // frames)

    def update_task_status(self, task, is_completed):
        """更新任务状态并重新排序"""
        task['completed'] = is_completed
        self.save_tasks()
        
        # 准备新的任务顺序
        incomplete_tasks = [t for t in self.tasks if not t.get('completed', False)]
        completed_tasks = [t for t in self.tasks if t.get('completed', False)]
        self.tasks = incomplete_tasks + completed_tasks
        
        # 使用动画刷新表格
        self.animate_table_refresh()

    def animate_table_refresh(self):
        """表格刷新动画"""
        # 保存当前任务顺序，避免重复添加
        current_tasks = self.tasks.copy()
        
        # 清空表格
        self.task_table.setRowCount(0)
        
        # 添加所有任务
        for index, task in enumerate(current_tasks):
            # 添加任务到表格
            self._add_task_to_table(task)
            current_row = index  # 使用index作为行号，避免重复计算
            
            # 设置初始透明度
            def update_row_opacity(row, value):
                for col in range(self.task_table.columnCount()):
                    item = self.task_table.item(row, col)
                    if item:
                        color = item.foreground().color()
                        color.setAlpha(int(255 * value))
                        item.setForeground(color)
                
                # 更新操作列的widget透明度
                operation_widget = self.task_table.cellWidget(row, 3)
                if operation_widget:
                    opacity_effect = QGraphicsOpacityEffect(operation_widget)
                    opacity_effect.setOpacity(value)
                    operation_widget.setGraphicsEffect(opacity_effect)
                
                self.task_table.viewport().update()
            
            # 设置初始透明度
            update_row_opacity(current_row, 0.0)
            
            # 创建渐入动画
            def create_fade_in(row, delay):
                frames = 10
                duration_per_frame = 30  # 每帧持续时间（毫秒）
                
                # 创建动画计时器
                timer = QTimer(self)
                current_frame = [0]  # 使用列表存储当前帧，以便在lambda中修改
                
                def animate_fade_in():
                    if current_frame[0] <= frames:
                        progress = current_frame[0] / frames
                        update_row_opacity(row, progress)
                        current_frame[0] += 1
                    else:
                        timer.stop()
                        # 动画完成后清理效果
                        operation_widget = self.task_table.cellWidget(row, 3)
                        if operation_widget:
                            operation_widget.setGraphicsEffect(None)
                
                timer.timeout.connect(animate_fade_in)
                QTimer.singleShot(delay, lambda: timer.start(duration_per_frame))
            
            # 错开每行的动画开始时间
            create_fade_in(current_row, index * 50)
        
        # 调整窗口高度
        self.adjust_window_height()

    def _add_task_to_table(self, task):
        """添加任务到表格"""
        current_row = self.task_table.rowCount()
        self.task_table.insertRow(current_row)
        
        # 待办事项
        task_text = task['text']
        if len(task_text) > 20:
            task_text = task_text[:20] + '...'
        task_item = QTableWidgetItem(task_text)
        task_item.setToolTip(task['text'])
        
        # 如果任务已完成，添加删除线
        if task.get('completed', False):
            font = task_item.font()
            font.setStrikeOut(True)
            task_item.setFont(font)
            task_item.setForeground(QColor('#999999'))
        
        self.task_table.setItem(current_row, 0, task_item)
        
        # 优先级
        priority_item = QTableWidgetItem(task['priority'])
        priority_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        if task.get('completed', False):
            priority_item.setForeground(QColor('#999999'))
            font = priority_item.font()
            font.setStrikeOut(True)
            priority_item.setFont(font)
        elif task['priority'] == '紧急':
            priority_item.setForeground(QColor('red'))
        elif task['priority'] == '高':
            priority_item.setForeground(QColor('#fd7e14'))
        self.task_table.setItem(current_row, 1, priority_item)
        
        # 截止时间
        deadline = QDateTime.fromString(task['deadline'], 'yyyy-MM-dd HH:mm:ss')
        deadline_str = deadline.toString('MM-dd')
        deadline_item = QTableWidgetItem(deadline_str)
        deadline_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        if task.get('completed', False):
            deadline_item.setForeground(QColor('#999999'))
            font = deadline_item.font()
            font.setStrikeOut(True)
            deadline_item.setFont(font)
        else:
         # 只比较日期部分
            deadline_date = deadline.date()

            current_date = QDate.currentDate()
            if deadline_date < current_date:
                deadline_item.setForeground(QColor('red'))
            
        self.task_table.setItem(current_row, 2, deadline_item)
        
        # 操作列：包含复选框和删除按钮
        operation_widget = QWidget()
        operation_layout = QHBoxLayout(operation_widget)
        operation_layout.setContentsMargins(0, 0, 0, 0)
        operation_layout.setSpacing(5)  # 设置按钮之间的间距
        operation_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # 复选框
        checkbox = QCheckBox()
        checkbox.setChecked(task.get('completed', False))
        checkbox.setStyleSheet("""
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
                border: 2px solid #ff8ba7;
                border-radius: 2px;
                background-color: #ff8ba7;
                image: url(data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='8' height='8' viewBox='0 0 24 24' fill='none' stroke='white' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpolyline points='20 6 9 17 4 12'%3E%3C/polyline%3E%3C/svg%3E);
            }
            QCheckBox::indicator:unchecked:hover {
                border-color: #45a049;
                background-color: rgba(76, 175, 80, 0.1);
            }
            QCheckBox::indicator:checked:hover {
                border-color: #ff7096;
                background-color: #ff7096;
            }
        """)
        checkbox.stateChanged.connect(lambda state, t=task: self.toggle_task_completion(t, state))
        
        # 删除按钮
        delete_btn = QPushButton("×")
        delete_btn.setFixedSize(16, 16)
        delete_btn.setStyleSheet("""
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
        """)
        delete_btn.clicked.connect(lambda _, t=task: self.confirm_delete_task(t))
        
        # 添加到布局
        operation_layout.addWidget(checkbox)
        operation_layout.addWidget(delete_btn)
        
        self.task_table.setCellWidget(current_row, 3, operation_widget)
        
        # 设置行高
        self.task_table.setRowHeight(current_row, 24)

    def adjust_window_height(self):
        """调整窗口高度"""
        # 基础UI元素高度
        title_height = 30     # 标题栏
        input_height = 40     # 输入区域
        padding = 10          # 上下内边距
        
        # 表格高度
        header_height = self.task_table.horizontalHeader().height()
        row_height = 24       # 单行高度
        row_count = self.task_table.rowCount()
        
        # 计算内容高度
        content_height = row_height if row_count == 0 else row_height * row_count
        
        # 计算总高度
        total_height = (title_height + 
                       input_height + 
                       header_height + 
                       content_height + 
                       padding * 2)
        
        print(f"Height calculation:")
        print(f"- Row count: {row_count}")
        print(f"- Title: {title_height}")
        print(f"- Input: {input_height}")
        print(f"- Header: {header_height}")
        print(f"- Content: {content_height}")
        print(f"- Padding: {padding * 2}")
        print(f"- Total: {total_height}")
        
        # 强制调整窗口大小
        self.setFixedHeight(total_height)

    def confirm_delete_task(self, task):
        """确认删除任务"""
        dialog = QDialog(self)
        dialog.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        dialog.setFixedSize(200, 100)  # 设置对话框大小
        layout = QVBoxLayout(dialog)
        
        label = QLabel("确定删除？", dialog)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(label)
        
        button_layout = QHBoxLayout()
        confirm_button = QPushButton("确定", dialog)
        cancel_button = QPushButton("取消", dialog)
        button_layout.addWidget(confirm_button)
        button_layout.addWidget(cancel_button)
        
        layout.addLayout(button_layout)
        
        confirm_button.clicked.connect(dialog.accept)
        cancel_button.clicked.connect(dialog.reject)
        
        # 计算对话框位置（居中显示）
        x = self.x() + (self.width() - dialog.width()) // 2
        y = self.y() + (self.height() - dialog.height()) // 2
        dialog.move(x, y)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.delete_task(task)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    widget = TodoWidget()
    widget.show()
    sys.exit(app.exec())
