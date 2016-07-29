from os.path import abspath, dirname
import sys
from pillar_server import PillarServer

activate_this = '/data/venv/bin/activate_this.py'
execfile(activate_this, dict(__file__=activate_this))
from flup.server.fcgi import WSGIServer

sys.path.append('/data/git/blender-cloud/bcloud-server/')

application = PillarServer(dirname(abspath(__file__)))
application.process_extensions()

if __name__ == '__main__':
    WSGIServer(application).run()
