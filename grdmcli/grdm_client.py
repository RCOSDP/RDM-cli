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

here = os.path.abspath(os.path.dirname(__file__))
IGNORE_PROJECTS = ['z6dne', 'ega24', 'm7ah9', '4hexc']
is_clear = True


class GRDMClient(Namespace):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self._meta = {}
        self.config_file = None
        self.template = './template_file.json'
        self.output_result_file = './output_result_file.json'

        self.user = None
        self.is_authenticated = False
        self.affiliated_institutions = []
        self.affiliated_users = []

        self.projects = []
        self.created_projects = []
        self.created_project_contributors = {}

    @property
    def template_schema_projects(self):
        return os.path.abspath(os.path.join(os.path.dirname(here), const.TEMPLATE_SCHEMA_PROJECTS))

    @property
    def template_schema_contributors(self):
        return os.path.abspath(os.path.join(os.path.dirname(here), const.TEMPLATE_SCHEMA_CONTRIBUTORS))

    def _request(self, method, url, params=None, data=None, headers=None):
        """  """
        # print('----{}:{}::{} from {}:{}::{}'.format(*inspect_info(inspect.currentframe(), inspect.stack())))

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
            print(f'WARN Exception: {response.errors[0].detail}')
            return None, response.errors[0].detail

        return _response, None

    def _check_config(self, verbose=True):
        """ The priority order
        - Command line arguments
        - Config file attributes
        - Environment variables
        """
        print('----{}:{}::{} from {}:{}::{}'.format(*inspect_info(inspect.currentframe(), inspect.stack())))

        if self.is_authenticated:
            return True

        print(f'Try get from config property')
        if self.config_file is None:
            self.config_file = Path(os.getcwd()) / const.CONFIG_FILENAME

        if os.path.exists(self.config_file):
            config = configparser.ConfigParser()
            print(f'config_file: {self.config_file}')
            config.read(self.config_file)
            config_dict = dict(config.items(const.CONFIG_SECTION))
            if self.osf_api_url is None:
                self.osf_api_url = config_dict.get(const.OSF_API_URL_VAR_NAME.lower())
            if self.osf_token is None:
                self.osf_token = config_dict.get(const.OSF_TOKEN_VAR_NAME.lower())
        else:
            self.config_file = None
            print(f'Missing the config file {const.CONFIG_FILENAME}')
            sys.exit(f'Missing the config file {const.CONFIG_FILENAME}')

        print(f'Try get from environment variable')
        if self.osf_api_url is None:
            self.osf_api_url = os.environ.get(const.OSF_API_URL_VAR_NAME)
        if self.osf_token is None:
            self.osf_token = os.environ.get(const.OSF_TOKEN_VAR_NAME)

        if not self.osf_api_url:
            sys.exit('Missing API URL')

        if isinstance(validators.url(self.osf_api_url, public=False), ValidationFailure):
            sys.exit('The API URL is invalid')

        if not self.osf_token:
            sys.exit('Missing Personal Access Token')

        if not self.is_authenticated:
            print('Check Personal Access Token')
            self._users_me(verbose=verbose)

    def _users_me(self, ignore_error=True, verbose=True):
        """ Get the currently logged-in user """
        print('----{}:{}::{} from {}:{}::{}'.format(*inspect_info(inspect.currentframe(), inspect.stack())))

        print('GET the currently logged-in user')
        _response, _error_message = self._request('GET', 'users/me/', params={}, data={})
        if _error_message and not ignore_error:
            sys.exit(_error_message)
        _content = _response.content

        # pprint(_response.json())
        # Parse JSON into an object with attributes corresponding to dict keys.
        response = json.loads(_content, object_hook=lambda d: SimpleNamespace(**d))

        self.is_authenticated = True
        self.user = response.data

        if verbose:
            print(f'[For development]You are logged in as:')
            print(f'\'{self.user.id}\' - {self.user.attributes.email} \'{self.user.attributes.full_name}\'')

            self._users_me_affiliated_institutions()
            self._users_me_affiliated_users()
            self._licenses()

    def _users_me_affiliated_institutions(self, ignore_error=True, verbose=True):
        """For development"""
        print('----{}:{}::{} from {}:{}::{}'.format(*inspect_info(inspect.currentframe(), inspect.stack())))

        if not self.user:
            sys.exit('Missing currently logged-in user')

        # users/{user.id}/institutions/
        params = {const.ORDERING_QUERY_PARAM: 'name'}
        _response, _error_message = self._request('GET', self.user.relationships.institutions.links.related.href, params=params)
        if _error_message and not ignore_error:
            sys.exit(_error_message)
        _content = _response.content

        # pprint(_response.json())
        # Parse JSON into an object with attributes corresponding to dict keys.
        response = json.loads(_content, object_hook=lambda d: SimpleNamespace(**d))

        self.affiliated_institutions = response.data
        _institutions_numb = response.links.meta.total
        self._meta.update({'_institutions': _institutions_numb})

        if verbose:
            print(f'[For development]List of affiliated institutions. [{_institutions_numb}]')
            for inst in self.affiliated_institutions:
                print(f'\'{inst.id}\' - \'{inst.attributes.name}\' [{inst.type}][{inst.attributes.description[:10]}...]')

    def _users_me_affiliated_users(self, ignore_error=True, verbose=True):
        """For development"""
        print('----{}:{}::{} from {}:{}::{}'.format(*inspect_info(inspect.currentframe(), inspect.stack())))

        if not self.user:
            sys.exit('Missing currently logged-in user')
        if not self.affiliated_institutions:
            sys.exit('Missing currently logged-in user\'s affiliated institutions')

        _users_numb = 0

        for inst in self.affiliated_institutions:
            # institutions/{inst.id}/users/
            params = {const.ORDERING_QUERY_PARAM: 'full_name'}
            _response, _error_message = self._request('GET', inst.relationships.users.links.related.href, params=params)
            if _error_message and not ignore_error:
                sys.exit(_error_message)
            _content = _response.content

            # pprint(_response.json())
            # Parse JSON into an object with attributes corresponding to dict keys.
            response = json.loads(_content, object_hook=lambda d: SimpleNamespace(**d))

            self.affiliated_users.extend(response.data)
            _users_numb = _users_numb + response.links.meta.total

        self._meta.update({'_users': _users_numb})

        if verbose:
            print(f'[For development]List of affiliated institutions\' users. [{_users_numb}]')
            for user in self.affiliated_users:
                print(f'\'{user.id}\' - \'{user.attributes.full_name}\'')

    def _licenses(self, ignore_error=True, verbose=True):
        """For development"""
        print('----{}:{}::{} from {}:{}::{}'.format(*inspect_info(inspect.currentframe(), inspect.stack())))

        if not self.user:
            sys.exit('Missing currently logged-in user')

        print(f'[For development]GET List of licenses')
        params = {const.ORDERING_QUERY_PARAM: 'name'}
        _response, _error_message = self._request('GET', 'licenses/', params=params, data={}, )
        if _error_message and not ignore_error:
            sys.exit(_error_message)
        _content = _response.content

        # pprint(_response.json())
        # Parse JSON into an object with attributes corresponding to dict keys.
        response = json.loads(_content, object_hook=lambda d: SimpleNamespace(**d))

        self.licenses = response.data
        _licenses_numb = response.links.meta.total
        self._meta.update({'_licenses': _licenses_numb})

        if verbose:
            print(f'[For development]List of licenses. [{_licenses_numb}]')
            for _license in self.licenses:
                print(f'\'{_license.id}\' - \'{_license.attributes.name}\' [{_license.type}]')

    def projects_list(self, ignore_error=True, verbose=True):
        """For development"""
        print('----{}:{}::{} from {}:{}::{}'.format(*inspect_info(inspect.currentframe(), inspect.stack())))

        print(f'Check config and authenticate by token')
        self._check_config()

        print(f'[For development]GET List of projects')
        params = {const.ORDERING_QUERY_PARAM: 'title'}
        _response, _error_message = self._request('GET', 'nodes/', params=params, data={}, )
        if _error_message and not ignore_error:
            sys.exit(_error_message)
        _content = _response.content

        # pprint(_response.json())
        # Parse JSON into an object with attributes corresponding to dict keys.
        response = json.loads(_content, object_hook=lambda d: SimpleNamespace(**d))

        self.projects = response.data
        _projects_numb = response.links.meta.total
        self._meta.update({'_projects': _projects_numb})

        if verbose:
            print(f'[For development]List of projects are those which are public or which the user has access to view. [{_projects_numb}]')
            for project in self.projects:
                print(f'\'{project.id}\' - \'{project.attributes.title}\' [{project.type}][{project.attributes.category}]{project.attributes.tags}')
                if is_clear and project.id not in IGNORE_PROJECTS:
                    self._projects_delete_project(project.id, ignore_error=True, verbose=False)

        sys.exit()

    def _projects_fake_project_content_data(self, pk, verbose=True):
        """  """
        print('----{}:{}::{} from {}:{}::{}'.format(*inspect_info(inspect.currentframe(), inspect.stack())))

        _content = json.dumps({
            'data': {
                'id': pk,
                'type': 'nodes',
                'attributes': {
                    'title': 'N/A',
                    'category': 'N/A'
                },
                'relationships': {}
            }
        })

        if verbose:
            print(f'prepared project data: {_content}')

        return _content

    def _projects_prepare_project_data(self, node_object, verbose=True):
        """  """
        print('----{}:{}::{} from {}:{}::{}'.format(*inspect_info(inspect.currentframe(), inspect.stack())))

        _project = node_object

        # For development
        _today_str = datetime.today().strftime('%Y-%m-%d %H:%M:%S')

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
        _public = _project.get('public', False)
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

        if verbose:
            print(f'prepared project data: {_data}')

        return _data

    def _projects_delete_project(self, pk, ignore_error=True, verbose=True):
        """  """
        print('----{}:{}::{} from {}:{}::{}'.format(*inspect_info(inspect.currentframe(), inspect.stack())))

        print(f'DELETE Remove project \'{pk}\'')
        _response, _error_message = self._request('DELETE', 'nodes/{node_id}/'.format(node_id=pk), params={}, data={}, )
        if _error_message and not ignore_error:
            sys.exit(_error_message)

        if verbose:
            print(f'Deleted project: \'{pk}\'')

    def _projects_load_project(self, pk, is_fake=True, ignore_error=True, verbose=True):
        """  """
        print('----{}:{}::{} from {}:{}::{}'.format(*inspect_info(inspect.currentframe(), inspect.stack())))

        _content = None
        _faked_or_loaded = f'[loaded nodes/{pk}/]'

        if is_fake:
            _faked_or_loaded = '[faked]'
            _content = self._projects_fake_project_content_data(pk, verbose=False)

        print(f'GET Retrieve project {_faked_or_loaded}')
        if not is_fake:
            _response, _error_message = self._request('GET', 'nodes/{node_id}/'.format(node_id=pk), params={}, data={}, )
            if _error_message and not ignore_error:
                sys.exit(_error_message)
            _content = _response.content

        # pprint(_response.json())
        # Parse JSON into an object with attributes corresponding to dict keys.
        response = json.loads(_content, object_hook=lambda d: SimpleNamespace(**d))

        project = response.data

        if verbose:
            print(f'Loaded project:')
            print(f'\'{project.id}\' - \'{project.attributes.title}\' [{project.type}][{project.attributes.category}]')

        return project, json.loads(_content)['data']

    def _projects_fork_project(self, node_object, ignore_error=True, verbose=True):
        print('----{}:{}::{} from {}:{}::{}'.format(*inspect_info(inspect.currentframe(), inspect.stack())))

        _data = self._projects_prepare_project_data(node_object, verbose=False)
        pk = node_object['fork_id']

        print(f'POST Fork a project from nodes/{pk}/')
        _response, _error_message = self._request('POST', 'nodes/{node_id}/forks/'.format(node_id=pk), params={}, data=_data, )
        if _error_message and not ignore_error:
            sys.exit(_error_message)
        _content = _response.content

        # pprint(_response.json())
        # Parse JSON into an object with attributes corresponding to dict keys.
        response = json.loads(_content, object_hook=lambda d: SimpleNamespace(**d))

        project = response.data

        self.created_projects.append(project)

        if verbose:
            print(f'Forked project:')
            print(f'\'{project.id}\' - \'{project.attributes.title}\' [{project.type}][{project.attributes.category}]')

        return project, json.loads(_content)['data']

    def _projects_create_project(self, node_object, ignore_error=True, verbose=True):
        """  """
        print('----{}:{}::{} from {}:{}::{}'.format(*inspect_info(inspect.currentframe(), inspect.stack())))

        _data = self._projects_prepare_project_data(node_object, verbose=False)

        print(f'POST Create new project')
        _response, _error_message = self._request('POST', 'nodes/', params={}, data=_data, )
        if _error_message and not ignore_error:
            sys.exit(_error_message)
        _content = _response.content

        # pprint(_response.json())
        # Parse JSON into an object with attributes corresponding to dict keys.
        response = json.loads(_content, object_hook=lambda d: SimpleNamespace(**d))

        project = response.data

        self.created_projects.append(project)

        if verbose:
            print(f'Created project:')
            print(f'\'{project.id}\' - \'{project.attributes.title}\' [{project.type}][{project.attributes.category}]')

        return project, json.loads(_content)['data']

    def _projects_add_component(self, parent_id, node_object, ignore_error=True, verbose=True):
        """  """
        print('----{}:{}::{} from {}:{}::{}'.format(*inspect_info(inspect.currentframe(), inspect.stack())))

        _children = node_object.get('children', [])
        _project_links = node_object.get('project_links', [])

        _data = self._projects_prepare_project_data(node_object, verbose=False)

        print(f'POST Create new component to nodes/{parent_id}/')
        _response, _error_message = self._request('POST', 'nodes/{node_id}/children/'.format(node_id=parent_id), params={}, data=_data, )
        if _error_message and not ignore_error:
            sys.exit(_error_message)
        _content = _response.content

        # pprint(_response.json())
        # Parse JSON into an object with attributes corresponding to dict keys.
        response = json.loads(_content, object_hook=lambda d: SimpleNamespace(**d))

        project = response.data

        self.created_projects.append(project)

        if verbose:
            print(f'Create component:')
            print(f'\'{project.id}\' - \'{project.attributes.title}\' [{project.type}][{project.attributes.category}]')

        # link a project (pointer)
        for idx_nid, _node_id in enumerate(_project_links):
            print(f'JSONPOINTER ./project_links/{idx_nid}/')
            project_link, project_link_dict = self._projects_link_project(project.id, _node_id, verbose=True)

            # update output object
            _project_links[idx_nid] = project_link.id
            # _project_links[idx_nid] = project_link_dict

        # create Components
        for idx_c, _comp_dict in enumerate(_children):
            _comp_id = _comp_dict.get('id')
            if _comp_id:
                print(f'JSONPOINTER ./children/{idx_c}/ ignored')

                # update output object
                _children[idx_c] = None
                continue

            print(f'JSONPOINTER ./children/{idx_c}/')
            component, component_dict = self._projects_add_component(project.id, _comp_dict, ignore_error=True, verbose=True)

            # update output object
            _children[idx_c]['id'] = component.id
            _children[idx_c]['type'] = component.type
            # _children[idx_c].update(component_dict)

        # Delete None
        if _children:
            node_object['children'] = [_child for _child in _children if _child is not None]

        return project, json.loads(_content)['data']

    def _projects_link_project(self, node_id, pointer_id, ignore_error=True, verbose=True):
        print('----{}:{}::{} from {}:{}::{}'.format(*inspect_info(inspect.currentframe(), inspect.stack())))

        _data = {
            "data": {
                "type": "node_links",  # required
                "relationships": {
                    "nodes": {
                        "data": {
                            "type": "nodes",  # required
                            "id": pointer_id  # required
                        }
                    }
                }
            }
        }

        _response, _error_message = self._request('POST', 'nodes/{node_id}/node_links/'.format(node_id=node_id), params={}, data=_data, )
        if _error_message and not ignore_error:
            sys.exit(_error_message)
        _content = _response.content

        # pprint(_response.json())
        # Parse JSON into an object with attributes corresponding to dict keys.
        response = json.loads(_content, object_hook=lambda d: SimpleNamespace(**d))

        project_link = response.data
        project = project_link.embeds.target_node.data

        if verbose:
            print(f'Created Node Links:')
            print(f'\'{project_link.id}\' - [{project_link.type}]')
            print(f'\'{project.id}\' - \'{project.attributes.title}\' [{project.type}][{project.attributes.category}]')

        return project, json.loads(_content)['data']

    def projects_create(self, verbose=True):
        """ Create Projects/Components following the inputted template file
        """
        print('----{}:{}::{} from {}:{}::{}'.format(*inspect_info(inspect.currentframe(), inspect.stack())))

        if not os.path.exists(self.template_schema_projects):
            sys.exit(f'Missing the template schema {self.template_schema_projects}')

        if not os.path.exists(self.template):
            sys.exit('Missing the template file')

        print(f'Check config and authenticate by token')
        self._check_config(verbose=False)

        print(f'USE the template of projects: {self.template}')
        _projects_dict = read_json_file(self.template)

        try:
            # check json schema
            print(f'USE the template of projects: {self.template_schema_projects}')
            check_json_schema(self.template_schema_projects, _projects_dict)

            print(f'CREATE Following the template of projects')
            _projects = _projects_dict.get('projects', [])
            for idx, _project_dict in enumerate(_projects):
                _id = _project_dict.get('id')
                _fork_id = _project_dict.get('fork_id')
                _children = _project_dict.get('children', [])
                _project_links = _project_dict.get('project_links', [])

                if _id:
                    print(f'JSONPOINTER /projects/{idx}/id == {_id}')
                    project, _ = self._projects_load_project(_id, is_fake=True, ignore_error=True, verbose=True)

                    # update output object
                    _projects[idx] = None
                elif _fork_id:
                    print(f'JSONPOINTER /projects/{idx}/fork_id == {_fork_id}')
                    project, project_dict = self._projects_fork_project(_project_dict, ignore_error=True, verbose=True)

                    # update output object
                    _projects[idx]['id'] = project.id
                    _projects[idx]['type'] = project.type
                    # _projects[idx].update(project_dict)
                else:
                    print(f'JSONPOINTER /projects/{idx}/')
                    project, project_dict = self._projects_create_project(_project_dict, ignore_error=True, verbose=True)

                    # update output object
                    _projects[idx]['id'] = project.id
                    _projects[idx]['type'] = project.type
                    # _projects[idx].update(project_dict)

                # link a project (JSONPOINTER)
                for idx_nid, _node_id in enumerate(_project_links):
                    print(f'JSONPOINTER ./project_links/{idx_nid}/')
                    project_link, project_link_dict = self._projects_link_project(project.id, _node_id, ignore_error=True, verbose=True)

                    # update output object
                    _project_links[idx_nid] = project_link.id
                    # _project_links[idx_nid] = project_link_dict

                # create Components
                for idx_c, _comp_dict in enumerate(_children):
                    _comp_id = _comp_dict.get('id')
                    if _comp_id:
                        print(f'JSONPOINTER ./children/{idx_c}/ ignored')

                        # update output object
                        _children[idx_c] = None
                        continue

                    print(f'JSONPOINTER ./children/{idx_c}/')
                    component, component_dict = self._projects_add_component(project.id, _comp_dict, ignore_error=True, verbose=True)

                    # update output object
                    _children[idx_c]['id'] = component.id
                    _children[idx_c]['type'] = component.type
                    # _children[idx_c].update(component_dict)

                # Delete None
                if _children:
                    _project_dict['children'] = [_child for _child in _children if _child is not None]

            # Delete None
            _projects_dict['projects'] = [_prj for _prj in _projects if _prj is not None]
        except Exception as err:
            print(f'Exception {err}')
            # sys.exit(f'Exception {err}')
            raise err
        finally:
            if verbose:
                print(f'Created projects. [{len(self.created_projects)}]')
                for _project in self.created_projects:
                    print(f'\'{_project.id}\' - \'{_project.attributes.title}\' [{_project.type}][{_project.attributes.category}]')

        print(f'USE the output result file: {self.output_result_file}')
        write_json_file(self.output_result_file, _projects_dict)

        sys.exit()

    def _projects_list_project_contributors(self, pk, ignore_error=True, verbose=True):
        """  """
        print('----{}:{}::{} from {}:{}::{}'.format(*inspect_info(inspect.currentframe(), inspect.stack())))

        if not self.user:
            sys.exit('Missing currently logged-in user')

        print(f'GET List of contributors')
        params = {const.ORDERING_QUERY_PARAM: 'name'}
        _response, _error_message = self._request('GET', 'nodes/{node_id}/contributors/'.format(node_id=pk), params=params, data={}, )
        if _error_message and not ignore_error:
            print(f'WARN {_error_message}')
            sys.exit(_error_message)
        _content = _response.content

        # pprint(_response.json())
        # Parse JSON into an object with attributes corresponding to dict keys.
        response = json.loads(_content, object_hook=lambda d: SimpleNamespace(**d))

        contributors = response.data
        _contributors_numb = response.links.meta.total

        if verbose:
            print(f'List of contributors in project. [{_contributors_numb}]')
            for contributor in contributors:
                users = contributor.embeds.users.data.attributes
                attrs = contributor.attributes
                print(f'\'{contributor.id}\' - \'{users.full_name}\' [{contributor.type}][{attrs.permission}][{attrs.index}]')

        return contributors, json.loads(_content)['data']

    def _projects_delete_project_contributor(self, pk, user_id, ignore_error=True, verbose=True):
        """  """
        print('----{}:{}::{} from {}:{}::{}'.format(*inspect_info(inspect.currentframe(), inspect.stack())))

        print(f'DELETE Remove contributor \'{pk}-{user_id}\'')
        _url = 'nodes/{node_id}/contributors/{user_id}'.format(node_id=pk, user_id=user_id)
        _response, _error_message = self._request('DELETE', _url, params={}, data={}, )
        if _error_message and not ignore_error:
            sys.exit(_error_message)

        if verbose:
            print(f'Deleted contributor: \'{pk}-{user_id}\'')

    def _projects_prepare_contributor_data(self, contributor_object, index, verbose=True):
        """  """
        print('----{}:{}::{} from {}:{}::{}'.format(*inspect_info(inspect.currentframe(), inspect.stack())))

        _contributor = contributor_object

        # initial
        _user_id = _contributor.get('id')
        _bibliographic = _contributor.get('bibliographic')
        _permission = _contributor.get('permission', 'write')
        _attributes = {
                    "index": index,
                    "bibliographic": _bibliographic,
                    "permission": _permission
                }
        _relationships = {
                    "user": {
                        "data": {
                            "type": "users",
                            "id": _user_id
                        }
                    }
                }

        _data = {
            "data": {
                "type": "contributors",
                "attributes": _attributes,
                "relationships": _relationships
            }
        }

        if verbose:
            print(f'prepared contributor data: {_data}')

        return _data

    def _projects_add_contributor(self, pk, contributor_object, index, ignore_error=True, verbose=True):
        """  """
        print('----{}:{}::{} from {}:{}::{}'.format(*inspect_info(inspect.currentframe(), inspect.stack())))

        _data = self._projects_prepare_contributor_data(contributor_object, index, verbose=True)
        user_id = contributor_object['id']

        print(f'CREATE Add contributor \'{pk}-{user_id}\'')
        _url = 'nodes/{node_id}/contributors/'.format(node_id=pk)
        _response, _error_message = self._request('POST', _url, params={}, data=_data, )
        if _error_message and not ignore_error:
            sys.exit(_error_message)
        _content = _response.content

        # pprint(_response.json())
        # Parse JSON into an object with attributes corresponding to dict keys.
        response = json.loads(_content, object_hook=lambda d: SimpleNamespace(**d))

        contributor = response.data

        self.created_project_contributors[pk].append(contributor)

        if verbose:
            print(f'Created contributor: \'{pk}-{user_id}\'')
            users = contributor.embeds.users.data.attributes
            attrs = contributor.attributes
            print(f'\'{contributor.id}\' - \'{users.full_name}\' [{contributor.type}][{attrs.permission}][{attrs.index}]')

        return contributor, json.loads(_content)['data']

    def contributors_create(self, verbose=True):
        """  """
        print('----{}:{}::{} from {}:{}::{}'.format(*inspect_info(inspect.currentframe(), inspect.stack())))

        if not os.path.exists(self.template_schema_contributors):
            sys.exit(f'Missing the template schema {self.template_schema_contributors}')

        if not os.path.exists(self.template):
            sys.exit('Missing the template file')

        print(f'Check config and authenticate by token')
        self._check_config(verbose=False)

        print(f'USE the template of contributors: {self.template}')
        _projects_dict = read_json_file(self.template)

        try:
            # check json schema
            print(f'USE the template of projects: {self.template_schema_contributors}')
            check_json_schema(self.template_schema_contributors, _projects_dict)

            print(f'REMOVE/CREATE Following the template of contributors')
            _projects = _projects_dict.get('projects', [])
            for idx, _project_dict in enumerate(_projects):
                _id = _project_dict.get('id')
                _contributors = _project_dict.get('contributors', [])

                if not _id:
                    print(f'JSONPOINTER /projects/{idx}/id == {_id}')

                    # update output object
                    _projects[idx] = None
                    continue

                self.created_project_contributors[_id] = []
                current_user_contributor = None

                print(f'JSONPOINTER /projects/{idx}/')
                print(f'REMOVE Current contributors')
                old_contributors, _old_contributors_dict = self._projects_list_project_contributors(_id, verbose=True)
                for contributor in old_contributors:
                    if contributor.embeds.users.data.id == self.user.id:
                        self.created_project_contributors[_id].append(contributor)
                        current_user_contributor = contributor
                        continue
                    self._projects_delete_project_contributor(_id, contributor.embeds.users.data.id, verbose=True)

                # add contributors
                for idx_contr, _user_dict in enumerate(_contributors):
                    if _user_dict['id'] == self.user.id:
                        if current_user_contributor:
                            # update output object
                            _contributors[idx_contr]['id'] = current_user_contributor.id
                            _contributors[idx_contr]['type'] = current_user_contributor.type
                            _contributors[idx_contr]['index'] = current_user_contributor.attributes.index
                            # _contributors[idx].update(contributor_dict)
                        continue
                    print(f'JSONPOINTER ./contributors/{idx_contr}/')
                    contributor, contributor_dict = self._projects_add_contributor(_id, _user_dict, idx_contr, verbose=True)

                    # update output object
                    _contributors[idx_contr]['id'] = contributor.id
                    _contributors[idx_contr]['type'] = contributor.type
                    _contributors[idx_contr]['index'] = contributor.attributes.index
                    # _contributors[idx].update(contributor_dict)

                # Delete None
                if _contributors:
                    _project_dict['contributors'] = [_contributor for _contributor in _contributors if _contributor is not None]

            # Delete None
            _projects_dict['projects'] = [_prj for _prj in _projects if _prj is not None]
        except Exception as err:
            print(f'Exception {err}')
            # sys.exit(f'Exception {err}')
            raise err
        finally:
            if verbose:
                for project_id, contributors in self.created_project_contributors.items():
                    print(f'Created contributors for project \'{project_id}\'. [{len(contributors)}]')
                    for contributor in contributors:
                        users = contributor.embeds.users.data.attributes
                        attrs = contributor.attributes
                        print(f'\'{contributor.id}\' - \'{users.full_name}\' [{contributor.type}][{attrs.permission}][{attrs.index}]')

            print(f'USE the output result file: {self.output_result_file}')
            write_json_file(self.output_result_file, _projects_dict)

            sys.exit()
