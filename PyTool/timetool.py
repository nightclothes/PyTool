"""
时间工具
"""
import datetime

def timer(func):
    """
    函数运行时间装饰器
    
    参数:
        func: 被装饰的函数
        
    返回:
        包装后的函数
    """

    def wrapper(*args, **kwargs):
        # 记录开始时间
        start_time = datetime.datetime.now()

        # 执行函数
        result = func(*args, **kwargs)

        # 计算运行时间
        end_time = datetime.datetime.now()
        run_time = end_time - start_time
        run_time = run_time.total_seconds()

        # 输出运行时间
        print(f"{func.__name__} : {run_time}s")

        return result
    
    

    return wrapper


def now_date():
    """
    获取当前日期
    
    返回:
        datetime.date: 当前日期对象
    """
    return datetime.datetime.now().date()

def now_time():
    """
    获取当前时间
    
    返回:
        datetime.time: 当前时间对象
    """
    return datetime.datetime.now().time()


