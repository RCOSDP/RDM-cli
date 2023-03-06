import configparser
import json
import os
import sys
from argparse import Namespace
from pathlib import Path
from pprint import pprint  # noqa
from types import SimpleNamespace

import requests
import validators
from validators import ValidationFailure

from grdmcli import constants as const
from . import status


class GRDMClient(Namespace):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self._meta = {}
        self.config_file = None

        self.user = None
        self.is_authenticated = False
        self.affiliated_institutions = []
        self.affiliated_users = []

        self.projects = []

    def _request(self, method, url, params=None, data=None, headers=None):
        if isinstance(validators.url(url, public=False), ValidationFailure):
            url = f'{self.osf_api_url}{url}'

        if data is None:
            data = {}

        if headers is None:
            headers = {}

        _params = {
            const.PAGE_SIZE_QUERY_PARAM: const.MAX_PAGE_SIZE,
            const.ORDERING_QUERY_PARAM: const.ORDERING_BY,
        }

        if isinstance(params, dict):
            _params.update(params)

        headers.update({"Authorization": f"Bearer {self.osf_token}"})

        response = requests.request(method, url, params=_params, data=data, headers=headers)

        if response.status_code != status.HTTP_200_OK:
            sys.exit('TODO')

        return response

    def _check_config(self):
        """ The priority order
        - Command line arguments
        - Config file attributes
        - Environment variables
        """
        if self.is_authenticated:
            return True

        # get from config property
        # print(f'get from config property')
        if self.config_file is None:
            self.config_file = Path(os.getcwd()) / const.CONFIG_FILENAME

        if os.path.exists(self.config_file):
            config = configparser.ConfigParser()
            # print(f'config_file {self.config_file}')
            config.read(self.config_file)
            config_dict = dict(config.items(const.CONFIG_SECTION))
            if self.osf_api_url is None:
                self.osf_api_url = config_dict.get(const.OSF_API_URL_VAR_NAME.lower())
            if self.osf_token is None:
                self.osf_token = config_dict.get(const.OSF_TOKEN_VAR_NAME.lower())
        else:
            self.config_file = None

        # get from environment variable
        # print(f'get from environment variable')
        if self.osf_api_url is None:
            self.osf_api_url = os.environ.get(const.OSF_API_URL_VAR_NAME)
        if self.osf_token is None:
            self.osf_token = os.environ.get(const.OSF_TOKEN_VAR_NAME)

        if isinstance(validators.url(self.osf_api_url, public=False), ValidationFailure):
            sys.exit('The API URL is invalid')

        if not self.osf_token:
            sys.exit('Missing Personal Access Token')

        self._users_me()

    def _users_me(self, verbose=True):
        _response = self._request('GET', 'users/me/', params={}, data={})

        # pprint(response.json())
        # Parse JSON into an object with attributes corresponding to dict keys.
        response = json.loads(_response.content, object_hook=lambda d: SimpleNamespace(**d))

        self.is_authenticated = True
        self.user = response.data

        if verbose:
            print(f'[For development]You are logged in as:')
            print(f'\'{self.user.id}\' - {self.user.attributes.email} \'{self.user.attributes.full_name}\'')

            self._users_me_affiliated_institutions()
            self._users_me_affiliated_users()

    def _users_me_affiliated_institutions(self, verbose=True):
        """For development"""
        if not self.user:
            sys.exit('Missing currently logged-in user')

        # users/{user.id}/institutions/
        _response = self._request('GET', self.user.relationships.institutions.links.related.href, params={const.ORDERING_QUERY_PARAM: 'name'})

        # pprint(response.json())
        # Parse JSON into an object with attributes corresponding to dict keys.
        response = json.loads(_response.content, object_hook=lambda d: SimpleNamespace(**d))

        self.affiliated_institutions = response.data
        _institutions_numb = response.links.meta.total
        self._meta.update({'_institutions': _institutions_numb})

        if verbose:
            print(f'[For development]List of affiliated institutions. [{_institutions_numb}]')
            for inst in self.affiliated_institutions:
                print(f'\'{inst.id}\' - \'{inst.attributes.name}\' [{inst.type}][{inst.attributes.description[10]}...]')

    def _users_me_affiliated_users(self, verbose=True):
        """For development"""
        if not self.user:
            sys.exit('Missing currently logged-in user')
        if not self.affiliated_institutions:
            sys.exit('Missing currently logged-in user\'s affiliated institutions')

        _users_numb = 0

        for inst in self.affiliated_institutions:
            # institutions/{inst.id}/users/
            _response = self._request('GET', inst.relationships.users.links.related.href, params={const.ORDERING_QUERY_PARAM: 'full_name'})

            # pprint(response.json())
            # Parse JSON into an object with attributes corresponding to dict keys.
            response = json.loads(_response.content, object_hook=lambda d: SimpleNamespace(**d))

            self.affiliated_users.extend(response.data)
            _users_numb = _users_numb + response.links.meta.total

        self._meta.update({'_users': _users_numb})

        if verbose:
            print(f'[For development]List of affiliated users. [{_users_numb}]')
            for user in self.affiliated_users:
                print(f'\'{user.id}\' - \'{user.attributes.full_name}\'')

    def projects_list(self, verbose=True):
        """For development"""
        self._check_config()

        print(f'[For development]GET List of projects')
        _response = self._request('GET', 'nodes/', params={const.ORDERING_QUERY_PARAM: 'title'}, data={}, )

        # pprint(response.json())
        # Parse JSON into an object with attributes corresponding to dict keys.
        response = json.loads(_response.content, object_hook=lambda d: SimpleNamespace(**d))

        self.projects = response.data
        _projects_numb = response.links.meta.total
        self._meta.update({'_projects': _projects_numb})

        if verbose:
            print(f'[For development]List of projects are those which are public or which the user has access to view. [{_projects_numb}]')
            for project in self.projects:
                print(f'\'{project.id}\' - \'{project.attributes.title}\' [{project.type}][{project.attributes.category}]')

    def projects_contributors_list(self):
        """For development"""
        self._check_config()

        print(f'GET List of contributors')
        sys.exit(f'TODO {__name__}')

    def projects_create(self):
        self._check_config()

        print(f'CREATE Following template of projects')
        sys.exit(f'TODO {__name__}')

    def contributors_create(self):
        self._check_config()

        print(f'CREATE Following template of contributors')
        sys.exit(f'TODO {__name__}')
