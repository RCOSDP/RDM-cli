import json
from types import SimpleNamespace
from unittest import mock

import pytest
import requests

from grdmcli.exceptions import GrdmCliException
from grdmcli.grdm_client.contributors import (
    _get_template_schema_contributors,
    _list_project_contributors,
    _delete_project_contributor,
    _prepare_project_contributor_data,
    _add_project_contributor,
    _overwrite_project_contributors,
    _clear_project_current_contributors,
    contributors_create
)
from tests.factories import GRDMClientFactory

get_str = """{
  "data": [
    {
      "relationships": {
        "node": {
          "links": {
            "related": {
              "href": "https://api.osf.io/v2/nodes/rcjd2/",
              "meta": {}
            }
          }
        },
        "users": {
          "links": {
            "related": {
              "href": "https://api.osf.io/v2/users/typ47/",
              "meta": {}
            }
          }
        }
      },
      "links": {
        "self": "https://api.osf.io/v2/nodes/rcjd2/contributors/typ47/"
      },
      "embeds": {
        "users": {
          "data": {
            "relationships": {
              "nodes": {
                "links": {
                  "related": {
                    "href": "https://api.osf.io/v2/users/typ47/nodes/",
                    "meta": {}
                  }
                }
              },
              "institutions": {
                "links": {
                  "self": {
                    "href": "https://api.osf.io/v2/users/typ47/relationships/institutions/",
                    "meta": {}
                  },
                  "related": {
                    "href": "https://api.osf.io/v2/users/typ47/institutions/",
                    "meta": {}
                  }
                }
              }
            },
            "links": {
              "self": "https://api.osf.io/v2/users/typ47/",
              "html": "https://osf.io/typ47/",
              "profile_image": "https://secure.gravatar.com/avatar/3dd8757ba100b8406413706886243811?d=identicon"
            },
            "attributes": {
              "family_name": "Geiger",
              "suffix": "",
              "locale": "en_us",
              "date_registered": "2014-03-18T19:11:57.252000",
              "middle_names": "J.",
              "given_name": "Brian",
              "full_name": "Brian J. Geiger",
              "active": true,
              "timezone": "America/New_York"
            },
            "type": "users",
            "id": "typ47"
          }
        }
      },
      "attributes": {
        "index": 0,
        "unregistered_contributor": null,
        "bibliographic": true,
        "permission": "admin"
      },
      "type": "contributors",
      "id": "rcjd2-typ47"
    },
    {
      "relationships": {
        "node": {
          "links": {
            "related": {
              "href": "https://api.osf.io/v2/nodes/y9jdt/",
              "meta": {}
            }
          }
        },
        "users": {
          "links": {
            "related": {
              "href": "https://api.osf.io/v2/users/typ46/",
              "meta": {}
            }
          }
        }
      },
      "links": {
        "self": "https://api.osf.io/v2/nodes/y9jdt/contributors/typ46/"
      },
      "embeds": {
        "users": {
          "data": {
            "relationships": {
              "nodes": {
                "links": {
                  "related": {
                    "href": "https://api.osf.io/v2/users/typ46/nodes/",
                    "meta": {}
                  }
                }
              },
              "institutions": {
                "links": {
                  "self": {
                    "href": "https://api.osf.io/v2/users/typ46/relationships/institutions/",
                    "meta": {}
                  },
                  "related": {
                    "href": "https://api.osf.io/v2/users/typ46/institutions/",
                    "meta": {}
                  }
                }
              }
            },
            "links": {
              "self": "https://api.osf.io/v2/users/typ46/",
              "html": "https://osf.io/typ46/",
              "profile_image": "https://secure.gravatar.com/avatar/3dd8757ba100b8406413706886243811?d=identicon"
            },
            "attributes": {
              "family_name": "Geiger",
              "suffix": "",
              "locale": "en_us",
              "date_registered": "2014-03-18T19:11:57.252000",
              "middle_names": "J.",
              "given_name": "Brian",
              "full_name": "Brian J. Geiger",
              "active": true,
              "timezone": "America/New_York"
            },
            "type": "users",
            "id": "typ46"
          }
        }
      },
      "attributes": {
        "index": 0,
        "unregistered_contributor": null,
        "bibliographic": true,
        "permission": "admin"
      },
      "type": "contributors",
      "id": "y9jdt-typ46"
    }
  ],
  "links": {
    "first": null,
    "last": null,
    "prev": null,
    "next": null,
    "meta": {
      "total": 9,
      "per_page": 10,
      "total_bibliographic": 1
    }
  }
}"""
post_str = """{
  "data": {
    "id": "bg8v7-faqpw",
    "type": "contributors",
    "attributes": {
      "index": 1,
      "bibliographic": true,
      "permission": "write",
      "unregistered_contributor": null
    },
    "relationships": {
      "users": {
        "links": {
          "related": {
            "href": "https://api.osf.io/v2/users/faqpw/",
            "meta": {}
          }
        },
        "data": {
          "id": "faqpw",
          "type": "users"
        }
      },
      "preprint": {
        "links": {
          "related": {
            "href": "https://api.osf.io/v2/preprints/bg8v7/",
            "meta": {}
          }
        },
        "data": {
          "id": "bg8v7",
          "type": "preprints"
        }
      }
    },
    "embeds": {
      "users": {
        "data": {
          "id": "typ47",
          "type": "users",
          "attributes": {
            "full_name": "Freddie Mercury1",
            "given_name": "Freddie",
            "middle_names": "",
            "family_name": "Mercury1",
            "suffix": "",
            "date_registered": "2022-05-04T19:39:33.138339",
            "active": true,
            "timezone": "Etc/UTC",
            "locale": "en_US",
            "social": {},
            "employment": [],
            "education": []
          },
          "relationships": {
            "nodes": {
              "links": {
                "related": {
                  "href": "https://api.osf.io/v2/users/faqpw/nodes/",
                  "meta": {}
                }
              }
            },
            "groups": {
              "links": {
                "related": {
                  "href": "https://api.osf.io/v2/users/faqpw/groups/",
                  "meta": {}
                }
              }
            },
            "registrations": {
              "links": {
                "related": {
                  "href": "https://api.osf.io/v2/users/faqpw/registrations/",
                  "meta": {}
                }
              }
            },
            "institutions": {
              "links": {
                "related": {
                  "href": "https://api.osf.io/v2/users/faqpw/institutions/",
                  "meta": {}
                },
                "self": {
                  "href": "https://api.osf.io/v2/users/faqpw/relationships/institutions/",
                  "meta": {}
                }
              }
            },
            "preprints": {
              "links": {
                "related": {
                  "href": "https://api.osf.io/v2/users/faqpw/preprints/",
                  "meta": {}
                }
              }
            }
          },
          "links": {
            "html": "https://osf.io/faqpw/",
            "profile_image": "https://secure.gravatar.com/avatar/c9ac5d6cc7964ba7eb2bb96f877bc983?d=identicon",
            "self": "https://api.osf.io/v2/users/faqpw/"
          }
        }
      }
    },
    "links": {
      "self": "https://api.osf.io/v2/preprints/bg8v7/contributors/faqpw/"
    }
  },
  "meta": {
    "version": "2.0"
  }
}"""
pk = 'node23'
user_id = 'typ46'
index = 0
contributor_object = {
    "id": "user45",
    "bibliographic": True,
    "permission": "admin"
}
error_message = 'error'

