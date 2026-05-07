"""
API 缓存工具模块

为频繁调用的 API 端点提供简单的内存缓存。
"""

import time
import functools
import hashlib
import json
from typing import Any, Callable, Dict, Optional, Tuple
from datetime import datetime, timedelta


class SimpleCache:
    """简单的内存缓存类"""
    
    def __init__(self, ttl: int = 30, max_size: int = 100):
        """
        初始化缓存
        
        Args:
            ttl: 默认生存时间（秒）
            max_size: 最大缓存条目数
        """
        self._cache: Dict[str, Tuple[Any, float]] = {}
        self._default_ttl = ttl
        self._max_size = max_size
        self._hits = 0
        self._misses = 0
    
    def get(self, key: str) -> Optional[Any]:
        """获取缓存值"""
        if key in self._cache:
            value, expiry = self._cache[key]
            if time.time() < expiry:
                self._hits += 1
                return value
            else:
                # 过期删除
                del self._cache[key]
        self._misses += 1
        return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """设置缓存值"""
        ttl = ttl or self._default_ttl
        
        # 清理过期和多余的缓存
        self._cleanup()
        
        self._cache[key] = (value, time.time() + ttl)
    
    def delete(self, key: str) -> bool:
        """删除缓存"""
        if key in self._cache:
            del self._cache[key]
            return True
        return False
    
    def clear(self) -> None:
        """清空所有缓存"""
        self._cache.clear()
        self._hits = 0
        self._misses = 0
    
    def _cleanup(self) -> None:
        """清理过期和多余的缓存"""
        now = time.time()
        
        # 删除过期项
        expired_keys = [k for k, (_, exp) in self._cache.items() if now >= exp]
        for k in expired_keys:
            del self._cache[k]
        
        # 如果超过最大size，删除最早的
        if len(self._cache) >= self._max_size:
            # 按过期时间排序，删除最久远的
            sorted_keys = sorted(self._cache.keys(), key=lambda k: self._cache[k][1])
            for k in sorted_keys[:len(self._cache) - self._max_size + 1]:
                del self._cache[k]
    
    @property
    def stats(self) -> Dict[str, Any]:
        """获取缓存统计"""
        total = self._hits + self._misses
        hit_rate = self._hits / total if total > 0 else 0
        return {
            "hits": self._hits,
            "misses": self._misses,
            "total": total,
            "hit_rate": round(hit_rate, 4),
            "size": len(self._cache)
        }
    
    def keys(self) -> list:
        """获取所有缓存键"""
        return list(self._cache.keys())


def make_cache_key(*args, **kwargs) -> str:
    """生成缓存键"""
    key_data = json.dumps({"args": args, "kwargs": kwargs}, sort_keys=True, default=str)
    return hashlib.md5(key_data.encode()).hexdigest()


def cached(ttl: int = 30, key_func: Optional[Callable] = None):
    """
    缓存装饰器
    
    Args:
        ttl: 生存时间（秒）
        key_func: 自定义键生成函数
        
    Usage:
        @cached(ttl=60)
        async def get_data():
            ...
        
        @cached(ttl=30, key_func=lambda x, y: f"{x}-{y}")
        async def get_user(user_id, version):
            ...
    """
    def decorator(func: Callable) -> Callable:
        # 创建函数级缓存
        cache = SimpleCache(ttl=ttl)
        
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            # 生成缓存键
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                cache_key = make_cache_key(func.__name__, *args, **kwargs)
            
            # 尝试获取缓存
            result = cache.get(cache_key)
            if result is not None:
                return result
            
            # 执行函数
            result = await func(*args, **kwargs)
            
            # 保存缓存
            cache.set(cache_key, result, ttl)
            
            return result
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            # 生成缓存键
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                cache_key = make_cache_key(func.__name__, *args, **kwargs)
            
            # 尝试获取缓存
            result = cache.get(cache_key)
            if result is not None:
                return result
            
            # 执行函数
            result = func(*args, **kwargs)
            
            # 保存缓存
            cache.set(cache_key, result, ttl)
            
            return result
        
        # 根据函数类型返回包装器
        if functools.iscoroutinefunction(func):
            async_wrapper.cache = cache
            async_wrapper.cache_clear = cache.clear
            async_wrapper.cache_stats = cache.stats
            return async_wrapper
        else:
            sync_wrapper.cache = cache
            sync_wrapper.cache_clear = cache.clear
            sync_wrapper.cache_stats = cache.stats
            return sync_wrapper
    
    return decorator


class CacheManager:
    """缓存管理器 - 管理多个缓存实例"""
    
    _instance: Optional['CacheManager'] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._caches: Dict[str, SimpleCache] = {}
        self._initialized = True
        
        # 预创建常用缓存
        self.get_cache("soul", ttl=30)
        self.get_cache("emotion", ttl=5)
        self.get_cache("memory", ttl=10)
        self.get_cache("config", ttl=60)
    
    def get_cache(self, name: str, ttl: int = 30, max_size: int = 100) -> SimpleCache:
        """
        获取或创建命名缓存
        
        Args:
            name: 缓存名称
            ttl: 生存时间
            max_size: 最大大小
        """
        if name not in self._caches:
            self._caches[name] = SimpleCache(ttl=ttl, max_size=max_size)
        return self._caches[name]
    
    def delete_cache(self, name: str) -> bool:
        """删除命名缓存"""
        if name in self._caches:
            del self._caches[name]
            return True
        return False
    
    def clear_all(self) -> None:
        """清空所有缓存"""
        for cache in self._caches.values():
            cache.clear()
    
    @property
    def stats(self) -> Dict[str, Dict]:
        """获取所有缓存的统计信息"""
        return {name: cache.stats for name, cache in self._caches.items()}


# 全局缓存管理器实例
cache_manager = CacheManager()


# 便捷函数
def get_soul_cache() -> SimpleCache:
    """获取灵魂配置缓存（30秒）"""
    return cache_manager.get_cache("soul", ttl=30)


def get_emotion_cache() -> SimpleCache:
    """获取情绪状态缓存（5秒）"""
    return cache_manager.get_cache("emotion", ttl=5)


def get_memory_cache() -> SimpleCache:
    """获取记忆统计缓存（10秒）"""
    return cache_manager.get_cache("memory", ttl=10)


def get_config_cache() -> SimpleCache:
    """获取配置缓存（60秒）"""
    return cache_manager.get_cache("config", ttl=60)


def invalidate_soul_cache() -> None:
    """使灵魂配置缓存失效"""
    cache = get_soul_cache()
    cache.clear()


def invalidate_emotion_cache() -> None:
    """使情绪状态缓存失效"""
    cache = get_emotion_cache()
    cache.clear()


def invalidate_memory_cache() -> None:
    """使记忆缓存失效"""
    cache = get_memory_cache()
    cache.clear()


def invalidate_config_cache() -> None:
    """使配置缓存失效"""
    cache = get_config_cache()
    cache.clear()


def clear_all_caches() -> None:
    """清空所有缓存"""
    cache_manager.clear_all()


def get_cache_stats() -> Dict[str, Dict]:
    """获取所有缓存统计"""
    return cache_manager.stats
