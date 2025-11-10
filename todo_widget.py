import sys
from datetime import datetime
from build import CONFIG_DATA  # Import CONFIG_DATA from build.py
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QPushButton, QLineEdit, QComboBox, 
                            QDateTimeEdit, QLabel, QTableWidget, QTableWidgetItem,
                            QHeaderView, QSizePolicy, QDialog, QMenu, QCheckBox, QGraphicsOpacityEffect, QCalendarWidget)
from PyQt6.QtCore import Qt, QDateTime, QPoint, QRect, QTimer, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QColor, QPainter
from PyQt6.QtCore import QDate
import json
import os
from pathlib import Path
import uuid
import re

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
        self.priority_values = {'不紧急不重要': 0, '紧急不重要': 1, '重要不紧急': 2, '紧急重要': 3}
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

        # 顶部自动收缩相关状态变量（用于实现类似QQ的吸顶与悬停展开）
        self.is_docked_top = False  # 布尔变量：记录窗口是否处于顶部收缩状态
        self.normal_geometry = None  # 变量：用于保存收缩前的窗口几何尺寸与位置，便于恢复
        self.dock_threshold = 3  # 整数：触顶判定的阈值（像素），小偏差更平滑
        self.title_bar_height = 22  # 整数：标题栏高度（与initUI中固定高度一致，便于收缩时仅显示标题栏）
        self.hover_expand_delay = 0  # 整数：悬停展开的延迟（毫秒），0表示立即展开，保持简单有效
        self.dock_icon = None  # 变量：用于保存收缩状态下的悬浮图标窗口引用，点击后展开主窗口

        # 分页相关状态变量（用于控制表格分页显示）
        self.page_size = 30 # 整数：每页显示的任务条数，按需求固定为20条
        self.current_page = 1  # 整数：当前页码，从1开始，用户点击上一页/下一页时更新
        self.total_pages = 1  # 整数：总页数，随任务数量变化动态计算
        self.page_label = None  # 变量：分页状态标签控件，用于显示“当前页/总页”文本
        self.pagination_widget = None  # 变量：分页容器控件，位于表格下方，包含上一页、页码、下一页三个元素

        # 移除最小高度限制
        self.setMinimumHeight(0)
        
        # 设置最小宽度
        self.setMinimumWidth(400)  # 增加最小宽度从300到400

        # 确保数据文件存在
        if not os.path.exists(self.data_file):
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump([], f, ensure_ascii=False)
        
        # 初始化UI
        self.initUI()
        
        # 加载任务数据
        self.load_tasks()
        
        
    def initUI(self):
        # 设置窗口位置和初始大小
        self.setGeometry(50, 50, 420, 350)  # 增加初始宽度从320到420
        
        # 移除最小高度限制的设置（仅保留最小宽度在 __init__ 中设置的 400）
        # 注意：这里不再调用 setMinimumSize(400, 300)，以允许窗口收缩到仅标题栏高度
        
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
        title_bar.setFixedHeight(22)  # 固定标题栏高度为22像素，避免随窗口拖拽变动
        title_bar.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)  # 设置标题栏垂直方向固定，水平自适应
        title_bar.setObjectName("titleBar")
        
        # 添加小标
        icon_label = QLabel('🦄')  # 使用独角兽表情，更加显眼
        icon_label.setStyleSheet("font-size: 16px; font-weight: bold;color: #9370DB;")  # 紫色独角兽icon_label.setObjectName("iconLabel")
        title_bar_layout.addWidget(icon_label)
        
        # 修改标题文本
        title_label = QLabel('待办清单-日事日毕，日清日高-{}'.format(json.loads(CONFIG_DATA)['current_version']))
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
        input_widget = QWidget()  # 创建输入区域容器控件（顶部操作/筛选栏），用于承载输入框、下拉框、日期、添加按钮
        input_layout = QHBoxLayout(input_widget)
        input_layout.setContentsMargins(8, 4, 8, 4)  # 减小上下边距
        input_layout.setSpacing(4)
        
        # 修复输入控件高度
        self.task_input = QLineEdit()
        self.task_input.setPlaceholderText('输入待办事项...')
        self.task_input.setFixedHeight(24)  # 固定高度
        
        self.priority_combo = QComboBox()
        self.priority_combo.addItems(['紧急重要', '重要不紧急', '紧急不重要', '不紧急不重要'])
        self.priority_combo.setCurrentText('重要不紧急')
        self.priority_combo.setFixedSize(100, 24)  # 增加宽度从50到100
        
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
        
        # 设置输入区域容器的尺寸策略：水平为 Preferred，垂直为 Fixed，避免拖拽窗口时该区域被拉伸变高
        input_widget.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)  # 仅允许水平自适应，垂直固定高度
        # 计算并设置输入区域容器的固定高度（控件高度24 + 上下边距4+4 = 32），确保拖动窗口时该区域高度不变化
        fixed_input_height = 24 + input_layout.contentsMargins().top() + input_layout.contentsMargins().bottom()  # 计算固定高度
        input_widget.setFixedHeight(fixed_input_height)  # 设置固定高度，防止垂直方向拉伸

        self.input_widget = input_widget  # 记录输入区域容器控件，便于收缩/展开时统一隐藏与显示
        layout.addWidget(input_widget)  # 将输入区域添加到主布局中
        
        # 表格设置
        self.task_table = QTableWidget()
        self.task_table.setColumnCount(4)
        self.task_table.setHorizontalHeaderLabels(['待办事项', '优先级 ↕', '日期 ↕', '完成'])
        
        # 设置第一列的宽度为自动调整以适应内容
        self.task_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.task_table.setEditTriggers(QTableWidget.EditTrigger.DoubleClicked)
        # 禁止用户选择表格中的行
        self.task_table.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        # # 隐藏表格的网格线
        # self.task_table.setShowGrid(False)
        # # 隐藏垂直头部（行号）
        # self.task_table.verticalHeader().setVisible(False)
    
        # 确保连接双击事件
        self.task_table.itemDoubleClicked.connect(self.handle_item_double_click)
        # 连接 itemChanged 信号
        self.task_table.itemChanged.connect(self.handle_item_changed)

        # 设置表格行高
        self.task_table.verticalHeader().setDefaultSectionSize(24)
        self.task_table.verticalHeader().setMinimumSectionSize(24)
        
        # 启用垂直滚动条按需显示（当内容超过可视区域时才显示）
        self.task_table.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)  # 设置滚动策略为按需显示，提升用户体验
        
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

        layout.addWidget(self.task_table)  # 将任务表格添加到主布局
        layout.setStretch(2, 1)  # 设置索引为2的控件（任务表格）为可伸缩项，承担窗口高度的剩余空间

        # 创建底部分页容器控件，包含上一页、当前页/总页、下一页三个元素
        pagination_widget = QWidget(self)  # 创建分页容器控件，作为主窗口的子控件
        pagination_layout = QHBoxLayout(pagination_widget)  # 创建水平布局，用于排列分页元素
        pagination_layout.setContentsMargins(8, 0, 8, 0)  # 设置左右内边距保持美观，垂直内边距为0以紧凑显示
        pagination_layout.setSpacing(6)  # 设置元素间距为6像素，保持简洁

        prev_btn = QPushButton('<')  # 创建上一页按钮，文本为“<”
        prev_btn.setFixedSize(24, 24)  # 固定按钮大小为24x24，简洁不占空间
        prev_btn.setStyleSheet('border:none;')  # 按钮样式移除边框，保持轻量感
        prev_btn.clicked.connect(self.on_prev_page)  # 绑定点击事件，触发上一页逻辑

        page_label = QLabel('1/1')  # 创建页码标签，初始显示为“1/1”
        page_label.setAlignment(Qt.AlignmentFlag.AlignCenter)  # 文本居中对齐，便于阅读
        page_label.setStyleSheet('font-size:12px;color:#333;')  # 设置文本样式为12px、深色，简洁易读

        next_btn = QPushButton('>')  # 创建下一页按钮，文本为“>”
        next_btn.setFixedSize(24, 24)  # 固定按钮大小为24x24，简洁不占空间
        next_btn.setStyleSheet('border:none;')  # 按钮样式移除边框，保持轻量感
        next_btn.clicked.connect(self.on_next_page)  # 绑定点击事件，触发下一页逻辑

        pagination_layout.addWidget(prev_btn)  # 将上一页按钮加入布局
        pagination_layout.addWidget(page_label)  # 将页码标签加入布局
        pagination_layout.addWidget(next_btn)  # 将下一页按钮加入布局

        pagination_widget.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)  # 分页容器垂直固定高度
        pagination_widget.setFixedHeight(26)  # 固定分页容器高度为26像素，避免拖拽时被拉伸

        self.pagination_widget = pagination_widget  # 记录分页容器控件引用，便于后续显示隐藏与高度计算
        self.page_label = page_label  # 记录页码标签控件引用，便于动态更新文本
        self.prev_btn = prev_btn  # 记录上一页按钮引用，便于根据边界禁用或启用
        self.next_btn = next_btn  # 记录下一页按钮引用，便于根据边界禁用或启用

        layout.addWidget(self.pagination_widget)  # 将分页容器添加到主布局中，位于表格下方

        # 创建一个背景widget来显示水印
        self.background_widget = QWidget(self)  # 创建背景展示控件（承载水印等），作为主窗口的子控件
        self.background_widget.setObjectName("backgroundWidget")
        self.background_widget.lower()  # 确保背景widget在最底层
        self.background_widget.setGeometry(0, 0, self.width(), self.height())

        # 记录需要在收缩时隐藏、展开时显示的内容控件集合（不含标题栏）
        self.content_widgets = [self.input_widget, self.task_table, self.background_widget, self.pagination_widget]  # 统一管理内容区可见性（包含分页栏）

        # 明确设置任务表格的尺寸策略为可扩展：水平与垂直均为 Expanding，使其充当主要的可伸缩区域
        self.task_table.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)  # 让表格承担窗口高度变化

        # 初始化悬浮图标窗口（用于收缩状态下显示可点击的图标）
        self.setup_dock_icon()  # 创建并配置悬浮图标窗口

        # 调整窗口大小以适应内容
        self.adjustSize()

        # 确保表格可以自适应窗口大小变化
        self.task_table.horizontalHeader().setStretchLastSection(True)
        self.task_table.verticalHeader().setStretchLastSection(False)

        # 在设置完表格后立即验证列宽
        self.verify_column_widths()

        # 计算并设置最大窗口高度（屏幕高度的约2/3），并在布局完成后调整高度
        screen = QApplication.primaryScreen()  # 获取主屏幕对象
        if screen is not None:  # 判断是否成功获取屏幕对象
            screen_height = screen.availableGeometry().height()  # 获取可用屏幕高度（排除任务栏）
        else:
            screen_height = 800  # 如果获取失败，设置一个合理的默认高度（800像素）
        self.max_window_height = int(screen_height * 2 / 3)  # 计算最大窗口高度为屏幕的2/3
        self.setMaximumHeight(self.max_window_height)  # 设置窗口最大高度，避免窗口过高影响体验
        QTimer.singleShot(0, self.adjust_window_height)  # 在布局完成后调整窗口高度与列表滚动

        # 同步标题栏高度（确保与title_bar的固定高度一致，防止样式调整后不匹配）
        self.title_bar_height = self.title_bar.height()  # 获取标题栏控件当前高度，用于顶部收缩时的高度控制

        # 初始化分页显示（根据当前任务数量计算总页数并更新标签与按钮状态）
        self.update_pagination_ui()  # 初始更新分页标签与按钮，确保首次显示正确

    def collapse_to_title(self):
        """将窗口收缩到仅显示标题栏的高度（实现顶端自动收缩）"""
        # 如果尚未保存正常几何信息，则在收缩前进行保存，便于恢复
        if self.normal_geometry is None:  # 仅在第一次收缩时记录，避免覆盖用户最新尺寸
            self.normal_geometry = self.geometry()  # 保存当前窗口的几何信息（位置与大小），用于恢复
        # 在收缩时隐藏除标题栏外的所有内容区域控件，随后隐藏主窗口本身，仅保留悬浮图标显示
        if hasattr(self, 'content_widgets'):  # 判断内容控件集合是否存在
            for w in self.content_widgets:  # 遍历需要隐藏的内容控件
                w.setVisible(False)  # 将内容控件设置为隐藏
        self.title_bar.setVisible(False)  # 收缩状态不显示标题栏，避免占据空间与误触
        self.hide()  # 隐藏主窗口，仅显示悬浮图标小窗口
        self.show_dock_icon()  # 显示悬浮图标（置顶、可点击），点击后再弹出主窗口
        # 标记当前处于顶部收缩状态，供事件逻辑判断使用
        self.is_docked_top = True  # 设置顶部收缩状态为真

    def expand_from_title(self):
        """从仅标题栏状态恢复到原始大小（悬停或拖动时展开）"""
        # 如果没有记录正常几何信息，提供一个合理的默认尺寸以避免异常
        if self.normal_geometry is None:  # 正常情况下会在收缩时记录，这里是兜底
            # 构造一个默认的几何（当前位置、当前宽度、最低合理高度），避免None导致无法恢复
            self.normal_geometry = QRect(self.x(), 0, max(self.width(), 420), max(self.height(), 350))  # 使用文件中初始尺寸作为参考
        # 恢复到保存的正常尺寸与位置，并显示主窗口（从悬浮图标点击后弹窗）
        self.move(self.normal_geometry.x(), 0)  # 展开时保持贴顶位置，呈现简洁的下拉展开
        self.resize(self.normal_geometry.width(), self.normal_geometry.height())  # 恢复宽高到收缩前的值
        self.show()  # 显示主窗口，使用户可见并操作
        self.raise_()  # 将主窗口置于最前，避免被其他窗口遮挡
        self.activateWindow()  # 激活主窗口，使其获得焦点
        self.hide_dock_icon()  # 隐藏悬浮图标窗口，避免与主窗口重叠或误触
        # 在展开时显示内容区域控件，恢复到正常布局与显示
        if hasattr(self, 'content_widgets'):  # 判断内容控件集合是否存在
            for w in self.content_widgets:  # 遍历需要显示的内容控件
                w.setVisible(True)  # 将内容控件设置为可见
        self.title_bar.setVisible(True)  # 展开后标题栏可见，保留窗口控制按钮
        # 保持顶部状态标记不变（悬停展开仍视为处于顶部收缩场景），仅在拖出顶部后再清除该状态
        # self.is_docked_top 不在此处修改，避免悬停展开后立即又收缩导致闪烁

    def setup_dock_icon(self):
        """创建并配置收缩状态下显示的悬浮图标窗口"""
        # 如果已创建过悬浮图标窗口，则无需重复创建
        if self.dock_icon is not None:  # 防止重复初始化
            return  # 已存在则直接返回
        # 创建一个无边框、置顶、小型的悬浮窗口，用于显示图标按钮
        self.dock_icon = QWidget(None, Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool | Qt.WindowType.WindowStaysOnTopHint)  # 悬浮图标顶层窗口
        self.dock_icon.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)  # 允许透明背景，视觉更简单
        self.dock_icon.setFixedSize(28, 28)  # 设置悬浮窗口的固定大小，尽量不占空间
        # 创建布局与按钮，用来承载可点击的图标（使用内置表情，避免额外资源）
        dock_layout = QHBoxLayout(self.dock_icon)  # 创建水平布局承载按钮
        dock_layout.setContentsMargins(0, 0, 0, 0)  # 移除内边距，图标贴边显示
        dock_layout.setSpacing(0)  # 移除间距，保证紧凑
        dock_btn = QPushButton('🦄')  # 使用独角兽表情作为图标按钮，易识别
        dock_btn.setFixedSize(28, 28)  # 设置按钮大小与窗口一致，便于点击
        dock_btn.setStyleSheet("border:none;font-size:18px;background-color:rgba(255,255,255,0.9);")  # 简洁样式，无边框，半透明白底
        dock_btn.clicked.connect(self.on_dock_icon_clicked)  # 绑定点击事件：点击后展开主窗口
        dock_layout.addWidget(dock_btn)  # 将按钮加入悬浮窗口布局
        self.dock_icon.hide()  # 初始隐藏，只有收缩时才显示

    def show_dock_icon(self):
        """显示悬浮图标窗口，并将其放置在屏幕顶端靠近主窗口的横坐标位置"""
        # 计算悬浮图标应显示的位置：尽量贴近主窗口的x位置，同时避免超出屏幕边界
        screen = QApplication.primaryScreen()  # 获取主屏幕对象
        screen_geom = screen.availableGeometry() if screen is not None else QRect(0, 0, 800, 600)  # 获取屏幕可用区域
        icon_w = self.dock_icon.width()  # 悬浮图标宽度
        # 计算x坐标：限制在屏幕内 [0, 屏幕宽-图标宽]
        target_x = max(0, min(self.x(), screen_geom.width() - icon_w))  # 贴近主窗口x，同时不越界
        target_y = 0  # y坐标设为屏幕顶端
        self.dock_icon.move(target_x, target_y)  # 移动悬浮图标到目标位置
        self.dock_icon.show()  # 显示悬浮图标窗口

    def hide_dock_icon(self):
        """隐藏悬浮图标窗口"""
        if self.dock_icon is not None and self.dock_icon.isVisible():  # 若悬浮图标存在且当前可见
            self.dock_icon.hide()  # 隐藏悬浮图标窗口

    def on_dock_icon_clicked(self):
        """悬浮图标点击事件：展开主窗口并清除顶部收缩状态"""
        self.expand_from_title()  # 执行展开逻辑，恢复主窗口显示与内容
        self.is_docked_top = False  # 清除顶部收缩状态，避免再次自动收缩

    def dock_check_and_collapse(self):
        """在拖动或释放后进行触顶判定，满足条件则自动收缩到标题栏"""
        # 获取当前窗口的顶部坐标（相对屏幕），用于判断是否已触达屏幕顶端
        top_y = self.frameGeometry().top()  # 读取窗口框架顶部的全局Y坐标
        # 当顶部坐标小于等于阈值时，认为已触顶，可执行收缩
        if top_y <= self.dock_threshold:  # 触顶条件：近似位于屏幕最上方
            self.collapse_to_title()  # 执行顶部收缩
        else:
            # 若未触顶且此前处于收缩状态，则取消收缩并恢复正常尺寸
            if self.is_docked_top:  # 仅在已收缩状态下进行恢复
                self.is_docked_top = False  # 清除顶部收缩状态标记
                self.expand_from_title()  # 恢复窗口到正常大小

    def initial_column_setup(self):
        """初始化列宽设置"""
        # 设置表格的固定总宽度
        content_width = self.width() - 5
        self.task_table.setFixedWidth(content_width)
        
        # 计算列宽
        fixed_width = 100 + 55 + 55  # 优先级列宽增加到100
        first_column_width = content_width - fixed_width - 10 # 减去10像素，防止表格内容溢出  
        
        # 设置列宽
        self.task_table.setColumnWidth(0, first_column_width)
        self.task_table.setColumnWidth(1, 100)  # 优先级列宽增加到100
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
            fixed_width = 100 + 55 + 55  # 优先级列宽增加到100
            first_column_width = content_width - fixed_width - 10 # 减去10像素，防止表格内容溢出  
            
            # 设置列宽
            self.task_table.setColumnWidth(0, first_column_width)
            self.task_table.setColumnWidth(1, 100)  # 优先级列宽增加到100
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
        deadline = self.deadline_edit.dateTime().toString('yyyy-MM-dd')
        
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
                        
                        # 处理旧版本优先级值
                        old_to_new = {
                            "紧急": "紧急重要",
                            "高": "重要不紧急",
                            "中": "紧急不重要",
                            "低": "不紧急不重要"
                        }
                        
                        # 检查并更新任务优先级
                        for task in self.tasks:
                            if 'priority' in task and task['priority'] not in self.priority_values:
                                old_priority = task['priority']
                                task['priority'] = old_to_new.get(old_priority, "不紧急不重要")
                                print(f"更新任务优先级: {old_priority} -> {task['priority']}")
                        
                        # 如果有优先级更新，保存任务数据
                        self.save_tasks()
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
        # 暂时断开 itemChanged 信号
        self.task_table.blockSignals(True)
        print("刷新表格显示-----信号已断开")
        
        # 分离已完成和未完成的任务（保持完成任务位于尾部）
        incomplete_tasks = [t for t in self.tasks if not t.get('completed', False)]  # 未完成任务列表
        completed_tasks = [t for t in self.tasks if t.get('completed', False)]  # 已完成任务列表

        # 在已完成任务组内，按照日期字符串进行降序排序（yyyy-MM-dd 字符串比较等同时间降序）
        try:
            completed_tasks.sort(  # 对完成任务排序
                key=lambda x: x.get('deadline', ''),  # 以日期字符串为键，避免 QDateTime 对象比较不一致
                reverse=True  # 固定为降序，确保最新日期在前
            )
        except Exception as e:
            print(f"完成任务排序失败: {e}")  # 打印错误但不中断流程
        
        # 更新排序后的任务到tasks集合
        self.tasks = incomplete_tasks + completed_tasks  # 合并任务列表，保持完成任务在末尾

        # 计算总页数（根据总任务数与每页数量，至少为1页）
        total_count = len(self.tasks)  # 获取任务总数
        self.total_pages = max(1, (total_count + self.page_size - 1) // self.page_size)  # 计算总页数

        # 若当前页超过范围，进行回退修正（例如删除到最后一页为空时回到最后一页有效页）
        if self.current_page > self.total_pages:  # 检查当前页是否越界
            self.current_page = self.total_pages  # 将当前页修正为最后一页
        if self.current_page < 1:  # 检查当前页是否小于1
            self.current_page = 1  # 将当前页修正为第一页

        # 计算当前页任务切片范围并得到展示列表
        start_index = (self.current_page - 1) * self.page_size  # 当前页起始索引
        end_index = start_index + self.page_size  # 当前页结束索引（不包含）
        display_tasks = self.tasks[start_index:end_index]  # 当前页要显示的任务列表

        # 清空表格
        self.task_table.setRowCount(0)  # 清空现有行
        
        # 添加当前页任务到表格
        for task in display_tasks:  # 遍历当前页的任务
            self._add_task_to_table(task)  # 将任务插入到表格中

        # 调整窗口高度
        self.adjust_window_height()

        # 更新分页标签与按钮启用状态，确保页码与按钮实时同步
        self.update_pagination_ui()  # 刷新分页显示元素

        # 重新连接 itemChanged 信号
        self.task_table.blockSignals(False)
        print("刷新表格显示-----信号已连接")

    def update_pagination_ui(self):
        """更新分页显示的标签与按钮状态"""  # 中文函数注释：用于刷新页码文本与按钮可用状态
        # 计算并显示“当前页/总页”的文本
        self.page_label.setText(f"{self.current_page}/{self.total_pages}")  # 设置标签文本为“当前页/总页”形式
        
        # 根据当前页边界调整按钮可用状态（第一页禁用上一页，最后一页禁用下一页）
        self.prev_btn.setEnabled(self.current_page > 1)  # 当当前页大于1时启用上一页按钮
        self.next_btn.setEnabled(self.current_page < self.total_pages)  # 当当前页小于总页数时启用下一页按钮

    def on_prev_page(self):
        """上一页按钮点击事件"""  # 中文函数注释：处理点击上一页逻辑
        if self.current_page > 1:  # 判断是否存在上一页
            self.current_page -= 1  # 当前页码减一，切换到上一页
            self.refresh_table()  # 刷新表格显示为上一页的数据

    def on_next_page(self):
        """下一页按钮点击事件"""  # 中文函数注释：处理点击下一页逻辑
        if self.current_page < self.total_pages:  # 判断是否存在下一页
            self.current_page += 1  # 当前页码加一，切换到下一页
            self.refresh_table()  # 刷新表格显示为下一页的数据

        # 更新分页标签与按钮状态（例如禁用在第一页的“<”按钮）
        self.update_pagination_ui()  # 刷新分页显示元素

    def on_header_clicked(self, logical_index):
        """处理表头点击事件"""
        if logical_index == 1:  # 优先级列
            self.sort_by_priority()
        elif logical_index == 2:  # 日期列
            self.sort_by_deadline()

    def sort_by_priority(self):
        """按优先级排序，且完成任务始终位于末尾并按日期降序"""  # 函数说明：优化完成任务的排序规则
        # 切换排序顺序
        self.sort_order['priority'] = (Qt.SortOrder.DescendingOrder 
            if self.sort_order['priority'] == Qt.SortOrder.AscendingOrder 
            else Qt.SortOrder.AscendingOrder)
        
        # 分别对未完成和已完成的任务进行排序
        incomplete_tasks = [t for t in self.tasks if not t.get('completed', False)]  # 未完成任务列表
        completed_tasks = [t for t in self.tasks if t.get('completed', False)]  # 已完成任务列表
        
        # 添加错误处理，确保优先级值存在于字典中
        def get_priority_value(task):
            priority = task['priority']
            # 如果是旧版本的优先级值，进行映射转换
            if priority not in self.priority_values:
                # 旧版本优先级映射到新版本
                old_to_new = {
                    "紧急": "紧急重要",
                    "高": "重要不紧急",
                    "中": "紧急不重要",
                    "低": "不紧急不重要"
                }
                priority = old_to_new.get(priority, "不紧急不重要")  # 默认映射到最低优先级
                # 更新任务的优先级
                task['priority'] = priority
            return self.priority_values.get(priority, 0)  # 如果仍然找不到，返回默认值0
        
        # 排序未完成的任务
        try:
            incomplete_tasks.sort(
                key=get_priority_value,
                reverse=(self.sort_order['priority'] == Qt.SortOrder.DescendingOrder)
            )
            
            # 已完成任务不按优先级排序，改为按日期字符串降序（最新在前）
            completed_tasks.sort(  # 对已完成任务排序
                key=lambda x: x.get('deadline', ''),  # 以日期字符串为键
                reverse=True  # 固定降序，确保最新日期靠前
            )
        except Exception as e:
            print(f"排序错误: {e}")
            # 发生错误时不改变任务顺序
        
        # 合并任务列表，已完成的任务始终在后面
        self.tasks = incomplete_tasks + completed_tasks
        
        # 保存更新后的任务数据
        self.save_tasks()
        
        # 更新表格显示
        self.refresh_table()
        
        # 更新表头显示
        arrow = '↓' if self.sort_order['priority'] == Qt.SortOrder.DescendingOrder else '↑'
        headers = ['待办事项', f'优先级 {arrow}', '日期 ↕', '完成']
        self.task_table.setHorizontalHeaderLabels(headers)

    def sort_by_deadline(self):
        """按截止日期排序；完成任务始终位于末尾并按日期降序"""  # 函数说明：优化完成任务排序规则
        # 切换排序顺序
        self.sort_order['deadline'] = (Qt.SortOrder.DescendingOrder 
            if self.sort_order['deadline'] == Qt.SortOrder.AscendingOrder 
            else Qt.SortOrder.AscendingOrder)
        
        # 分别对未完成和已完成的任务进行排序
        incomplete_tasks = [t for t in self.tasks if not t.get('completed', False)]  # 未完成任务列表
        completed_tasks = [t for t in self.tasks if t.get('completed', False)]  # 已完成任务列表
        
        # 排序未完成的任务
        incomplete_tasks.sort(
            key=lambda x: QDateTime.fromString(x['deadline'], 'yyyy-MM-dd'),
            reverse=(self.sort_order['deadline'] == Qt.SortOrder.DescendingOrder)
        )
        
        # 已完成任务固定按日期字符串降序（最新在前），不受表头排序箭头影响
        completed_tasks.sort(  # 对已完成任务排序
            key=lambda x: x.get('deadline', ''),  # 以日期字符串为键
            reverse=True  # 固定降序，确保最新日期靠前
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
                # 如果点击的是标题栏且当前为顶部收缩状态，则先展开，便于拖动窗口离开顶部
                if self.is_docked_top:  # 顶部收缩时点击标题栏
                    self.expand_from_title()  # 展开到正常高度，用户可直接拖动离开顶部
                self.dragging = True  # 标记正在拖动窗口
                self.offset = event.pos()  # 记录鼠标相对窗口的偏移量，用于计算新位置

    def mouseReleaseEvent(self, event):
        """鼠标释放事件"""
        self.dragging = False
        self.resizing = False
        self.resize_edge = None
        self.unsetCursor()
        # 在鼠标释放时进行一次触顶判定并处理顶部收缩（简单有效，避免拖动过程中闪烁）
        self.dock_check_and_collapse()  # 根据当前窗口位置决定是否收缩到标题栏

    def mouseMoveEvent(self, event):
        """鼠标移动事件"""
        if self.dragging:
            # 处理窗口拖动
            self.move(self.mapToGlobal(event.pos() - self.offset))  # 根据鼠标移动更新窗口位置
            # 在拖动过程中，如果已从顶部拉出较明显距离，则视为取消顶部收缩状态
            if self.is_docked_top and self.frameGeometry().top() > self.dock_threshold:  # 拖离顶部阈值
                self.is_docked_top = False  # 清除顶部收缩状态
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

    def enterEvent(self, event):
        """鼠标进入窗口事件（用于顶部收缩时的悬停展开）"""
        # 已改为通过点击悬浮图标来展开，此处不进行悬停展开，保持逻辑简洁稳定
        # 调用父类默认实现，保持事件链完整
        super().enterEvent(event)  # 继续执行父类逻辑

    def leaveEvent(self, event):
        """鼠标离开窗口事件（用于顶部收缩时的自动恢复仅标题栏）"""
        # 已改为点击展开/收缩，不在鼠标离开窗口时自动改变状态，避免误触
        # 调用父类默认实现，保持事件链完整
        super().leaveEvent(event)  # 继续执行父类逻辑

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


    def toggle_task_completion(self, task, state):
        """切换任务完成状态"""  # 中文注释：根据复选框状态更新任务完成与动画
        is_completed = state == Qt.CheckState.Checked.value  # 判断是否为“已选中”即完成
        
        # 在当前页的表格中查找该任务对应的行（通过隐藏的任务ID进行匹配）
        current_row = None  # 当前页中的行索引
        for row in range(self.task_table.rowCount()):  # 遍历当前页的每一行
            item0 = self.task_table.item(row, 0)  # 获取第0列的 QTableWidgetItem
            if item0 and item0.data(Qt.ItemDataRole.UserRole) == task.get('id'):  # 比对隐藏的任务ID
                current_row = row  # 找到匹配行
                break  # 结束循环
        
        if current_row is not None:  # 若找到对应行
            # 创建动画效果（传入任务对象，避免分页索引错误）
            self.animate_row_completion(current_row, is_completed, task)

    def animate_row_completion(self, row, is_completed, task):
        """行完成动画"""  # 中文注释：为指定行添加完成动画，并在动画结束后更新任务状态
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
        
        def animate_frame():  # 中文注释：按帧更新透明度与删除线效果
            nonlocal current_frame
            if current_frame <= frames:
                progress = current_frame / frames
                update_opacity(progress)
                current_frame += 1
            else:
                timer.stop()
                # 动画完成后更新任务状态（直接使用传入的任务对象）
                self.update_task_status(task, is_completed)
        
        timer = QTimer(self)
        timer.timeout.connect(animate_frame)
        timer.start(duration // frames)

    def update_task_status(self, task, is_completed):
        """更新任务状态并重新排序"""
        task['completed'] = is_completed
        self.save_tasks()
        
        # 准备新的任务顺序（完成任务固定在末尾且按日期降序）
        incomplete_tasks = [t for t in self.tasks if not t.get('completed', False)]  # 未完成任务列表
        completed_tasks = [t for t in self.tasks if t.get('completed', False)]  # 已完成任务列表
        try:
            completed_tasks.sort(  # 对已完成任务排序
                key=lambda x: x.get('deadline', ''),  # 使用日期字符串排序（yyyy-MM-dd），兼容性更好
                reverse=True  # 固定降序，确保最新日期靠前
            )
        except Exception as e:
            print(f"完成任务排序失败: {e}")  # 打印错误但不中断流程
        self.tasks = incomplete_tasks + completed_tasks  # 合并任务顺序，保持完成任务在后
        
        # 使用动画刷新表格
        self.animate_table_refresh()

    def animate_table_refresh(self):
        """表格刷新动画"""

        # 暂时断开 itemChanged 信号
        self.task_table.blockSignals(True)
        print("表格刷新动画-----信号已断开，开始刷新表格。")
        
        # 保存当前页任务列表，避免重复添加（按分页切片展示）
        start_index = (self.current_page - 1) * self.page_size  # 当前页起始索引
        end_index = start_index + self.page_size  # 当前页结束索引（不包含）
        current_tasks = self.tasks[start_index:end_index]  # 当前页任务列表
        
        # 清空表格
        self.task_table.setRowCount(0)
        
        # 添加当前页的所有任务
        for index, task in enumerate(current_tasks):  # 遍历当前页任务
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
                
                # 更操作列的widget透明
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

        # 重新连接 itemChanged 信号
        self.task_table.blockSignals(False)
        print("Item changed 信号已连接")

    def _add_task_to_table(self, task):
        """添加任务到表格"""
        current_row = self.task_table.rowCount()
        self.task_table.insertRow(current_row)
        
        # 待办事项
        task_text = task['text']
        if len(task_text) > 20:
            task_text = task_text[:20] + '...'
        task_item = QTableWidgetItem(task_text)  # 创建文本单元格
        task_item.setToolTip(task['text'])  # 设置完整文本为气泡提示
        task_item.setData(Qt.ItemDataRole.UserRole, task.get('id'))  # 在用户角色数据中存储任务ID（隐藏值，用于映射）
        
        # 如果任务已完成，添加删除线
        if task.get('completed', False):
            font = task_item.font()
            font.setStrikeOut(True)
            task_item.setFont(font)
            task_item.setForeground(QColor('#999999'))
        
        self.task_table.setItem(current_row, 0, task_item)
        
        # 处理旧版本优先级值
        old_to_new = {
            "紧急": "紧急重要",
            "高": "重要不紧急",
            "中": "紧急不重要",
            "低": "不紧急不重要"
        }
        
        # 检查并更新任务优先级
        if 'priority' in task and task['priority'] not in self.priority_values:
            old_priority = task['priority']
            task['priority'] = old_to_new.get(old_priority, "不紧急不重要")
            print(f"表格中更新任务优先级: {old_priority} -> {task['priority']}")
        
        # 优先级下拉框
        priority_combo = QComboBox()
        priority_combo.addItems(['紧急重要', '重要不紧急', '紧急不重要', '不紧急不重要'])
        try:
            priority_combo.setCurrentText(task['priority'])
        except Exception as e:
            print(f"设置优先级下拉框失败: {e}，使用默认值'不紧急不重要'")
            priority_combo.setCurrentText('不紧急不重要')
            task['priority'] = '不紧急不重要'
        
        priority_combo.setFixedSize(100, 24)  # 增加宽度从50到100
        
        # 获取当前优先级和完成状态
        current_priority = task['priority']
        is_completed = task.get('completed', False)
        
        # 基础样式
        base_style = """
            /* 主框架样式 */
            QComboBox {
                border: none;             /* 移除边框 */
                background: transparent;   /* 背景透明 */
                padding-left: 4px;        /* 左侧填充，文字不贴边 */
                %s                        /* 预留位置用于添加删除线样式 */
            }
            
            /* 下拉按钮样式 */
            QComboBox::drop-down {
                border: none;             /* 移除下拉按钮边框 */
                width: 20px;              /* 设置下拉按钮宽度 */
            }
            
            /* 下拉列表样式 */
            QComboBox QAbstractItemView {
                border: 1px solid #ffccd5;  /* 下拉框边框 */
                background: white;          /* 下拉框背景 */
                selection-background-color: #ffecef;  /* 选中项背景色 */
            }
            
            /* 下拉列表中不同优先级的颜色 */
            QComboBox QAbstractItemView::item[text="紧急重要"] {
                color: red;               /* 紧急级别显示红色 */
            }
            QComboBox QAbstractItemView::item[text="重要不紧急"] {
                color: orange;            /* 高级别显示橙色 */
            }
        """
        
        # 根据完成状态和优先级设置样式
        if is_completed:
            # 已完成任务：添加删除线，使用灰色
            style_extra = "color: #999999; text-decoration: line-through;"
        else:
            # 未完成任务：根据优先级设置颜色
            if current_priority == '紧急重要':
                style_extra = "color: #FF0000;"  # 更鲜艳的红色
            elif current_priority == '重要不紧急':
                style_extra = "color: orange;"
            else:
                style_extra = "color: black;"
        
        # 应用样式
        priority_combo.setStyleSheet(base_style % style_extra)
        
        # 如果任务已完成，禁用下拉框
        if is_completed:
            priority_combo.setEnabled(False)
        
        # 连接信号 - 使用activated信号代替currentTextChanged
        # activated信号只在用户明确选择选项时触发，而不会在鼠标滚轮滚动时触发
        priority_combo.activated.connect(
            lambda index, t=task: self.update_task_priority(t, priority_combo.itemText(index))
        )
        
        # 禁用鼠标滚轮事件
        priority_combo.wheelEvent = lambda event: event.ignore()
        
        # 添加到表格
        self.task_table.setCellWidget(current_row, 1, priority_combo)
        
        # 截止时间
        deadline = QDateTime.fromString(task['deadline'], 'yyyy-MM-dd')
        deadline_str = deadline.toString('MM-dd')
        
        # 创建日期选择按钮
        date_btn = QPushButton(deadline_str)
        date_btn.setFixedSize(50, 24)
        
        # 设置日期按钮样式
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
            # 检查是否过期
            if deadline.date() < QDate.currentDate():
                text_color = 'red'
            else:
                text_color = 'black'
                
            date_btn.setStyleSheet(f"""
                QPushButton {{
                    border: none;
                    background: transparent;
                    color: {text_color};
                }}
                QPushButton:hover {{
                    background-color: #ffecef;
                }}
            """)
            
            # 创建日历选择器
            def show_calendar():
                calendar = QCalendarWidget(self)
                calendar.setWindowFlags(Qt.WindowType.Popup)
                calendar.setGridVisible(True)
                
                # 设置日历样式
                calendar.setStyleSheet("""
                    QCalendarWidget {
                        background-color: white;
                        border: 1px solid #ffccd5;
                    }
                    QCalendarWidget QToolButton {
                        color: black;
                        background-color: transparent;
                        border: none;
                    }
                    QCalendarWidget QToolButton:hover {
                        background-color: #ffecef;
                    }
                    QCalendarWidget QMenu {
                        background-color: white;
                        border: 1px solid #ffccd5;
                    }
                    QCalendarWidget QSpinBox {
                        border: 1px solid #ffccd5;
                        border-radius: 2px;
                    }
                    QCalendarWidget QTableView {
                        selection-background-color: #ffecef;
                        selection-color: black;
                    }
                """)
                
                # 设置日历位置
                pos = date_btn.mapToGlobal(date_btn.rect().bottomLeft())
                calendar.move(pos)
                
                # 设置当前选中日期
                calendar.setSelectedDate(deadline.date())
                
                # 日期选择处理
                def date_selected(qdate):
                    new_deadline = qdate.toString('yyyy-MM-dd')
                    if task['deadline'] != new_deadline:
                        task['deadline'] = new_deadline
                        date_btn.setText(qdate.toString('MM-dd'))
                        self.save_tasks()
                        self.refresh_table()
                    calendar.close()
                
                calendar.clicked.connect(date_selected)
                calendar.show()
            
            date_btn.clicked.connect(show_calendar)
        
        # 添加到表格
        self.task_table.setCellWidget(current_row, 2, date_btn)
        
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
                image: url(:/resources/checked.png);  // 使用资源路径
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
        checkbox.stateChanged.connect(lambda state, t=task: self.toggle_task_completion(t, state))  # 仍旧传递任务对象（包含ID），行索引将在函数内通过ID匹配
        
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

    def update_task_priority(self, task, new_priority):
        """更新任务优先级"""
        if task['priority'] != new_priority:
            task['priority'] = new_priority
            self.save_tasks()
            self.refresh_table()
            print("任务优先级已更新并保存")

    def adjust_window_height(self):
        """调整窗口高度，使窗口最大高度约为屏幕高度的2/3；超过时列表区域滚动"""  # 为函数添加中文说明，明确功能
        # 动态读取实际UI元素高度，避免估值误差导致顶部操作栏被拉伸
        title_height = self.title_bar.height()  # 读取标题栏实际高度，保证计算精准
        input_height = self.input_widget.height()  # 读取输入区域实际高度，避免因估值偏差造成布局异常
        footer_height = self.pagination_widget.height() if hasattr(self, 'pagination_widget') and self.pagination_widget is not None else 0  # 读取分页栏高度（若存在）
        padding = 10          # 上下内边距，用于整体高度的缓冲

        # 表格头部高度与行信息
        header_height = self.task_table.horizontalHeader().height()  # 获取表格表头高度
        row_height = 24       # 单行高度，与插入行时保持一致
        row_count = self.task_table.rowCount()  # 当前表格行数（任务数量）

        # 计算列表内容区域高度（不含表头），若无行则至少一行高度以保持美观
        content_height = row_height if row_count == 0 else row_height * row_count  # 根据行数计算内容高度

        # 计算整窗理论高度（标题+输入+表头+内容+分页栏+内边距）
        total_height = (title_height + input_height + header_height + content_height + footer_height + padding * 2)  # 理论总高度

        # 若未事先初始化最大高度，则动态计算一次（兼容性兜底）
        if not hasattr(self, 'max_window_height'):  # 检查是否已有最大窗口高度属性
            screen = QApplication.primaryScreen()  # 获取主屏幕对象
            if screen is not None:  # 判断是否成功获取屏幕对象
                screen_height = screen.availableGeometry().height()  # 获取可用屏幕高度
            else:
                screen_height = 800  # 默认高度兜底
            self.max_window_height = int(screen_height * 2 / 3)  # 计算最大窗口高度为屏幕的2/3
            self.setMaximumHeight(self.max_window_height)  # 设置窗口最大高度

        # 打印调试信息，便于观察高度计算情况
        print(f"Height calculation: rows={row_count}, title={title_height}, input={input_height}, footer={footer_height}, header={header_height}, content={content_height}, padding={padding * 2}, total={total_height}, max={self.max_window_height}")  # 输出高度信息

        # 根据是否超过最大窗口高度进行处理（避免使用 setFixedHeight 以免突破最大高度约束）
        if total_height <= self.max_window_height:  # 未超过最大高度的情况
            target_height = total_height  # 目标窗口高度为理论总高度
            self.resize(self.width(), target_height)  # 使用 resize 调整窗口高度，遵循最大高度限制
            # 设置表格高度范围：最大为内容高度（含表头），最小为至少一行显示（含表头）
            self.task_table.setMaximumHeight(header_height + content_height)  # 表格最大高度为当前内容高度
            self.task_table.setMinimumHeight(header_height + row_height)  # 表格最小高度至少一行，避免过小
        else:  # 超过最大高度的情况
            self.resize(self.width(), self.max_window_height)  # 将窗口高度限制在最大高度
            available_table_height = self.max_window_height - (title_height + input_height + footer_height + padding * 2)  # 计算可用于表格显示的高度（动态）
            # 确保表格高度至少包含表头高度和一行内容，避免表头被遮挡
            available_table_height = max(available_table_height, header_height + row_height)  # 最小高度保护
            # 设置表格高度范围：最大为可用高度，最小为至少一行
            self.task_table.setMaximumHeight(available_table_height)  # 表格最大高度设为可用高度，超出部分滚动显示
            self.task_table.setMinimumHeight(header_height + row_height)  # 表格最小高度至少一行内容
            self.task_table.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)  # 按需显示滚动条，便于浏览更多任务

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

    def handle_item_double_click(self, item):
        """处理双击事件"""  # 中文注释：通过隐藏ID查找任务，避免分页造成的行索引错误
        print("=== 双击事件触发 ===")
        row = item.row()  # 当前页中的行索引
        column = item.column()  # 当前列索引
        item_id = item.data(Qt.ItemDataRole.UserRole)  # 读取隐藏的任务ID
        task = next((t for t in self.tasks if t.get('id') == item_id), None)  # 通过ID查找任务对象
        if task is None:  # 若未找到任务对象，打印并返回
            print("未找到匹配任务，可能是索引异常")
            return
        print(f"行: {row}, 列: {column}")
        print(f"当前任务: {task}")
        
        if column == 0:  # 待办事项列
            print("开始编辑待办事项")
            self.task_table.editItem(item)
            
        # elif column == 2:  # 日期列
        #     print("开始编辑日期")
        #     self.task_table.editItem(item)
        #     # 设置项为可编辑状态
        #     item.setFlags(item.flags() | Qt.ItemFlag.ItemIsEditable)
        #     # 设置编辑模式下的文本数据
        #     item.setData(Qt.ItemDataRole.EditRole, item.text())
        #     # 设置显示模式下的文本数据
        #     item.setData(Qt.ItemDataRole.DisplayRole, item.text())

    def handle_item_changed(self, item):
        """处理单元格内容改变"""  # 中文注释：通过隐藏ID查找任务，避免分页造成的行索引错误
        row = item.row()  # 当前页中的行索引
        column = item.column()  # 当前列索引
        item_id = item.data(Qt.ItemDataRole.UserRole)  # 读取隐藏的任务ID
        task = next((t for t in self.tasks if t.get('id') == item_id), None)  # 通过ID查找任务对象
        if task is None:  # 若未找到任务对象，打印并返回
            print("未找到匹配任务，可能是索引异常")
            return
        
        if column == 0:  # 待办事项列
            new_text = item.text().strip()
            if new_text:
                if task['text'] != new_text:
                    print(f"新的待办事项文本: {new_text}")
                    task['text'] = new_text
                    self.save_tasks()
                    self.refresh_table()
                    print("任务已保存  表格已刷新")
        
        # elif column == 2:  # 日期列
        #     new_text = item.text().strip()
        #     # Attempt to parse the input date in "M-D" format and auto-complete to "MM-DD"
        #     try:
        #         month, day = map(int, new_text.split('-'))
        #         if month < 10:
        #             month_str = f"0{month}"
        #         else:
        #             month_str = str(month)
        #         if day < 10:
        #             day_str = f"0{day}"
        #         else:
        #             day_str = str(day)
        #         new_text = f"{month_str}-{day_str}"
        #     except ValueError:
        #         print("日期格式异常，未保存")
        #         self.refresh_table()
        #         return

        #     if re.match(r'^(0[1-9]|1[0-2])-(0[1-9]|[12]\d|3[01])$', new_text):
        #         current_year = QDateTime.fromString(task['deadline'], 'yyyy-MM-dd').date().year()
        #         month, day = map(int, new_text.split('-'))
        #         new_date = QDate(current_year, month, day)
        #         if new_date.isValid():
        #             new_deadline = new_date.toString('yyyy-MM-dd')
        #             if task['deadline'] != new_deadline:    
        #                 print(f"新的日期文本: {new_text}")
        #                 task['deadline'] = new_deadline
        #                 self.save_tasks()
        #                 print("任务已保存")
        #                 self.refresh_table()
        #                 print("表格已刷新")
        #         else:
        #             print("无效的日期")
        #             self.refresh_table()
        #     else:
        #         print("日期格式不正确，未保存")
        #         self.refresh_table()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    widget = TodoWidget()
    widget.show()
    sys.exit(app.exec())
