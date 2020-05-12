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


    def upload_data(self, excludes=['.localcache', 'entrypoint']):
        """ Uploads any data from root of the data folder into the dropbox Apps/project/directory. Will exclude 
        any directories given to upload_data. 
        """
        _, local_path = self._syncable_local_subfolders.get('root') # get the rootpath
        responses = []
        for dn, dirs, files in os.walk(local_path):
            dirs[:] = [d for d in dirs if d not in excludes]
            for f in files:
                local_path = dn + '/' + f 
                dbx_path = '/' + local_path 
                print('uploading... ', dbx_path)
                with open(local_path, 'rb') as f:
                    res = self._dbx.files_upload(f.read(), dbx_path)
                    responses.append(res)
        return responses


    def download_data(self):
        """ Downloads all data from the dropbox project root into the local data folder.  
        """

        dbx_path, local_path = self._syncable_local_subfolders.get('root') # get the paths
        responses = []
        
        for entry in dbx.files_list_folder(dbx_path, recursive=True).entries:
            if isinstance(entry, dropbox.files.FolderMetadata):
                p = local_path / entry.path_lower.replace('/' + self._project_name, '')[1:]
                print('creating folder: ', p)
                pathlib.Path(p).mkdir(parents=True, exist_ok=True)
        
            elif isinstance(entry, dropbox.files.FileMetadata):
                p = local_path / entry.path_lower.replace('/' + self._project_name, '')[1:]
                print('downloading file: ', p)
                md = dbx.files_download_to_file(p, entry.path_lower)
                responses.append((md, f'bytes downloaded: {md.size}'))

        return responses 


@click.command() 
@click.option('-n', '--project-name', type=click.STRING, 
    help='Pull files into data/raw and data/models from dropbox. If none defaults to PROJECT_NAME')
def pull_from_dropbox(project_name):
    client = DropboxAPI(project_name)
    client.login() 
    client.download_data()


@click.command() 
@click.option('-n', '--project-name', type=click.STRING, default=None,
    help='Push files into data/raw and data/models from dropbox. If none defaults to PROJECT_NAME')
def push_to_dropbox(project_name):
    client = DropboxAPI(project_name)
    client.login()
    client.upload_data()


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

