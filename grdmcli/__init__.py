import os

__all__ = [
    '__version__',
]

here = os.path.abspath(os.path.dirname(__file__))

with open(os.path.join(os.path.dirname(here), 'VERSION'), encoding='utf-8') as version_file:
    """Read version from file."""
    __version__ = version_file.read().strip()
