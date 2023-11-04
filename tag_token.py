from dataclasses import dataclass, field
from enum import Enum, auto

class TagCategory(Enum):
    TEXT = auto()
    FLOW = auto()
    METADATA = auto()
    START_CHILDREN = auto()
    END_CHILDREN = auto()
    P = auto()
    SPAN = auto()
    DIV = auto()
    TITLE = auto()
    META = auto()
    BODY = auto()
    H1 = auto()
    H4 = auto()
    UL = auto()
    LI = auto()
    BLOCKQUOTE = auto()
    EM = auto()
    HR = auto()
    I = auto()
    A = auto()
    HEAD = auto()
    FOOTER = auto()
    IMG = auto()
    NAV = auto()
    EOF = auto()


@dataclass
class Token:
    name: TagCategory
    str_val: str = ""
    attrs: dict = field(default_factory=dict)