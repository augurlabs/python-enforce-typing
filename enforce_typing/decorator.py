import typing
import inspect
from contextlib import suppress
from functools import wraps

extra_info = []

def enforce_types(wrapped):
    spec = inspect.getfullargspec(wrapped)

    def strip_type_string(type_hint):
        return str(type_hint).replace("typing.", "")

    def check_type(type_hint, value):
        # We don't need to check for Any type
        if type_hint is typing.Any:
            return True
        elif (type_hint is None) and (value is not None):
            return False
        elif type_hint is None:
            return True

        type_origin = typing.get_origin(type_hint)

        if type_origin is not None: # the type hint is of a compound type
            if type_origin is not type(value):
                # the containing type for the type hint is not the same as the
                # type of the value
                return False

            # If the type is subscripted, we will get a tuple of the types here
            type_args = typing.get_args(type_hint)

            # There are no type arguments for this compound type, so no further
            # checking is needed
            if len(type_args) == 0:
                return True

            if isinstance(value, list):
                # The type arguments for the list type is a tuple with one value
                target_type = type_args[0]
                for index, element in enumerate(value):
                    if not check_type(target_type, element):
                        extra_info.append(f"type mismatch for element at index {index}")
                        return False

            elif isinstance(value, tuple):
                # The type of a tuple is a tuple of the types of each of its
                # elements. They must be the same length
                if len(value) != len(type_args):
                    extra_info.append(f"tuple contains an incorrect number of arguments")
                    extra_info.append(f"expected {len(type_args)}, got {len(value)}")
                    return False

                # create a list of tuples from the types and values of the tuple
                for index, (target_type, element) in enumerate(zip(type_args, value)):
                    if not check_type(target_type, element):
                        extra_info.append(f"type mismatch for element of tuple at index {index}")
                        return False

            elif isinstance(value, dict):
                key_type, elem_type = type_args
                for key, elem in value.items():
                    if (not check_type(key_type, key)) or (not check_type(elem_type, elem)):
                        extra_info.append(f"type mismatch for dictionary key value pair")
                        return False

            elif isinstance(value, typing.Union):
                # The value must match at least one the types in the union args
                return isinstance(value, type_args)
            else:
                # Other types not supported for now
                extra_info.append(f"Type checking for {type(value)} is currently unsupported")
                return False
            return True
        else:
            if isinstance(value, type_hint):
                return True
            else:
                extra_info.append(f"expected type {strip_type_string(type_hint)}, got type {type(value)}")

    def check_types(*args, **kwargs):
        params = dict(zip(spec.args, args))
        params.update(kwargs)
        for name, value in params.items():
            with suppress(KeyError):
                type_hint = spec.annotations[name]
                if not check_type(type_hint, value):
                    # for information in extra_info:
                    #     print(information)
                    extra_info.clear()
                    raise TypeError(f"Expected type '{strip_type_string(type_hint)}' for attribute '{name}' but received type '{type(value)}'")

    def decorate(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            check_types(*args, **kwargs)
            result = func(*args, **kwargs)
            return_type = inspect.signature(func).return_annotation
            if not check_type(return_type, result):
                # for information in extra_info:
                #     print(information)
                raise TypeError(f"Expected type '{return_type}' for return value, but received type '{type(result)}')")

        return wrapper

    if inspect.isclass(wrapped):
        wrapped.__init__ = decorate(wrapped.__init__)
        return wrapped

    return decorate(wrapped)
