import configparser
import inspect
import json
import os
import sys
from argparse import Namespace
from datetime import datetime
from pathlib import Path
from pprint import pprint  # noqa
from types import SimpleNamespace

import requests
import validators
from validators import ValidationFailure

from grdmcli import constants as const
from . import status
from .utils import *


class GRDMClient(Namespace):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self._meta = {}
        self.config_file = None

        self.user = None
        self.is_authenticated = False
        self.affiliated_institutions = []
        self.affiliated_users = []

        self.projects = []
        self.created_projects = []

    def _request(self, method, url, params=None, data=None, headers=None):
        print('----{}:{}::{} from {}:{}::{}'.format(*inspect_info(inspect.currentframe(), inspect.stack())))
        if isinstance(validators.url(url, public=False), ValidationFailure):
            url = f'{self.osf_api_url}{url}'

        if data is None:
            data = {}

        if headers is None:
            headers = {}

        _params = {
            const.PAGE_SIZE_QUERY_PARAM: const.MAX_PAGE_SIZE,
            const.ORDERING_QUERY_PARAM: const.ORDERING_BY,
        }

        if isinstance(params, dict):
            _params.update(params)

        headers.update({
            "Authorization": f"Bearer {self.osf_token}",
            "Content-Type": "application/json",
        })

        _response = requests.request(method, url, params=_params, data=json.dumps(data), headers=headers)

        if not status.is_success(_response.status_code):
            # pprint(_response.json())
            # Parse JSON into an object with attributes corresponding to dict keys.
            response = json.loads(_response.content, object_hook=lambda d: SimpleNamespace(**d))
            sys.exit(response.errors[0].detail)

        return _response

    def _check_config(self, verbose=True):
        """ The priority order
        - Command line arguments
        - Config file attributes
        - Environment variables
        """
        print('----{}:{}::{} from {}:{}::{}'.format(*inspect_info(inspect.currentframe(), inspect.stack())))

        if self.is_authenticated:
            return True

        # get from config property
        # print(f'get from config property')
        if self.config_file is None:
            self.config_file = Path(os.getcwd()) / const.CONFIG_FILENAME

        if os.path.exists(self.config_file):
            config = configparser.ConfigParser()
            # print(f'config_file {self.config_file}')
            config.read(self.config_file)
            config_dict = dict(config.items(const.CONFIG_SECTION))
            if self.osf_api_url is None:
                self.osf_api_url = config_dict.get(const.OSF_API_URL_VAR_NAME.lower())
            if self.osf_token is None:
                self.osf_token = config_dict.get(const.OSF_TOKEN_VAR_NAME.lower())
        else:
            self.config_file = None

        # get from environment variable
        # print(f'get from environment variable')
        if self.osf_api_url is None:
            self.osf_api_url = os.environ.get(const.OSF_API_URL_VAR_NAME)
        if self.osf_token is None:
            self.osf_token = os.environ.get(const.OSF_TOKEN_VAR_NAME)

        if isinstance(validators.url(self.osf_api_url, public=False), ValidationFailure):
            sys.exit('The API URL is invalid')

        if not self.osf_token:
            sys.exit('Missing Personal Access Token')

        self._users_me(verbose)

    def _users_me(self, verbose=True):
        """ Get the currently logged-in user """
        print('----{}:{}::{} from {}:{}::{}'.format(*inspect_info(inspect.currentframe(), inspect.stack())))

        _response = self._request('GET', 'users/me/', params={}, data={})

        # pprint(_response.json())
        # Parse JSON into an object with attributes corresponding to dict keys.
        response = json.loads(_response.content, object_hook=lambda d: SimpleNamespace(**d))

        self.is_authenticated = True
        self.user = response.data

        if verbose:
            print(f'[For development]You are logged in as:')
            print(f'\'{self.user.id}\' - {self.user.attributes.email} \'{self.user.attributes.full_name}\'')

            self._users_me_affiliated_institutions()
            self._users_me_affiliated_users()
            self._licenses()

    def _users_me_affiliated_institutions(self, verbose=True):
        """For development"""
        print('----{}:{}::{} from {}:{}::{}'.format(*inspect_info(inspect.currentframe(), inspect.stack())))

        if not self.user:
            sys.exit('Missing currently logged-in user')

        # users/{user.id}/institutions/
        _response = self._request('GET', self.user.relationships.institutions.links.related.href, params={const.ORDERING_QUERY_PARAM: 'name'})

        # pprint(_response.json())
        # Parse JSON into an object with attributes corresponding to dict keys.
        response = json.loads(_response.content, object_hook=lambda d: SimpleNamespace(**d))

        self.affiliated_institutions = response.data
        _institutions_numb = response.links.meta.total
        self._meta.update({'_institutions': _institutions_numb})

        if verbose:
            print(f'[For development]List of affiliated institutions. [{_institutions_numb}]')
            for inst in self.affiliated_institutions:
                print(f'\'{inst.id}\' - \'{inst.attributes.name}\' [{inst.type}][{inst.attributes.description[:10]}...]')

    def _users_me_affiliated_users(self, verbose=True):
        """For development"""
        print('----{}:{}::{} from {}:{}::{}'.format(*inspect_info(inspect.currentframe(), inspect.stack())))

        if not self.user:
            sys.exit('Missing currently logged-in user')
        if not self.affiliated_institutions:
            sys.exit('Missing currently logged-in user\'s affiliated institutions')

        _users_numb = 0

        for inst in self.affiliated_institutions:
            # institutions/{inst.id}/users/
            _response = self._request('GET', inst.relationships.users.links.related.href, params={const.ORDERING_QUERY_PARAM: 'full_name'})

            # pprint(_response.json())
            # Parse JSON into an object with attributes corresponding to dict keys.
            response = json.loads(_response.content, object_hook=lambda d: SimpleNamespace(**d))

            self.affiliated_users.extend(response.data)
            _users_numb = _users_numb + response.links.meta.total

        self._meta.update({'_users': _users_numb})

        if verbose:
            print(f'[For development]List of affiliated institutions\' users. [{_users_numb}]')
            for user in self.affiliated_users:
                print(f'\'{user.id}\' - \'{user.attributes.full_name}\'')

    def _licenses(self, verbose=True):
        """For development"""
        print('----{}:{}::{} from {}:{}::{}'.format(*inspect_info(inspect.currentframe(), inspect.stack())))

        if not self.user:
            sys.exit('Missing currently logged-in user')

        print(f'[For development]GET List of licenses')
        _response = self._request('GET', 'licenses/', params={const.ORDERING_QUERY_PARAM: 'name'}, data={}, )

        # pprint(_response.json())
        # Parse JSON into an object with attributes corresponding to dict keys.
        response = json.loads(_response.content, object_hook=lambda d: SimpleNamespace(**d))

        self.licenses = response.data
        _licenses_numb = response.links.meta.total
        self._meta.update({'_licenses': _licenses_numb})

        if verbose:
            print(f'[For development]List of licenses. [{_licenses_numb}]')
            for _license in self.licenses:
                print(f'\'{_license.id}\' - \'{_license.attributes.name}\' [{_license.type}]')

    def projects_list(self, verbose=True):
        """For development"""
        print('----{}:{}::{} from {}:{}::{}'.format(*inspect_info(inspect.currentframe(), inspect.stack())))

        self._check_config()

        print(f'[For development]GET List of projects')
        _response = self._request('GET', 'nodes/', params={const.ORDERING_QUERY_PARAM: 'title'}, data={}, )

        # pprint(_response.json())
        # Parse JSON into an object with attributes corresponding to dict keys.
        response = json.loads(_response.content, object_hook=lambda d: SimpleNamespace(**d))

        self.projects = response.data
        _projects_numb = response.links.meta.total
        self._meta.update({'_projects': _projects_numb})

        if verbose:
            print(f'[For development]List of projects are those which are public or which the user has access to view. [{_projects_numb}]')
            for project in self.projects:
                print(f'\'{project.id}\' - \'{project.attributes.title}\' [{project.type}][{project.attributes.category}]')

    def projects_contributors_list(self, verbose=True):
        """For development"""
        print('----{}:{}::{} from {}:{}::{}'.format(*inspect_info(inspect.currentframe(), inspect.stack())))

        self._check_config()

        print(f'GET List of contributors')
        sys.exit(f'TODO {inspect.stack()[0][3]}')

    def _projects_load_project(self, pk, verbose=True):
        print('----{}:{}::{} from {}:{}::{}'.format(*inspect_info(inspect.currentframe(), inspect.stack())))
        return {}

    def _projects_fork_project(self, pk, verbose=True):
        print('----{}:{}::{} from {}:{}::{}'.format(*inspect_info(inspect.currentframe(), inspect.stack())))
        return {}

    def _projects_create_project(self, node_object, verbose=True):
        print('----{}:{}::{} from {}:{}::{}'.format(*inspect_info(inspect.currentframe(), inspect.stack())))
        _today_str = datetime.today().strftime('%Y-%m-%d %H:%M:%S')
        _project = node_object

        # initial
        _category = _project.get('category')
        _title = _project.get('title')
        _attributes = {
            'category': _category,
            'title': f'[{_today_str}] {_title}',
        }
        _relationships = {}

        # update template_from
        _template_from = _project.get('template_from')
        if _template_from:
            _attributes['template_from'] = _template_from

        # update description
        _description = _project.get('description', '')
        _attributes['description'] = _description

        # update description
        _public = _project.get('public')
        _attributes['public'] = _public

        # update description
        _tags = _project.get('tags', [])
        _attributes['tags'] = _tags

        # update node_license
        _license = _project.get('node_license')
        if _license:
            _relationships['license'] = {
                'data': {
                    'type': 'licenses',
                    'id': _license.get('id')
                }
            }

            _attributes['node_license'] = {
                'copyright_holders': _license.get('copyright_holders'),
                'year': _license.get('year')
            }

        _data = {
            'data': {
                'type': 'nodes',
                'attributes': _attributes,
                'relationships': _relationships
            }
        }

        _response = self._request('POST', 'nodes/', params={}, data=_data, )

        # pprint(_response.json())
        # Parse JSON into an object with attributes corresponding to dict keys.
        response = json.loads(_response.content, object_hook=lambda d: SimpleNamespace(**d))

        project = response.data

        return project

    def _projects_add_component(self, project, node, verbose=True):
        print('----{}:{}::{} from {}:{}::{}'.format(*inspect_info(inspect.currentframe(), inspect.stack())))
        _children = node.get('children', [])
        _project_links = node.get('project_links', [])

        # create Components
        for _comp in _children:
            component = self._projects_add_component(project, _comp)
            self.created_projects.append(component)

        # link a project (pointer)
        for _node in _project_links:
            self._projects_link_project(project, _node)

        return {}

    def _projects_link_project(self, project, node, verbose=True):
        print('----{}:{}::{} from {}:{}::{}'.format(*inspect_info(inspect.currentframe(), inspect.stack())))
        return {}

    def projects_create(self, verbose=True):
        """  """
        print('----{}:{}::{} from {}:{}::{}'.format(*inspect_info(inspect.currentframe(), inspect.stack())))

        if not os.path.exists(const.TEMPLATE_SCHEMA_PROJECTS):
            sys.exit(f'Missing the template schema {const.TEMPLATE_SCHEMA_PROJECTS}')

        if not os.path.exists(self.template):
            sys.exit('Missing the template file')

        self._check_config(verbose=False)

        print(f'CREATE Following the template of projects')

        try:
            _projects_struct = read_json_file(self.template)

            # check json schema
            check_json_schema(const.TEMPLATE_SCHEMA_PROJECTS, _projects_struct)

            _projects = _projects_struct.get('projects', [])
            for _project in _projects:
                _id = _project.get('id')
                _fork_id = _project.get('fork_id')
                _children = _project.get('children', [])
                _project_links = _project.get('project_links', [])

                if _id:
                    project = self._projects_load_project(_id)
                elif _fork_id:
                    project = self._projects_fork_project(_fork_id)
                else:
                    project = self._projects_create_project(_project)

                self.created_projects.append(project)

                # create Components
                for _comp in _children:
                    component = self._projects_add_component(project, _comp)
                    self.created_projects.append(component)

                # link a project (pointer)
                for _node in _project_links:
                    self._projects_link_project(project, _node)
        except Exception as exce:
            print('!---{}:{}::{} from {}:{}::{}'.format(*inspect_info(inspect.currentframe(), inspect.stack())))
            sys.exit(f'Exception {exce}')
        finally:
            if verbose:
                print(f'Created projects. [{len(self.created_projects)}]')
                for _project in self.created_projects:
                    print(f'\'{_project.id}\' - \'{_project.attributes.title}\' [{_project.type}][{_project.attributes.category}]')

    def contributors_create(self, verbose=True):
        """  """
        print('----{}:{}::{} from {}:{}::{}'.format(*inspect_info(inspect.currentframe(), inspect.stack())))

        if not os.path.exists(const.TEMPLATE_SCHEMA_CONTRIBUTORS):
            sys.exit(f'Missing the template schema {const.TEMPLATE_SCHEMA_CONTRIBUTORS}')

        if not os.path.exists(self.template):
            sys.exit('Missing the template file')

        self._check_config()

        print(f'CREATE Following the template of contributors')
        sys.exit(f'TODO {inspect.stack()[0][3]}')
