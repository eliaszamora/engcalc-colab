__version__ = "0.3.1"


def load_ipython_extension(ipython):
    from .magic import EngMagics
    ipython.register_magics(EngMagics)
