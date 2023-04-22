import time
from .path import Path

def timeIt(prefix=None):
    def wrap(fn):
        def wrapped_fn(*args, **kwargs):
            ts = time.time()
            result = fn(*args, **kwargs)
            te = time.time()
            print('%r  %2.2f s' % (fn.__name__, (te - ts)))
            return result
        return wrapped_fn
    return wrap