project_dict = {
    "projects": [
        {
            "id": "nid01",
            "contributors": [
                {
                    "id": "typ46",
                    "bibliographic": True,
                    "permission": "admin"
                },
                {
                    "id": "uid03",
                    "bibliographic": True,
                    "permission": "write"
                }
            ]
        },
        {
            "id": "nid02",
            "contributors": [
                {
                    "id": "typ46",
                    "bibliographic": True,
                    "permission": "admin"
                },
                {
                    "id": "uid03",
                    "bibliographic": True,
                    "permission": "write"
                },
                {
                    "id": "uid03",
                    "bibliographic": False,
                    "permission": "read"
                }
            ]
        }
    ]
}

get_obj = json.loads(get_str, object_hook=lambda d: SimpleNamespace(**d))
post_obj = json.loads(post_str, object_hook=lambda d: SimpleNamespace(**d))


@pytest.fixture
def grdm_client():
    return GRDMClientFactory()


def test_get_template_schema_contributors__normal():
    actual = _get_template_schema_contributors(grdm_client)
    assert type(actual) is str
    assert actual.__contains__('contributors_create_schema.json')


def test_list_project_contributors__auth_false(grdm_client):
    mock.patch.object(grdm_client, '_request', return_value=(None, error_message))
    grdm_client.user = None
    with pytest.raises(SystemExit) as ex_info:
        _list_project_contributors(grdm_client, pk)
    assert ex_info.value.code == 'Missing currently logged-in user'


