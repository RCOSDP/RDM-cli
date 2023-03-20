import configparser
import inspect  # noqa
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

from . import constants as const, status, utils  # noqa

here = os.path.abspath(os.path.dirname(__file__))


class CommonCLI(Namespace):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self._meta = {}
        self.template = './template_file.json'
        self.output_result_file = './output_result_file.json'

        self.user = None
        self.is_authenticated = False

    @property
    def config_file(self):
        return Path(os.getcwd()) / const.CONFIG_FILENAME

    @property
    def has_required_attributes(self):
        return self.osf_token is not None and self.osf_api_url is not None

    def _request(self, method, url, params=None, data=None, headers=None):
        """Make a request

        :param method: string
        :param url: string of URL; will be validated
        :param params: dictionary of query parameters needed to update
        :param data: dictionary of request body
        :param headers: dictionary of request headers
        :return: response data, and the first error message
        """
        # print('----{}:{}::{} from {}:{}::{}'.format(*utils.inspect_info(inspect.currentframe(), inspect.stack())))

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

        headers.update({
            "Authorization": f"Bearer {self.osf_token}",
            "Content-Type": "application/json",
        })

        _response = requests.request(method, url, params=_params, data=json.dumps(data), headers=headers)

        if not status.is_success(_response.status_code):
            # pprint(_response.json())
            # Parse JSON into an object with attributes corresponding to dict keys.
            response = json.loads(_response.content, object_hook=lambda d: SimpleNamespace(**d))
            # print(f'WARN Exception: {response.errors[0].detail}')
            return None, response.errors[0].detail

        return _response, None

    def _load_required_attributes_from_config_file(self):
        """Update osf_api_url and osf_token from configuration file

        :return: None
        """
        if not os.path.exists(self.config_file):
            print(f'Missing the config file {self.config_file}')
            return False

        print(f'Read config_file: {self.config_file}')
        config = configparser.ConfigParser()
        config.read(self.config_file)
        config_dict = dict(config.items(const.CONFIG_SECTION))
        # get osf_api_url
        if self.osf_api_url is None:
            self.osf_api_url = config_dict.get(const.OSF_API_URL_VAR_NAME.lower())
        # get osf_token
        if self.osf_token is None:
            self.osf_token = config_dict.get(const.OSF_TOKEN_VAR_NAME.lower())

    def _load_required_attributes_from_environment(self):
        """Update osf_api_url and osf_token from environment variables

        :return: None
        """
        if self.osf_api_url is None:
            self.osf_api_url = os.environ.get(const.OSF_API_URL_VAR_NAME)
        if self.osf_token is None:
            self.osf_token = os.environ.get(const.OSF_TOKEN_VAR_NAME)

    def _check_config(self, verbose=True):
        """The priority order\n
        - Command line arguments\n
        - Config file attributes\n
        - Environment variables\n

        :param verbose:
        :return: None
        """
        # print('----{}:{}::{} from {}:{}::{}'.format(*utils.inspect_info(inspect.currentframe(), inspect.stack())))

        # ignore if user is authenticated
        if self.is_authenticated:
            return True

        if not self.has_required_attributes:
            print(f'Try get from config property')
            self._load_required_attributes_from_config_file()

        if not self.has_required_attributes:
            print(f'Try get from environment variable')
            self._load_required_attributes_from_environment()

        if not self.osf_api_url:
            sys.exit('Missing API URL')

        if isinstance(validators.url(self.osf_api_url, public=False), ValidationFailure):
            sys.exit('The API URL is invalid')

        if not self.osf_token:
            sys.exit('Missing Personal Access Token')

        if not self.is_authenticated:
            print('Check Personal Access Token')
            self._users_me(ignore_error=False, verbose=verbose)

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
