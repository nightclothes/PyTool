"""
杂项工具模块
"""
import psutil
import os
import subprocess
import re
import platform

def find_pro(name_or_pid)->bool:
    """
    检查指定名称或PID的进程是否正在运行
    
    参数:
        name_or_pid: 进程名称(字符串)或进程ID(整数)
        
    返回:
        bool: 进程是否正在运行
    """
    
    
    try:
        # 如果传入的是PID
        if isinstance(name_or_pid, int):
            return psutil.pid_exists(name_or_pid)
            
        # 如果传入的是进程名称
        elif isinstance(name_or_pid, str):
            for proc in psutil.process_iter(['name']):
                try:
                    if proc.name().lower() == name_or_pid.lower():
                        return True
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    pass
        return False
        
    except Exception as e:
        return False

def start_exe(exe_path: str, args: list = None) -> bool:
    """
    启动指定的exe文件
    
    参数:
        exe_path (str): exe文件的路径
        args (list, optional): 传递给exe文件的参数列表，默认为None
        
    返回:
        bool: 启动是否成功
    """
    try:
        if args is None:
            args = []
        # 检查路径是否存在
        if not os.path.exists(exe_path):
            return False
        psutil.Popen([exe_path] + args, shell=True)
        return True
    except Exception as e:
        return False

def terminate_exe(name_or_pid) -> bool:
    """
    终止指定的exe进程，但不会终止自身进程
    
    参数:
        name_or_pid: 进程名称(字符串)或进程ID(整数)
        
    返回:
        bool: 终止是否成功
    """
    try:
        current_pid = os.getpid()
        # 如果传入的是PID
        if isinstance(name_or_pid, int):
            if name_or_pid == current_pid:
                return False
            if psutil.pid_exists(name_or_pid):
                proc = psutil.Process(name_or_pid)
                proc.terminate()
                return True
            return False
            
        # 如果传入的是进程名称
        elif isinstance(name_or_pid, str):
            terminated = False
            for proc in psutil.process_iter(['name', 'pid']):
                try:
                    if proc.name().lower() == name_or_pid.lower():
                        if proc.pid != current_pid:
                            proc.terminate()
                            terminated = True
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    pass
            return terminated
            
    except Exception as e:
        return False


def ping(host = "www.baidu.com", count=4):
    """
    执行ping命令并返回平均延迟（毫秒）
    :param host: 目标主机
    :param count: 发送的ping包数量
    :return: 平均延迟（单位：毫秒），如果失败返回None
    """
    try:
        # Windows系统使用 '-n'，Linux/macOS使用 '-c'
        param = '-n' if platform.system().lower() == 'windows' else '-c'
        command = ['ping', param, str(count), host]
        output = subprocess.check_output(command, stderr=subprocess.STDOUT, universal_newlines=True)
        
        # 解析输出获取平均延迟
        if 'Windows' in platform.system():
            # 支持中英文Windows系统
            match = re.search(r'(?:平均|Average) = (\d+)ms', output) or re.search(r'Average = (\d+)ms', output)
        else:
            match = re.search(r'min/avg/max/mdev = [\d.]+/([\d.]+)/[\d.]+/[\d.]+ ms', output)
        
        if match:
            return float(match.group(1))
        else:
            return None
    except subprocess.CalledProcessError:
        return None




if __name__ == "__main__":
    print(find_pro("python.exe"))
    print(ping("www.baidu.com"))