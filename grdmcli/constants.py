import os

CONFIG_FILENAME = '.grdmcli.config'
CONFIG_SECTION = 'default'

OSF_API_URL_VAR_NAME = 'OSF_API_URL'
OSF_TOKEN_VAR_NAME = 'OSF_TOKEN'
SSL_CERT_VERIFY_VAR_NAME = 'SSL_CERT_VERIFY'
SSL_CERT_FILE_VAR_NAME = 'SSL_CERT_FILE'
SSL_KEY_FILE_VAR_NAME = 'SSL_KEY_FILE'
DEBUG_VAR_NAME = 'DEBUG'
VERBOSE_VAR_NAME = 'VERBOSE'

TEMPLATE_FILE_NAME_DEFAULT = './template_file.json'
OUTPUT_RESULT_FILE_NAME_DEFAULT = './output_result_file.json'

MAX_PAGE_SIZE = 1000
PAGE_SIZE_QUERY_PARAM = 'page[size]'
ORDERING_QUERY_PARAM = 'sort'
ORDERING_BY = 'pk'

TEMPLATE_SCHEMA_PROJECTS = './json_schema/projects_create_schema.json'
TEMPLATE_SCHEMA_CONTRIBUTORS = './json_schema/contributors_create_schema.json'

# For `requests.request` keyword arguments
# verify: (optional) Either a boolean, in which case it controls whether we verify
# the server's TLS certificate, or a string, in which case it must be a path
# to a CA bundle to use. Defaults to `True`.
SSL_CERT_VERIFY = True
# cert: (optional) if String, path to ssl client cert file (.pem). If Tuple, ('cert', 'key') pair.
SSL_CERT_FILE = os.environ.get('SSL_CERT_FILE', None)
SSL_KEY_FILE = os.environ.get('SSL_KEY_FILE', None)

# Logging config
DEBUG = False
VERBOSE = False
LOGGING_FORMAT = '%(asctime)s %(levelname)-8s : %(message)s'
