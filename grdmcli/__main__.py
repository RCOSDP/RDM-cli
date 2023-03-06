from __future__ import print_function

import argparse
import inspect  # noqa

import six
import sys

from grdmcli import __version__
from grdmcli.grdm_client import GRDMClient
from grdmcli.utils import inspect_info


def _add_subparser(parser, name, desc, aliases=None):
    if aliases is None:
        aliases = []

    options = {
        'description': desc,
        'formatter_class': argparse.RawDescriptionHelpFormatter,
    }

    if six.PY3:
        options['aliases'] = aliases

    return parser.add_parser(name, **options)


def _subparser_add_config_args(parser):
    parser.add_argument('--osf_token', help='the Personal Access Token')
    parser.add_argument('--osf_api_url', help='the API URL')


def main():
    # print('----{}:{}::{} from {}:{}::{}'.format(*inspect_info(inspect.currentframe(), inspect.stack())))
    client = GRDMClient()

    _have_config_parsers = []

    cli_parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    _have_config_parsers.append(cli_parser)
    cli_parser.add_argument('-v', '--version', action='version',
                            version=f'{__version__}')

    # dest=entity stores the name of the entity in a variable
    entity_subparsers = cli_parser.add_subparsers(dest='entity')

    # START entity=projects

    projects_parser = _add_subparser(entity_subparsers, 'projects', 'projects entity')
    # dest=command stores the name of the command in a variable
    projects_cmd_subparsers = projects_parser.add_subparsers(dest='command')

    # [For development] command=list
    projects_list_parser = _add_subparser(projects_cmd_subparsers, 'list', 'projects list command', ['ls', ])
    projects_list_parser.set_defaults(func='projects_list')
    # to add config args
    _have_config_parsers.append(projects_list_parser)

    # command=create
    projects_create_parser = _add_subparser(projects_cmd_subparsers, 'create', 'projects create command')
    projects_create_parser.set_defaults(func='projects_create')
    # to add template arg
    projects_create_parser.add_argument('--template', required=True,
                                        help='template file for projects/components')
    # to add config args
    _have_config_parsers.append(projects_create_parser)

    # END entity=projects

    # [START] entity=contributors

    contributors_parser = _add_subparser(entity_subparsers, 'contributors', 'contributors entity')
    # dest=command stores the name of the command in a variable
    contributors_cmd_subparsers = contributors_parser.add_subparsers(dest='command')

    # [For development] command=list
    contributors_list_parser = _add_subparser(contributors_cmd_subparsers, 'list', 'contributors list command', ['ls', ])
    contributors_list_parser.set_defaults(func='contributors_list')
    # to add config args
    _have_config_parsers.append(contributors_list_parser)

    # command=create
    contributors_create_parser = _add_subparser(contributors_cmd_subparsers, 'create', 'contributors create command')
    contributors_create_parser.set_defaults(func='contributors_create')
    # to add template arg
    contributors_create_parser.add_argument('--template', required=True,
                                            help='template file for contributors')
    # to add config args
    _have_config_parsers.append(contributors_create_parser)

    # [END] entity=contributors

    # [For development][START] entity=users

    users_parser = _add_subparser(entity_subparsers, 'users', 'users entity')
    # dest=command stores the name of the command in a variable
    users_cmd_subparsers = users_parser.add_subparsers(dest='command')

    # command=list
    users_list_parser = _add_subparser(users_cmd_subparsers, 'list', 'users list command', ['ls', ])
    users_list_parser.set_defaults(func='affiliated_users_list')
    # to add config args
    _have_config_parsers.append(users_list_parser)

    # [END] entity=contributors

    for _parser in _have_config_parsers:
        _subparser_add_config_args(_parser)

    # Python2 argparse exits with an error when no command is given
    if six.PY2 and len(sys.argv) == 1:
        print(f'Python2 argparse exits with an error when no command is given')
        cli_parser.print_help()
        return

    print('----{}:{}::{} from {}:{}::{}'.format(*inspect_info(inspect.currentframe(), inspect.stack())))
    cli_parser.parse_args(namespace=client)

    _args = []
    if client.entity:
        _args.append(client.entity)
        if client.command:
            _args.append(client.command)
    _args.append('-h')

    if hasattr(client, 'func'):
        # give functions a chance to influence the exit code this setup is,
        # so we can print usage for the sub command even if there was an error further down
        try:
            print(f'Start process')
            exit_code = client.__getattribute__(client.func)()
        except SystemExit as e:
            exit_code = e.code
        finally:
            print(f'End process')

        if exit_code is not None:
            cli_parser.parse_args(_args)
            sys.exit(exit_code)
    else:
        cli_parser.parse_args(_args)


if __name__ == "__main__":
    main()
