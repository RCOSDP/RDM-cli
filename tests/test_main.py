import argparse
import sys

import pytest
from unittest import mock

from grdmcli.__main__ import (_add_subparser, _subparser_add_config_args, main)
from grdmcli.grdm_client import GRDMClient

__version__ = '0.0.1.dev0'


class TestMainForProjectsCreate:

    @mock.patch('six.PY3', True)
    def test_add_subparser__aliases_none(self):
        cli_parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
        cli_parser.add_argument('-v', '--version', action='version',
                                version=f'{__version__}')
        entity_subparsers = cli_parser.add_subparsers(dest='entity')
        projects_parser = _add_subparser(entity_subparsers, 'projects', 'projects entity')
        assert projects_parser.description == 'projects entity'
        assert len(entity_subparsers.choices) == 1
        assert type(projects_parser.formatter_class) is type(argparse.ArgumentDefaultsHelpFormatter)

    @mock.patch('six.PY3', True)
    def test_add_subparser__aliases_exist(self):
        cli_parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
        cli_parser.add_argument('-v', '--version', action='version',
                                version=f'{__version__}')
        entity_subparsers = cli_parser.add_subparsers(dest='entity')
        projects_parser = _add_subparser(entity_subparsers, 'projects', 'projects entity',
                                         ['aliases1'])
        assert projects_parser.description == 'projects entity'
        assert len(entity_subparsers.choices) == 2
        assert type(projects_parser.formatter_class) is type(argparse.ArgumentDefaultsHelpFormatter)

    @mock.patch('six.PY3', False)
    def test_add_subparser__not_py3(self):
        cli_parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
        cli_parser.add_argument('-v', '--version', action='version',
                                version=f'{__version__}')
        entity_subparsers = cli_parser.add_subparsers(dest='entity')
        projects_parser = _add_subparser(entity_subparsers, 'projects', 'projects entity',
                                         ['aliases1'])
        assert projects_parser.description == 'projects entity'
        assert len(entity_subparsers.choices) == 1
        assert type(projects_parser.formatter_class) == type(argparse.ArgumentDefaultsHelpFormatter)

    def test_subparser_add_config_args__success(self):
        parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
        _subparser_add_config_args(parser)
        args = parser.parse_args(["--osf_token", "osf_token", "--osf_api_url", "osf_api_url"])
        assert args.osf_token == 'osf_token'
        assert args.osf_api_url == 'osf_api_url'

    @mock.patch('six.PY2', True)
    @mock.patch('sys.argv', ['grdmcli'])
    def test_main__py2_and_arg_is_one(self, capfd):
        with mock.patch.object(GRDMClient, '__init__', return_value=None):
            main()
            captured = capfd.readouterr()
            assert captured.out.__contains__(f'Python2 argparse exits with an error when no command is given')

    @mock.patch('six.PY2', False)
    @mock.patch('sys.exit', side_effect=Exception())
    def test_main__exit_code_missing_api_url(self, mocker, monkeypatch, capfd):
        monkeypatch.setattr(sys, 'argv', ['grdmcli', 'projects', 'create', '--template', 'template-test'])
        exit_code = 'Missing API URL'
        with mock.patch.object(GRDMClient, "projects_create", side_effect=SystemExit(exit_code)):
            with pytest.raises(Exception) as error_msg:
                main()
                lines = capfd.readouterr().out.split('\n')
                assert lines[0] == f'Start process'
                assert lines[1] == f'End process'
                assert lines[3] == f'ERROR: {exit_code}'
                assert error_msg.value.args[0] == exit_code

    @mock.patch('six.PY2', False)
    @mock.patch('sys.exit', side_effect=Exception())
    def test_main__exit_code_keyboard_interrupt(self, mocker, monkeypatch, capfd):
        monkeypatch.setattr(sys, 'argv', ['grdmcli', 'projects', 'create', '--template', 'template-test'])
        exit_code = 'KeyboardInterrupt'
        with mock.patch.object(GRDMClient, "projects_create", side_effect=KeyboardInterrupt):
            with pytest.raises(Exception):
                main()
                lines = capfd.readouterr().out.split('\n')
                assert lines[0] == f'Start process'
                assert lines[1] == f'End process'
                assert lines[3].__contains__(f'ERROR: {exit_code}')
                assert lines[4] == 'For help: grdmcli projects create --help'
        mocker.assert_called_once_with(exit_code)

    @mock.patch('six.PY2', False)
    def test_main__exit_code_false(self, monkeypatch, capfd):
        monkeypatch.setattr(sys, 'argv', ['grdmcli', 'projects', 'create', '--template', 'template-test'])
        with mock.patch.object(GRDMClient, "projects_create", return_value=None):
            main()
            lines = capfd.readouterr().out.split('\n')
            assert lines[0] == f'Start process'
            assert lines[1] == f'End process'

    @mock.patch('six.PY2', False)
    @mock.patch('sys.exit', side_effect=Exception())
    def test_main__argparse_not_set_default_function(self, mocker, monkeypatch, capfd):
        monkeypatch.setattr(sys, 'argv', ['grdmcli', 'projects', 'create', '--template', 'template-test'])
        with mock.patch('argparse.ArgumentParser.set_defaults', set_defaults=None):
            with pytest.raises(Exception):
                main()
            lines = capfd.readouterr().out.split('\n')
            assert lines[0] == 'usage: grdmcli projects create [-h] --template TEMPLATE'
            mocker.assert_called_once_with(0)
