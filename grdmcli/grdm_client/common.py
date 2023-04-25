import configparser
import inspect  # noqa
import json
import logging
import os
import sys
from argparse import Namespace
from pathlib import Path
from pprint import pprint  # noqa
from types import SimpleNamespace

import requests
import urllib3  # noqa
import validators
from validators import ValidationFailure

from .. import constants as const, status, utils  # noqa

here = os.path.abspath(os.path.dirname(__file__))

# config logging
handler = logging.StreamHandler()
formatter = logging.Formatter(const.LOGGING_FORMAT)
handler.setFormatter(formatter)
logger = logging.getLogger()
logger.propagate = False
logger.addHandler(handler)
logger.setLevel(logging.DEBUG if const.DEBUG else logging.INFO)

logging.getLogger('urllib3').setLevel(logging.DEBUG if const.DEBUG else logging.WARNING)
if const.DEBUG:
    # disable urllib3 logs
    urllib3.disable_warnings()


class CommonCLI(Namespace):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self._meta = {}
        self.config_default = {}
        self.template = const.TEMPLATE_FILE_NAME_DEFAULT
        self.output_result_file = const.OUTPUT_RESULT_FILE_NAME_DEFAULT

        self.user = None
        self.is_authenticated = False

        # Call initial methods before parse_args
        self._load_option_from_config_file()

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
        # logger.debug('----{}:{}::{} from {}:{}::{}'.format(*utils.inspect_info(inspect.currentframe(), inspect.stack())))

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
        ssl_options = {
            'verify': False
        }
        if self.ssl_cert_verify:
            ssl_options['verify'] = self.ssl_cert_verify
            if const.SSL_CERT_FILE:
                ssl_options['cert'] = const.SSL_CERT_FILE
                if const.SSL_KEY_FILE:
                    ssl_options['cert'] = (const.SSL_CERT_FILE, const.SSL_KEY_FILE)

        _response = requests.request(method, url,
                                     params=_params, data=json.dumps(data), headers=headers,
                                     **ssl_options)

        if not status.is_success(_response.status_code):
            try:
                # pprint(_response.json())
                # Parse JSON into an object with attributes corresponding to dict keys.
                response = json.loads(_response.content, object_hook=lambda d: SimpleNamespace(**d))
                error = response.errors[0]
                error_msg = error.detail
                if hasattr(error, 'source'):
                    error_msg = f'{error_msg}. The pointer is {error.source.pointer}'
            except Exception:
                error_msg = f'{_response.status_code} {_response.reason}'

            return None, error_msg

        return _response, None

    def _load_option_from_config_file(self):
        """Load config option from configuration file

        :return: None
        """
        if not os.path.exists(self.config_file):
            logger.warning(f'Missing the config file {self.config_file}')
            return False

        config = configparser.ConfigParser()
        config.read(self.config_file)
        if const.CONFIG_SECTION in config:
            self.config_default = config[const.CONFIG_SECTION]

        # get ssl_cert_verify
        self.ssl_cert_verify = self.config_default.getboolean(const.SSL_CERT_VERIFY_VAR_NAME.lower(),
                                                              const.SSL_CERT_VERIFY)
        # get debug
        self.debug = self.config_default.getboolean(const.DEBUG_VAR_NAME.lower(), const.DEBUG)
        # get verbose
        self.verbose = self.config_default.getboolean(const.VERBOSE_VAR_NAME.lower(), const.VERBOSE)

        if self.debug:
            logger.setLevel(logging.DEBUG)
            # disable urllib3 logs
            urllib3.disable_warnings()

    def _load_required_attributes_from_config_file(self):
        """Update osf_api_url and osf_token from configuration file

        :return: None
        """
        logger.info(f'Read config_file: {self.config_file}')

        # get osf_api_url
        if self.osf_api_url is None:
            self.osf_api_url = self.config_default.get(const.OSF_API_URL_VAR_NAME.lower())
        # get osf_token
        if self.osf_token is None:
            self.osf_token = self.config_default.get(const.OSF_TOKEN_VAR_NAME.lower())

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
        # logger.debug('----{}:{}::{} from {}:{}::{}'.format(*utils.inspect_info(inspect.currentframe(), inspect.stack())))

        # ignore if user is authenticated
        if self.is_authenticated:
            return True

        if not self.has_required_attributes:
            logger.info('Try get from config property')
            self._load_required_attributes_from_config_file()

        if not self.has_required_attributes:
            logger.info('Try get from environment variable')
            self._load_required_attributes_from_environment()

        if not self.osf_api_url:
            sys.exit('Missing API URL')

        if isinstance(validators.url(self.osf_api_url, public=False), ValidationFailure):
            sys.exit('The API URL is invalid')

        if not self.osf_token:
            sys.exit('Missing Personal Access Token')

        if not self.is_authenticated:
            logger.info('Check Personal Access Token')
            self._users_me(ignore_error=False, verbose=verbose)

    def _prepare_output_file(self):
        """Create directory for output result if it's not existing

        :return: None
        """
        # prepare output file
        if not os.path.exists(self.output_result_file):
            _directory = os.path.abspath(os.path.join(self.output_result_file, os.pardir))
            if not os.path.isdir(_directory):
                Path(_directory).mkdir(parents=True, exist_ok=True)
                logger.info(f'The new directory \'{_directory}\' is created.')

    def force_update_config(self):
        """ Force update optional config items according the flags from command line arguments

        :return: None
        """
        if self.enable_debug:
            self.debug = True
            logger.setLevel(logging.DEBUG)
            # disable urllib3 logs
            urllib3.disable_warnings()

        if self.enable_verbose:
            self.verbose = True

        if self.disable_ssl_verify:
            self.ssl_cert_verify = False
