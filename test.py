from enforce_typing import enforce_types
import inspect, typing

class Test:
    pass

@enforce_types
def fun(i: typing.List[typing.Dict[str, typing.Any]]) -> None:
    return # Test()

fun([{10: [10]}])
