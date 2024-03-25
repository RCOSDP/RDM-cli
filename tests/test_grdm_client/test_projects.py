import json
import logging
from types import SimpleNamespace
from unittest import mock

import pytest
import requests
import re

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
    projects_get,
    get_all_linked_node,
    convert_contributor_with_template_get_cli,
    call_api_user_nodes
)
from tests.factories import GRDMClientFactory
from tests.utils import *

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
get_cli_project = [
    {
        "id": "333",
        "type": "nodes",
        "attributes": {
            "fork": False,
            "title": "Project Example 0018",
            "description": "Lorem Ipsum has been",
            "category": "project",
            "tags": [
                "0018",
                "cli",
                "development",
                "required properties"
            ],
            "node_license": {
                "copyright_holders": [
                    "Copyright (c) 2024"
                ],
                "year": "2024"
            },
            "public": True
        },
        "relationships": {
            "license": {
                "data": {
                    "id": "1",
                    "type": "licenses"
                }
            },
            "children": {
                "links": {
                    "related": {
                        "href": "http://localhost:8000/v2/nodes/jbkzh/children/",
                        "meta": { }
                    }
                }
            }
        }
    },
    {
        "id": "1234",
        "type": "nodes",
        "attributes": {
            "fork": False,
            "title": "Project Example 0018",
            "description": "Lorem Ipsum has been",
            "category": "project",
            "tags": [
                "0018",
                "cli",
                "development",
                "required properties"
            ],
            "node_license": {
                "copyright_holders": [
                    "Copyright (c) 2024"
                ],
                "year": "2024"
            },
            "public": True
        },
        "relationships": {
            "license": {
                "data": {
                    "id": "1",
                    "type": "licenses"
                }
            },
            "children": {
                "links": {
                    "related": {
                        "href": "http://localhost:8000/v2/nodes/jbkzh/children/",
                        "meta": { }
                    }
                }
            },
            "parent": {
                "links": {
                    "related": {
                        "href": "http://localhost:8000/v2/nodes/jbkzh/",
                        "meta": {}
                    }
                },
                "data": {
                    "id": "333",
                    "type": "nodes"
                }
            }
        }
    },
    {
        "id": "6qrsy",
        "type": "nodes",
        "attributes": {
            "fork": False,
            "title": "Project Example 0018",
            "description": "Lorem Ipsum has been",
            "category": "project",
            "tags": [
                "0018",
                "cli",
                "development",
                "required properties"
            ],
            "node_license": {
                "copyright_holders": [
                    "Copyright (c) 2024"
                ],
                "year": "2024"
            },
            "public": True
        },
        "relationships": {
            "license": {
                "data": {
                    "id": "1",
                    "type": "licenses"
                }
            },
            "children": {
                "links": {
                    "related": {
                        "href": "http://localhost:8000/v2/nodes/jbkzh/children/",
                        "meta": { }
                    }
                }
            },
            "parent": {
                "links": {
                    "related": {
                        "href": "http://localhost:8000/v2/nodes/jbkzh/",
                        "meta": {}
                    }
                },
                "data": {
                    "id": "jbkzh",
                    "type": "nodes"
                }
            }
        }
    },
    {
        "id": "wh9my",
        "type": "nodes",
        "attributes": {
            "fork": False,
            "title": "Project Example 0018",
            "description": "L ever since the 1500s, when an unknown printer took a galley of type and scrambled it to make a type specimen book.",
            "category": "project",
            "tags": [
                "0018",
                "cli",
                "development",
                "required properties"
            ],
            "node_license": {
                "copyright_holders": [
                    "Copyright (c) 2024"
                ],
                "year": "2024"
            },
            "public": True
        },
        "relationships": {
            "license": {
                "data": {
                    "id": "1",
                    "type": "licenses"
                }
            },
            "children": {
                "links": {
                    "related": {
                        "href": "http://localhost:8000/v2/nodes/wh9my/children/",
                        "meta": {}
                    }
                }
            },
            "contributors": {
                "links": {
                    "related": {
                        "href": "http://localhost:8000/v2/nodes/wh9my/contributors/",
                        "meta": {}
                    }
                }
            },
            "parent": {
                "links": {
                    "related": {
                        "href": "http://localhost:8000/v2/nodes/jbkzh/",
                        "meta": {}
                    }
                },
                "data": {
                    "id": "6qrsy",
                    "type": "nodes"
                }
            }
        }
    },
    {
        "id": "jbkzh",
        "type": "nodes",
        "attributes": {
            "fork": False,
            "title": "Project Example 0018",
            "description": "Lorem Ipsum has been",
            "category": "project",
            "tags": [
                "0018",
                "cli",
                "development",
                "required properties"
            ],
            "node_license": {
                "copyright_holders": [
                    "Copyright (c) 2024"
                ],
                "year": "2024"
            },
            "public": True
        },
        "relationships": {
            "license": {
                "data": {
                    "id": "1",
                    "type": "licenses"
                }
            },
            "children": {
                "links": {
                    "related": {
                        "href": "http://localhost:8000/v2/nodes/jbkzh/children/",
                        "meta": { }
                    }
                }
            },
        }
    },
    {
        "id": "uhnj5",
        "type": "nodes",
        "attributes": {
            "fork": True,
            "title": "Project Example 0018",
            "description": "Lorem Ipsum has been",
            "category": "project",
            "tags": [
                "0018",
                "cli",
                "development",
                "required properties"
            ],
            "node_license": {
                "copyright_holders": [
                    "Copyright (c) 2024"
                ],
                "year": "2024"
            },
            "public": True
        },
        "relationships": {
            "forked_from": {
                "links": {
                    "related": {
                        "href": "http://localhost:8000/v2/nodes/qhbgu/",
                        "meta": {}
                    }
                },
                "data": {
                    "id": "qhbgu",
                    "type": "nodes"
                }
            },
            "license": {
                "data": {
                    "id": "1",
                    "type": "licenses"
                }
            },
            "children": {
                "links": {
                    "related": {
                        "href": "http://localhost:8000/v2/nodes/jbkzh/children/",
                        "meta": { }
                    }
                }
            },
            "parent": {
                "links": {
                    "related": {
                        "href": "http://localhost:8000/v2/nodes/jbkzh/",
                        "meta": {}
                    }
                },
                "data": {
                    "id": "wh9my",
                    "type": "nodes"
                }
            }
        }
    }
]
get_cli_user_node = {
    "data": get_cli_project,
    "links": {
        "last": "http://localhost:8000/v2/users/qv42t/nodes/?page=7",
        "next": "http://localhost:8000/v2/users/qv42t/nodes/?page=2",
        "meta": {
            "total": 4,
            "per_page": 2
        }
    }
}
get_cli_licenses_dict = {
    "data": [
        {
            "links": {
                "self": "https://api.osf.io/v2/licenses/563c1cf88c5e4a3877f9e968/"
            },
            "attributes": {
                "text": "Copyright (c) {{year}}, {{copyrightHolders}}All rights reserved.The full descriptive text of the License.",
                "required_fields": [
                    "year",
                    "copyrightHolders"
                ],
                "name": "BSD 3-Clause \"Simplified\" License"
            },
            "type": "licenses",
            "id": "1"
        }
    ],
    "links": {
        "first": "",
        "last": "null",
        "prev": "",
        "next": "null",
        "meta": {
            "total": 1,
            "per_page": 1
        }
    }
}
get_cli_linked_nodes = {
    "jbkzh": ['1', '2', '3'],
    "wh9my": ['1', '2', '3'],
    "uhnj5": ['1', '2', '3'],
    "6qrsy": ['1', '2', '3'],
}

