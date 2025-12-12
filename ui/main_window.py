import sys
import uuid
from datetime import datetime
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QGridLayout, QPushButton, QLineEdit, QComboBox, 
                            QDateTimeEdit, QLabel, QTableWidget, QTableWidgetItem,
                            QHeaderView, QSizePolicy, QDialog, QMenu, QCheckBox, QGraphicsOpacityEffect, 
                            QCalendarWidget, QMessageBox, QInputDialog)
from PyQt6.QtCore import Qt, QDateTime, QPoint, QRect, QTimer, QPropertyAnimation, QEasingCurve, QEvent, QDate
from PyQt6.QtGui import QColor, QFont, QKeySequence, QShortcut, QAction

from core.config import get_current_version
from core.task_manager import TaskManager
from .dialogs import DeleteConfirmDialog, ReminderDialog
from .pomodoro_widget import PomodoroWidget
from .styles import (MAIN_WINDOW_STYLE, MENU_STYLE, CHECKBOX_STYLE, 
                    DELETE_BTN_STYLE, CALENDAR_STYLE)

class TodoWidget(QMainWindow):
    def __init__(self):
        super().__init__()
        self.task_manager = TaskManager()
        self.task_count = 0  # 用于跟踪序号
        
        # 移除系统默认的标题栏
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        
        # 初始化拖拽相关变量
        self.dragging = False
        self.resizing = False
        self.offset = QPoint()
        self.resize_edge = None
        self.resize_margin = 5  # 调整大小的边缘宽度
        self.bottom_margin = 20     # 增大底部边缘检测范围到20像素

        # 顶部自动收缩相关状态变量
        self.is_docked_top = False  # 布尔变量：记录窗口是否处于顶部收缩状态
        self.normal_geometry = None  # 变量：用于保存收缩前的窗口几何尺寸与位置，便于恢复
        self.dock_threshold = 3  # 整数：触顶判定的阈值（像素），小偏差更平滑
        self.title_bar_height = 22  # 整数：标题栏高度
        self.hover_expand_delay = 0  # 整数：悬停展开的延迟（毫秒）
        self.dock_icon = None  # 变量：用于保存收缩状态下的悬浮图标窗口引用

        # 分页相关状态变量
        self.page_size = 30 # 整数：每页显示的任务条数
        self.current_page = 1  # 整数：当前页码
        self.total_pages = 1  # 整数：总页数
        self.page_label = None  # 变量：分页状态标签控件
        self.pagination_widget = None  # 变量：分页容器控件

        # 移除最小高度限制
        self.setMinimumHeight(0)
        
        # 设置最小宽度
        self.setMinimumWidth(160)
        
        # 加载任务数据
        self.task_manager.load_tasks()
        
        # 初始化UI
        self.initUI()
        # self.apply_styles()  # 恢复原有基础样式，不应用粉色主题
        
        self.refresh_table()
        
    def initUI(self):
        # 设置窗口标题（任务栏显示名称）
        self.setWindowTitle(f"TodoList V{get_current_version()}")

        # 设置窗口位置和初始大小
        self.setGeometry(50, 50, 380, 350)
        
        # 创建主窗口部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(20)
        
        # 自定义标题栏
        title_bar = QWidget()
        title_bar_layout = QHBoxLayout(title_bar)
        title_bar_layout.setContentsMargins(8, 0, 0, 0)
        title_bar_layout.setSpacing(4)
        title_bar.setFixedHeight(22)
        title_bar.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        title_bar.setObjectName("titleBar")
        
        # 添加小标
        icon_label = QLabel('🦄')
        icon_label.setStyleSheet("font-size: 16px; font-weight: bold;color: #9370DB;")
        title_bar_layout.addWidget(icon_label)
        
        # 修改标题文本
        title_label = QLabel('待办清单-日事日毕，日清日高-{}'.format(get_current_version()))
        title_label.setObjectName("titleLabel")
        title_bar_layout.addWidget(title_label)
        title_bar_layout.addStretch()
        
        # 最小化、收缩和关闭按钮
        min_button = QPushButton('－')
        min_button.setFixedSize(22, 22)
        min_button.setObjectName("minButton")
        min_button.clicked.connect(self.showMinimized)
        collapse_button = QPushButton('收缩')
        collapse_button.setFixedSize(36, 22)
        collapse_button.setObjectName("collapseButton")
        collapse_button.clicked.connect(lambda: self.toggle_collapse())
        
        close_button = QPushButton('×')
        close_button.setFixedSize(22, 22)
        close_button.setObjectName("closeButton")
        close_button.clicked.connect(self.close)
        
        title_bar_layout.addWidget(min_button)
        title_bar_layout.addWidget(collapse_button)
        title_bar_layout.addWidget(close_button)
        
        # 保存标题栏引用用于拖动
        self.title_bar = title_bar
        
        # 主布局
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(1, 0, 3, 5)
        layout.setSpacing(0)
        
        # 添加标题栏和其他部件
        layout.addWidget(title_bar)
        
        # 创建输入区域
        input_widget = QWidget()
        input_widget.setObjectName("input_widget")
        input_layout = QGridLayout(input_widget)
        input_layout.setContentsMargins(8, 4, 8, 4)
        input_layout.setHorizontalSpacing(4)
        input_layout.setVerticalSpacing(6)
        
        self.task_input = QLineEdit()
        self.task_input.setPlaceholderText('输入待办事项...')
        self.task_input.setFixedHeight(24)
        self.task_input.setMinimumWidth(0)
        self.task_input.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        
        self.priority_combo = QComboBox()
        self.priority_combo.addItems(['紧急重要', '重要不紧急', '紧急不重要', '不紧急不重要'])
        self.priority_combo.setCurrentText('重要不紧急')
        self.priority_combo.setFixedSize(80, 24)
        self.priority_combo.setMinimumWidth(0)
        self.priority_combo.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        
        self.deadline_edit = QDateTimeEdit(QDateTime.currentDateTime())
        self.deadline_edit.setDisplayFormat("MM-dd")
        self.deadline_edit.setCalendarPopup(True)
        self.deadline_edit.setFixedSize(50, 24)
        self.deadline_edit.setMinimumWidth(0)
        self.deadline_edit.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        
        add_button = QPushButton('添加')
        add_button.setFixedSize(50, 24)
        add_button.setMinimumWidth(0)
        add_button.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        add_button.clicked.connect(self.add_task)
        self.add_button = add_button
        
        # 网格布局初始放置
        input_layout.addWidget(self.task_input, 0, 0, 1, 3)
        input_layout.addWidget(self.priority_combo, 0, 3, 1, 1)
        input_layout.addWidget(self.deadline_edit, 0, 4, 1, 1)
        input_layout.addWidget(add_button, 0, 5, 1, 1)
        
        input_widget.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        fixed_input_height = 24 + input_layout.contentsMargins().top() + input_layout.contentsMargins().bottom()
        input_widget.setMinimumHeight(fixed_input_height)

        self.input_widget = input_widget
        layout.addWidget(input_widget)
        
        # 番茄钟组件
        self.pomodoro_widget = PomodoroWidget(self.task_manager)
        layout.addWidget(self.pomodoro_widget)
        
        # 表格设置
        self.task_table = QTableWidget()
        self.task_table.setColumnCount(4)
        self.task_table.setHorizontalHeaderLabels(['待办事项', '优先级 ↕', '日期 ↕', '完成'])
        
        self.task_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.task_table.setEditTriggers(QTableWidget.EditTrigger.DoubleClicked)
        self.task_table.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        self.task_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.task_table.customContextMenuRequested.connect(self.show_context_menu)
    
        self.task_table.itemDoubleClicked.connect(self.handle_item_double_click)
        self.task_table.itemChanged.connect(self.handle_item_changed)

        self.task_table.verticalHeader().setDefaultSectionSize(24)
        self.task_table.verticalHeader().setMinimumSectionSize(24)
        self.task_table.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        header = self.task_table.horizontalHeader()
        header.sectionClicked.connect(self.on_header_clicked)
        header.setStretchLastSection(False)
        header.setMinimumSectionSize(0)
        header.setDefaultSectionSize(45)
        self.task_table.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        header.setSectionsMovable(False)
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        for i in range(1, 4):
            header.setSectionResizeMode(i, QHeaderView.ResizeMode.Interactive)
        
        QTimer.singleShot(0, self.initial_column_setup)

        layout.addWidget(self.task_table)
        layout.setStretch(2, 1)

        # 创建底部分页容器控件
        pagination_widget = QWidget(self)
        pagination_layout = QHBoxLayout(pagination_widget)
        pagination_layout.setContentsMargins(8, 0, 8, 0)
        pagination_layout.setSpacing(6)

        prev_btn = QPushButton('<')
        prev_btn.setFixedSize(24, 24)
        prev_btn.setStyleSheet('border:none;')
        prev_btn.clicked.connect(self.on_prev_page)

        page_label = QLabel('1/1')
        page_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        page_label.setStyleSheet('font-size:12px;color:#333;')

        next_btn = QPushButton('>')
        next_btn.setFixedSize(24, 24)
        next_btn.setStyleSheet('border:none;')
        next_btn.clicked.connect(self.on_next_page)

        pagination_layout.addWidget(prev_btn)
        pagination_layout.addWidget(page_label)
        pagination_layout.addWidget(next_btn)

        pagination_widget.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        pagination_widget.setFixedHeight(26)

        self.pagination_widget = pagination_widget
        self.page_label = page_label
        self.prev_btn = prev_btn
        self.next_btn = next_btn

        layout.addWidget(self.pagination_widget)

        # 创建一个背景widget来显示水印
        self.background_widget = QWidget(self)
        self.background_widget.setObjectName("backgroundWidget")
        self.background_widget.lower()
        self.background_widget.setGeometry(0, 0, self.width(), self.height())

        self.content_widgets = [self.input_widget, self.pomodoro_widget, self.task_table, self.background_widget, self.pagination_widget]
        self.task_table.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        self.setup_dock_icon()
        # self.adjustSize()

        self.task_table.horizontalHeader().setStretchLastSection(False)
        self.task_table.verticalHeader().setStretchLastSection(False)

        self.verify_column_widths()

        screen = QApplication.primaryScreen()
        if screen is not None:
            screen_height = screen.availableGeometry().height()
        else:
            screen_height = 800
        self.max_window_height = int(screen_height)
        self.setMaximumHeight(self.max_window_height)
        QTimer.singleShot(0, self.adjust_window_height)

        self.title_bar_height = self.title_bar.height()
        self.update_pagination_ui()
        self.update_table_font_by_window()
        self.title_bar.installEventFilter(self)

        try:
            self.collapse_shortcut = QShortcut(QKeySequence('Alt+S'), self)
            self.collapse_shortcut.activated.connect(self.toggle_collapse)
        except Exception as e:
            print(f"快捷键注册失败: {e}")

    def apply_styles(self):
        self.setStyleSheet(MAIN_WINDOW_STYLE)

    def add_task(self):
        """添加任务"""
        task_text = self.task_input.text().strip()
        if not task_text:
            return
        
        priority = self.priority_combo.currentText()
        deadline = self.deadline_edit.dateTime().toString('yyyy-MM-dd')
        
        task = {
            'id': str(uuid.uuid4()),
            'text': task_text,
            'priority': priority,
            'deadline': deadline,
            'completed': False
        }
        
        self.task_manager.add_task(task)
        self.task_input.clear()
        self.refresh_table()
        self.adjust_window_height()

    def delete_task(self, task):
        """删除任务"""
        self.task_manager.delete_task(task)
        self.refresh_table()
        self.adjust_window_height()

    def refresh_table(self):
        """刷新表格显示"""
        self.task_table.blockSignals(True)
        # print("刷新表格显示-----信号已断开")
        
        # 获取用于显示的任务（已处理完成状态和排序）
        all_display_tasks = self.task_manager.get_tasks_for_display()

        # 计算总页数
        total_count = len(all_display_tasks)
        self.total_pages = max(1, (total_count + self.page_size - 1) // self.page_size)

        if self.current_page > self.total_pages:
            self.current_page = self.total_pages
        if self.current_page < 1:
            self.current_page = 1

        start_index = (self.current_page - 1) * self.page_size
        end_index = start_index + self.page_size
        display_tasks = all_display_tasks[start_index:end_index]

        self.task_table.setRowCount(0)
        
        for task in display_tasks:
            self._add_task_to_table(task)

        self.adjust_window_height()
        self.update_pagination_ui()
        self.update_table_font_by_window()

        self.task_table.blockSignals(False)
        # print("刷新表格显示-----信号已连接")

        hsb = self.task_table.horizontalScrollBar()
        if hsb.maximum() > 0 and hsb.value() != 0:
            self.smooth_scrollbar(hsb, 0, 180)

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
        task_item.setData(Qt.ItemDataRole.UserRole, task.get('id'))
        
        if task.get('completed', False):
            font = task_item.font()
            font.setStrikeOut(True)
            task_item.setFont(font)
            task_item.setForeground(QColor('#999999'))
        
        self.task_table.setItem(current_row, 0, task_item)
        
        # 优先级下拉框
        priority_combo = QComboBox()
        priority_combo.addItems(['紧急重要', '重要不紧急', '紧急不重要', '不紧急不重要'])
        try:
            priority_combo.setCurrentText(task['priority'])
        except Exception as e:
            priority_combo.setCurrentText('不紧急不重要')
            task['priority'] = '不紧急不重要'
        
        priority_combo.setFixedSize(80, 24)
        
        current_priority = task['priority']
        is_completed = task.get('completed', False)
        
        base_style = """
            QComboBox {
                border: none;
                background: transparent;
                padding-left: 4px;
                %s
            }
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            QComboBox QAbstractItemView {
                border: 1px solid #e0e0e0;
                background: white;
                selection-background-color: #f5f5f5;
            }
            QComboBox QAbstractItemView::item[text="紧急重要"] { color: red; }
            QComboBox QAbstractItemView::item[text="重要不紧急"] { color: orange; }
        """
        
        if is_completed:
            style_extra = "color: #999999; text-decoration: line-through;"
        else:
            if current_priority == '紧急重要':
                style_extra = "color: #FF0000;"
            elif current_priority == '重要不紧急':
                style_extra = "color: orange;"
            else:
                style_extra = "color: black;"
        
        priority_combo.setStyleSheet(base_style % style_extra)
        
        if is_completed:
            priority_combo.setEnabled(False)
        
        priority_combo.activated.connect(
            lambda index, t=task: self.update_task_priority(t, priority_combo.itemText(index))
        )
        priority_combo.wheelEvent = lambda event: event.ignore()
        self.task_table.setCellWidget(current_row, 1, priority_combo)
        
        # 截止时间
        deadline = QDateTime.fromString(task['deadline'], 'yyyy-MM-dd')
        deadline_str = deadline.toString('MM-dd')
        
        date_btn = QPushButton(deadline_str)
        date_btn.setFixedSize(50, 24)
        
        if task.get('completed', False):
            date_btn.setStyleSheet("""
                QPushButton {
                    border: none;
                    background: transparent;
                    color: #999999;
                    text-decoration: line-through;
                }
            """)
            date_btn.setEnabled(False)
        else:
            if deadline.date() < QDate.currentDate():
                text_color = 'red'
                font_weight = "bold"
            else:
                text_color = 'black'
                font_weight = "normal"
            
            date_btn.setStyleSheet(f"""
                QPushButton {{
                    border: none;
                    background-color: transparent;
                    color: {text_color};
                    font-weight: {font_weight};
                    text-align: left;
                    padding-left: 0px;
                }}
                QPushButton:hover {{
                    background-color: #f5f5f5;
                }}
            """)
            
            date_btn.clicked.connect(lambda: self.show_calendar_for_task(task, date_btn))
            
        self.task_table.setCellWidget(current_row, 2, date_btn)
        
        # 操作列
        operation_widget = QWidget()
        operation_layout = QHBoxLayout(operation_widget)
        operation_layout.setContentsMargins(0, 0, 0, 0)
        operation_layout.setSpacing(5)
        operation_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        checkbox = QCheckBox()
        checkbox.setChecked(task.get('completed', False))
        checkbox.setStyleSheet(CHECKBOX_STYLE)
        checkbox.stateChanged.connect(lambda state, t=task: self.toggle_task_completion(t, state))
        
        delete_btn = QPushButton("×")
        delete_btn.setFixedSize(16, 16)
        delete_btn.setStyleSheet(DELETE_BTN_STYLE)
        delete_btn.clicked.connect(lambda _, t=task: self.confirm_delete_task(t))
        
        operation_layout.addWidget(checkbox)
        operation_layout.addWidget(delete_btn)
        self.task_table.setCellWidget(current_row, 3, operation_widget)
        self.task_table.setRowHeight(current_row, 24)

    def show_calendar_for_task(self, task, date_btn):
        calendar = QCalendarWidget(self)
        calendar.setWindowFlags(Qt.WindowType.Popup)
        calendar.setGridVisible(True)
        calendar.setStyleSheet(CALENDAR_STYLE)
        
        pos = date_btn.mapToGlobal(date_btn.rect().bottomLeft())
        calendar.move(pos)
        
        deadline = QDateTime.fromString(task['deadline'], 'yyyy-MM-dd')
        calendar.setSelectedDate(deadline.date())
        
        def date_selected(qdate):
            new_deadline = qdate.toString('yyyy-MM-dd')
            if task['deadline'] != new_deadline:
                task['deadline'] = new_deadline
                date_btn.setText(qdate.toString('MM-dd'))
                self.task_manager.save_tasks()
                self.refresh_table()
            calendar.close()
        
        calendar.clicked.connect(date_selected)
        calendar.show()

    def update_task_priority(self, task, new_priority):
        if task['priority'] != new_priority:
            task['priority'] = new_priority
            self.task_manager.save_tasks()
            self.refresh_table()

    def confirm_delete_task(self, task):
        dialog = DeleteConfirmDialog(self)
        # 计算居中位置：基于主窗口当前的几何中心
        main_geo = self.frameGeometry()
        center = main_geo.center()
        x = center.x() - dialog.width() // 2
        y = center.y() - dialog.height() // 2
        dialog.move(x, y)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.delete_task(task)

    def handle_item_double_click(self, item):
        row = item.row()
        column = item.column()
        item_id = item.data(Qt.ItemDataRole.UserRole)
        task = next((t for t in self.task_manager.tasks if t.get('id') == item_id), None)
        if task is None:
            return
        
        if column == 0:
            self.task_table.editItem(item)

    def handle_item_changed(self, item):
        column = item.column()
        item_id = item.data(Qt.ItemDataRole.UserRole)
        task = next((t for t in self.task_manager.tasks if t.get('id') == item_id), None)
        if task is None:
            return
        
        if column == 0:
            new_text = item.text().strip()
            if new_text and task['text'] != new_text:
                task['text'] = new_text
                self.task_manager.save_tasks()
                self.refresh_table()

    def on_header_clicked(self, logical_index):
        if logical_index == 1:
            sort_order = self.task_manager.sort_by_priority()
            self.refresh_table()
            arrow = '↓' if sort_order == Qt.SortOrder.DescendingOrder else '↑'
            headers = ['待办事项', f'优先级 {arrow}', '日期 ↕', '完成']
            self.task_table.setHorizontalHeaderLabels(headers)
        elif logical_index == 2:
            sort_order = self.task_manager.sort_by_deadline()
            self.refresh_table()
            arrow = '↓' if sort_order == Qt.SortOrder.DescendingOrder else '↑'
            headers = ['待办事项', '优先级 ↕', f'日期 {arrow}', '操作']
            self.task_table.setHorizontalHeaderLabels(headers)

    def toggle_task_completion(self, task, state):
        is_completed = state == Qt.CheckState.Checked.value
        current_row = None
        for row in range(self.task_table.rowCount()):
            item0 = self.task_table.item(row, 0)
            if item0 and item0.data(Qt.ItemDataRole.UserRole) == task.get('id'):
                current_row = row
                break
        
        if current_row is not None:
            self.animate_row_completion(current_row, is_completed, task)

    def animate_row_completion(self, row, is_completed, task):
        def update_opacity(value):
            for col in range(self.task_table.columnCount()):
                item = self.task_table.item(row, col)
                if item:
                    color = item.foreground().color()
                    color.setAlpha(int(255 * (1 - value)))
                    item.setForeground(color)
                    font = item.font()
                    font.setStrikeOut(value == 1.0 and is_completed)
                    item.setFont(font)
            self.task_table.viewport().update()
        
        duration = 500
        frames = 20
        current_frame = 0
        
        def animate_frame():
            nonlocal current_frame
            if current_frame <= frames:
                progress = current_frame / frames
                update_opacity(progress)
                current_frame += 1
            else:
                timer.stop()
                self.update_task_status(task, is_completed)
        
        timer = QTimer(self)
        timer.timeout.connect(animate_frame)
        timer.start(duration // frames)

    def update_task_status(self, task, is_completed):
        task['completed'] = is_completed
        self.task_manager.save_tasks()
        # 刷新表格会重新排序
        self.refresh_table()

    def show_context_menu(self, pos):
        item = self.task_table.itemAt(pos)
        if not item: return
        row = item.row()
        id_item = self.task_table.item(row, 0)
        if not id_item: return
        task_id = id_item.data(Qt.ItemDataRole.UserRole)
        task = next((t for t in self.task_manager.tasks if t.get('id') == task_id), None)
        if not task: return

        menu = QMenu(self)
        menu.setStyleSheet(MENU_STYLE)
        
        # 移除提醒相关菜单
        
        menu.exec(self.task_table.mapToGlobal(pos))

    # --- 窗口交互、调整大小、收缩等逻辑 ---
    # 为了保持代码简洁，这里直接复制原有逻辑，稍作适配
    
    def adjust_window_height(self):
        title_height = self.title_bar.height()
        input_height = self.input_widget.height()
        pomodoro_height = self.pomodoro_widget.height() if hasattr(self, 'pomodoro_widget') else 0
        footer_height = self.pagination_widget.height() if self.pagination_widget else 0
        padding = 10
        header_height = self.task_table.horizontalHeader().height()
        row_height = 24
        row_count = self.task_table.rowCount()
        content_height = row_height if row_count == 0 else row_height * row_count
        total_height = (title_height + input_height + pomodoro_height + header_height + content_height + footer_height + padding * 2)

        if total_height <= self.max_window_height:
            self.resize(self.width(), total_height)
            self.task_table.setMaximumHeight(header_height + content_height)
            self.task_table.setMinimumHeight(header_height + row_height)
        else:
            self.resize(self.width(), self.max_window_height)
            available = self.max_window_height - (title_height + input_height + pomodoro_height + footer_height + padding * 2)
            available = max(available, header_height + row_height)
            self.task_table.setMaximumHeight(available)
            self.task_table.setMinimumHeight(header_height + row_height)
            self.task_table.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

    def collapse_to_title(self):
        if self.normal_geometry is None:
            self.normal_geometry = self.geometry()
        for w in self.content_widgets:
            w.setVisible(False)
        self.title_bar.setVisible(False)
        self.hide()
        self.show_dock_icon()
        self.is_docked_top = True

    def expand_from_title(self):
        if self.normal_geometry is None:
            self.normal_geometry = QRect(self.x(), 0, max(self.width(), 420), max(self.height(), 350))
        self.move(self.normal_geometry.x(), 0)
        self.resize(self.normal_geometry.width(), self.normal_geometry.height())
        self.show()
        self.raise_()
        self.activateWindow()
        self.hide_dock_icon()
        for w in self.content_widgets:
            w.setVisible(True)
        self.title_bar.setVisible(True)
        self.is_docked_top = False

    def toggle_collapse(self):
        if self.is_docked_top:
            self.expand_from_title()
        else:
            self.collapse_to_title()

    def eventFilter(self, obj, event):
        if obj is getattr(self, 'title_bar', None) and event.type() == QEvent.Type.MouseButtonDblClick:
            self.toggle_collapse()
            return True
        return super().eventFilter(obj, event)

    def setup_dock_icon(self):
        if self.dock_icon is not None: return
        self.dock_icon = QWidget(None, Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool | Qt.WindowType.WindowStaysOnTopHint)
        self.dock_icon.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.dock_icon.setFixedSize(28, 28)
        dock_layout = QHBoxLayout(self.dock_icon)
        dock_layout.setContentsMargins(0, 0, 0, 0)
        dock_layout.setSpacing(0)
        dock_btn = QPushButton('🦄')
        dock_btn.setFixedSize(28, 28)
        dock_btn.setStyleSheet("border:none;font-size:18px;background-color:rgba(255,255,255,0.9);")
        dock_btn.clicked.connect(self.on_dock_icon_clicked)
        dock_layout.addWidget(dock_btn)
        self.dock_icon.hide()

    def show_dock_icon(self):
        screen = QApplication.primaryScreen()
        screen_geom = screen.availableGeometry() if screen else QRect(0, 0, 800, 600)
        icon_w = self.dock_icon.width()
        target_x = max(0, min(self.x(), screen_geom.width() - icon_w))
        self.dock_icon.move(target_x, 0)
        self.dock_icon.show()

    def hide_dock_icon(self):
        if self.dock_icon and self.dock_icon.isVisible():
            self.dock_icon.hide()

    def on_dock_icon_clicked(self):
        self.expand_from_title()
        self.is_docked_top = False

    def initial_column_setup(self):
        content_width = self.width() - 5
        self.task_table.setFixedWidth(content_width)
        self.task_table.setColumnWidth(1, 80)
        self.task_table.setColumnWidth(2, 50)
        self.task_table.setColumnWidth(3, 50)
        self.task_table.horizontalHeader().updateGeometry()
        self.task_table.updateGeometry()

    def verify_column_widths(self):
        self.task_table.setColumnWidth(1, 80)
        self.task_table.setColumnWidth(2, 50)
        self.task_table.setColumnWidth(3, 50)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, 'task_table'):
            content_width = self.width() - 5
            self.task_table.setFixedWidth(content_width)
            self.task_table.setColumnWidth(1, 80)
            self.task_table.setColumnWidth(2, 50)
            self.task_table.setColumnWidth(3, 50)
            self.task_table.horizontalHeader().updateGeometry()
            self.task_table.updateGeometry()
            
            hsb = self.task_table.horizontalScrollBar()
            vsb = self.task_table.verticalScrollBar()
            if hsb.maximum() == 0: hsb.setValue(0)
            elif hsb.value() != 0: self.smooth_scrollbar(hsb, 0, 180)
            if vsb.maximum() == 0: vsb.setValue(0)
            
            self.update_table_font_by_window()
        
        try:
            self.relayout_input_bar()
        except: pass

    def update_table_font_by_window(self):
        w, h = self.width(), self.height()
        if w <= 480 or h <= 360:
            self.apply_table_font(11)
        elif w <= 640 or h <= 540:
            self.apply_table_font(13)
        else:
            self.apply_table_font(15)

    def apply_table_font(self, size_px):
        table_font = QFont()
        table_font.setPixelSize(size_px)
        self.task_table.setFont(table_font)
        item_css = f"font-size: {size_px}px;"
        for row in range(self.task_table.rowCount()):
            for col_idx in [1, 2, 3]:
                widget = self.task_table.cellWidget(row, col_idx)
                if widget:
                    if col_idx == 3: # 操作列
                        for child in widget.findChildren(QWidget):
                            if isinstance(child, QPushButton):
                                child.setStyleSheet(child.styleSheet() + f"\nQPushButton {{{item_css}}}")
                    else:
                        widget.setStyleSheet(widget.styleSheet() + f"\nQWidget {{{item_css}}}")

    def relayout_input_bar(self):
        if not hasattr(self, 'input_widget'): return
        # print(f"DEBUG: relayout_input_bar called, window width={self.width()}")
        layout = self.input_widget.layout()
        if not isinstance(layout, QGridLayout): return
        while layout.count():
            item = layout.takeAt(0)
            w = item.widget()
            if w: w.setParent(self.input_widget)
        width = self.width()
        if width >= 380:
            layout.addWidget(self.task_input, 0, 0, 1, 3)
            layout.addWidget(self.priority_combo, 0, 3, 1, 1)
            layout.addWidget(self.deadline_edit, 0, 4, 1, 1)
            layout.addWidget(self.add_button, 0, 5, 1, 1)
        elif width >= 300:
            layout.addWidget(self.task_input, 0, 0, 1, 6)
            layout.addWidget(self.priority_combo, 1, 0, 1, 2)
            layout.addWidget(self.deadline_edit, 1, 2, 1, 2)
            layout.addWidget(self.add_button, 1, 4, 1, 2)
        else:
            layout.addWidget(self.task_input, 0, 0, 1, 6)
            layout.addWidget(self.priority_combo, 1, 0, 1, 6)
            layout.addWidget(self.deadline_edit, 2, 0, 1, 6)
            layout.addWidget(self.add_button, 3, 0, 1, 6)

    def smooth_scrollbar(self, scrollbar, to_value, duration=200):
        try:
            anim = QPropertyAnimation(scrollbar, b"value", self)
            anim.setDuration(duration)
            anim.setStartValue(scrollbar.value())
            anim.setEndValue(to_value)
            anim.setEasingCurve(QEasingCurve.Type.InOutCubic)
            anim.start()
        except: pass

    def update_pagination_ui(self):
        if self.page_label:
            self.page_label.setText(f"{self.current_page}/{self.total_pages}")
        if self.prev_btn:
            self.prev_btn.setEnabled(self.current_page > 1)
        if self.next_btn:
            self.next_btn.setEnabled(self.current_page < self.total_pages)

    def on_prev_page(self):
        if self.current_page > 1:
            self.current_page -= 1
            self.refresh_table()

    def on_next_page(self):
        if self.current_page < self.total_pages:
            self.current_page += 1
            self.refresh_table()

    # 鼠标事件处理
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            if self.is_on_edge(event.pos()):
                self.resizing = True
                self.resize_edge = self.get_resize_edge(event.pos())
            elif self.title_bar.geometry().contains(event.pos()):
                if self.is_docked_top:
                    self.expand_from_title()
                self.dragging = True
                self.offset = event.pos()

    def mouseReleaseEvent(self, event):
        self.dragging = False
        self.resizing = False
        self.resize_edge = None
        self.unsetCursor()

    def mouseMoveEvent(self, event):
        if self.dragging:
            self.move(self.mapToGlobal(event.pos() - self.offset))
            if self.is_docked_top and self.frameGeometry().top() > self.dock_threshold:
                self.is_docked_top = False
        elif self.resizing:
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
        rect = self.rect()
        on_right = pos.x() >= rect.right() - self.resize_margin
        on_bottom = pos.y() >= rect.bottom() - self.bottom_margin
        if on_right and pos.y() >= rect.bottom() - self.resize_margin: return True
        if on_bottom: return True
        return on_right

    def get_resize_edge(self, pos):
        rect = self.rect()
        edge = []
        if pos.x() >= rect.right() - self.resize_margin: edge.append('right')
        if pos.y() >= rect.bottom() - self.bottom_margin: edge.append('bottom')
        return ' '.join(edge)
