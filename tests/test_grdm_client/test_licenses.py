import json
from types import SimpleNamespace
from unittest import mock

import pytest
import requests

from grdmcli.exceptions import GrdmCliException
from grdmcli.grdm_client.licenses import (_licenses, _find_license_id_from_name, MSG_E001)
from tests.factories import GRDMClientForProjectCreateFactory

licenses_dict = {
    "data": [
        {
            "links": {
                "self": "https://api.osf.io/v2/licenses/563c1cf88c5e4a3877f9e968/"
            },
            "attributes": {
                "text": "Copyright (c) {{year}}, {{copyrightHolders}}\nAll rights reserved.\n\nThe full descriptive text of the License.\n",
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
        "last": "https://api.osf.io/v2/licenses/?page=2",
        "prev": "",
        "next": "https://api.osf.io/v2/licenses/?page=2",
        "meta": {
            "total": 16,
            "per_page": 10
        }
    }
}

licenses_object = json.loads(json.dumps(licenses_dict), object_hook=lambda d: SimpleNamespace(**d))


@pytest.fixture
def grdm_client():
    return GRDMClientForProjectCreateFactory()


def test_licenses__user_not_exist(grdm_client):
    grdm_client.user = None
    with pytest.raises(SystemExit) as ex_info:
        _licenses(grdm_client)
    assert ex_info.value.code == MSG_E001


def test_licenses__send_request_error_and_ignore_error_false_sys_exit(capfd, grdm_client):
    _error_message = 'error'
    with mock.patch.object(grdm_client, '_request', return_value=(None, _error_message)):
        with pytest.raises(SystemExit) as ex_info:
            _licenses(grdm_client, ignore_error=False)
        assert ex_info.value.code == _error_message
        lines = capfd.readouterr().out.split('\n')
        assert lines[0] == f'GET List of licenses'
        assert lines[1] == f'WARN {_error_message}'


def test_licenses__send_request_error_and_ignore_error_true_return_false(capfd, grdm_client):
    _error_message = 'error'
    with mock.patch.object(grdm_client, '_request', return_value=(None, _error_message)):
        actual = _licenses(grdm_client, ignore_error=True)
        lines = capfd.readouterr().out.split('\n')
        assert actual is False
        assert lines[0] == f'GET List of licenses'
        assert lines[1] == f'WARN {_error_message}'


def test_licenses__send_request_success_verbose_false(capfd, grdm_client):
    resp = requests.Response()
    resp._content = json.dumps(licenses_dict)
    with mock.patch.object(grdm_client, '_request', return_value=(resp, None)):
        _licenses(grdm_client, verbose=False)
        expect_response = json.loads(resp.content, object_hook=lambda d: SimpleNamespace(**d))
        assert grdm_client.licenses == expect_response.data
        assert grdm_client._meta['_licenses'] == expect_response.links.meta.total
        captured = capfd.readouterr()
        assert captured.out == f'GET List of licenses\n'


def test_licenses__send_request_success_verbose_true(capfd, grdm_client):
    resp = requests.Response()
    resp._content = json.dumps(licenses_dict)
    with mock.patch.object(grdm_client, '_request', return_value=(resp, None)):
        _licenses(grdm_client, verbose=True)
        assert grdm_client.licenses == licenses_object.data
        assert grdm_client._meta['_licenses'] == licenses_object.links.meta.total
        lines = capfd.readouterr().out.split('\n')
        assert lines[0] == f'GET List of licenses'
        assert lines[1] == f'[For development]List of licenses. [{licenses_object.links.meta.total}]'
        assert lines[
                   2] == f'\'{grdm_client.licenses[0].id}\' - \'{grdm_client.licenses[0].attributes.name}\' [{grdm_client.licenses[0].type}]'


def test_find_license_id_from_name__not_licenses_raise_error(grdm_client):
    _license = licenses_object.data[0]
    grdm_client.licenses = []
    with mock.patch.object(grdm_client, '_licenses', return_value=licenses_object.data):
        with pytest.raises(GrdmCliException) as ex_info:
            _find_license_id_from_name(grdm_client, _license.attributes.name)
        assert ex_info.value.args[0] == f'License name \'{_license.attributes.name}\' is not registered.'


def test_find_license_id_from_name__return_license_id(grdm_client):
    _license = licenses_object.data[0]
    grdm_client.licenses = licenses_object.data
    with mock.patch.object(grdm_client, '_licenses', return_value=licenses_object.data):
        actual = _find_license_id_from_name(grdm_client, _license.attributes.name)
        assert actual == _license.id
