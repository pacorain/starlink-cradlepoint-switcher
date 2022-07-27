from typing import Any, Awaitable, Union


class asyncproperty(property):
    def __get__(self, __obj: Any, __type: Union[Any, None]) -> Awaitable[Any]:
        aw = self.fget(__obj)
        return aw

    def __set__(self, __obj: Any, __value: Any) -> Awaitable[None]:
        aw = self.fset(__obj, __value)
        return aw

    def __delete__(self, __obj: Any) -> Awaitable[None]:
        aw = self.fdel(__obj)
        return aw
