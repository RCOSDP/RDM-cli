import json
import logging
from unittest import mock

import pytest
import requests

from grdmcli.grdm_client.develop import _delete_project, projects_list
from tests.factories import GRDMClientFactory
from utils import *


@pytest.fixture(autouse=True)
def set_log_level(caplog):
    caplog.clear()
    caplog.set_level(logging.DEBUG)


@pytest.fixture
def grdm_client():
    return GRDMClientFactory()


def test_delete_project__send_request_error_and_ignore_error_false_sys_exit(caplog, grdm_client):
    _error_message = 'error'
    pk = 'ega24'
    with mock.patch.object(grdm_client, '_request', return_value=(None, _error_message)):
        with pytest.raises(SystemExit) as ex_info:
            _delete_project(grdm_client, pk, ignore_error=False)
        assert ex_info.value.code == _error_message
        assert len(caplog.records) == 2
        assert caplog.records[0].levelname == info_level_log
        assert caplog.records[0].message == f'Remove project node/\'{pk}\'/'
        assert caplog.records[1].levelname == warning_level_log
        assert caplog.records[1].message == f'{_error_message}'


def test_delete_project__send_request_error_and_ignore_error_true_return_false(caplog, grdm_client):
    _error_message = 'error'
    pk = 'ega24'
    with mock.patch.object(grdm_client, '_request', return_value=(None, _error_message)):
        actual = _delete_project(grdm_client, pk, ignore_error=True)
    assert not actual
    assert len(caplog.records) == 2
    assert caplog.records[0].levelname == info_level_log
    assert caplog.records[0].message == f'Remove project node/\'{pk}\'/'
    assert caplog.records[1].levelname == warning_level_log
    assert caplog.records[1].message == f'{_error_message}'


def test_delete_project__send_request_success_and_verbose_false(caplog, grdm_client):
    pk = 'ega24'
    resp = requests.Response()
    resp.status_code = 204
    with mock.patch.object(grdm_client, '_request', return_value=(resp, None)):
        _delete_project(grdm_client, pk, verbose=False)
    assert len(caplog.records) == 1
    assert caplog.records[0].levelname == info_level_log
    assert caplog.records[0].message == f'Remove project node/\'{pk}\'/'


def test_delete_project__send_request_success_and_verbose_true(caplog, grdm_client):
    pk = 'ega24'
    resp = requests.Response()
    resp.status_code = 204
    with mock.patch.object(grdm_client, '_request', return_value=(resp, None)):
        _delete_project(grdm_client, pk, verbose=True)
    assert len(caplog.records) == 2
    assert caplog.records[0].levelname == info_level_log
    assert caplog.records[0].message == f'Remove project node/\'{pk}\'/'
    assert caplog.records[1].levelname == debug_level_log
    assert caplog.records[1].message == f'Deleted project: node/\'{pk}\'/'


@mock.patch('grdmcli.constants.DEBUG', False)
def test_projects_list__send_request_error_and_ignore_error_false_sys_exit(grdm_client, caplog):
    _error_message = 'error'
    with mock.patch.object(grdm_client, '_request', return_value=(None, _error_message)):
        with pytest.raises(SystemExit) as ex_info:
            projects_list(grdm_client, ignore_error=False)
        assert ex_info.value.args[0] == _error_message
        assert len(caplog.records) == 3
        assert caplog.records[0].levelname == info_level_log
        assert caplog.records[0].message == f'Check config and authenticate by token'
        assert caplog.records[1].levelname == info_level_log
        assert caplog.records[1].message == f'Get list of projects'
        assert caplog.records[2].levelname == warning_level_log
        assert caplog.records[2].message == f'{_error_message}'


@mock.patch('grdmcli.constants.DEBUG', False)
def test_projects_list__send_request_error_and_ignore_error_true__return_none(grdm_client, caplog):
    _error_message = 'error'
    with mock.patch.object(grdm_client, '_request', return_value=(None, _error_message)):
        actual1, actual2 = projects_list(grdm_client, ignore_error=True)
    assert actual1 == actual2 is None
    assert len(caplog.records) == 3
    assert caplog.records[0].levelname == info_level_log
    assert caplog.records[0].message == f'Check config and authenticate by token'
    assert caplog.records[1].levelname == info_level_log
    assert caplog.records[1].message == f'Get list of projects'
    assert caplog.records[2].levelname == warning_level_log
    assert caplog.records[2].message == f'{_error_message}'


