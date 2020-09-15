# Usage and Research Guidelines
---------------------------------

This little build system for data science projects was directly forked from https://github.com/drivendata/cookiecutter-data-science. The principles are based on their [blog article](http://drivendata.github.io/cookiecutter-data-science/) for reproducible collaborative data science projects. We've made some tweaks to the project
structure and developed a build system that suits our needs, but the basic principles from this article should be followed. 




## How to Use this Repo and Best Practices
-----------

The directory structure of your new project looks like this: 

```
├── LICENSE
├── Makefile           <- Makefile controller with development commands
├── README.md          <- The top-level README for developers using this project.
├── data
│   ├── .localcache/        <- Where the cache API writes to (local only)
│   ├── models/             <- Where the data_manager.model API writes to (synced to cloud)
│   ├── entrypoint/         <- Where the data_manager.clean API writes to (local only).
│   ├── raw/                <- The original, immutable data dump (synced to cloud)
|   └── data-dictionary.md  <- Documentation of the raw data and models
│
│
├── notebooks           <- Jupyter notebooks. Any nb ending .report.ipynb gets generated as 
│                         a report. Any nb starting with _ does stays out of version control.
│                         
│
├── scripts/            <- Standalone scripts (optional). User defined utilities for moving data
│                         into the raw folder. It is recommended to write as CLIs.
│
├── reports/            <- Generated analysis as HTML, PDF, LaTeX, etc.
│   └── figures/        <- (Optional) static graphics and figures to be used in reporting
│
├── requirements.txt    <- The requirements file for reproducing the project environment. This is 
│                         seperate from the ``setup.py`` which contains requirements for the 
│                         build system and should not be modified.
│
├── _{{cookiecutter.package_name}}_build_system     <- APIs and tooling for the build-system. DO NOT MODIFY!!
│
│
├── {{cookiecutter.package_name}}       <- User defined code for this project. 
│   ├── __init__.py                     <- Contains public imports from _build_system package that can be used
│   ├── _version.py                     <- package version data (bump this and git tag to create dev cycles)
|   ├── _build                          <- a private package that contains the build system tooling
│       └── __init__.py 
|       └── ...
|     ...                         <- Any developed python code for maintaining reproducibilty using APIs in build system
│
│
└── HISTORY.md            <- for tracking changes to the project package
```

This is very similar to the original cookie-cutter but we've added some features to improve the build system which will be outlined below in detail.



### Installation and Overview

To install a fresh project add new packages to requirements.txt, initialize a new git repository, create a virtual environment with your method of choice and run. Note that if you are adding from github you should add it as ``<package_name> @ git+<github_link>`` since we are using setuptools.

```{bash}
$ make install
```

This will install your requirements.txt, install the build-system, inject custom git-hooks and enable nbdime to help with ipynb merging. 

If you can't or don't want to use dropbox you're done! Note however that any files in the data folder will not enter version control... because they don't belong there!!

If you do want to use dropbox then you should supply a .env file with an API access token to as outlined in .env-example. This allows you to sync your raw data and models to a dropbox folder. 

If you are creating a new project and want to sync to dropbox run
```{bash}
$ make push-to-dropbox
```
This will create a new dropbox project in your Apps/ folder that corresponds to this repository and upload anything in the root, raw and models folders to dropbox. 

If you are a cloning an ongoing project and want to sync data from dropbox you can run once you've installed the above commands.
```{bash}
$ make pull-from-dropbox
``` 
This will pull raw data and models into your local project and populate the entrypoint folder by running any registered cleaning methods (more on this below)

If you want to generate html reports from project notebooks you can run 
```{bash}
$ make persist-notebooks
```

This builds any notebooks in that folder with the extension ``.report.ipynb`` into html. This guarantees that any javascript is captured and can be deployed to a fileserver or viewed locally. In order to generate pdfs or other reports you're on your own since it requires quite a bit of work to extract and encode static files. 

Note that ``persist-notebooks`` is also run using git's ``pre-commit`` hook so that on every commit any reports are rebuilt. If you want to disable this simply remove the ``pre-commit`` script from your ``.git/hooks/`` folder.   


### Workflow

Okay great, its setup but what's the point? The main takeaway is that this setup helps enforce good practices for making data science projects reproducible by providing APIs that support a workflow.

Here are some basic principles that we have in mind:

1. Raw data must always be immutable. 
2. Data processing can and should evolve but must flow in one direction.
3. Jupyter Notebooks are invaluable tools... Don't abuse or misuse them!
4. The entire pipeline should always be independent, reproducible and testable. 
5. A data science project should always be governed by a clearly defined research purpose and set of goals. 


