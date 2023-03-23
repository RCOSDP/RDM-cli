import inspect  # noqa

from .common import CommonCLI
from .. import constants as utils  # noqa


class GRDMClient(CommonCLI):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # For contributors
        self.created_project_contributors = []

    # Imported methods
    from .users import (
        _users_me,
    )
    from .contributors import (
        _get_template_schema_contributors,
        _list_project_contributors,
        _delete_project_contributor,
        _prepare_project_contributor_data,
        _add_project_contributor,
        _overwrite_project_contributors,
        _clear_project_current_contributors,
        contributors_create,
    )
    template_schema_contributors = property(_get_template_schema_contributors)
