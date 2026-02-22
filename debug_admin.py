#!/usr/bin/env python
"""Debug权限检查"""

import sys
import os

print("="*60)
print("DEBUG 管理员权限检查")
print("="*60)

try:
    import ctypes
    is_admin = bool(ctypes.windll.shell32.IsUserAnAdmin())
    print(f"\n当前是否为管理员: {is_admin}")
    
    if is_admin:
        print("\n✓ 已是管理员，可以启动GUI")
        print("\n[继续启动GUI...]")
        sys.path.insert(0, 'src')
        from PyQt6.QtWidgets import QApplication
        from qfluentwidgets import Theme, setTheme
        from amdl.fluent_gui import FluentMainWindow
        
        app = QApplication(sys.argv)
        setTheme(Theme.AUTO)
        window = FluentMainWindow()
        window.show()
        print("✓ GUI已显示")
        sys.exit(app.exec())
    else:
        print("\n❌ 不是管理员，需要请求权限...")
        print("\n这里应该弹出UAC对话框")
        print("如果没有看到对话框，说明权限请求代码有问题")
        
        import subprocess
        script_path = os.path.abspath(__file__)
        print(f"\n脚本路径: {script_path}")
        print(f"Python路径: {sys.executable}")
        
        print("\n尝试用PowerShell以管理员身份重启...")
        cmd = f'powershell -Command "Start-Process \'{sys.executable}\' -ArgumentList \'{script_path}\' -Verb RunAs"'
        print(f"命令: {cmd}")
        subprocess.Popen(cmd, shell=True)
        print("\n✓ 已发送重启请求，如果授予权限，新窗口应该显示GUI")
        print("（原窗口会退出）")
        
except Exception as e:
    import traceback
    print(f"\n❌ 错误: {e}")
    traceback.print_exc()

print("\n按回车键退出...")
input()
