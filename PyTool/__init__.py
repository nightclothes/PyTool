#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PyTool - 功能丰富的Python工具库

主要模块:
- core: 核心功能模块（进程管理、锁管理等）
- utils: 实用工具模块
- database: 数据库访问模块
- communication: 进程间通信模块
- logging: 日志系统模块
- config: 配置管理模块
- exceptions: 异常处理模块
"""

__version__ = "1.0.0"
__author__ = "PyTool Team"
__email__ = "pytool@example.com"
__description__ = "一个功能丰富的Python工具库"

# 导入主要模块
from .core import *
from .utils import *
from .database import *
from .communication import *
from .logging import *
from .config import *
from .exceptions import *

__all__ = [
    # 版本信息
    "__version__",
    "__author__",
    "__email__",
    "__description__",
    
    # 核心模块
    "TaskPro",
    "TaskProMgr",
    "KeyTLock",
    "KeyPLock",
    
    # 工具模块
    "find_pro",
    "start_exe",
    "terminate_exe",
    "ping",
    "timer",
    "now_date",
    "now_time",
    
    # 数据库模块
    "SqliteMgr",
    
    # 通信模块
    "Pair",
    
    # 日志模块
    "Logger",
    
    # 配置模块
    "Cfg",
    
    # 异常处理模块
    "Dumper",
]


