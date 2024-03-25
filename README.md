# RDM-cli
コマンドラインツールによるGakuNin RDMの一括処理機能

## Python version
Let using the supported Python versions. Refer to https://devguide.python.org/versions/  
Recommend using the latest stable Python version (Python 3.11.3 - April 5, 2023).  
**\* Note that Python 3.9+ cannot be used on Windows 7 or earlier.**

## Install and Usages

### Configuration

#### Requirement configuration
You need to provide your credentials as Personal Access Token (PAT),
by setting the `OSF_TOKEN` environment variable.  
You also need to provide the server URL, by setting the `OSF_API_URL` environment variable.

You can set default values for the token and the server URL
by using a configuration file in the current directory.  
Create `.grdmcli.config` and set
```text
[default]
osf_token = <Your Personal Access Token>
osf_api_url = http://localhost:8000/v2/
```

##### Required scopes of the token:
From all publicly documented scopes, please select:  
- `osf.full_write` : View and edit all information associated with this account, including for private projects.

#### Optional configuration
- If you are using a self-signed SSL certificate (e.g., Testing), please skip the verification of the SSL server certificate using the following configuration.  
  In `.grdmcli.config`, you can overwrite it by:
  ```
  ssl_cert_verify = false
  ```
  Or disable by an **optional argument** `--disable_ssl_verify` in command line.  

- `debug` and `verbose` is set `False` in the `constants.py`  
  ```
  DEBUG = False
  VERBOSE = False
  ```
  In `.grdmcli.config`, you can overwrite them by:
  ```
  debug = true
  verbose = true
  ```
  Or **enable** by **optional arguments** `--debug` and `--verbose` in command line

### Install as package
Change directory to the root of the project directory and run:
```cmd
python -m pip install .
```
`.` refers to the current working directory

Or install via specific branch
```cmd
python -m pip install git+https://github.com/RCOSDP/RDM-cli.git@feature/202303-cli/4.2.cli_add_member
```

