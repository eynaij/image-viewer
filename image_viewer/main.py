#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Awesome image-viewer tools
"""

from __future__ import print_function
from __future__ import absolute_import
import argparse
import os
import yaml
import sys
try:
    import commands
except Exception as e:
    import subprocess as commands
from gunicorn.app.wsgiapp import run
import re
import click
import platform
import werkzeug


_ROOT = os.path.abspath(os.path.dirname(__file__))
_CFGROOT = os.path.join(os.environ['HOME'], '.image-viewer')


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cfg', default=None, type=str, help='input config yaml')
    parser.add_argument('--version', dest='version', action='store_true', help='print version')
    args = parser.parse_args()
    if args.version:
        get_version()
    return args


def get_version():
    from . import __version__
    __version__ = '0.0.1'
    message = "Python %(python)s\nimage-viewer %(app)s"
    click.echo(
        message
        % {
            "python": platform.python_version(),
            "app": __version__,
        },
    )
    sys.exit()


def createdb(database, schema):
    print("initializing database: %s"  % database)
    cmd = 'sqlite3 %s < %s' % (database, schema)
    (status, output) = commands.getstatusoutput(cmd)
    output = output.split('\n')
    print(output)


def main():
    args = parse_args()
    if args.cfg is None:
        args.cfg = os.path.join(_CFGROOT, 'image-viewer.yaml')
    if not os.path.exists(args.cfg):
        print('%s not found, please create via image-viewer-cfg' % args.cfg)
        sys.exit()

    with open(args.cfg, 'r') as fid:
        cfg = yaml.load(fid.read(), Loader=yaml.SafeLoader)

    # create database
    db = os.path.join(_CFGROOT, cfg['database'])
    schema = os.path.join(_ROOT, "schema.sql")
    if not os.path.exists(db):
        createdb(db, schema)

    workers = str(cfg["workers"])
    host = str(cfg["host"])
    port = str(cfg["port"])
    log_level = "DEBUG"
    app = "image_viewer.viewer:app"

    sys.argv[0] = re.sub(r'(-script\.pyw|\.exe)?$', '', sys.argv[0])
    sys.argv.append(app)
    sys.argv.append('--bind')
    sys.argv.append('%s:%s' % (host, port))
    sys.argv.append('--log-level')
    sys.argv.append(log_level)
    sys.argv.append('--workers')
    sys.argv.append(workers)
    sys.exit(run())


if __name__ == "__main__":
    main()
