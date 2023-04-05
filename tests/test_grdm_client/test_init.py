from grdmcli.grdm_client import GRDMClient


def test_init_grdm_client():
    grdm_client = GRDMClient()
    assert grdm_client.created_project_contributors == []
    assert grdm_client.user is None
    assert grdm_client._meta == {}
    assert grdm_client.template == './template_file.json'
    assert grdm_client.output_result_file == './output_result_file.json'
    assert grdm_client.is_authenticated is False
