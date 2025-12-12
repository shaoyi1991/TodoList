import json
import os

CONFIG_DATA = '''
{
    "current_version": "1.4.251212",
    "versions": [
    {
        "version": "1.4.251212",
        "description": "1、增加番茄钟提醒功能；2、代码解耦优化"
      },
    {
        "version": "1.3.251113",
        "description": "1、双击标题栏隐藏窗口；2、列宽支持调整；3、窗口宽度支持更小。"
      },
    {
        "version": "1.3.251112",
        "description": "1、高度、宽度不再限制；2、字体根据窗口大小自适应"
      },
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

# Constants
DATA_FILE = 'todo_data.json'
PRIORITY_VALUES = {'不紧急不重要': 0, '紧急不重要': 1, '重要不紧急': 2, '紧急重要': 3}
