import json
import os
from PyQt6.QtCore import Qt, QDateTime
from .config import DATA_FILE, PRIORITY_VALUES

class TaskManager:
    def __init__(self, data_file=DATA_FILE):
        self.data_file = data_file
        self.tasks = []
        self.pomodoro_stats = {}
        # Sort order state
        self.sort_order = {'priority': Qt.SortOrder.AscendingOrder, 'deadline': Qt.SortOrder.AscendingOrder}

    def load_tasks(self):
        """加载任务"""
        try:
            if os.path.exists(self.data_file):
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    content_str = f.read().strip()
                    if content_str:
                        content = json.loads(content_str)
                        
                        # 兼容性处理：判断是旧的列表格式还是新的字典格式
                        if isinstance(content, list):
                            self.tasks = content
                            self.pomodoro_stats = {}
                            print(f"检测到旧版数据格式，加载任务: {len(self.tasks)} 条")
                        elif isinstance(content, dict):
                            self.tasks = content.get('tasks', [])
                            self.pomodoro_stats = content.get('pomodoro_stats', {})
                            print(f"加载新版数据格式，任务: {len(self.tasks)} 条，番茄记录: {len(self.pomodoro_stats)} 天")
                        else:
                            self.tasks = []
                            self.pomodoro_stats = {}
                        
                        # 处理旧版本优先级值
                        old_to_new = {
                            "紧急": "紧急重要",
                            "高": "重要不紧急",
                            "中": "紧急不重要",
                            "低": "不紧急不重要"
                        }
                        
                        updated = False
                        for task in self.tasks:
                            if 'priority' in task and task['priority'] not in PRIORITY_VALUES:
                                old_priority = task['priority']
                                task['priority'] = old_to_new.get(old_priority, "不紧急不重要")
                                print(f"更新任务优先级: {old_priority} -> {task['priority']}")
                                updated = True
                        
                        if updated:
                            self.save_tasks()
                    else:
                        self.tasks = []
                        self.pomodoro_stats = {}
            else:
                self.tasks = []
                self.pomodoro_stats = {}
        except Exception as e:
            print(f"加载任务失败: {e}")
            self.tasks = []
            self.pomodoro_stats = {}
            # 创建新的数据文件
            self.save_tasks()
        return self.tasks

    def save_tasks(self):
        """保存任务到文件"""
        try:
            data = {
                "tasks": self.tasks,
                "pomodoro_stats": self.pomodoro_stats
            }
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print(f"成功保存数据: 任务 {len(self.tasks)} 条")
        except Exception as e:
            print(f"保存任务失败: {e}")

    def get_pomodoro_stats(self):
        return self.pomodoro_stats

    def update_pomodoro_stats(self, date_str, count):
        self.pomodoro_stats[date_str] = count
        self.save_tasks()

    def add_task(self, task):
        self.tasks.append(task)
        self.save_tasks()

    def delete_task(self, task):
        if task in self.tasks:
            self.tasks.remove(task)
            self.save_tasks()

    def get_tasks_for_display(self):
        """获取用于显示的任务列表（处理排序和完成状态）"""
        incomplete_tasks = [t for t in self.tasks if not t.get('completed', False)]
        completed_tasks = [t for t in self.tasks if t.get('completed', False)]

        # 完成任务始终按日期降序
        try:
            completed_tasks.sort(
                key=lambda x: x.get('deadline', ''),
                reverse=True
            )
        except Exception as e:
            print(f"完成任务排序失败: {e}")

        # 未完成任务按列表顺序（已在sort_by_*中处理）
        return incomplete_tasks + completed_tasks

    def sort_by_priority(self):
        """按优先级排序"""
        # 切换排序顺序
        self.sort_order['priority'] = (Qt.SortOrder.DescendingOrder 
            if self.sort_order['priority'] == Qt.SortOrder.AscendingOrder 
            else Qt.SortOrder.AscendingOrder)
        
        incomplete_tasks = [t for t in self.tasks if not t.get('completed', False)]
        completed_tasks = [t for t in self.tasks if t.get('completed', False)]
        
        def get_priority_value(task):
            priority = task['priority']
            if priority not in PRIORITY_VALUES:
                # 再次检查映射（理论上load时已处理，但防万一）
                old_to_new = {
                    "紧急": "紧急重要",
                    "高": "重要不紧急",
                    "中": "紧急不重要",
                    "低": "不紧急不重要"
                }
                priority = old_to_new.get(priority, "不紧急不重要")
                task['priority'] = priority
            return PRIORITY_VALUES.get(priority, 0)
        
        try:
            incomplete_tasks.sort(
                key=get_priority_value,
                reverse=(self.sort_order['priority'] == Qt.SortOrder.DescendingOrder)
            )
        except Exception as e:
            print(f"排序错误: {e}")

        # 更新主列表顺序
        self.tasks = incomplete_tasks + completed_tasks
        self.save_tasks()
        return self.sort_order['priority']

    def sort_by_deadline(self):
        """按截止日期排序"""
        self.sort_order['deadline'] = (Qt.SortOrder.DescendingOrder 
            if self.sort_order['deadline'] == Qt.SortOrder.AscendingOrder 
            else Qt.SortOrder.AscendingOrder)
        
        incomplete_tasks = [t for t in self.tasks if not t.get('completed', False)]
        completed_tasks = [t for t in self.tasks if t.get('completed', False)]
        
        incomplete_tasks.sort(
            key=lambda x: QDateTime.fromString(x['deadline'], 'yyyy-MM-dd'),
            reverse=(self.sort_order['deadline'] == Qt.SortOrder.DescendingOrder)
        )
        
        self.tasks = incomplete_tasks + completed_tasks
        self.save_tasks()
        return self.sort_order['deadline']

    def update_tasks_list(self, new_tasks):
        """更新任务列表（通常用于重新排序后的同步）"""
        self.tasks = new_tasks
        self.save_tasks()
