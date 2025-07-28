"""
进程管理器模块
"""

from typing import Any,Callable
import threading
import multiprocessing
from enum import Enum

class TaskStatus(Enum):
    READY = "ready"
    RUNNING = "running"
    STOPPED = "stopped"


class TaskPro(object):
    """
    任务进程管理类
    
    用于管理单个任务进程的生命周期，包括启动、停止、重启和状态监控等功能。
    支持优雅停止和强制终止两种停止方式。
    """
    
    def __init__(self):
        """
        初始化任务进程管理器
        
        创建必要的事件对象和监控线程，为任务管理做准备。
        """
        # 任务基本信息
        self._task = None                                    # 任务函数
        self._name = None                                    # 任务名称
        self._args = None                                    # 任务参数元组
        self._kwargs = None                                  # 任务关键字参数字典
        self._pid = None                                     # 进程ID
        self._status = None                                  # 任务状态
        
        # 进程控制事件
        self._stop_event = multiprocessing.Event()          # 停止信号事件
        self._start_success_event = multiprocessing.Event() # 启动成功确认事件
        self._process = None                                 # 进程对象

        # 任务监控机制
        self._update_event = multiprocessing.Event()        # 监控线程控制事件
        self._lock = threading.Lock()                       # 线程锁，保护共享资源访问
        self._update_worker = threading.Thread(target=self._update_job, daemon=True)  # 监控线程
        self._update_worker.start()                         # 启动监控线程

    def set(self, task: Callable, name: str, args: tuple = None, kwargs: dict = None) -> bool:
        """
        设置任务信息
        
        @param task: 要执行的任务函数
        @param name: 任务名称
        @param args: 任务参数元组
        @param kwargs: 任务关键字参数字典
        @return: 设置是否成功
        """
        # 检查是否已经设置过任务，避免重复设置
        if self._task is not None:
            return False
            
        # 设置任务基本信息
        self._task = task
        self._name = name
        self._args = args if args is not None else ()        # 确保args为元组
        self._kwargs = kwargs if kwargs is not None else {}  # 确保kwargs为字典
        self._status = TaskStatus.READY                      # 设置初始状态为就绪
        return True

    def start(self, timeout: float = 10.0) -> bool:
        """
        启动任务进程
        
        @param timeout: 等待启动成功确认的超时时间（秒），默认10秒
        @return: 启动是否成功
        """
        with self._lock:                                     # 获取线程锁，确保线程安全
            # 检查任务是否已设置
            if self._task is None:
                return False
            
            # 如果进程已经在运行，不重复启动
            if self._process is not None and self._process.is_alive():
                return False
                
            # 清除之前的事件状态
            self._stop_event.clear()
            self._start_success_event.clear()               # 清除启动成功事件
            
            # 准备传递给子进程的参数，处理可能的字段冲突
            process_kwargs = self._kwargs.copy()            # 复制原始kwargs
            process_kwargs['stop_event'] = self._stop_event # 传递停止事件（覆盖可能存在的同名字段）
            process_kwargs['start_success_event'] = self._start_success_event  # 传递启动成功事件（覆盖可能存在的同名字段）
            
            # 创建新的进程对象，将控制事件传递给任务函数
            self._process = multiprocessing.Process(
                target=self._task,
                args=self._args,
                kwargs=process_kwargs,                       # 使用处理后的kwargs
                daemon=True                                  # 设置为守护进程
            )
            
            # 启动进程
            self._process.start()
            
        # 等待进程启动成功确认（使用传入的超时时间）
        if self._start_success_event.wait(timeout=timeout):
            with self._lock:
                self._status = TaskStatus.RUNNING            # 启动成功，更新状态
            return True
        else:
            # 启动超时，终止进程
            with self._lock:
                if self._process and self._process.is_alive():
                    self._process.terminate()
                    self._process.join(timeout=2.0)
                self._process = None
                self._status = TaskStatus.STOPPED
            return False


    def stop(self) -> bool:
        """
        停止任务进程
        
        先尝试优雅停止，如果进程不响应则强制终止
        
        @return: 停止是否成功
        """
        with self._lock:                                     # 获取线程锁，确保线程安全
            # 检查进程是否存在
            if self._process is None:
                return False
            
            # 如果进程已经停止，直接返回成功
            if not self._process.is_alive():
                self._process = None
                self._status = TaskStatus.STOPPED
                return True
            
            # 设置停止事件，通知任务进程退出
            self._stop_event.set()
            
            # 先尝试优雅停止（等待5秒）
            self._process.join(timeout=5)
            
            # 如果进程仍在运行，强制终止
            if self._process and self._process.is_alive():
                self._process.terminate()                # 发送终止信号
                self._process.join(timeout=1)            # 等待进程完全退出
            
            # 清理进程对象并更新状态
            self._process = None
            self._status = TaskStatus.STOPPED
            return True

    def is_alive(self) -> bool:
        """
        检查任务进程是否还在运行
        
        @return: 进程是否存活
        """
        with self._lock:                                     # 获取线程锁，确保线程安全
            return self._process is not None and self._process.is_alive()

    def get_status(self) -> TaskStatus:
        """
        获取任务状态
        
        @return: 当前任务状态
        """
        with self._lock:                                     # 获取线程锁，确保线程安全
            return self._status

    def get_name(self) -> str:
        """
        获取任务名称
        
        @return: 任务名称
        """
        return self._name

    def get_pid(self) -> int:
        """
        获取进程ID
        
        @return: 进程ID，如果进程不存在返回None
        """
        with self._lock:                                     # 获取线程锁，确保线程安全
            if self._process and self._process.is_alive():
                return self._process.pid
            return None

    def restart(self) -> bool:
        """
        重启任务进程
        
        @return: 重启是否成功
        """
        # 检查任务是否已设置
        if self._task is None:
            return False
        
        # 先停止当前进程（如果正在运行）
        if self._process is not None and self._process.is_alive():
            self.stop()                              # 停止当前进程
        
        # 重新启动任务进程
        return self.start()

    def info(self) -> dict:
        """
        获取任务信息
        
        @return: 包含任务详细信息的字典
        """
        with self._lock:                                     # 获取线程锁，确保线程安全
            return {
                'name': self._name,
                'status': self._status.value if self._status else None,
                'pid': self._process.pid if self._process and self._process.is_alive() else None,
                'is_alive': self._process.is_alive() if self._process else False,
                'args': self._args,
                'kwargs': self._kwargs
            }

    def __del__(self):
        """
        析构函数，确保进程和线程正确清理
        
        在对象被销毁时自动调用，确保所有资源得到正确释放。
        """
        try:
            # 如果进程仍在运行，停止进程
            if hasattr(self, '_process') and self._process is not None and self._process.is_alive():
                self.stop()
            
            # 停止监控线程
            if hasattr(self, '_update_event'):
                self._update_event.set()                # 设置事件，通知监控线程退出
        except Exception:
            # 忽略析构时的异常，避免程序崩溃
            pass

    def _update_job(self) -> None:
        """
        监控任务状态的后台线程函数
        
        持续监控任务进程的状态变化，自动处理进程意外退出和结束信号。
        该方法在单独的线程中运行，直到收到停止信号。
        """
        while not self._update_event.is_set():
            try:
                with self._lock:                             # 获取线程锁，确保线程安全
                    if self._process is not None:
                        # 检查进程是否还在运行
                        if not self._process.is_alive():
                            if self._status == TaskStatus.RUNNING:
                                # 进程意外结束，更新状态
                                self._status = TaskStatus.STOPPED
                                self._process = None
                
                # 等待一段时间再进行下次检查（1秒间隔）
                self._update_event.wait(timeout=1.0)
                
            except Exception:
                 # 忽略监控过程中的异常，确保监控线程不会崩溃
                 continue


