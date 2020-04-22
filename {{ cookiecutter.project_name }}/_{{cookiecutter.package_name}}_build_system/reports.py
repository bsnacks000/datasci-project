import click 
import os
import sys
import subprocess

from .config import REPORTS_DIR, NOTEBOOKS_DIR


@click.command()
def persist_notebooks():
    """ Use nbconvert to check notebooks into reports using html. All notebooks with the 
    extension <name>.report.ipynb will be checked in.
    """ 
    filepaths = [str(NOTEBOOKS_DIR / n) for n in os.listdir(NOTEBOOKS_DIR) if n.endswith('report.ipynb')]
    if len(filepaths) == 0:
        print("No ipynb filepaths found. Any notebooks you want to persist as html must end with the 'report.ipynb' extension")
        sys.exit(0)

    filepaths_str = filepaths.pop()

    print(f'Converting the following notebooks: {filepaths_str}')
    cmd = f'jupyter nbconvert {filepaths_str} --to=html --execute --log-level=INFO --output-dir={REPORTS_DIR}'

    subprocess.run(cmd, shell=True, check=True)