nodes_str = '''{
    "data": [
        {
            "id": "qhrc6",
            "type": "nodes",
            "attributes": {
                "title": "Project Example Monkey24",
                "description": "Monkey24",
                "category": "project",
                "custom_citation": null,
                "date_created": "2023-04-25T11:11:50.727814",
                "date_modified": "2023-04-25T11:12:09.128967",
                "registration": false,
                "preprint": false,
                "fork": false,
                "collection": false,
                "tags": [
                    "cli",
                    "development",
                    "example"
                ],
                "access_requests_enabled": true,
                "node_license": null,
                "current_user_can_comment": true,
                "current_user_permissions": [
                    "admin",
                    "write",
                    "read"
                ],
                "current_user_is_contributor": true,
                "current_user_is_contributor_or_group_member": true,
                "wiki_enabled": true,
                "public": false,
                "quota_rate": 2.7263e-07,
                "quota_threshold": 0.9,
                "subjects": []
            },
            "relationships": {
                "creator": {
                    "links": {
                        "related": {
                            "href": "http://localhost:8000/v2/users/qm73w/",
                            "meta": {}
                        }
                    },
                    "data": {
                        "id": "qm73w",
                        "type": "users"
                    }
                },
                "children": {
                    "links": {
                        "related": {
                            "href": "http://localhost:8000/v2/nodes/qhrc6/children/",
                            "meta": {}
                        }
                    }
                },
                "comments": {
                    "links": {
                        "related": {
                            "href": "http://localhost:8000/v2/nodes/qhrc6/comments/?filter%5Btarget%5D=qhrc6",
                            "meta": {}
                        }
                    }
                },
                "contributors": {
                    "links": {
                        "related": {
                            "href": "http://localhost:8000/v2/nodes/qhrc6/contributors/",
                            "meta": {}
                        }
                    }
                },
                "bibliographic_contributors": {
                    "links": {
                        "related": {
                            "href": "http://localhost:8000/v2/nodes/qhrc6/bibliographic_contributors/",
                            "meta": {}
                        }
                    }
                },
                "implicit_contributors": {
                    "links": {
                        "related": {
                            "href": "http://localhost:8000/v2/nodes/qhrc6/implicit_contributors/",
                            "meta": {}
                        }
                    }
                },
                "files": {
                    "links": {
                        "related": {
                            "href": "http://localhost:8000/v2/nodes/qhrc6/files/",
                            "meta": {}
                        }
                    }
                },
                "addons": {
                    "links": {
                        "related": {
                            "href": "http://localhost:8000/v2/nodes/qhrc6/addons/",
                            "meta": {}
                        }
                    }
                },
                "settings": {
                    "links": {
                        "related": {
                            "href": "http://localhost:8000/v2/nodes/qhrc6/settings/",
                            "meta": {}
                        }
                    },
                    "data": {
                        "id": "qhrc6",
                        "type": "nodes"
                    }
                },
                "wikis": {
                    "links": {
                        "related": {
                            "href": "http://localhost:8000/v2/nodes/qhrc6/wikis/",
                            "meta": {}
                        }
                    }
                },
                "forks": {
                    "links": {
                        "related": {
                            "href": "http://localhost:8000/v2/nodes/qhrc6/forks/",
                            "meta": {}
                        }
                    }
                },
                "groups": {
                    "links": {
                        "related": {
                            "href": "http://localhost:8000/v2/nodes/qhrc6/groups/",
                            "meta": {}
                        }
                    }
                },
                "node_links": {
                    "links": {
                        "related": {
                            "href": "http://localhost:8000/v2/nodes/qhrc6/node_links/",
                            "meta": {}
                        }
                    }
                },
                "linked_by_nodes": {
                    "links": {
                        "related": {
                            "href": "http://localhost:8000/v2/nodes/qhrc6/linked_by_nodes/",
                            "meta": {}
                        }
                    }
                },
                "linked_by_registrations": {
                    "links": {
                        "related": {
                            "href": "http://localhost:8000/v2/nodes/qhrc6/linked_by_registrations/",
                            "meta": {}
                        }
                    }
                },
                "identifiers": {
                    "links": {
                        "related": {
                            "href": "http://localhost:8000/v2/nodes/qhrc6/identifiers/",
                            "meta": {}
                        }
                    }
                },
                "affiliated_institutions": {
                    "links": {
                        "related": {
                            "href": "http://localhost:8000/v2/nodes/qhrc6/institutions/",
                            "meta": {}
                        },
                        "self": {
                            "href": "http://localhost:8000/v2/nodes/qhrc6/relationships/institutions/",
                            "meta": {}
                        }
                    }
                },
                "draft_registrations": {
                    "links": {
                        "related": {
                            "href": "http://localhost:8000/v2/nodes/qhrc6/draft_registrations/",
                            "meta": {}
                        }
                    }
                },
                "registrations": {
                    "links": {
                        "related": {
                            "href": "http://localhost:8000/v2/nodes/qhrc6/registrations/",
                            "meta": {}
                        }
                    }
                },
                "region": {
                    "links": {
                        "related": {
                            "href": "http://localhost:8000/v2/regions/csic/",
                            "meta": {}
                        }
                    },
                    "data": {
                        "id": "csic",
                        "type": "regions"
                    }
                },
                "root": {
                    "links": {
                        "related": {
                            "href": "http://localhost:8000/v2/nodes/qhrc6/",
                            "meta": {}
                        }
                    },
                    "data": {
                        "id": "qhrc6",
                        "type": "nodes"
                    }
                },
                "logs": {
                    "links": {
                        "related": {
                            "href": "http://localhost:8000/v2/nodes/qhrc6/logs/",
                            "meta": {}
                        }
                    }
                },
                "linked_nodes": {
                    "links": {
                        "related": {
                            "href": "http://localhost:8000/v2/nodes/qhrc6/linked_nodes/",
                            "meta": {}
                        },
                        "self": {
                            "href": "http://localhost:8000/v2/nodes/qhrc6/relationships/linked_nodes/",
                            "meta": {}
                        }
                    }
                },
                "linked_registrations": {
                    "links": {
                        "related": {
                            "href": "http://localhost:8000/v2/nodes/qhrc6/linked_registrations/",
                            "meta": {}
                        },
                        "self": {
                            "href": "http://localhost:8000/v2/nodes/qhrc6/relationships/linked_registrations/",
                            "meta": {}
                        }
                    }
                },
                "view_only_links": {
                    "links": {
                        "related": {
                            "href": "http://localhost:8000/v2/nodes/qhrc6/view_only_links/",
                            "meta": {}
                        }
                    }
                },
                "citation": {
                    "links": {
                        "related": {
                            "href": "http://localhost:8000/v2/nodes/qhrc6/citation/",
                            "meta": {}
                        }
                    },
                    "data": {
                        "id": "qhrc6",
                        "type": "nodes"
                    }
                },
                "preprints": {
                    "links": {
                        "related": {
                            "href": "http://localhost:8000/v2/nodes/qhrc6/preprints/",
                            "meta": {}
                        }
                    }
                }
            },
            "links": {
                "html": "http://localhost:5000/qhrc6/",
                "self": "http://localhost:8000/v2/nodes/qhrc6/"
            }
        }],
    "links": {
        "first": null,
        "last": "http://localhost:8000/v2/nodes/?page=36",
        "prev": null,
        "next": "http://localhost:8000/v2/nodes/?page=2",
        "meta": {
            "total": 1,
            "per_page": 1
        }
    },
    "meta": {
        "version": "2.0"
    }
}'''


