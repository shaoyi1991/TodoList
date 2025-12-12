import json
import os
from datetime import datetime, date
from PyQt6.QtCore import QObject, QTimer, pyqtSignal

class PomodoroManager(QObject):
    # Signals
    timer_updated = pyqtSignal(str) # "25:00"
    state_changed = pyqtSignal(bool) # True=Running, False=Stopped
    pomodoro_completed = pyqtSignal(int) # Today's count

    def __init__(self, task_manager):
        super().__init__()
        self.task_manager = task_manager
        
        self.WORK_TIME = 25 * 60 # 25 minutes
        self.remaining_time = self.WORK_TIME
        self.is_running = False
        
        self.timer = QTimer()
        self.timer.timeout.connect(self.on_tick)
        self.timer.setInterval(1000) # 1 second

    def get_today_count(self):
        today = date.today().isoformat()
        stats = self.task_manager.get_pomodoro_stats()
        return stats.get(today, 0)

    def get_history(self, days=7):
        """Return last N days of history sorted by date descending"""
        stats = self.task_manager.get_pomodoro_stats()
        
        # Helper to parse date string for sorting
        def parse_date(date_str):
            try:
                parts = date_str.split('-')
                return date(int(parts[0]), int(parts[1]), int(parts[2]))
            except:
                return date.min

        # Sort descending by actual date object
        sorted_dates = sorted(stats.keys(), key=parse_date, reverse=True)
        
        if not sorted_dates:
            return []
            
        # Get top N newest dates
        relevant_dates = sorted_dates[:days]
        
        return [(d, stats[d]) for d in relevant_dates]

    def start_timer(self):
        if not self.is_running:
            self.is_running = True
            self.timer.start()
            self.state_changed.emit(True)

    def pause_timer(self):
        if self.is_running:
            self.is_running = False
            self.timer.stop()
            self.state_changed.emit(False)

    def reset_timer(self):
        self.pause_timer()
        self.remaining_time = self.WORK_TIME
        self.update_display()

    def on_tick(self):
        self.remaining_time -= 1
        if self.remaining_time <= 0:
            self.complete_session()
        else:
            self.update_display()

    def update_display(self):
        minutes = self.remaining_time // 60
        seconds = self.remaining_time % 60
        self.timer_updated.emit(f"{minutes:02d}:{seconds:02d}")

    def complete_session(self):
        self.reset_timer()
        
        today = date.today().isoformat()
        current_count = self.get_today_count()
        new_count = current_count + 1
        self.task_manager.update_pomodoro_stats(today, new_count)
        
        self.pomodoro_completed.emit(new_count)
