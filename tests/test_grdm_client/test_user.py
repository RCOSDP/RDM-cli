import json
import logging
from types import SimpleNamespace
from unittest import mock

import pytest
import requests

from grdmcli.grdm_client.users import (
    _users_me,
    _users_me_affiliated_institutions,
    _users_me_affiliated_users,
    MSG_E001)
from tests.factories import GRDMClientFactory, user_str
from utils import *


@pytest.fixture
def grdm_client():
    return GRDMClientFactory()


@pytest.fixture(autouse=True)
def set_log_level(caplog):
    caplog.clear()
    caplog.set_level(logging.DEBUG)


_users_me_institutions_str = '''{
    "data": [
        {
            "id": "csic",
            "type": "institutions",
            "attributes": {
                "name": "Spanish National Research Council [Test]",
                "description": "Related resources are in the institutional intranet web site only.",
                "assets": {
                    "logo": "/static/img/institutions/shields/csic-shield.png",
                    "logo_rounded": "/static/img/institutions/shields-rounded-corners/csic-shield-rounded-corners.png"
                },
                "logo_path": "/static/img/institutions/shields/csic-shield.png"
            },
            "relationships": {
                "nodes": {
                    "links": {
                        "related": {
                            "href": "http://localhost:8000/v2/institutions/csic/nodes/",
                            "meta": {}
                        }
                    }
                },
                "registrations": {
                    "links": {
                        "related": {
                            "href": "http://localhost:8000/v2/institutions/csic/registrations/",
                            "meta": {}
                        }
                    }
                },
                "users": {
                    "links": {
                        "related": {
                            "href": "http://localhost:8000/v2/institutions/csic/users/",
                            "meta": {}
                        }
                    }
                },
                "department_metrics": {
                    "links": {
                        "related": {
                            "href": "http://localhost:8000/v2/institutions/csic/metrics/departments/",
                            "meta": {}
                        }
                    }
                },
                "user_metrics": {
                    "links": {
                        "related": {
                            "href": "http://localhost:8000/v2/institutions/csic/metrics/users/",
                            "meta": {}
                        }
                    }
                },
                "summary_metrics": {
                    "links": {
                        "related": {
                            "href": "http://localhost:8000/v2/institutions/csic/metrics/summary/",
                            "meta": {}
                        }
                    },
                    "data": {
                        "id": "csic",
                        "type": "institution-summary-metrics"
                    }
                }
            },
            "links": {
                "self": "http://localhost:8000/v2/institutions/csic/",
                "html": "http://localhost:5000/institutions/csic/"
            }
        }
    ],
    "links": {
        "first": null,
        "last": null,
        "prev": null,
        "next": null,
        "meta": {
            "total": 1,
            "per_page": 10
        }
    },
    "meta": {
        "version": "2.0"
    }
}'''
_users_me_institutions_obj = json.loads(_users_me_institutions_str, object_hook=lambda d: SimpleNamespace(**d))


def test_users_me__send_request_error_and_ignore_error_false_sys_exit(caplog, grdm_client):
    _error_message = 'error'
    with mock.patch.object(grdm_client, '_request', return_value=(None, _error_message)):
        with pytest.raises(SystemExit) as ex_info:
            _users_me(grdm_client, ignore_error=False)
        assert ex_info.value.code == _error_message
        assert len(caplog.records) == 2
        assert caplog.records[0].levelname == info_level_log
        assert caplog.records[0].message == f'Get the currently logged-in user'
        assert caplog.records[1].levelname == warning_level_log
        assert caplog.records[1].message == f'{_error_message}'


def test_users_me__send_request_error_and_ignore_error_true_return_false(caplog, grdm_client):
    _error_message = 'error'
    with mock.patch.object(grdm_client, '_request', return_value=(None, _error_message)):
        actual = _users_me(grdm_client, ignore_error=True)
        assert actual is False
        assert len(caplog.records) == 2
        assert caplog.records[0].levelname == info_level_log
        assert caplog.records[0].message == f'Get the currently logged-in user'
        assert caplog.records[1].levelname == warning_level_log
        assert caplog.records[1].message == f'{_error_message}'


