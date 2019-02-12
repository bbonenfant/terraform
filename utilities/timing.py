""" Useful classes for collecting timing information. """
from time import time
from typing import Callable, Optional


class TimingStruct:
    """ Small struct for holding timing data. """
    __slots__ = ['start', 'elapsed']

    def __init__(self):
        self.start = time()
        self.elapsed = None

    def time(self):
        """ Stop the timer. """
        self.elapsed = time() - self.start
        return self.elapsed


class TimingDict(dict):
    """
        Inherits from dict to make a simple interface for timing.

    How to use:
        Append times you want to track to the dictionary:
            ```
            time_dict = TimingDict()
            time_dict.put('a_slow_process')
            ```
        Stop the timer for an already set timer:
            ```
            time_dict.a_slow_process.time()
            ```
        Print out a tabulated form of the TimingDict:
            ```
            print(time_dict)
            ```
            "A Slow Process: 12.34s"
    """

    def __repr__(self):
        """ Prints out a table of elapsed times with nice formatting. """
        return '\n'.join([f'{name.replace("_", " ").title()}: {struct.elapsed:.2f}s'
                          for name, struct in super().items() if struct.elapsed is not None])

    def __getattr__(self, item: str):
        """ Hooks into getattr, allowing for attribute calls. """
        try:
            return super().__getitem__(item)
        except KeyError:
            raise AttributeError(item)

    def put(self, name: str):
        """ Put a 'name' into the dict as a key with value TimingStruct. """
        super().__setitem__(name, TimingStruct())

    def time(self, name: str, outer_func: Optional[Callable] = None, *outer_args, **outer_kwargs):
        """ Decorator for timing a function. Allows for function-call functionality. """
        def decorator(func: Callable):
            def wrapper(*args, **kwargs):
                """ Sets the timer, runs the function, stops the timer. """
                self.put(name)
                results = func(*args, **kwargs)
                self.get(name).time()
                return results

            # If this has been treated as a function call, we sub in the corrects args and kwargs.
            if func == outer_func:
                return wrapper(*outer_args, **outer_kwargs)
            return wrapper

        # If outer_func is defined, we treat this as a function call.
        if outer_func is not None:
            return decorator(outer_func)
        return decorator
