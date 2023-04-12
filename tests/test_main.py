import argparse
import sys
from unittest import mock

import pytest

from grdmcli.__main__ import (_add_subparser, _subparser_add_config_args, main)
from grdmcli.grdm_client import GRDMClient

__version__ = '0.0.1.dev0'

_create = 'contributors'


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


@mock.patch('six.PY2', True)
@mock.patch('sys.argv', ['grdmcli'])
def test_main__py2_and_arg_is_one(capfd):
    with mock.patch.object(GRDMClient, '__init__', return_value=None):
        main()
        captured = capfd.readouterr()
        assert captured.out.__contains__(f'Python2 argparse exits with an error when no command is given')


@mock.patch('six.PY2', False)
def test_main__exit_code_missing_api_url(monkeypatch, capfd):
    monkeypatch.setattr(sys, 'argv', ['grdmcli', _create, 'create', '--template', 'template-test'])
    exit_code = 'Missing API URL'
    with mock.patch.object(GRDMClient, f'{_create}_create', side_effect=SystemExit(exit_code)):
        with pytest.raises(SystemExit) as ex_info:
            main()
        assert ex_info.value.code == exit_code
        captured = capfd.readouterr()
        lines = captured.out.split('\n')
        assert lines[0] == f'Start process'
        assert lines[1] == f'End process'
        assert lines[2] == f'For help: grdmcli {_create} create --help'
        assert len(lines) == 4
        assert captured.err.__contains__(f'ERROR: {exit_code}')


@mock.patch('six.PY2', False)
def test_main__exit_code_keyboard_interrupt(monkeypatch, capfd):
    monkeypatch.setattr(sys, 'argv', ['grdmcli', _create, 'create', '--template', 'template-test'])
    exit_code = 'KeyboardInterrupt'
    with mock.patch.object(GRDMClient, f'{_create}_create', side_effect=KeyboardInterrupt):
        with pytest.raises(SystemExit) as ex_info:
            main()
        assert ex_info.value.code == exit_code
        captured = capfd.readouterr()
        lines = captured.out.split('\n')
        assert lines[0] == f'Start process'
        assert lines[1] == f'End process'
        assert lines[2] == f'For help: grdmcli {_create} create --help'
        assert captured.err.__contains__(f'ERROR: {exit_code}')
        assert len(lines) == 4


@mock.patch('six.PY2', False)
def test_main__exit_code_false(monkeypatch, capfd):
    monkeypatch.setattr(sys, 'argv', ['grdmcli', _create, 'create', '--template', 'template-test'])
    with mock.patch.object(GRDMClient, f'{_create}_create', return_value=None):
        main()
        lines = capfd.readouterr().out.split('\n')
        assert lines[0] == f'Start process'
        assert lines[1] == f'End process'


@mock.patch('six.PY2', False)
def test_main__argparse_not_set_default_function(monkeypatch, capfd):
    monkeypatch.setattr(sys, 'argv', ['grdmcli', _create, 'create', '--template', 'template-test'])
    with mock.patch('argparse.ArgumentParser.set_defaults', set_defaults=None):
        with pytest.raises(SystemExit) as ex_info:
            main()
        lines = capfd.readouterr().out.split('\n')
        assert lines[0] == f'usage: grdmcli {_create} create [-h] --template TEMPLATE'
        assert ex_info.value.code == 0
