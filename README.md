# RDM-cli
コマンドラインツールによるGakuNin RDMの一括処理機能

## Python (dev in 3.6)
This CLI tool needs Python at least version 3.3.

## Install and Usages

### Configuration
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

### Install as package
Change directory to the root of the project directory and run:
```cmd
python -m pip install .
```
`.` refers to the current working directory

Or install via specific branch
```cmd
python -m pip install git+https://github.com/RCOSDP/RDM-cli.git@feature/202303-cli/.2.cli_add_member
```

#### 参加メンバーの新規登録、上書き

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
usage: grdmcli contributors create [-h] --template TEMPLATE
                                   [--output_result_file OUTPUT_RESULT_FILE]
                                   [--osf_token OSF_TOKEN]
                                   [--osf_api_url OSF_API_URL]

contributors create command

optional arguments:
  -h, --help            show this help message and exit
  --template TEMPLATE   template file for contributors
  --output_result_file OUTPUT_RESULT_FILE
                        the output result file path
  --osf_token OSF_TOKEN
                        the Personal Access Token
  --osf_api_url OSF_API_URL
                        the API URL
```

### How to run UT TCs
- To run test code in the `test` module,  
Ensure the following packages in `requirements.txt` are installed:
```
# for testing
pytest
pytest-cov
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
