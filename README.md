# RDM-cli
コマンドラインツールによるGakuNin RDMの一括処理機能

## Install and Usages

### Install as package
Change directory to the root of the project directory and run:
```cmd
python -m pip install .
```
`.` refers to the current working directory

### Usages

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
