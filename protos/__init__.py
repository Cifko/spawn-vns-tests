if __package__ is not None and __package__ != "":
    import os, sys

    _i = os.path.dirname(os.path.abspath(__file__))
    if _i not in sys.path:
        sys.path.insert(0, _i)
    del _i  # clean up global name space
