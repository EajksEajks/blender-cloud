#!/usr/bin/env python

from pillar import PillarServer
from attract import AttractExtension

attract = AttractExtension()

app = PillarServer('.')
app.load_extension(attract, '/attract')
app.process_extensions()

if __name__ == '__main__':
    app.run('::0', 5001, debug=True)