As the original article points out some of these pieces are unfortunately social contracts. And since we are working in Python (and maybe R) we can easily get around these things if wanted to. The ``data/`` folder is not a database and the ``_{{cookiecutter.package_name}}_build_system`` package private API is not truly off limits but that doesn't mean we can't agree to treat these as such. 

To this end we've created a simple ``DataManager`` Python API and a set of best practices to help us solve issues 1-4 and have some boiler plate to provide some structure for issue 5. 


### Raw Data is Immutable

The original cookie-cutter project talks about this a great deal and we agree. We will treat the ``data/`` folder for these projects as a sacred place. We should only interact the data in subfolders via the ``make`` utilities to assure that the data files in there are in sync with our code. We will also only ever upload to cloud via the same ``make`` utilities. 

Data streams added to ``data/raw`` should __NEVER__ be altered once they enter into a project, whether we code a script to do it or place the files there ourselves. Our spec outlines that these be either ``csv`` or ``json`` files created independently of any code that would exist inside a notebook or the project Python package. We figure that all data can be represented in either format so the bare minimum is that some raw data stream must contain either one of these formats. 

We supply a ``scripts/`` folder that can be used to inject raw data streams into the project folder if you want to keep any a-priori data collection code alongside the project, but we __NEVER__ populate raw data from inside ``notebooks/`` or ``{{cookiecutter.package_name}}``.  


### Unidirectional Data Flow

The ``data/`` folder can not be a free-for-all for this workflow to function correctly. If a dev allows themselves to upload random files in random folders from random scripts and notebooks it obscures intention and can lead to bugs during collaboration. How many times has someone moved a file on you in a project and caused the whole thing to break? Or you changed a cell in a notebook that persisted a file called "data-v1-2020-blahblah.csv" that only worked with a particular function in "my-awesome-notebook-v17-a-42.ipynb", but then you accidently opened the wrong version and ran the thing twice and copied in the wrong file and etc. etc. etc....

Data science is a chaotic (or creative depending on your stance) endeavor. But data processing should ultimately be rigourous. Luckily it is the part of the data science workflow that can be easily modeled. Our system includes a "chain" of folders which create entry and exit points for different steps in the development process. This is similar to the original build, but we parsed it down to operations that can be directly controlled via a decorator style API we've developed to work directly with ``make`` utilities to give the dev more flexibility. If utilized correctly, once pre-processing and modeling functions are fully developed they simply become part of the build. 

```
├── data
│   ├── .localcache/        
│   ├── models/             
│   ├── entrypoint/         
│   ├── raw/                
```

Our data flows from ``raw/`` to ``entrypoint/`` to ``models/`` via a registry API that hooks directly into the Makefile commands, with ``.localcache`` used more flexibly throughout for optimization and convenience via memoization and/or explicit caching.

Here's an overview of how this works. Say we load three raw data streams into the ``raw/`` folder and we want to do some processing on two of them in order to create a new dataset in ``entrypoint/`` before we model. The third we want to use directly because its already clean or maybe we're using some weird ensemble learning stack and need it go into our pipeline seperately. 
```python
# We're in {{cookiecutter.package_name}}.registry.clean.py

@data_manager.clean(['a.csv','b.csv'], ['d.csv'])
def make_d_from_a_and_b(my_a, my_b):
    # ...fancy processing here ...
    return my_d
```

By running ``make entrypoint`` the build system will automatically attempt to process ``a.csv`` and ``b.csv`` to make ``d.csv`` and persist it in the entrypoints folder. Furthermore because ``c.csv`` exists in the ``raw/`` folder but is not a part of the user defined pre-processing pipeline, it is simply just carried over and is available. So ``entrypoint/`` will contain ``c.csv`` and ``d.csv``. 

This is a key piece because it does not make any assumptions about the _state_ of the raw data. Raw data is not neccesarily _dirty_ data, though most data scientists would say that you usually need to tidy up at least a few things before trying to model something. Whether you do that using our API or somewhere else is up to you, but once it enters this system it is guaranteed to flow only one way.   

If a file in ``raw/`` is not registered to a cleaning method then it will simply be carried over to ``entrypoint/`` for you to use as you see fit. If there was another method registered say:

```python
@data_manager.clean(['b.csv','c.csv'], ['e.json', 'f.data.pkl'])
def make_e_and_f_from_b_and_c(my_b, my_c):
    # ...fancy processing here ...
    return my_e, my_f
```

Now that this method is also registered,  ``c.csv`` would no longer be considered an entrypoint candidate since it is being processed. The ``entrypoint/`` folder would now contain ``d.csv``, ``e.json`` and ``f.data.pkl``. Our spec also allows ``pkl`` files at this stage since they have been processed and that might be more convenient in some cases. They must be written with the ``.data.pkl`` extension or they will not be recognized by our parser.

