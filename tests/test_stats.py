import copy

from bson import ObjectId
from pillar.tests import common_test_data as ctd

from tests.abstract_cloud_test import AbstractCloudTest


class StatsTest(AbstractCloudTest):
    def test_count_public_nodes(self):
        self.enter_app_context()

        # Create two public and two private projects. Only the assets from the
        # public projects should be counted.
        public1 = self.create_project_with_admin(
            24 * 'a', project_overrides={'_id': ObjectId(), 'is_private': False})
        public2 = self.create_project_with_admin(
            24 * 'b', project_overrides={'_id': ObjectId(), 'is_private': False})
        private1 = self.create_project_with_admin(
            24 * 'c', project_overrides={'_id': ObjectId(), 'is_private': True})
        private2 = self.create_project_with_admin(
            24 * 'd', project_overrides={'_id': ObjectId(), 'is_private': None})

        self.assertEqual(4, self.app.db('projects').count_documents({}))

        # Create asset node
        self.assertEqual('asset', ctd.EXAMPLE_NODE['node_type'])
        example_node = copy.deepcopy(ctd.EXAMPLE_NODE)
        del example_node['_id']
        del example_node['project']

        for pid in (public1, public2, private1, private2):
            self.create_node({'_id': ObjectId(), 'project': pid, **example_node})
            self.create_node({'_id': ObjectId(), 'project': pid, **example_node})
            self.create_node({'_id': ObjectId(), 'project': pid, **example_node})
            self.create_node({'_id': ObjectId(), 'project': pid, **example_node})

        # Count the asset nodes
        from cloud.stats import count_nodes
        count = count_nodes({'node_type': 'asset'})
        self.assertEqual(8, count)