content_obj = json.loads(_content, object_hook=lambda d: SimpleNamespace(**d))
fork_project_obj = json.loads(fork_project_str, object_hook=lambda d: SimpleNamespace(**d))
new_project_obj = json.loads(new_project_str, object_hook=lambda d: SimpleNamespace(**d))
link_project_obj = json.loads(link_project_str, object_hook=lambda d: SimpleNamespace(**d))
projects_obj = json.loads(json.dumps(projects), object_hook=lambda d: SimpleNamespace(**d))
get_cli_licenses_object = json.loads(json.dumps(get_cli_licenses_dict), object_hook=lambda d: SimpleNamespace(**d))
get_cli_project_obj = json.loads(json.dumps(get_cli_project), object_hook=lambda d: SimpleNamespace(**d))

@pytest.fixture
def grdm_client():
    return GRDMClientFactory()


@pytest.fixture(autouse=True)
def set_log_level(caplog):
    caplog.clear()
    caplog.set_level(logging.DEBUG)


def test_get_template_schema_projects__normal():
    actual = _get_template_schema_projects(grdm_client)
    assert type(actual) is str
    assert actual.__contains__('projects_create_schema.json')


def test_fake_project_content_data__verbose_false(caplog):
    actual = _fake_project_content_data(grdm_client, 'node01', verbose=False)
    assert actual == _content
    assert len(caplog.records) == 0


def test_fake_project_content_data__verbose_true(caplog):
    actual = _fake_project_content_data(grdm_client, 'node01', verbose=True)
    assert actual == _content
    assert len(caplog.records) == 1
    assert caplog.records[0].levelname == debug_level_log
    assert caplog.records[0].message == f'Prepared project data: {_content}'


def test_prepare_project_data__all_new_not_license(grdm_client):
    _project = projects.get('projects')[0]
    actual = _prepare_project_data(grdm_client, _project, verbose=False)
    assert actual['data']['type'] == 'nodes'
    assert actual['data']['attributes']['tags'] == _project['tags']
    assert actual['data']['attributes']['public'] == _project['public']
    assert actual['data']['relationships'] == {}


def test_prepare_project_data__new_has_license_verbose_true(grdm_client, caplog):
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
    assert len(caplog.records) == 1
    assert caplog.records[0].levelname == debug_level_log
    assert caplog.records[0].message.__contains__('Prepared project data:')


