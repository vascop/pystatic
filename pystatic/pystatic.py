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
import argparse
import sys


CWD = getcwd()
ROOT = path.abspath(path.dirname(__file__))
SETUP = path.join(ROOT, "project")

T = "templates"
A = "assets"
C = "conf"
V = path.join(C, "vars.yaml")
O = "output"

TEMPLATES = path.join(SETUP, T)
ASSETS = path.join(SETUP, A)
CONF = path.join(SETUP, C)
VARS = path.join(CONF, V)
OUTPUT = path.join(SETUP, O)

HOST = "127.0.0.1"
PORT = 12321

VERBOSE = False


class EventHandler(pyinotify.ProcessEvent):
    def __init__(self, args):
        pyinotify.ProcessEvent.__init__(self)
        self.cwd = getcwd()
        self.origin = path.join(self.cwd, args.origin)
        self.vard = getvars(self.origin)
        add_assets(self.origin, path.join(self.origin, O))
        settings.configure(TEMPLATE_LOADERS=("django.template.loaders.filesystem.Loader",), TEMPLATE_DIRS=(path.join(self.origin, T),))
        build_templates(self.origin, path.join(self.origin, O), self.vard)

    def process_default(self, event):
        if event.name.endswith('kate-swp') or event.name.endswith('~') or event.name.startswith('.') or event.name.startswith('qt_temp'):
            return
        if event.path.startswith(path.join(self.origin, C)):
            self.vard = getvars(self.origin)
        if event.path.startswith(path.join(self.origin, C)) or event.path.startswith(path.join(self.origin, A)):
            add_assets(self.origin, path.join(self.origin, O))

        build_templates(self.origin, path.join(self.origin, O), self.vard)
        print "[{}] Rebuilt output".format(strftime("%H:%M:%S", localtime()))


class Server(SocketServer.TCPServer):
    allow_reuse_address = True


class RequestHandler(SimpleHTTPServer.SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        if VERBOSE:
            print "[{}] {}".format(strftime("%H:%M:%S", localtime()), format%args)
        return


def getvars(origin):
    try:
        f = open(path.join(origin, V), 'r')
        vard = yaml.load(f)
        f.close()
        return vard
    except:
        print "Error: coulnd't read the 'conf/vars.yaml' file."
        return None


def add_assets(origin, target):
    target_dir = path.join(target, A)
    if path.exists(target_dir):
        shutil.rmtree(target_dir)
    origin_dir = path.join(origin, A)
    if not path.exists(origin_dir):
        print "Error: Can't find assets at origin directory."
        print "Aborting"
        sys.exit()
    shutil.copytree(origin_dir, target_dir)
    print "Created {}".format(path.join(getcwd(), target_dir))


def build_templates(origin, target, vard):
    origin_dir = path.join(origin, T)
    if not path.exists(origin_dir):
        print "Error: Can't find templates at origin directory."
        print "Aborting"
        sys.exit()
    for fich in listdir(origin_dir):
        if fich.startswith('_') or fich.startswith('.') or fich.endswith('~'):
            continue
        try:
            s = render_to_string(fich, vard)
            fpath = path.join(target, fich)
            f = open(fpath, 'w')
            f.write(s)
            f.close()
            print "Created {}".format(path.join(getcwd(), fpath))
        except TemplateDoesNotExist as e:
            print "Error: Couldn't find", e


def init(args):
    """ scaffolds a new project, overwrites everything without mercy """
    if not path.exists(args.target):
        makedirs(args.target)
    chdir(args.target)

    cwd = getcwd()

    if path.exists(T):
        shutil.rmtree(T)
    shutil.copytree(TEMPLATES, T)
    print "Created {}".format(path.join(cwd, T))
    if path.exists(A):
        shutil.rmtree(A)
    shutil.copytree(ASSETS, A)
    print "Created {}".format(path.join(cwd, A))
    if path.exists(C):
        shutil.rmtree(C)
    shutil.copytree(CONF, C)
    print "Created {}".format(path.join(cwd, C))
    if path.exists(O):
        shutil.rmtree(O)
    shutil.copytree(OUTPUT, O)
    print "Created {}".format(path.join(cwd, O))

    print 'Project created at {}'.format(cwd)


def build_output(args):
    """ builds the project output directory from the templates, assets, etc """
    if not path.exists(args.target):
        makedirs(args.target)
    cwd = getcwd()
    print "Created {}".format(path.join(cwd, args.target))

    settings.configure(TEMPLATE_LOADERS=("django.template.loaders.filesystem.Loader",), TEMPLATE_DIRS=(path.join(args.origin, T),))

    add_assets(args.origin, args.target)
    vard = getvars(args.origin)
    build_templates(args.origin, args.target, vard)

    print 'Project output at {}'.format(path.join(cwd, args.target))


def run_server(args):
    """ launches a preview server """
    if not path.exists(args.origin):
        print "Error: Can't find origin directory."
        print "Aborting"
        sys.exit()
    cwd = getcwd()
    if not path.exists(path.join(args.origin, O)):
        print "Error: Can't find output directory."
        print "Aborting"
        sys.exit()
    handler = RequestHandler
    httpd = Server((HOST, args.port), handler)
    if args.noauto:
        print "[{}] Live at http://{}:{}".format(strftime("%H:%M:%S", localtime()), HOST, args.port)
        try:
            chdir(path.join(cwd, args.origin, O))
            httpd.serve_forever()
        except KeyboardInterrupt:
            print "Aborting"
            sys.exit()
    else:
        t = threading.Thread(target=httpd.serve_forever)
        t.daemon = True
        t.start()
        print "[{}] Live at http://{}:{}".format(strftime("%H:%M:%S", localtime()), HOST, args.port)
        wm = pyinotify.WatchManager()
        handler = EventHandler(args)
        notifier = pyinotify.Notifier(wm, handler)
        mask = pyinotify.IN_CLOSE_WRITE | pyinotify.IN_MOVED_TO | pyinotify.IN_MOVED_FROM | pyinotify.IN_CREATE | pyinotify.IN_DELETE | pyinotify.IN_ATTRIB
        wm.add_watch([path.join(cwd, args.origin, A), path.join(cwd, args.origin, C), path.join(cwd, args.origin, T)], mask, auto_add=True, rec=True)
        chdir(path.join(cwd, args.origin, O))
        notifier.loop()


def main():
    parser = argparse.ArgumentParser(prog='pystatic', description='Static Website Generator')
    subparsers = parser.add_subparsers()

    parser_init = subparsers.add_parser('init', help='scaffold a new project')
    parser_init.add_argument('target', nargs='?', default=CWD, help='target directory of new project')
    parser_init.set_defaults(func=init)

    parser_build = subparsers.add_parser('build', help='build project output')
    parser_build.add_argument('--origin', '-o', default=CWD, help='origin directory to build from')
    parser_build.add_argument('target', nargs='?', default=O, help='target directory of built project')
    parser_build.set_defaults(func=build_output)

    parser_server = subparsers.add_parser('server', help='launch a preview server')
    parser_server.add_argument('--origin', '-o', default=CWD, help='origin directory to serve')
    parser_server.add_argument('--noauto', '-n', action="store_true", help='stop auto-reloading with changes')
    parser_server.add_argument('port', nargs='?', type=int, default=PORT, help='server port, {} by default'.format(PORT))
    parser_server.set_defaults(func=run_server)

    args = parser.parse_args()
    args.func(args)

if __name__ == "__main__":
    main()