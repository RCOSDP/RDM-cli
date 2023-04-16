from grdmcli.exceptions import GrdmCliException


def test_grdm_cli__exception():
    error_msg = 'error message'
    exception = GrdmCliException(error_msg)
    assert isinstance(exception, GrdmCliException)
    assert isinstance(exception, Exception)
    assert str(exception) == error_msg
