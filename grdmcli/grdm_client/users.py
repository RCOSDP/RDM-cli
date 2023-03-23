import inspect  # noqa
import json
import sys
from datetime import datetime  # noqa
from pprint import pprint  # noqa
from types import SimpleNamespace

from .. import constants as const, utils  # noqa

__all__ = [
    '_users_me',
]
MSG_E001 = 'Missing currently logged-in user'


def _users_me(self, ignore_error=True, verbose=True):
    """Get the currently logged-in user

    :param ignore_error: boolean
    :param verbose: boolean
    :return: None
    """
    # print('----{}:{}::{} from {}:{}::{}'.format(*utils.inspect_info(inspect.currentframe(), inspect.stack())))

    print('GET the currently logged-in user')
    _response, _error_message = self._request('GET', 'users/me/', params={}, data={})
    if _error_message:
        print(f'WARN {_error_message}')
        if not ignore_error:
            sys.exit(_error_message)
        return False
    _content = _response.content

    # pprint(_response.json())
    # Parse JSON into an object with attributes corresponding to dict keys.
    response = json.loads(_content, object_hook=lambda d: SimpleNamespace(**d))

    self.is_authenticated = True
    self.user = response.data

    if verbose:
        print(f'You are logged in as:')
        print(f'\'{self.user.id}\' - {self.user.attributes.email} \'{self.user.attributes.full_name}\'')
