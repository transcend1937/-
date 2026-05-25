import sys
import os

# 将 src 目录加入导入路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from exam.app import app