def test_prepare_project_data__fork_project(grdm_client, caplog):
    _project = projects['projects'][3]
    actual = _prepare_project_data(grdm_client, _project, verbose=True)
    assert actual['data']['type'] == 'nodes'
    assert actual['data']['attributes']['tags'] == _project['tags']
    assert actual['data']['attributes']['public'] == _project['public']
    assert actual['data']['relationships'] == {}


def test_load_project__is_fake_and_verbose_true(caplog, grdm_client):
    with mock.patch.object(grdm_client, '_fake_project_content_data', return_value=_content):
        actual1, actual2 = _load_project(grdm_client, pk='node01', verbose=True)
    _faked_or_loaded = '[faked]'
    assert caplog.records[0].message == f'Retrieve project nodes/node01/ {_faked_or_loaded}'
    assert caplog.records[1].message == f'Loaded project nodes/node01/'
    assert len(caplog.records) == 3
    assert actual1 == content_obj.data
    assert type(actual2) is dict


def test_load_project__is_fake_false_and_request_error_and_ignore_error_false_sys_exit(grdm_client, caplog):
    error_message = 'error'
    with mock.patch.object(grdm_client, '_request', return_value=(None, error_message)):
        with pytest.raises(SystemExit) as ex_info:
            _load_project(grdm_client, pk='node01', is_fake=False, ignore_error=False)
        assert ex_info.value.code == error_message
        _faked_or_loaded = f'[loaded]'
        assert len(caplog.records) == 2
        assert caplog.records[0].levelname == info_level_log
        assert caplog.records[0].message == f'Retrieve project nodes/node01/ {_faked_or_loaded}'
        assert caplog.records[1].levelname == warning_level_log
        assert caplog.records[1].message == f'{error_message}'


def test_load_project__is_fake_false_and_request_error_and_ignore_error_true(grdm_client, caplog):
    error_message = 'error'
    with mock.patch.object(grdm_client, '_request', return_value=(None, error_message)):
        actual1, actual2 = _load_project(grdm_client, pk='node01', is_fake=False, ignore_error=True)
    _faked_or_loaded = f'[loaded]'
    assert caplog.records[0].levelname == info_level_log
    assert caplog.records[0].message == f'Retrieve project nodes/node01/ {_faked_or_loaded}'
    assert caplog.records[1].levelname == warning_level_log
    assert caplog.records[1].message == f'{error_message}'
    assert len(caplog.records) == 2
    assert actual1 == actual2 is None


def test_load_project__is_fake_false_verbose_false(caplog, grdm_client):
    resp = requests.Response()
    resp._content = new_project_str
    with mock.patch.object(grdm_client, '_request', return_value=(resp, None)):
        actual1, actual2 = _load_project(grdm_client, pk='node01', is_fake=False, verbose=False)
    _faked_or_loaded = f'[loaded]'
    project_id = json.loads(new_project_str)['data']['id']
    assert len(caplog.records) == 2
    assert caplog.records[0].levelname == info_level_log
    assert caplog.records[0].message == f'Retrieve project nodes/node01/ {_faked_or_loaded}'
    assert actual1 == new_project_obj.data
    assert actual2 == json.loads(new_project_str)['data']
    assert caplog.records[1].levelname == info_level_log
    assert caplog.records[1].message == f'Loaded project nodes/{project_id}/'


def test_fork_project__request_error_and_ignore_error_false_sys_exit(grdm_client, caplog):
    _node_project = projects['projects'][3]
    error_message = 'error'
    with mock.patch.object(grdm_client, '_request', return_value=(None, error_message)):
        with pytest.raises(SystemExit) as ex_info:
            _fork_project(grdm_client, _node_project, ignore_error=False, verbose=False)
        assert ex_info.value.code == error_message
        pk = _node_project['fork_id']
        assert caplog.records[0].levelname == info_level_log
        assert caplog.records[0].message == f'Fork a project from nodes/{pk}/'
        assert caplog.records[1].levelname == warning_level_log
        assert 'Ignore the following attributes' in caplog.records[1].message
        assert caplog.records[2].levelname == warning_level_log
        assert caplog.records[2].message == f'{error_message}'
        assert len(caplog.records) == 3


def test_fork_project__request_error_and_ignore_error_true(grdm_client, caplog):
    error_message = 'error'
    _node_project = projects['projects'][3]
    with mock.patch.object(grdm_client, '_request', return_value=(None, error_message)):
        actual1, actual2 = _fork_project(grdm_client, _node_project, ignore_error=True, verbose=False)
    pk = _node_project['fork_id']
    assert actual1 == actual2 is None
    assert caplog.records[0].levelname == info_level_log
    assert caplog.records[0].message == f'Fork a project from nodes/{pk}/'
    assert caplog.records[1].levelname == warning_level_log
    assert 'Ignore the following attributes' in caplog.records[1].message
    assert caplog.records[2].levelname == warning_level_log
    assert caplog.records[2].message == f'{error_message}'
    assert len(caplog.records) == 3


