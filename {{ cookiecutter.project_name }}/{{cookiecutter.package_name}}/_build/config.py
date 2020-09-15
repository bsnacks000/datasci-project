import os
import pathlib
import dotenv

PROJECT_NAME = '{{cookiecutter.package_name}}' ## XXX will be configured by cookiecutter

# global paths for the project directory...
ROOT_DIR = pathlib.Path(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
DATA_DIR = ROOT_DIR / 'data'
RAW_DATA_DIR = DATA_DIR / 'raw'
ENTRYPOINT_DATA_DIR = DATA_DIR / 'entrypoint'
CACHE_DIR = DATA_DIR / '.localcache'
MODELS_DIR = DATA_DIR / 'models'

REPORTS_DIR = ROOT_DIR / 'reports'
NOTEBOOKS_DIR = ROOT_DIR / 'notebooks'
{{cookiecutter.package_name}}_DIR = ROOT_DIR / '{{cookiecutter.package_name}}'

# load the access token
dotenv.load_dotenv(ROOT_DIR / '.env', verbose=True)
DROPBOX_ACCESS_TOKEN = os.environ.get('DROPBOX_ACCESS_TOKEN')
DROPBOX_APP_KEY = os.environ.get('DROPBOX_APP_KEY')
DROPBOX_APP_SECRET = os.environ.get('DROPBOX_APP_SECRET')
