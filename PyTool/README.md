# PyTool

## 介绍

PyTool 是一个功能丰富的 Python 工具库，提供了进程管理、线程安全、数据库访问、进程通信、日志记录等多种实用功能。该工具库专为高并发、多进程应用场景设计，具有良好的线程安全性和进程安全性。

## 主要特性

- 🚀 **高性能进程管理** - 支持进程生命周期管理、状态监控、优雅停止
- 🔒 **线程/进程安全** - 提供基于虚拟地址的锁管理机制
- 📊 **数据库访问** - 线程安全的 SQLite 数据库操作，支持事务管理
- 🌐 **进程间通信** - 基于 ZMQ 的高效进程通信解决方案
- 📝 **日志系统** - 自动分类存储的日志管理系统
- ⚙️ **配置管理** - 基于 YAML 的配置文件管理，支持加密
- 🛠️ **实用工具** - 时间工具、进程查找、网络检测等实用功能
- 💥 **异常处理** - 自动生成进程转储文件，便于调试

## 功能模块

- [x] **进程管理** (`pmgr.py`) - 任务进程生命周期管理
- [x] **线程锁管理** (`tlock.py`) - 基于虚拟地址的线程锁
- [x] **进程锁管理** (`plock.py`) - 基于文件锁的进程锁
- [x] **异常Dump** (`dump.py`) - 自动进程转储和调试
- [x] **日志系统** (`logger.py`) - 分级日志记录和存储
- [x] **时间工具** (`timetool.py`) - 时间处理和性能测量
- [x] **进程通信** (`pcom.py`) - ZMQ 基础的进程间通信
- [x] **SQLite数据库访问** (`sqlite.py`) - 线程安全的数据库操作
- [x] **配置文件** (`config.py`) - YAML 配置管理和加密
- [x] **实用工具** (`utils.py`) - 进程管理和网络工具

## 安装

### 依赖要求

```bash
pip install pyyaml
pip install filelock
pip install pyzmq
pip install psutil
pip install pydumpling
```

### 安装方式

1. **直接使用**：将 `PyTool` 目录复制到你的项目中
2. **模块导入**：将 `PyTool` 添加到 Python 路径中

```python
import sys
sys.path.append('path/to/PyTool')
from PyTool import pmgr, logger, config
```

## 快速开始

### 1. 进程管理

```python
from PyTool.pmgr import TaskProMgr
import time

def worker_task(name, count, stop_event, start_success_event):
    """工作任务函数"""
    print(f"任务 {name} 启动")
    start_success_event.set()  # 通知启动成功
    
    for i in range(count):
        if stop_event.is_set():
            break
        print(f"任务 {name} 执行第 {i+1} 次")
        time.sleep(1)
    print(f"任务 {name} 结束")

# 创建进程管理器
mgr = TaskProMgr()

# 创建任务
mgr.create_task("task1", worker_task, "任务1", 10)

# 启动任务（支持超时设置）
mgr.start_task("task1", timeout=5.0)

# 查看任务状态
print(mgr.get_task_info("task1"))

# 停止任务
mgr.stop_task("task1")
```

### 2. 线程安全锁

```python
from PyTool.tlock import KeyTLock
import threading
import time

# 创建线程锁管理器
tlock = KeyTLock()

def worker(worker_id):
    # 使用虚拟地址加锁
    with tlock.lock("shared_resource"):
        print(f"工作线程 {worker_id} 获得锁")
        time.sleep(1)
        print(f"工作线程 {worker_id} 释放锁")

# 创建多个线程
threads = []
for i in range(3):
    t = threading.Thread(target=worker, args=(i,))
    threads.append(t)
    t.start()

for t in threads:
    t.join()
```

### 3. 数据库操作

```python
from PyTool.sqlite import SqliteMgr

# 创建数据库管理器
db = SqliteMgr("test.db")

# 创建表
db.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        email TEXT UNIQUE
    )
""")

# 插入数据
db.execute("INSERT INTO users (name, email) VALUES (?, ?)", ("张三", "zhangsan@example.com"))

# 查询数据
result = db.execute("SELECT * FROM users WHERE name = ?", ("张三",))
print(result)

# 使用事务
with db.transaction():
    db.execute("INSERT INTO users (name, email) VALUES (?, ?)", ("李四", "lisi@example.com"))
    db.execute("INSERT INTO users (name, email) VALUES (?, ?)", ("王五", "wangwu@example.com"))
```

### 4. 日志系统

