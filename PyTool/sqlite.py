"""
sqlite数据库访问模块
"""

import sqlite3
import threading
from filelock import FileLock
from pathlib import Path
from contextlib import contextmanager

class SqliteMgr:
    """
    SQLite数据库管理器类
    提供线程安全和进程安全的数据库操作
    使用双重锁机制保证并发安全：
    - 线程锁(__t_lock): 保证同一进程内多线程安全
    - 进程锁(__p_lock): 通过文件锁保证跨进程安全
    """
    
    def __init__(self, db_path: str, optimize: bool = True):
        """
        初始化SQLite数据库管理器
        
        参数:
            db_path: 数据库文件路径(相对或绝对路径)
            optimize: 是否启用数据库优化配置(默认True)
            
        属性:
            __t_lock: threading.Lock对象，用于线程同步
            __db_path: Path对象，数据库文件的绝对路径
            __p_lock: FileLock对象，用于进程间同步
        """
        self.__t_lock = threading.Lock()  # 线程锁 - 用于同一进程内的线程同步
        self.__db_path = str(Path(db_path).absolute())  # 转换为绝对路径
        self.__p_lock = FileLock(f"{self.__db_path}.lock")  # 进程锁 - 使用文件锁实现跨进程同步

        # 数据库优化配置
        if optimize:
            self._optimize()

    def _get_con(self):
        """
        获取数据库连接
        """
        return sqlite3.connect(
            self.__db_path,
            check_same_thread=False,  # 不允许多线程使用同一个连接
            isolation_level="EXCLUSIVE",     # 每个sql语句事务独立
            timeout=30.0,            # 连接超时时间
            detect_types=sqlite3.PARSE_DECLTYPES  # 创建表时的类型
        )

    def _optimize(self):
        """
        数据库优化配置
        设置以下优化参数:
        - WAL日志模式: 提高并发性能
        - 同步模式: 设置为NORMAL以平衡性能和数据安全
        - 缓存大小: 增大缓存提高性能
        - 临时存储: 使用内存临时表提高速度
        - 页面大小: 设置为操作系统页大小的倍数
        - 自动清理: 启用自动清理WAL文件
        """
        with self.__p_lock, self.__t_lock:
            # 使用无事务隔离级别的连接进行优化设置
            conn = sqlite3.connect(str(self.__db_path), isolation_level=None)
            cursor = conn.cursor()
            # 设置WAL日志模式(提高并发性能)
            cursor.execute("PRAGMA journal_mode=WAL")
            # 设置同步模式为NORMAL(平衡性能和数据安全)
            cursor.execute("PRAGMA synchronous=NORMAL") 
            # 增大缓存大小(默认2000页)
            cursor.execute("PRAGMA cache_size=-10000")  
            # 使用内存临时表(提高临时表操作速度)
            cursor.execute("PRAGMA temp_store=MEMORY")
            # 设置页面大小为4096(操作系统页大小的倍数)
            cursor.execute("PRAGMA page_size=4096")
            # 启用自动清理WAL文件
            cursor.execute("PRAGMA wal_autocheckpoint=100")
            conn.close()

    def __del__(self):
        """
        析构函数
        确保在对象销毁时释放所有锁资源
        避免资源泄漏
        """
        try:
            if hasattr(self, '_SqliteMgr__p_lock') and self.__p_lock.is_locked:
                self.__p_lock.release()
        except Exception:
            pass  # 忽略析构时的异常
        


    @contextmanager
    def transaction(self):
        """
        上下文管理器，提供数据库事务支持
        
        使用方式:
        with db.transaction() as cursor:
            cursor.execute(...)
            
        特性:
        1. 自动获取线程锁和进程锁
        2. 自动提交事务(成功时)或回滚(失败时)
        3. 自动关闭数据库连接
        4. 异常会自动向上抛出
        """
        with self.__p_lock, self.__t_lock:
            conn = None
            try:
                conn = self._get_con()
                cursor = conn.cursor()
                yield cursor  # 将游标交给上下文使用
                conn.commit()  # 执行成功则提交事务
            except Exception as e:
                if conn:
                    conn.rollback()  # 执行失败则回滚事务
                raise e  # 重新抛出异常
            finally:
                if conn:
                    conn.close()

    def execute(self, sql: str):
        """
        执行SQL语句并返回结果
        
        参数:
            sql: 要执行的SQL语句
            
        返回:
            查询结果列表(对于查询语句)
            
        异常:
            执行失败会抛出原生的sqlite3异常
        """
        with self.__p_lock, self.__t_lock:
            conn = None
            try:
                conn = self._get_con()
                cursor = conn.cursor()
                cursor.execute(sql)
                conn.commit()
                return cursor.fetchall()  # 返回查询结果
            except Exception as e:
                if conn:
                    conn.rollback()
                raise e
            finally:
                if conn:
                    conn.close()



def thread_task(db_path, name_prefix, start_idx, count):
    """
    线程任务：批量插入数据
    @param db_path: 数据库文件路径
    @param name_prefix: 名字前缀
    @param start_idx: 起始编号
    @param count: 插入数量
    """
    db = SqliteMgr(db_path)
    for i in range(count):
        sql = f"INSERT INTO user (name, age) VALUES ('{name_prefix}_{start_idx + i}', {20 + i % 10})"
        db.execute(sql)

def process_task(db_path, proc_idx, thread_num, insert_per_thread):
    """
    进程任务：启动多个线程并发插入
    @param db_path: 数据库文件路径
    @param proc_idx: 进程编号
    @param thread_num: 线程数
    @param insert_per_thread: 每线程插入数量
    """
    threads = []
    for t in range(thread_num):
        th = threading.Thread(target=thread_task, args=(db_path, f"P{proc_idx}T{t}", t * insert_per_thread, insert_per_thread))
        threads.append(th)
        th.start()
    for th in threads:
        th.join()                 
if __name__ == "__main__":
    """
    SqliteMgr 多进程多线程并发测试用例
    验证高并发下的线程安全和进程安全
    """
    import os
    import tempfile
    import multiprocessing
    import threading
    import time

    # 创建临时数据库文件
    db_file = os.path.join(tempfile.gettempdir(), "test_sqlite_mgr_mpmt.db")
    if os.path.exists(db_file):
        os.remove(db_file)

    # 先建表
    db = SqliteMgr(db_file)
    create_sql = """
    CREATE TABLE IF NOT EXISTS user (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        age INTEGER
    )
    """
    db.execute(create_sql)
    print("建表成功")



    # 并发参数
    process_num = 4
    thread_num = 5
    insert_per_thread = 20

    # 启动多个进程，每个进程多个线程
    processes = []
    for p in range(process_num):
        proc = multiprocessing.Process(target=process_task, args=(db_file, p, thread_num, insert_per_thread))
        processes.append(proc)
        proc.start()
    for proc in processes:
        proc.join()

    # 主进程查询总数
    db = SqliteMgr(db_file)
    result = db.execute("SELECT COUNT(*) FROM user")
    print(f"多进程多线程并发插入后总记录数: {result[0][0]}")
    # 查询部分数据
    sample = db.execute("SELECT * FROM user ORDER BY id LIMIT 10")
    print("部分样本数据:", sample)

    # 清理
    os.remove(db_file)
    print("测试完成，临时数据库已删除")





