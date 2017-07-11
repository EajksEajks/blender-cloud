from pillar.tests import PillarTestServer, AbstractPillarTest


class CloudTestServer(PillarTestServer):
    def __init__(self, *args, **kwargs):
        PillarTestServer.__init__(self, *args, **kwargs)

        from flamenco import FlamencoExtension
        from attract import AttractExtension
        from cloud import CloudExtension

        self.load_extension(FlamencoExtension(), '/flamenco')
        self.load_extension(AttractExtension(), '/attract')
        self.load_extension(CloudExtension(), None)


class AbstractCloudTest(AbstractPillarTest):
    pillar_server_class = CloudTestServer

    def tearDown(self):
        self.unload_modules('cloud')
        self.unload_modules('attract')
        self.unload_modules('flamenco')
        AbstractPillarTest.tearDown(self)
