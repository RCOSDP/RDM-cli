import inspect  # noqa
import json
import logging
import os
import sys
from pprint import pprint  # noqa
from types import SimpleNamespace
from concurrent.futures import ThreadPoolExecutor
import re

from .. import constants as const, utils

__all__ = [
    '_get_template_schema_projects',
    '_fake_project_content_data',
    '_prepare_project_data',
    '_load_project',
    '_fork_project',
    '_create_project',
    '_link_project_to_project',
    '_add_project_pointers',
    '_add_project_components',
    '_projects_add_component',
    '_create_or_load_project',
    'projects_create',
    'projects_get_list',
    'projects_get'
]
here = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))

logger = logging.getLogger(__name__)


def _get_template_schema_projects(self):
    return os.path.abspath(os.path.join(os.path.dirname(here), const.TEMPLATE_SCHEMA_PROJECTS))


def _fake_project_content_data(self, pk, verbose=True):
    """Fake a response data for project.
    Use this method when you don't want to send a request to retrieve a project

    :param pk: string - Project GUID
    :param verbose: boolean
    :return: string of object
    """
    # logger.debug('----{}:{}::{} from {}:{}::{}'.format(*utils.inspect_info(inspect.currentframe(), inspect.stack())))

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
        logger.debug(f'Prepared project data: {_content}')

    return _content


