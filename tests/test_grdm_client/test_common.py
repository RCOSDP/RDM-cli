import configparser
import json
import os
from unittest import mock
import pytest

import requests

from grdmcli.grdm_client.common import CommonCLI

from tests.factories import CommonCLIFactory


@pytest.fixture
def common_cli():
    return CommonCLIFactory()


class TestCommonCLI:
    url = 'https://api.test.osf.io/v2/nodes/{node_id}/contributors/'.format(node_id='abc32')

    common_cli = CommonCLI()

    def test_init_has_required_attributes_false(self):
        self.common_cli.osf_token = None
        self.common_cli.osf_api_url = None
        assert self.common_cli.is_authenticated is False
        assert self.common_cli.user is None
        assert self.common_cli.template == './template_file.json'
        assert self.common_cli.output_result_file == './output_result_file.json'
        assert self.common_cli._meta == {}
        assert self.common_cli.config_file is not None
        assert self.common_cli.has_required_attributes is False

    def test_init_osf_token_is_none(self):
        self.common_cli.osf_token = None
        self.common_cli.osf_api_url = 'http://localhost:8000/v2/'
        assert self.common_cli.is_authenticated is False
        assert self.common_cli.user is None
        assert self.common_cli.template == './template_file.json'
        assert self.common_cli.output_result_file == './output_result_file.json'
        assert self.common_cli._meta == {}
        assert self.common_cli.config_file is not None
        assert self.common_cli.has_required_attributes is False

    def test_init_osf_api_url_is_none(self):
        self.common_cli.osf_token = 'access-token'
        self.common_cli.osf_api_url = None
        assert self.common_cli.is_authenticated is False
        assert self.common_cli.user is None
        assert self.common_cli.template == './template_file.json'
        assert self.common_cli.output_result_file == './output_result_file.json'
        assert self.common_cli._meta == {}
        assert self.common_cli.config_file is not None
        assert self.common_cli.has_required_attributes is False

    def test_init(self):
        self.common_cli.osf_token = 'access-token'
        self.common_cli.osf_api_url = 'http://localhost:8000/v2/'
        assert self.common_cli.is_authenticated is False
        assert self.common_cli.user is None
        assert self.common_cli.template == './template_file.json'
        assert self.common_cli.output_result_file == './output_result_file.json'
        assert self.common_cli._meta == {}
        assert self.common_cli.config_file is not None
        assert self.common_cli.has_required_attributes is True

    @mock.patch('requests.request')
    def test_request_not_success(self, mock_get, common_cli):
        resp = requests.Response()
        resp._content = json.dumps({'errors': [{'detail': 'mock error'}]})
        resp.status_code = 400
        mock_get.return_value = resp
        actual1, actual2 = CommonCLI._request(common_cli, 'GET', self.url)
        assert actual1 is None
        assert actual2 == 'mock error'

    @mock.patch('requests.request')
    def test_request_success(self, mock_get, common_cli):
        resp = requests.Response()
        resp._content = 'success'
        resp.status_code = 200
        mock_get.return_value = resp
        actual1, actual2 = CommonCLI._request(common_cli, 'GET', self.url, {})
        assert actual1 == resp
        assert actual2 is None

    @mock.patch('requests.request')
    def test_request_invalid(self, mock_get, common_cli):
        resp = requests.Response()
        resp._content = 'success'
        resp.status_code = 200
        mock_get.return_value = resp
        actual1, actual2 = CommonCLI._request(common_cli, 'GET', 'test', {})
        assert actual1 == resp
        assert actual2 is None

    @mock.patch("os.path.exists", return_value=False)
    def test_load_required_attributes_from_config_file_return_false(self, mocker, common_cli):
        actual = CommonCLI._load_required_attributes_from_config_file(common_cli)
        assert actual is False

    @mock.patch("os.path.exists", return_value=True)
    def test_load_required_attributes_from_config_file_update(self, mocker, common_cli):
        config = configparser.ConfigParser()
        config.read_dict({"default": {'osf_token': 'access-token-update',
                                      'osf_api_url': 'http://localhost:8001/v2/'}})
        common_cli.osf_api_url = None
        common_cli.osf_token = None
        mock_parser = mock.MagicMock(return_value=config)
        with mock.patch("configparser.ConfigParser", new=mock_parser):
            CommonCLI._load_required_attributes_from_config_file(common_cli)
            assert common_cli.osf_api_url == 'http://localhost:8001/v2/'
            assert common_cli.osf_token == 'access-token-update'

    @mock.patch("os.path.exists", return_value=True)
    def test_load_required_attributes_from_config_file_not_update(self, mocker, common_cli):
        config = configparser.ConfigParser()
        config.read_dict({"default": {'osf_token': 'access-token-update',
                                      'osf_api_url': 'http://localhost:8001/v2/'}})
        mock_parser = mock.MagicMock(return_value=config)
        with mock.patch("configparser.ConfigParser", new=mock_parser):
            CommonCLI._load_required_attributes_from_config_file(common_cli)
            assert common_cli.osf_api_url == 'http://localhost:8000/v2/'
            assert common_cli.osf_token == 'access-token'

    def test_load_required_attributes_from_environment_update(self, common_cli):
        common_cli.osf_token = None
        common_cli.osf_api_url = None
        os.environ['OSF_TOKEN'] = 'token-update'
        os.environ['OSF_API_url'] = 'http://localhost:8003/v2/'
        CommonCLI._load_required_attributes_from_environment(common_cli)
        assert common_cli.osf_token == 'token-update'
        assert common_cli.osf_api_url == 'http://localhost:8003/v2/'

    def test_load_required_attributes_from_environment_not_update(self, common_cli):
        CommonCLI._load_required_attributes_from_environment(common_cli)
        assert common_cli.osf_token == 'access-token'
        assert common_cli.osf_api_url == 'http://localhost:8000/v2/'

    def test_check_config_is_auth_true(self, common_cli):
        common_cli.is_authenticated = True
        CommonCLI._check_config(common_cli)
        assert common_cli.is_authenticated is True

    def test_check_config_is_auth_false(self, common_cli):
        with pytest.raises(Exception):
            CommonCLI._check_config(common_cli)
        common_cli.is_authenticated = False

    @mock.patch('sys.exit', return_value=Exception())
    def test_check_config_has_not_osf_api_url(self, mocker_exit, common_cli):
        common_cli.osf_api_url = None
        with pytest.raises(Exception):
            CommonCLI._check_config(common_cli)
        mocker_exit.assert_called_once_with('Missing API URL')

    @mock.patch('sys.exit', return_value=Exception())
    def test_check_config_has_osf_api_url_invalid(self, mocker_exit, common_cli):
        common_cli.osf_api_url = 'osf_api_url'
        with pytest.raises(Exception):
            CommonCLI._check_config(common_cli)
        mocker_exit.assert_called_once_with('The API URL is invalid')

    @mock.patch('sys.exit', return_value=Exception())
    def test_check_config_has_not_osf_token(self, mocker_exit, common_cli):
        common_cli.osf_token = None
        with pytest.raises(Exception):
            CommonCLI._check_config(common_cli)
        mocker_exit.assert_called_once_with('Missing Personal Access Token')
