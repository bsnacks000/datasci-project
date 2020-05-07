 #!/usr/bin/env python
# -*- coding: utf-8 -*-
from setuptools import setup, find_packages
import os 


######### NOTE this should be changed in cookie-cutter
NAME = '{{cookiecutter.package_name}}'
DESCRIPTION = 'This is boilerplate for project description'
############

with open('README.md') as f: 
    readme = f.read()

with open('HISTORY.md') as f:
    history = f.read()

with open('requirements.txt') as f:
    requirements_txt = f.read().split('\n')

test_requirements = [
    'pytest',
    'pytest-cov'
]

_requirements = [
    'jupyter>=1.0.0', 
    'dropbox',
    'click', 
    'python-dotenv',
    'flask-caching', 
    'nbdime', 
    'jupyter_contrib_nbextensions', 
    'ipywidgets'
]

requirements = requirements_txt + _requirements

# build the version from _version.py
here = os.path.abspath(os.path.dirname(__file__))
about = {}
project_slug = NAME.lower().replace("-", "_").replace(" ", "_")
with open(os.path.join(here, project_slug, '_version.py')) as f:
    exec(f.read(), about)


setup(
    name=NAME,
    description= '',
    version=about['VERSION'],
    long_description=readme,
    history=history,
    packages=find_packages(exclude=["*.tests", "*.tests.*", "tests.*", "tests", "scripts"]),
    include_package_data=True,
    install_requires=requirements,
    test_suite='pytest',
    tests_require=test_requirements,
    entry_points={
        'console_scripts': [
            'persist-notebooks=_{{cookiecutter.package_name}}_build_system.reports:persist_notebooks', 
            'push-to-dropbox=_{{cookiecutter.package_name}}_build_system.dropbox_api:push_to_dropbox',
            'pull-from-dropbox=_{{cookiecutter.package_name}}_build_system.dropbox_api:pull_from_dropbox', 
            'build-entrypoint=_{{cookiecutter.package_name}}_build_system.data:build_entrypoint', 
            'build-models=_{{cookiecutter.package_name}}_build_system.data:build_models', 
            'flush-dropbox=_{{cookiecutter.package_name}}_build_system.dropbox_api:flush_dropbox'
            # 'initialize-dropbox-project=_{{cookiecutter.package_name}}_build_system.dropbox_api:initialize_dropbox_project'
        ]
    }, 
    classifiers=[
        # Trove classifiers
        # Full list: https://pypi.python.org/pypi?%3Aaction=list_classifiers
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: Implementation :: CPython'
    ],
)