from abstract_cloud_test import AbstractCloudTest


class LinkedRolesTest(AbstractCloudTest):
    def test_linked_roles(self):
        user_id = self.create_user(roles=[])
        db_user = self.fetch_user_from_db(user_id)

        self.badger(db_user['email'], {'subscriber'}, 'grant')
        db_user = self.fetch_user_from_db(user_id)
        self.assertEqual({'subscriber', 'flamenco-user', 'attract-user'},
                         set(db_user['roles']))

        self.badger(db_user['email'], {'subscriber'}, 'revoke')
        db_user = self.fetch_user_from_db(user_id)
        self.assertEqual(set(),
                         set(db_user.get('roles', [])))
