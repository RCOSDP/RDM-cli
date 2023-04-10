from grdmcli.status import *


def test_is_informational__true():
    assert is_informational(HTTP_100_CONTINUE)
    assert is_informational(HTTP_101_SWITCHING_PROTOCOLS)


def test_is_informational__false():
    assert not is_informational(HTTP_200_OK)
    assert not is_informational(HTTP_300_MULTIPLE_CHOICES)
    assert not is_informational(HTTP_404_NOT_FOUND)
    assert not is_informational(HTTP_500_INTERNAL_SERVER_ERROR)


def test_is_success__true():
    assert is_success(HTTP_200_OK)
    assert is_success(HTTP_201_CREATED)
    assert is_success(HTTP_202_ACCEPTED)
    assert is_success(HTTP_203_NON_AUTHORITATIVE_INFORMATION)
    assert is_success(HTTP_204_NO_CONTENT)
    assert is_success(HTTP_205_RESET_CONTENT)
    assert is_success(HTTP_206_PARTIAL_CONTENT)
    assert is_success(HTTP_207_MULTI_STATUS)


def test_is_success__false():
    assert not is_success(HTTP_100_CONTINUE)
    assert not is_success(HTTP_300_MULTIPLE_CHOICES)
    assert not is_success(HTTP_404_NOT_FOUND)
    assert not is_success(HTTP_500_INTERNAL_SERVER_ERROR)


def test_is_redirect__true():
    assert is_redirect(HTTP_300_MULTIPLE_CHOICES)
    assert is_redirect(HTTP_301_MOVED_PERMANENTLY)
    assert is_redirect(HTTP_302_FOUND)
    assert is_redirect(HTTP_303_SEE_OTHER)
    assert is_redirect(HTTP_304_NOT_MODIFIED)
    assert is_redirect(HTTP_305_USE_PROXY)
    assert is_redirect(HTTP_306_RESERVED)
    assert is_redirect(HTTP_307_TEMPORARY_REDIRECT)


def test_is_redirect__false():
    assert not is_redirect(HTTP_100_CONTINUE)
    assert not is_redirect(HTTP_200_OK)
    assert not is_redirect(HTTP_404_NOT_FOUND)
    assert not is_redirect(HTTP_500_INTERNAL_SERVER_ERROR)


def test_is_client_error__true():
    assert is_client_error(HTTP_400_BAD_REQUEST)
    assert is_client_error(HTTP_401_UNAUTHORIZED)
    assert is_client_error(HTTP_402_PAYMENT_REQUIRED)
    assert is_client_error(HTTP_403_FORBIDDEN)
    assert is_client_error(HTTP_404_NOT_FOUND)
    assert is_client_error(HTTP_405_METHOD_NOT_ALLOWED)
    assert is_client_error(HTTP_406_NOT_ACCEPTABLE)
    assert is_client_error(HTTP_407_PROXY_AUTHENTICATION_REQUIRED)
    assert is_client_error(HTTP_408_REQUEST_TIMEOUT)
    assert is_client_error(HTTP_409_CONFLICT)
    assert is_client_error(HTTP_410_GONE)
    assert is_client_error(HTTP_411_LENGTH_REQUIRED)
    assert is_client_error(HTTP_412_PRECONDITION_FAILED)
    assert is_client_error(HTTP_413_REQUEST_ENTITY_TOO_LARGE)
    assert is_client_error(HTTP_414_REQUEST_URI_TOO_LONG)
    assert is_client_error(HTTP_415_UNSUPPORTED_MEDIA_TYPE)
    assert is_client_error(HTTP_416_REQUESTED_RANGE_NOT_SATISFIABLE)
    assert is_client_error(HTTP_417_EXPECTATION_FAILED)
    assert is_client_error(HTTP_422_UNPROCESSABLE_ENTITY)
    assert is_client_error(HTTP_423_LOCKED)
    assert is_client_error(HTTP_424_FAILED_DEPENDENCY)
    assert is_client_error(HTTP_428_PRECONDITION_REQUIRED)
    assert is_client_error(HTTP_429_TOO_MANY_REQUESTS)
    assert is_client_error(HTTP_431_REQUEST_HEADER_FIELDS_TOO_LARGE)
    assert is_client_error(HTTP_451_UNAVAILABLE_FOR_LEGAL_REASONS)


def test_is_client_error__false():
    assert not is_client_error(HTTP_100_CONTINUE)
    assert not is_client_error(HTTP_200_OK)
    assert not is_client_error(HTTP_300_MULTIPLE_CHOICES)
    assert not is_client_error(HTTP_500_INTERNAL_SERVER_ERROR)


def test_is_server_error__true():
    assert is_server_error(HTTP_500_INTERNAL_SERVER_ERROR)
    assert is_server_error(HTTP_501_NOT_IMPLEMENTED)
    assert is_server_error(HTTP_502_BAD_GATEWAY)
    assert is_server_error(HTTP_503_SERVICE_UNAVAILABLE)
    assert is_server_error(HTTP_504_GATEWAY_TIMEOUT)
    assert is_server_error(HTTP_505_HTTP_VERSION_NOT_SUPPORTED)
    assert is_server_error(HTTP_507_INSUFFICIENT_STORAGE)
    assert is_server_error(HTTP_511_NETWORK_AUTHENTICATION_REQUIRED)


def test_is_server_error__false():
    assert not is_server_error(HTTP_100_CONTINUE)
    assert not is_server_error(HTTP_200_OK)
    assert not is_server_error(HTTP_300_MULTIPLE_CHOICES)
    assert not is_server_error(HTTP_404_NOT_FOUND)
