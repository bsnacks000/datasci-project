# Data Science Project 


This is based on a fork of http://drivendata.github.io/cookiecutter-data-science/ with some tweaks and modifications. 

* A build system that generates reports from jupyter notebooks using pre-commit hooks.  
* Dropbox sync of raw data and models using Oauth. 
* A data pipeline that supports multiple caching layers. 
* A customizable data cleaning and modeling API that supports reproducability and uni-directional data flow.
* README and documentation focused on outlining research methodology


Read GUIDELINES.md for more details.

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

    cookiecutter https://github.com/bsnacks000/datasci-project


### The resulting directory structure
------------

The resulting directory structure can be found in the repo GUIDELINES.md
