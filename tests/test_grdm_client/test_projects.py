import json
from types import SimpleNamespace
from unittest import mock

import pytest
import requests

from grdmcli.exceptions import GrdmCliException
from grdmcli.grdm_client.projects import (
    _get_template_schema_projects,
    _fake_project_content_data,
    _prepare_project_data,
    _load_project,
    _fork_project,
    _create_project,
    _link_project_to_project,
    _add_project_pointers,
    _add_project_components,
    _projects_add_component,
    _create_or_load_project,
    projects_create,
)
from tests.factories import GRDMClientFactory

_content = json.dumps({
    'data': {
        'id': 'node01',
        'type': 'nodes',
        'attributes': {
            'title': 'N/A',
            'category': 'N/A'
        },
        'relationships': {}
    }
})
# index = 0: new , index = 1: license, index = 2: link, index = 3: fork
projects = {
    "projects": [
        {
            "category": "project",
            "title": "Project Example 001",
            "description": "Lorem Ipsum has been the industry's standard dummy text ever since the 1500s, when an unknown printer took a galley of type and scrambled it to make a type specimen book.",
            "public": False,
            "tags": [
                "replication",
                "reproducibility",
                "open science",
                "reproduction",
                "psychological science",
                "psychology",
                "metascience",
                "crowdsource"
            ],
            "template_from": "abc36",
            "children": [
                {
                    "id": "abcd3",
                    "category": "analysis",
                    "title": "Analysis Component Example 001",
                    "description": "Lorem Ipsum is simply dummy text of the printing and typesetting industry.",
                    "public": False,
                    "tags": [
                        "analysis",
                        "component"
                    ]
                },
                {
                    "id": "abcd4",
                    "category": "communication",
                    "title": "Communication Component Example 001"
                }
            ]
        },
        {
            "id": "abcd5",
            "category": "project",
            "title": "Project Example License 001",
            "description": "Lorem Ipsum has been the industry's standard dummy text ever since the 1500s, when an unknown printer took a galley of type and scrambled it to make a type specimen book.",
            "tags": [
                "license"
            ],
            "node_license": {
                "license_name": "MIT License",
                "copyright_holders": [
                    "holder1",
                    "holder2"
                ],
                "year": "2023"
            }
        },
        {
            "id": "nid20",
            "children": [
                {
                    "category": "project",
                    "title": "Project Example 003",
                    "children": [
                        {
                            "category": "project",
                            "title": "Project Example 004"
                        }
                    ],
                    "project_links": [
                        "nid90",
                        "nid91"
                    ]
                }
            ],
            "project_links": [
                "nid92",
                "nid93"
            ]
        },
        {
            "fork_id": "abcd7",
            "category": "project",
            "title": "Project Example 002",
            "description": "Lorem Ipsum has been the industry's standard dummy text ever since the 1500s.",
            "public": False,
            "tags": [
                "replication",
                "fork"
            ],
            "children": []
        }
    ]
}
fork_project_str = """{
    "data": {
        "id": "nfid1",
        "type": "nodes",
        "attributes": {
            "category": "project",
            "fork": true,
            "preprint": false,
            "current_user_permissions": [
            "read",
            "write",
            "admin"
            ],
            "date_modified": "2016-07-23T00:21:05.371000",
            "forked_date": "2016-11-08T15:59:03.114000",
            "collection": false,
            "registration": false,
            "date_created": "2012-04-01T15:49:07.702000",
            "title": "Project Example 002",
            "node_license": null,
            "description": "Lorem Ipsum has been the industry's standard dummy text ever since the 1500s.",
            "public": false,
            "tags": [
                "replication",
                "fork"
            ]
        },
        "relationships": {}
    }
}"""
new_project_str = """{"data":{
    "relationships": {},
    "links": {
        "self": "https://api.osf.io/v2/nodes/ezcuj/",
        "html": "https://osf.io/ezcuj/"
    },
    "attributes": {
        "category": "project",
        "title": "Project Example 001",
        "template_from": "abc36",
        "public": true,
        "tags": [
            "replication",
            "reproducibility",
            "open science",
            "reproduction",
            "psychological science",
            "psychology",
            "metascience",
            "crowdsource"
        ],
        "fork": false,
        "preprint": false,
        "description": "",
        "current_user_permissions": [
            "read"
        ],
        "date_modified": "2016-12-08T21:45:17.058000",
        "collection": false,
        "registration": false,
        "date_created": "2012-04-01T15:49:07.702000",
        "current_user_can_comment": true,
        "node_license": null
    },
    "type": "nodes",
    "id": "ezcuj"
}}"""
link_project_str = """{
    "data": {
        "id": "73pnd",
        "type": "nodes",
        "attributes": {
            "category": "project",
            "fork": false,
            "preprint": false,
            "description": null,
            "current_user_permissions": [
                "read"
            ],
            "date_modified": "2016-10-02T19:50:23.605000",
            "title": "Replication of Hajcak &amp; Foti (2008, PS, Study 1)",
            "collection": false,
            "registration": false,
            "date_created": "2012-10-31T18:50:46.111000",
            "current_user_can_comment": false,
            "node_license":null,
            "public": true,
            "tags": [
                "anxiety"
            ]
        },
        "relationships":{},
        "embeds":{
            "target_node":{
                "data":{
                    "id": "74pnd",
                    "type": "nodes",
                    "attributes": {
                        "category": "project",
                        "fork": true,
                        "preprint": false,
                        "description": null,
                        "current_user_permissions": [
                            "read"
                        ],
                        "title": "Replication of Hajcak &amp; Foti (2008, PS, Study 2)",
                        "collection": false,
                        "registration": false,
                        "date_created": "2012-10-31T18:50:46.111000",
                        "current_user_can_comment": false,
                        "node_license": null,
                        "public": true,
                        "tags": [
                            "motivation"
                        ]
                    }
                }
            }
        }
    }
}"""
content_obj = json.loads(_content, object_hook=lambda d: SimpleNamespace(**d))
fork_project_obj = json.loads(fork_project_str, object_hook=lambda d: SimpleNamespace(**d))
new_project_obj = json.loads(new_project_str, object_hook=lambda d: SimpleNamespace(**d))
link_project_obj = json.loads(link_project_str, object_hook=lambda d: SimpleNamespace(**d))
projects_obj = json.loads(json.dumps(projects), object_hook=lambda d: SimpleNamespace(**d))


