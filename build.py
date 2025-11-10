import PyInstaller.__main__
import os
import json

CONFIG_DATA = '''
{
    "current_version": "1.3.251110",
    "versions": [
    {
        "version": "1.3.251110",
        "description": "1、数据列表支持滚动；2、已完成事项按日期降序排序；3、增加分页功能；4、支持缩小到屏幕顶部。"
      },
     {
        "version": "1.3.250721",
        "description": "兼容历史优先级数据，避免点击优先级闪退；取消鼠标滑动时会修改优先级"
      },
      {
        "version": "1.3.250718",
        "description": "修改优先级为四象限原则"
      },
      {
        "version": "1.2.141119",
        "description": "1、优先级编辑支持下来选择；2、日期编辑支持日历选择。"
      },
      {
        "version": "1.0.141119",
        "description": "1、支持表格内容编辑,双击修改(为了界面简洁，仅支持文本输入)。2、增加版本号显示及历史版本更新记录"
      },
      {
        "version": "1.0.0",
        "description": "Beta release with limited features."
      }
    ]
}
'''

def get_current_version():
    config = json.loads(CONFIG_DATA)
    return config['current_version']

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
        '--name=TodoListV{}'.format(get_current_version()), # 可执行文件名称
        '--clean',         # 清理临时文件
        '--hidden-import', 'win32com.client',  # 添加这行
        # 使用--add-data参数来添加数据文件到打包后的可执行文件中
        '--add-data', f'todo.ico{os.pathsep}.',  # 添加todo.ico图标文件
        '--add-data', f'todo_data.json{os.pathsep}.',  # 添加todo_data.json数据文件
        #'--add-data', f'version_config.json{os.pathsep}.',  # 添加version_config.json配置文件
    ]
    
    # 执行打包
    PyInstaller.__main__.run(args)
    print("Build completed! Check the 'dist' folder for the executable.")

if __name__ == '__main__':
    build_exe() 


