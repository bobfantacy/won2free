from abc import ABC, abstractmethod

class BaseModel(ABC):
    
    __pkey__ = 'id'
    __pkeytype__ = 'N'
    
    def __init__(self, *args, **kwargs):
        for (key , value) in kwargs.items():
            setattr(self, key, value)
    
    def to_dict(self):
        return {key: getattr(self, key) for key in self.__dict__ if not key.startswith('_')}

    @classmethod
    def from_dict(cls, data):
        instance = cls()
        for key, value in data.items():
            setattr(instance, key, value)
        return instance