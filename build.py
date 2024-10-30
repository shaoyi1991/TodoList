import PyInstaller.__main__
import os

def build_exe():
    # 确保图标文件存在
    if not os.path.exists('todo.ico'):
        print("Error: Icon file 'todo.ico' not found!")
        return
    
    # PyInstaller参数
    args = [
        'todo_widget.py',  # 主程序文件
        '--onefile',       # 打包成单个文件
        '--noconsole',     # 不显示控制台窗口
        '--icon=todo.ico', # 使用图标
        '--name=TodoList', # 可执行文件名称
        '--clean',         # 清理临时文件
        '--hidden-import', 'win32com.client',  # 添加这行
        # 添加数据文件
        '--add-data', f'todo.ico{os.pathsep}.',
        '--add-data', f'todo_data.json{os.pathsep}.',
    ]
    
    # 执行打包
    PyInstaller.__main__.run(args)
    print("Build completed! Check the 'dist' folder for the executable.")

if __name__ == '__main__':
    build_exe() 