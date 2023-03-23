import inspect  # noqa
import json
import sys
from datetime import datetime  # noqa
from pprint import pprint  # noqa
from types import SimpleNamespace

from .. import constants as const, utils  # noqa

__all__ = [
    '_delete_project',
    'projects_list',
]
MSG_E001 = 'Missing currently logged-in user'

# [For development]
DEBUG = True
IS_CLEAR = True
IGNORE_PROJECTS = [
    'z6dne', 'ega24', 'm7ah9', '4hexc',
    '3hzsb', 'pcth2',  # 004 private
    '2naek', '78fea',  # fork of 004 private
    'be43a', 'be43a',  # template by 004 private
    'zgpjs', 'be43a',  # template by 004 private
]


def _delete_project(self, pk, ignore_error=True, verbose=True):
    """For development"""
    # print('----{}:{}::{} from {}:{}::{}'.format(*utils.inspect_info(inspect.currentframe(), inspect.stack())))

    print(f'DELETE Remove project \'{pk}\'')
    _response, _error_message = self._request('DELETE', 'nodes/{node_id}/'.format(node_id=pk), params={}, data={}, )
    if _error_message:
        print(f'WARN {_error_message}')
        if not ignore_error:
            sys.exit(_error_message)
        return False

    if verbose:
        print(f'Deleted project: \'{pk}\'')


def projects_list(self, ignore_error=True, verbose=True):
    """For development"""
    # print('----{}:{}::{} from {}:{}::{}'.format(*utils.inspect_info(inspect.currentframe(), inspect.stack())))

    print(f'Check config and authenticate by token')
    self._check_config()

    # [For development]
    if DEBUG:
        self._users_me_affiliated_institutions(ignore_error=True, verbose=True)
        self._users_me_affiliated_users(ignore_error=True, verbose=True)
        self._licenses(ignore_error=True, verbose=True)

    print(f'[For development]GET List of projects')
    params = {const.ORDERING_QUERY_PARAM: 'title'}
    _response, _error_message = self._request('GET', 'nodes/', params=params, data={}, )
    if _error_message:
        print(f'WARN {_error_message}')
        if not ignore_error:
            sys.exit(_error_message)
        return None, None
    _content = _response.content

    # pprint(_response.json())
    # Parse JSON into an object with attributes corresponding to dict keys.
    response = json.loads(_content, object_hook=lambda d: SimpleNamespace(**d))

    self.projects = response.data
    _projects_numb = response.links.meta.total
    self._meta.update({'_projects': _projects_numb})

    if verbose:
        print(f'[For development]List of projects are those which are public or which the user has access to view. [{_projects_numb}]')
        for project in self.projects:
            print(f'\'{project.id}\' - \'{project.attributes.title}\' [{project.type}][{project.attributes.category}]{project.attributes.tags}')
            if IS_CLEAR and project.id not in IGNORE_PROJECTS:
                self._delete_project(project.id, ignore_error=True, verbose=False)

    sys.exit(0)