def test_fork_project__verbose_true(grdm_client, caplog):
    resp = requests.Response()
    resp._content = fork_project_str
    _node_project = projects['projects'][3]
    with mock.patch.object(grdm_client, '_request', return_value=(resp, None)):
        actual1, actual2 = _fork_project(grdm_client, _node_project, verbose=True)
    pk = _node_project['fork_id']
    assert actual1 == fork_project_obj.data
    assert actual2 == json.loads(fork_project_str)['data']
    assert caplog.records[0].levelname == info_level_log
    assert caplog.records[0].message == f'Fork a project from nodes/{pk}/'
    assert caplog.records[1].levelname == warning_level_log
    assert 'Ignore the following attributes' in caplog.records[1].message
    assert caplog.records[2].levelname == info_level_log
    assert caplog.records[2].message == f'Forked project nodes/{fork_project_obj.data.id}/'
    assert caplog.records[3].levelname == debug_level_log
    assert len(caplog.records) == 4


def test_create_project__request_error_and_ignore_error_false_sys_exit(grdm_client, caplog):
    _node_project = projects['projects'][0]
    error_message = 'error'
    with mock.patch('tests.factories.GRDMClientFactory._prepare_project_data', return_value=True):
        with mock.patch.object(grdm_client, '_request', return_value=(None, error_message)):
            with pytest.raises(SystemExit) as ex_info:
                _create_project(grdm_client, _node_project, ignore_error=False, verbose=False)
            assert ex_info.value.code == error_message
            assert caplog.records[0].levelname == info_level_log
            assert caplog.records[0].message == f'Create new project'
            assert caplog.records[1].levelname == warning_level_log
            assert caplog.records[1].message == f'{error_message}'
            assert len(caplog.records) == 2


def test_create_project__request_error_and_ignore_error_true(grdm_client, caplog):
    error_message = 'error'
    _node_project = projects['projects'][0]
    with mock.patch('tests.factories.GRDMClientFactory._prepare_project_data', return_value=True):
        with mock.patch.object(grdm_client, '_request', return_value=(None, error_message)):
            actual1, actual2 = _create_project(grdm_client, _node_project, ignore_error=True, verbose=False)
        assert actual1 == actual2 is None
        assert caplog.records[0].levelname == info_level_log
        assert caplog.records[0].message == f'Create new project'
        assert caplog.records[1].levelname == warning_level_log
        assert caplog.records[1].message == f'{error_message}'
        assert len(caplog.records) == 2


def test_create_project__verbose_true(grdm_client, caplog):
    resp = requests.Response()
    resp._content = new_project_str
    _node_project = projects['projects'][0]
    project_id = json.loads(new_project_str)['data']['id']
    with mock.patch('tests.factories.GRDMClientFactory._prepare_project_data', return_value=True):
        with mock.patch.object(grdm_client, '_request', return_value=(resp, None)):
            actual1, actual2 = _create_project(grdm_client, _node_project, verbose=True)
        assert actual1 == new_project_obj.data
        assert actual2 == json.loads(new_project_str)['data']
        assert caplog.records[0].levelname == info_level_log
        assert caplog.records[0].message == f'Create new project'
        assert caplog.records[1].levelname == info_level_log
        assert caplog.records[1].message == f'Created project \'{project_id}\''
        assert caplog.records[2].levelname == debug_level_log
        assert len(caplog.records) == 3


def test_create_project__verbose_false(grdm_client, caplog):
    resp = requests.Response()
    resp._content = new_project_str
    _node_project = projects['projects'][0]
    project_id = json.loads(new_project_str)['data']['id']
    with mock.patch('tests.factories.GRDMClientFactory._prepare_project_data', return_value=True):
        with mock.patch.object(grdm_client, '_request', return_value=(resp, None)):
            actual1, actual2 = _create_project(grdm_client, _node_project, verbose=False)
        assert actual1 == new_project_obj.data
        assert actual2 == json.loads(new_project_str)['data']
        assert caplog.records[0].levelname == info_level_log
        assert caplog.records[0].message == f'Create new project'
        assert caplog.records[1].levelname == info_level_log
        assert caplog.records[1].message == f'Created project \'{project_id}\''
        assert len(caplog.records) == 2


def test_link_project_to_project__request_error_and_ignore_error_false_sys_exit(grdm_client, caplog):
    _project_id = projects['projects'][2]['id']
    error_message = 'error'
    with mock.patch.object(grdm_client, '_request', return_value=(None, error_message)):
        with pytest.raises(SystemExit) as ex_info:
            _link_project_to_project(grdm_client, _project_id, 'abcd6', ignore_error=False, verbose=False)
        assert ex_info.value.code == error_message
        assert caplog.records[0].levelname == info_level_log
        assert caplog.records[0].message == f'Create a link to nodes/{_project_id}/'
        assert caplog.records[1].levelname == warning_level_log
        assert caplog.records[1].message == f'{error_message}'
        assert len(caplog.records) == 2


