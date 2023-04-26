import inspect  # noqa
import json
import logging
import sys
from datetime import datetime  # noqa
from pprint import pprint  # noqa
from types import SimpleNamespace

from .. import constants as const, utils  # noqa

__all__ = [
    '_users_me',
    '_users_me_affiliated_institutions',
    '_users_me_affiliated_users',
]
MSG_E001 = 'Missing currently logged-in user'

logger = logging.getLogger(__name__)


def _users_me(self, ignore_error=True, verbose=True):
    """Get the currently logged-in user

    :param ignore_error: boolean
    :param verbose: boolean
    :return: None
    """
    # logger.debug('----{}:{}::{} from {}:{}::{}'.format(*utils.inspect_info(inspect.currentframe(), inspect.stack())))

    logger.info('Get the currently logged-in user')
    _response, _error_message = self._request('GET', 'users/me/', params={}, data={})
    if _error_message:
        logger.warning(_error_message)
        if not ignore_error:
            sys.exit(_error_message)
        return False
    _content = _response.content

    # pprint(_response.json())
    # Parse JSON into an object with attributes corresponding to dict keys.
    response = json.loads(_content, object_hook=lambda d: SimpleNamespace(**d))

    self.is_authenticated = True
    self.user = response.data

    logger.info(f'You are logged in as \'{self.user.id}\'')
    if verbose:
        logger.debug(f'\'{self.user.id}\' - \'{self.user.attributes.full_name}\'')


def _users_me_affiliated_institutions(self, ignore_error=True, verbose=True):
    """For development"""
    # logger.debug('----{}:{}::{} from {}:{}::{}'.format(*utils.inspect_info(inspect.currentframe(), inspect.stack())))

    if not self.user:
        sys.exit(MSG_E001)

    # users/{user.id}/institutions/
    params = {const.ORDERING_QUERY_PARAM: 'name'}
    _response, _error_message = self._request('GET', self.user.relationships.institutions.links.related.href, params=params)
    if _error_message:
        logger.warning(_error_message)
        if not ignore_error:
            sys.exit(_error_message)
        return False
    _content = _response.content

    # pprint(_response.json())
    # Parse JSON into an object with attributes corresponding to dict keys.
    response = json.loads(_content, object_hook=lambda d: SimpleNamespace(**d))

    self.affiliated_institutions = response.data
    _institutions_numb = response.links.meta.total
    self._meta.update({'_institutions': _institutions_numb})

    logger.info(f'List of affiliated institutions. [{_institutions_numb}]')
    if verbose:
        for inst in self.affiliated_institutions:
            logger.debug(f'\'{inst.id}\' - \'{inst.attributes.name}\' [{inst.type}][{inst.attributes.description[:10]}...]')


def _users_me_affiliated_users(self, ignore_error=True, verbose=True):
    """For development"""
    # logger.debug('----{}:{}::{} from {}:{}::{}'.format(*utils.inspect_info(inspect.currentframe(), inspect.stack())))

    if not self.user:
        sys.exit(MSG_E001)

    if not self.affiliated_institutions:
        sys.exit('Missing currently logged-in user\'s affiliated institutions')

    _users_numb = 0

    for inst in self.affiliated_institutions:
        # institutions/{inst.id}/users/
        params = {const.ORDERING_QUERY_PARAM: 'full_name'}
        _response, _error_message = self._request('GET', inst.relationships.users.links.related.href, params=params)
        if _error_message:
            logger.warning(_error_message)
            if not ignore_error:
                sys.exit(_error_message)
            return False
        _content = _response.content

        # pprint(_response.json())
        # Parse JSON into an object with attributes corresponding to dict keys.
        response = json.loads(_content, object_hook=lambda d: SimpleNamespace(**d))

        self.affiliated_users.extend(response.data)
        _users_numb = _users_numb + response.links.meta.total

    self._meta.update({'_users': _users_numb})

    logger.info(f'List of affiliated institutions\' users. [{_users_numb}]')
    if verbose:
        for user in self.affiliated_users:
            logger.debug(f'\'{user.id}\' - \'{user.attributes.full_name}\'')
