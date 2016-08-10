from os.path import abspath, dirname
import sys

activate_this = '/data/venv/bin/activate_this.py'
execfile(activate_this, dict(__file__=activate_this))
from flup.server.fcgi import WSGIServer
from pillar import PillarServer

sys.path.append('/data/git/blender-cloud/')

application = PillarServer(dirname(abspath(__file__)))
application.process_extensions()

if __name__ == '__main__':
    WSGIServer(application).run()
