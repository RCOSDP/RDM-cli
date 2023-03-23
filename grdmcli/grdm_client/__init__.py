import inspect  # noqa

from .common import CommonCLI
from .. import constants as utils  # noqa


class GRDMClient(CommonCLI):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    # Imported methods
    from .users import (
        _users_me,
    )
