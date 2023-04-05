import json

from types import SimpleNamespace


class CommonCLIFactory:
    def __init__(self):
        self.osf_token = 'access-token'
        self.osf_api_url = 'http://localhost:8000/v2/'
        self.config_file = 'D:/config.config'
        self.is_authenticated = False

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


class GRDMClientFactory(CommonCLIFactory):

    def __init__(self):
        super().__init__()
        self.user = json.loads('{"id": "typ46"}',
                               object_hook=lambda d: SimpleNamespace(**d))
        self.created_project_contributors = []
        self.template_schema_contributors = 'path-to-schema'
        self.template = 'path-to-template'
        self.output_result_file = 'path-to-write-file'

    def _users_me(self):
        pass

    def _prepare_project_contributor_data(self, _contributor_object, _index, verbose=True):
        pass

    def _delete_project_contributor(self, pk, user_id, ignore_error=True, verbose=True):
        pass

    def _list_project_contributors(self, pk, ignore_error=True, verbose=True):
        pass

    def _add_project_contributor(self, pk, contributor_object, index, ignore_error=True, verbose=True):
        pass

    def _overwrite_project_contributors(self, contributors, pk, contributor_user_ids, current_user_contributor):
        pass
