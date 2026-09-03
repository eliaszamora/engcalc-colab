__version__ = "0.21.0"


def load_ipython_extension(ipython):
    from .magic import EngMagics
    ipython.register_magics(EngMagics)
