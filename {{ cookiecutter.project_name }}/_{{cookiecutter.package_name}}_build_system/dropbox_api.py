import dropbox 
from dropbox.exceptions import ApiError
from dropbox.files import FileMetadata

from .config import DROPBOX_ACCESS_TOKEN, PROJECT_NAME,\
     DATA_DIR, RAW_DATA_DIR, MODELS_DIR

import click 
import os 

import logging 
import sys
l = logging.getLogger(__name__)


class DropboxAPI(object):
    """ A wrapper around the dropbox API. Will use the ACCESS_TOKEN 
    provided in .env or passed in via __init__. 
    """ 

    def __init__(self, 
        project_name=None, 
        root_data_dir=None,
        raw_data_dir=None, 
        models_dir=None, 
        access_token=None):

        self._project_name = project_name or PROJECT_NAME
        self._access_token = access_token
        # these are the dropbox project path, local abspath for syncing
        self._syncable_local_subfolders = {
            'models': ('/' + self._project_name + '/models', models_dir or MODELS_DIR), 
            'raw': ('/'+ self._project_name + '/raw', raw_data_dir or RAW_DATA_DIR),
            'root': ('/' + self._project_name, root_data_dir or DATA_DIR)
        }

    def login(self):
        try:
            if self._access_token is None:
                assert DROPBOX_ACCESS_TOKEN is not None, 'An access token was not provided.'
                self._token = DROPBOX_ACCESS_TOKEN
            self._dbx = dropbox.Dropbox(DROPBOX_ACCESS_TOKEN)
       
        except AssertionError:
            raise        

        except Exception:
            l.exception('Failure logging into dropbox') 
            sys.exit(1)


    @property 
    def dbx(self):
        return self._dbx


    def flush_folder(self, subfolder):
        """ delete all contents of a project subfolder
        """
        dbx_path, _ = self._syncable_local_subfolders.get(subfolder) 

        entries = []
        for entry in self._dbx.files_list_folder(dbx_path).entries:
            print(f'deleting from {dbx_path}...  {entry.path_lower}')
            e = self._dbx.files_delete(entry.path_lower)
            entries.append(e)
        return entries


    def upload_data(self, subfolder):
        """ Uploads any data from the subfolder into the dropbox Apps/project/subfolder. 
        """
        dbx_path, local_path = self._syncable_local_subfolders.get(subfolder) # get the paths
        # print(dbx_path, local_path)
        responses = []
        filenames = [f for f in os.listdir(str(local_path))]
        print(filenames)
        for file_name in filenames: 
            f = local_path / file_name 
            if not os.path.isdir(f):
                dbx_file_path = dbx_path + '/' + file_name  
                print(f, dbx_file_path)
                with open(f, 'rb') as f:
                    res = self._dbx.files_upload(f.read(), dbx_file_path)
                    responses.append(res)
        return responses


    def download_data(self, subfolder):
        """ Downloads data from the subfolYder into the local data/subfolder. 
        """
        dbx_path, local_path = self._syncable_local_subfolders.get(subfolder) # get the paths
        responses = []
        for entry in self._dbx.files_list_folder(dbx_path).entries:
            if isinstance(entry, FileMetadata):
                print(entry)
                md = self._dbx.files_download_to_file(str(local_path) + '/' + str(entry.name), entry.path_lower)
                responses.append((md, f'bytes downloaded: {md.size}'))
        return responses


@click.command() 
@click.option('-n', '--project-name', type=click.STRING, 
    help='Pull files into data/raw and data/models from dropbox. If none defaults to PROJECT_NAME')
def pull_from_dropbox(project_name):
    client = DropboxAPI(project_name)
    client.login() 
    client.download_data('root')
    client.download_data('raw') 
    client.download_data('models')



@click.command() 
@click.option('-n', '--project-name', type=click.STRING, default=None,
    help='Push files into data/raw and data/models from dropbox. If none defaults to PROJECT_NAME')
def push_to_dropbox(project_name):
    client = DropboxAPI(project_name)
    client.login()
    client.upload_data('root')
    client.upload_data('raw') 
    client.upload_data('models')



@click.command()
@click.option('-n', '--project-name', type=click.STRING, default=None, help='Flush the data folders on dropbox')
def flush_dropbox(project_name):
    message = 'This will delete the contents of the project data folders on dropbox! Your local raw files will remain intact... Continue?'
    if click.confirm(message, abort=True):
        if click.confirm('Really delete the things???', abort=True):
            client = DropboxAPI(project_name)
            client.login()
            client.flush_folder('raw')
            client.flush_folder('models')

