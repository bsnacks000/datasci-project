""" Base classes to work with the data folder
"""
from .config import RAW_DATA_DIR, ENTRYPOINT_DATA_DIR,\
    CACHE_DIR, MODELS_DIR
import pathlib
from flask_caching import Cache
from . import pathutils

import sys
import collections
import click 
import functools 
import inspect
import os
import json 
import csv
import shutil
import pickle
import joblib
import datetime
import pandas as pd 
import sklearn


class Parser(object):

    def read(self, filepath):
        raise NotImplementedError 

    def write(self, filepath, data):
        raise NotImplementedError


class JsonParser(Parser):

    def read(self, filepath):
        with open(filepath, 'r') as f:
            data = json.load(f)
        return data 

    def write(self, filepath, data):
        pathutils.touch_filepath(filepath)
        with open(filepath, 'w') as f:
            json.dump(data, f)


class PandasCSVParser(Parser):

    def read(self, filepath):
        return pd.read_csv(filepath)
    
    def write(self, filepath, data):
        pathutils.touch_filepath(filepath)
        if not isinstance(data, pd.DataFrame):
            data = pd.DataFrame.from_records(data)
        data.to_csv(filepath, index=False)


class PickleParser(Parser):

    def read(self, filepath):
        return pickle.load(open(filepath, 'rb'))

    def write(self, filepath, data):
        pathutils.touch_filepath(filepath)
        pickle.dump(data, open(filepath, 'wb'))


class SklearnPklParser(Parser):

    def read(self, filepath):
        return joblib.load(open(filepath, 'rb'))

    def write(self, filepath, model):
        pathutils.touch_filepath(filepath)
        joblib.dump(model, open(filepath, 'wb'))
        # print(filepath)
        # NOTE this metadata will only really work with sklearn built ins
        # other parsers need to be implemented for other libraries. 
        # This API should be extended and these classes globally registered...
        fpath = str(filepath).replace('model.pkl', 'metadata.json')
        with open(fpath, 'w') as f:
            json.dump({
                'sklearn-version': sklearn.__version__, 
                'model-name': str(filepath).split('/')[-1]
            }, f)


