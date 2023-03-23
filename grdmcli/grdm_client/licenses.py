import inspect  # noqa
import json
import sys
from datetime import datetime  # noqa
from pprint import pprint  # noqa
from types import SimpleNamespace

from .. import constants as const, utils  # noqa

from ..exceptions import GrdmCliException

__all__ = [
    '_licenses',
    '_find_license_id_from_name',
]

MSG_E001 = 'Missing currently logged-in user'


def _licenses(self, ignore_error=True, verbose=True):
    """For development"""
    # print('----{}:{}::{} from {}:{}::{}'.format(*utils.inspect_info(inspect.currentframe(), inspect.stack())))

    if not self.user:
        sys.exit(MSG_E001)

    print(f'GET List of licenses')
    params = {const.ORDERING_QUERY_PARAM: 'name'}
    _response, _error_message = self._request('GET', 'licenses/', params=params, data={}, )
    if _error_message:
        print(f'WARN {_error_message}')
        if not ignore_error:
            sys.exit(_error_message)
        return False
    _content = _response.content

    # pprint(_response.json())
    # Parse JSON into an object with attributes corresponding to dict keys.
    response = json.loads(_content, object_hook=lambda d: SimpleNamespace(**d))

    self.licenses = response.data
    _licenses_numb = response.links.meta.total
    self._meta.update({'_licenses': _licenses_numb})

    if verbose:
        print(f'[For development]List of licenses. [{_licenses_numb}]')
        for _license in self.licenses:
            print(f'\'{_license.id}\' - \'{_license.attributes.name}\' [{_license.type}]')


def _find_license_id_from_name(self, name, verbose=True):
    if not hasattr(self, 'licenses') or not self.licenses or len(self.licenses):
        self._licenses(ignore_error=True, verbose=False)

    for _license in self.licenses:
        if _license.attributes.name == name:
            return _license.id

    raise GrdmCliException(f'License name \'{name}\' is not registered.')

