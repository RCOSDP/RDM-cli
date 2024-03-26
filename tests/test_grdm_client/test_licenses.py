import json
import logging
from types import SimpleNamespace
from unittest import mock

import pytest
import requests

from grdmcli.grdm_client.licenses import (
    _licenses,
    _find_license_id_from_name,
    MSG_E001
)
from tests.factories import GRDMClientFactory
from tests.utils import *

licenses_dict = {
    "data": [
        {
            "links": {
                "self": "https://api.osf.io/v2/licenses/563c1cf88c5e4a3877f9e968/"
            },
            "attributes": {
                "text": "Copyright (c) {{year}}, {{copyrightHolders}}All rights reserved.The full descriptive text of the License.",
                "required_fields": [
                    "year",
                    "copyrightHolders"
                ],
                "name": "BSD 2-Clause \"Simplified\" License"
            },
            "type": "licenses",
            "id": "563c1cf88c5e4a3877f9e968"
        },
        {
            "links": {
                "self": "https://api.osf.io/v2/licenses/563c1cf88c5e4a3877f9e968/"
            },
            "attributes": {
                "text": "Copyright (c) {{year}}, {{copyrightHolders}}All rights reserved.The full descriptive text of the License.",
                "required_fields": [
                    "year",
                    "copyrightHolders"
                ],
                "name": "BSD 3-Clause \"Simplified\" License"
            },
            "type": "licenses",
            "id": "123"
        }
    ],
    "links": {
        "first": "",
        "last": "null",
        "prev": "",
        "next": "null",
        "meta": {
            "total": 2,
            "per_page": 1
        }
    }
}
licenses_dict_page_1 = {
    "data": [
        {
            "links": {
                "self": "https://api.osf.io/v2/licenses/563c1cf88c5e4a3877f9e968/"
            },
            "attributes": {
                "text": "Copyright (c) {{year}}, {{copyrightHolders}}All rights reserved.The full descriptive text of the License.",
                "required_fields": [
                    "year",
                    "copyrightHolders"
                ],
                "name": "BSD 2-Clause \"Simplified\" License"
            },
            "type": "licenses",
            "id": "563c1cf88c5e4a3877f9e968"
        }
    ],
    "links": {
        "first": "",
        "last": "null",
        "prev": "",
        "next": "null",
        "meta": {
            "total": 2,
            "per_page": 1
        }
    }
}
licenses_dict_page_2 = {
    "data": [
        {
            "links": {
                "self": "https://api.osf.io/v2/licenses/563c1cf88c5e4a3877f9e968/"
            },
            "attributes": {
                "text": "Copyright (c) {{year}}, {{copyrightHolders}}All rights reserved.The full descriptive text of the License.",
                "required_fields": [
                    "year",
                    "copyrightHolders"
                ],
                "name": "BSD 3-Clause \"Simplified\" License"
            },
            "type": "licenses",
            "id": "123"
        }
    ],
    "links": {
        "first": "",
        "last": "null",
        "prev": "",
        "next": "null",
        "meta": {
            "total": 2,
            "per_page": 1
        }
    }
}

licenses_object = json.loads(json.dumps(licenses_dict), object_hook=lambda d: SimpleNamespace(**d))


@pytest.fixture(autouse=True)
def set_log_level(caplog):
    caplog.set_level(logging.DEBUG)


@pytest.fixture
def grdm_client():
    return GRDMClientFactory()


def test_licenses__user_not_exist(grdm_client):
    grdm_client.user = None
    with pytest.raises(SystemExit) as ex_info:
        _licenses(grdm_client)
    assert ex_info.value.code == MSG_E001


