# Cookiecutter Data Science

_A logical, reasonably standardized, but flexible project structure for doing and sharing data science work._

This is a fork of http://drivendata.github.io/cookiecutter-data-science/ with some tweaks and modifications. 

* A build system that generates reports from jupyter notebooks using pre-commit hooks.  
* Dropbox sync of raw data and models using Oauth instead of AWS. 
* A data pipeline that supports multiple caching layers. 
* A data cleaning API that can be used to register and develop pre-preprocessing pipelines
* README and documentation focused on outlining research methodology

### Requirements to use the cookiecutter template:
-----------
 - Python 3.5 +
 - [Cookiecutter Python package](http://cookiecutter.readthedocs.org/en/latest/installation.html) >= 1.4.0: This can be installed with pip by or conda depending on how you manage your Python packages:

``` bash
$ pip install cookiecutter
```

or

``` bash
$ conda config --add channels conda-forge
$ conda install cookiecutter
```


### To start a new project, run:
------------

    cookiecutter https://github.com/bsnacks000/cookiecutter-data-science


### The resulting directory structure
------------

The resulting directory structure can be found in the repo GUIDELINES.md


### Installing development requirements
------------

    pip install -r requirements.txt

### Running the tests
------------

    py.test tests