def test_list_project_contributors__send_request_error_and_ignore_error_false_sys_exit(grdm_client):
    with mock.patch.object(grdm_client, '_request', return_value=(None, error_message)):
        with pytest.raises(SystemExit) as ex_info:
            _list_project_contributors(grdm_client, pk, ignore_error=False)
        assert ex_info.value.code == error_message


def test_list_project_contributors__send_request_error_and_ignore_error_true_return_list_empty(grdm_client):
    with mock.patch.object(grdm_client, '_request', return_value=(None, error_message)):
        data_dict, data_json = _list_project_contributors(grdm_client, pk, ignore_error=True)
        assert data_dict == []
        assert data_json == []


def test_list_project_contributors__verbose_true(grdm_client):
    resp = requests.Response()
    resp._content = get_str
    with mock.patch.object(grdm_client, '_request', return_value=(resp, None)):
        list_contributor, data_json = _list_project_contributors(grdm_client, pk)
        assert len(list_contributor) > 0
        assert len(data_json) > 0
        assert type(list_contributor) is list


def test_list_project_contributors__verbose_false(grdm_client):
    resp = requests.Response()
    resp._content = get_str
    with mock.patch.object(grdm_client, '_request', return_value=(resp, None)):
        list_contributor, data_json = _list_project_contributors(grdm_client, pk, verbose=False)
        assert len(list_contributor) > 0
        assert len(data_json) > 0
        assert type(list_contributor) is list


@mock.patch('sys.exit', side_effect=Exception())
def test_delete_project_contributor__send_request_error_and_ignore_error_false_sys_exit(mocker, grdm_client):
    with mock.patch.object(grdm_client, '_request', return_value=(None, error_message)):
        with pytest.raises(Exception):
            _delete_project_contributor(grdm_client, pk, user_id, ignore_error=False)
        mocker.assert_called_once_with(error_message)


def test_delete_project_contributor__send_request_error_and_ignore_error_true(grdm_client, capfd):
    with mock.patch.object(grdm_client, '_request', return_value=(None, error_message)):
        _delete_project_contributor(grdm_client, pk, user_id)
        captured = capfd.readouterr()
        lines = captured.out.split('\n')
        assert lines[0] == f'DELETE Remove contributor \'{pk}-{user_id}\''
        assert lines[1] == f'WARN {error_message}'
        assert lines[2] == f'Deleted contributor: \'{pk}-{user_id}\''


def test_delete_project_contributor__success(grdm_client, capfd):
    with mock.patch.object(grdm_client, '_request', return_value=(None, None)):
        _delete_project_contributor(grdm_client, pk, user_id)
        captured = capfd.readouterr()
        lines = captured.out.split('\n')
        assert lines[0] == f'DELETE Remove contributor \'{pk}-{user_id}\''
        assert lines[1] == f'Deleted contributor: \'{pk}-{user_id}\''


def test_prepare_project_contributor_data__verbose_false(capfd):
    actual = _prepare_project_contributor_data(grdm_client, contributor_object, index, verbose=False)
    captured = capfd.readouterr()
    assert captured.out is ''
    assert type(actual) is dict
    assert actual['data']['attributes']['permission'] == contributor_object['permission']


def test_prepare_project_contributor_data__verbose_true(capfd):
    actual = _prepare_project_contributor_data(grdm_client, contributor_object, index)
    captured = capfd.readouterr()
    assert captured.out.__contains__('Prepared contributor data')
    assert type(actual) is dict
    assert actual['data']['attributes']['permission'] == contributor_object['permission']


def test_add_project_contributor__send_request_error_and_ignore_error_false_sys_exit(grdm_client):
    with mock.patch.object(grdm_client, '_request', return_value=(None, error_message)):
        with pytest.raises(SystemExit) as ex_info:
            _add_project_contributor(grdm_client, pk, contributor_object, index, ignore_error=False)
        assert ex_info.value.code == error_message


def test_add_project_contributor__send_request_error_and_ignore_error_true_return_none(capfd, grdm_client):
    with mock.patch.object(grdm_client, '_request', return_value=(None, error_message)):
        actual1, actual2 = _add_project_contributor(grdm_client, pk, contributor_object, index)
        captured = capfd.readouterr()
        assert captured.out.__contains__(f'WARN {error_message}')
        assert actual2 == actual1 is None


