import sys
import os
import ctypes
from PyQt6.QtGui import QIcon

# 确保项目根目录在 sys.path 中
# 这解决了在不同目录下运行脚本时可能出现的模块导入错误
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from PyQt6.QtWidgets import QApplication
from ui.main_window import TodoWidget

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

if __name__ == '__main__':
    # 设置 AppUserModelID，确保任务栏图标正确显示
    try:
        myappid = 'todolist.app.version.1.0' # 任意唯一的字符串
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
    except Exception:
        pass

    app = QApplication(sys.argv)
    
    # 设置应用程序图标
    icon_path = resource_path('todo.ico')
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))
        
    widget = TodoWidget()
    widget.show()
    sys.exit(app.exec())