@pytest.fixture
def grdm_client():
    return GRDMClientFactory()


def test_get_template_schema_projects__normal():
    actual = _get_template_schema_projects(grdm_client)
    assert type(actual) is str
    assert actual.__contains__('projects_create_schema.json')


def test_fake_project_content_data__verbose_false(capfd):
    actual = _fake_project_content_data(grdm_client, 'node01', verbose=False)
    captured = capfd.readouterr()
    assert actual == _content
    assert captured.out == ''


def test_fake_project_content_data__verbose_true(capfd):
    actual = _fake_project_content_data(grdm_client, 'node01', verbose=True)
    captured = capfd.readouterr()
    assert actual == _content
    assert captured.out == f'prepared project data: {_content}\n'


def test_prepare_project_data__all_new_not_license(grdm_client):
    _project = projects.get('projects')[0]
    actual = _prepare_project_data(grdm_client, _project, verbose=False)
    assert actual['data']['type'] == 'nodes'
    assert actual['data']['attributes']['tags'] == _project['tags']
    assert actual['data']['attributes']['public'] == _project['public']
    assert actual['data']['relationships'] == {}


def test_prepare_project_data__new_has_license_verbose_true(grdm_client, capfd):
    license_id = 'license01'
    _project = projects['projects'][1]
    with mock.patch.object(grdm_client, '_find_license_id_from_name', return_value=license_id):
        actual = _prepare_project_data(grdm_client, _project, verbose=True)
        assert actual['data']['type'] == 'nodes'
        assert actual['data']['attributes']['tags'] == _project['tags']
        assert actual['data']['attributes']['public'] is False
        _license = _project.get('node_license', {})
        del _license['license_name']
        assert actual['data']['attributes']['node_license'] == _license
        assert actual['data']['relationships']['license']['data']['id'] == license_id
        capture = capfd.readouterr()
        lines = capture.out.split('\n')
        assert len(lines) == 2
        assert lines[0].__contains__('Prepared project data:')


