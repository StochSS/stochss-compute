from __future__ import annotations

from stochss_compute.api.cache import CacheProvider, CacheProviderConfig

class SimpleDiskCacheConfig(CacheProviderConfig):
    root_dir = "sd-cache/"

class SimpleDiskCache(CacheProvider):
    def __init__(self, config: SimpleDiskCacheConfig):
        self.config = config

    def put(id: str, value):
        pass

    def get(id: str):
        pass

    def exists(id: str) -> bool:
        pass