def test_link_project_to_project__request_error_and_ignore_error_true(grdm_client, caplog):
    error_message = 'error'
    _project_id = projects['projects'][2]['id']
    with mock.patch.object(grdm_client, '_request', return_value=(None, error_message)):
        actual1, actual2 = _link_project_to_project(grdm_client, _project_id, 'abcd6', ignore_error=True)
    assert actual1 == actual2 is None
    assert caplog.records[0].levelname == info_level_log
    assert caplog.records[0].message == f'Create a link to nodes/{_project_id}/'
    assert caplog.records[1].levelname == warning_level_log
    assert caplog.records[1].message == f'{error_message}'
    assert len(caplog.records) == 2


def test_link_project_to_project__verbose_true(grdm_client, caplog):
    resp = requests.Response()
    resp._content = link_project_str
    _project_id = projects['projects'][2]['id']
    project_id = json.loads(link_project_str)['data']['id']
    with mock.patch.object(grdm_client, '_request', return_value=(resp, None)):
        actual1, actual2 = _link_project_to_project(grdm_client, _project_id, '74pnd', verbose=True)
    project_link = link_project_obj.data.embeds.target_node.data
    assert actual1 == project_link
    assert actual2 == json.loads(link_project_str)['data']
    assert caplog.records[0].levelname == info_level_log
    assert caplog.records[0].message == f'Create a link to nodes/{_project_id}/'
    assert caplog.records[1].levelname == info_level_log
    assert caplog.records[1].message == f'Created Node Links \'{project_id}\''
    assert caplog.records[2].levelname == debug_level_log
    assert caplog.records[2].message == f'\'{link_project_obj.data.id}\' - [{project_link.type}]'
    assert len(caplog.records) == 4


def test_link_project_to_project__verbose_false(grdm_client, caplog):
    resp = requests.Response()
    resp._content = link_project_str
    _project_id = projects['projects'][2]['id']
    with mock.patch.object(grdm_client, '_request', return_value=(resp, None)):
        actual1, actual2 = _link_project_to_project(grdm_client, _project_id, '74pnd', verbose=False)
    project_link = link_project_obj.data.embeds.target_node.data
    assert actual1 == project_link
    assert actual2 == json.loads(link_project_str)['data']
    assert caplog.records[0].levelname == info_level_log
    assert caplog.records[0].message == f'Create a link to nodes/{_project_id}/'
    assert len(caplog.records) == 2


def test_link_project_to_project__target_node_error_verbose_true(grdm_client, caplog):
    _project_link_error = json.loads(link_project_str)
    _project_link_error['data']['embeds']['target_node'] = {"errors": [{"detail": "error link"}]}
    resp = requests.Response()
    resp._content = json.dumps(_project_link_error)
    _project_id = projects['projects'][2]['id']
    with mock.patch.object(grdm_client, '_request', return_value=(resp, None)):
        actual1, actual2 = _link_project_to_project(grdm_client, _project_id, '74pnd', verbose=True)
    assert actual1 is None
    assert actual2 == _project_link_error['data']
    assert caplog.records[0].levelname == info_level_log
    assert caplog.records[0].message == f'Create a link to nodes/{_project_id}/'
    assert caplog.records[1].levelname == warning_level_log
    assert caplog.records[1].message == f'When link to 74pnd: error link'
    assert len(caplog.records) == 2


def test_add_project_pointers__project_link_is_none(grdm_client, caplog):
    _project = projects_obj.projects[2]
    _project_links = ['74pnd', 'abcd7']
    project_link = link_project_obj.data.embeds.target_node.data
    with mock.patch.object(grdm_client, '_link_project_to_project', side_effect=[(project_link, None), (None, None)]):
        _add_project_pointers(grdm_client, _project_links, _project)
    assert _project_links == ['74pnd', None]
    assert caplog.records[0].levelname == info_level_log
    assert caplog.records[0].message == f'JSONPOINTER ./project_links/0/'
    assert caplog.records[1].levelname == info_level_log
    assert caplog.records[1].message == f'JSONPOINTER ./project_links/1/'
    assert len(caplog.records) == 2


def test_create_or_load_project__case_load_project_none(grdm_client, caplog):
    _projects = (projects.get('projects', [])).copy()
    _id = _projects[2].get('id')
    with mock.patch.object(grdm_client, '_load_project', return_value=(None, None)):
        actual = _create_or_load_project(grdm_client, _projects, 2)
    assert caplog.records[0].levelname == info_level_log
    assert caplog.records[0].message == f'JSONPOINTER /projects/2/id == {_id}'
    assert len(caplog.records) == 1
    assert actual == _projects[2] is None


def test_create_or_load_project__case_load_project(caplog, grdm_client):
    _projects = projects.get('projects', [])
    _id = _projects[2].get('id')
    with mock.patch.object(grdm_client, '_load_project', return_value=(link_project_obj.data, None)):
        actual = _create_or_load_project(grdm_client, _projects, 2)
    assert len(caplog.records) == 1
    assert caplog.records[0].levelname == info_level_log
    assert caplog.records[0].message == f'JSONPOINTER /projects/2/id == {_id}'
    assert actual is link_project_obj.data
    assert _projects[2]['id'] == link_project_obj.data.id
    assert _projects[2]['type'] == link_project_obj.data.type