def test_add_project_contributor__success(capfd, grdm_client):
    resp = requests.Response()
    resp._content = post_str
    with mock.patch.object(grdm_client, '_request', return_value=(resp, None)):
        actual1, actual2 = _add_project_contributor(grdm_client, pk, contributor_object, index)
        captured = capfd.readouterr()
        _user_id = contributor_object['id']
        assert captured.out.__contains__(f'Created contributor: \'{pk}-{_user_id}\'')
        assert type(actual1) is SimpleNamespace
        assert type(actual2) is dict
        assert len(grdm_client.created_project_contributors) > 0


def test_clear_project_current_contributors_success(grdm_client):
    data = get_obj.data
    with mock.patch.object(grdm_client, '_list_project_contributors', return_value=(data, None)):
        current_user_contributor = _clear_project_current_contributors(grdm_client, pk, [], None)
        assert type(current_user_contributor) is SimpleNamespace
        assert len(grdm_client.created_project_contributors) == 1
        assert current_user_contributor == data[1]


def test_overwrite_project_contributors__current_user_in_contributors(grdm_client, capfd):
    _contributors = [project_dict["projects"][0]["contributors"][0]]
    _id = project_dict.get('id')
    contributor_user_ids = [grdm_client.user.id]
    current_user_contributor = get_obj.data[1]
    _overwrite_project_contributors(grdm_client, _contributors, _id, contributor_user_ids,
                                    current_user_contributor)
    captured = capfd.readouterr()
    assert captured.out == f'WARN This member is the currently logged-in user, so skip creating/updating\n'


def test_overwrite_project_contributors__add_project_success(grdm_client, capfd):
    with mock.patch.object(grdm_client, '_add_project_contributor', return_value=(post_obj.data, None)):
        _contributors = [project_dict['projects'][0]['contributors'][1]]
        _id = project_dict.get('id')
        current_project_contributor_user_ids = [grdm_client.user.id]
        current_user_contributor = get_obj.data[0]
        _overwrite_project_contributors(grdm_client, _contributors, _id,
                                        current_project_contributor_user_ids, current_user_contributor)
        captured = capfd.readouterr()
        _user_idx = 0
        assert captured.out == f'JSONPOINTER ./contributors/{_user_idx}/\n'
        assert _contributors[0]['id'] == post_obj.data.id
        assert _contributors[0]['type'] == post_obj.data.type
        assert _contributors[0]['permission'] == post_obj.data.attributes.permission
        assert _contributors[0]['index'] == post_obj.data.attributes.index
        assert _contributors[0]['bibliographic'] == post_obj.data.attributes.bibliographic


def test_overwrite_project_contributors__add_project_none(grdm_client, capfd):
    with mock.patch.object(grdm_client, '_add_project_contributor', return_value=(None, None)):
        _contributors = [project_dict['projects'][0]['contributors'][1]]
        _id = project_dict.get('id')
        current_project_contributor_user_ids = [grdm_client.user.id]
        current_user_contributor = get_obj.data[0]
        _overwrite_project_contributors(grdm_client, _contributors, _id,
                                        current_project_contributor_user_ids, current_user_contributor)
        captured = capfd.readouterr()
        _user_idx = 0
        assert captured.out == f'JSONPOINTER ./contributors/{_user_idx}/\n'


def test_overwrite_project_contributors__user_is_duplicate(grdm_client, capfd):
    _contributors = project_dict.get('projects')[1].get('contributors')
    with mock.patch.object(grdm_client, '_add_project_contributor', return_value=(post_obj.data, None)):
        _id = project_dict.get('id')
        contributor_user_ids = [grdm_client.user.id]
        current_user_contributor = post_obj.data
        _overwrite_project_contributors(grdm_client, _contributors, _id, contributor_user_ids,
                                        current_user_contributor)
        captured = capfd.readouterr()
        lines = captured.out.split('\n')
        _user_idx = 1
        assert lines[0] == f'WARN This member is the currently logged-in user, so skip creating/updating'
        assert lines[1] == f'JSONPOINTER ./contributors/{_user_idx}/'
        assert lines[2] == f'WARN Duplicate member object in template file'


def test_contributors_create__file_path_schema_not_exist(grdm_client):
    with mock.patch('os.path.exists', return_value=False):
        with pytest.raises(SystemExit) as ex_info:
            contributors_create(grdm_client)
        assert ex_info.value.code == f'Missing the template schema {grdm_client.template_schema_contributors}'


def test_contributors_create__file_path_template_not_exist(grdm_client):
    with mock.patch('os.path.exists', side_effect=[True, False]):
        with pytest.raises(SystemExit) as ex_info:
            contributors_create(grdm_client)
        assert ex_info.value.code == f'Missing the template file'


