#!/usr/bin/env python
"""Debug launcher - 不需要管理员权限"""

import sys
import traceback

sys.path.insert(0, 'src')

print("=" * 60)
print("DEBUG LAUNCHER - 测试GUI")
print("=" * 60)

try:
    print("\n[1/5] 导入PyQt6...")
    from PyQt6.QtWidgets import QApplication
    from qfluentwidgets import Theme, setTheme
    print("✓ PyQt6导入成功")
    
    print("\n[2/5] 导入GUI模块...")
    from amdl.fluent_gui import FluentMainWindow
    print("✓ GUI模块导入成功")
    
    print("\n[3/5] 创建QApplication...")
    app = QApplication(sys.argv)
    print("✓ QApplication创建成功")
    
    print("\n[4/5] 初始化主窗口...")
    setTheme(Theme.AUTO)
    app.setApplicationName("AppleMusic Downloader")
    window = FluentMainWindow()
    print("✓ 主窗口初始化成功")
    
    print("\n[5/5] 显示窗口并启动事件循环...")
    window.show()
    print("✓ 窗口已显示，启动事件循环...")
    print("\n如果程序停在这里，说明GUI正常运行。关闭窗口即可退出。")
    print("=" * 60)
    
    sys.exit(app.exec())
    
except Exception as e:
    print(f"\n❌ 错误: {str(e)}")
    print("\n完整错误信息:")
    traceback.print_exc()
    print("\n按回车键退出...")
    input()