class _DataManager(object):
    """ Manages the data transfer between raw/ entrypoint/ and models/ folder by providing 
    a decorator API and registry. This object should be treated as a singleton. 
    """
    _processor_registry = collections.OrderedDict()
    _modeler_registry = collections.OrderedDict()
    _parsers = {
        'json': JsonParser(), 
        'csv': PandasCSVParser(), 
        'model.pkl': SklearnPklParser(), 
        'data.pkl': PickleParser()
    }
    
    def __init__(self, raw_folder=None, entrypoint_folder=None, models_folder=None):
        self._raw_folder = raw_folder or RAW_DATA_DIR 
        self._entrypoint_folder = entrypoint_folder or ENTRYPOINT_DATA_DIR 
        self._models_folder = models_folder or MODELS_DIR 


    def _load_data(self, filenames, folder):
        """ loads the input data in filename order
        """
        data = []
        for f in filenames:
            parser = self.get_parser(f)
            d = parser.read(folder / f)
            data.append(d)
        return data 


    def _write_data(self, filenames, folder, *data):
        """ writes the cleaned data in filename order
        """
        for i, f in enumerate(filenames):
            parser = self.get_parser(f)
            parser.write(folder / f, data[i])


    def _check_output(self, data, filenames):
        """ Checks that the output lines up with the provided output filenames. This is
        the best we can do in python to make sure we're going to have a successful write.
        """

        if isinstance(data, tuple):  # if we have multiple return vals check the thing mathces
            if len(data) != len(filenames):
                raise ValueError(f'''Length of cleaned data ({len(data)}) 
                    does not match length of output filenames ({len(filenames)})''')
        else:
            if len(filenames) != 1: # if we have a single return val check we only have 1 filename to write
                raise ValueError(f'''Output of cleaned data was an object but 
                    a tuple of length ({len(filenames)}) was expected''')


    def _do_process(self, registry, source_folder, target_folder):
        """ blows through a registry, pulls in material from source folder, does calcs and 
        writes outputs to a target folder.
        """

        for func, fnames in registry.items():
            input_filenames, output_filenames = fnames  
            input_data = self._load_data(input_filenames, source_folder)
            processed_data = func(*input_data)
            # print(processed_data)
            self._check_output(processed_data, output_filenames)
            if not isinstance(processed_data, tuple):
                processed_data = (processed_data,)    
            self._write_data(output_filenames, target_folder, *processed_data)
            

    def _check_argspec_conditions(self, func, filenames):
        """ helper that checks the argspec of a function and assures we only have 
        args and that 
        """
        argspec = inspect.getfullargspec(func)
        conditions = [
                len(argspec.args)==len(filenames),   # postitional args should match num of filenames
                argspec.varargs is None,  # everything else blank
                argspec.varkw is None, 
                argspec.defaults is None, 
                len(argspec.kwonlyargs) == 0, 
                argspec.kwonlydefaults is None
            ]
        if not all(conditions):
            raise TypeError('Arguments must match length raw_filenames, contain no defaults \
                and except no varargs or kwargs')
    

    def available_entrypoints(self):
        """ Return a list of posix paths from the entrypoint folder.
        """
        return pathutils.build_subpaths(self._entrypoint_folder, accept=['*.csv', '*.json', '.data.pkl'])
        
    
    def available_models(self):
        """ Return a list of posix paths from the models folder
        """
        return pathutils.build_subpaths(self._models_folder, accept=['*.csv', '*.json', '.data.pkl', '.model.pkl'])
        

    def available_raw_data(self):
        """ Return a list of posix paths from the raw folder
        """
        return pathutils.build_subpaths(self._raw_folder, accept=['*.csv', '*.json'])
    

    def get_parser(self, filename):
        """ a helper to grab the parser by file extension.
        """
        if str(filename).endswith('json'):
            return self._parsers['json']
        
        elif str(filename).endswith('csv'):
            return self._parsers['csv']

        elif str(filename).endswith('model.pkl'):
            return self._parsers['model.pkl']

        elif str(filename).endswith('data.pkl'):
            return self._parsers['data.pkl']
        
        else:
            raise TypeError('Parser extension not found')


    def clean(self, raw_filenames=[], cleaned_filenames=[]):
        """ registers a user defined cleaning method. When the process method 
        is executed on the data_manager it will read files in from raw data 
        and execute each method to create output data files in entrypoint to be 
        used for analysis
        """
        assert len(raw_filenames) >= 1 or len(cleaned_filenames) >= 1, 'filenames must be >= 1'
        def _wrapper(func):
            self._check_argspec_conditions(func, raw_filenames)
            self._processor_registry[func] = (raw_filenames, cleaned_filenames)
        return _wrapper


    def model(self, entrypoint_filenames=[], model_filenames=[]):
        """ registers a user defined modeling mdethod. When the method is executed 
        on the data manager it will read files from entrypoint/ and execute each method 
        to create output data files. 
        """
        assert len(entrypoint_filenames) >= 1 or len(model_filenames) >= 1, 'filenames must be >= 1'
        def _wrapper(func):
            self._check_argspec_conditions(func, entrypoint_filenames)
            self._modeler_registry[func] = (entrypoint_filenames, model_filenames)
        return _wrapper


    def update_entrypoint(self):
        """ Create or update the entrypoint data by executing all the registered 
        cleaning methods. This is an update or create operation. 

        Here are the rules for this API:
        1. The function should contain the same number of inputs as raw_filenames[]. 
        2. The function should return the same number of args as cleaned_filenames[]
        3. No kwargs... the script should be self contained 

        During an update if any files in raw/ are not included in the cleaning script
        or no cleaning functions were registered then it simply copies the raw 
        files into entrypoint. We assume in this case that the cleaning code is not registered
        and only exists in the project notebook files and dynamically via the .localcache 

        For example... for raw/a.csv raw/b.csv raw/c.csv  
        @data_manager.clean(['a.csv', 'b.csv'], ['d.csv'])
        def make_d(a, b):
            <<< do fancy things with a and b to make d >>>
            return d 

        Will create entrypoint/d.csv and entrypoint/c.csv 
        
        For simplicity we only handle csv and json. Pretty much all data can be represented in either
        of these formats.
        """

        raw_list = self.available_raw_data()
        if len(raw_list) == 0: # no files in raw data
            return 

        if len(self._processor_registry) == 0: # no registered cleaning methods - just move everything over
            print('No registered cleaning methods found... copying over raw data')
            shutil.rmtree(self._entrypoint_folder)   # flush and copy
            shutil.copytree(self._raw_folder, self._entrypoint_folder)
            gk = pathlib.Path(self._entrypoint_folder) / '.gitkeep'
            gk.touch()
            return

        try:
            raw_fnames = []
            for p in raw_list: 
                _, after = pathutils.path_splitter(str(p), after='raw')
                raw_fnames.append(after)
            
            raw_set = set(raw_fnames)  # all the raw files
            s = set()  # all the raw files being processed
            for func, fnames in self._processor_registry.items():
                raw, _ = fnames 
                for r in raw:
                    s.add(r)

            diff = list(raw_set - s)  # diff are the raw files that aren't being cleaned... we can transfer these
            print('Raw files not being cleaned: ', diff)
            for d in diff:
                d_src_path = self._raw_folder / d  
                d_dest_path = self._entrypoint_folder / d
                shutil.copy2(d_src_path, d_dest_path)

            self._do_process(self._processor_registry, self._raw_folder, self._entrypoint_folder)
        
        except Exception as err:
            shutil.rmtree(self._entrypoint_folder)
            os.makedirs(self._entrypoint_folder)
            gk = pathlib.Path(self._entrypoint_folder ) / '.gitkeep'
            gk.touch()
            raise  


    def update_models(self):
        """ This works similar to update_entrypoint but works for models. It uses the entrypoint/ data 
        does a lookup and pipes 
        """
        
        entrypoint_list = self.available_entrypoints()
        if len(entrypoint_list) == 0:
            return 

        if len(self._modeler_registry) == 0:  # we simply return if no model pipelines are registered.
            print('No registered modeling methods found...')
            return

        try:
            for entry_name in entrypoint_list:  # validate extensions
                entry_name = str(entry_name)
                assert entry_name.endswith('.json') \
                    or entry_name.endswith('.csv') \
                    or entry_name.endswith('data.pkl'), f'Invalid file extension: {entry_name}'
            
            # NOTE we don't need the extra logic like update_entrypoint to "transfer" files that aren't being processed
            # We assume that if you did not register entrypoint to a model then you don't want to model it  
            self._do_process(self._modeler_registry, self._entrypoint_folder, self._models_folder)

        except Exception as err:
            shutil.rmtree(self._models_folder)
            os.makedirs(self._models_folder)
            gk = pathlib.Path(self._models_folder) / '.gitkeep'
            gk.touch()
            raise


