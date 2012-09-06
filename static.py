from django.template.loader import render_to_string
from django.template.base import TemplateDoesNotExist
from django.conf import settings
import os.path
import yaml
import shutil
import SimpleHTTPServer
import SocketServer
import time
import threading
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer


ROOT = os.path.abspath(os.path.dirname(__file__))
TEMPLATES = os.path.join(ROOT, "templates/")
ASSETS = os.path.join(ROOT, "assets/")
OUTPUT = os.path.join(ROOT, "output/")
VARS = os.path.join(ROOT, "vars.yaml")

HOST = "127.0.0.1"
PORT = 12321

settings.configure(TEMPLATE_LOADERS=("django.template.loaders.filesystem.Loader",), TEMPLATE_DIRS=(TEMPLATES,))


class ChangeHandler(FileSystemEventHandler):
    def __init__(self):
        FileSystemEventHandler.__init__(self)
        self.rebuild()

    def on_any_event(self, event):
        print event
        self.httpd.shutdown()
        self.httpd.server_close()
        self.t.join()
        self.rebuild()

    def rebuild(self):
        vard = getvars()
        outputtree()
        asset_dir = addassets(vard)
        build_templates(vard)
        self.t, self.httpd = runserver()


class Server(SocketServer.TCPServer):
    allow_reuse_address = True

def rm_border_slashes(s):
    while '/' in s:
        if '/' == s[0]:
            s = s[1:]
        elif '/' == s[-1]:
            s = s[:-1]
        else:
            return s
    return s

def runserver():
    os.chdir(OUTPUT)
    handler = SimpleHTTPServer.SimpleHTTPRequestHandler
    httpd = Server((HOST, PORT), handler, bind_and_activate=False)
    httpd.server_bind()
    httpd.server_activate()
    t = threading.Thread(target=httpd.serve_forever)
    t.daemon = True
    t.start()
    print "Live at http://{0}:{1}".format(HOST, PORT)
    return t, httpd

def getvars():
    f = open(VARS)
    vard = yaml.load(f)
    f.close()
    return vard


def outputtree():
    if os.path.exists(OUTPUT):
        shutil.rmtree(OUTPUT)
    os.makedirs(OUTPUT)

def addassets(vard):
    asset_dir = rm_border_slashes(vard['assets']['base_url'])
    if asset_dir is not None and asset_dir != "":
        asset_dir = OUTPUT + asset_dir
        shutil.copytree(ASSETS, asset_dir)
    return asset_dir

def build_templates(vard):
    for fich in os.listdir(TEMPLATES):
        s = ''
        if fich.startswith('_') or fich.startswith('.') or fich.endswith('~'):
            continue

        try:
            s = render_to_string(fich, vard)
        except TemplateDoesNotExist as e:
            print "Couldn\'t find", e
        if s != '':
            path = OUTPUT + fich
            f = open(path, 'w')
            f.write(s)
            f.close()
            print "Built", path


if __name__ == "__main__":
    # Watch for changes
    handler = ChangeHandler()
    observer = Observer()
    observer.schedule(handler, path=ROOT, recursive=True)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()