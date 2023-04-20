"""Utility functions

Helpers and other assorted functions.
"""

import inspect
import json
import logging

import jsonschema

from grdmcli.exceptions import GrdmCliException
from . import constants as const  # noqa

__all__ = [
    'inspect_info',
    'read_json_file',
    'write_json_file',
    'check_json_schema',
]

logger = logging.getLogger(__name__)


def inspect_info(current_frame, stack_info):
    frame_info, stack_first = inspect.getframeinfo(current_frame), stack_info[1]
    return frame_info[0], frame_info[1], frame_info[2], stack_first[1], stack_first[2], stack_first[3]


def read_json_file(file_path):
    """Read json file

    Args:
        file_path (String): file path for read

    Returns:
        json string

    Raises:
        Exception: message "Cannot read json file"
    """
    with open(file_path, "r", encoding='utf-8') as read_file:
        try:
            input_data = json.load(read_file)
            return input_data
        except Exception as exc:
            raise GrdmCliException("Cannot read json file", exc)


def write_json_file(file, data):
    """Write json file

    Args:
        file (String): string file path
        data (Dict): json dict

    Raises:
        Exception: message "Cannot write json file"
    """
    with open(file, "w", encoding='utf-8') as write_file:
        try:
            json.dump(data, write_file, ensure_ascii=False, indent=4, sort_keys=False)
            logger.info(f'File was written successfully: {file}')
        except Exception as exc:
            raise GrdmCliException('Cannot write json file', exc)


def check_json_schema(schema_file_path, data):
    """Check json schema

    Args:
        schema_file_path (String): String json schema file path
        data (String): String json data

    Raises:
        Exception: json validate error message
    """
    try:
        schema = read_json_file(schema_file_path)
        jsonschema.validate(data, schema=schema)
    except jsonschema.exceptions.ValidationError as json_error:
        raise GrdmCliException(json_error.__dict__)
