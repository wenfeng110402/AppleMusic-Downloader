#!/usr/bin/env python
"""应用启动器 - 处理管理员权限和GUI初始化"""

import sys
import os
import traceback
import ctypes

# 确保能找到amdl模块
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)


def is_admin() -> bool:
    """检查是否为管理员"""
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False


def main():
    """应用主入口"""
    
    # 检查管理员权限
    if not is_admin():
        print("检测到程序未以管理员身份运行，请求提升权限...")
        
        script_path = os.path.abspath(__file__)
        python_exe = sys.executable
        
        # 用PowerShell以管理员身份重启
        try:
            import subprocess
            cmd = f'powershell -Command "Start-Process \'{python_exe}\' -ArgumentList \'{script_path}\' -Verb RunAs"'
            subprocess.Popen(cmd, shell=True)
            print("✓ 已发送权限提升请求，请在UAC对话框中选择'是'")
            sys.exit(0)
        except Exception as e:
            print(f"权限提升失败: {e}")
            print("将尝试以当前权限运行程序...")
    
    # 启动GUI
    try:
        print("✓ 以管理员身份运行")
        print("✓ 启动GUI...")
        
        from PyQt6.QtWidgets import QApplication
        from qfluentwidgets import Theme, setTheme
        
        print("✓ 导入GUI模块...")
        from amdl.fluent_gui import FluentMainWindow
        
        print("✓ 创建应用程序...")
        app = QApplication(sys.argv)
        setTheme(Theme.AUTO)
        app.setApplicationName("AppleMusic Downloader")
        app.setApplicationVersion("3.1.0")
        
        print("✓ 创建主窗口...")
        window = FluentMainWindow()
        print("✓ 显示窗口...")
        window.show()
        
        print("✓ GUI已启动，进入事件循环")
        sys.exit(app.exec())
        
    except Exception as e:
        print(f"❌ 错误: {str(e)}")
        traceback.print_exc()
        print("\n按回车键退出...")
        input()
        sys.exit(1)


if __name__ == "__main__":
    main()
