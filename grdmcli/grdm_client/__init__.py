import inspect  # noqa
import logging
from datetime import datetime  # noqa

from .common import CommonCLI
from .. import constants as utils  # noqa

logger = logging.getLogger(__name__)


class GRDMClient(CommonCLI):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # For development functions
        self.affiliated_institutions = []
        self.affiliated_users = []
        self.projects = []

        # For projects functions
        self.created_projects = []

        # For contributors functions
        self.created_project_contributors = []

    # # Imported methods

    from .users import (
        _users_me,
        # For development
        _users_me_affiliated_institutions,
        _users_me_affiliated_users,
    )
    # For development
    from .develop import (
        _delete_project,
        projects_list,
    )
    # For projects functions
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
    # For contributors functions
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

    # # Overwrite methods

    def _prepare_project_data(self, node_object, verbose=True):
        """Make a request body for the API Create new Node

        :param node_object: object of node
        :param verbose: boolean
        :return: object of request body
        """
        # logger.debug('----{}:{}::{} from {}:{}::{}'.format(*utils.inspect_info(inspect.currentframe(), inspect.stack())))

        _project = node_object

        # For development
        _today_str = datetime.today().strftime('%Y-%m-%d %H:%M:%S')

        # initial
        _category = _project.get('category')
        _title = _project.get('title')
        _attributes = {
            'category': _category,
            # 'title': _title,
            'title': f'[{_today_str}] {_title}',  # For development
        }
        _relationships = {}

        # update template_from
        _template_from = _project.get('template_from')
        if _template_from:
            _attributes['template_from'] = _template_from

        # update description
        _description = _project.get('description', '')
        _attributes['description'] = _description

        # update description
        _public = _project.get('public', False)
        _attributes['public'] = _public

        # update description
        _tags = _project.get('tags', [])
        _attributes['tags'] = _tags

        # update node_license
        _license = _project.get('node_license')
        if _license:
            # required 'id'
            _relationships['license'] = {
                'data': {
                    'type': 'licenses',
                    'id': self._find_license_id_from_name(_license.get('license_name'))
                }
            }
            # required 'copyright_holders' and 'year'
            _attributes['node_license'] = {
                'copyright_holders': _license.get('copyright_holders'),
                'year': _license.get('year')
            }

        _data = {
            'data': {
                'type': 'nodes',
                'attributes': _attributes,
                'relationships': _relationships
            }
        }

        if verbose:
            logger.debug(f'Prepared project data: {_data}')

        return _data
