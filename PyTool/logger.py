"""
日志系统
"""
import datetime
import logging
import os


class Logger:
    """
    日志管理器类
    """
    __logger_store = {}

    @classmethod
    def get_logger(
            cls,
            logger_name: str,
    ) -> logging.Logger:
        """
        获取或创建一个logger实例
        """
        # 如果logger已存在，直接返回缓存的实例
        if logger_name in cls.__logger_store:
            return cls.__logger_store[logger_name]

        # 创建日志目录结构：./日志/年-月-日/logger_name.log
        today: str = datetime.datetime.now().strftime("%Y-%m-%d")
        father_dir: str = cls.__get_father_directory()
        father_dir += r"\{}\{}".format("日志", today)
        cls.__create_directory(father_dir)
        logger_path = father_dir + r"\{}.log".format(logger_name)

        # 配置文件日志处理器
        file_handler = logging.FileHandler(
            filename=logger_path,
            mode="a",  # 追加模式
            encoding="utf-8",
            delay=False,
            errors=None
        )
        file_handler.setLevel(logging.DEBUG)

        # 配置控制台日志处理器
        stream_handler = logging.StreamHandler()
        stream_handler.setLevel(logging.DEBUG)

        # 配置日志格式
        file_formatter = logging.Formatter(
            fmt='[%(asctime)s]'  # 时间
                '[%(filename)s]'  # 文件名
                '[%(process)d]'  # 进程ID
                '[%(thread)d]'  # 线程ID
                '[%(name)s]'  # 日志名
                '[%(funcName)s]'  # 函数名
                '[%(lineno)d]'  # 行号
                '[%(levelname)s]'  # 日志级别
                '%(message)s',  # 日志信息
            datefmt='%Y-%m-%d %H:%M:%S'
        )

        # 应用格式化器
        file_handler.setFormatter(file_formatter)
        stream_handler.setFormatter(file_formatter)

        # 创建并配置logger
        new_logger = logging.getLogger(logger_name)
        new_logger.setLevel(logging.DEBUG)
        new_logger.addHandler(file_handler)
        new_logger.addHandler(stream_handler)

        # 缓存并返回logger实例
        cls.__logger_store[logger_name] = new_logger
        return new_logger

    @staticmethod
    def __get_father_directory(abspath: str | None = None) -> str:
        """
        获取指定路径的父目录

        @param abspath: 指定的绝对路径。如果为None，则返回当前文件的父目录
        @return: 父目录的绝对路径
        """
        if abspath is not None:
            return os.path.dirname(os.path.abspath(abspath))
        else:
            return os.path.dirname(os.path.abspath(__file__))

    @staticmethod
    def __create_directory(dir_path: str) -> None:
        """
        创建目录（如果不存在）

        @param dir_path: 要创建的目录路径
        """
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)