def test_prepare_project_data__fork_project(grdm_client, capfd):
    _project = projects['projects'][3]
    actual = _prepare_project_data(grdm_client, _project, verbose=True)
    assert actual['data']['type'] == 'nodes'
    assert actual['data']['attributes']['tags'] == _project['tags']
    assert actual['data']['attributes']['public'] == _project['public']
    assert actual['data']['relationships'] == {}


def test_load_project__is_fake_and_verbose_true(capfd, grdm_client):
    with mock.patch.object(grdm_client, '_fake_project_content_data', return_value=_content):
        actual1, actual2 = _load_project(grdm_client, pk='node01', verbose=True)
        _faked_or_loaded = '[faked]'
        lines = capfd.readouterr().out.split('\n')
        assert lines[0] == f'GET Retrieve project {_faked_or_loaded}'
        assert lines[1] == f'Loaded project:'
        assert len(lines) == 4
        assert actual1 == content_obj.data
        assert type(actual2) is dict


def test_load_project__is_fake_false_and_request_error_and_ignore_error_false_sys_exit(grdm_client, capfd):
    error_message = 'error'
    with mock.patch.object(grdm_client, '_request', return_value=(None, error_message)):
        with pytest.raises(SystemExit) as ex_info:
            _load_project(grdm_client, pk='node01', is_fake=False, ignore_error=False)
        assert ex_info.value.code == error_message
        lines = capfd.readouterr().out.split('\n')
        _faked_or_loaded = f'[loaded nodes/node01/]'
        assert lines[0] == f'GET Retrieve project {_faked_or_loaded}'
        assert lines[1] == f'WARN {error_message}'


def test_load_project__is_fake_false_and_request_error_and_ignore_error_true(grdm_client, capfd):
    error_message = 'error'
    with mock.patch.object(grdm_client, '_request', return_value=(None, error_message)):
        actual1, actual2 = _load_project(grdm_client, pk='node01', is_fake=False, ignore_error=True)
        lines = capfd.readouterr().out.split('\n')
        _faked_or_loaded = f'[loaded nodes/node01/]'
        assert lines[0] == f'GET Retrieve project {_faked_or_loaded}'
        assert lines[1] == f'WARN {error_message}'
        assert len(lines) == 3
        assert actual1 == actual2 is None


def test_load_project__is_fake_false_verbose_false(capfd, grdm_client):
    resp = requests.Response()
    resp._content = new_project_str
    with mock.patch.object(grdm_client, '_request', return_value=(resp, None)):
        actual1, actual2 = _load_project(grdm_client, pk='node01', is_fake=False, verbose=False)
        captured = capfd.readouterr()
        _faked_or_loaded = f'[loaded nodes/node01/]'
        assert captured.out == f'GET Retrieve project {_faked_or_loaded}\n'
        assert actual1 == new_project_obj.data
        assert actual2 == json.loads(new_project_str)['data']


def test_fork_project__request_error_and_ignore_error_false_sys_exit(grdm_client, capfd):
    _node_project = projects['projects'][3]
    error_message = 'error'
    with mock.patch.object(grdm_client, '_request', return_value=(None, error_message)):
        with pytest.raises(SystemExit) as ex_info:
            _fork_project(grdm_client, _node_project, ignore_error=False, verbose=False)
        assert ex_info.value.code == error_message
        lines = capfd.readouterr().out.split('\n')
        pk = _node_project['fork_id']
        assert lines[0] == f'POST Fork a project from nodes/{pk}/'
        assert lines[1] == f'WARN {error_message}'
        assert len(lines) == 3


