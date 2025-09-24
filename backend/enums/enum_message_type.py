from enum import Enum

class E_Message_Type(Enum):
    TEXT = 0
    IMAGE = 1
    VIDEO = 2
    AUDIO = 3
    FILE = 4
    AUTO_MESS = 5

    @classmethod
    def fromNumber(cls, number):
        return cls(number)