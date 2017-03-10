from os.path import abspath, dirname
import sys

from pillar import PillarServer
from attract import AttractExtension
from flamenco import FlamencoExtension
from cloud import CloudExtension

sys.path.append('/data/git/blender-cloud')

attract = AttractExtension()
flamenco = FlamencoExtension()
cloud = CloudExtension()

application = PillarServer(dirname(abspath(__file__)))
application.load_extension(attract, '/attract')
application.load_extension(flamenco, '/flamenco')
application.load_extension(cloud, None)
application.process_extensions()
