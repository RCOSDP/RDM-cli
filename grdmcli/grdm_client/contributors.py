import inspect  # noqa
import json
import logging
import os
import sys
from pprint import pprint  # noqa
from types import SimpleNamespace

from .. import constants as const, utils

__all__ = [
    '_get_template_schema_contributors',
    '_list_project_contributors',
    '_delete_project_contributor',
    '_prepare_project_contributor_data',
    '_add_project_contributor',
    '_overwrite_project_contributors',
    '_clear_project_current_contributors',
    'contributors_create',
]
here = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))

logger = logging.getLogger(__name__)


def _get_template_schema_contributors(self):
    return os.path.abspath(os.path.join(os.path.dirname(here), const.TEMPLATE_SCHEMA_CONTRIBUTORS))


def _list_project_contributors(self, pk, ignore_error=True, verbose=True):
    """Get list of contributors of a project by project GUID

    :param pk: string - Project GUID
    :param ignore_error: boolean
    :param verbose: boolean
    :return: contributors object, and contributors list
    """
    # logger.debug('----{}:{}::{} from {}:{}::{}'.format(*utils.inspect_info(inspect.currentframe(), inspect.stack())))

    if not self.user:
        sys.exit('Missing currently logged-in user')

    logger.info('Get list of contributors')
    params = {const.ORDERING_QUERY_PARAM: 'name'}
    _url = 'nodes/{node_id}/contributors/'.format(node_id=pk)
    _response, _error_message = self._request('GET', _url, params=params, data={}, )
    if _error_message:
        logger.warning(_error_message)
        if not ignore_error:
            sys.exit(_error_message)
        return [], []
    _content = _response.content

    # pprint(_response.json())
    # Parse JSON into an object with attributes corresponding to dict keys.
    response = json.loads(_content, object_hook=lambda d: SimpleNamespace(**d))

    contributors = response.data
    _contributors_numb = response.links.meta.total

    logger.info(f'List of contributors in project. [{_contributors_numb}]')
    if verbose:
        for contributor in contributors:
            attrs = contributor.attributes
            bibliographic_text = '[visible]' if attrs.bibliographic else ''
            tags_info = f'[{contributor.type}][{attrs.permission}][{attrs.index}]{bibliographic_text}'
            users = contributor.embeds.users
            if not hasattr(users, 'errors'):
                user = users.data.attributes
                logger.debug(f'\'{contributor.id}\' - \'{user.full_name}\' {tags_info}')
            else:
                errors = users.errors
                logger.debug(f'\'{contributor.id}\' - \'{errors[0].detail}\' {tags_info }')

    return contributors, json.loads(_content)['data']


def _delete_project_contributor(self, pk, user_id, ignore_error=True, verbose=True):
    """Delete a contributor from a project

    :param pk: string - Project GUID
    :param user_id: string - User GUID of a contributor
    :param ignore_error: boolean
    :param verbose: boolean
    :return: tuple of user_id, is_deleted
    """
    # logger.debug('----{}:{}::{} from {}:{}::{}'.format(*utils.inspect_info(inspect.currentframe(), inspect.stack())))

    logger.info(f'Remove contributor \'{pk}-{user_id}\'')
    _url = 'nodes/{node_id}/contributors/{user_id}'.format(node_id=pk, user_id=user_id)
    _response, _error_message = self._request('DELETE', _url, params={}, data={}, )
    is_deleted = not bool(_error_message)
    if _error_message:
        logger.warning(f'{_error_message}')
        if not ignore_error:
            sys.exit(_error_message)

    if verbose and is_deleted:
        logger.debug(f'Deleted contributor: \'{pk}-{user_id}\'')

    return user_id, is_deleted


