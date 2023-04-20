import inspect  # noqa
import logging

from .common import CommonCLI
from .. import constants as utils  # noqa

logger = logging.getLogger(__name__)


class GRDMClient(CommonCLI):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # For projects functions
        self.created_projects = []

    # # Imported methods

    from .users import (
        _users_me,
    )
    from .licenses import (
        _licenses,
        _find_license_id_from_name,
    )
    from .projects import (
        _get_template_schema_projects,
        _fake_project_content_data,
        _prepare_project_data,
        _load_project,
        _fork_project,
        _create_project,
        _link_project_to_project,
        _add_project_pointers,
        _add_project_components,
        _projects_add_component,
        _create_or_load_project,
        projects_create,
    )
    template_schema_projects = property(_get_template_schema_projects)

    # # Overwrite methods
