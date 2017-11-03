from os.path import abspath, dirname
import sys

my_path = dirname(abspath(__file__))
sys.path.append(my_path)

from pillar import PillarServer
from attract import AttractExtension
from flamenco import FlamencoExtension
from svnman import SVNManExtension
from cloud import CloudExtension

attract = AttractExtension()
flamenco = FlamencoExtension()
svnman = SVNManExtension()
cloud = CloudExtension()

application = PillarServer(my_path)
application.load_extension(attract, '/attract')
application.load_extension(flamenco, '/flamenco')
application.load_extension(svnman, '/svn')
application.load_extension(cloud, None)
application.process_extensions()
