# This program is free software. It comes without any warranty, to
# the extent permitted by applicable law. You can redistribute it
# and/or modify it under the terms of the Do What The Fuck You Want
# Public License.

from django.template.loader import render_to_string
from django.template.base import TemplateDoesNotExist
from django.conf import settings
from os import path, getcwd, chdir, makedirs, listdir
import yaml
import shutil
import SimpleHTTPServer
import SocketServer
from time import strftime, localtime
import threading
import pyinotify


PROJ = getcwd()
ROOT = path.abspath(path.dirname(__file__))
SETUP = path.join(ROOT, "project")

TEMPLATES = path.join(PROJ, "templates")
ASSETS = path.join(PROJ, "assets")
CONF = path.join(PROJ, "conf")
VARS = path.join(CONF, "vars.yaml")
OUTPUT = path.join(PROJ, "output")

HOST = "127.0.0.1"
PORT = 12321

VERBOSE = False

settings.configure(TEMPLATE_LOADERS=("django.template.loaders.filesystem.Loader",), TEMPLATE_DIRS=(TEMPLATES,))


class EventHandler(pyinotify.ProcessEvent):
    def __init__(self):
        pyinotify.ProcessEvent.__init__(self)
        setupshop()
        self.vard = getvars()
        addassets()
        build_templates(self.vard)
        self.t, self.httpd = runserver(first=True)

    def process_default(self, event):
        if event.name.endswith('kate-swp') or event.name.endswith('~') or event.name.startswith('.') or event.name.startswith('qt_temp'):
            return

        if event.path == CONF:
            self.vard = getvars()
        if event.path == CONF or event.path == ASSETS:
            addassets()

        build_templates(self.vard)
        print "[{}] Rebuilt output".format(strftime("%H:%M:%S", localtime()))

class Server(SocketServer.TCPServer):
    allow_reuse_address = True

class RequestHandler(SimpleHTTPServer.SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        if VERBOSE:
            print "[{}] {}".format(strftime("%H:%M:%S", localtime()), format%args)
        return

def rm_border_slashes(s):
    while '/' in s:
        if '/' == s[0]:
            s = s[1:]
        elif '/' == s[-1]:
            s = s[:-1]
        else:
            return s
    return s

def runserver(first=False):
    chdir(OUTPUT)
    handler = RequestHandler
    httpd = Server((HOST, PORT), handler, bind_and_activate=False)
    httpd.server_bind()
    httpd.server_activate()
    t = threading.Thread(target=httpd.serve_forever)
    t.start()
    if first:
        print "[{}] Live at http://{}:{}".format(strftime("%H:%M:%S", localtime()), HOST, PORT)
    return t, httpd

def getvars():
    f = open(VARS, 'r')
    vard = yaml.load(f)
    f.close()
    return vard

def setupshop():
    shutil.copytree(path.join(SETUP, "templates"), TEMPLATES)
    shutil.copytree(path.join(SETUP, "assets"), ASSETS)
    shutil.copytree(path.join(SETUP, "conf"), CONF)
    shutil.copytree(path.join(SETUP, "output"), OUTPUT)

def addassets():
    asset_dir = path.join(OUTPUT, "assets")
    if path.exists(asset_dir):
        shutil.rmtree(asset_dir)
    shutil.copytree(ASSETS, asset_dir)

def build_templates(vard):
    for fich in listdir(TEMPLATES):
        s = ''
        if fich.startswith('_') or fich.startswith('.') or fich.endswith('~'):
            continue

        try:
            s = render_to_string(fich, vard)
        except TemplateDoesNotExist as e:
            print "Couldn\'t find", e
        if s != '':
            fpath = path.join(OUTPUT, fich)
            f = open(fpath, 'w')
            f.write(s)
            f.close()
            #print "Built", path


if __name__ == "__main__":
    wm = pyinotify.WatchManager()
    handler = EventHandler()
    notifier = pyinotify.Notifier(wm, handler)
    mask = pyinotify.IN_CLOSE_WRITE | pyinotify.IN_MOVED_TO | pyinotify.IN_MOVED_FROM | pyinotify.IN_CREATE | pyinotify.IN_DELETE | pyinotify.IN_ATTRIB
    wm.add_watch([ASSETS, CONF, TEMPLATES], mask, auto_add=True, rec=True)
    notifier.loop()