import inspect  # noqa
import json
import logging
import os
import sys
from pprint import pprint  # noqa
from types import SimpleNamespace

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
                'id': self._find_license_id_from_name(_license.get('license_name'))
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
    _faked_or_loaded = f'[loaded nodes/{pk}/]'

    if is_fake:
        _faked_or_loaded = '[faked]'
        _content = self._fake_project_content_data(pk, verbose=verbose)

    logger.info(f'GET Retrieve project {_faked_or_loaded}')
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

    if verbose:
        logger.debug('Loaded project:')
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

    logger.info(f'POST Fork a project from nodes/{pk}/')
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

    if verbose:
        logger.debug('Forked project:')
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

    logger.info('POST Create new project')
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

    if verbose:
        logger.debug('Created project:')
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

    logger.info(f'POST Create a link to nodes/{node_id}/')
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

    if verbose:
        if project:
            logger.debug('Created Node Links:')
            logger.debug(f'\'{project_link.id}\' - [{project_link.type}]')
            logger.debug(f'\'{project.id}\' - \'{project.attributes.title}\' [{project.type}][{project.attributes.category}]')
        else:
            errors = target_node.errors
            logger.debug(f'ERROR when link to {pointer_id}: {errors[0].detail}')

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

    logger.info(f'POST Create new component to nodes/{parent_id}/')
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

    if verbose:
        logger.debug('Create component:')
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
        project, _ = self._load_project(_id, is_fake=False, ignore_error=True, verbose=verbose)

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

    logger.info(f'USE the template of projects: {self.template}')
    _projects_dict = utils.read_json_file(self.template)

    try:
        # check json schema
        logger.info(f'VALIDATE BY the template of projects: {self.template_schema_projects}')
        utils.check_json_schema(self.template_schema_projects, _projects_dict)

        logger.info('LOOP Following the template of projects')
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
            logger.info(f'USE the output result file: {self.output_result_file}')
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
