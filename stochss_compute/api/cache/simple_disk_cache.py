from __future__ import annotations

import os

from stochss_compute.api.cache import CacheProvider, CacheProviderConfig

class SimpleDiskCacheConfig(CacheProviderConfig):
    root_dir = "sd-cache/"

class SimpleDiskCache(CacheProvider):
    def __init__(self, config: SimpleDiskCacheConfig):
        self.config = config

    def put(self, id: str, value: str):
        # Write value to a file with the name `id`. If a file already exists, replace it.
        with open(os.path.join(self.config.root_dir, id), "w+") as outfile:
            outfile.write(value)

    def get(self, id: str):
        # Read the file in as a string, return the contents.
        with open(os.path.join(self.config.root_dir, id), "r") as infile:
            return infile.read()

    def exists(self, id: str) -> bool:
        # Check to see if the file exists on disk.
        return os.path.isfile(os.path.join(self.config.root_dir, id))