def test_users_me__send_request_success_and_verbose_false(caplog, grdm_client):
    resp = requests.Response()
    resp._content = '{"data":{"id": "typ46", "attributes": {"full_name": "Casey Rollins","email": "abc.gmail"}}}'
    with mock.patch.object(grdm_client, '_request', return_value=(resp, None)):
        _users_me(grdm_client, verbose=False)
        expect_response = json.loads(resp.content, object_hook=lambda d: SimpleNamespace(**d))
        assert grdm_client.is_authenticated is True
        assert grdm_client.user == expect_response.data
        assert len(caplog.records) == 2
        assert caplog.records[0].levelname == info_level_log
        assert caplog.records[0].message == f'Get the currently logged-in user'


def test_users_me__send_request_success_and_verbose_true(caplog, grdm_client):
    resp = requests.Response()
    resp._content = '{"data":{"id": "typ46", "attributes": {"full_name": "Casey Rollins","email": "abc.gmail"}}}'
    with mock.patch.object(grdm_client, '_request', return_value=(resp, None)):
        _users_me(grdm_client, verbose=True)
        expect_response = json.loads(resp.content, object_hook=lambda d: SimpleNamespace(**d))
        assert grdm_client.is_authenticated is True
        assert grdm_client.user == expect_response.data
        assert len(caplog.records) == 3
        assert caplog.records[0].levelname == info_level_log
        assert caplog.records[0].message == f'Get the currently logged-in user'
        assert caplog.records[1].levelname == info_level_log
        assert caplog.records[1].message == f'You are logged in as \'{grdm_client.user.id}\''
        assert caplog.records[2].levelname == debug_level_log
        assert caplog.records[2].message == f'\'{grdm_client.user.id}\' - \'{grdm_client.user.attributes.full_name}\''


def test_users_me_affiliated_institutions__not_user(grdm_client, caplog):
    grdm_client.user = None
    with pytest.raises(SystemExit) as ex_info:
        _users_me_affiliated_institutions(grdm_client)
    assert ex_info.value.code == MSG_E001


def test_users_me_affiliated_institutions__send_request_error_ignore_error_false(caplog, grdm_client):
    _error_message = 'error'
    with mock.patch.object(grdm_client, '_request', return_value=(None, _error_message)):
        with pytest.raises(SystemExit) as ex_info:
            _users_me_affiliated_institutions(grdm_client, ignore_error=False)
        assert ex_info.value.code == _error_message
        assert len(caplog.records) == 1
        assert caplog.records[0].levelname == warning_level_log
        assert caplog.records[0].message == f'{_error_message}'


def test_users_me_affiliated_institutions__send_request_error_ignore_error_true(caplog, grdm_client):
    _error_message = 'error'
    with mock.patch.object(grdm_client, '_request', return_value=(None, _error_message)):
        actual = _users_me_affiliated_institutions(grdm_client)
        assert not actual
        assert len(caplog.records) == 1
        assert caplog.records[0].levelname == warning_level_log
        assert caplog.records[0].message == f'{_error_message}'


def test_users_me_affiliated_institutions__send_request_success_verbose_true(caplog, grdm_client):
    resp = requests.Response()
    resp._content = _users_me_institutions_str
    with mock.patch.object(grdm_client, '_request', return_value=(resp, None)):
        _users_me_affiliated_institutions(grdm_client)
    assert grdm_client.affiliated_institutions == _users_me_institutions_obj.data
    _institutions_numb = _users_me_institutions_obj.links.meta.total
    assert grdm_client._meta == {'_institutions': _institutions_numb}
    assert len(caplog.records) == 2
    assert caplog.records[0].levelname == info_level_log
    assert caplog.records[0].message == f'List of affiliated institutions. [{_institutions_numb}]'
    assert caplog.records[1].levelname == debug_level_log
    inst = grdm_client.affiliated_institutions[0]
    assert caplog.records[1].message == \
           f'\'{inst.id}\' - \'{inst.attributes.name}\' [{inst.type}][{inst.attributes.description[:10]}...]'