def test_create_or_load_project__case_create_project_none(caplog, grdm_client):
    _projects = (projects.get('projects', [])).copy()
    with mock.patch.object(grdm_client, '_create_project', return_value=(None, None)):
        actual = _create_or_load_project(grdm_client, _projects, 0)
    assert len(caplog.records) == 1
    assert caplog.records[0].levelname == info_level_log
    assert caplog.records[0].message == f'JSONPOINTER /projects/0/'
    assert actual == _projects[0] is None


def test_create_or_load_project__case_create_project(caplog, grdm_client):
    _projects = projects.get('projects', [])
    with mock.patch.object(grdm_client, '_create_project', return_value=(new_project_obj.data, None)):
        actual = _create_or_load_project(grdm_client, _projects, 0)
    assert len(caplog.records) == 1
    assert caplog.records[0].levelname == info_level_log
    assert caplog.records[0].message == f'JSONPOINTER /projects/0/'
    assert actual is new_project_obj.data
    assert _projects[0]['id'] == new_project_obj.data.id
    assert _projects[0]['type'] == new_project_obj.data.type


def test_create_or_load_project__case_fork_project_none(caplog, grdm_client):
    _projects = (projects.get('projects', [])).copy()
    _fork_id = _projects[3].get('fork_id')
    with mock.patch.object(grdm_client, '_fork_project', return_value=(None, None)):
        actual = _create_or_load_project(grdm_client, _projects, 3)
    assert len(caplog.records) == 1
    assert caplog.records[0].levelname == info_level_log
    assert caplog.records[0].message == f'JSONPOINTER /projects/3/fork_id == {_fork_id}'
    assert actual == _projects[3] is None


def test_create_or_load_project__case_fork_project(caplog, grdm_client):
    _projects = projects.get('projects', [])
    _fork_id = _projects[3].get('fork_id')
    with mock.patch.object(grdm_client, '_fork_project', return_value=(fork_project_obj.data, None)):
        actual = _create_or_load_project(grdm_client, _projects, 3)
    assert len(caplog.records) == 1
    assert caplog.records[0].levelname == info_level_log
    assert caplog.records[0].message == f'JSONPOINTER /projects/3/fork_id == {_fork_id}'
    assert actual is fork_project_obj.data
    assert _projects[3]['id'] == fork_project_obj.data.id
    assert _projects[3]['type'] == fork_project_obj.data.type


def test_add_project_components__children_exist_id_ignored(grdm_client, caplog):
    _children = projects['projects'][0]['children']
    children = [_children[1]]
    _add_project_components(grdm_client, children, link_project_obj.data)
    assert len(caplog.records) == 1
    assert caplog.records[0].levelname == info_level_log
    assert caplog.records[0].message == f'JSONPOINTER ./children/0/ ignored'
    assert children[0] is None


def test_add_project_components__add_components_is_none(grdm_client, caplog):
    _children = (projects['projects'][2]['children']).copy()
    children = [_children[0]]
    with mock.patch.object(grdm_client, '_projects_add_component', return_value=(None, None)):
        _add_project_components(grdm_client, children, link_project_obj.data)
    assert len(caplog.records) == 1
    assert caplog.records[0].levelname == info_level_log
    assert caplog.records[0].message == f'JSONPOINTER ./children/0/'
    assert children[0] is None


def test_add_project_components__add_components_success(grdm_client, caplog):
    _project = link_project_obj.data
    _children = projects['projects'][2]['children']
    children = [_children[0]]
    component = new_project_obj.data
    with mock.patch.object(grdm_client, '_projects_add_component', return_value=(component, None)):
        _add_project_components(grdm_client, children, _project)
    assert len(caplog.records) == 1
    assert caplog.records[0].levelname == info_level_log
    assert caplog.records[0].message == f'JSONPOINTER ./children/0/'
    assert children[0]['id'] == component.id
    assert children[0]['type'] == component.type


def test_projects_add_component__request_error_and_ignore_error_false_sys_exit(grdm_client, caplog):
    _project = projects['projects'][2]
    error_message = 'error'
    parent_id = 'nid11'
    with mock.patch('tests.factories.GRDMClientFactory._prepare_project_data', return_value=True):
        with mock.patch.object(grdm_client, '_request', return_value=(None, error_message)):
            with pytest.raises(SystemExit) as ex_info:
                _projects_add_component(grdm_client, parent_id, _project, ignore_error=False)
            assert ex_info.value.code == error_message
            assert len(caplog.records) == 2
            assert caplog.records[0].levelname == info_level_log
            assert caplog.records[0].message == f'Create new component to nodes/{parent_id}/'
            assert caplog.records[1].levelname == warning_level_log
            assert caplog.records[1].message == f'{error_message}'


def test_projects_add_component__request_error_and_ignore_error_true(grdm_client, caplog):
    error_message = 'error'
    _project = projects['projects'][2]
    parent_id = 'nid11'
    with mock.patch('tests.factories.GRDMClientFactory._prepare_project_data', return_value=True):
        with mock.patch.object(grdm_client, '_request', return_value=(None, error_message)):
            actual1, actual2 = _projects_add_component(grdm_client, parent_id, _project, ignore_error=True)
        assert actual1 == actual2 is None
        assert caplog.records[0].levelname == info_level_log
        assert caplog.records[0].message == f'Create new component to nodes/{parent_id}/'
        assert caplog.records[1].levelname == warning_level_log
        assert caplog.records[1].message == f'{error_message}'
        assert len(caplog.records) == 2


