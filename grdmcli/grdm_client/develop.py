import inspect  # noqa
import json
import logging
import sys
from datetime import datetime  # noqa
from pprint import pprint  # noqa
from types import SimpleNamespace

from .. import constants as const, utils  # noqa

__all__ = [
    '_delete_project',
    'projects_list',
    'projects_delete',
]
MSG_E001 = 'Missing currently logged-in user'

# [For development]
IS_CLEAR = True
IGNORE_PROJECTS = [
    'z6dne', 'ega24', 'm7ah9', '4hexc',
    '3hzsb', 'pcth2',  # 004 private
    '2naek', '78fea',  # fork of 004 private
    'be43a', 'be43a',  # template by 004 private
    'zgpjs', 'be43a',  # template by 004 private
]

logger = logging.getLogger(__name__)


def _delete_project(self, pk, ignore_error=True, verbose=True):
    """For development"""
    # logger.debug('----{}:{}::{} from {}:{}::{}'.format(*utils.inspect_info(inspect.currentframe(), inspect.stack())))

    logger.info(f'Remove project node/\'{pk}\'/')
    _response, _error_message = self._request('DELETE', 'nodes/{node_id}/'.format(node_id=pk), params={}, data={}, )
    if _error_message:
        logger.warning(f'{_error_message}')
        if not ignore_error:
            sys.exit(_error_message)
        return False

    logger.info(f'Deleted project: node/\'{pk}\'/')


def projects_list(self, ignore_error=True):
    """For development"""
    # logger.debug('----{}:{}::{} from {}:{}::{}'.format(*utils.inspect_info(inspect.currentframe(), inspect.stack())))
    verbose = self.verbose

    logger.info(f'Check config and authenticate by token')
    self._check_config()

    # [For development]
    if const.DEBUG:
        self._users_me_affiliated_institutions(ignore_error=True, verbose=verbose)
        self._users_me_affiliated_users(ignore_error=True, verbose=verbose)
        self._licenses(ignore_error=True, verbose=verbose)

    logger.info(f'Get list of projects')
    params = {const.ORDERING_QUERY_PARAM: 'title'}
    _response, _error_message = self._request('GET', 'nodes/', params=params, data={}, )
    if _error_message:
        logger.warning(f'{_error_message}')
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

    logger.info(f'List of projects are those which are public or which the user has access to view. [{_projects_numb}]')
    if verbose:
        for project in self.projects:
            tags_info = f'[{project.type}][{project.attributes.category}]{project.attributes.tags}'
            logger.debug(f'\'{project.id}\' - \'{project.attributes.title}\' {tags_info}')
            if IS_CLEAR and project.id not in IGNORE_PROJECTS:
                self._delete_project(project.id, ignore_error=True, verbose=verbose)

    sys.exit(0)


def projects_delete(self, ignore_error=True):
    """For development"""
    # logger.debug('----{}:{}::{} from {}:{}::{}'.format(*utils.inspect_info(inspect.currentframe(), inspect.stack())))
    verbose = self.verbose

    logger.info('Check config and authenticate by token')
    self._check_config()

    try:
        projects = [
        ]
        for project in projects:
            self._delete_project(project, ignore_error=True, verbose=verbose)

        sys.exit(0)
    except Exception as err:
        # logger.error(err)
        sys.exit(err)