def test_licenses__send_request_error_and_ignore_error_false_sys_exit(caplog, grdm_client):
    _error_message = 'error'
    with mock.patch.object(grdm_client, '_request', return_value=(None, _error_message)):
        with pytest.raises(SystemExit) as ex_info:
            _licenses(grdm_client, ignore_error=False)
        assert ex_info.value.code == _error_message
        assert len(caplog.records) == 2
        assert caplog.records[0].levelname == info_level_log
        assert caplog.records[0].message == f'Get list of licenses'
        assert caplog.records[1].levelname == warning_level_log
        assert caplog.records[1].message == f'{_error_message}'


def test_licenses__send_request_error_and_ignore_error_true_return_false(caplog, grdm_client):
    _error_message = 'error'
    with mock.patch.object(grdm_client, '_request', return_value=(None, _error_message)):
        actual = _licenses(grdm_client, ignore_error=True)
    assert len(caplog.records) == 2
    assert actual is False
    assert caplog.records[0].levelname == info_level_log
    assert caplog.records[0].message == f'Get list of licenses'
    assert caplog.records[1].levelname == warning_level_log
    assert caplog.records[1].message == f'{_error_message}'


def test_licenses__send_request_success_verbose_false(caplog, grdm_client):
    resp1 = requests.Response()
    resp1._content = json.dumps(licenses_dict_page_1)

    resp2 = requests.Response()
    resp2._content = json.dumps(licenses_dict_page_2)
    converted_res_2 = json.loads(resp2.content, object_hook=lambda d: SimpleNamespace(**d))

    with mock.patch.object(grdm_client, '_request', return_value=(resp1, None)):
        with mock.patch.object(grdm_client, 'parse_api_response', return_value=(converted_res_2)):
            _licenses(grdm_client, verbose=False)
    expect_response = json.loads(json.dumps(licenses_dict), object_hook=lambda d: SimpleNamespace(**d))
    assert grdm_client.licenses == expect_response.data
    assert grdm_client._meta['_licenses'] == expect_response.links.meta.total


    assert len(caplog.records) == 2
    assert caplog.records[0].levelname == info_level_log
    assert caplog.records[0].message == f'Get list of licenses'
    assert caplog.records[1].levelname == info_level_log
    assert 'List of licenses' in caplog.records[1].message


def test_licenses__send_request_success_verbose_true(caplog, grdm_client):
    resp1 = requests.Response()
    resp1._content = json.dumps(licenses_dict_page_1)

    resp2 = requests.Response()
    resp2._content = json.dumps(licenses_dict_page_2)
    converted_res_2 = json.loads(resp2.content, object_hook=lambda d: SimpleNamespace(**d))

    with mock.patch.object(grdm_client, '_request', return_value=(resp1, None)):
        with mock.patch.object(grdm_client, 'parse_api_response', return_value=(converted_res_2)):
            _licenses(grdm_client, verbose=True)
    assert grdm_client.licenses == licenses_object.data
    assert grdm_client._meta['_licenses'] == licenses_object.links.meta.total
    assert len(caplog.records) == 4
    assert caplog.records[0].levelname == info_level_log
    assert caplog.records[0].message == f'Get list of licenses'
    assert caplog.records[1].levelname == info_level_log
    assert 'List of licenses' in caplog.records[1].message
    assert caplog.records[2].levelname == debug_level_log


def test_find_license_id_from_name__not_licenses_warning(caplog, grdm_client):
    _license = licenses_object.data[0]
    grdm_client.licenses = []
    with mock.patch.object(grdm_client, '_licenses', return_value=licenses_object.data):
        _find_license_id_from_name(grdm_client, _license.attributes.name)
        assert len(caplog.records) == 1
        assert caplog.records[0].levelname == warning_level_log
        assert caplog.records[0].message == f'License name \'{_license.attributes.name}\' is not registered.'


def test_find_license_id_from_name__return_license_id(grdm_client):
    _license = licenses_object.data[0]
    grdm_client.licenses = licenses_object.data
    with mock.patch.object(grdm_client, '_licenses', return_value=licenses_object.data):
        actual = _find_license_id_from_name(grdm_client, _license.attributes.name)
        assert actual == _license.id
