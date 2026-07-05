from __future__ import annotations
import sys
import gamdl.cli

# 直接调用cli.main，将argv透传，保留amdl命令，行为与gamdl一致
def main():
    sys.argv = ["gamdl", *sys.argv[1:]]
    gamdl.cli.main() #type: ignore
# 真的就只有这么点
    