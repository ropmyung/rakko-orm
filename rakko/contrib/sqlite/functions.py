# Modified for Rakko ORM: adapt integration imports and model/query interfaces to the rakko package.

from pypika_tortoise.terms import Function


class Random(Function):
    """
    Generate random number.

    :samp:`Random()`
    """

    def __init__(self, alias=None) -> None:
        super().__init__("RANDOM", alias=alias)
