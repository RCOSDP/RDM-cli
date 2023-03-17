from __future__ import print_function

import argparse
import inspect  # noqa
import sys

import six

from . import __version__
from .grdm_client import GRDMClient
from .utils import inspect_info


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

    # [START] block entity=projects

    projects_parser = _add_subparser(entity_subparsers, 'projects', 'projects entity')
    # dest=command stores the name of the command in a variable
    projects_cmd_subparsers = projects_parser.add_subparsers(dest='command')

    # [For development] block command=list
    projects_list_parser = _add_subparser(projects_cmd_subparsers, 'list', 'projects list command', ['ls', ])
    projects_list_parser.set_defaults(func='projects_list')
    # to add config args
    _have_config_parsers.append(projects_list_parser)

    # block command=create
    projects_create_parser = _add_subparser(projects_cmd_subparsers, 'create', 'projects create command')
    projects_create_parser.set_defaults(func='projects_create')
    # to add template arg
    projects_create_parser.add_argument('--template', required=True,
                                        default='./template_file.json',
                                        help='template file for projects/components')
    projects_create_parser.add_argument('--output_result_file',
                                        default='./output_result_file.json',
                                        help='the output result file path')
    # to add config args
    _have_config_parsers.append(projects_create_parser)

    # [END] block entity=projects

    # [START] block entity=contributors

    contributors_parser = _add_subparser(entity_subparsers, 'contributors', 'contributors entity')
    # dest=command stores the name of the command in a variable
    contributors_cmd_subparsers = contributors_parser.add_subparsers(dest='command')

    # block command=create
    contributors_create_parser = _add_subparser(contributors_cmd_subparsers, 'create', 'contributors create command')
    contributors_create_parser.set_defaults(func='contributors_create')
    # to add template arg
    contributors_create_parser.add_argument('--template', required=True,
                                            default='./template_file.json',
                                            help='template file for contributors')
    contributors_create_parser.add_argument('--output_result_file',
                                            default='./output_result_file.json',
                                            help='the output result file path')
    # to add config args
    _have_config_parsers.append(contributors_create_parser)

    # [END] block entity=contributors

    for _parser in _have_config_parsers:
        _subparser_add_config_args(_parser)

    # Python2 argparse exits with an error when no command is given
    if six.PY2 and len(sys.argv) == 1:
        print(f'Python2 argparse exits with an error when no command is given')
        cli_parser.print_help()
        return

    cli_parser.parse_args(namespace=client)

    _args = []
    if client.entity:
        _args.append(client.entity)
        if client.command:
            _args.append(client.command)
    _args.append('--help')

    if hasattr(client, 'func'):
        exit_code = None
        # give functions a chance to influence the exit code this setup is,
        # so we can print usage for the sub command even if there was an error further down
        try:
            print(f'Start process')
            exit_code = client.__getattribute__(client.func)()
        except SystemExit as e:
            exit_code = e.code
        except KeyboardInterrupt as e:
            exit_code = KeyboardInterrupt.__name__
        finally:
            print(f'End process')
            if exit_code:
                print(f'ERROR: {exit_code}', file=sys.stderr)
                _args_str = ' '.join(_args)
                print(f'For help: {cli_parser.prog} {_args_str}')
                # cli_parser.parse_args(_args)
                sys.exit(exit_code)
    else:
        cli_parser.parse_args(_args)


if __name__ == "__main__":
    main()
