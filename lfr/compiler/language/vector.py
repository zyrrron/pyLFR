from typing import Generic, List, Optional, Type, TypeVar

from lfr.compiler.language.vectorrange import VectorRange

T = TypeVar("T")


class Vector(Generic[T]):
    """
    Vector of objects T
    """

    def __init__(
        self,
        id: str,
        vector_type: Optional[Type[T]] = None,
        startindex: int = 0,
        endindex: int = -1,
    ):
        self.id = id
        self.startindex = startindex
        self.endindex = endindex
        self.vec: List[T] = []

        if vector_type is not None:
            # If it's a singular item avoid the indexing
            if len(self) == 1:
                self.vec.append(vector_type(self.id))
            else:
                for i in range(len(self)):
                    self.vec.append(vector_type(self.id + "_" + str(i)))
        else:
            print("Creating a vector of type [None]")

    def __len__(self) -> int:
        return abs(self.startindex - self.endindex) + 1

    def get_items(self) -> List[T]:
        return self.vec

    def get_range(
        self, startindex: Optional[int] = None, endindex: Optional[int] = None
    ) -> VectorRange:
        start = startindex if startindex is not None else self.startindex
        end = endindex if endindex is not None else self.endindex
        ret = VectorRange(self, start, end)

        return ret

    def __getitem__(self, key):
        if isinstance(key, slice):
            start, stop, step = key.indices(len(self.vec))
            return [self.vec[i] for i in range(start, stop, step)]
        if key > len(self.vec) - 1:
            raise IndexError()
        return self.vec[key]

    @classmethod
    def create_from_list_things(cls, id: str, list_of_things: List):
        ret = cls(id)
        ret.vec = list_of_things
        ret.startindex = 0
        ret.endindex = len(list_of_things) - 1
        return ret
