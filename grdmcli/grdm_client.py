import configparser
import inspect  # noqa
import json
import os
import sys
from argparse import Namespace
from datetime import datetime  # noqa
from pathlib import Path
from pprint import pprint  # noqa
from types import SimpleNamespace

import requests
import validators
from validators import ValidationFailure

from . import constants as const, status, utils

here = os.path.abspath(os.path.dirname(__file__))
MSG_E001 = 'Missing currently logged-in user'

# [For development]
DEBUG = True
IS_CLEAR = True
IGNORE_PROJECTS = ['z6dne', 'ega24', 'm7ah9', '4hexc']


class GRDMClient(Namespace):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self._meta = {}
        self.template = './template_file.json'
        self.output_result_file = './output_result_file.json'

        self.user = None
        self.is_authenticated = False
        self.affiliated_institutions = []  # For development
        self.affiliated_users = []  # For development

        self.projects = []
        self.created_projects = []
        self.created_project_contributors = []

    @property
    def config_file(self):
        return Path(os.getcwd()) / const.CONFIG_FILENAME

    @property
    def has_required_attributes(self):
        return self.osf_token is not None and self.osf_api_url is not None

    @property
    def template_schema_projects(self):
        return os.path.abspath(os.path.join(os.path.dirname(here), const.TEMPLATE_SCHEMA_PROJECTS))

    @property
    def template_schema_contributors(self):
        return os.path.abspath(os.path.join(os.path.dirname(here), const.TEMPLATE_SCHEMA_CONTRIBUTORS))

    def _request(self, method, url, params=None, data=None, headers=None):
        """Make a request

        :param method: string
        :param url: string of URL; will be validated
        :param params: dictionary of query parameters needed to update
        :param data: dictionary of request body
        :param headers: dictionary of request headers
        :return: response data, and the first error message
        """
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
            # print(f'WARN Exception: {response.errors[0].detail}')
            return None, response.errors[0].detail

        return _response, None

    def _load_required_attributes_from_config_file(self):
        """Update osf_api_url and osf_token from configuration file

        :return: None
        """
        if not os.path.exists(self.config_file):
            print(f'Missing the config file {self.config_file}')
            return False

        print(f'Read config_file: {self.config_file}')
        config = configparser.ConfigParser()
        config.read(self.config_file)
        config_dict = dict(config.items(const.CONFIG_SECTION))
        # get osf_api_url
        if self.osf_api_url is None:
            self.osf_api_url = config_dict.get(const.OSF_API_URL_VAR_NAME.lower())
        # get osf_token
        if self.osf_token is None:
            self.osf_token = config_dict.get(const.OSF_TOKEN_VAR_NAME.lower())

    def _load_required_attributes_from_environment(self):
        """Update osf_api_url and osf_token from environment variables

        :return: None
        """
        if self.osf_api_url is None:
            self.osf_api_url = os.environ.get(const.OSF_API_URL_VAR_NAME)
        if self.osf_token is None:
            self.osf_token = os.environ.get(const.OSF_TOKEN_VAR_NAME)

    def _check_config(self, verbose=True):
        """The priority order\n
        - Command line arguments\n
        - Config file attributes\n
        - Environment variables\n

        :param verbose:
        :return: None
        """
        # print('----{}:{}::{} from {}:{}::{}'.format(*inspect_info(inspect.currentframe(), inspect.stack())))

        # ignore if user is authenticated
        if self.is_authenticated:
            return True

        if not self.has_required_attributes:
            print(f'Try get from config property')
            self._load_required_attributes_from_config_file()

        if not self.has_required_attributes:
            print(f'Try get from environment variable')
            self._load_required_attributes_from_environment()

        if not self.osf_api_url:
            sys.exit('Missing API URL')

        if isinstance(validators.url(self.osf_api_url, public=False), ValidationFailure):
            sys.exit('The API URL is invalid')

        if not self.osf_token:
            sys.exit('Missing Personal Access Token')

        if not self.is_authenticated:
            print('Check Personal Access Token')
            self._users_me(ignore_error=False, verbose=verbose)

    def _users_me(self, ignore_error=True, verbose=True):
        """Get the currently logged-in user

        :param ignore_error: boolean
        :param verbose: boolean
        :return: None
        """
        """  """
        # print('----{}:{}::{} from {}:{}::{}'.format(*inspect_info(inspect.currentframe(), inspect.stack())))

        print('GET the currently logged-in user')
        _response, _error_message = self._request('GET', 'users/me/', params={}, data={})
        if _error_message:
            print(f'WARN {_error_message}')
            if not ignore_error:
                sys.exit(_error_message)
            return False
        _content = _response.content

        # pprint(_response.json())
        # Parse JSON into an object with attributes corresponding to dict keys.
        response = json.loads(_content, object_hook=lambda d: SimpleNamespace(**d))

        self.is_authenticated = True
        self.user = response.data

        if verbose:
            print(f'You are logged in as:')
            print(f'\'{self.user.id}\' - {self.user.attributes.email} \'{self.user.attributes.full_name}\'')

    def _users_me_affiliated_institutions(self, ignore_error=True, verbose=True):
        """For development"""
        # print('----{}:{}::{} from {}:{}::{}'.format(*inspect_info(inspect.currentframe(), inspect.stack())))

        if not self.user:
            sys.exit(MSG_E001)

        # users/{user.id}/institutions/
        params = {const.ORDERING_QUERY_PARAM: 'name'}
        _response, _error_message = self._request('GET', self.user.relationships.institutions.links.related.href, params=params)
        if _error_message:
            print(f'WARN {_error_message}')
            if not ignore_error:
                sys.exit(_error_message)
            return False
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
        # print('----{}:{}::{} from {}:{}::{}'.format(*inspect_info(inspect.currentframe(), inspect.stack())))

        if not self.user:
            sys.exit(MSG_E001)

        if not self.affiliated_institutions:
            sys.exit('Missing currently logged-in user\'s affiliated institutions')

        _users_numb = 0

        for inst in self.affiliated_institutions:
            # institutions/{inst.id}/users/
            params = {const.ORDERING_QUERY_PARAM: 'full_name'}
            _response, _error_message = self._request('GET', inst.relationships.users.links.related.href, params=params)
            if _error_message:
                print(f'WARN {_error_message}')
                if not ignore_error:
                    sys.exit(_error_message)
                return False
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
        # print('----{}:{}::{} from {}:{}::{}'.format(*inspect_info(inspect.currentframe(), inspect.stack())))

        if not self.user:
            sys.exit(MSG_E001)

        print(f'[For development]GET List of licenses')
        params = {const.ORDERING_QUERY_PARAM: 'name'}
        _response, _error_message = self._request('GET', 'licenses/', params=params, data={}, )
        if _error_message:
            print(f'WARN {_error_message}')
            if not ignore_error:
                sys.exit(_error_message)
            return False
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

    def _projects_delete_project(self, pk, ignore_error=True, verbose=True):
        """For development"""
        # print('----{}:{}::{} from {}:{}::{}'.format(*inspect_info(inspect.currentframe(), inspect.stack())))

        print(f'DELETE Remove project \'{pk}\'')
        _response, _error_message = self._request('DELETE', 'nodes/{node_id}/'.format(node_id=pk), params={}, data={}, )
        if _error_message:
            print(f'WARN {_error_message}')
            if not ignore_error:
                sys.exit(_error_message)
            return False

        if verbose:
            print(f'Deleted project: \'{pk}\'')

    def projects_list(self, ignore_error=True, verbose=True):
        """For development"""
        # print('----{}:{}::{} from {}:{}::{}'.format(*inspect_info(inspect.currentframe(), inspect.stack())))

        print(f'Check config and authenticate by token')
        self._check_config()

        # [For development]
        if DEBUG:
            self._users_me_affiliated_institutions(ignore_error=True, verbose=True)
            self._users_me_affiliated_users(ignore_error=True, verbose=True)
            self._licenses(ignore_error=True, verbose=True)

        print(f'[For development]GET List of projects')
        params = {const.ORDERING_QUERY_PARAM: 'title'}
        _response, _error_message = self._request('GET', 'nodes/', params=params, data={}, )
        if _error_message:
            print(f'WARN {_error_message}')
            if not ignore_error:
                sys.exit(_error_message)
            return None, None
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
                if IS_CLEAR and project.id not in IGNORE_PROJECTS:
                    self._projects_delete_project(project.id, ignore_error=True, verbose=False)

        sys.exit(0)

    def _projects_fake_project_content_data(self, pk, verbose=True):
        """Fake a response data for project.
        Use this method when you don't want to send a request to retrieve a project

        :param pk: string - Project GUID
        :param verbose: boolean
        :return: string of object
        """
        # print('----{}:{}::{} from {}:{}::{}'.format(*inspect_info(inspect.currentframe(), inspect.stack())))

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
        """Make a request body for the API Create new Node

        :param node_object: object of node
        :param verbose: boolean
        :return: object of request body
        """
        # print('----{}:{}::{} from {}:{}::{}'.format(*inspect_info(inspect.currentframe(), inspect.stack())))

        _project = node_object

        # For development
        _today_str = datetime.today().strftime('%Y-%m-%d %H:%M:%S')

        # initial
        _category = _project.get('category')
        _title = _project.get('title')
        _attributes = {
            'category': _category,
            # 'title': _title,
            'title': f'[{_today_str}] {_title}',  # For development
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
            # required 'id'
            _relationships['license'] = {
                'data': {
                    'type': 'licenses',
                    'id': _license.get('id')
                }
            }
            # required 'copyright_holders' and 'year'
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
            print(f'Prepared project data: {_data}')

        return _data

    def _projects_load_project(self, pk, is_fake=True, ignore_error=True, verbose=True):
        """Retrieve project by its GUID

        :param pk: string - Project GUID
        :param is_fake: bool - fake a project's content data; don't make request
        :param ignore_error: boolean
        :param verbose: boolean
        :return: project object, and project dictionary
        """
        # print('----{}:{}::{} from {}:{}::{}'.format(*inspect_info(inspect.currentframe(), inspect.stack())))

        _content = None
        _faked_or_loaded = f'[loaded nodes/{pk}/]'

        if is_fake:
            _faked_or_loaded = '[faked]'
            _content = self._projects_fake_project_content_data(pk, verbose=False)

        print(f'GET Retrieve project {_faked_or_loaded}')
        if not is_fake:
            _response, _error_message = self._request('GET', 'nodes/{node_id}/'.format(node_id=pk), params={}, data={}, )
            if _error_message:
                print(f'WARN {_error_message}')
                if not ignore_error:
                    sys.exit(_error_message)
                return None, None
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
        """Fork a new project by an original project's GUID, title and category attributes

        :param node_object: object includes project's GUID and new project's attributes
        :param ignore_error: boolean
        :param verbose: boolean
        :return: project object, and project dictionary
        """
        # print('----{}:{}::{} from {}:{}::{}'.format(*inspect_info(inspect.currentframe(), inspect.stack())))

        _data = self._projects_prepare_project_data(node_object, verbose=False)
        pk = node_object['fork_id']

        print(f'POST Fork a project from nodes/{pk}/')
        _response, _error_message = self._request('POST', 'nodes/{node_id}/forks/'.format(node_id=pk), params={}, data=_data, )
        if _error_message:
            print(f'WARN {_error_message}')
            if not ignore_error:
                sys.exit(_error_message)
            return None, None
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
        """Create new project by title and category attributes

        :param node_object: object includes new project's attributes
        :param ignore_error: boolean
        :param verbose: boolean
        :return: project object, and project dictionary
        """
        # print('----{}:{}::{} from {}:{}::{}'.format(*inspect_info(inspect.currentframe(), inspect.stack())))

        _data = self._projects_prepare_project_data(node_object, verbose=False)

        print(f'POST Create new project')
        _response, _error_message = self._request('POST', 'nodes/', params={}, data=_data, )
        if _error_message:
            print(f'WARN {_error_message}')
            if not ignore_error:
                sys.exit(_error_message)
            return None, None
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

    def _projects_link_project(self, node_id, pointer_id, ignore_error=True, verbose=True):
        """Add a link to another project into this project by project's GUID.\n

        :param node_id: string - Project GUID
        :param pointer_id:  string - Project GUID, the other project
        :param ignore_error: boolean
        :param verbose: boolean
        :return: component object, and component dictionary
        """
        # print('----{}:{}::{} from {}:{}::{}'.format(*inspect_info(inspect.currentframe(), inspect.stack())))

        # prepare request data
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

        print(f'POST Create a link to nodes/{node_id}/')
        _url = 'nodes/{node_id}/node_links/'.format(node_id=node_id)
        _response, _error_message = self._request('POST', _url, params={}, data=_data, )
        if _error_message:
            print(f'WARN {_error_message}')
            if not ignore_error:
                sys.exit(_error_message)
            return None, None
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

    def _add_project_pointers(self, project_links, project):
        """Link a project to this project from list of project_links in template file

        :param project_links: list of existing project GUID
        :param project: object of project
        :return: None
        """
        for _node_id_idx, _node_id in enumerate(project_links):
            print(f'JSONPOINTER ./project_links/{_node_id_idx}/')
            project_link, _ = self._projects_link_project(project.id, _node_id, ignore_error=True, verbose=True)

            if project_link is None:
                # has error, update output object
                project_links[_node_id_idx] = None
                continue

            # update output object
            # can overwrite object by dictionary _project_links[_node_id_idx] = _
            project_links[_node_id_idx] = project_link.id

    def _add_project_components(self, children, project):
        """Add component to project from list of children in template file

        :param children: object of component from template file
        :param project: object of project
        :return: None
        """
        for _component_idx, _component_dict in enumerate(children):
            _component_id = _component_dict.get('id')

            if _component_id:
                print(f'JSONPOINTER ./children/{_component_idx}/ ignored')

                # update output object
                children[_component_idx] = None
                continue

            print(f'JSONPOINTER ./children/{_component_idx}/')
            component, _ = self._projects_add_component(project.id, _component_dict, ignore_error=True, verbose=True)

            if component is None:
                # has error, update output object
                children[_component_idx] = None
                continue

            # update output object
            # can overwrite object by dictionary _children[_component_idx].update(_)
            children[_component_idx]['id'] = component.id
            children[_component_idx]['type'] = component.type

    def _projects_add_component(self, parent_id, node_object, ignore_error=True, verbose=True):
        """Add a component into project by project's GUID, component's attributes such as title and category.\n
        In scope of method, call component as 'project' and its child as 'component'.

        :param parent_id: string - Project GUID
        :param node_object: object includes new component's attributes
        :param ignore_error: boolean
        :param verbose: boolean
        :return: component object, and component dictionary
        """
        # print('----{}:{}::{} from {}:{}::{}'.format(*inspect_info(inspect.currentframe(), inspect.stack())))

        _children = node_object.get('children', [])
        _project_links = node_object.get('project_links', [])

        _data = self._projects_prepare_project_data(node_object, verbose=False)

        print(f'POST Create new component to nodes/{parent_id}/')
        _url = 'nodes/{node_id}/children/'.format(node_id=parent_id)
        _response, _error_message = self._request('POST', _url, params={}, data=_data, )
        if _error_message:
            print(f'WARN {_error_message}')
            if not ignore_error:
                sys.exit(_error_message)
            return None, None
        _content = _response.content

        # pprint(_response.json())
        # Parse JSON into an object with attributes corresponding to dict keys.
        response = json.loads(_content, object_hook=lambda d: SimpleNamespace(**d))

        project = response.data

        self.created_projects.append(project)

        if verbose:
            print(f'Create component:')
            print(f'\'{project.id}\' - \'{project.attributes.title}\' [{project.type}][{project.attributes.category}]')

        # link a project to this node (parent_node_id = project.id)
        self._add_project_pointers(_project_links, project)

        # Delete None from project_links
        if _project_links:
            node_object['project_links'] = [_pointer for _pointer in _project_links if _pointer is not None]

        # add Components to this node (parent_node_id = project.id)
        self._add_project_components(_children, project)

        # Delete None from children
        if _children:
            node_object['children'] = [_child for _child in _children if _child is not None]

        return project, json.loads(_content)['data']

    def _create_or_load_project(self, projects, project_idx):
        """Create new project or fork project or load project

        :param projects: list of project from template
        :param project_idx: integer of project index base on it order in project list
        :return: project object or None
        """
        _project_dict = projects[project_idx]
        _id = _project_dict.get('id')
        _fork_id = _project_dict.get('fork_id')

        if _id:
            print(f'JSONPOINTER /projects/{project_idx}/id == {_id}')
            project, _ = self._projects_load_project(_id, is_fake=True, ignore_error=True, verbose=True)

            if project is None:
                # has error, update output object
                projects[project_idx] = None
                return None

            # update output object
            # can overwrite object by dictionary _projects[_project_idx].update(_)
            _project_dict['id'] = project.id
            _project_dict['type'] = project.type
        elif _fork_id:
            print(f'JSONPOINTER /projects/{project_idx}/fork_id == {_fork_id}')
            project, _ = self._projects_fork_project(_project_dict, ignore_error=True, verbose=True)

            if project is None:
                # has error, update output object
                projects[project_idx] = None
                return None

            # update output object
            # can overwrite object by dictionary _projects[_project_idx].update(_)
            _project_dict['id'] = project.id
            _project_dict['type'] = project.type
        else:
            print(f'JSONPOINTER /projects/{project_idx}/')
            project, _ = self._projects_create_project(_project_dict, ignore_error=True, verbose=True)

            if project is None:
                # has error, update output object
                projects[project_idx] = None
                return None

            # update output object
            # can overwrite object by dictionary _projects[_project_idx].update(_)
            _project_dict['id'] = project.id
            _project_dict['type'] = project.type

        return project

    def projects_create(self, verbose=True):
        """Create Projects/Components following the structure and info which defined in a template JSON file.\n
        (1) For each project, you can create new with/without template form, fork from existing project.\n
        (2) You also can create new components and link other projects to a project/component.
        It can combine (1) and (2) into one: create/fork project and add components and link projects.\n
        Or only (2) by pass an existing project GUID as id in an object includes 'children' and 'project_links'.

        :param verbose: boolean
        :return: None
        """
        # print('----{}:{}::{} from {}:{}::{}'.format(*inspect_info(inspect.currentframe(), inspect.stack())))

        print(f'Check config and authenticate by token')
        self._check_config(verbose=False)

        if not os.path.exists(self.template_schema_projects):
            sys.exit(f'Missing the template schema {self.template_schema_projects}')

        if not os.path.exists(self.template):
            sys.exit('Missing the template file')

        print(f'USE the template of projects: {self.template}')
        _projects_dict = utils.read_json_file(self.template)

        try:
            # check json schema
            print(f'VALIDATE BY the template of projects: {self.template_schema_projects}')
            utils.check_json_schema(self.template_schema_projects, _projects_dict)

            print(f'LOOP Following the template of projects')
            _projects = _projects_dict.get('projects', [])
            for _project_idx, _project_dict in enumerate(_projects):
                _id = _project_dict.get('id')
                _fork_id = _project_dict.get('fork_id')
                _children = _project_dict.get('children', [])
                _project_links = _project_dict.get('project_links', [])

                # create new or fork project or load project
                project = self._create_or_load_project(_projects, _project_idx)
                if project is None:
                    continue

                # link a project to this node (parent_node_id = project.id)
                self._add_project_pointers(_project_links, project)

                # Delete None from project_links
                if _project_links:
                    _project_dict['project_links'] = [_pointer for _pointer in _project_links if _pointer is not None]

                # add Components to this node (parent_node_id = project.id)
                self._add_project_components(_children, project)

                # Delete None from children
                if _children:
                    _project_dict['children'] = [_child for _child in _children if _child is not None]

            # Delete None from projects
            _projects_dict['projects'] = [_prj for _prj in _projects if _prj is not None]
        except Exception as err:
            print(f'Exception {err}')
            raise err
        finally:
            if verbose:
                print(f'Created projects. [{len(self.created_projects)}]')
                for _project in self.created_projects:
                    print(f'\'{_project.id}\' - \'{_project.attributes.title}\' [{_project.type}][{_project.attributes.category}]')

            print(f'USE the output result file: {self.output_result_file}')
            utils.write_json_file(self.output_result_file, _projects_dict)

            sys.exit(0)

    def _projects_list_project_contributors(self, pk, ignore_error=True, verbose=True):
        """Get list of contributors of a project by project GUID

        :param pk: string - Project GUID
        :param ignore_error: boolean
        :param verbose: boolean
        :return: contributors object, and contributors list
        """
        # print('----{}:{}::{} from {}:{}::{}'.format(*inspect_info(inspect.currentframe(), inspect.stack())))

        if not self.user:
            sys.exit(MSG_E001)

        print(f'GET List of contributors')
        params = {const.ORDERING_QUERY_PARAM: 'name'}
        _url = 'nodes/{node_id}/contributors/'.format(node_id=pk)
        _response, _error_message = self._request('GET', _url, params=params, data={}, )
        if _error_message:
            print(f'WARN {_error_message}')
            if not ignore_error:
                sys.exit(_error_message)
            return [], []
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
        """Delete a contributor from a project

        :param pk: string - Project GUID
        :param user_id: string - User GUID of a contributor
        :param ignore_error: boolean
        :param verbose: boolean
        :return: None
        """
        # print('----{}:{}::{} from {}:{}::{}'.format(*inspect_info(inspect.currentframe(), inspect.stack())))

        print(f'DELETE Remove contributor \'{pk}-{user_id}\'')
        _url = 'nodes/{node_id}/contributors/{user_id}'.format(node_id=pk, user_id=user_id)
        _response, _error_message = self._request('DELETE', _url, params={}, data={}, )
        if _error_message:
            print(f'WARN {_error_message}')
            if not ignore_error:
                sys.exit(_error_message)

        if verbose:
            print(f'Deleted contributor: \'{pk}-{user_id}\'')

    def _projects_prepare_contributor_data(self, contributor_object, index, verbose=True):
        """Make a request body for the API Create new Contributor

        :param contributor_object: object includes user GUID and new contributor's attributes
        :param index: contributor's index attribute
        :param verbose: boolean
        :return: object of request body
        """
        # print('----{}:{}::{} from {}:{}::{}'.format(*inspect_info(inspect.currentframe(), inspect.stack())))

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
            print(f'Prepared contributor data: {_data}')

        return _data

    def _projects_add_contributor(self, pk, contributor_object, index, ignore_error=True, verbose=True):
        """

        :param pk: string - Project GUID
        :param contributor_object: object includes user GUID and new contributor's attributes
        :param index: contributor's index attribute
        :param ignore_error: boolean
        :param verbose: boolean
        :return: contributor object, and contributor dictionary
        """
        # print('----{}:{}::{} from {}:{}::{}'.format(*inspect_info(inspect.currentframe(), inspect.stack())))

        _data = self._projects_prepare_contributor_data(contributor_object, index, verbose=True)
        user_id = contributor_object['id']

        print(f'CREATE Add contributor \'{pk}-{user_id}\'')
        _url = 'nodes/{node_id}/contributors/'.format(node_id=pk)
        _response, _error_message = self._request('POST', _url, params={}, data=_data, )
        if _error_message:
            print(f'WARN {_error_message}')
            if not ignore_error:
                sys.exit(_error_message)
            return None, None
        _content = _response.content

        # pprint(_response.json())
        # Parse JSON into an object with attributes corresponding to dict keys.
        response = json.loads(_content, object_hook=lambda d: SimpleNamespace(**d))

        contributor = response.data

        self.created_project_contributors.append(contributor)

        if verbose:
            print(f'Created contributor: \'{pk}-{user_id}\'')
            users = contributor.embeds.users.data.attributes
            attrs = contributor.attributes
            print(f'\'{contributor.id}\' - \'{users.full_name}\' [{contributor.type}][{attrs.permission}][{attrs.index}]')

        return contributor, json.loads(_content)['data']

    def _overwrite_project_contributors(self, contributors, pk, contributor_user_ids, current_user_contributor):
        """Add all new contributors to this project

        :param pk: string - Project GUID
        :param contributors: list of new contributors
        :param contributor_user_ids: list of the user GUID which is project contributor
        :param current_user_contributor: object of contributor which is current user
        :return: None
        """
        _invalid_user_obj_number = 0
        for _user_idx, _user_dict in enumerate(contributors):
            _user_id = _user_dict['id']

            if _user_id == self.user.id:
                print(f'WARN This member is the currently logged-in user, so skip creating/updating')
                if current_user_contributor:
                    # update output object
                    # can overwrite object by _contributors[_user_idx].update(contributor_dict)
                    _obj = contributors[_user_idx]
                    _contributor_attr = current_user_contributor.attributes
                    _obj['id'] = current_user_contributor.id
                    _obj['type'] = current_user_contributor.type
                    _obj['index'] = _contributor_attr.index
                    _obj['bibliographic'] = _contributor_attr.bibliographic
                    _obj['permission'] = _contributor_attr.permission
                continue

            if _user_id in contributor_user_ids:
                print(f'WARN Duplicate member object in template file')
                # update output object
                contributors[_user_idx] = None
                _invalid_user_obj_number += 1
                continue

            print(f'JSONPOINTER ./contributors/{_user_idx}/')
            # Call API Create a contributor
            _index = _user_idx - _invalid_user_obj_number
            contributor, _ = self._projects_add_contributor(pk, _user_dict, _index, verbose=True)
            if contributor is None:
                # has error, update output object
                contributors[_user_idx] = None
                _invalid_user_obj_number += 1
                continue

            # update output object
            # can overwrite object by _contributors[_user_idx].update(_)
            _obj = contributors[_user_idx]
            _contributor_attr = contributor.attributes
            _obj['id'] = contributor.id
            _obj['type'] = contributor.type
            _obj['index'] = _contributor_attr.index
            _obj['bibliographic'] = _contributor_attr.bibliographic
            _obj['permission'] = _contributor_attr.permission

    def _clear_project_current_contributors(self, pk, contributor_user_ids, current_user_contributor):
        """Clear list of current contributors from this project, except for the currently logged-in user

        :param pk: string - Project GUID
        :param contributor_user_ids: list of the user GUID which is project contributor
        :param current_user_contributor: object of contributor which is current user
        :return: object of contributor which is current user
        """
        # Get all current contributors from this project
        old_contributors, _ = self._projects_list_project_contributors(pk, verbose=True)
        # Delete all current contributors from this project
        for contributor in old_contributors:
            # except for the currently logged-in user
            if contributor.embeds.users.data.id == self.user.id:
                self.created_project_contributors.append(contributor)
                current_user_contributor = contributor
                contributor_user_ids.append(self.user.id)
                continue
            # Delete current contributor
            self._projects_delete_project_contributor(pk, contributor.embeds.users.data.id, verbose=True)
        return current_user_contributor

    def contributors_create(self, verbose=True):
        """Overwrite the contributor list of a project following the structure and info which defined in a template JSON file.\n
        Delete contributors from the project; expect the current user as admin.\n
        Add contributors in order from template into the project.

        :param verbose: boolean
        :return: None
        """
        # print('----{}:{}::{} from {}:{}::{}'.format(*inspect_info(inspect.currentframe(), inspect.stack())))

        print(f'Check config and authenticate by token')
        # the current_user_id is self.user.id
        self._check_config(verbose=False)

        if not os.path.exists(self.template_schema_contributors):
            sys.exit(f'Missing the template schema {self.template_schema_contributors}')

        if not os.path.exists(self.template):
            sys.exit('Missing the template file')

        print(f'USE the template of contributors: {self.template}')
        _projects_dict = utils.read_json_file(self.template)

        try:
            # check json schema
            print(f'VALIDATE BY the template of projects: {self.template_schema_contributors}')
            utils.check_json_schema(self.template_schema_contributors, _projects_dict)

            print(f'LOOP Following the template of contributors')
            _projects = _projects_dict.get('projects', [])
            for idx, _project_dict in enumerate(_projects):
                _id = _project_dict.get('id')
                _contributors = _project_dict.get('contributors', [])

                if not _id:
                    print(f'JSONPOINTER /projects/{idx}/id == {_id}')

                    # update output object and ignore it
                    _projects[idx] = None
                    continue

                current_user_contributor = None
                current_project_contributor_user_ids = []

                print(f'JSONPOINTER /projects/{idx}/')
                print(f'REMOVE Current contributors')
                current_user_contributor = self._clear_project_current_contributors(_id, current_project_contributor_user_ids, current_user_contributor)

                print(f'OVERWRITE new contributors')
                self._overwrite_project_contributors(_contributors, _id, current_project_contributor_user_ids, current_user_contributor)

                # Delete None from contributors
                if _contributors:
                    _project_dict['contributors'] = [_contributor for _contributor in _contributors if _contributor is not None]

            # Delete None from projects
            _projects_dict['projects'] = [_prj for _prj in _projects if _prj is not None]
        except Exception as err:
            print(f'Exception {err}')
            raise err
        finally:
            if verbose:
                print(f'Created contributors for projects . [{len(self.created_project_contributors)}]')
                for contributor in self.created_project_contributors:
                    users = contributor.embeds.users.data.attributes
                    attrs = contributor.attributes
                    print(f'\'{contributor.id}\' - \'{users.full_name}\' [{contributor.type}][{attrs.permission}][{attrs.index}]')

            print(f'USE the output result file: {self.output_result_file}')
            utils.write_json_file(self.output_result_file, _projects_dict)

            sys.exit(0)
