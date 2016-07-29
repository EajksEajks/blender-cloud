#!/usr/bin/env python

from pillar_server import PillarServer

app = PillarServer('.')
app.process_extensions()

if __name__ == '__main__':
    app.run('::0', 5000, debug=True)
