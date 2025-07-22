"""
进程通信
"""
import zmq
import json
import threading
import queue
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Callable, Optional
from logger import *

class ZMQPair:
    """
    基于ZMQ PAIR-PAIR模式的进程间通信类
    
    提供异步的双向通信功能，支持消息的发送和接收。
    使用线程池处理消息的发送和接收，支持超时和重试机制。
    
    属性:
        __context (zmq.Context): ZMQ上下文
        __socket (zmq.Socket): ZMQ套接字
        __thread_pool (ThreadPoolExecutor): 线程池
        __stop_event (Event): 停止状态事件
        __msg_queue (queue.Queue): 消息队列
        __logger (logging.Logger): 日志记录器
    """

    def __init__(self, 
                 name: str = "ZMQPair", 
                 address: str = None, 
                 is_server: bool = False,
                 logger: Optional[logging.Logger] = None):
        """
        初始化ZMQ PAIR通信实例
        
        参数:
            name (str): 实例名称，用于日志标识
            address (str): 绑定/连接地址，服务端默认为"tcp://localhost:5555"，客户端默认为"tcp://localhost:5555"
            is_server (bool): 是否为服务端，True表示服务端，False表示客户端
            logger (logging.Logger): 日志记录器
        """
        self.__receive_callback = None
        self.__context = zmq.Context()
        self.__socket = self.__context.socket(zmq.PAIR)
        self.__thread_pool = ThreadPoolExecutor(max_workers=2)
        self.__stop_event = threading.Event()
        self.__stop_event.set()
        self.__msg_queue = queue.Queue()
        self.__logger = Logger.get_logger(f"{name}_{os.getpid()}") if logger is None else logger

        # 根据是否为服务端进行绑定或连接
        try:
            if is_server:
                server_address = address if address else "tcp://localhost:5555"
                self.__socket.bind(server_address)
                self.__logger.info(f"绑定地址: {server_address}")
            else:
                client_address = address if address else "tcp://localhost:5555"
                self.__socket.connect(client_address)
                self.__logger.info(f"连接到地址: {client_address}")
        except zmq.ZMQError as e:
            raise e

    def start(self) -> None:
        """
        启动通信服务
        
        启动消息接收和发送线程。
        """
        if not self.__stop_event.is_set():
            return

        self.__stop_event.clear()
        self.__thread_pool.submit(self.__receive_loop)
        self.__thread_pool.submit(self.__send_loop)
        self.__logger.info("通信服务已启动")

    def stop(self) -> None:
        """
        停止通信服务
        
        关闭套接字和线程池。
        """
        self.__stop_event.set()
        if self.__socket:
            self.__socket.close()
        self.__thread_pool.shutdown(wait=True)
        self.__context.term()
        self.__logger.info("通信服务已停止")

    def send(self, data: Any, timeout: float = 1.0) -> bool:
        """
        发送数据
        
        参数:
            data (Any): 要发送的数据，将被JSON序列化
            timeout (float): 超时时间（秒）
            
        返回:
            bool: 发送是否成功
        """
        try:
            self.__msg_queue.put(data, timeout=timeout)
            return True
        except queue.Full:
            self.__logger.error("发送队列已满")
            return False

    def receive(self, callback: Callable[[Any], None]) -> None:
        """
        注册接收回调函数
        
        参数:
            callback (Callable[[Any], None]): 处理接收数据的回调函数
        """
        self.__receive_callback = callback

    def block(self, timeout: float = None) -> bool:
        """
        阻塞当前线程，直到通信服务停止或超时
        
        参数:
            timeout (float): 超时时间(秒)，None表示无限等待
            
        返回:
            bool: 如果通信服务正常停止返回True，超时返回False
        """
        return self.__stop_event.wait(timeout=timeout)

    def __send_loop(self) -> None:
        """
        发送循环
        
        从消息队列中获取数据并发送。
        """
        while not self.__stop_event.is_set():
            try:
                data = self.__msg_queue.get(timeout=0.1)
                try:
                    message = json.dumps(data).encode('utf-8')
                    self.__socket.send(message, flags=zmq.NOBLOCK)
                    self.__logger.debug(f"发送数据: {data}")
                except zmq.ZMQError as e:
                    if e.errno == zmq.EAGAIN:
                        # 发送缓冲区已满，重新放入队列
                        self.__msg_queue.put(data)
                    else:
                        self.__logger.error(f"发送数据失败: {e}")
            except queue.Empty:
                continue
            except Exception as e:
                self.__logger.error(f"发送循环异常: {e}")

    def __receive_loop(self) -> None:
        """
        接收循环
        
        接收数据并调用回调函数处理。
        """
        while not self.__stop_event.is_set():
            try:
                if self.__socket.poll(100, zmq.POLLIN):
                    message = self.__socket.recv(flags=zmq.NOBLOCK)
                    try:
                        data = json.loads(message.decode('utf-8'))
                        self.__logger.debug(f"接收数据: {data}")
                        if self.__receive_callback:
                            self.__receive_callback(data)
                    except json.JSONDecodeError as e:
                        self.__logger.error(f"解析接收数据失败: {e}")
            except zmq.ZMQError as e:
                if e.errno != zmq.EAGAIN:
                    self.__logger.error(f"接收数据失败: {e}")
            except Exception as e:
                self.__logger.error(f"接收循环异常: {e}")




import multiprocessing
import time


def server_proc():
    """
    服务端进程，接收并回复消息
    """
    def on_receive(data):
        print(f"[Server] 收到: {data}")
    server = ZMQPair(is_server=True, name="Server")
    server.receive(on_receive)
    server.start()
    for i in range(3):
        server.send({"msg": f"server hello {i}"})
        time.sleep(1)
    server.block(5)
    server.stop()

def client_proc():
    """
    客户端进程，发送并接收消息
    """
    def on_receive(data):
        print(f"[Client] 收到: {data}")
    client = ZMQPair(is_server=False, name="Client")
    client.receive(on_receive)
    client.start()
    for i in range(3):
        client.send({"msg": f"client hello {i}"})
        time.sleep(1)
    client.block(5)
    client.stop()

if __name__ == "__main__":
    """
    ZMQPair 测试用例：演示服务端和客户端的进程间通信
    """

    # 启动服务端和客户端进程
    server = multiprocessing.Process(target=server_proc)
    client = multiprocessing.Process(target=client_proc)
    server.start()
    time.sleep(0.5)  # 确保服务端先启动
    client.start()
    server.join()
    client.join()
    print("ZMQPair 测试完成")








