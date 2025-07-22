"""
线程锁
"""
import threading
from collections import OrderedDict

class KeyTLock:
    """
    线程锁管理器类，用于管理基于虚拟地址的线程锁
    在对象销毁时会自动清理所有锁资源
    """
    
    def __init__(self):
        """
        初始化线程锁管理器
        """
        # 用于保护_cache操作的互斥锁
        self._lock = threading.Lock()
        # 使用有序字典存储锁对象，key为虚拟地址
        self._cache = OrderedDict()

    def __del__(self):
        """
        析构函数，自动清理所有锁资源
        """
        self._clear()

    def _add(self, key):
        """
        为指定key添加一个新的线程锁
        
        @param key: 唯一标识
        """
        with self._lock:
            if key not in self._cache:
                self._cache[key] = threading.Lock()

    def _del(self, key):
        """
        删除指定key的线程锁
        
        @param key: 要删除的标识
        """
        with self._lock:
            self._cache.pop(key, None)

    def _clear(self):
        """
        清空所有已缓存的线程锁
        """
        with self._lock:
            self._cache.clear()

    class _LockContext:
        """
        内部锁上下文管理器类
        """
        def __init__(self, lock):
            self._lock = lock
        def __enter__(self):
            self._lock.acquire()
            return self
        def __exit__(self, exc_type, exc_val, exc_tb):
            self._lock.release()

    def lock(self, key):
        """
        获取指定key的锁对象上下文管理器
        
        @param key: 唯一标识
        @return: 锁对象的上下文管理器，可用于with语句
        """
        self._add(key)
        return self._LockContext(self._cache[key])





if __name__ == "__main__":
    """
    TLock 使用示例：多线程环境下对同一资源加锁
    """
    import time
    import threading

    tlock = KeyTLock()
    shared_data = []

    def worker(key, value):
        """
        工作线程函数，演示如何使用TLock对共享资源加锁
        @param key: 锁的虚拟地址
        @param value: 要添加到共享数据的值
        """
        with tlock.lock(key):
            # 临界区开始
            shared_data.append(value)
            print(f"线程 {threading.current_thread().name} 添加了 {value}")
            time.sleep(0.1)
            # 临界区结束

    threads = []
    for i in range(10):
        t = threading.Thread(target=worker, args=("resource1", i), name=f"T{i}")
        threads.append(t)
        t.start()

    for t in threads:
        t.join()

    print("最终共享数据:", shared_data)