@mock.patch('os.path.exists', side_effect=[True, True])
@mock.patch('sys.exit')
def test_contributors_create__success_verbose_false(mocker, grdm_client, capfd):
    _projects = project_dict["projects"][0]
    with mock.patch('grdmcli.utils.read_json_file', return_value={"projects": [_projects]}):
        with mock.patch('grdmcli.utils.check_json_schema'):
            with mock.patch('grdmcli.utils.write_json_file'):
                contributors_create(grdm_client, verbose=False)
            captured = capfd.readouterr()
            lines = captured.out.split('\n')
            assert lines[4] == 'JSONPOINTER /projects/0/'
            assert lines[5] == 'REMOVE Current contributors'
            assert lines[6] == 'OVERWRITE new contributors'
            assert lines[7] == f'USE the output result file: {grdm_client.output_result_file}'


@mock.patch('os.path.exists', side_effect=[True, True])
@mock.patch('sys.exit')
def test_contributors_create__created_project_contributors_empty(mocker, grdm_client, capfd):
    grdm_client.created_project_contributors = []
    _projects = project_dict["projects"][1]
    with mock.patch('grdmcli.utils.read_json_file', return_value={"projects": [_projects]}):
        with mock.patch('grdmcli.utils.check_json_schema'):
            with mock.patch('grdmcli.utils.write_json_file'):
                contributors_create(grdm_client, verbose=True)
            captured = capfd.readouterr()
            lines = captured.out.split('\n')
            assert lines[4] == 'JSONPOINTER /projects/0/'
            assert lines[5] == 'REMOVE Current contributors'
            assert lines[6] == 'OVERWRITE new contributors'
            assert lines[7] == f'Created contributors for projects. [{len(grdm_client.created_project_contributors)}]'
            assert lines[8] == f'USE the output result file: {grdm_client.output_result_file}'


@mock.patch('os.path.exists', side_effect=[True, True])
@mock.patch('sys.exit')
def test_contributors_create__created_project_contributors_exists(mocker, grdm_client, capfd):
    grdm_client.created_project_contributors = get_obj.data
    _projects = project_dict["projects"][1]
    mocker.patch('grdmcli.utils.write_json_file')
    mocker.patch('grdmcli.utils.check_json_schema')
    with mock.patch('grdmcli.utils.read_json_file', return_value={"projects": [_projects]}):
        contributors_create(grdm_client, verbose=True)
        lines = capfd.readouterr().out.split('\n')
        prj_created = len(grdm_client.created_project_contributors)
        assert lines[4] == 'JSONPOINTER /projects/0/'
        assert lines[5] == 'REMOVE Current contributors'
        assert lines[6] == 'OVERWRITE new contributors'
        assert lines[7] == f'Created contributors for projects. [{prj_created}]'
        assert lines[8 + prj_created] == f'USE the output result file: {grdm_client.output_result_file}'


@mock.patch('os.path.exists', side_effect=[True, True])
@mock.patch('grdmcli.utils.read_json_file', return_value=project_dict)
@mock.patch('grdmcli.utils.write_json_file')
def test_contributors_create__verbose_false_check_schema_raise_error(mocker_write, mocker_read, grdm_client, capfd):
    err = 'check schema error'
    with pytest.raises(SystemExit) as ex_sys:
        with mock.patch('grdmcli.utils.check_json_schema', side_effect=GrdmCliException(err)):
            contributors_create(grdm_client, verbose=False)
    assert ex_sys.value.code == 0
    lines = capfd.readouterr().out.split('\n')
    assert lines[2] == f'VALIDATE BY the template of projects: {grdm_client.template_schema_contributors}'
    assert lines[3] == f'Exception {err}'
    assert lines[4] == f'USE the output result file: {grdm_client.output_result_file}'


@mock.patch('os.path.exists', side_effect=[True, True])
@mock.patch('sys.exit')
def test_contributors_create__project_not_id(mocker, grdm_client, capfd):
    contributor = {"contributors": project_dict['projects'][0]['contributors']}
    _projects_dict = {'projects': [contributor]}
    with mock.patch('grdmcli.utils.read_json_file', return_value=_projects_dict):
        with mock.patch('grdmcli.utils.check_json_schema'):
            with mock.patch('grdmcli.utils.write_json_file'):
                contributors_create(grdm_client, verbose=False)
            captured = capfd.readouterr()
            lines = captured.out.split('\n')
            assert lines[4] == f'JSONPOINTER /projects/0/id == None'
            assert lines[5] == f'USE the output result file: {grdm_client.output_result_file}'