def test_projects_add_component__verbose_true(grdm_client, caplog):
    resp = requests.Response()
    resp._content = new_project_str
    _project = projects['projects'][2]
    parent_id = 'nid11'
    _project['project_links'] = ['nid92', None]
    _project['children'] = [_project['children'][0], None]
    project_id = json.loads(new_project_str)['data']['id']
    with mock.patch('tests.factories.GRDMClientFactory._prepare_project_data', return_value=True):
        with mock.patch.object(grdm_client, '_request', return_value=(resp, None)):
            actual1, actual2 = _projects_add_component(grdm_client, parent_id, _project, verbose=True)
    assert _project['project_links'] == ['nid92']
    assert _project['children'] == [_project['children'][0]]
    assert actual1 == new_project_obj.data
    assert actual2 == json.loads(new_project_str)['data']
    assert caplog.records[0].levelname == info_level_log
    assert caplog.records[0].message == f'Create new component to nodes/{parent_id}/'
    assert caplog.records[1].levelname == info_level_log
    assert caplog.records[1].message == f'Created component \'{project_id}\''
    assert caplog.records[2].levelname == debug_level_log
    assert len(caplog.records) == 3


@mock.patch('os.path.exists', return_value=False)
def test_projects_create__schema_not_exist(grdm_client, caplog):
    with pytest.raises(SystemExit) as ex_info:
        projects_create(grdm_client)
    assert caplog.records[0].levelname == info_level_log
    assert caplog.records[0].message == 'Check config and authenticate by token'
    assert len(caplog.records) == 1
    assert ex_info.value.code == f'Missing the template schema {grdm_client.template_schema_projects}'


@mock.patch('os.path.exists', side_effect=[True, False])
def test_projects_create__template_file_not_exist(grdm_client, caplog):
    with pytest.raises(SystemExit) as ex_info:
        projects_create(grdm_client)
    assert caplog.records[0].levelname == info_level_log
    assert caplog.records[0].message == 'Check config and authenticate by token'
    assert len(caplog.records) == 1
    assert ex_info.value.code == f'Missing the template file'


@mock.patch('grdmcli.utils.read_json_file', return_value=projects)
@mock.patch('os.path.exists', side_effect=[True, True])
def test_projects_create__verbose_false_check_schema_raise_error(mocker, grdm_client, caplog):
    err = 'check schema error'
    with mock.patch('grdmcli.utils.check_json_schema', side_effect=GrdmCliException(err)):
        with pytest.raises(SystemExit) as ex_info:
            projects_create(grdm_client)
        assert len(caplog.records) == 3
        assert caplog.records[0].levelname == info_level_log
        assert caplog.records[0].message == 'Check config and authenticate by token'
        assert caplog.records[1].levelname == info_level_log
        assert caplog.records[1].message == f'Use the template of projects: {grdm_client.template}'
        assert caplog.records[2].levelname == info_level_log
        assert caplog.records[2].message == f'Validate by the template of projects: {grdm_client.template_schema_projects}'
        assert str(ex_info.value.args[0]) == err


@mock.patch('grdmcli.utils.read_json_file', return_value=projects)
@mock.patch('os.path.exists', side_effect=[True, True])
def test_projects_create__verbose_true(mocker, grdm_client, caplog):
    _projects = {"projects": [projects['projects'][2]]}
    grdm_client.created_projects.append(fork_project_obj.data)
    mocker.patch('grdmcli.utils.check_json_schema')
    with mock.patch.object(grdm_client, '_create_or_load_project', return_value=fork_project_obj.data):
        with pytest.raises(SystemExit) as ex_info:
            projects_create(grdm_client)
        assert caplog.records[3].levelname == info_level_log
        assert caplog.records[3].message == 'Loop following the template of projects'
        assert caplog.records[4].message == 'The \'projects\' object is empty'
        assert _projects == _projects
        assert ex_info.value.args[0] == 0


@mock.patch('sys.exit')
@mock.patch('grdmcli.utils.write_json_file')
def test_projects_create__case_create_or_load_project_none(mocker, grdm_client, caplog):
    _projects = {"projects": [projects['projects'][2]]}
    mocker.patch('grdmcli.utils.check_json_schema')
    mocker.patch('os.path.exists', side_effect=[True, True])
    with mock.patch('grdmcli.utils.read_json_file', return_value=_projects):
        with mock.patch.object(grdm_client, '_create_or_load_project',
                               return_value=test_create_or_load_project__case_load_project_none(grdm_client, caplog)):
            projects_create(grdm_client)
        assert caplog.records[4].message == 'Loop following the template of projects'
        assert caplog.records[5].message == 'Project is not found'
        assert caplog.records[6].message == 'The \'projects\' object is empty'