Note that the input and output are mapped directly to input and output return values. This is checked at run time and will cause the build to fail if there is a mismatch.

Methods are run in the order they are declared within the module.
```python 
@data_manager.clean(['a.csv', 'c.csv'], ['d.csv'])
def make_d_from_a_and_c(a, c):
    # ... fancy processing here ... 
    return d
```
This will overwrite ``d.csv`` since this method was declared later. 

The ``@data_manager.model`` decorator works identically to the clean API except that it only excepts data from the ``entrypoint/`` folder and writes binary models to the ``models/`` folder. 

```python
@data_manager.model(['d.csv'], ['regression.model.pkl'])
def make_some_model(d_data):
    # ... fancy data science things here ...
    return model
```
Here ``regression.model.pkl`` is saved to the ``models/`` folder. We'll automatically save metadata as json that contains the model name and version info. Depending on your needs you probably want to export any training/testing data for correctly reproducing the model as either pickle, csv or json.

We have a built in parser for ``scikit-learn`` though there are plans to extend this with the [mlflow](https://www.mlflow.org/docs/latest/index.html) package to help in persisting production level models with metadata. The parser interface is extremely simple and hooks for other Python ML libraries such as Keras and XGBoost will eventually be added.

A key thing to notice is that nowhere is the user actually writing directly to the data folder. Instead we use the ``data_manager`` API to do this and just handle the processing. This assures the integrity of the data as it moves through the pipeline. 

A final note is the placement of these modules in {{cookiecutter.package_name}}. The ``registry`` package should not be removed since it is used as a hook in the build system for ``make entrypoint`` and ``make models``. If this package is removed or the ``__init__.py`` module altered there is a good chance you will break the build system. Only the provided ``data_manager`` singleton should be used to decorate cleaning methods. 

If more modules are needed they should be placed into the ``registry`` package and imported into the ``__init__.py`` underneath the ``data_manager`` and ``localcache`` instances to avoid circular import and ensure that the decorators register the correct functions.

### Jupyter and Reproducibility 

Jupyter notebooks are pretty great but they should not be the beginning and end of a project. Being undisciplined in the development of a notebook based project will at best lead to something disorganized and difficult to reproduce. We've seen a lot of projects that start out with good, clear intentions and reasonable goals, end up looking something like this...

```
├── my-project
│   ├── .ipynb_checkpoints/
│   ├── data.csv
│   ├── data-v2.csv
│   ├── data-v3-test.csv
│   ├── My Notebook (Version1).ipynb
│   ├── My Notebook (Version1)(1).ipynb
│   ├── My Other Notebook-v1_with_modeling.ipynb
│   ├── My Other Other Notebook-v1-FINAL(V1).ipynb
│   ├── other-data.json
│   ├── other-data(CLEAN).json
│   ├── other-data(CLEAN)(1).csv
│   ├── test-model.ipynb
    ...          
```

We agree with [drivendata](http://drivendata.github.io/cookiecutter-data-science/) when they say that notebooks are exploratory tools for communication, should maintain a sense of ownership and implement consistent naming conventions. There should not be directories full of notebooks used as dumping grounds for poorly or partially written scripts. On the flip side, they are also not full-blown interactive web applications. 

Ideally they should be focused on implementing a particular idea with the data, be well documented using markdown and follow a clear naming convention that provides a level of ownership to the work. This is especially important when collaboration needs to happen within the same project since notebooks are very difficult to version control. Merge conflicts between notebooks are sometimes impossible to conventionally resolve. 

That being said, notebooks are extremely useful and can be used in development if collaborators keep disciplined. We've added some features into this build-system to help assure that if a user is developing alot in notebooks that they can keep both the data and versioning under control. 

Firstly, we automatically inject [nbdime](https://github.com/jupyter/nbdime) into ``.gitattributes`` to help resolve merge conflicts between notebook versions that might be modified on different branches or by different users. 

We also define a hierarchy of notebooks. Any notebook extension that ends with ``.report.ipynb`` will automatically be generated into html using either the ``make persist-notebooks`` command or before each commit. This script is injected into ``.git/hooks/`` during ``make install`` and creates a pre-commit hook that assures that any reports are updated. These should be thought of as the "final" bit you want to write to proove your point.

Other notebooks are considered "development" in that they will be version-controlled using both .ipynb_checkpoints and git. This is where rough development work can take place and devs can collab... Pipelines can be tested, pre-processing steps developed, models trained and analyzed. Its ok if its a little sloppy...it's not official. Finally, any notebooks prefixed with a ``_`` will not be version controlled. This allows you to develop freely and independently without cluttering up the workspace for everyone involved. 

Please, please please... __DO NOT COPY PASTE CODE__ between notebooks. That is what the project package is for. Any functions or classes that handle visualization or an intermediate part of the pipeline can and should be implemented within the package. I would argue that almost _all_ code should eventually make its way into modules and loaded into the notebooks. It makes the project even more transparent and extremely easy to unittest. At the very least, long notebook scripts should be broken down into sets of static functions, heavily documented and placed in the top cell away from the "script" that is being run.  

A final key agreement, possibly the most important, that needs to be mentioned is the read-only nature of the ``data/`` folder when used in conjunction with notebooks. Like working in the project package above, under no circumstances should the user write directly to any parts of the ``data/`` folder. It should be treated as __READ-ONLY__. We provide two special functions that can be imported from ``{{cookiecutter.package_name}}.registry`` to fetch data from both the ``entrypoint`` and the ``models`` subfolders. Only the build-system is allowed to write to these folders via the decorator API mentioned above. 

The user can however freely write to the ``localcache`` object provided in ``{{cookiecutter.package_name}}.registry`` anywhere in the project package or notebooks. This is mainly for the purposes of optimization and memoization. In some cases it may be used to create ad-hoc datastores. It is simply a [flask-caching](https://flask-caching.readthedocs.io/en/latest/) object configured to use the file system with reasonable defaults.  

### The Importance of Research Goals

Finally its important that each project have a clearly defined set of research goals and/or specs and that both the code and the models/notebooks/reports are working together to achieve these common goals. The granularity for which you define a "project" is ultimately based on the domain-specifc problem you're trying to solve. 

We've provided some boilerplate (and an explanation below) of what we think are important when developing a project from a research perspective.  


### TLDR; 

Here are the basic rules to follow so that this setup might hopefully help you be more productive... 

* Treat the ``data/`` folder like you would a production database. Don't abuse it and only interact with it indirectly.  
* Raw data streams are immutable. Do not delete anything in there that you commit nor alter the schema or data itself. 
* Entrypoint data can be derived from the raw data using the ``data_manager`` API. Think of this as production level pre-processing that helps assure reproducibility. It is the actual data used for the project and should evolve dynamically alongside the work. 
* Models are ultimately derived from the entrypoint data using the ``data_manager`` API. This should be the final step in making production models for use in reports or the greater world. 
* If you need to write data from within the ``notebooks/`` or project package use the ``localcache``. Do not ever write to the ``data/`` folder directly.  
* Always use the ``Makefile`` to sync project data upstream and build your local ``data/`` folder. Treat the _{{cookiecutter.package_name}}._build package as private.
* Never directly consume an outside data stream within the project. All data streams should be collected stored as ``json`` or ``csv`` in the raw data folder.
* If you feel the need to keep your data collection work with the project use the ``scripts/`` folder. These should be completely independent of any project code.  
* Do not copy and paste code between notebooks. Thats what project packages are for... if you find yourself reusing the same piece of code create a module level function or class-based API within the project package and import the functionality into your notebooks.
* Use the ``make reports`` feature with git hooks to assure that your generated html reports are always up to date with any changes.
* Keep rough notebooks out of version control by appending an underscore to the notebook. Be nice to your collaborators and don't make a mess.
* Treat your project_package as a library. Use git to tag releases and write unittests for any business logic used by the decorator API and your project notebooks.
* Make sure the project is focused on clearly defined research goals and specs that are well planned in advance.



### Example 

* An example demonstrating the decorator API and commands can be found [here](https://github.com/bsnacks000/datasci-example)




## Research README fill in the blanks
-------

It’s important to be clear about what exactly is being accomplished by doing the analytics, as well as why. It helps the researcher stay on track and avoid tangents, and it helps to communicate to others what is being done. In formal research this is typically done in the research proposal phase - before any other work begins.

The README.md in the root of this project should be filled in accordingly for every project.


#### Author(s):

Put your freaking name on it!


#### Research Question (& optional, hypothesis): 

This may be the most important part. Coming up with a good research question is tricky - https://www.scribbr.com/research-process/research-questions/ . Basically, you want something that is clear and specific and feasible to answer with resources and time at the disposal of the project. It provides direction and a clear stopping point to the project.

#### Background / literature review:

Why are we doing this research / what are we gaining from doing it. 
    What has already been done (by us and others), and what were the key takeaways that help us?

#### Proposed methodology:

It helps to think through how you would want to approach the problem to see if it’s feasible - even if in the end the approach gets revised. 
    What data sources and methods do you plan to use / what are the advantages and limits?

#### Bibliography:

Keep adding to the list of sources used so that it’s all in one place.