def _prepare_project_data(self, node_object, verbose=True):
    """Make a request body for the API Create new Node

    :param node_object: object of node
    :param verbose: boolean
    :return: object of request body
    """
    # logger.debug('----{}:{}::{} from {}:{}::{}'.format(*utils.inspect_info(inspect.currentframe(), inspect.stack())))

    _project = node_object

    # initial
    _category = _project.get('category')
    _title = _project.get('title')
    _attributes = {
        'category': _category,
        'title': _title,
    }
    _relationships = {}

    # update template_from
    _template_from = _project.get('template_from')
    if _template_from:
        _attributes['template_from'] = _template_from
        logger.warning('By default, the project from template will be made private.')
        _project['public'] = False

    # update description
    _description = _project.get('description', '')
    _attributes['description'] = _description

    # update public
    _public = _project.get('public', False)
    _attributes['public'] = _public

    # update tags
    _tags = _project.get('tags', [])
    _attributes['tags'] = _tags

    # update node_license
    _license = _project.get('node_license')
    if _license:
        _license_id = self._find_license_id_from_name(_license.get('license_name'))
        if _license_id is None:
            return None  # to ignore creating node

        # required 'id'
        _relationships['license'] = {
            'data': {
                'type': 'licenses',
                'id': _license_id
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
        logger.debug(f'Prepared project data: {_data}')

    return _data


def _load_project(self, pk, is_fake=True, ignore_error=True, verbose=True):
    """Retrieve project by its GUID

    :param pk: string - Project GUID
    :param is_fake: bool - fake a project's content data; don't make request
    :param ignore_error: boolean
    :param verbose: boolean
    :return: project object, and project dictionary
    """
    # logger.debug('----{}:{}::{} from {}:{}::{}'.format(*utils.inspect_info(inspect.currentframe(), inspect.stack())))

    _content = None
    _faked_or_loaded = f'[loaded]'

    if is_fake:
        _faked_or_loaded = '[faked]'
        _content = self._fake_project_content_data(pk, verbose=verbose)

    logger.info(f'Retrieve project nodes/{pk}/ {_faked_or_loaded}')
    if not is_fake:
        _response, _error_message = self._request('GET', 'nodes/{node_id}/'.format(node_id=pk), params={}, data={}, )
        if _error_message:
            logger.warning(_error_message)
            if not ignore_error:
                sys.exit(_error_message)
            return None, None
        _content = _response.content

    # pprint(_response.json())
    # Parse JSON into an object with attributes corresponding to dict keys.
    response = json.loads(_content, object_hook=lambda d: SimpleNamespace(**d))

    project = response.data

    self.created_projects.append(project)

    logger.info(f'Loaded project nodes/{project.id}/')
    if verbose:
        logger.debug(f'\'{project.id}\' - \'{project.attributes.title}\' [{project.type}][{project.attributes.category}]')

    return project, json.loads(_content)['data']


def _fork_project(self, node_object, ignore_error=True, verbose=True):
    """Fork a new project by an original project's GUID, title and category attributes

    :param node_object: object includes project's GUID and new project's attributes
    :param ignore_error: boolean
    :param verbose: boolean
    :return: project object, and project dictionary
    """
    # logger.debug('----{}:{}::{} from {}:{}::{}'.format(*utils.inspect_info(inspect.currentframe(), inspect.stack())))

    _data = self._prepare_project_data(node_object, verbose=verbose)
    pk = node_object['fork_id']

    logger.info(f'Fork a project from nodes/{pk}/')
    logger.warning('Ignore the following attributes: \'category\', \'description\', \'node_license\', \'public\', \'tags\'')
    _response, _error_message = self._request('POST', 'nodes/{node_id}/forks/'.format(node_id=pk),
                                              params={}, data=_data, )
    if _error_message:
        logger.warning(_error_message)
        if not ignore_error:
            sys.exit(_error_message)
        return None, None
    _content = _response.content

    # pprint(_response.json())
    # Parse JSON into an object with attributes corresponding to dict keys.
    response = json.loads(_content, object_hook=lambda d: SimpleNamespace(**d))

    project = response.data

    self.created_projects.append(project)

    logger.info(f'Forked project nodes/{project.id}/')
    if verbose:
        logger.debug(f'\'{project.id}\' - \'{project.attributes.title}\' [{project.type}][{project.attributes.category}]')

    return project, json.loads(_content)['data']


def _create_project(self, node_object, ignore_error=True, verbose=True):
    """Create new project by title and category attributes

    :param node_object: object includes new project's attributes
    :param ignore_error: boolean
    :param verbose: boolean
    :return: project object, and project dictionary
    """
    # logger.debug('----{}:{}::{} from {}:{}::{}'.format(*utils.inspect_info(inspect.currentframe(), inspect.stack())))

    _data = self._prepare_project_data(node_object, verbose=verbose)
    # ignore if licence not found
    if _data is None:
        return None, None

    logger.info('Create new project')
    _response, _error_message = self._request('POST', 'nodes/', params={}, data=_data, )
    if _error_message:
        logger.warning(_error_message)
        if 'licence' in _error_message:
            logger.warning('Project can be created. Please check manually.')
        if not ignore_error:
            sys.exit(_error_message)
        return None, None
    _content = _response.content

    # pprint(_response.json())
    # Parse JSON into an object with attributes corresponding to dict keys.
    response = json.loads(_content, object_hook=lambda d: SimpleNamespace(**d))

    project = response.data

    self.created_projects.append(project)

    logger.info(f'Created project \'{project.id}\'')
    if verbose:
        logger.debug(f'\'{project.id}\' - \'{project.attributes.title}\' [{project.type}][{project.attributes.category}]')

    return project, json.loads(_content)['data']


def _link_project_to_project(self, node_id, pointer_id, ignore_error=True, verbose=True):
    """Add a link to another project into this project by project's GUID.\n

    :param node_id: string - Project GUID
    :param pointer_id:  string - Project GUID, the other project
    :param ignore_error: boolean
    :param verbose: boolean
    :return: component object, and component dictionary
    """
    # logger.debug('----{}:{}::{} from {}:{}::{}'.format(*utils.inspect_info(inspect.currentframe(), inspect.stack())))

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

    logger.info(f'Create a link to nodes/{node_id}/')
    _url = 'nodes/{node_id}/node_links/'.format(node_id=node_id)
    _response, _error_message = self._request('POST', _url, params={}, data=_data, )
    if _error_message:
        logger.warning(_error_message)
        if not ignore_error:
            sys.exit(_error_message)
        return None, None
    _content = _response.content

    # pprint(_response.json())
    # Parse JSON into an object with attributes corresponding to dict keys.
    response = json.loads(_content, object_hook=lambda d: SimpleNamespace(**d))

    project_link = response.data
    project = None
    target_node = project_link.embeds.target_node
    if not hasattr(target_node, 'errors'):
        project = project_link.embeds.target_node.data

    if project:
        logger.info(f'Created Node Links \'{project_link.id}\'')
        if verbose:
            logger.debug(f'\'{project_link.id}\' - [{project_link.type}]')
            logger.debug(f'\'{project.id}\' - \'{project.attributes.title}\' [{project.type}][{project.attributes.category}]')
    else:
        errors = target_node.errors
        logger.warning(f'When link to {pointer_id}: {errors[0].detail}')

    return project, json.loads(_content)['data']


def _add_project_pointers(self, project_links, project, verbose=True):
    """Link a project to this project from list of project_links in template file

    :param project_links: list of existing project GUID
    :param project: object of project
    :return: None
    """
    for _node_id_idx, _node_id in enumerate(project_links):
        logger.info(f'JSONPOINTER ./project_links/{_node_id_idx}/')
        project_link, _ = self._link_project_to_project(project.id, _node_id, ignore_error=True, verbose=verbose)

        if project_link is None:
            # has error, update output object
            project_links[_node_id_idx] = None
            continue

        # update output object
        # can overwrite object by dictionary _project_links[_node_id_idx] = _
        project_links[_node_id_idx] = project_link.id


def _add_project_components(self, children, project, verbose=True):
    """Add component to project from list of children in template file

    :param children: object of component from template file
    :param project: object of project
    :return: None
    """
    for _component_idx, _component_dict in enumerate(children):
        _component_id = _component_dict.get('id')

        if _component_id:
            logger.info(f'JSONPOINTER ./children/{_component_idx}/ ignored')

            # update output object
            children[_component_idx] = None
            continue

        logger.info(f'JSONPOINTER ./children/{_component_idx}/')
        component, _ = self._projects_add_component(project.id, _component_dict, ignore_error=True, verbose=verbose)

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
    # logger.debug('----{}:{}::{} from {}:{}::{}'.format(*utils.inspect_info(inspect.currentframe(), inspect.stack())))

    _children = node_object.get('children', [])
    _project_links = node_object.get('project_links', [])

    _data = self._prepare_project_data(node_object, verbose=verbose)
    # ignore if licence not found
    if _data is None:
        return None, None

    logger.info(f'Create new component to nodes/{parent_id}/')
    _url = 'nodes/{node_id}/children/'.format(node_id=parent_id)
    _response, _error_message = self._request('POST', _url, params={}, data=_data, )
    if _error_message:
        logger.warning(_error_message)
        if 'licence' in _error_message:
            logger.warning('Project can be created. Please check manually.')
        if not ignore_error:
            sys.exit(_error_message)
        return None, None
    _content = _response.content

    # pprint(_response.json())
    # Parse JSON into an object with attributes corresponding to dict keys.
    response = json.loads(_content, object_hook=lambda d: SimpleNamespace(**d))

    project = response.data

    self.created_projects.append(project)

    logger.info(f'Created component \'{project.id}\'')
    if verbose:
        logger.debug(f'\'{project.id}\' - \'{project.attributes.title}\' [{project.type}][{project.attributes.category}]')

    # link a project to this node (parent_node_id = project.id)
    self._add_project_pointers(_project_links, project, verbose=verbose)

    # Delete None from project_links
    if _project_links:
        node_object['project_links'] = [_pointer for _pointer in _project_links if _pointer is not None]

    # add Components to this node (parent_node_id = project.id)
    self._add_project_components(_children, project, verbose=verbose)

    # Delete None from children
    if _children:
        node_object['children'] = [_child for _child in _children if _child is not None]

    return project, json.loads(_content)['data']


def _create_or_load_project(self, projects, project_idx, verbose=True):
    """Create new project or fork project or load project

    :param projects: list of project from template
    :param project_idx: integer of project index base on it order in project list
    :return: project object or None
    """
    _project_dict = projects[project_idx]
    _id = _project_dict.get('id')
    _fork_id = _project_dict.get('fork_id')

    if _id:
        logger.info(f'JSONPOINTER /projects/{project_idx}/id == {_id}')
        project, _ = self._load_project(_id, is_fake=const.IS_FAKE_LOAD_PROJECT, ignore_error=True, verbose=verbose)

        if project is None:
            # has error, update output object
            projects[project_idx] = None
            return None

        # update output object
        # can overwrite object by dictionary _projects[_project_idx].update(_)
        _project_dict['id'] = project.id
        _project_dict['type'] = project.type
    elif _fork_id:
        logger.info(f'JSONPOINTER /projects/{project_idx}/fork_id == {_fork_id}')
        project, _ = self._fork_project(_project_dict, ignore_error=True, verbose=verbose)

        if project is None:
            # has error, update output object
            projects[project_idx] = None
            return None

        # update output object
        # can overwrite object by dictionary _projects[_project_idx].update(_)
        _project_dict['id'] = project.id
        _project_dict['type'] = project.type
    else:
        logger.info(f'JSONPOINTER /projects/{project_idx}/')
        project, _ = self._create_project(_project_dict, ignore_error=True, verbose=verbose)

        if project is None:
            # has error, update output object
            projects[project_idx] = None
            return None

        # update output object
        # can overwrite object by dictionary _projects[_project_idx].update(_)
        _project_dict['id'] = project.id
        _project_dict['type'] = project.type

    return project


def projects_create(self):
    """Create Projects/Components following the structure and info which defined in a template JSON file.\n
    (1) For each project, you can create new with/without template form, fork from existing project.\n
    (2) You also can create new components and link other projects to a project/component.
    It can combine (1) and (2) into one: create/fork project and add components and link projects.\n
    Or only (2) by pass an existing project GUID as id in an object includes 'children' and 'project_links'.

    :param verbose: boolean
    :return: None
    """
    # logger.debug('----{}:{}::{} from {}:{}::{}'.format(*utils.inspect_info(inspect.currentframe(), inspect.stack())))
    verbose = self.verbose

    logger.info('Check config and authenticate by token')
    self._check_config(verbose=verbose)

    if not os.path.exists(self.template_schema_projects):
        sys.exit(f'Missing the template schema {self.template_schema_projects}')

    if not os.path.exists(self.template):
        sys.exit('Missing the template file')

    logger.info(f'Use the template of projects: {self.template}')
    _projects_dict = utils.read_json_file(self.template)

    try:
        # check json schema
        logger.info(f'Validate by the template of projects: {self.template_schema_projects}')
        utils.check_json_schema(self.template_schema_projects, _projects_dict)

        logger.info('Loop following the template of projects')
        _projects = _projects_dict.get('projects', [])
        for _project_idx, _project_dict in enumerate(_projects):
            _children = _project_dict.get('children', [])
            _project_links = _project_dict.get('project_links', [])

            # create new or fork project or load project
            project = self._create_or_load_project(_projects, _project_idx, verbose=verbose)
            if project is None:
                logger.warning(f'Project is not found')

                # update output object and ignore it
                _projects[_project_idx] = None
                continue

            # link a project to this node (parent_node_id = project.id)
            self._add_project_pointers(_project_links, project, verbose=verbose)

            # Delete None from project_links
            if _project_links:
                _project_dict['project_links'] = [_pointer for _pointer in _project_links if _pointer is not None]

            # add Components to this node (parent_node_id = project.id)
            self._add_project_components(_children, project, verbose=verbose)

            # Delete None from children
            if _children:
                _project_dict['children'] = [_child for _child in _children if _child is not None]

        # Delete None from projects
        _projects_dict['projects'] = [_prj for _prj in _projects if _prj is not None]

        _length = len(self.created_projects)
        if _length:
            # prepare output file
            logger.info(f'Use the output result file: {self.output_result_file}')
            self._prepare_output_file()
            # write output file
            utils.write_json_file(self.output_result_file, _projects_dict)
        else:
            logger.warning('The \'projects\' object is empty')

        sys.exit(0)
    except Exception as err:
        # logger.error(err)
        sys.exit(err)
    finally:
        _length = len(self.created_projects)
        if verbose and _length:
            logger.debug(f'Created projects. [{len(self.created_projects)}]')
            for _project in self.created_projects:
                logger.debug(
                    f'\'{_project.id}\' - \'{_project.attributes.title}\' [{_project.type}][{_project.attributes.category}]')

def list_cli_response_handler(response):
    response = json.loads(response.content, object_hook=lambda d: SimpleNamespace(**d))
    projects = []
    projects_list = response.data

    # Data aggregation
    for prj in projects_list:
        projects.append({
            'id': prj.id,
            'title': prj.attributes.title
        })

    return projects

# Get project of user
def call_api_user_nodes(self, page=1, params={}):
    _response, _error_message = self._request('GET', f'users/{self.user.id}/nodes?page={page}',
                                              params=params, data={}, )

    if _error_message:
        sys.exit(_error_message)

    return _response


def projects_get_list(self):
    # validate file and folder
    if self.output_result_file and self.output_result_file.endswith('.json') is False:
        sys.exit('The output file type is not valid')

    logger.info('Check validate done')
        # load config
    verbose = self.verbose
    logger.info('Check config and authenticate by token')
    self._check_config(verbose=verbose)

    # Call api get project list
    logger.info('Get project list...')
    _response = call_api_user_nodes(self)
    response = json.loads(_response.content, object_hook=lambda d: SimpleNamespace(**d))

    # Add first data to projects
    projects = []
    projects.extend(list_cli_response_handler(_response))

    # handle data if total data is more than first response
    total_data = response.links.meta.total
    data_per_page = response.links.meta.per_page
    page_count = total_data / data_per_page
    current_page = 1
    while(current_page < page_count):
        current_page += 1
        project = list_cli_response_handler(call_api_user_nodes(self, current_page))
        projects.extend(project)

    logger.info('Get project list successfully.')

    # Return value
    result = {'projects': projects}
    if self.output_result_file:
        self._prepare_output_file()
        # write output JSON file
        utils.write_json_file(self.output_result_file, result)
        logger.info('Write file successfully.')

    if self.display_console or not self.output_result_file:
        # write the result in JSON format to standard output (stdout)
        log_result = f'\n{json.dumps(result, indent=4)}'
        print(log_result)
        logger.info('Display console successfully.')
        
def projects_get(self):
    """PROJECT GET CLI: get project and details base on input id of user
    (or get all project if not input provided)
    """
    # load config
    verbose = self.verbose
    logger.info('Check config and authenticate by token')
    self._check_config(verbose=verbose)
    # init global state
    self.nodes_tree = {}
    self.linked_nodes_tree = {}
    self.contributors_list = []

    list_node_ids = []

    # validate argument
    if (self.output_projects_file and
            self.output_projects_file.endswith('.json') is False or
            self.output_contributors_file and
            self.output_contributors_file.endswith('.json') is False):
        sys.exit('The output file type is not valid')
    if (self.project_id):
        # input may be has unexpected comma or space,
        # below code will flatten them and return final id
        flatten_ids = []
        # Check if exist any comma in id input will be skip to ''
        for input_id in self.project_id:
            if ',' not in input_id:
                flatten_ids.append(input_id)
            else:
                flatten_ids.append('')
        # use set to remove duplicate id
        list_node_ids = list(set(flatten_ids))

    # Get all licenses
    self._licenses(False)

    len_list_node_ids = len(list_node_ids)

    # user use --project_ids and --project_ids <= PAGE_SIZE_SERVER
    if len_list_node_ids > 0 and len_list_node_ids <= const.PAGE_SIZE_SERVER:
        # input user maybe has comma so need to split to get correct length
        id_str = ','.join(list_node_ids)

        # Gotten node ids
        self.gotten_node_ids = []
        params = {
            'page[size]': const.PAGE_SIZE_SERVER,
            'filter[id]': id_str
        }
        _res = call_api_user_nodes(self, 1, params)
        response = json.loads(_res.content,
                              object_hook=lambda d: SimpleNamespace(**d))

        nodes_list = response.data
        # In DD if 'any' node_id is not valid
        # will show only 1 message "Project not found"
        if len(nodes_list) < len_list_node_ids:
            logger.error("Project not found")

        # Loop get details of node
        for node in nodes_list:
            converted_node = get_complete_node_details_recursive(self, node)
            if converted_node is not None:
                self.nodes_tree[converted_node.id] = converted_node

    # user do not use --project_ids or
    # --project_ids is larger than PAGE_SIZE_SERVER
    else:
        # Variable used to store the IDs of nodes
        # that either themselves or
        # their children are included in --project_ids
        relevant_nodes = []

        # Get all user nodes
        list_nodes = self.get_all_data_from_api(f'users/{self.user.id}/nodes',
                                                {'page[size]': 100})
        self.nodes_tree = {node.id: node for node in list_nodes}

        # Get all urls of linked nodes and contributors of each node
        contributors_api_urls = []
        linked_node_api_urls = []
        for node_id in self.nodes_tree.keys():
            linked_node_api_urls.append(f'nodes/{node_id}/linked_nodes')
            contributors_api_urls.append(f'nodes/{node_id}/contributors')

        linked_nodes = []
        # create parallel call api get all of all nodes
        with ThreadPoolExecutor(
             max_workers=const.MAX_THREADS_CALL_API
             ) as executor:
            linked_nodes.extend(
                list(executor.map(lambda url: get_all_linked_node(self, url),
                     linked_node_api_urls)))
        for n_ln in linked_nodes:
            for key, value in n_ln.items():
                self.linked_nodes_tree[key] = value

        node_contributors = []
        # create parallel call api get all of all nodes
        with ThreadPoolExecutor(
             max_workers=const.MAX_THREADS_CALL_API) as executor:
            node_contributors.extend(
                list(executor.map(lambda url: get_all_contributor(self, url),
                     contributors_api_urls)))
        self.contributors_list = node_contributors

        """Retrieve project details,
        convert them to a template-based data format,
        and establish parent-child relationships between projects."""
        tree_node_ids = self.nodes_tree.keys()
        for node_id in tree_node_ids:
            # get details of node
            current_node = self.nodes_tree[node_id]
            # current_node include attribute 'attributes'
            # => it has not converted yet => need to convert
            if hasattr(current_node, 'attributes'):
                current_node = get_details_node_with_template_get_cli(
                               self, current_node, True)
            self.nodes_tree[node_id] = current_node

            # check if current node is satisfy the input node id of user
            if node_id in list_node_ids:
                relevant_nodes.append(current_node)

            # Handle when node has parent_id
            if hasattr(current_node, 'parent_id'):
                # parent info
                parent_id = current_node.parent_id
                parent_content = self.nodes_tree[parent_id]

                # If the content of parent type 'list'
                # => The parent has been moved to its parent yet
                if isinstance(parent_content, list):
                    # Store the IDs of ancestors from the highest-level parent
                    # to the current project node
                    # pass current highest parent
                    ancestor_ids = [id for id in parent_content]

                    # loop until the end of the highest tree parent found,
                    # cause the upper parent can be move to higher parent
                    while isinstance(self.nodes_tree[ancestor_ids[0]], list):
                        high_parent = self.nodes_tree[ancestor_ids[0]]
                        ancestor_ids = high_parent + ancestor_ids
                    ancestor_ids.append(parent_id)

                    # Variable represent the current_node's parent children
                    represent_relative_children = self.nodes_tree[ancestor_ids[0]].children
                    # children is currently
                    # access to children of ancestor_ids[0] above
                    # so use count = 1
                    count = 1
                    while count < len(ancestor_ids):
                        # Get list id base on order of children
                        # to get info details of ancestor_ids[count]
                        ids = [child.id for child in
                               represent_relative_children]
                        lower_parent = represent_relative_children[
                                         ids.index(ancestor_ids[count])]
                        represent_relative_children = lower_parent.children
                        count += 1
                    # remove parent_id flag before push to parent
                    delattr(current_node, 'parent_id')
                    # loop to access to nearly parent and add current node
                    # represent_relative_children is represent of
                    #   access children step by step from root node
                    # so the root node will update correctly
                    represent_relative_children.append(current_node)
                    self.nodes_tree[current_node.id] = ancestor_ids
                else:
                    # if node include attribute 'attributes'
                    # => it has not converted yet => need to convert
                    if hasattr(self.nodes_tree[parent_id], 'attributes'):
                        self.nodes_tree[parent_id] = get_details_node_with_template_get_cli(
                            self, self.nodes_tree[parent_id], True)
                    # remove parent_id flag before push to parent
                    delattr(current_node, 'parent_id')
                    self.nodes_tree[parent_id].children.append(current_node)
                    self.nodes_tree[node_id] = [parent_id]
            else:
                # update node with node details
                self.nodes_tree[node_id] = current_node

        if len(relevant_nodes) < len_list_node_ids:
            logger.error("Project not found")

        # refilter if user input id more than 100 (id saved in relevant_node)
        if len_list_node_ids > const.PAGE_SIZE_SERVER:
            # use _clone_relevant_nodes cause below logic will multate data in relevant_nodes
            _clone_relevant_nodes = [node for node in relevant_nodes]
            for node in _clone_relevant_nodes:
                node_content = self.nodes_tree[node.id]
                # check above level parent is has any node in list project id of user input
                # if true => remove current node
                while isinstance(node_content, list) and len(node_content) > 0:
                    if bool(set(node_content) & set(list_node_ids)):
                        relevant_nodes.pop(relevant_nodes.index(node))
                        node_content = None
                    else:
                        # continue go to above parent
                        highest_parent_content = self.nodes_tree[node_content[0]]
                        node_content = highest_parent_content
            result_nodes = {}
            # re-update nodes_tree to template output
            for node in relevant_nodes:
                result_nodes[node.id] = node
            self.nodes_tree = result_nodes

    # write project
    if self.output_projects_file:
        self._prepare_output_file(self.output_projects_file)
        # Filter the tree nodes to retrieve all values
        # and exclude elements of type list
        # (type list is the nodes that have been moved to the parent node)
        nodes = [convert_namespace_to_dict(obj)
                 for obj in list(self.nodes_tree.values())
                 if not isinstance(obj, list)]
        rs = {'projects': nodes}
        utils.write_json_file(self.output_projects_file, rs)
    # # write contributor
    if self.output_contributors_file:
        self._prepare_output_file(self.output_contributors_file)
        rs = {'projects': self.contributors_list}
        utils.write_json_file(self.output_contributors_file, rs)

    logger.info("Get the project and contributor information completed.")


def get_details_node_with_template_get_cli(self, node, keep_parent=False):
    """Add linked node, project_links (if existed) and license to received node
    :param node: original node get from api
    :param keep_parent: the flag to check parent of current node,
        if exit parent in relationships will add new attr "parent_id"
    :return: Node details
    """
    attributes = node.attributes
    result = {
        'id': node.id,
        'category': attributes.category,
        'title': attributes.title,
        'description': attributes.description,
        'public':  attributes.public,
        'tags':  attributes.tags,
        'children': [],
        'project_links': self.linked_nodes_tree.get(node.id, [])
    }
    license = attributes.node_license
    relationships = node.relationships
    if hasattr(relationships, 'forked_from') and relationships.forked_from.data.id is not None:
        result['fork_id'] = relationships.forked_from.data.id
    # map license to node
    if license and hasattr(relationships, 'license'):
        license_id = relationships.license.data.id
        for lc in self.licenses:
            if lc.id == license_id:
                license.license_name = lc.attributes.name
        if hasattr(license, 'license_name'):
            result['node_license'] = convert_namespace_to_dict(license)
    # mapping template_from
    template_from = ''
    if hasattr(relationships, 'template_node'):
        result['template_from'] = relationships.template_node.data.id

    if keep_parent and hasattr(relationships, 'parent'):
        result['parent_id'] = relationships.parent.data.id

    return SimpleNamespace(**result)


def get_all_linked_node(self, url):
    """Get all linked_node with url
    :param url: url to get linked_node (format: 'nodes/{node_id}/linked_nodes')
    :return: dict with key is the node_id, value is list of linked_node id
    """
    node_id = url.split("/")[1]
    linked_nodes = [linked_node.id for linked_node in self.get_all_data_from_api(url)]
    return {node_id: linked_nodes}


def get_all_contributor(self, url):
    """Get all contributors with url
    :param url: url to get contributors (format: 'nodes/{node_id}/contributors')
    :return: dict with key is the node_id, value is list of contributors
    """
    node_id = url.split("/")[1]
    api_contributors = self.get_all_data_from_api(url)
    # convert_namespace_to_dict to convert the contributor to dict
    # convert_contributor_with_template_get_cli
    #   to convert contributor to template of PROJECT GET
    contributors = []
    for contributor in api_contributors:
        contributors.append(convert_namespace_to_dict(
                            convert_contributor_with_template_get_cli(
                                contributor
                            )))
    return {'id': node_id, 'contributors': contributors}


def get_complete_node_details_recursive(self, node, traverse_parent=False):
    """Retrieves node details and retrieve details of its children recursively,
    until there are no more children.
    Use only for case user input project_id less than PAGE_SIZE_SERVER
    :param node: node need to get additional attribute
    :param traverse_parent: flag to keep parent id of node when convert node
        (use for mapping parent and children)
    :return: new Node
    """

    # None => current node_id has been gotten before
    if node.id in list(self.gotten_node_ids):
        return None
    # convert_response_node_get_cli
    _return_node = get_details_node_with_template_get_cli(self, node, traverse_parent)

    # get link
    url_node_link = f'nodes/{node.id}/linked_nodes'
    node_links = self.get_all_data_from_api(url_node_link)
    node_links_id = [obj.id for obj in node_links]
    _return_node.project_links = node_links_id

    # get contributor
    url_node_contributor = f'nodes/{node.id}/contributors'
    dict_contributors = get_all_contributor(self, url_node_contributor)

    # Init key value of node.id in tree if it has not already existed
    self.contributors_list.append(dict_contributors)

    if not traverse_parent:
        # loop with child
        url_get_all_child = node.relationships.children.links.related.href
        response_children = self.parse_api_response('GET', url_get_all_child)
        list_converted_children = []
        for child in response_children.data:
            converted_child_node = get_complete_node_details_recursive(self, child)
            if converted_child_node is not None:
                list_converted_children.append(converted_child_node)
                self.gotten_node_ids.append(converted_child_node.id)
            else:
                # move gotten node from self.nodes_tree to child of current node
                list_converted_children.append(self.nodes_tree[child.id])
                self.nodes_tree.pop(child.id)
        _return_node.children = list_converted_children
    self.gotten_node_ids.append(node.id)

    return _return_node


def convert_contributor_with_template_get_cli(original):
    """Convert contributor with template of PROJECT GET
    :param original: original contributor
    :return: new converted contributor base on template
    """
    attributes = original.attributes
    permission = attributes.permission if hasattr(attributes, 'permission') else ''

    result = {
        "id": original.relationships.users.data.id,
        "bibliographic": attributes.bibliographic,
        "permission": permission
    }

    return SimpleNamespace(**result)


def convert_namespace_to_dict(namespace):
    """Convert namespace and namespace inside to dict
    :param namespace: namespace want to convert
    :return: dict converted from namespace
    """
    if isinstance(namespace, SimpleNamespace):
        return {
                key: convert_namespace_to_dict(value) for key,
                value in namespace.__dict__.items()}
    elif isinstance(namespace, list):
        return [convert_namespace_to_dict(item) for item in namespace]
    else:
        return namespace