def test_fork_project__request_error_and_ignore_error_true(grdm_client, capfd):
    error_message = 'error'
    _node_project = projects['projects'][3]
    with mock.patch.object(grdm_client, '_request', return_value=(None, error_message)):
        actual1, actual2 = _fork_project(grdm_client, _node_project, ignore_error=True, verbose=False)
        lines = capfd.readouterr().out.split('\n')
        pk = _node_project['fork_id']
        assert actual1 == actual2 is None
        assert lines[0] == f'POST Fork a project from nodes/{pk}/'
        assert lines[1] == f'WARN {error_message}'
        assert len(lines) == 3


def test_fork_project__verbose_true(grdm_client, capfd):
    resp = requests.Response()
    resp._content = fork_project_str
    _node_project = projects['projects'][3]
    with mock.patch.object(grdm_client, '_request', return_value=(resp, None)):
        actual1, actual2 = _fork_project(grdm_client, _node_project, verbose=True)
        lines = capfd.readouterr().out.split('\n')
        pk = _node_project['fork_id']
        assert actual1 == fork_project_obj.data
        assert actual2 == json.loads(fork_project_str)['data']
        assert lines[0] == f'POST Fork a project from nodes/{pk}/'
        assert lines[1] == f'Forked project:'
        assert len(lines) == 4


def test_create_project__request_error_and_ignore_error_false_sys_exit(grdm_client, capfd):
    _node_project = projects['projects'][0]
    error_message = 'error'
    with mock.patch.object(grdm_client, '_request', return_value=(None, error_message)):
        with pytest.raises(SystemExit) as ex_info:
            _create_project(grdm_client, _node_project, ignore_error=False, verbose=False)
        assert ex_info.value.code == error_message
        lines = capfd.readouterr().out.split('\n')
        assert lines[0] == f'POST Create new project'
        assert lines[1] == f'WARN {error_message}'
        assert len(lines) == 3


def test_create_project__request_error_and_ignore_error_true(grdm_client, capfd):
    error_message = 'error'
    _node_project = projects['projects'][0]
    with mock.patch.object(grdm_client, '_request', return_value=(None, error_message)):
        actual1, actual2 = _create_project(grdm_client, _node_project, ignore_error=True, verbose=False)
        lines = capfd.readouterr().out.split('\n')
        assert actual1 == actual2 is None
        assert lines[0] == f'POST Create new project'
        assert lines[1] == f'WARN {error_message}'
        assert len(lines) == 3


def test_create_project__verbose_true(grdm_client, capfd):
    resp = requests.Response()
    resp._content = new_project_str
    _node_project = projects['projects'][0]
    with mock.patch.object(grdm_client, '_request', return_value=(resp, None)):
        actual1, actual2 = _create_project(grdm_client, _node_project, verbose=True)
        lines = capfd.readouterr().out.split('\n')
        assert actual1 == new_project_obj.data
        assert actual2 == json.loads(new_project_str)['data']
        assert lines[0] == f'POST Create new project'
        assert lines[1] == f'Created project:'
        assert len(lines) == 4


def test_link_project_to_project__request_error_and_ignore_error_false_sys_exit(grdm_client, capfd):
    _project_id = projects['projects'][2]['id']
    error_message = 'error'
    with mock.patch.object(grdm_client, '_request', return_value=(None, error_message)):
        with pytest.raises(SystemExit) as ex_info:
            _link_project_to_project(grdm_client, _project_id, 'abcd6', ignore_error=False, verbose=False)
        assert ex_info.value.code == error_message
        lines = capfd.readouterr().out.split('\n')
        assert lines[0] == f'POST Create a link to nodes/{_project_id}/'
        assert lines[1] == f'WARN {error_message}'
        assert len(lines) == 3


