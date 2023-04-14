import inspect
import json
from unittest import mock

import jsonschema
import pytest

from grdmcli import utils
from grdmcli.exceptions import GrdmCliException

data = {
    "projects": [{
        "title": "test validate schema"
    }]
}
jsonschema_str = """{
    "title": "GRDM CLI - Projects/Components Template schema",
    "description": "For projects/components definition JSON Schema",
    "type": "object",
    "properties": {
        "projects": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string"
                    }
                },
                "additionalProperties": false
            }
        }
    },
    "required": [
        "projects"
    ],
    "additionalProperties": false
}"""
file_path = 'test_path.json'


def test_inspect_info__normal():
    current_frame = inspect.currentframe()
    stack_info = inspect.stack()
    result = utils.inspect_info(current_frame, stack_info)
    assert isinstance(result, tuple)
    assert isinstance(result[0], str)
    assert isinstance(result[1], int)
    assert isinstance(result[2], str)
    assert result[2] == 'test_inspect_info__normal'
    assert isinstance(result[3], str)
    assert isinstance(result[4], int)
    assert isinstance(result[5], str)


def test_read_json_file__success():
    with mock.patch('builtins.open', mock.mock_open(read_data=json.dumps(data))) as mock_file:
        res = utils.read_json_file(file_path)
        assert res == data
        mock_file.assert_called_with(file_path, 'r', encoding='utf-8')


def test_read_json_file__exception():
    with mock.patch('builtins.open', mock.mock_open(read_data=data)):
        with pytest.raises(GrdmCliException) as ex_infor:
            utils.read_json_file(file_path)
        assert 'Cannot read json file' == ex_infor.value.args[0]


def test_write_json_file__success(capfd):
    with mock.patch('builtins.open', mock.mock_open()) as mock_file:
        utils.write_json_file(file_path, data)
        assert capfd.readouterr().out == f"File was written successfully:  {file_path}\n"
        mock_file.assert_called_with(file_path, 'w', encoding='utf-8')


def test_write_json_file__exception():
    with mock.patch('builtins.open', mock.mock_open(read_data=json.dumps(data))):
        with mock.patch("json.dump", side_effect=Exception()):
            with pytest.raises(GrdmCliException) as ex_info:
                utils.write_json_file(file_path, data)
            assert 'Cannot write json file' == ex_info.value.args[0]


@mock.patch('grdmcli.utils.read_json_file', return_value=json.loads(jsonschema_str))
def test_check_json_schema__success(mocker):
    with mock.patch('grdmcli.utils.read_json_file', return_value=json.loads(jsonschema_str)):
        utils.check_json_schema(file_path, data)


@mock.patch('grdmcli.utils.read_json_file', return_value=json.loads(jsonschema_str))
def test_check_json_schema__error(mocker):
    with mock.patch('jsonschema.validate', side_effect=jsonschema.exceptions.ValidationError('error')):
        with pytest.raises(GrdmCliException) as ex_info:
            utils.check_json_schema(file_path, data)
        assert ex_info.value.args[0]['message'] == 'error'
