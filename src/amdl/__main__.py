import sys
import os

# 确保能找到amdl模块
if 'amdl' not in sys.modules:
    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(current_dir)
    if parent_dir not in sys.path:
        sys.path.insert(0, parent_dir)

from amdl.launcher import main


if __name__ == "__main__":
    main()