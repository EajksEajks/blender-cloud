from datetime import timedelta

from bson import ObjectId

from tests.abstract_cloud_test import AbstractCloudTest
from cloud.routes import get_random_featured_nodes


class RandomFeaturedNodeTest(AbstractCloudTest):
    def setUp(self, **kwargs):
        super().setUp(**kwargs)

        self.pid, _ = self.ensure_project_exists()
        self.file_id, _ = self.ensure_file_exists(file_overrides={
            'variations': [
                {'format': 'mp4',
                 'duration': 75  # 01:15
                 },
            ],
        })

        self.uid = self.create_user()

        from pillar.api.utils import utcnow
        self.fake_now = utcnow()

    def test_random_feature_node_returns_6_nodes(self):
        from pillar.web.nodes.routes import url_for_node

        base_node = {
            'name': 'Just a node name',
            'project': self.pid,
            'description': '',
            'node_type': 'asset',
            'user': self.uid,
        }
        base_props = {
            'status': 'published',
            'file': self.file_id,
            'content_type': 'video',
            'order': 0
        }

        def create_asset(weeks):
            return self.create_node({
                **base_node,
                '_created': self.fake_now - timedelta(weeks=weeks),
                'properties': base_props,
            })

        all_asset_ids = [create_asset(i) for i in range(20)]

        with self.app.app_context():
            proj_col = self.app.db('projects')
            proj_col.update_one(
                {'_id': self.pid},
                {'$set': {
                    'nodes_featured': all_asset_ids,
                }})

        with self.app.test_request_context():
            random_assets = get_random_featured_nodes()

            self.assertIs(len(random_assets), 6)
            for asset in random_assets:
                aid = asset['_id']
                self.assertIn(ObjectId(asset['_id']), all_asset_ids)
                self.assertEqual(f'/p/default-project/{aid}', url_for_node(node=asset))

    def test_random_feature_ignore(self):
        def assert_ignored():
            with self.app.test_request_context():
                random_assets = get_random_featured_nodes()
                self.assertIs(len(random_assets), 0)

        base_node = {
            'name': 'Just a node name',
            'project': self.pid,
            'description': '',
            'node_type': 'asset',
            'user': self.uid,
        }
        base_props = {
            'status': 'published',
            'file': self.file_id,
            'content_type': 'video',
            'order': 0
        }

        node_id = self.create_node({
                **base_node,
                '_created': self.fake_now - timedelta(days=5),
                'properties': base_props,
            })

        # Not featured, should be ignored
        assert_ignored()

        # Featured but project is private, should be ignored
        with self.app.app_context():
            proj_col = self.app.db('projects')
            proj_col.update_one(
                {'_id': self.pid},
                {'$set': {
                    'nodes_featured': [node_id],
                    'is_private': True,
                }})
        assert_ignored()

        # Featured but node is deleted, should be ignored
        with self.app.app_context():
            proj_col = self.app.db('projects')
            proj_col.update_one(
                {'_id': self.pid},
                {'$set': {
                    'nodes_featured': [node_id],
                    'is_private': False,
                }})

            node_col = self.app.db('nodes')
            node_col.update_one(
                {'_id': node_id},
                {'$set': {
                    '_deleted': True,
                }})
        assert_ignored()

    def test_random_feature_node_data(self):
        base_node = {
            'name': 'Just a node name',
            'project': self.pid,
            'description': '',
            'node_type': 'asset',
            'user': self.uid,
        }
        base_props = {
            'status': 'published',
            'file': self.file_id,
            'content_type': 'video',
            'duration_seconds': 75,
            'order': 0
        }

        node_id = self.create_node({
            **base_node,
            '_created': self.fake_now,
            'properties': base_props,
        })

        with self.app.app_context():
            proj_col = self.app.db('projects')
            proj_col.update_one(
                {'_id': self.pid},
                {'$set': {
                    'nodes_featured': [node_id],
                }})

        with self.app.test_request_context():
            random_assets = get_random_featured_nodes()
            self.assertIs(len(random_assets), 1)

            asset = random_assets[0]
            self.assertEqual('Just a node name', asset['name'])
            self.assertEqual('Unittest project', asset['project']['name'])
            self.assertEqual('video', asset['properties']['content_type'])
            self.assertTrue(asset.properties.content_type == 'video')
            self.assertEqual(self.fake_now, asset['_created'])
            self.assertEqual(str(node_id), asset['_id'])
            self.assertEqual(75, asset['properties']['duration_seconds'])
            self.assertNotIn('user', asset)