#### プロジェクト/コンポーネントの新規作成
The following functions are possible
- Create new projects
- Create new components for each specific project
- Create new projects from an available template
- Create new components from an available template (don't support on the website UI)
- Creates a fork of an available project
- Link an available other projects to each specific project

The impossible ones:
- Update attributes for available projects

**\* Notice** about the order of creating a project/component:
- Create project (includes `category`, `title`, `description`, `public`, `tags`)
- Add license (as `node_license`)
- Create components for the created project
- Link to other projects (as `project_links`)

**\* Notice** about forking from a project/component:  
When forking, the following information will be changed: `title`.  
The other properties will be ignored: `category`, `description`, `public`, `tags`, `node_license`.

##### Usages
Get help and see available commands, get help on a specific command
```cmd
grdmcli --help
grdmcli projects --help
grdmcli projects create --help
```

Example for projects/components creation function 
```text
$ grdmcli projects create --help
usage: grdmcli projects create [-h]
                               --template TEMPLATE
                               [--output_result_file OUTPUT_RESULT_FILE]
                               [--osf_token OSF_TOKEN]
                               [--osf_api_url OSF_API_URL]
                               [--disable_ssl_verify]
                               [--debug]
                               [--verbose]

projects create command

options:
  -h, --help            show this help message and exit
  --template TEMPLATE   The template file for projects/components
  --output_result_file OUTPUT_RESULT_FILE
                        The output result file path
  --osf_token OSF_TOKEN
                        The Personal Access Token
  --osf_api_url OSF_API_URL
                        The API URL
  --disable_ssl_verify  Disable SSL verification
  --debug               Enable Debug mode
  --verbose             Enable Verbose mode
```

Refer to [docs/Template_file_design.xlsx](docs/Template_file_design.xlsx) for template file design.

Refer to [docs/sample](docs/sample) for template sample.


#### 参加メンバーの新規登録、上書き
The following functions are possible:
- Overwrite the project's contributor list

**\* Notice** about the order of registration/overwrite contributors of a project/component:
- Clear available contributors from the project. Except the current user. This member is project admin.
- Add new contributors list. Except the current user

**\* Notice** about creating a contoributor:  
- When the command is executed, it first deletes all contributors and then inserts the user according to the template.
- The "currently logged-in user" will keep its role as ProjectAdmin, and other attributes will not change.(No Delete/Create/Update)

##### Usages
Get help and see available commands, get help on a specific command
```cmd
grdmcli --help
grdmcli contributors --help
grdmcli contributors create --help
```

Example for contributors registration/overwrite function 
```text
$ grdmcli contributors create --help
usage: grdmcli contributors create [-h]
                                   --template TEMPLATE
                                   [--output_result_file OUTPUT_RESULT_FILE]
                                   [--osf_token OSF_TOKEN]
                                   [--osf_api_url OSF_API_URL]
                                   [--disable_ssl_verify]
                                   [--debug]
                                   [--verbose]

contributors create command

options:
  -h, --help            show this help message and exit
  --template TEMPLATE   The template file for contributors
  --output_result_file OUTPUT_RESULT_FILE
                        The output result file path
  --osf_token OSF_TOKEN
                        The Personal Access Token
  --osf_api_url OSF_API_URL
                        The API URL
  --disable_ssl_verify  Disable SSL verification
  --debug               Enable Debug mode
  --verbose             Enable Verbose mode
```

Refer to [docs/Template_file_design.xlsx](docs/Template_file_design.xlsx) for template file design.

Refer to [docs/sample](docs/sample) for template sample.


#### コマンドラインツールによるプロジェクト情報の抽出
The following functions are possible:
- Get the all project/components and contributors information of user

**\* Notice** About input information
- If project_id is not specified, information of all projects/components and contributors of the user will be gotten
- If project_id is specified, only project/component and contributor information of the specified project will be gotten

**\* Notice** About output information
- The output will be 2 Json files and can be input for "grdmcli projects create" and "grdmcli contributors create" commands.
- Can output information of more than 1000 projects and 1000 contributors

##### Usages
Get help and see available commands, get help on a specific command
```cmd
grdmcli --help
grdmcli projects --help
grdmcli projects get --help
```

Example for projects get function 
```text
$ grdmcli projects get --help
usage: grdmcli projects get [-h]
                                   [--project_id PROJECT_ID [PROJECT_ID ...]]
                                   [--output_projects_file OUTPUT_PROJECTS_FILE]
                                   [--output_contributors_file OUTPUT_CONTRIBUTORS_FILE]
                                   [--osf_token OSF_TOKEN]
                                   [--osf_api_url OSF_API_URL]
                                   [--disable_ssl_verify]
                                   [--debug]
                                   [--verbose]

projects get command

options:
  -h, --help            show this help message and exit
  --project_id PROJECT_ID [PROJECT_ID ...]
                        List id of project that user want to get information
  --output_projects_file OUTPUT_PROJECTS_FILE
                        The output projects file path
  --output_contributors_file OUTPUT_CONTRIBUTORS_FILE
                        The output contributors file path
  --osf_token OSF_TOKEN
                        The Personal Access Token
  --osf_api_url OSF_API_URL
                        The API URL
  --disable_ssl_verify  Disable SSL verification
  --debug               Enable Debug mode
  --verbose             Enable Verbose mode
```

### How to run UT TCs
- To run test code in the `test` module,  
Ensure the following packages in `requirements.txt` are installed:
```
# for testing
pytest==7.3.1
pytest-cov==4.0.0
```

- Run TC
  ```cmd
  coverage run -m --source=./ pytest ./tests/
  ```
  Run `pytest` module with all test cases under `./tests/` directory and measure on `./` all directories of code

- Create an HTML report, `htmlcov` folder will be exported
  ```cmd
  coverage html
  ```

- Show report coverage stats on modules.
  ```cmd
  coverage report -m
  ```

## Working in “development mode” (a.k.a. “Editable Installs”)
Change directory to the root of the project directory and run:
```cmd
python -m pip install -e .
```
The pip command-line flag `-e` is short for `--editable`, 
and `.` refers to the current working directory,
so together, it means to install the current directory (i.e. your project) in editable mode.

## Reference Links
- https://packaging.python.org/en/latest/guides/distributing-packages-using-setuptools/