def _prepare_project_contributor_data(self, contributor_object, index, verbose=True):
    """Make a request body for the API Create new Contributor

    :param contributor_object: object includes user GUID and new contributor's attributes
    :param index: contributor's index attribute
    :param verbose: boolean
    :return: object of request body
    """
    # logger.debug('----{}:{}::{} from {}:{}::{}'.format(*utils.inspect_info(inspect.currentframe(), inspect.stack())))

    _contributor = contributor_object

    # initial
    _user_id = _contributor.get('id')
    _bibliographic = _contributor.get('bibliographic', True)
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
        logger.debug(f'Prepared contributor data: {_data}')

    return _data


def _add_project_contributor(self, pk, contributor_object, index, ignore_error=True, verbose=True):
    """

    :param pk: string - Project GUID
    :param contributor_object: object includes user GUID and new contributor's attributes
    :param index: contributor's index attribute
    :param ignore_error: boolean
    :param verbose: boolean
    :return: contributor object, and contributor dictionary
    """
    # logger.debug('----{}:{}::{} from {}:{}::{}'.format(*utils.inspect_info(inspect.currentframe(), inspect.stack())))

    _data = self._prepare_project_contributor_data(contributor_object, index, verbose=verbose)
    user_id = contributor_object['id']

    logger.info(f'Add contributor \'{pk}-{user_id}\'')
    _url = 'nodes/{node_id}/contributors/'.format(node_id=pk)
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

    contributor = response.data

    self.created_project_contributors.append(contributor)

    if verbose:
        logger.debug(f'Created contributor: \'{pk}-{user_id}\'')
        users = contributor.embeds.users.data.attributes
        attrs = contributor.attributes
        logger.debug(f'\'{contributor.id}\' - \'{users.full_name}\' [{contributor.type}][{attrs.permission}][{attrs.index}]')

    return contributor, json.loads(_content)['data']


def _overwrite_project_contributors(self, contributors, pk, contributor_user_ids, current_user_contributor, verbose=True):
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
        logger.info(f'JSONPOINTER ./contributors/{_user_idx}/ user_id={_user_id}')

        if _user_id == self.user.id:
            logger.warning('This member is the currently logged-in user, so skip creating/updating')
            if current_user_contributor:
                # update output object
                # can overwrite object by _contributors[_user_idx].update(contributor_dict)
                _index = _user_idx - _invalid_user_obj_number
                _obj = contributors[_user_idx]
                _contributor_attr = current_user_contributor.attributes
                _obj['id'] = current_user_contributor.id
                _obj['type'] = current_user_contributor.type
                _obj['index'] = _index
                _obj['bibliographic'] = _contributor_attr.bibliographic
                _obj['permission'] = _contributor_attr.permission
            continue

        if _user_id in contributor_user_ids:
            logger.warning('Duplicate member object in template file')
            # update output object
            contributors[_user_idx] = None
            _invalid_user_obj_number += 1
            continue

        # Call API Create a contributor
        _index = _user_idx - _invalid_user_obj_number
        contributor, _ = self._add_project_contributor(pk, _user_dict, _index, verbose=verbose)
        if contributor is None:
            # has error, update output object
            contributors[_user_idx] = None
            _invalid_user_obj_number += 1
            continue

        # cache user id after adding
        contributor_user_ids.append(_user_id)

        # update output object
        # can overwrite object by _contributors[_user_idx].update(_)
        _obj = contributors[_user_idx]
        _contributor_attr = contributor.attributes
        _obj['id'] = contributor.id
        _obj['type'] = contributor.type
        _obj['index'] = _contributor_attr.index
        _obj['bibliographic'] = _contributor_attr.bibliographic
        _obj['permission'] = _contributor_attr.permission


