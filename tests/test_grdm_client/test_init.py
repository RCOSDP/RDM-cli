from grdmcli.grdm_client import GRDMClient


def test_init__grdm_client():
    args = {'osf_token': 'osf-token', 'osf_api_url': 'http://localhost:8000/v2/', 'ssl_cert_verify': False}
    grdm_client = GRDMClient(**args)
    assert grdm_client.user is None
    assert grdm_client._meta == {}
    assert grdm_client.config_default == {}
    assert grdm_client.template == './template_file.json'
    assert grdm_client.output_result_file == './output_result_file.json'
    assert not grdm_client.is_authenticated
    assert grdm_client.config_file
    assert grdm_client.has_required_attributes
    assert grdm_client.affiliated_institutions == []
    assert grdm_client.affiliated_users == []
    assert grdm_client.projects == []
    # project create
    assert grdm_client.created_projects == []
    # contributors create
    assert grdm_client.created_project_contributors == []
