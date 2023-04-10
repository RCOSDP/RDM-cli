import inspect
import json
from unittest import mock

import jsonschema
import pytest

from grdmcli import utils
from grdmcli.exceptions import GrdmCliException

data = {
    "projects": [
        {
            "id": "abcd2",
            "category": "project",
            "title": "Project Example 001",
            "description": "Lorem Ipsum has been the industry's standard dummy text ever since the 1500s, when an unknown printer took a galley of type and scrambled it to make a type specimen book.",
            "public": False,
            "tags": [
                "replication",
                "reproducibility",
                "open science",
                "reproduction",
                "psychological science",
                "psychology",
                "metascience",
                "crowdsource"
            ],
            "children": [
                {
                    "id": "abcd3",
                    "category": "analysis",
                    "title": "Analysis Component Example 001",
                    "description": "Lorem Ipsum is simply dummy text of the printing and typesetting industry.",
                    "public": False,
                    "tags": [
                        "analysis",
                        "component"
                    ]
                },
                {
                    "id": "abcd4",
                    "category": "communication",
                    "title": "Communication Component Example 001"
                },

            ]
        },
        {
            "id": "abcd5",
            "category": "analysis",
            "title": "Analysis Example 001"
        }
    ]
}
json_schema = """{
    "title": "GRDM CLI - Projects/Components Template schema",
    "description": "For projects/components definition JSON Schema",
    "type": "object",
    "properties": {
        "projects": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "id": {
                        "$ref": "#/definitions/NodeIdOrNull",
                        "default": null
                    },
                    "fork_id": {
                        "$ref": "#/definitions/NodeIdOrNull",
                        "default": null
                    },
                    "template_from": {
                        "$ref": "#/definitions/NodeId"
                    },
                    "category": {
                        "$ref": "#/definitions/NodeCategory"
                    },
                    "title": {
                        "type": "string"
                    },
                    "description": {
                        "type": "string"
                    },
                    "node_license": {
                        "$ref": "#/definitions/NodeLicense"
                    },
                    "public": {
                        "type": "boolean"
                    },
                    "tags": {
                        "type": "array",
                        "items": {
                            "type": "string"
                        }
                    },
                    "children": {
                        "$ref": "#/definitions/NodeChildren"
                    },
                    "project_links": {
                        "type": "array",
                        "items": {
                            "$ref": "#/definitions/NodeId"
                        }
                    }
                },
                "additionalProperties": false,
                "anyOf": [
                    {
                        "properties": {
                            "id": {
                                "$ref": "#/definitions/NodeId"
                            }
                        },
                        "required": [
                            "id"
                        ]
                    },
                    {
                        "required": [
                            "category",
                            "title"
                        ]
                    }
                ]
            }
        }
    },
    "required": [
        "projects"
    ],
    "additionalProperties": false,
    "definitions": {
        "NodeId": {
            "type": "string",
            "pattern": "^[23456789abcdefghjkmnpqrstuvwxyz]{5}$"
        },
        "NodeIdOrNull": {
            "anyOf": [
                {
                    "type": "null"
                },
                {
                    "$ref": "#/definitions/NodeId"
                }
            ]
        },
        "NodeCategory": {
            "enum": [
                "analysis",
                "communication",
                "data",
                "hypothesis",
                "instrumentation",
                "methods and measures",
                "procedure",
                "project",
                "software",
                "other"
            ]
        },
        "NodeLicense": {
            "type": "object",
            "properties": {
                "license_name": {
                    "type": "string"
                },
                "copyright_holders": {
                    "type": "array",
                    "items": {
                        "type": "string"
                    }
                },
                "year": {
                    "type": "string"
                }
            },
            "required": [
                "license_name",
                "copyright_holders",
                "year"
            ],
            "additionalProperties": false
        },
        "NodeChildren": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "id": {
                        "$ref": "#/definitions/NodeIdOrNull"
                    },
                    "template_from": {
                        "$ref": "#/definitions/NodeId"
                    },
                    "category": {
                        "$ref": "#/definitions/NodeCategory"
                    },
                    "title": {
                        "type": "string"
                    },
                    "description": {
                        "type": "string"
                    },
                    "node_license": {
                        "$ref": "#/definitions/NodeLicense"
                    },
                    "public": {
                        "type": "boolean"
                    },
                    "tags": {
                        "type": "array",
                        "items": {
                            "type": "string"
                        }
                    },
                    "children": {
                        "$ref": "#/definitions/NodeChildren"
                    },
                    "project_links": {
                        "type": "array",
                        "items": {
                            "$ref": "#/definitions/NodeId"
                        }
                    }
                },
                "anyOf": [
                    {
                        "properties": {
                            "id": {
                                "$ref": "#/definitions/NodeId"
                            }
                        },
                        "required": [
                            "id"
                        ]
                    },
                    {
                        "required": [
                            "category",
                            "title"
                        ]
                    }
                ],
                "additionalProperties": false
            }
        }
    }
}"""
file_path = 'projects_create_schema.json'


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
    with mock.patch('grdmcli.utils.read_json_file', return_value=json.loads(json_schema)):
        utils.check_json_schema(file_path, data)


def test_check_json_schema_error():
    with mock.patch('grdmcli.utils.read_json_file', return_value={}):
        with mock.patch('jsonschema.validate', side_effect=jsonschema.exceptions.ValidationError('error')):
            with pytest.raises(GrdmCliException):
                utils.check_json_schema(file_path, data)
