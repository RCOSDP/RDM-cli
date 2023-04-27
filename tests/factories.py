import json
from argparse import Namespace
from types import SimpleNamespace

user_str = '''{
        "id": "typ46",
        "type": "users",
        "attributes": {
            "uid": "36",
            "full_name": "admin01_inst17 example.com.vn",
            "given_name": "admin01_inst17",
            "middle_names": "",
            "family_name": "example.com.vn",
            "suffix": "",
            "date_registered": "2023-01-31T08:28:35.644862",
            "active": true,
            "timezone": "Etc/UTC",
            "locale": "en_US",
            "social": {},
            "employment": [
                {
                    "title": "",
                    "endYear": null,
                    "ongoing": false,
                    "endMonth": null,
                    "startYear": null,
                    "department": "",
                    "startMonth": null,
                    "institution": "TMA",
                    "department_ja": "",
                    "institution_ja": "TMA"
                }
            ],
            "education": [],
            "can_view_reviews": [],
            "accepted_terms_of_service": true
        },
        "relationships": {
            "nodes": {
                "links": {
                    "related": {
                        "href": "http://localhost:8000/v2/users/qm73w/nodes/",
                        "meta": {}
                    }
                }
            },
            "groups": {
                "links": {
                    "related": {
                        "href": "http://localhost:8000/v2/users/qm73w/groups/",
                        "meta": {}
                    }
                }
            },
            "quickfiles": {
                "links": {
                    "related": {
                        "href": "http://localhost:8000/v2/users/qm73w/quickfiles/",
                        "meta": {}
                    },
                    "upload": {
                        "href": "http://localhost:7777/v1/resources/uancbt93pe/providers/osfstorage/",
                        "meta": {}
                    },
                    "download": {
                        "href": "http://localhost:7777/v1/resources/uancbt93pe/providers/osfstorage/?zip=",
                        "meta": {}
                    }
                }
            },
            "registrations": {
                "links": {
                    "related": {
                        "href": "http://localhost:8000/v2/users/qm73w/registrations/",
                        "meta": {}
                    }
                }
            },
            "institutions": {
                "links": {
                    "related": {
                        "href": "http://localhost:8000/v2/users/qm73w/institutions/",
                        "meta": {}
                    },
                    "self": {
                        "href": "http://localhost:8000/v2/users/qm73w/relationships/institutions/",
                        "meta": {}
                    }
                }
            },
            "preprints": {
                "links": {
                    "related": {
                        "href": "http://localhost:8000/v2/users/qm73w/preprints/",
                        "meta": {}
                    }
                }
            },
            "emails": {
                "links": {
                    "related": {
                        "href": "http://localhost:8000/v2/users/qm73w/settings/emails/",
                        "meta": {}
                    }
                }
            },
            "default_region": {
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
            "settings": {
                "links": {
                    "related": {
                        "href": "http://localhost:8000/v2/users/qm73w/settings/",
                        "meta": {}
                    }
                },
                "data": {
                    "id": "qm73w",
                    "type": "user-settings"
                }
            }
        },
        "links": {
            "html": "http://localhost:5000/qm73w/",
            "profile_image": "https://secure.gravatar.com/avatar/bca17c92257b100912db5f810514a98b?d=identicon",
            "self": "http://localhost:8000/v2/users/qm73w/"
        }
    }'''


class CommonCLIFactory(Namespace):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.config_default = {}
        self._meta = {}
        self.config_file = 'D:/config.config'
        self.is_authenticated = False
        self.user = None
        self.template = 'path-to-template'
        self.output_result_file = 'path-to-write-file'
        self.affiliated_institutions = []
        self.affiliated_users = []
        self.projects = []

    @property
    def has_required_attributes(self):
        return self.osf_token is not None and self.osf_api_url is not None

    def _request(self, method, url, params=None, data=None, headers=None):
        pass

    def _load_required_attributes_from_config_file(self):
        pass

    def _load_required_attributes_from_environment(self):
        pass

    def _check_config(self, verbose=True):
        pass

    def _users_me(self, ignore_error=True, verbose=True):
        pass

    def _prepare_output_file(self):
        pass


class GRDMClientFactory(CommonCLIFactory):

    def __init__(self):
        super().__init__()
        self.user = json.loads(user_str, object_hook=lambda d: SimpleNamespace(**d))
        self.verbose = False

        # For projects functions
        self.created_projects = []
        self.template_schema_projects = 'path-to-schema'

    # For projects functions

    def _fake_project_content_data(self, pk, verbose=True):
        pass

    def _prepare_project_data(self, node_object, verbose=True):
        pass

    def _find_license_id_from_name(self, name, verbose=True):
        pass

    def _link_project_to_project(self, node_id, pointer_id, ignore_error=True, verbose=True):
        pass

    def _licenses(self, ignore_error=True, verbose=True):
        pass

    def _add_project_pointers(self, project_links, project, verbose=True):
        pass

    def _create_project(self, node_object, ignore_error=True, verbose=True):
        pass

    def _load_project(self, pk, is_fake=True, ignore_error=True, verbose=True):
        pass

    def _fork_project(self, node_object, ignore_error=True, verbose=True):
        pass

    def _projects_add_component(self, parent_id, node_object, ignore_error=True, verbose=True):
        pass

    def _add_project_components(self, children, project, verbose=True):
        pass

    def _create_or_load_project(self, projects, project_idx):
        pass
