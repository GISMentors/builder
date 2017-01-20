#!/usr/bin/env python

from __future__ import print_function

from flask import Flask
from flask import request
from flask import json
from flask import make_response
import subprocess
import glob
import re
import os
import shutil
import sys

os.environ['PYTHONPATH'] = '/var/www/opengeolabs/gismentors/build-env/lib/python2.7/site-packages'

SKOLENI_DIR='/var/www/opengeolabs/gismentors/skoleni/'
WORKSHOPS=(
    "geonetwork-zacatecnik",
    "geopython-english",
    "geopython-pokrocily",
    "geopython-zacatecnik",
    "geoserver-zacatecnik",
    "grass-gis-pokrocily",
    "grass-gis-zacatecnik",
    "isprs-summer-school-2016",
    "mapserver-zacatecnik",
    "open-source-gis",
    "otevrena-geodata",
    "postgis-pokrocily",
    "postgis-zacatecnik",
    "qgis-pokrocily",
    "qgis-zacatecnik",
    "vugtk",
)

WORKSHOPSEN=(
    "geopython-english",
    "isprs-summer-school-2016",
)

WORKSHOPSPDF=(
    "grass-gis-zacatecnik",
    "otevrena-geodata",
    "qgis-zacatecnik",
)

SPHINX = 'sphinx-template'

app = Flask(__name__)

@app.route('/')
def hello_world():
    return 'Hello World!\n'


@app.route('/build', methods=['POST'])
def build():
    data = json.loads(request.get_data())
    branch = _get_branch(data)

    if branch == 'master':
    	return _build_master(data)

    
def _build_master(data):
    repository = data['repository']['name']

    def build_repo(name):
        print("{sep}\nBuilding {repo}\n{sep}\n".format(repo=name, sep='*' * 80),
              file=sys.stderr)
        curdir = os.path.abspath('./')
        os.chdir(os.path.join(SKOLENI_DIR, name))

        _update_git()
        branch = 'en' if name in WORKSHOPSEN else 'master'
        _update_git_template(branch)
        _update_html()
        if name in WORKSHOPSPDF:
            _update_pdf()

        os.chdir(curdir)

    if repository in WORKSHOPS:
        build_repo(repository)

    elif repository == SPHINX:
        _update_git_template()
        for workshop in WORKSHOPS:
            build_repo(workshop)

    resp = make_response('{"status":"success"}', 200)
    resp.headers['Content-type'] = 'application/json'
    return resp


def _update_git():
    subprocess.call(["git", "pull"])


def _update_git_template(branch='master'):
    curdir = os.path.abspath('./')
    os.chdir(os.path.join(SKOLENI_DIR, SPHINX))
    print("SPHINX TEMPLATE BRANCH: {}".format(branch),
          file=sys.stderr)
    subprocess.call(["git", "checkout", branch])
    _update_git()
    os.chdir(curdir)


def _update_html():
    subprocess.call(["make", "clean"])
    subprocess.call(["make", "html"])


def _update_pdf():
    subprocess.call(["make", "latexpdf"])
    file_name = max(glob.iglob('_build/latex/*.pdf'), key=os.path.getctime)
    dest_file = '{base}.{ext}'.format(
        base='-'.join(os.path.basename(file_name).split('-', -1)[:-1]),
        ext='pdf'
    )
    shutil.copy(file_name, '_build/html/{}'.format(dest_file))

def _get_branch(data):
    ref = data['ref']
    return ref.split('/')[-1]

if __name__ == '__main__':
    app.run()