def test_link_project_to_project__request_error_and_ignore_error_true(grdm_client, capfd):
    error_message = 'error'
    _project_id = projects['projects'][2]['id']
    with mock.patch.object(grdm_client, '_request', return_value=(None, error_message)):
        actual1, actual2 = _link_project_to_project(grdm_client, _project_id, 'abcd6', ignore_error=True)
        lines = capfd.readouterr().out.split('\n')
        assert actual1 == actual2 is None
        assert lines[0] == f'POST Create a link to nodes/{_project_id}/'
        assert lines[1] == f'WARN {error_message}'
        assert len(lines) == 3


def test_link_project_to_project__verbose_true(grdm_client, capfd):
    resp = requests.Response()
    resp._content = link_project_str
    _project_id = projects['projects'][2]['id']
    with mock.patch.object(grdm_client, '_request', return_value=(resp, None)):
        actual1, actual2 = _link_project_to_project(grdm_client, _project_id, '74pnd', verbose=True)
        lines = capfd.readouterr().out.split('\n')
        project_link = link_project_obj.data.embeds.target_node.data
        assert actual1 == project_link
        assert actual2 == json.loads(link_project_str)['data']
        assert lines[0] == f'POST Create a link to nodes/{_project_id}/'
        assert lines[1] == f'Created Node Links:'
        assert len(lines) == 5


def test_add_project_pointers__project_link_is_none(grdm_client, capfd):
    _project = projects_obj.projects[2]
    _project_links = ['74pnd', 'abcd7']
    project_link = link_project_obj.data.embeds.target_node.data
    with mock.patch.object(grdm_client, '_link_project_to_project', side_effect=[(project_link, None), (None, None)]):
        _add_project_pointers(grdm_client, _project_links, _project)
        lines = capfd.readouterr().out.split('\n')
        assert _project_links == ['74pnd', None]
        assert lines[0] == f'JSONPOINTER ./project_links/0/'
        assert lines[1] == f'JSONPOINTER ./project_links/1/'
        assert len(lines) == 3


def test_create_or_load_project__case_load_project_none(grdm_client, capfd):
    _projects = (projects.get('projects', [])).copy()
    _id = _projects[2].get('id')
    with mock.patch.object(grdm_client, '_load_project', return_value=(None, None)):
        actual = _create_or_load_project(grdm_client, _projects, 2)
        lines = capfd.readouterr().out
        assert lines == f'JSONPOINTER /projects/2/id == {_id}\n'
        assert actual is None
        assert _projects[2] is None


def test_create_or_load_project__case_load_project(capfd, grdm_client):
    _projects = projects.get('projects', [])
    _id = _projects[2].get('id')
    with mock.patch.object(grdm_client, '_load_project', return_value=(link_project_obj.data, None)):
        actual = _create_or_load_project(grdm_client, _projects, 2)
        lines = capfd.readouterr().out
        assert lines == f'JSONPOINTER /projects/2/id == {_id}\n'
        assert actual is link_project_obj.data
        assert _projects[2]['id'] == link_project_obj.data.id
        assert _projects[2]['type'] == link_project_obj.data.type


def test_create_or_load_project__case_create_project_none(capfd, grdm_client):
    _projects = (projects.get('projects', [])).copy()
    with mock.patch.object(grdm_client, '_create_project', return_value=(None, None)):
        actual = _create_or_load_project(grdm_client, _projects, 0)
        lines = capfd.readouterr().out
        assert lines == f'JSONPOINTER /projects/0/\n'
        assert actual is None
        assert _projects[0] is None


def test_create_or_load_project__case_create_project(capfd, grdm_client):
    _projects = projects.get('projects', [])
    with mock.patch.object(grdm_client, '_create_project', return_value=(new_project_obj.data, None)):
        actual = _create_or_load_project(grdm_client, _projects, 0)
        lines = capfd.readouterr().out
        assert lines == f'JSONPOINTER /projects/0/\n'
        assert actual is new_project_obj.data
        assert _projects[0]['id'] == new_project_obj.data.id
        assert _projects[0]['type'] == new_project_obj.data.type