def test_users_me_affiliated_institutions__send_request_success_verbose_false(caplog, grdm_client):
    resp = requests.Response()
    resp._content = _users_me_institutions_str
    with mock.patch.object(grdm_client, '_request', return_value=(resp, None)):
        _users_me_affiliated_institutions(grdm_client, verbose=False)
    assert grdm_client.affiliated_institutions == _users_me_institutions_obj.data
    _institutions_numb = _users_me_institutions_obj.links.meta.total
    assert grdm_client._meta == {'_institutions': _institutions_numb}
    assert len(caplog.records) == 1


def test_users_me_affiliated_users__not_user(grdm_client, caplog):
    grdm_client.user = None
    with pytest.raises(SystemExit) as ex_info:
        _users_me_affiliated_users(grdm_client)
    assert ex_info.value.code == MSG_E001


def test_users_me_affiliated_users__not_affiliated_institutions(grdm_client, caplog):
    grdm_client.affiliated_institutions = []
    with pytest.raises(SystemExit) as ex_info:
        _users_me_affiliated_users(grdm_client)
    assert ex_info.value.code == 'Missing currently logged-in user\'s affiliated institutions'


def test_users_me_affiliated_users__send_request_error_ignore_error_true(caplog, grdm_client):
    _error_message = 'error'
    grdm_client.affiliated_institutions = _users_me_institutions_obj.data
    with mock.patch.object(grdm_client, '_request', return_value=(None, _error_message)):
        actual = _users_me_affiliated_users(grdm_client)
        assert not actual
        assert len(caplog.records) == 1
        assert caplog.records[0].levelname == warning_level_log
        assert caplog.records[0].message == f'{_error_message}'


def test_users_me_affiliated_users__send_request_error_ignore_error_false(caplog, grdm_client):
    _error_message = 'error'
    grdm_client.affiliated_institutions = _users_me_institutions_obj.data
    with mock.patch.object(grdm_client, '_request', return_value=(None, _error_message)):
        with pytest.raises(SystemExit) as ex_info:
            _users_me_affiliated_users(grdm_client, ignore_error=False)
        assert ex_info.value.code == _error_message
        assert len(caplog.records) == 1
        assert caplog.records[0].levelname == warning_level_log
        assert caplog.records[0].message == f'{_error_message}'


def test_users_me_affiliated_users__success(caplog, grdm_client):
    _data = {'data': [json.loads(user_str)], 'links': {'meta': {'total': 1}}}
    resp = requests.Response()
    resp._content = json.dumps(_data)
    grdm_client.affiliated_institutions = _users_me_institutions_obj.data
    with mock.patch.object(grdm_client, '_request', return_value=(resp, None)):
        _users_me_affiliated_users(grdm_client)
    _users_numb = 1
    assert grdm_client._meta['_users'] == 1
    assert len(caplog.records) == 2
    assert caplog.records[0].levelname == info_level_log
    assert caplog.records[0].message == f'List of affiliated institutions\' users. [{_users_numb}]'
    assert caplog.records[1].levelname == debug_level_log
    assert caplog.records[1].message == f'\'{grdm_client.user.id}\' - \'{grdm_client.user.attributes.full_name}\''


def test_users_me_affiliated_users__success_verbose_false(caplog, grdm_client):
    _data = {'data': [json.loads(user_str)], 'links': {'meta': {'total': 1}}}
    resp = requests.Response()
    resp._content = json.dumps(_data)
    grdm_client.affiliated_institutions = _users_me_institutions_obj.data
    with mock.patch.object(grdm_client, '_request', return_value=(resp, None)):
        _users_me_affiliated_users(grdm_client, verbose=False)
    assert len(caplog.records) == 1
    assert grdm_client._meta['_users'] == 1
