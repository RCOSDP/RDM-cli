import inspect
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
                }
            ]
        }
    ]
}
file_path = 'test_path.json'


def test_inspect_info():
    current_frame = inspect.currentframe()
    stack_info = inspect.stack()
    result = utils.inspect_info(current_frame, stack_info)
    assert isinstance(result, tuple)
    assert isinstance(result[0], str)
    assert isinstance(result[1], int)
    assert isinstance(result[2], str)
    assert result[2] == 'test_inspect_info'
    assert isinstance(result[3], str)
    assert isinstance(result[4], int)
    assert isinstance(result[5], str)


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