def fetch_data(filename, folder_name='entrypoint'):
    """ Fetch a dataset from entrypoint or a model from models.
    """
    from {{cookiecutter.package_name}}.registry import data_manager # lazy import singleton to avoid module issues

    if folder_name == 'entrypoint':
        fpath = data_manager._entrypoint_folder / filename 
    elif folder_name == 'models':
        fpath = data_manager._models_folder / filename
    else:
        raise TypeError('Can only read from entrypoint or models folders')

    parser = data_manager.get_parser(filename)
    return parser.read(fpath)


def create_cache():
    """ Configure an instance of the flask_caching.Cache for use
    with the filesystem with reasonable defaults. We act clever and 
    realize that flask is just an object and we can fake 
    """
    class _App(object):
        config = {}

    cache_config = {
        'CACHE_TYPE': 'filesystem',
        'CACHE_DEFAULT_TIMEOUT': 60 * 60 * 24 * 7,
        'CACHE_THRESHOLD': 100,
        'CACHE_DIR': CACHE_DIR
    }
    return Cache(app=_App(), with_jinja2_ext=False, config=cache_config)


def create_data_manager():
    """ Return an instance of data manager given folders. If these are set to none will 
    use the project default.
    """
    return _DataManager()




@click.command()
def build_entrypoint():
    """ Builds (or re-builds) the entrypoint folder by flushing and then 
    running any registered cleaning methods on the raw data folder. 
    """
    try:
        from .. import registry   
    except ImportError as err:
        print(str(err))
        print('Could not import data_manager from {{cookiecutter.package_name}}.registry.')
        sys.exit(1)
    
    registry.data_manager.update_entrypoint()


@click.command()
def build_models():
    """ Builds (or rebuilds) the models folder by flushing and running 
    any registered modeling methods on the entrypoint data.
    """
    try:
        from .. import registry      
    except ImportError as err:
        print(str(err))
        print('Could not import data_manager from {{cookiecutter.package_name}}.registry.')
        sys.exit(1)
    
    registry.data_manager.update_models()