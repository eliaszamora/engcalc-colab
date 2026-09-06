__version__ = "0.27.0"


def load_ipython_extension(ipython):
    from .magic import EngMagics
    ipython.register_magics(EngMagics)
