import configparser
import json
import logging
import os
from unittest import mock
from types import SimpleNamespace

import pytest
import requests

from grdmcli.grdm_client.common import CommonCLI
from tests.factories import CommonCLIFactory
from tests.utils import *


@pytest.fixture
def common_cli():
    args = {'osf_token': 'osf-token',
            'osf_api_url': 'http://localhost:8000/v2/',
            'ssl_cert_verify': True,
            'enable_debug': True,
            'enable_verbose': True}
    return CommonCLIFactory(**args)


class TestCommonCLI:
    url = 'https://api.test.osf.io/v2/nodes/{node_id}/projects/'.format(node_id='abc32')
    args = {'osf_token': 'osf-token', 'osf_api_url': 'http://localhost:8000/v2/', 'ssl_cert_verify': False}
    common_cli = CommonCLI(**args)

    @pytest.fixture(autouse=True)
    def set_log_level(self, caplog):
        caplog.clear()
        caplog.set_level(logging.DEBUG)

    def test_init__normal(self):
        assert self.common_cli.is_authenticated is False
        assert self.common_cli.user is None
        assert self.common_cli.template == './template_file.json'
        assert self.common_cli.output_result_file == './output_result_file.json'
        assert self.common_cli._meta == {}
        assert self.common_cli.config_file is not None
        assert self.common_cli.has_required_attributes is True

    def test_init__osf_token_is_none(self):
        self.common_cli.osf_token = None
        assert self.common_cli.is_authenticated is False
        assert self.common_cli.user is None
        assert self.common_cli.template == './template_file.json'
        assert self.common_cli.output_result_file == './output_result_file.json'
        assert self.common_cli._meta == {}
        assert self.common_cli.config_file is not None
        assert self.common_cli.has_required_attributes is False

    def test_init__osf_api_url_is_none(self):
        self.common_cli.osf_api_url = None
        assert self.common_cli.is_authenticated is False
        assert self.common_cli.user is None
        assert self.common_cli.template == './template_file.json'
        assert self.common_cli.output_result_file == './output_result_file.json'
        assert self.common_cli._meta == {}
        assert self.common_cli.config_file is not None
        assert self.common_cli.has_required_attributes is False

    def test_init__has_required_attributes_false(self):
        self.common_cli.osf_token = None
        self.common_cli.osf_api_url = None
        assert self.common_cli.is_authenticated is False
        assert self.common_cli.user is None
        assert self.common_cli.template == './template_file.json'
        assert self.common_cli.output_result_file == './output_result_file.json'
        assert self.common_cli._meta == {}
        assert self.common_cli.config_file is not None
        assert self.common_cli.has_required_attributes is False

    @mock.patch('requests.request')
    def test_request__not_success(self, mock_get, common_cli):
        resp = requests.Response()
        resp._content = json.dumps({'errors': [{'detail': 'mock error'}]})
        resp.status_code = 400
        mock_get.return_value = resp
        actual1, actual2 = CommonCLI._request(common_cli, 'GET', self.url)
        assert actual1 is None
        assert actual2 == 'mock error'

    @mock.patch('requests.request')
    def test_request__error_exception(self, mock_get, common_cli):
        resp = requests.Response()
        resp.reason = 'system error'
        resp.status_code = 500
        mock_get.return_value = resp
        actual1, actual2 = CommonCLI._request(common_cli, 'GET', self.url)
        assert actual1 is None
        assert actual2 == f'{resp.status_code} {resp.reason}'

    @mock.patch('requests.request')
    def test_request__error_source(self, mock_get, common_cli):
        resp = requests.Response()
        resp._content = """{
            "errors": [
                {
                    "source": {
                        "pointer": "/data"
                    },
                    "detail": "Request must include /data.",
                    "meta": {}
                }
            ]
        }"""
        resp.status_code = 400
        mock_get.return_value = resp
        actual1, actual2 = CommonCLI._request(common_cli, 'GET', self.url)
        assert actual1 is None
        assert actual2 == f'Request must include /data.. The pointer is /data'

    @mock.patch('requests.request')
    def test_request__success(self, mock_get, common_cli):
        resp = requests.Response()
        resp._content = 'success'
        resp.status_code = 200
        mock_get.return_value = resp
        actual1, actual2 = CommonCLI._request(common_cli, 'GET', self.url, {})
        assert actual1 == resp
        assert actual2 is None

    @mock.patch('requests.request')
    @mock.patch('grdmcli.constants.SSL_CERT_FILE', 'ssl-cert-string')
    @mock.patch('grdmcli.constants.SSL_KEY_FILE', 'ssl-key-string')
    def test_request__success_with_ssl_cert_verify_is_true(self, mock_get, common_cli):
        common_cli.ssl_cert_verify = True
        resp = requests.Response()
        resp._content = 'success'
        resp.status_code = 200
        mock_get.return_value = resp
        actual1, actual2 = CommonCLI._request(common_cli, 'GET', self.url, {})
        assert actual1 == resp
        assert actual2 is None

    @mock.patch('requests.request')
    def test_request__url_invalid(self, mock_get, common_cli):
        resp = requests.Response()
        resp._content = 'success'
        resp.status_code = 200
        mock_get.return_value = resp
        actual1, actual2 = CommonCLI._request(common_cli, 'GET', 'test', {})
        assert actual1 == resp
        assert actual2 is None

    @mock.patch("os.path.exists", return_value=False)
    def test_load_option_from_config_file__return_false(self, common_cli, caplog):
        actual = CommonCLI._load_option_from_config_file(common_cli)
        assert caplog.records[0].levelname == warning_level_log
        assert caplog.records[0].message == f'Missing the config file {common_cli.config_file}'
        assert len(caplog.records) == 1
        assert actual is False

    @mock.patch("os.path.exists", return_value=True)
    @mock.patch('grdmcli.constants.CONFIG_SECTION', 'default')
    def test_load_option_from_config_file__update(self, mocker, common_cli):
        config = configparser.ConfigParser()
        config.read_dict({"default": {'osf_token': 'access-token-update',
                                      'osf_api_url': 'http://localhost:8001/v2/',
                                      'ssl_cert_verify': True,
                                      'debug': True,
                                      'verbose': True}})
        mock_parser = mock.MagicMock(return_value=config)
        with mock.patch("configparser.ConfigParser", mock_parser):
            CommonCLI._load_option_from_config_file(common_cli)
        assert common_cli.ssl_cert_verify
        assert common_cli.debug

    def test_load_required_from_config_file__update(self, common_cli, caplog):
        common_cli.osf_api_url = None
        common_cli.osf_token = None
        common_cli.config_default = {'osf_token': 'access-token-update',
                                     'osf_api_url': 'http://localhost:8001/v2/',
                                     'ssl_cert_verify': True,
                                     'debug': True,
                                     'verbose': True}
        CommonCLI._load_required_attributes_from_config_file(common_cli)
        assert common_cli.osf_api_url == 'http://localhost:8001/v2/'
        assert common_cli.osf_token == 'access-token-update'
        assert len(caplog.records) == 1
        assert caplog.records[0].levelname == info_level_log
        assert caplog.records[0].message == f'Read config_file: {common_cli.config_file}'

    def test_load_required_attributes_from_config_file__not_update(self, common_cli, caplog):
        common_cli.config_default = {'osf_token': 'access-token-update',
                                     'osf_api_url': 'http://localhost:8001/v2/',
                                     'ssl_cert_verify': True,
                                     'debug': True,
                                     'verbose': True}
        CommonCLI._load_required_attributes_from_config_file(common_cli)
        assert common_cli.osf_api_url == 'http://localhost:8000/v2/'
        assert common_cli.osf_token == 'osf-token'
        assert len(caplog.records) == 1
        assert caplog.records[0].levelname == info_level_log
        assert caplog.records[0].message == f'Read config_file: {common_cli.config_file}'

    def test_load_required_attributes_from_environment__update(self, common_cli):
        common_cli.osf_token = None
        common_cli.osf_api_url = None
        os.environ['OSF_TOKEN'] = 'token-update'
        os.environ['OSF_API_url'] = 'http://localhost:8003/v2/'
        CommonCLI._load_required_attributes_from_environment(common_cli)
        assert common_cli.osf_token == 'token-update'
        assert common_cli.osf_api_url == 'http://localhost:8003/v2/'

    def test_load_required_attributes_from_environment__not_update(self, common_cli):
        CommonCLI._load_required_attributes_from_environment(common_cli)
        assert common_cli.osf_token == 'osf-token'
        assert common_cli.osf_api_url == 'http://localhost:8000/v2/'

    def test_check_config__is_auth_true(self, common_cli):
        common_cli.is_authenticated = True
        CommonCLI._check_config(common_cli)
        assert common_cli.is_authenticated is True

    def test_check_config__is_auth_false(self, common_cli, caplog):
        CommonCLI._check_config(common_cli)
        assert common_cli.is_authenticated is False

        assert caplog.records[0].levelname == info_level_log
        assert caplog.records[0].message == f'Check Personal Access Token'
        assert len(caplog.records) == 1

    def test_check_config__has_not_osf_api_url(self, common_cli, caplog):
        common_cli.osf_api_url = None
        with pytest.raises(SystemExit) as ex_info:
            CommonCLI._check_config(common_cli)
        assert caplog.records[0].levelname == info_level_log
        assert caplog.records[0].message == f'Try get from config property'
        assert caplog.records[1].levelname == info_level_log
        assert caplog.records[1].message == f'Try get from environment variable'
        assert len(caplog.records) == 2
        assert ex_info.value.code == 'Missing API URL'

    def test_check_config__has_osf_api_url_invalid(self, common_cli):
        common_cli.osf_api_url = 'osf_api_url'
        with pytest.raises(SystemExit) as ex_info:
            CommonCLI._check_config(common_cli)
        assert ex_info.value.code == 'The API URL is invalid'

    def test_check_config__has_not_osf_token(self, common_cli, caplog):
        common_cli.osf_token = None
        with pytest.raises(SystemExit) as ex_info:
            CommonCLI._check_config(common_cli)
        assert caplog.records[0].levelname == info_level_log
        assert caplog.records[0].message == f'Try get from config property'
        assert caplog.records[1].levelname == info_level_log
        assert caplog.records[1].message == f'Try get from environment variable'
        assert len(caplog.records) == 2
        assert ex_info.value.code == 'Missing Personal Access Token'

    @mock.patch("os.path.exists", return_value=False)
    @mock.patch("pathlib.Path.mkdir")
    def test_prepare_output_file__is_not_directory(self, mocker, common_cli, caplog):
        with mock.patch('grdmcli.grdm_client.common.os.path.join', return_value='/None'):
            with mock.patch('grdmcli.grdm_client.common.os.path.isdir', return_value=False):
                CommonCLI._prepare_output_file(common_cli)
                assert caplog.records[0].levelname == info_level_log
                assert caplog.records[0].message.__contains__('The new directory')
                assert len(caplog.records) == 1

    @mock.patch("os.path.exists", return_value=True)
    def test_prepare_output_file__output_file_exist(self, mocker, common_cli, caplog):
        CommonCLI._prepare_output_file(common_cli)
        assert len(caplog.records) == 0

    def test_force_update_config__update(self, common_cli):
        common_cli.disable_ssl_verify = True
        CommonCLI.force_update_config(common_cli)
        assert common_cli.debug
        assert common_cli.verbose
        assert not common_cli.ssl_cert_verify

    def test_force_update_config__not_update(self, common_cli):
        common_cli.enable_debug = False
        common_cli.enable_verbose = False
        common_cli.disable_ssl_verify = False
        CommonCLI.force_update_config(common_cli)
        assert common_cli.ssl_cert_verify

    def test_get_all_data_from_api__page_count_more_than_one(self, common_cli):
        res_dict = {
            'data': [1],
            'links': {
                'meta': {
                    "total": 2,
                    "per_page": 1
                }
            }
        }
        resp = requests.Response()
        resp._content = json.dumps(res_dict)
        with mock.patch.object(common_cli, 'parse_api_response', return_value = json.loads(resp.content, object_hook=lambda d: SimpleNamespace(**d))):
            CommonCLI.get_all_data_from_api(common_cli, 'user/123/nodes')
    
    def test_parse_api_response__successful(self, common_cli):
        res_dict = {
            'data': [1],
            'links': {
                'meta': {
                    "total": 2,
                    "per_page": 1
                }
            }
        }
        resp = requests.Response()
        resp._content = json.dumps(res_dict)
        with mock.patch.object(common_cli, '_request', return_value=(resp, None)):
            CommonCLI.parse_api_response(common_cli, 'GET', 'user/123/nodes')
    
    def test_parse_api_response__error(self, common_cli):
        res_dict = {
            'data': [1],
            'links': {
                'meta': {
                    "total": 2,
                    "per_page": 1
                }
            }
        }
        resp = requests.Response()
        resp._content = json.dumps(res_dict)
        with mock.patch.object(common_cli, '_request', return_value=(None, 'error_message')):
            with pytest.raises(SystemExit) as ex_info:
                CommonCLI.parse_api_response(common_cli, 'GET', 'user/123/nodes')

