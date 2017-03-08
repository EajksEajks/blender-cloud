from os.path import abspath, dirname
import sys

from pillar import PillarServer
from attract import AttractExtension
from flamenco import FlamencoExtension

sys.path.append('/data/git/blender-cloud')

attract = AttractExtension()
flamenco = FlamencoExtension()

application = PillarServer(dirname(abspath(__file__)))
application.load_extension(attract, '/attract')
application.load_extension(flamenco, '/flamenco')
application.process_extensions()