def test_create_or_load_project__case_fork_project_none(capfd, grdm_client):
    _projects = (projects.get('projects', [])).copy()
    _fork_id = _projects[3].get('fork_id')
    with mock.patch.object(grdm_client, '_fork_project', return_value=(None, None)):
        actual = _create_or_load_project(grdm_client, _projects, 3)
        lines = capfd.readouterr().out
        assert lines == f'JSONPOINTER /projects/3/fork_id == {_fork_id}\n'
        assert actual is None
        assert _projects[3] is None


def test_create_or_load_project__case_fork_project(capfd, grdm_client):
    _projects = projects.get('projects', [])
    _fork_id = _projects[3].get('fork_id')
    with mock.patch.object(grdm_client, '_fork_project', return_value=(fork_project_obj.data, None)):
        actual = _create_or_load_project(grdm_client, _projects, 3)
        lines = capfd.readouterr().out
        assert lines == f'JSONPOINTER /projects/3/fork_id == {_fork_id}\n'
        assert actual is fork_project_obj.data
        assert _projects[3]['id'] == fork_project_obj.data.id
        assert _projects[3]['type'] == fork_project_obj.data.type


def test_add_project_components__children_exist_id_ignored(grdm_client, capfd):
    _children = projects['projects'][0]['children']
    children = [_children[1]]
    _add_project_components(grdm_client, children, link_project_obj.data)
    assert capfd.readouterr().out == f'JSONPOINTER ./children/0/ ignored\n'
    assert children[0] is None


def test_add_project_components__add_components_is_none(grdm_client, capfd):
    _children = (projects['projects'][2]['children']).copy()
    children = [_children[0]]
    with mock.patch.object(grdm_client, '_projects_add_component', return_value=(None, None)):
        _add_project_components(grdm_client, children, link_project_obj.data)
    assert capfd.readouterr().out == f'JSONPOINTER ./children/0/\n'
    assert children[0] is None


def test_add_project_components__add_components_success(grdm_client, capfd):
    _project = link_project_obj.data
    _children = projects['projects'][2]['children']
    children = [_children[0]]
    component = new_project_obj.data
    with mock.patch.object(grdm_client, '_projects_add_component', return_value=(component, None)):
        _add_project_components(grdm_client, children, _project)
    assert capfd.readouterr().out == f'JSONPOINTER ./children/0/\n'
    assert children[0]['id'] == component.id
    assert children[0]['type'] == component.type


def test_projects_add_component__request_error_and_ignore_error_false_sys_exit(grdm_client, capfd):
    _project = projects['projects'][2]
    error_message = 'error'
    parent_id = 'nid11'
    with mock.patch.object(grdm_client, '_request', return_value=(None, error_message)):
        with pytest.raises(SystemExit) as ex_info:
            _projects_add_component(grdm_client, parent_id, _project, ignore_error=False)
        assert ex_info.value.code == error_message
        captured = capfd.readouterr()
        lines = captured.out.split('\n')
        assert lines[0] == f'POST Create new component to nodes/{parent_id}/'
        assert lines[1] == f'WARN {error_message}'
        assert len(lines) == 3


def test_projects_add_component__request_error_and_ignore_error_true(grdm_client, capfd):
    error_message = 'error'
    _project = projects['projects'][2]
    parent_id = 'nid11'
    with mock.patch.object(grdm_client, '_request', return_value=(None, error_message)):
        actual1, actual2 = _projects_add_component(grdm_client, parent_id, _project, ignore_error=True)
        captured = capfd.readouterr()
        lines = captured.out.split('\n')
        assert actual1 == actual2 is None
        assert lines[0] == f'POST Create new component to nodes/{parent_id}/'
        assert lines[1] == f'WARN {error_message}'
        assert len(lines) == 3


