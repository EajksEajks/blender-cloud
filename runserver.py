#!/usr/bin/env python

from pillar import PillarServer
from attract import AttractExtension
from flamenco import FlamencoExtension
from cloud import CloudExtension

attract = AttractExtension()
flamenco = FlamencoExtension()
cloud = CloudExtension()

app = PillarServer('.')
app.load_extension(attract, '/attract')
app.load_extension(flamenco, '/flamenco')
app.load_extension(cloud, None)
app.process_extensions()

if __name__ == '__main__':
    app.run('::0', 5001, debug=True)