```python
from PyTool.logger import Logger

# 获取日志实例
logger = Logger.get_logger("MyApp")

# 记录不同级别的日志
logger.debug("调试信息")
logger.info("普通信息")
logger.warning("警告信息")
logger.error("错误信息")
logger.critical("严重错误")

# 日志文件自动按日期和名称分类存储在 logs/ 目录下
```

### 5. 配置管理

```python
from PyTool.config import Cfg

# 创建配置管理器
config = Cfg("config.yaml")

# 设置配置项
config.set("database.host", "localhost")
config.set("database.port", 3306)
config.set("app.debug", True)

# 获取配置项
host = config.get("database.host")
port = config.get("database.port", 5432)  # 默认值

# 保存配置
config.save()

# 加密敏感配置
config.set_encrypted("database.password", "secret123")
password = config.get_encrypted("database.password")
```

### 6. 进程间通信

```python
from PyTool.pcom import Pair
import time

# 进程A - 发送方
def sender_process():
    pair = Pair("tcp://127.0.0.1:5555", is_server=True)
    
    for i in range(5):
        message = f"消息 {i+1}"
        pair.send(message)
        print(f"发送: {message}")
        
        # 接收回复
        reply = pair.recv(timeout=5000)
        if reply:
            print(f"收到回复: {reply}")
        time.sleep(1)
    
    pair.close()

# 进程B - 接收方
def receiver_process():
    pair = Pair("tcp://127.0.0.1:5555", is_server=False)
    
    while True:
        message = pair.recv(timeout=5000)
        if message:
            print(f"接收: {message}")
            # 发送回复
            pair.send(f"已收到: {message}")
        else:
            break
    
    pair.close()
```

### 7. 时间工具和性能测量

```python
from PyTool.timetool import timer, now_date, now_time
import time

# 使用装饰器测量函数执行时间
@timer
def slow_function():
    time.sleep(2)
    return "完成"

result = slow_function()  # 自动打印执行时间

# 获取当前日期和时间
print(f"当前日期: {now_date()}")  # 格式: 2024-01-01
print(f"当前时间: {now_time()}")  # 格式: 14:30:25
```

### 8. 异常处理和进程转储

```python
from PyTool.dump import Dumper

# 设置自动进程转储
dumper = Dumper.setup(app_name="MyApp", dump_dir="./dumps")

# 当程序发生未捕获异常时，会自动生成dump文件
def problematic_function():
    raise ValueError("这是一个测试异常")

# 加载和调试dump文件
# Dumper.load("./dumps/MyApp_20240101_143025.dump")
```

### 9. 实用工具

```python
from PyTool.utils import find_pro, start_exe, terminate_exe, ping

# 检查进程是否运行
if find_pro("notepad.exe"):
    print("记事本正在运行")

# 启动程序
if start_exe("notepad.exe", ["test.txt"]):
    print("成功启动记事本")

# 终止进程
if terminate_exe("notepad.exe"):
    print("成功终止记事本")

# 网络延迟测试
latency = ping("www.baidu.com", count=4)
if latency:
    print(f"平均延迟: {latency}ms")
```

## 详细API文档

### 进程管理 (pmgr.py)

#### TaskPro 类

**主要方法：**

- `__init__(task_id, target, *args, **kwargs)` - 初始化任务进程
- `start(timeout=10.0)` - 启动进程，支持启动超时设置
- `stop(timeout=10.0)` - 停止进程，支持优雅停止
- `restart(timeout=10.0)` - 重启进程
- `is_alive()` - 检查进程是否存活
- `get_info()` - 获取进程详细信息

**特性：**
- 启动成功确认机制
- 优雅停止支持
- 进程状态监控
- 参数传递优化

#### TaskProMgr 类

**主要方法：**

- `create_task(task_id, target, *args, **kwargs)` - 创建任务
- `start_task(task_id, timeout=10.0)` - 启动指定任务
- `stop_task(task_id, timeout=10.0)` - 停止指定任务
- `restart_task(task_id, timeout=10.0)` - 重启指定任务
- `remove_task(task_id)` - 移除任务
- `get_task_info(task_id)` - 获取任务信息
- `list_tasks()` - 列出所有任务ID
- `get_all_tasks_info()` - 获取所有任务信息
- `stop_all_tasks(timeout=10.0)` - 停止所有任务

### 线程锁管理 (tlock.py)

#### KeyTLock 类

**主要方法：**

- `lock(virtual_addr)` - 获取指定虚拟地址的锁（返回上下文管理器）
- `_add(virtual_addr)` - 添加锁
- `_del(virtual_addr)` - 删除锁
- `_clear()` - 清除所有锁

