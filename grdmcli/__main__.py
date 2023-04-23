from __future__ import print_function

import argparse
import inspect  # noqa
import logging
import sys

import six

from . import __version__
from . import constants as const  # noqa
from .grdm_client import GRDMClient
from .utils import inspect_info  # noqa

logger = logging.getLogger(__name__)


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
    parser.add_argument('--osf_token', help='The Personal Access Token')
    parser.add_argument('--osf_api_url', help='The API URL')
    parser.add_argument('--disable_ssl_verify', action='store_true', help='Disable SSL verification')
    parser.add_argument('--debug', action='store_true', dest='enable_debug', help='Enable Debug mode')
    parser.add_argument('--verbose', action='store_true', dest='enable_verbose', help='Enable Verbose mode')


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

    # [START] block entity=contributors

    contributors_parser = _add_subparser(entity_subparsers, 'contributors', 'contributors entity')
    # dest=command stores the name of the command in a variable
    contributors_cmd_subparsers = contributors_parser.add_subparsers(dest='command')

    # block command=create
    contributors_create_parser = _add_subparser(contributors_cmd_subparsers, 'create', 'contributors create command')
    contributors_create_parser.set_defaults(func='contributors_create')
    # to add template arg
    contributors_create_parser.add_argument('--template', required=True,
                                            default=const.TEMPLATE_FILE_NAME_DEFAULT,
                                            help='The template file for contributors')
    contributors_create_parser.add_argument('--output_result_file',
                                            default=const.OUTPUT_RESULT_FILE_NAME_DEFAULT,
                                            help='The output result file path')
    # to add config args
    _have_config_parsers.append(contributors_create_parser)

    # [END] block entity=contributors

    for _parser in _have_config_parsers:
        _subparser_add_config_args(_parser)

    # Python2 argparse exits with an error when no command is given
    if six.PY2 and len(sys.argv) == 1:
        logger.warning('Python2 argparse exits with an error when no command is given')
        cli_parser.print_help()
        return

    cli_parser.parse_args(namespace=client)
    client.force_update_config()

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
            logger.info('Start process')
            exit_code = client.__getattribute__(client.func)()
        except SystemExit as e:
            exit_code = e.code
        except KeyboardInterrupt:
            exit_code = KeyboardInterrupt.__name__
        except Exception as e:
            exit_code = e
        finally:
            logger.info('End process')
            if exit_code:
                logger.error(exit_code)
                _args_str = ' '.join(_args)
                logger.info(f'For help: {cli_parser.prog} {_args_str}')
                # cli_parser.parse_args(_args)
                print('\n')
                sys.exit(exit_code)
    else:
        cli_parser.parse_args(_args)


if __name__ == '__main__':
    main()
