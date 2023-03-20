import inspect  # noqa
import json
import sys
from datetime import datetime  # noqa
from pprint import pprint  # noqa
from types import SimpleNamespace

from . import constants as const, constants as utils  # noqa
from .common import CommonCLI

MSG_E001 = 'Missing currently logged-in user'

# [For development]
DEBUG = True
IS_CLEAR = True
IGNORE_PROJECTS = ['z6dne', 'ega24', 'm7ah9', '4hexc']


class ProjectsListCli(CommonCLI):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.affiliated_institutions = []  # For development
        self.affiliated_users = []  # For development
        self.projects = []  # For development

    def _users_me_affiliated_institutions(self, ignore_error=True, verbose=True):
        """For development"""
        # print('----{}:{}::{} from {}:{}::{}'.format(*utils.inspect_info(inspect.currentframe(), inspect.stack())))

        if not self.user:
            sys.exit(MSG_E001)

        # users/{user.id}/institutions/
        params = {const.ORDERING_QUERY_PARAM: 'name'}
        _response, _error_message = self._request('GET', self.user.relationships.institutions.links.related.href, params=params)
        if _error_message:
            print(f'WARN {_error_message}')
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

        if verbose:
            print(f'[For development]List of affiliated institutions. [{_institutions_numb}]')
            for inst in self.affiliated_institutions:
                print(f'\'{inst.id}\' - \'{inst.attributes.name}\' [{inst.type}][{inst.attributes.description[:10]}...]')

    def _users_me_affiliated_users(self, ignore_error=True, verbose=True):
        """For development"""
        # print('----{}:{}::{} from {}:{}::{}'.format(*utils.inspect_info(inspect.currentframe(), inspect.stack())))

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
                print(f'WARN {_error_message}')
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

        if verbose:
            print(f'[For development]List of affiliated institutions\' users. [{_users_numb}]')
            for user in self.affiliated_users:
                print(f'\'{user.id}\' - \'{user.attributes.full_name}\'')

    def _licenses(self, ignore_error=True, verbose=True):
        """For development"""
        # print('----{}:{}::{} from {}:{}::{}'.format(*utils.inspect_info(inspect.currentframe(), inspect.stack())))

        if not self.user:
            sys.exit(MSG_E001)

        print(f'[For development]GET List of licenses')
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

    def _projects_delete_project(self, pk, ignore_error=True, verbose=True):
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
                    self._projects_delete_project(project.id, ignore_error=True, verbose=False)

        sys.exit(0)
