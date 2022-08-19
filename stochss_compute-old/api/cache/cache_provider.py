from __future__ import annotations

from abc import ABC
from abc import abstractmethod

class CacheProviderConfig(ABC):
    def __init__(self, **kwargs):
        """
        Easy way to apply some number of named arguments onto self.
        """

        self.__dict__ = {**self.__dict__, **kwargs}

class CacheProvider(ABC):
    def __init__(self, config: CacheProviderConfig):
        pass

    @abstractmethod
    def put(id: str, value):
        pass

    @abstractmethod
    def get(id: str):
        pass

    @abstractmethod
    def exists(id: str) -> bool:
        pass
