from flask import Flask
from flask import request
from flask import json
import subprocess
import glob
import sre
import os
import shutil

SKOLENI_DIR='/home/skoleni/'
WORKSHOPS=(
        "vugtk",
        "geopython",
        "grass-gis-zacatecnik",
        "postgis-zacatecnik",
        "postgis-pokrocily",
        "otevrena-geodata",
        "open-source-gis",
        "grass-gis-pokrocily",
        "qgis-zacatecnik",
        "qgis-pokrocily"
)

SPHINX = 'sphinx-template'

app = Flask(__name__)

@app.route('/')
def hello_world():
    return 'Hello World!'

@app.route('/build', methods=['POST'])
def build():
    data = json.loads(request.get_data())
    branch = _get_branch(data)

    if branch == 'master':
        _build_master(data)


def _build_master(data):
    repository = data['name']

    def build_repo(name):
        curdir = os.path.abspath('./')
        os.chdir(os.path.join(SKOLENI_DIR, name))

        _update_git()
        _update_html()
        _update_pdf()

        os.chdir(curdir)

    if repository in WORKSHOPS:
        build_repo(repository)


    elif repository == SPHINX:
        for workshop in WORKSHOPS:
            build_repo(workshop)


def _update_git():
    subprocess.call(["git", "pull"])

def _update_html():
    subprocess.call(["make", "clean"])
    subprocess.call(["make", "html"])

def _update_pdf():
    subprocess.call(["make", "latexpdf"])
    file_name = os.path.basename(
        glob.glob(
            os.path.join('_build/latex/*.pdf', 'html/*.pdf'))[0]
    )
    shutil.copy(file_name, 'html')
    target_file_name = sre.sub('-([0-9]\.).*', '.pdf', file_name)
    target = os.path.join('html', target_file_name)
    source = os.path.join('html', file_name)
    if os.path.islink(target):
        os.unlink(target)
    os.symlink(source, target)


def _get_branch(data):
    ref = data['ref']
    return ref.split('/')[-1]

if __name__ == '__main__':
    app.run()

