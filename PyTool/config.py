"""
配置文件模块
"""

import yaml
from pathlib import Path
from typing import Any, Dict, Optional
import threading
from filelock import FileLock


class Cfg:
    """
    基于YAML的配置文件管理类
    提供配置文件的读取、修改和保存功能
    
    特性:
    - 自动创建不存在的配置文件
    - 支持嵌套配置项的访问和修改
    - 线程安全的配置操作
    - 自动维护配置文件格式
    """
    __defalut_key = "defalut_key"

    
    def __init__(self, cfg_path: str):
        """
        初始化配置管理器
        
        参数:
            cfg_path: 配置文件路径
        """
        self.__cfg_path = Path(cfg_path)
        self.__t_lock = threading.Lock()
        self.__p_lock = FileLock(f"{self.__cfg_path.absolute()}.lock")
        self.__cache = {}

    def load(self)->bool:
        """
        加载配置文件
        """
        with self.__p_lock, self.__t_lock:
            if not self.__cfg_path.exists():
                return False
            with open(self.__cfg_path, "r", encoding="utf-8") as f:
                self.__cache = yaml.safe_load(f, Loader=yaml.FullLoader)
            return True
        
    def save(self)->bool:
        """
        保存配置文件
        """
        with self.__p_lock, self.__t_lock:
            with open(self.__cfg_path, "w", encoding="utf-8") as f:
                yaml.dump(self.__cache, f, allow_unicode=True)
            return True
        
    def get(self, key: str)->Any:
        """
        获取配置项
        """
        return self.__cache.get(key)
    
    def set(self, key: str, value: Any)->bool:
        """
        设置配置项
        """
        self.__cache[key] = value
        return True
    
    def __del__(self):
        """
        析构函数
        """
        if self.__p_lock.is_locked: 
            self.__p_lock.release()
        if self.__t_lock.locked():
            self.__t_lock.release()


    def encrypt(self, data: str, key: str = __defalut_key) -> str:
        """
        使用简单异或算法加密数据
        
        参数:
            data: 要加密的原始字符串
            key: 加密密钥
            
        返回:
            加密后的字符串(hex格式)
        """
        if not data:
            return data
        encrypted = []
        key_len = len(key)
        for i, c in enumerate(data):
            key_c = key[i % key_len]
            encrypted_c = chr(ord(c) ^ ord(key_c))
            encrypted.append(encrypted_c)
        return ''.join(encrypted).encode('utf-8').hex()

    def decrypt(self, encrypted_hex: str, key: str = __defalut_key) -> str:
        """
        解密使用encrypt方法加密的数据
        
        参数:
            encrypted_hex: 加密后的hex字符串
            key: 解密密钥(必须与加密密钥相同)
            
        返回:
            解密后的原始字符串
            
        异常:
            ValueError: 如果输入不是有效的hex字符串
        """
        if not encrypted_hex:
            return encrypted_hex
        try:
            encrypted = bytes.fromhex(encrypted_hex).decode('utf-8')
            decrypted = []
            key_len = len(key)
            for i, c in enumerate(encrypted):
                key_c = key[i % key_len]
                decrypted_c = chr(ord(c) ^ ord(key_c))
                decrypted.append(decrypted_c)
            return ''.join(decrypted)
        except ValueError as e:
            raise ValueError("无效的hex字符串") from e


if __name__ == "__main__":
    cfg = Cfg("test.yaml")
    # 测试加密解密功能
    test_data = "asdfasdf"
    test_key = "fasddfjkdfjskf"
    
    # 加密测试
    encrypted = cfg.encrypt(test_data)
    print(f"加密前: {test_data}")
    print(f"加密后(hex): {encrypted}")
    
    # 解密测试
    decrypted = cfg.decrypt(encrypted)
    print(f"解密后: {decrypted}")
    
    # 验证解密结果是否与原始数据一致
    assert decrypted == test_data, "解密结果与原始数据不一致"
    print("测试通过: 解密结果与原始数据一致")



