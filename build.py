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

os.environ['PYTHONPATH'] = '/var/www/opengeolabs/gismentors/build-env/local/lib/python2.7/site-packages'
os.environ['PYTHONPATH'] += ':/var/www/opengeolabs/gismentors/build-env/lib/python2.7/site-packages'

SKOLENI_DIR='/var/www/opengeolabs/gismentors/skoleni/'
WORKSHOPS=(
    "basic-data-processing-workshop",
    "geonetwork-zacatecnik",
    "geopython-english",
    "geopython-pokrocily",
    "geopython-zacatecnik",
    "geoserver-zacatecnik",
    "grass-gis-pokrocily",
    "grass-gis-zacatecnik",
    "grass-gis-workshop-jena-2018",
    "grass-gis-irsae-winter-course-2018",
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
    "grass-gis-workshop-jena-2018",
    "grass-gis-irsae-winter-course-2018",
    "yungo-plugins",
)

WORKSHOPSPDF=(
    "postgis-zacatecnik",
    "grass-gis-zacatecnik",
    "otevrena-geodata",
    "qgis-zacatecnik",
    "qgis-pokrocily",
)

BRANCHES = {
    "qgis-zacatecnik" : ['release_2_18', 'release_2_14'],
    "qgis-pokrocily"  : ['release_2_18', 'release_2_14']
}

SPHINX = 'sphinx-template'

app = Flask(__name__)

@app.route('/')
def hello_world():
    return 'Hello World!\n'


@app.route('/build', methods=['POST'])
def build():
    data = json.loads(request.get_data())
    repository = data['repository']['name']
    branch = _get_branch(data)

    if branch == 'master':
        _build_branch(repository)
    elif repository in BRANCHES and branch in BRANCHES[repository]:
        _build_branch(repository, branch)

    resp = make_response('{"status":"success"}', 200)
    resp.headers['Content-type'] = 'application/json'
    return resp


def _restore_symlinks(repo_dir):
    curdir = os.path.abspath('./')
    os.chdir(os.path.join(SKOLENI_DIR, repo_dir, "_build", "html"))
    for branch in BRANCHES[repo_dir]:
        source = os.path.join(SKOLENI_DIR, '{}_{}'.format(repo_dir, branch), '_build', 'html')
        target = branch.split('_', 1)[1].replace('_', '.')
        if not os.path.exists(target):
            print ("Restoring symlink '{}' -> '{}'".format(source, target))
            os.symlink(source, target)
    os.chdir(curdir)

def _build_branch(repository, branch='master'):

    def build_repo(name, branch):
        print("{sep}\nBuilding {repo} ({branch})\n{sep}\n".format(repo=name, sep='*' * 80, branch=branch),
              file=sys.stderr)
        curdir = os.path.abspath('./')
        repo_dir = name
        if branch != 'master':
            repo_dir += '_{}'.format(branch)
        os.chdir(os.path.join(SKOLENI_DIR, repo_dir))

        _update_git()

        template_branch = 'en' if name in WORKSHOPSEN else 'master'
        _update_git_template(template_branch)

        _update_html()

        if name in BRANCHES:
            _restore_symlinks(name)

        if name in WORKSHOPSPDF:
            _update_pdf()

        # publish build
        publish_dir = os.path.join(SKOLENI_DIR, '..', name)
        print("PUBLISH DIR: {}".format(publish_dir))
        if os.path.exists(publish_dir):
            shutil.rmtree(publish_dir)
        shutil.copytree("_build/html", publish_dir)

        os.chdir(curdir)

    if repository in WORKSHOPS:
        build_repo(repository, branch)

    elif repository == SPHINX:
        _update_git_template()
        for workshop in WORKSHOPS:
            build_repo(workshop, branch)

    print("{sep}\nBuilder finished\n{sep}\n".format(sep='*' * 80),
          file=sys.stderr)


def _update_git():
    subprocess.call(["git", "pull"])
    print("{}: UPDATED".format(os.path.abspath('./')))

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
    try:
        file_name = max(glob.iglob('_build/latex/*.pdf'), key=os.path.getctime)
    except ValueError:
        return
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
