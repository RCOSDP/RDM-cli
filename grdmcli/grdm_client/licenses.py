import inspect  # noqa
import json
import logging
import sys
from datetime import datetime  # noqa
from pprint import pprint  # noqa
from types import SimpleNamespace
import math
from concurrent.futures import ThreadPoolExecutor

from .. import constants as const, utils  # noqa

__all__ = [
    '_licenses',
    '_find_license_id_from_name',
]

MSG_E001 = 'Missing currently logged-in user'

logger = logging.getLogger(__name__)


def _licenses(self, ignore_error=True, verbose=True):
    """Get list of project's license and store in the licenses property

    :param ignore_error: boolean
    :param verbose: boolean
    """
    # logger.debug('----{}:{}::{} from {}:{}::{}'.format(*utils.inspect_info(inspect.currentframe(), inspect.stack())))

    if not self.user:
        sys.exit(MSG_E001)

    logger.info('Get list of licenses')
    _licenses = []
    _licenses_numb = 0

    # get first time to get page_count and total
    params = {const.ORDERING_QUERY_PARAM: 'name'}
    _response, _error_message = self._request('GET', 'licenses/', params=params, data={}, )
    if _error_message:
        logger.warning(_error_message)
        if not ignore_error:
            sys.exit(_error_message)
        return False

    response = json.loads(_response.content, object_hook=lambda d: SimpleNamespace(**d))

    _licenses_numb = response.links.meta.total
    data_per_page = response.links.meta.per_page
    page_count = math.ceil(_licenses_numb / data_per_page)
    _licenses.extend(response.data)

    # if first time get is not get all data, will use thread to call api get all
    if (page_count > 1):
        urls = [f'licenses/?page={current_page}' for current_page in range(2, page_count + 1)]

        # initialize ThreadPoolExecutor and use it to call api multi time
        with ThreadPoolExecutor(max_workers = const.MAX_THREADS_CALL_API) as executor:
            responses = list(executor.map(lambda url: self.parse_api_response('GET', url), urls))
            for res in responses:
                _licenses.extend(res.data)

    self.licenses = _licenses
    self._meta.update({'_licenses': _licenses_numb})

    logger.info(f'List of licenses. [{_licenses_numb}]')
    if verbose:
        for _license in self.licenses:
            logger.debug(f'\'{_license.id}\' - \'{_license.attributes.name}\' [{_license.type}]')


def _find_license_id_from_name(self, name, verbose=True):
    """Find the licence in the available list of node license by name and return the id.\n
    The name comparison is case-insensitive.

    :param name: string of license name
    :param verbose: boolean
    :return: license id
    :raise: GrdmCliException
    """
    if not (hasattr(self, 'licenses') and self.licenses):
        self._licenses(ignore_error=True, verbose=verbose)

    for _license in self.licenses:
        if _license.attributes.name.casefold() == name.casefold():
            return _license.id

    logger.warning(f'License name \'{name}\' is not registered.')

    return None