def _clear_project_current_contributors(self, pk, contributor_user_ids, current_user_contributor, verbose=True):
    """Clear list of current contributors from this project, except for the currently logged-in user

    :param pk: string - Project GUID
    :param contributor_user_ids: list of the user GUID which is project contributor
    :param current_user_contributor: object of contributor which is current user
    :return: object of contributor which is current user
    """
    # Get all current contributors from this project
    old_contributors, _ = self._list_project_contributors(pk, verbose=verbose)

    if not old_contributors:
        return None

    # Delete all current contributors from this project
    for contributor in old_contributors:
        users = contributor.embeds.users
        if hasattr(users, 'errors'):
            continue

        # except for the currently logged-in user
        if users.data.id == self.user.id:
            logger.debug(f'Ignore currently logged-in user {self.user.id}')
            self.created_project_contributors.append(contributor)
            current_user_contributor = contributor
            contributor_user_ids.append(self.user.id)
            continue

        # Delete available contributor
        user_id = users.data.id
        _, is_deleted = self._delete_project_contributor(pk, user_id, verbose=verbose)

        # in case cannot delete
        if not is_deleted:
            self.created_project_contributors.append(contributor)
            contributor_user_ids.append(user_id)

    return current_user_contributor


def contributors_create(self):
    """Overwrite the contributor list of a project following the structure and info which defined in a template JSON file.\n
    Delete contributors from the project; expect the current user as admin.\n
    Add contributors in order from template into the project.

    :return: None
    """
    # logger.debug('----{}:{}::{} from {}:{}::{}'.format(*utils.inspect_info(inspect.currentframe(), inspect.stack())))
    verbose = self.verbose

    logger.info('Check config and authenticate by token')
    # the current_user_id is self.user.id
    self._check_config(verbose=verbose)

    if not os.path.exists(self.template_schema_contributors):
        sys.exit(f'Missing the template schema {self.template_schema_contributors}')

    if not os.path.exists(self.template):
        sys.exit('Missing the template file')

    logger.info(f'Use the template of contributors: {self.template}')
    _projects_dict = utils.read_json_file(self.template)

    try:
        # check json schema
        logger.info(f'Validate by the template of projects: {self.template_schema_contributors}')
        utils.check_json_schema(self.template_schema_contributors, _projects_dict)

        logger.info('Loop following the template of contributors')
        _projects = _projects_dict.get('projects', [])
        for idx, _project_dict in enumerate(_projects):
            _id = _project_dict.get('id')
            logger.info(f'JSONPOINTER /projects/{idx}/')
            _contributors = _project_dict.get('contributors', [])

            if not _id:
                logger.warning(f'Missing project id')

                # update output object and ignore it
                _projects[idx] = None
                continue

            current_user_contributor = None
            current_project_contributor_user_ids = []

            logger.info('Remove current contributors')
            current_user_contributor = self._clear_project_current_contributors(_id, current_project_contributor_user_ids, current_user_contributor, verbose=verbose)

            if current_user_contributor is None:
                logger.warning(f'Project is not found')

                # update output object and ignore it
                _projects[idx] = None
                continue

            logger.info('Overwrite new contributors')
            self._overwrite_project_contributors(_contributors, _id, current_project_contributor_user_ids, current_user_contributor, verbose=verbose)

            # update all current contributors of this project
            current_project_contributors, _ = self._list_project_contributors(_id, verbose=verbose)
            _length_all = len(self.created_project_contributors)
            _length_prj = len(current_project_contributors)
            self.created_project_contributors[-_length_prj:] = current_project_contributors

            # Delete None from contributors
            if _contributors:
                _project_dict['contributors'] = [_contributor for _contributor in _contributors if _contributor is not None]

        # Delete None from projects
        _projects_dict['projects'] = [_prj for _prj in _projects if _prj is not None]

        _length = len(self.created_project_contributors)
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
        _length = len(self.created_project_contributors)
        if verbose and _length:
            logger.debug(f'Created contributors for projects. [{_length}]')
            for contributor in self.created_project_contributors:
                attrs = contributor.attributes
                bibliographic_text = '[visible]' if attrs.bibliographic else ''
                tags_info = f'[{contributor.type}][{attrs.permission}][{attrs.index}]{bibliographic_text}'
                users = contributor.embeds.users.data.attributes
                logger.debug(f'\'{contributor.id}\' - \'{users.full_name}\' {tags_info}')
