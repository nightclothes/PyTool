"""
进程锁
"""

import multiprocessing
from collections import OrderedDict

class KeyPLock:
    """
    进程锁管理器类，用于管理基于虚拟地址的进程锁
    使用filelock实现跨进程文件锁
    """
    def __init__(self, lock_dir="./pylocks"):
        """
        初始化进程锁管理器
        
        @param lock_dir: 文件锁存储目录，默认为./pylocks
        """
        import os
        from filelock import FileLock
        
        # 创建锁目录(如果不存在)
        os.makedirs(lock_dir, exist_ok=True)
        self.lock_dir = lock_dir
        
        # 用于保护_cache操作的进程互斥锁
        self._lock = multiprocessing.Lock()
        # 使用有序字典存储锁对象，key为虚拟地址
        self._cache = OrderedDict()

    def __del__(self):
        """
        析构函数，自动清理所有锁资源
        """
        self._clear()

    def _add(self, key):
        """
        为指定key添加一个新的文件锁
        
        @param key: 虚拟地址作为唯一标识
        """
        from filelock import FileLock
        with self._lock:
            if key not in self._cache:
                lock_file = f"{self.lock_dir}/{key}.lock"
                self._cache[key] = FileLock(lock_file)

    def _del(self, key):
        """
        删除指定key的文件锁
        
        @param key: 要删除的虚拟地址
        """
        with self._lock:
            self._cache.pop(key, None)

    def _clear(self):
        """
        清空所有已缓存的文件锁
        """
        with self._lock:
            self._cache.clear()

    class _LockContext:
        """
        内部文件锁上下文管理器类
        """
        def __init__(self, lock):
            self._lock = lock
        def __enter__(self):
            self._lock.acquire()
            print(f"进程 {multiprocessing.current_process().name} 获取锁")
            return self
        def __exit__(self, exc_type, exc_val, exc_tb):
            self._lock.release()
            print(f"进程 {multiprocessing.current_process().name} 释放锁")

    def lock(self, key):
        """
        获取指定key的文件锁对象上下文管理器
        
        @param key: 虚拟地址作为唯一标识
        @return: 文件锁对象的上下文管理器，可用于with语句
        """
        self._add(key)
        return self._LockContext(self._cache[key])
import time
import multiprocessing


def worker(key, value, plock, shared_data):
    """
    工作进程函数，演示如何使用KeyPLock对共享资源加锁
    @param key: 锁的虚拟地址
    @param value: 要添加到共享数据的值
    @param plock: KeyPLock实例
    @param shared_data: 共享数据列表
    """
    with plock.lock(key):
        # 临界区开始
        shared_data.append(value)
        print(f"进程 {multiprocessing.current_process().name} 添加了 {value}")
        time.sleep(0.1)
        # 临界区结束

if __name__ == "__main__":
    """
    KeyPLock 使用示例：多进程环境下对同一资源加锁
    """
    plock = KeyPLock()
    manager = multiprocessing.Manager()
    shared_data = manager.list()
    processes = []
    for i in range(10):
        p = multiprocessing.Process(target=worker, args=("resource1", i, plock, shared_data), name=f"P{i}")
        processes.append(p)
        p.start()

    for p in processes:
        p.join()

    print("最终共享数据:", list(shared_data))


