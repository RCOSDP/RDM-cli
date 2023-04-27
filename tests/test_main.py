import argparse
import logging
import sys
from unittest import mock

import pytest

from grdmcli.__main__ import (
    _add_subparser,
    _subparser_add_config_args,
    main
)
from grdmcli.grdm_client import GRDMClient
from tests.utils import *


@pytest.fixture(autouse=True)
def set_log_level(caplog):
    caplog.clear()
    caplog.set_level(logging.DEBUG)


__version__ = '0.0.1.dev0'

_create = 'projects'


@mock.patch('six.PY3', True)
def test_add_subparser__aliases_none():
    cli_parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    cli_parser.add_argument('-v', '--version', action='version',
                            version=f'{__version__}')
    entity_subparsers = cli_parser.add_subparsers(dest='entity')
    _parser = _add_subparser(entity_subparsers, _create, f'{_create} entity')
    assert _parser.description == f'{_create} entity'
    assert len(entity_subparsers.choices) == 1
    assert type(_parser.formatter_class) is type(argparse.ArgumentDefaultsHelpFormatter)


@mock.patch('six.PY3', True)
def test_add_subparser__aliases_exist():
    cli_parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    cli_parser.add_argument('-v', '--version', action='version',
                            version=f'{__version__}')
    entity_subparsers = cli_parser.add_subparsers(dest='entity')
    _parser = _add_subparser(entity_subparsers, _create, f'{_create} entity',
                             ['aliases1'])
    assert _parser.description == f'{_create} entity'
    assert len(entity_subparsers.choices) == 2
    assert type(_parser.formatter_class) is type(argparse.ArgumentDefaultsHelpFormatter)


@mock.patch('six.PY3', False)
def test_add_subparser__not_py3():
    cli_parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    cli_parser.add_argument('-v', '--version', action='version',
                            version=f'{__version__}')
    entity_subparsers = cli_parser.add_subparsers(dest='entity')
    subparser = _add_subparser(entity_subparsers, _create, f'{_create} entity',
                               ['aliases1'])
    assert subparser.description == f'{_create} entity'
    assert len(entity_subparsers.choices) == 1
    assert type(subparser.formatter_class) is type(argparse.ArgumentDefaultsHelpFormatter)


def test_subparser_add_config_args__success():
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    _subparser_add_config_args(parser)
    args = parser.parse_args(["--osf_token", "osf_token", "--osf_api_url", "osf_api_url"])
    assert args.osf_token == 'osf_token'
    assert args.osf_api_url == 'osf_api_url'
    assert not args.enable_debug
    assert not args.enable_verbose
    assert not args.disable_ssl_verify


@mock.patch('six.PY2', True)
@mock.patch('sys.argv', ['grdmcli'])
def test_main__py2_and_arg_is_one(caplog):
    with mock.patch.object(GRDMClient, '__init__', return_value=None):
        main()
    assert len(caplog.records) == 1
    assert caplog.records[0].levelname == warning_level_log
    assert caplog.records[0].message.__contains__(f'Python2 argparse exits with an error when no command is given')


@mock.patch('six.PY2', False)
def test_main__exit_code_missing_api_url(monkeypatch, caplog):
    monkeypatch.setattr(sys, 'argv', ['grdmcli', _create, 'create', '--template', 'template-test'])
    exit_code = 'Missing API URL'
    with pytest.raises(SystemExit) as ex_info:
        with mock.patch('grdmcli.grdm_client.common.os.path.exists', return_value=False):
            with mock.patch.object(GRDMClient, f'{_create}_create', side_effect=SystemExit(exit_code)):
                main()
    assert ex_info.value.code == exit_code
    assert len(caplog.records) == 5
    assert 'Missing the config file' in caplog.records[0].message
    assert caplog.records[1].message == 'Start process'
    assert caplog.records[2].message == 'End process'
    assert caplog.records[3].message == 'Missing API URL'
    assert caplog.records[4].message == f'For help: grdmcli {_create} create --help'


@mock.patch('six.PY2', False)
def test_main__exit_code_keyboard_interrupt(monkeypatch, caplog):
    monkeypatch.setattr(sys, 'argv', ['grdmcli', _create, 'create', '--template', 'template-test'])
    exit_code = 'KeyboardInterrupt'
    with mock.patch.object(GRDMClient, f'{_create}_create', side_effect=KeyboardInterrupt):
        with mock.patch('grdmcli.grdm_client.common.os.path.exists', return_value=False):
            with pytest.raises(SystemExit) as ex_info:
                main()
        assert ex_info.value.code == exit_code
        assert len(caplog.records) == 5
        assert caplog.records[0].levelname == warning_level_log
        assert 'Missing the config file' in caplog.records[0].message
        assert caplog.records[1].levelname == info_level_log
        assert caplog.records[1].message == f'Start process'
        assert caplog.records[2].levelname == info_level_log
        assert caplog.records[2].message == f'End process'
        assert caplog.records[3].levelname == error_level_log
        assert caplog.records[3].message == f'{exit_code}'
        assert caplog.records[4].levelname == info_level_log
        assert caplog.records[4].message == f'For help: grdmcli {_create} create --help'


@mock.patch('six.PY2', False)
def test_main__exit_code_exception(monkeypatch, caplog):
    monkeypatch.setattr(sys, 'argv', ['grdmcli', _create, 'create', '--template', 'template-test'])
    exit_code = 'error'
    with mock.patch.object(GRDMClient, f'{_create}_create', side_effect=Exception(exit_code)):
        with mock.patch('grdmcli.grdm_client.common.os.path.exists', return_value=False):
            with pytest.raises(SystemExit) as ex_info:
                main()
        assert str(ex_info.value.code) == exit_code
        assert len(caplog.records) == 5
        assert caplog.records[0].levelname == warning_level_log
        assert 'Missing the config file' in caplog.records[0].message
        assert caplog.records[1].levelname == info_level_log
        assert caplog.records[1].message == f'Start process'
        assert caplog.records[2].levelname == info_level_log
        assert caplog.records[2].message == f'End process'
        assert caplog.records[3].levelname == error_level_log
        assert caplog.records[3].message == f'{exit_code}'
        assert caplog.records[4].levelname == info_level_log
        assert caplog.records[4].message == f'For help: grdmcli {_create} create --help'


@mock.patch('six.PY2', False)
def test_main__exit_code_false(monkeypatch, caplog):
    monkeypatch.setattr(sys, 'argv', ['grdmcli', _create, 'create', '--template', 'template-test'])
    with mock.patch.object(GRDMClient, f'{_create}_create', return_value=None):
        with mock.patch('grdmcli.grdm_client.common.os.path.exists', return_value=False):
            main()
    assert len(caplog.records) == 3
    assert caplog.records[0].levelname == warning_level_log
    assert 'Missing the config file' in caplog.records[0].message
    assert caplog.records[1].levelname == info_level_log
    assert caplog.records[1].message == f'Start process'
    assert caplog.records[2].levelname == info_level_log
    assert caplog.records[2].message == f'End process'


@mock.patch('six.PY2', False)
def test_main__argparse_not_set_default_function(monkeypatch, capfd):
    monkeypatch.setattr(sys, 'argv', ['grdmcli', _create, 'create', '--template', 'template-test'])
    with pytest.raises(SystemExit) as ex_info:
        with mock.patch('argparse.ArgumentParser.set_defaults', set_defaults=None):
            main()
    assert capfd.readouterr().out.__contains__(f'usage: grdmcli {_create} create [-h] --template TEMPLATE')
    assert ex_info.value.code == 0