@mock.patch('grdmcli.constants.DEBUG', True)
def test_projects_list__debug_true_verbose_false(grdm_client, caplog):
    grdm_client.verbose = False
    resp = requests.Response()
    resp.status_code = 200
    resp._content = nodes_str
    with pytest.raises(SystemExit) as ex_info:
        with mock.patch.object(grdm_client, '_request', return_value=(resp, None)):
            projects_list(grdm_client)
    assert ex_info.value.args[0] == 0
    assert grdm_client._meta['_projects'] == 1
    assert len(caplog.records) == 3
    assert caplog.records[0].levelname == info_level_log
    assert caplog.records[0].message == f'Check config and authenticate by token'
    assert caplog.records[1].levelname == info_level_log
    assert caplog.records[1].message == f'Get list of projects'
    assert caplog.records[2].levelname == info_level_log
    assert caplog.records[2].message == f'List of projects are those which are public or which the user has access to view. [1]'


def test_projects_list__verbose_true_and_project_id_not_in_ignore_project(grdm_client, caplog):
    grdm_client.verbose = True
    resp = requests.Response()
    resp.status_code = 200
    resp._content = nodes_str
    with pytest.raises(SystemExit) as ex_info:
        with mock.patch.object(grdm_client, '_request', return_value=(resp, None)):
            projects_list(grdm_client)
    assert ex_info.value.args[0] == 0
    assert grdm_client._meta['_projects'] == 1
    assert len(caplog.records) == 4
    assert caplog.records[0].levelname == info_level_log
    assert caplog.records[0].message == f'Check config and authenticate by token'
    assert caplog.records[1].levelname == info_level_log
    assert caplog.records[1].message == f'Get list of projects'
    assert caplog.records[2].levelname == info_level_log
    assert caplog.records[2].message == f'List of projects are those which are public or which the user has access to view. [1]'
    assert caplog.records[3].levelname == debug_level_log


def test_projects_list__verbose_true_and_project_id_in_ignore_project(grdm_client, caplog):
    grdm_client.verbose = True
    _data = json.loads(nodes_str)
    _data['data'][0]['id'] = 'be43a'
    resp = requests.Response()
    resp.status_code = 200
    resp._content = json.dumps(_data)
    with pytest.raises(SystemExit) as ex_info:
        with mock.patch.object(grdm_client, '_request', return_value=(resp, None)):
            projects_list(grdm_client)
    assert ex_info.value.args[0] == 0
    assert grdm_client._meta['_projects'] == 1
    assert len(caplog.records) == 4
    assert caplog.records[0].levelname == info_level_log
    assert caplog.records[0].message == f'Check config and authenticate by token'
    assert caplog.records[1].levelname == info_level_log
    assert caplog.records[1].message == f'Get list of projects'
    assert caplog.records[2].levelname == info_level_log
    assert caplog.records[2].message == f'List of projects are those which are public or which the user has access to view. [1]'
    assert caplog.records[3].levelname == debug_level_log