# Get cli _request mocker
def mock_get_cli__request(url, params = {}):
    pattern_licenses = r'^licenses(?:/.+)?$'
    pattern_user_node = r'^users\/[^\/]+\/nodes(?:/.+)?$'
    pattern_linked_node = r'^nodes\/[^\/]+\/linked_nodes(?:/.+)?$'
    pattern_contributors = r'^nodes\/[^\/]+\/contributors(?:/.+)?$'
    logging.info(url)
    if re.match(pattern_licenses, url):
        return get_cli_licenses_dict
    elif re.match(pattern_user_node, url):
        return get_cli_project_obj
    elif re.match(pattern_linked_node, url):
        return {
            'data': [
                {
                    "id": "456"
                },
                {
                    "id": "123"
                },
            ],
            "links": {
                "meta": {
                    "total": 2,
                    "per_page": 10
                }
            }
        }
    elif re.match(pattern_contributors, url):
        return {
                "data": [
                    {
                        "id": "g3uzd-jdm2p",
                        "attributes": {
                            "index": 0,
                            "bibliographic": True,
                            "permission": "admin",
                            "unregistered_contributor": None
                        }
                    },
                    {
                        "id": "g3uzd-1234",
                        "attributes": {
                            "index": 0,
                            "bibliographic": True,
                            "permission": "admin",
                            "unregistered_contributor": None
                        }
                    },
                ]
            }


@mock.patch('grdmcli.utils.write_json_file')
@mock.patch('grdmcli.grdm_client.licenses._licenses')
def test_projects_get__case_input_project_id_less_than_spec_without_output_location(mocker, grdm_client):
    user_node_resp = requests.Response()
    user_node_resp._content = json.dumps(get_cli_user_node)
    with mock.patch('grdmcli.grdm_client.projects.call_api_user_nodes', side_effect=(user_node_resp, None)), \
        mock.patch.object(grdm_client, 'project_id', 'jbkzh'), \
        mock.patch.object(grdm_client, 'licenses', return_value=(get_cli_licenses_object.data)):
            projects_get(grdm_client)


@mock.patch('grdmcli.utils.write_json_file')
@mock.patch('grdmcli.grdm_client.licenses._licenses')
def test_projects_get__case_input_project_id_less_than_100_wrong_file_type(mocker, grdm_client):
    resp = requests.Response()
    resp._content = get_cli_project

    user_node_resp = requests.Response()
    user_node_resp._content = json.dumps(get_cli_user_node)
    with mock.patch('grdmcli.grdm_client.projects.call_api_user_nodes', side_effect=(user_node_resp, None)):
        with mock.patch.object(grdm_client, 'output_projects_file', './abc/test.txt'):
            with pytest.raises(SystemExit) as ex_info:
                projects_get(grdm_client)
            assert str(ex_info.value) == "The output file type is not valid"


@mock.patch('grdmcli.utils.write_json_file')
@mock.patch('grdmcli.grdm_client.licenses._licenses')
def test_projects_get__case_input_project_id_more_than_spec_without_output_location(mocker, grdm_client):
    resp = requests.Response()
    resp._content = get_cli_project

    user_node_resp = requests.Response()
    user_node_resp._content = json.dumps(get_cli_user_node)
    with mock.patch('grdmcli.constants.PAGE_SIZE_SERVER', new=1), \
        mock.patch('grdmcli.grdm_client.projects.call_api_user_nodes', side_effect=(user_node_resp, None)), \
        mock.patch('grdmcli.grdm_client.projects.get_all_linked_node', return_value=get_cli_linked_nodes), \
        mock.patch('grdmcli.grdm_client.projects.get_all_contributor'), \
        mock.patch.object(grdm_client, 'get_all_data_from_api', side_effect = mock_get_cli__request), \
        mock.patch.object(grdm_client, 'project_id', 'jbkzh wh9my 1234'), \
        mock.patch.object(grdm_client, 'licenses', get_cli_licenses_object.data):
            projects_get(grdm_client)


def test_get_all_linked_node(grdm_client):
    with mock.patch.object(grdm_client, 'get_all_data_from_api', return_value = []):
        get_all_linked_node(grdm_client, 'user/id/nodes')


def test_convert_contributor_with_template_get_cli(grdm_client):
    data = {
        'id': 123,
        'attributes': {
            'bibliographic': 'somedata',
        }
    }
    convert_contributor_with_template_get_cli(json.loads(json.dumps(data), object_hook=lambda d: SimpleNamespace(**d)))


def test_call_api_user_nodes_error(grdm_client):
    error_message = 'error_message'
    with mock.patch.object(grdm_client, '_request', return_value=(None, error_message)):
        with pytest.raises(SystemExit) as ex_info:
            call_api_user_nodes(grdm_client, 'GET', 'url')
        assert ex_info.value.code == error_message


def test_call_api_user_nodes_successful(grdm_client):
    resp = requests.Response()
    with mock.patch.object(grdm_client, '_request', return_value=(resp, None)):
        call_api_user_nodes(grdm_client, 'GET', 'url')