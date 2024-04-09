import inspect  # noqa
import json
import logging
import os
import sys
from pprint import pprint  # noqa
from types import SimpleNamespace

from .. import constants as const, utils

from grdmcli.status import HTTP_403_FORBIDDEN, HTTP_404_NOT_FOUND

__all__ = [
    '_get_template_schema_projects',
    '_fake_project_content_data',
    '_prepare_project_data',
    '_load_project',
    '_fork_project',
    '_create_project',
    '_update_project',
    '_link_project_to_project',
    '_overwrite_node_link',
    '_update_project_component',
    '_overwrite_node_link_update_component',
    '_add_project_pointers',
    '_add_project_components',
    '_projects_add_component',
    '_create_or_update_project',
    '_remapping_node',
    '_convert_node_to_create_schema',
    'projects_create'
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

    # get node id
    _id = _project.get('id', None)

    # template_from is only use for create new
    if _id is None:
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
            if _id is None:
                return None  # to ignore creating node
            # 2.2 remove license attribute and continue create project
            _project.pop('node_license', None)
        else:
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

    data = {
        'type': 'nodes',
        'attributes': _attributes,
        'relationships': _relationships
    }

    if _id:
        data['id'] = _id

    _data = {
        'data': data
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
            # new feature of CREATE, UPDATE, FORK
            # will continue next node if current node has error
            # so will log error without exit
            logger.error(_error_message)
        return None, None
    _content = _response.content

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

    # Parse JSON into an object with attributes corresponding to dict keys.
    response = json.loads(_content, object_hook=lambda d: SimpleNamespace(**d))

    project = response.data

    self.created_projects.append(project)

    logger.info(f'Created project \'{project.id}\'')
    if verbose:
        logger.debug(f'\'{project.id}\' - \'{project.attributes.title}\' [{project.type}][{project.attributes.category}]')

    return project, json.loads(_content)['data']


def _update_project(self, node_object, ignore_error=True, verbose=True):
    """Overwrite object base on input node_object

    :param node_object: object includes new project's attributes
    :param ignore_error: boolean
    :param verbose: boolean
    :return: project object, and project dictionary
    """
    _data = self._prepare_project_data(node_object, verbose=verbose)
    _id = _data.get('data').get('id')

    logger.info('Update project')
    _response, _error_message = self._request('PUT', f'nodes/{_id}/', params={}, data=_data, )

    if _error_message:
        if not ignore_error:
            sys.exit(_error_message)
        if str(HTTP_403_FORBIDDEN) in _error_message:
            logger.error('Project could not be created')
        else:
            logger.error(_error_message)
        return None, None
    _content = _response.content

    # Parse JSON into an object with attributes corresponding to dict keys.
    response = json.loads(_content, object_hook=lambda d: SimpleNamespace(**d))

    project = response.data

    self.created_projects.append(project)

    logger.info(f'Updated project \'{project.id}\'')
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

    # Parse JSON into an object with attributes corresponding to dict keys.
    response = json.loads(_content, object_hook=lambda d: SimpleNamespace(**d))

    project_link = response.data
    project = None
    target_node = project_link.embeds.target_node
    if not hasattr(target_node, 'errors'):
        project = project_link.embeds.target_node.data

    if project:
        # node_id has already been added to projects_creation_output so only need add project_links
        if not check_dict_key(self.projects_creation_output[node_id], 'project_links'):
            self.projects_creation_output[node_id]['project_links'] = []
        if project.id not in self.projects_creation_output[node_id]['project_links']:
            self.projects_creation_output[node_id]['project_links'].append(project.id)

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
        project_link, linked = self._link_project_to_project(project.id, _node_id, ignore_error=True, verbose=verbose)

        if project_link is None:
            # has error, update output object
            project_links[_node_id_idx] = None
            continue

        # update output object
        # can overwrite object by dictionary _project_links[_node_id_idx] = _
        project_links[_node_id_idx] = linked['id']
    return project_links


def _add_project_components(self, children, project, verbose=True):
    """Add component to project from list of children in template file

    :param children: object of component from template file
    :param project: object of project
    :return: None
    """
    # get id of all children of current node, use for checking of step update children if exist
    children_of_project = self.get_all_data_from_api(f'nodes/{project.id}/children')
    list_children_of_project_ids = [node.id for node in children_of_project]

    for _component_idx, _component_dict in enumerate(children):
        _component_id = _component_dict.get('id')

        # Update children if ID EXIST in input
        if _component_id:
            # The input children_id is invalid if id has not exited in current_node's children
            if _component_id not in list_children_of_project_ids:
                logger.error("Project could not created")
                continue
            # update child node
            component = self._update_project_component(_component_dict, verbose)
            self._overwrite_node_link(component, _component_dict, verbose)
        # create new children if ID NOT EXIST in input
        else:
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

        # handle create/update children of current child
        self._overwrite_node_link_update_component(_component_dict, verbose)


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

    project.parent_id = parent_id
    # add to output for creating output file
    self.projects_creation_output[project.id] = convert_namespace_to_dict(project)

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


def _create_or_update_project(self, projects, project_idx, verbose=True):
    """Create new project or fork project or load project

    :param projects: list of project from template
    :param project_idx: integer of project index base on it order in project list
    :return: project object or None
    """
    _project_dict = projects[project_idx]
    _id = _project_dict.get('id')
    _fork_id = _project_dict.get('fork_id')

    # check exist both fork_id and id => skip
    if _id and _fork_id:
        logger.error('Project could not be created')
        return None
    elif _fork_id:
        logger.info(f'JSONPOINTER /projects/{project_idx}/fork_id == {_fork_id}')
        project, _ = self._fork_project(_project_dict, ignore_error=True, verbose=verbose)

        if project is None:
            # has error, update output object
            logger.warning(f'Project could not be created')
            projects[project_idx] = None
            return None

        # update output object
        # can overwrite object by dictionary _projects[_project_idx].update(_)
        _project_dict['id'] = project.id
        _project_dict['type'] = project.type

        # overwrite project
        self.projects_creation_output[project.id] = convert_namespace_to_dict(project)
    elif _id:
        logger.info(f'JSONPOINTER /projects/{project_idx}/id == {_id}')
        project, _ = self._load_project(_id, is_fake=const.IS_FAKE_LOAD_PROJECT, ignore_error=True, verbose=verbose)

        if project is None:
            # has error, update output object
            projects[project_idx] = None
            logger.error('Project could not be created')
            return None

        # update output object
        # can overwrite object by dictionary _projects[_project_idx].update(_)
        _project_dict['id'] = project.id
        _project_dict['type'] = project.type

        # overwrite project
        project, _  = self._update_project(_project_dict, ignore_error=True, verbose=verbose)

        # add to output
        self.projects_creation_output[project.id] = convert_namespace_to_dict(project)
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

        # add to output
        self.projects_creation_output[project.id] = convert_namespace_to_dict(project)
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

    self.projects_creation_output = {}

    logger.info(f'Use the template of projects: {self.template}')
    _input_prj_dicts = utils.read_json_file(self.template)

    try:
        # check json schema
        logger.info(f'Validate by the template of projects: {self.template_schema_projects}')
        utils.check_json_schema(self.template_schema_projects, _input_prj_dicts)

        logger.info('Loop following the template of projects')
        _input_projects = _input_prj_dicts.get('projects', [])
        for _project_idx, _input_prj_dict in enumerate(_input_projects):
            _input_children = _input_prj_dict.get('children', [])
            # project_link in input file
            _input_prj_link_ids = _input_prj_dict.get('project_links', None)

            # create new or fork project or update project
            project = self._create_or_update_project(_input_projects, _project_idx, verbose)
            if project is None:
                # update output object and ignore it
                _input_projects[_project_idx] = None
                continue

            # link a project to this node (parent_node_id = project.id)
            parent_node_id = _input_prj_dict.get('id', None)
            if _input_prj_link_ids is not None:
                # Add node link to project if current node is first create
                if parent_node_id is None:
                    # None => create new project base on _project_links
                    self._add_project_pointers(_input_prj_link_ids, project, verbose)

                    # Delete None from project_links
                    _input_prj_dict['project_links'] = [_pointer for _pointer in _input_prj_link_ids
                                                        if _pointer is not None]
                # overwrite node link of current project base on template input
                else:
                    self._overwrite_node_link(project, _input_prj_dict, verbose)

            # handle children of this node
            if len(_input_children):
                _input_prj_dict['children'] = [_child for _child in _input_children if _child is not None]
                _filtered_input_children = _input_prj_dict['children']

                # Create Components and lower level component
                self._add_project_components(_filtered_input_children, project, verbose)

        # Delete None from projects
        _input_prj_dicts['projects'] = [_prj for _prj in _input_projects if _prj is not None]

        _length = len(self.created_projects)
        if _length:
            # prepare output file
            logger.info(f'Use the output result file: {self.output_result_file}')
            self._prepare_output_file()
            # write output file
            output_result = {'projects': self._remapping_node(self.projects_creation_output)}
            utils.write_json_file(self.output_result_file, output_result)
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
                

def _overwrite_node_link(self, project, project_dict, verbose=True):
    """Override the node_link of input project if it has already existed.

    :param project: Object project want to update
    :param project_dict: Dict type project want to update, \n
        in this project_dict need to has project_links (from input)\n
        to checking and update
    :param verbose: Boolean
    :return"""

    parent_node_id = project_dict.get('id', None)
    # project_link in input file
    _input_prj_links_id = project_dict.get('project_links', None)
    if _input_prj_links_id is None:
        return
    _project_links = self.get_all_data_from_api(f'nodes/{parent_node_id}/node_links/')

    # list node id of linked
    _node_link_ids = []
    # list linked id
    _linked_ids = []
    for node in _project_links:
        _linked_ids.append(node.id)
        _node_link_ids.append(node.relationships.target_node.data.id)

    # list node_id will add new
    add_node_link_id_list = [node_id for node_id in _input_prj_links_id
                        if node_id not in _node_link_ids]
    # list node_id will remove from linked relationship
    remove_node_link_id_list = [node_id for node_id in _node_link_ids
                            if node_id not in _input_prj_links_id]

    # list id of linked relationship of removed node_id
    remove_linked_ids = []
    # find the linked_id need to delete
    # base on filtered node_id need to delete link_node above
    for node_id in remove_node_link_id_list:
        if node_id in _node_link_ids:
            remove_linked_ids.append(_linked_ids[
                _node_link_ids.index(node_id)])

    # remove node_link
    # use remove_linked_ids to process delete
    for linked_ids in remove_linked_ids:
        _, _error_message = self._request('DELETE', f'nodes/{parent_node_id}/node_links/{linked_ids}/')
        if _error_message:
            logger.error(_error_message)

    # Get node_link need to add new
    _need_create_node_link_ids = []
    for node_link_id in add_node_link_id_list:
        _, _error_message = self._request('GET', f'nodes/{node_link_id}')
        if _error_message:
            if str(HTTP_404_NOT_FOUND) in _error_message:
                logger.warn(f'"Target Node {node_link_id} not found"')
            continue
        _need_create_node_link_ids.append(node_link_id)

    # call api to create node_link
    self._add_project_pointers(_need_create_node_link_ids, project, verbose=verbose)


def _update_project_component(self, child_project_dict, verbose=True):
    """Update component (project children)

    :param child_project_dict: children dictionary
    :param verbose: Boolean
    :return"""

    child_id = child_project_dict.get('id', None)

    # call api get to check existence of child_project
    _, _error_message = self._request('GET', f'nodes/{child_id}/')

    # if any error (include not children has not existed)
    # will log error and do not handle update
    if _error_message:
        logger.error('Project could not be created')
    else:
        # prepare data to update node
        _data = self._prepare_project_data(child_project_dict, verbose=verbose)
        _response_child, _error_message_child = self._request('PUT', f'nodes/{child_id}/',
                                                    params={}, data=_data, )
        if _error_message_child:
            # handle message of each message code
            if str(HTTP_403_FORBIDDEN) in _error_message_child:
                logger.error(_error_message_child)
            else:
                logger.error("Project could not be created")
            return None
        response = json.loads(_response_child.content,
                                object_hook=lambda d: SimpleNamespace(**d))
        _node = response.data
        self.created_projects.append(_node)

        # Add current update node to output variable,
        # add parent_id to check later if it has parent relationship
        output_node = _node
        relationships = _node.relationships
        if hasattr(relationships, 'parent'):
            output_node.parent_id = relationships.parent.data.id
        if check_dict_key(child_project_dict, 'project_links'):
            output_node.project_links = child_project_dict['project_links']
        self.projects_creation_output[_node.id] = convert_namespace_to_dict(output_node)

        # OverrideNodeLink
        _child_node_link = child_project_dict.get('project_links', None)
        if _child_node_link:
            self._overwrite_node_link(_node, child_project_dict, verbose=verbose)

        # Handle children of current node
        _ip_children = child_project_dict.get('children', [])
        if len(_ip_children):
            child_project_dict['children'] = [_child for _child in _ip_children if _child is not None]
            _filtered_ip_children = child_project_dict['children']
            self._add_project_components(_filtered_ip_children, _node, verbose)
        return _node


def _overwrite_node_link_update_component(self, _input_prj_dicts, verbose=True):
    """Update component node link and update current component with the update of _input_prj_dicts

    :param _input_prj_dicts: list children want to update
    :param verbose: Boolean
    :return"""

    logger.info('Loop following the template of child projects')
    _input_projects = _input_prj_dicts.get('projects', [])
    for _project_idx, _input_prj_dict in enumerate(_input_projects):
        _input_children = _input_prj_dict.get('children', [])
        # project_link in input file
        _input_prj_links_id = _input_prj_dict.get('project_links', None)

        # create new or fork project or update project
        project = self._create_or_update_project(_input_projects, _project_idx, verbose)
        if project is None:
            # update output object and ignore it
            _input_projects[_project_idx] = None
            continue

        # link a project to this node (parent_node_id = project.id)
        parent_node_id = _input_prj_dict.get('id', None)
        if _input_prj_links_id is not None:
            # Add node link to project if current node is first create
            if parent_node_id is None:
                # None => create new project base on _project_links
                self._add_project_pointers(_input_prj_links_id, project, verbose)

                # Delete None from project_links
                _input_prj_dict['project_links'] = [_pointer for _pointer in _input_prj_links_id
                                                    if _pointer is not None]
            # overwrite node link of current project base on template input
            else:
                self._overwrite_node_link(project, _input_prj_dict, verbose)

        # Delete None from children
        if len(_input_children):
            _input_prj_dict['children'] = [_child for _child in _input_children if _child is not None]
            _filtered_ip_children = _input_prj_dict['children']

            # Create Components and lower level component
            self._add_project_components(_filtered_ip_children, project, verbose)


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


def _remapping_node(self, tree_root):
    """Receive a root dictionary and\n
        use the value properties to remapping with parent relationships
    
    :param tree_root: node dictionary with key is the id of node, value is node
    :return: list dictionary of mapped node (parent and children)
    """

    # get list node ids in tree_root
    list_ids = tree_root.keys()
    for id in list_ids:
        current_node = tree_root[id]
        # mapping to the parent if current node has parent_id
        if check_dict_key(current_node, 'parent_id'):
            parent_id = current_node['parent_id']
            parent_node = tree_root[parent_id]

            # when add child to it's parent,
            # that child will be change value to list
            # (ex: ['id_parent1', 'id_parent2',...]) => 'The order access id'
            # that value use to add lower children to correct parent tree 
            # A > B > C > D
            # D find parent C (assume C value is ['id_a', 'id_b'])
            # D will access to A first, then B, then C and add to C's children

            # parent value is list => current parent had been added to higher parent
            if type(parent_node) is list:
                # store 'The order access id' of parent
                last_parent_location = [id for id in parent_node]

                # add id_parent to create fully 'The order access id' of current node
                last_parent_location.append(parent_id)

                # check if the highest parent is also list,
                # we will loop and get the order access id
                # until the highest parent is object (current final parent root)
                while type(tree_root[last_parent_location[0]]) is list:
                    # get 'The order access id' of the highest parent
                    highest_parent = tree_root[last_parent_location[0]]
                    # update child 'The order access id'
                    last_parent_location = highest_parent + last_parent_location

                # get highest parent from 'The order access id'
                highest_parent = tree_root[last_parent_location[0]]
                # check if the parent has children property or not
                if not check_dict_key(highest_parent, 'children'):
                    # init if not exit property children
                    tree_root[last_parent_location[0]]['children'] = []
                # the final property children that current child can be appended to
                final_location_children = highest_parent['children']
                # start count from 1 cause
                # highest_parent has already start with index 0
                count = 1
                while count < len(last_parent_location):
                    # loop and store the children property of each parent until the last parent
                    list_ids_parent = [node['id'] for node in final_location_children]
                    index_parent = list_ids_parent.index(last_parent_location[count])
                    if not check_dict_key(final_location_children[index_parent], 'children'):
                        final_location_children[index_parent]['children'] = []
                    final_location_children = final_location_children[index_parent]['children']
                    count += 1

                # append current child to the final location
                final_location_children.append(self._convert_node_to_create_schema(current_node))
                # re-update value of child in the tree with list ids of parent
                tree_root[id] = last_parent_location
            else:
                # if the parent is object => add current child to parent's children
                if not check_dict_key(tree_root[parent_id], 'children'):
                    tree_root[parent_id]['children'] = []
                # convert child with template output before add to parent
                tree_root[parent_id]['children'].append(self._convert_node_to_create_schema(current_node))
                # update children with list parent ids
                tree_root[id] = [parent_id]
        else:
            # if has no property parent_id => current node is root
            tree_root[id] = self._convert_node_to_create_schema(current_node)
    # return list dictionary node
    return [node for node in tree_root.values() if type(node) is not list]


def _convert_node_to_create_schema(self, node):
    """Receive a node and convert it to the dictionary value base on output schema
    
    :param node: node need to convert
    :return: list dictionary of mapped node (parent and children)
    """

    attributes = node['attributes']
    relationships = node['relationships']
    license = attributes['node_license']

    result = {}
    result['id'] = node['id']
    result['type'] = node['type']
    result['title'] = attributes['title']
    result['category'] = attributes['category']
    result['description'] = attributes['description']
    result['public'] = attributes['public']
    result['tags'] = attributes['tags']

    if check_dict_key(attributes, 'children'):
        result['children'] = attributes['children']
    # get all node_link_id to update to project_links
    if check_dict_key(node, 'project_links'):
        _project_links = self.get_all_data_from_api(f'nodes/{node["id"]}/node_links/')
        result['project_links'] = []
        for project_link in _project_links:
            project = None
            target_node = project_link.embeds.target_node
            if not hasattr(target_node, 'errors'):
                project = project_link.embeds.target_node.data
                result['project_links'].append(project.id)

    # get license and add license_name to the output
    if license and check_dict_key(relationships, 'license'):
        license_id = relationships['license']['data']['id']
        if not (hasattr(self, 'licenses') and self.licenses):
            self._licenses(ignore_error=True)
        for lc in self.licenses:
            if lc.id == license_id:
                license['license_name'] = lc.attributes.name
        if check_dict_key(license, 'license_name'):
            result['node_license'] = convert_namespace_to_dict(license)

    # get fork_id if the node has forked from anther node
    if (check_dict_key(relationships, 'forked_from') and
        relationships['forked_from']['data']['id'] is not None):
        result['fork_id'] = relationships['forked_from']['data']['id']

    # mapping template_from
    if check_dict_key(relationships, 'template_node'):
        result['template_from'] = relationships['template_node']['data']['id']

    return result


def check_dict_key(dict, key):
    """Check the key is in dictionary
    
    :param dict: node want to check
    :param key: key need to check
    :return: Boolean
    """

    return hasattr(SimpleNamespace(**dict), key)