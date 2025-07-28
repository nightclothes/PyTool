"""
dump
"""
import datetime
import os
import sys

import pydumpling
from logger import Logger


class Dumper:
    """
    进程转储工具类，用于在程序崩溃时自动生成进程转储文件
    基于pydumpling库实现，支持Windows和Linux系统
    """

    def __init__(self, app_name: str = "app", dump_dir: str = None):
        """
        初始化进程转储工具

        @param app_name: 应用程序名称，用于生成dump文件名前缀
        @param dump_dir: 转储文件保存目录，如果为None则使用当前目录下的dumps文件夹
        """
        self.__app_name = app_name
        self.__dump_dir = dump_dir or os.path.join(os.path.dirname(os.path.abspath(__file__)), "dumps")
        self.__original_excepthook = sys.excepthook

        # 确保dump目录存在
        if not os.path.exists(self.__dump_dir):
            os.makedirs(self.__dump_dir)

    def _exception_handler(self, exc_type, exc_value, exc_traceback) -> None:
        """
        异常处理函数

        @param exc_type: 异常类型
        @param exc_value: 异常值
        @param exc_traceback: 异常回溯
        """
        try:
            # 生成dump文件
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            dump_file = os.path.join(self.__dump_dir, f"{self.__app_name}_{timestamp}.dump")
            pydumpling.save_dumping(filename=dump_file, exc_info=(exc_type, exc_value, exc_traceback))

            # 记录异常信息到日志
            logger = Logger.get_logger("ProcessDumper")
            logger.critical(f"程序发生未捕获的异常，已生成转储文件：{dump_file}")
            logger.critical(f"异常类型：{exc_type.__name__}")
            logger.critical(f"异常信息：{str(exc_value)}")

        except Exception as e:
            logger = Logger.get_logger("ProcessDumper")
            logger.error(f"生成转储文件失败：{str(e)}")

        # 调用原始的异常处理器
        if self.__original_excepthook and self.__original_excepthook != self._exception_handler:
            self.__original_excepthook(exc_type, exc_value, exc_traceback)

    def _install(self) -> None:
        """
        安装进程转储处理器
        """
        # 设置异常处理器
        sys.excepthook = self._exception_handler

    @classmethod
    def setup(cls, app_name: str = "app", dump_dir: str = None) -> 'Dumper':
        """
        快速设置进程转储处理器

        @param app_name: 应用程序名称
        @param dump_dir: 转储文件保存目录
        @return: ProcessDumper实例
        """
        dumper = cls(app_name=app_name, dump_dir=dump_dir)
        dumper._install()
        return dumper

    @staticmethod
    def load(dump_file: str) -> None:
        """
        加载dump文件并启动pdb调试

        @param dump_file: dump文件路径
        """
        return pydumpling.debug_dumpling(dump_file=dump_file)
