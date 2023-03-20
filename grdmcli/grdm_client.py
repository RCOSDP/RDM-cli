import inspect  # noqa
from datetime import datetime  # noqa

from . import constants as utils  # noqa
from .contributors import ContributorsCLI
from .projects import ProjectsCLI
from .projects_list import ProjectsListCli


class GRDMClient(ProjectsCLI, ContributorsCLI, ProjectsListCli):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def _projects_prepare_project_data(self, node_object, verbose=True):
        """Make a request body for the API Create new Node

        :param node_object: object of node
        :param verbose: boolean
        :return: object of request body
        """
        # print('----{}:{}::{} from {}:{}::{}'.format(*utils.inspect_info(inspect.currentframe(), inspect.stack())))

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
                    'id': _license.get('id')
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
            print(f'Prepared project data: {_data}')

        return _data
