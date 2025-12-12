import PyInstaller.__main__
import os
import sys

# 1. 获取脚本所在目录的绝对路径
script_dir = os.path.dirname(os.path.abspath(__file__))

# 2. 切换当前工作目录到脚本所在目录
# 这确保了后续的相对路径（如 'todo.ico', 'main.py'）都能正确解析
os.chdir(script_dir)

# 3. 将脚本所在目录添加到 sys.path
# 这确保了能够正确导入 core.config
if script_dir not in sys.path:
    sys.path.insert(0, script_dir)

from core.config import get_current_version

def build_exe():
    print(f"Working directory: {os.getcwd()}")
    
    # 确保图标文件存在
    icon_path = os.path.join(script_dir, 'todo.ico')
    if not os.path.exists(icon_path):
        print(f"Error: Icon file '{icon_path}' not found!")
        return

    try:
        version = get_current_version()
    except Exception as e:
        print(f"Error reading version: {e}")
        return
    
    print(f"Building version: {version}")
    
    # 构建绝对路径的参数，防止路径混淆
    main_script = os.path.join(script_dir, 'main.py')
    
    # PyInstaller参数
    args = [
        main_script,       # 主程序文件
        '--onefile',       # 打包成单个文件
        '--noconsole',     # 不显示控制台窗口
        f'--icon={icon_path}', # 使用图标
        f'--name=TodoListV{version}', # 可执行文件名称
        '--clean',         # 清理临时文件
        '--hidden-import', 'win32com.client',
        # 使用--add-data参数来添加数据文件到打包后的可执行文件中
        f'--add-data', f'{icon_path}{os.pathsep}.',  # 添加todo.ico图标文件
        f'--add-data', f'todo_data.json{os.pathsep}.',  # 添加todo_data.json数据文件
    ]
    
    # 执行打包
    try:
        PyInstaller.__main__.run(args)
        print("Build completed! Check the 'dist' folder for the executable.")
    except Exception as e:
        print(f"Build failed: {e}")

if __name__ == '__main__':
    build_exe()
