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
    '_users_institutions',
]
MSG_E001 = 'Missing currently logged-in user'
MSG_E002 = 'Invalid institutions response format. Expected "data" as a list of objects with "id" and "type".'

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


def _users_institutions(self, verbose=True):
    """Get institution relationships of the currently logged-in user.

    :param verbose: boolean
    :return: list of institutions
    """
    if not self.user:
        logger.warning(MSG_E001)
        sys.exit(MSG_E001)

    _url = f'users/{self.user.id}/relationships/institutions/'
    _response, _error_message = self._request('GET', _url, params={}, data={})
    if _error_message:
        logger.warning(_error_message)
        sys.exit(_error_message)

    _content = _response.content
    response_json = json.loads(_content)
    institutions = response_json.get('data')
    if not isinstance(institutions, list):
        logger.warning(MSG_E002)
        sys.exit(MSG_E002)

    for idx, institution in enumerate(institutions):
        if not isinstance(institution, dict) or not institution.get('id') or not institution.get('type'):
            _error_message = f'{MSG_E002} Invalid item at index {idx}.'
            logger.warning(_error_message)
            sys.exit(_error_message)

    self.affiliated_institutions = institutions

    if verbose and self.affiliated_institutions:
        logger.debug(f'Found affiliated institutions. [{len(self.affiliated_institutions)}]')

    return self.affiliated_institutions