def test_projects_add_component__verbose_true(grdm_client, capfd):
    resp = requests.Response()
    resp._content = new_project_str
    _project = projects['projects'][2]
    parent_id = 'nid11'
    _project['project_links'] = ['nid92', None]
    _project['children'] = [_project['children'][0], None]
    with mock.patch.object(grdm_client, '_request', return_value=(resp, None)):
        actual1, actual2 = _projects_add_component(grdm_client, parent_id, _project, verbose=True)
        assert _project['project_links'] == ['nid92']
        assert _project['children'] == [_project['children'][0]]
        assert actual1 == new_project_obj.data
        assert actual2 == json.loads(new_project_str)['data']
        lines = capfd.readouterr().out.split('\n')
        assert lines[0] == f'POST Create new component to nodes/{parent_id}/'
        assert lines[1] == f'Create component:'
        assert len(lines) == 4


def test_projects_create__schema_not_exist(grdm_client):
    with mock.patch('os.path.exists', return_value=False):
        with pytest.raises(SystemExit) as ex_info:
            projects_create(grdm_client)
        assert ex_info.value.code == f'Missing the template schema {grdm_client.template_schema_projects}'


def test_projects_create__template_file_not_exist(grdm_client):
    with mock.patch('os.path.exists', side_effect=[True, False]):
        with pytest.raises(SystemExit) as ex_info:
            projects_create(grdm_client)
        assert ex_info.value.code == f'Missing the template file'


@mock.patch('sys.exit')
@mock.patch('grdmcli.utils.read_json_file', return_value=projects)
def test_projects_create__verbose_false_check_schema_raise_error(mocker, grdm_client, capfd):
    err = 'check schema error'
    mocker.patch('os.path.exists', side_effect=[True, True])
    mocker.patch('grdmcli.utils.write_json_file')
    with mock.patch('grdmcli.utils.check_json_schema', side_effect=GrdmCliException(err)):
        with pytest.raises(GrdmCliException) as error_message:
            projects_create(grdm_client, verbose=False)
        lines = capfd.readouterr().out.split('\n')
        assert lines[2] == f'VALIDATE BY the template of projects: {grdm_client.template_schema_projects}'
        assert lines[3] == f'Exception {err}'
        assert lines[4] == f'USE the output result file: {grdm_client.output_result_file}'
        assert error_message.value.args[0] == err


@mock.patch('sys.exit')
def test_projects_create__verbose_true(mocker, grdm_client, capfd):
    _projects = {"projects": [projects['projects'][2]]}
    grdm_client.created_projects.append(fork_project_obj.data)
    mocker.patch('grdmcli.utils.check_json_schema')
    mocker.patch('os.path.exists', side_effect=[True, True])
    with mock.patch('grdmcli.utils.read_json_file', return_value=_projects):
        with mock.patch.object(grdm_client, '_create_or_load_project', return_value=fork_project_obj.data):
            with mock.patch('grdmcli.utils.write_json_file'):
                projects_create(grdm_client, verbose=True)
                lines = capfd.readouterr().out.split('\n')
                size = len(grdm_client.created_projects)
                assert lines[4] == f'Created projects. [{size}]'
                assert lines[5 + size] == f'USE the output result file: {grdm_client.output_result_file}'
                assert _projects == _projects


@mock.patch('sys.exit')
@mock.patch('grdmcli.utils.write_json_file')
def test_projects_create__case_create_or_load_project_none(mocker, grdm_client, capfd):
    _projects = {"projects": [projects['projects'][2]]}
    mocker.patch('grdmcli.utils.check_json_schema')
    mocker.patch('os.path.exists', side_effect=[True, True])
    with mock.patch('grdmcli.utils.read_json_file', return_value=_projects):
        with mock.patch.object(grdm_client, '_create_or_load_project',
                               return_value=test_create_or_load_project__case_load_project_none(grdm_client, capfd)):
            projects_create(grdm_client, verbose=False)
            lines = capfd.readouterr().out.split('\n')
            assert lines[4] == f'USE the output result file: {grdm_client.output_result_file}'