class TaskProMgr(object):
    """
    任务进程管理器类
    
    用于管理多个TaskPro实例，提供集中化的任务管理功能。
    支持任务的创建、启动、停止、重启、移除等操作，以及批量管理功能。
    使用线程锁确保多线程环境下的安全性。
    """
    
    def __init__(self):
        """
        初始化进程管理器
        
        创建任务字典和线程锁，为多任务管理做准备。
        """
        self._tasks = {}                                     # 任务字典，存储任务名称到TaskPro实例的映射
        self._lock = threading.Lock()                        # 线程锁，确保多线程安全
    
    def create_task(self, name: str, task: Callable, args: tuple = None, kwargs: dict = None) -> bool:
        """
        创建新任务
        
        @param name: 任务名称
        @param task: 任务函数
        @param args: 任务参数
        @param kwargs: 任务关键字参数
        @return: 创建是否成功
        """
        with self._lock:                                     # 获取线程锁，确保线程安全
            # 检查任务名称是否已存在
            if name in self._tasks:
                return False
            
            # 创建新的TaskPro实例
            task_pro = TaskPro()
            # 设置任务信息
            if task_pro.set(task, name, args, kwargs):
                self._tasks[name] = task_pro                 # 添加到任务字典
                return True
            return False
    
    def start_task(self, name: str, timeout: float = 10.0) -> bool:
        """
        启动指定任务
        
        @param name: 任务名称
        @param timeout: 等待启动成功确认的超时时间（秒），默认10秒
        @return: 启动是否成功
        """
        with self._lock:                                     # 获取线程锁
            if name in self._tasks:
                return self._tasks[name].start(timeout)      # 启动指定任务，传递超时参数
            return False                                     # 任务不存在
    
    def stop_task(self, name: str) -> bool:
        """
        停止指定任务
        
        @param name: 任务名称
        @return: 停止是否成功
        """
        with self._lock:                                     # 获取线程锁
            if name in self._tasks:
                return self._tasks[name].stop()              # 优雅停止指定任务
            return False                                     # 任务不存在
    

    
    def restart_task(self, name: str) -> bool:
        """
        重启指定任务
        
        @param name: 任务名称
        @return: 重启是否成功
        """
        with self._lock:                                     # 获取线程锁
            if name in self._tasks:
                return self._tasks[name].restart()           # 重启指定任务
            return False                                     # 任务不存在
    
    def remove_task(self, name: str) -> bool:
        """
        移除指定任务
        
        @param name: 任务名称
        @return: 移除是否成功
        """
        with self._lock:                                     # 获取线程锁
            if name in self._tasks:
                # 先停止任务进程
                self._tasks[name].stop()
                # 从任务字典中移除
                del self._tasks[name]
                return True
            return False                                     # 任务不存在
    
    def get_task_info(self, name: str) -> dict:
        """
        获取指定任务信息
        
        @param name: 任务名称
        @return: 任务信息字典
        """
        with self._lock:                                     # 获取线程锁
            if name in self._tasks:
                return self._tasks[name].info()              # 返回任务详细信息
            return None                                      # 任务不存在
    
    def list_tasks(self) -> list:
        """
        列出所有任务
        
        @return: 任务名称列表
        """
        with self._lock:                                     # 获取线程锁
            return list(self._tasks.keys())                  # 返回所有任务名称列表
    
    def get_all_tasks_info(self) -> dict:
        """
        获取所有任务信息
        
        @return: 包含所有任务信息的字典
        """
        with self._lock:                                     # 获取线程锁
            result = {}
            # 遍历所有任务，收集信息
            for name, task in self._tasks.items():
                result[name] = task.info()                   # 获取每个任务的详细信息
            return result
    
    def stop_all_tasks(self) -> bool:
        """
        停止所有任务
        
        @return: 操作是否成功
        """
        with self._lock:                                     # 获取线程锁
            success = True
            # 遍历所有任务，逐个停止
            for task in self._tasks.values():
                if not task.stop():                          # 优雅停止任务
                    success = False                          # 记录失败状态
            return success
    

    
    def __del__(self):
        """
        析构函数，确保所有任务正确清理
        
        在对象销毁时自动调用，确保所有管理的任务进程都被正确终止，
        防止僵尸进程的产生。
        """
        try:
            # 检查属性是否存在，避免在对象初始化失败时出错
            if hasattr(self, '_tasks'):
                # 停止所有任务，确保资源清理
                self.stop_all_tasks()
        except Exception:
            # 忽略清理过程中的异常，避免析构函数抛出异常
            pass