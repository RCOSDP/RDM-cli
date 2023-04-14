import json
from types import SimpleNamespace
from unittest import mock

import pytest
import requests

from grdmcli.grdm_client.users import _users_me
from tests.factories import GRDMClientForProjectCreateFactory


@pytest.fixture
def grdm_client():
    return GRDMClientForProjectCreateFactory()


def test_users_me__send_request_error_and_ignore_error_false_sys_exit(capfd, grdm_client):
    _error_message = 'error'
    with mock.patch.object(grdm_client, '_request', return_value=(None, _error_message)):
        with pytest.raises(SystemExit) as ex_info:
            _users_me(grdm_client, ignore_error=False)
        assert ex_info.value.code == _error_message
        lines = capfd.readouterr().out.split('\n')
        assert lines[0] == f'GET the currently logged-in user'
        assert lines[1] == f'WARN {_error_message}'


def test_users_me__send_request_error_and_ignore_error_true_return_false(capfd, grdm_client):
    _error_message = 'error'
    with mock.patch.object(grdm_client, '_request', return_value=(None, _error_message)):
        actual = _users_me(grdm_client, ignore_error=True)
        lines = capfd.readouterr().out.split('\n')
        assert actual is False
        assert lines[0] == f'GET the currently logged-in user'
        assert lines[1] == f'WARN {_error_message}'


def test_users_me__send_request_success_and_verbose_false(capfd, grdm_client):
    resp = requests.Response()
    resp._content = '{"data":{"id": "typ46", "attributes": {"full_name": "Casey Rollins","email": "abc.gmail"}}}'
    with mock.patch.object(grdm_client, '_request', return_value=(resp, None)):
        _users_me(grdm_client, verbose=False)
        expect_response = json.loads(resp.content, object_hook=lambda d: SimpleNamespace(**d))
        assert grdm_client.is_authenticated is True
        assert grdm_client.user == expect_response.data
        captured = capfd.readouterr()
        assert captured.out == f'GET the currently logged-in user\n'


def test_users_me__send_request_success_and_verbose_true(capfd, grdm_client):
    resp = requests.Response()
    resp._content = '{"data":{"id": "typ46", "attributes": {"full_name": "Casey Rollins","email": "abc.gmail"}}}'
    with mock.patch.object(grdm_client, '_request', return_value=(resp, None)):
        _users_me(grdm_client, verbose=True)
        expect_response = json.loads(resp.content, object_hook=lambda d: SimpleNamespace(**d))
        assert grdm_client.is_authenticated is True
        assert grdm_client.user == expect_response.data
        lines = capfd.readouterr().out.split('\n')
        assert lines[0] == f'GET the currently logged-in user'
        assert lines[1] == f'You are logged in as:'
        assert lines[2] == \
               f'\'{grdm_client.user.id}\' - {grdm_client.user.attributes.email} \'{grdm_client.user.attributes.full_name}\''
