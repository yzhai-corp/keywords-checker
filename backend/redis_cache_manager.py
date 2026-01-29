"""
Redis Cache Manager for Keywords Checker
Handles caching of Skills and Reference files from S3
"""

import os
import logging
import json
import hashlib
import redis
from typing import Optional, List, Dict

logger = logging.getLogger(__name__)


class RedisCacheManager:
    """Manages Redis caching for Skills and Reference files"""
    
    def __init__(self, host=None, port=None, db=0, ttl=3600):
        """
        Initialize RedisCacheManager
        
        Args:
            host: Redis host (defaults to env var REDIS_HOST)
            port: Redis port (defaults to env var REDIS_PORT or 6379)
            db: Redis database number
            ttl: Cache TTL in seconds (default: 1 hour)
        """
        self.host = host or os.getenv('REDIS_HOST', 'localhost')
        self.port = int(port or os.getenv('REDIS_PORT', 6379))
        self.db = db
        self.ttl = ttl
        
        try:
            self.redis_client = redis.Redis(
                host=self.host,
                port=self.port,
                db=self.db,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5
            )
            
            # Test connection
            self.redis_client.ping()
            logger.info(f"Redis connected: {self.host}:{self.port} (DB: {self.db})")
            self.enabled = True
            
        except (redis.ConnectionError, redis.TimeoutError) as e:
            logger.warning(f"Redis connection failed: {e}. Running without cache.")
            self.redis_client = None
            self.enabled = False
    
    def _generate_key(self, prefix: str, identifier: str) -> str:
        """
        Generate a cache key
        
        Args:
            prefix: Key prefix (e.g., 'skill', 'reference')
            identifier: Unique identifier (e.g., skill name, file path)
            
        Returns:
            str: Cache key
        """
        # Use hash to keep key length consistent
        hash_id = hashlib.md5(identifier.encode()).hexdigest()
        return f"keywords_checker:{prefix}:{hash_id}"
    
    def get(self, prefix: str, identifier: str) -> Optional[str]:
        """
        Get cached content
        
        Args:
            prefix: Key prefix
            identifier: Unique identifier
            
        Returns:
            str: Cached content or None if not found
        """
        if not self.enabled:
            return None
        
        try:
            key = self._generate_key(prefix, identifier)
            value = self.redis_client.get(key)
            
            if value:
                logger.debug(f"Cache hit: {prefix}:{identifier}")
            else:
                logger.debug(f"Cache miss: {prefix}:{identifier}")
            
            return value
            
        except redis.RedisError as e:
            logger.error(f"Redis get error: {e}")
            return None
    
    def set(self, prefix: str, identifier: str, content: str, ttl: Optional[int] = None) -> bool:
        """
        Set cache content
        
        Args:
            prefix: Key prefix
            identifier: Unique identifier
            content: Content to cache
            ttl: Optional TTL override (seconds)
            
        Returns:
            bool: True if successful
        """
        if not self.enabled:
            return False
        
        try:
            key = self._generate_key(prefix, identifier)
            cache_ttl = ttl if ttl is not None else self.ttl
            
            self.redis_client.setex(key, cache_ttl, content)
            logger.debug(f"Cache set: {prefix}:{identifier} (TTL: {cache_ttl}s)")
            
            return True
            
        except redis.RedisError as e:
            logger.error(f"Redis set error: {e}")
            return False
    
    def delete(self, prefix: str, identifier: str) -> bool:
        """
        Delete cached content
        
        Args:
            prefix: Key prefix
            identifier: Unique identifier
            
        Returns:
            bool: True if successful
        """
        if not self.enabled:
            return False
        
        try:
            key = self._generate_key(prefix, identifier)
            result = self.redis_client.delete(key)
            
            if result:
                logger.debug(f"Cache deleted: {prefix}:{identifier}")
            
            return bool(result)
            
        except redis.RedisError as e:
            logger.error(f"Redis delete error: {e}")
            return False
    
    def get_skill_file(self, file_key: str) -> Optional[str]:
        """
        Get skill file from cache
        
        Args:
            file_key: S3 key for skill file
            
        Returns:
            str: Cached content or None
        """
        return self.get('skill', file_key)
    
    def set_skill_file(self, file_key: str, content: str, ttl: Optional[int] = None) -> bool:
        """
        Cache skill file
        
        Args:
            file_key: S3 key for skill file
            content: File content
            ttl: Optional TTL override
            
        Returns:
            bool: True if successful
        """
        return self.set('skill', file_key, content, ttl)
    
    def get_reference_file(self, file_key: str) -> Optional[str]:
        """
        Get reference file from cache
        
        Args:
            file_key: S3 key for reference file
            
        Returns:
            str: Cached content or None
        """
        return self.get('reference', file_key)
    
    def set_reference_file(self, file_key: str, content: str, ttl: Optional[int] = None) -> bool:
        """
        Cache reference file
        
        Args:
            file_key: S3 key for reference file
            content: File content
            ttl: Optional TTL override
            
        Returns:
            bool: True if successful
        """
        return self.set('reference', file_key, content, ttl)
    
    def flush_all(self) -> bool:
        """
        Flush all cached data
        
        Returns:
            bool: True if successful
        """
        if not self.enabled:
            return False
        
        try:
            self.redis_client.flushdb()
            logger.info("Redis cache flushed")
            return True
            
        except redis.RedisError as e:
            logger.error(f"Redis flush error: {e}")
            return False
    
    def get_stats(self) -> Dict[str, any]:
        """
        Get cache statistics
        
        Returns:
            dict: Cache statistics
        """
        if not self.enabled:
            return {'enabled': False}
        
        try:
            info = self.redis_client.info('stats')
            
            return {
                'enabled': True,
                'host': self.host,
                'port': self.port,
                'db': self.db,
                'ttl': self.ttl,
                'keys': self.redis_client.dbsize(),
                'hits': info.get('keyspace_hits', 0),
                'misses': info.get('keyspace_misses', 0)
            }
            
        except redis.RedisError as e:
            logger.error(f"Redis stats error: {e}")
            return {'enabled': False, 'error': str(e)}
