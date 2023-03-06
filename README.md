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
View helper
```cmd
grdmcli --help
```

```text

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
