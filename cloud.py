#!/usr/bin/env python

from pillar import PillarServer

app = PillarServer('.')
app.process_extensions()

if __name__ == '__main__':
    app.run('::0', 5001, debug=True)
