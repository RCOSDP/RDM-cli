import argparse
from unittest import mock

from grdmcli import __main__ as main

__version__ = '0.0.1.dev0'


@mock.patch('six.PY3', True)
def test_add_subparser_aliases_none():
    cli_parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    cli_parser.add_argument('-v', '--version', action='version',
                            version=f'{__version__}')
    entity_subparsers = cli_parser.add_subparsers(dest='entity')
    contributors_parser = main._add_subparser(entity_subparsers, 'contributors', 'contributors entity')
    assert contributors_parser.description == 'contributors entity'
    assert len(entity_subparsers.choices) == 1
    assert type(contributors_parser.formatter_class) is type(argparse.ArgumentDefaultsHelpFormatter)


@mock.patch('six.PY3', True)
def test_add_subparser_aliases_exist():
    cli_parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    cli_parser.add_argument('-v', '--version', action='version',
                            version=f'{__version__}')
    entity_subparsers = cli_parser.add_subparsers(dest='entity')
    contributors_parser = main._add_subparser(entity_subparsers, 'contributors', 'contributors entity', ['aliases1'])
    assert contributors_parser.description == 'contributors entity'
    assert len(entity_subparsers.choices) == 2
    assert type(contributors_parser.formatter_class) is type(argparse.ArgumentDefaultsHelpFormatter)


@mock.patch('six.PY3', False)
def test_add_subparser_not_py3():
    cli_parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    cli_parser.add_argument('-v', '--version', action='version',
                            version=f'{__version__}')
    entity_subparsers = cli_parser.add_subparsers(dest='entity')
    contributors_parser = main._add_subparser(entity_subparsers, 'contributors', 'contributors entity', ['aliases1'])
    assert contributors_parser.description == 'contributors entity'
    assert len(entity_subparsers.choices) == 1
    assert type(contributors_parser.formatter_class) == type(argparse.ArgumentDefaultsHelpFormatter)


def test_subparser_add_config_args():
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    main._subparser_add_config_args(parser)
    args = parser.parse_args(["--osf_token", "osf_token", "--osf_api_url", "osf_api_url"])
    assert args.osf_token == 'osf_token'
    assert args.osf_api_url == 'osf_api_url'
