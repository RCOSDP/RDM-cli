import json

import jsonschema
from unittest import mock

import pytest

from grdmcli import utils
from grdmcli.exceptions import GrdmCliException

data = {
    "projects": [
        {
            "id": "23abc",
            "contributors": [
                {
                    "id": "user2",
                    "bibliographic": True,
                    "permission": "admin"
                },
                {
                    "id": "user3",
                    "bibliographic": True,
                    "permission": "admin"
                },
                {
                    "id": "user4",
                    "bibliographic": True,
                    "permission": "write"
                }
            ]
        }
    ]
}
file_path = 'test_path.json'


def test_read_json_file():
    with mock.patch('builtins.open', mock.mock_open(read_data=json.dumps(data))) as mock_file:
        res = utils.read_json_file(file_path)
        assert res == data
        mock_file.assert_called_with(file_path, 'r', encoding='utf-8')


def test_read_json_file_exception():
    with mock.patch('builtins.open', mock.mock_open(read_data=data)):
        with pytest.raises(GrdmCliException):
            utils.read_json_file(file_path)


def test_write_json_file():
    with mock.patch('builtins.open', mock.mock_open()) as mock_file:
        utils.write_json_file(file_path, data)
        mock_file.assert_called_with(file_path, 'w', encoding='utf-8')


def test_write_json_file_exception():
    with mock.patch('builtins.open', mock.mock_open()):
        with mock.patch('json.dump', side_effect=Exception()):
            with pytest.raises(GrdmCliException):
                utils.write_json_file(file_path, data)


def test_check_json_schema():
    with mock.patch('grdmcli.utils.read_json_file', return_value=data):
        utils.check_json_schema(file_path, data)


def test_check_json_schema_error():
    with mock.patch('grdmcli.utils.read_json_file', return_value={}):
        with mock.patch('jsonschema.validate', side_effect=jsonschema.exceptions.ValidationError('error')):
            with pytest.raises(GrdmCliException):
                utils.check_json_schema(file_path, data)
