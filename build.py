#!/usr/bin/env python

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
    "open-source-gis",
    "otevrena-geodata",
    "postgis-pokrocily",
    "postgis-zacatecnik",
    "qgis-pokrocily",
    "qgis-zacatecnik",
    "sphinx-template",
    "vugtk"
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
        curdir = os.path.abspath('./')
        os.chdir(os.path.join(SKOLENI_DIR, name))

        _update_git()
        _update_html()
        #_update_pdf()

        os.chdir(curdir)

    if repository in WORKSHOPS:
        build_repo(repository)


    elif repository == SPHINX:
        for workshop in WORKSHOPS:
            build_repo(workshop)

    resp = make_response('{"status":"success"}', 200)
    resp.headers['Content-type'] = 'application/json'
    return resp


def _update_git():
    subprocess.call(["git", "pull"])


def _update_html():
    subprocess.call(["make", "clean"])
    subprocess.call(["make", "html"])


def _update_pdf():
    subprocess.call(["make", "latexpdf"])
    file_name = glob.glob('_build/latex/*.pdf')[0]
    shutil.copy(file_name, '_build/html')


def _get_branch(data):
    ref = data['ref']
    return ref.split('/')[-1]

if __name__ == '__main__':
    app.run()
