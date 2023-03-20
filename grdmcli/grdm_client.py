import inspect  # noqa
from pprint import pprint  # noqa

from . import constants as utils  # noqa
from .common import CommonCLI


class GRDMClient(CommonCLI):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
