""" Use these singletons and functions to manage your data.
"""
# DO NOT MODIFY THIS MODULE!

from .._build.data import create_data_manager,\
    create_cache, fetch_data

data_manager = create_data_manager()
localcache = create_cache()

# register functions to avoid a circular import 
from . import clean 
from . import model 