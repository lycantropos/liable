from abc import (ABC,
                 abstractmethod)
from typing import (TypingMeta,
                    Union,
                    Type,
                    Tuple)

from liable.types import NamespaceType


class Annotation(ABC):
    def __init__(self, origin: Union[Type, TypingMeta]):
        self.origin = origin

    @abstractmethod
    def to_string(self, namespace: NamespaceType) -> str:
        raise NotImplemented

    @property
    @abstractmethod
    def bases(self) -> Tuple[Type, ...]:
        raise NotImplemented