**使用方式：**
```python
with tlock.lock("resource_name"):
    # 临界区代码
    pass
```

### 进程锁管理 (plock.py)

#### KeyPLock 类

**主要方法：**

- `lock(virtual_addr)` - 获取指定虚拟地址的进程锁（返回上下文管理器）
- `_add(virtual_addr)` - 添加进程锁
- `_del(virtual_addr)` - 删除进程锁
- `_clear()` - 清除所有进程锁

**特性：**
- 基于文件锁实现
- 跨进程安全
- 自动资源清理

### SQLite数据库 (sqlite.py)

#### SqliteMgr 类

**主要方法：**

- `__init__(db_path)` - 初始化数据库管理器
- `execute(sql, params=None)` - 执行SQL语句
- `transaction()` - 获取事务上下文管理器

**特性：**
- 线程安全和进程安全
- 自动数据库优化配置
- 事务支持
- 连接池管理

### 日志系统 (logger.py)

#### Logger 类

**主要方法：**

- `get_logger(name)` - 获取或创建日志实例（类方法）

**特性：**
- 自动按日期和名称分类存储
- 支持文件和控制台双重输出
- 详细的日志格式
- 线程安全

### 配置管理 (config.py)

#### Cfg 类

**主要方法：**

- `__init__(config_file)` - 初始化配置管理器
- `get(key, default=None)` - 获取配置项
- `set(key, value)` - 设置配置项
- `save()` - 保存配置到文件
- `load()` - 从文件加载配置
- `get_encrypted(key, default=None)` - 获取加密配置项
- `set_encrypted(key, value)` - 设置加密配置项

**特性：**
- 基于YAML格式
- 支持嵌套配置访问
- 线程安全操作
- 简单加密支持
- 自动文件创建

### 进程通信 (pcom.py)

#### Pair 类

**主要方法：**

- `__init__(address, is_server=True)` - 初始化通信对
- `send(message)` - 发送消息
- `recv(timeout=1000)` - 接收消息
- `close()` - 关闭连接

**特性：**
- 基于ZMQ PAIR-PAIR模式
- 异步双向通信
- 超时和重试机制
- 自动资源管理

## 最佳实践

### 1. 进程管理最佳实践

```python
# 推荐的任务函数结构
def worker_task(task_name, stop_event, start_success_event, **kwargs):
    try:
        # 初始化代码
        print(f"任务 {task_name} 初始化")
        
        # 通知启动成功
        start_success_event.set()
        
        # 主循环
        while not stop_event.is_set():
            # 执行任务逻辑
            time.sleep(1)
            
    except Exception as e:
        print(f"任务异常: {e}")
    finally:
        print(f"任务 {task_name} 清理资源")
```

### 2. 数据库操作最佳实践

```python
# 使用事务确保数据一致性
with db.transaction():
    # 批量操作
    for user in users:
        db.execute("INSERT INTO users (name, email) VALUES (?, ?)", 
                  (user['name'], user['email']))

# 使用参数化查询防止SQL注入
result = db.execute("SELECT * FROM users WHERE age > ? AND city = ?", 
                   (18, "北京"))
```

### 3. 锁使用最佳实践

```python
# 使用有意义的锁名称
with tlock.lock(f"user_data_{user_id}"):
    # 操作特定用户数据
    pass

# 避免嵌套锁，防止死锁
# 错误示例：
# with tlock.lock("lock1"):
#     with tlock.lock("lock2"):  # 可能导致死锁
#         pass
```

### 4. 配置管理最佳实践

```python
# 使用分层配置结构
config.set("database.mysql.host", "localhost")
config.set("database.mysql.port", 3306)
config.set("database.redis.host", "localhost")
config.set("database.redis.port", 6379)

# 敏感信息使用加密存储
config.set_encrypted("database.mysql.password", "secret")
config.set_encrypted("api.secret_key", "your_secret_key")
```

## 注意事项

1. **进程管理**：确保任务函数正确处理 `stop_event` 和 `start_success_event`
2. **数据库操作**：长时间运行的应用建议定期重连数据库
3. **锁管理**：避免长时间持有锁，防止性能问题
4. **进程通信**：注意网络超时设置，避免无限等待
5. **日志系统**：合理设置日志级别，避免日志文件过大
6. **配置管理**：定期备份配置文件，避免数据丢失

## 许可证

本项目采用 MIT 许可证，详情请参阅 LICENSE 文件。

## 贡献

欢迎提交 Issue 和 Pull Request 来改进这个项目。

## 更新日志

### v1.0.0
- 初始版本发布
- 包含所有核心功能模块
- 完整的文档和示例
