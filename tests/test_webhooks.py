import hashlib
import hmac
import json
from abstract_cloud_test import AbstractCloudTest


class AbstractWebhookTest(AbstractCloudTest):
    def setUp(self, **kwargs):
        super().setUp(**kwargs)
        self.enter_app_context()
        self.create_standard_groups()
        self.hmac_secret = b'1234 je moeder'
        self.app.config['BLENDER_ID_WEBHOOK_USER_CHANGED_SECRET'] = self.hmac_secret.decode()
        self.uid = self.create_user(24 * 'a',
                                    roles={'subscriber'},
                                    email='old@email.address')


class UserModifiedTest(AbstractWebhookTest):
    def test_change_full_name(self):
        payload = {'id': 1112333,
                   'old_email': 'old@email.address',
                   'full_name': 'ကြယ်ဆွတ်',
                   'email': 'old@email.address',
                   'roles': ['cloud_subscriber']}
        as_json = json.dumps(payload).encode()
        mac = hmac.new(self.hmac_secret,
                       as_json, hashlib.sha256)
        self.post('/api/webhooks/user-modified',
                  data=as_json,
                  content_type='application/json',
                  headers={'X-Webhook-HMAC': mac.hexdigest()},
                  expected_status=204)

        # Check the effect on the user
        db_user = self.fetch_user_from_db(self.uid)
        self.assertEqual('old@email.address', db_user['email'])
        self.assertEqual('ကြယ်ဆွတ်', db_user['full_name'])
        self.assertEqual(['subscriber'], db_user['roles'])

    def test_clear_full_name(self):
        """An empty full name should make it fall back to the username"""
        payload = {'id': 1112333,
                   'old_email': 'old@email.address',
                   'full_name': '',
                   'email': 'old@email.address',
                   'roles': ['cloud_subscriber']}
        as_json = json.dumps(payload).encode()
        mac = hmac.new(self.hmac_secret,
                       as_json, hashlib.sha256)
        self.post('/api/webhooks/user-modified',
                  data=as_json,
                  content_type='application/json',
                  headers={'X-Webhook-HMAC': mac.hexdigest()},
                  expected_status=204)

        # Check the effect on the user
        db_user = self.fetch_user_from_db(self.uid)
        self.assertNotEqual('', db_user['username'])
        self.assertEqual('old@email.address', db_user['email'])
        self.assertEqual(db_user['username'], db_user['full_name'])
        self.assertEqual(['subscriber'], db_user['roles'])

    def test_change_email(self):
        payload = {'id': 1112333,
                   'old_email': 'old@email.address',
                   'full_name': 'ကြယ်ဆွတ်',
                   'email': 'new.address+here-there@email.address',
                   'roles': ['cloud_subscriber']}
        as_json = json.dumps(payload).encode()
        mac = hmac.new(self.hmac_secret,
                       as_json, hashlib.sha256)
        self.post('/api/webhooks/user-modified',
                  data=as_json,
                  content_type='application/json',
                  headers={'X-Webhook-HMAC': mac.hexdigest()},
                  expected_status=204)

        # Check the effect on the user
        db_user = self.fetch_user_from_db(self.uid)
        self.assertEqual('new.address+here-there@email.address', db_user['email'])
        self.assertEqual('ကြယ်ဆွတ်', db_user['full_name'])
        self.assertEqual(['subscriber'], db_user['roles'])

    def test_change_email_unknown_old(self):
        payload = {'id': 1112333,
                   'old_email': 'ancient@email.address',
                   'full_name': 'ကြယ်ဆွတ်',
                   'email': 'old@email.address',
                   'roles': ['cloud_demo']}
        as_json = json.dumps(payload).encode()
        mac = hmac.new(self.hmac_secret,
                       as_json, hashlib.sha256)
        self.post('/api/webhooks/user-modified',
                  data=as_json,
                  content_type='application/json',
                  headers={'X-Webhook-HMAC': mac.hexdigest()},
                  expected_status=204)

        # Check the effect on the user
        db_user = self.fetch_user_from_db(self.uid)
        self.assertEqual('old@email.address', db_user['email'])
        self.assertEqual('ကြယ်ဆွတ်', db_user['full_name'])
        self.assertEqual(['demo'], db_user['roles'])

    def test_change_email_unknown_bid_known(self):
        users_coll = self.app.db('users')
        users_coll.update_one({'_id': self.uid},
                              {'$set': {'auth': [
                                  {'provider': 'mastodon', 'user_id': 'hey@there'},
                                  {'provider': 'blender-id', 'user_id': '1112333'}
                              ]}})

        payload = {'id': 1112333,
                   'old_email': 'new@elsewhere.address',
                   'full_name': 'ကြယ်ဆွတ်',
                   'email': 'new@elsewhere.address',
                   'roles': ['cloud_demo']}
        as_json = json.dumps(payload).encode()
        mac = hmac.new(self.hmac_secret,
                       as_json, hashlib.sha256)
        self.post('/api/webhooks/user-modified',
                  data=as_json,
                  content_type='application/json',
                  headers={'X-Webhook-HMAC': mac.hexdigest()},
                  expected_status=204)

        # Check the effect on the user
        db_user = self.fetch_user_from_db(self.uid)
        self.assertEqual('new@elsewhere.address', db_user['email'])
        self.assertEqual('ကြယ်ဆွတ်', db_user['full_name'])
        self.assertEqual(['demo'], db_user['roles'])

    def test_multiple_users_matching(self):
        users_coll = self.app.db('users')
        users_coll.update_one({'_id': self.uid},
                              {'$set': {'auth': [
                                  {'provider': 'mastodon', 'user_id': 'hey@there'},
                                  {'provider': 'blender-id', 'user_id': '1112333'}
                              ]}})

        # Create another user with email=new@elsewhere.address
        other_uid = self.create_user(24 * 'b', email='new@elsewhere.address')

        payload = {'id': 1112333,
                   'old_email': 'new@elsewhere.address',
                   'full_name': 'ကြယ်ဆွတ်',
                   'email': 'new@elsewhere.address',
                   'roles': ['cloud_demo']}
        as_json = json.dumps(payload).encode()
        mac = hmac.new(self.hmac_secret,
                       as_json, hashlib.sha256)
        self.post('/api/webhooks/user-modified',
                  data=as_json,
                  content_type='application/json',
                  headers={'X-Webhook-HMAC': mac.hexdigest()},
                  expected_status=204)

        # Check the effect on the user
        db_user = self.fetch_user_from_db(self.uid)
        self.assertEqual('new@elsewhere.address', db_user['email'])
        self.assertEqual('ကြယ်ဆွတ်', db_user['full_name'])
        self.assertEqual(['demo'], db_user['roles'])

        # The other user with the email address should still be there.
        # This *will* cause problems later, so the code should log this
        # as error condition!
        other_user = self.fetch_user_from_db(other_uid)
        self.assertEqual('new@elsewhere.address', other_user['email'])



    def test_change_roles(self):
        payload = {'id': 1112333,
                   'old_email': 'old@email.address',
                   'full_name': 'ကြယ်ဆွတ်',
                   'email': 'old@email.address',
                   'roles': ['cloud_demo']}
        as_json = json.dumps(payload).encode()
        mac = hmac.new(self.hmac_secret,
                       as_json, hashlib.sha256)
        self.post('/api/webhooks/user-modified',
                  data=as_json,
                  content_type='application/json',
                  headers={'X-Webhook-HMAC': mac.hexdigest()},
                  expected_status=204)

        # Check the effect on the user
        db_user = self.fetch_user_from_db(self.uid)
        self.assertEqual('old@email.address', db_user['email'])
        self.assertEqual('ကြယ်ဆွတ်', db_user['full_name'])
        self.assertEqual({'demo'}, set(db_user['roles']))

    def test_bad_hmac(self):
        payload = {'id': 1112333,
                   'old_email': 'old@email.address',
                   'full_name': 'ကြယ်ဆွတ်',
                   'email': 'new@email.address',
                   'roles': ['cloud_demo']}
        as_json = json.dumps(payload).encode()
        mac = hmac.new(self.hmac_secret,
                       as_json, hashlib.sha256)
        self.post('/api/webhooks/user-modified',
                  data=as_json,
                  content_type='application/json',
                  headers={'X-Webhook-HMAC': mac.hexdigest()[:-2]},
                  expected_status=400)

        # Check the effect on the user
        db_user = self.fetch_user_from_db(self.uid)
        self.assertEqual('old@email.address', db_user['email'])
        self.assertEqual('คนรักของผัดไทย', db_user['full_name'])
        self.assertEqual({'subscriber'}, set(db_user['roles']))

    def test_no_hmac(self):
        payload = {'id': 1112333,
                   'old_email': 'old@email.address',
                   'full_name': 'ကြယ်ဆွတ်',
                   'email': 'new@email.address',
                   'roles': ['cloud_demo']}
        as_json = json.dumps(payload).encode()
        self.post('/api/webhooks/user-modified',
                  data=as_json,
                  content_type='application/json',
                  expected_status=400)

        # Check the effect on the user
        db_user = self.fetch_user_from_db(self.uid)
        self.assertEqual('old@email.address', db_user['email'])
        self.assertEqual('คนรักของผัดไทย', db_user['full_name'])
        self.assertEqual({'subscriber'}, set(db_user['roles']))

    def test_huge_request(self):
        payload = b'a' * 1024 * 100
        mac = hmac.new(self.hmac_secret, payload, hashlib.sha256)
        self.post('/api/webhooks/user-modified',
                  data=payload,
                  content_type='application/json',
                  headers={'X-Webhook-HMAC': mac.hexdigest()},
                  expected_status=400)

        # Check the effect on the user
        db_user = self.fetch_user_from_db(self.uid)
        self.assertEqual('old@email.address', db_user['email'])
        self.assertEqual('คนรักของผัดไทย', db_user['full_name'])
        self.assertEqual({'subscriber'}, set(db_user['roles']))

    def test_invalid_json(self):
        payload = b'\x00' * 1024 * 5
        mac = hmac.new(self.hmac_secret, payload, hashlib.sha256)
        self.post('/api/webhooks/user-modified',
                  data=payload,
                  content_type='application/json',
                  headers={'X-Webhook-HMAC': mac.hexdigest()},
                  expected_status=400)

        # Check the effect on the user
        db_user = self.fetch_user_from_db(self.uid)
        self.assertEqual('old@email.address', db_user['email'])
        self.assertEqual('คนรักของผัดไทย', db_user['full_name'])
        self.assertEqual({'subscriber'}, set(db_user['roles']))

    def test_text_plain(self):
        payload = b'{"valid": false}'
        mac = hmac.new(self.hmac_secret, payload, hashlib.sha256)
        self.post('/api/webhooks/user-modified',
                  data=payload,
                  content_type='text/plain',
                  headers={'X-Webhook-HMAC': mac.hexdigest()},
                  expected_status=400)

        # Check the effect on the user
        db_user = self.fetch_user_from_db(self.uid)
        self.assertEqual('old@email.address', db_user['email'])
        self.assertEqual('คนรักของผัดไทย', db_user['full_name'])
        self.assertEqual({'subscriber'}, set(db_user['roles']))


class UserScoreTest(AbstractCloudTest):
    def setUp(self, **kwargs):
        super().setUp(**kwargs)
        self.payload = {'id': 123,
                        'old_email': 'old@email.address',
                        'full_name': 'ကြယ်ဆွတ်',
                        'email': 'new@email.address',
                        'roles': ['cloud_demo']}

    def test_score_bid_only(self):
        from cloud.webhooks import score
        self.assertEqual(10, score(self.payload,
                                   {'auth': [
                                       {'provider': 'mastodon', 'user_id': 'hey@there'},
                                       {'provider': 'blender-id', 'user_id': '123'}
                                   ]}))

    def test_score_old_mail_only(self):
        from cloud.webhooks import score
        self.assertEqual(1, score(self.payload, {'email': 'old@email.address'}))

    def test_score_new_mail_only(self):
        from cloud.webhooks import score
        self.assertEqual(2, score(self.payload, {'email': 'new@email.address'}))

    def test_match_everything(self):
        from cloud.webhooks import score
        self.payload['old_email'] = self.payload['email']
        self.assertEqual(13, score(self.payload,
                                   {'auth': [
                                       {'provider': 'mastodon', 'user_id': 'hey@there'},
                                       {'provider': 'blender-id', 'user_id': '123'}
                                   ],
                                       'email': 'new@email.address'
                                   }))


class UserModifiedUserCreationTest(AbstractWebhookTest):
    def test_unknown_email(self):
        payload = {'id': 1112333,
                   'old_email': 'unknown@email.address',
                   'full_name': 'ကြယ်ဆွတ်',
                   'email': 'new@email.address',
                   'roles': ['cloud_demo']}
        as_json = json.dumps(payload).encode()
        mac = hmac.new(self.hmac_secret,
                       as_json, hashlib.sha256)
        self.post('/api/webhooks/user-modified',
                  data=as_json,
                  content_type='application/json',
                  headers={'X-Webhook-HMAC': mac.hexdigest()},
                  expected_status=204)

        # Check that the user has been created, and the existing user has not been touched.
        db_user = self.fetch_user_from_db(self.uid)
        self.assertEqual('old@email.address', db_user['email'])
        self.assertEqual('คนรักของผัดไทย', db_user['full_name'])
        self.assertEqual({'subscriber'}, set(db_user['roles']))

        users_coll = self.app.db('users')
        new_user = users_coll.find_one({'email': 'new@email.address'})
        self.assertIsNotNone(new_user)
        self.assertEqual('ကြယ်ဆွတ်', new_user['full_name'])
        self.assertEqual('new', new_user['username'])  # based on email address
        self.assertEqual(['demo'], new_user['roles'])
        self.assertEqual({
            'provider': 'blender-id',
            'user_id': '1112333',
            'token': '',
        }, new_user['auth'][0])

    def test_create_subscriber(self):
        payload = {'id': 1112333,
                   'old_email': 'unknown@email.address',
                   'full_name': 'ကြယ်ဆွတ်',
                   'email': 'new@email.address',
                   'roles': ['cloud_subscriber', 'cloud_has_subscription']}
        as_json = json.dumps(payload).encode()
        mac = hmac.new(self.hmac_secret,
                       as_json, hashlib.sha256)
        self.post('/api/webhooks/user-modified',
                  data=as_json,
                  content_type='application/json',
                  headers={'X-Webhook-HMAC': mac.hexdigest()},
                  expected_status=204)

        # Check that the user has been created, and the existing user has not been touched.
        db_user = self.fetch_user_from_db(self.uid)
        self.assertEqual('old@email.address', db_user['email'])
        self.assertEqual('คนรักของผัดไทย', db_user['full_name'])
        self.assertEqual({'subscriber'}, set(db_user['roles']))

        users_coll = self.app.db('users')
        new_user = users_coll.find_one({'email': 'new@email.address'})
        self.assertIsNotNone(new_user)
        self.assertEqual('new', new_user['username'])
        self.assertEqual('ကြယ်ဆွတ်', new_user['full_name'])
        self.assertEqual(['subscriber', 'has_subscription'], new_user['roles'])

    def test_create_renewable(self):
        payload = {'id': 1112333,
                   'old_email': 'unknown@email.address',
                   'full_name': 'ကြယ်ဆွတ်',
                   'email': 'new@email.address',
                   'roles': ['cloud_has_subscription']}
        as_json = json.dumps(payload).encode()
        mac = hmac.new(self.hmac_secret,
                       as_json, hashlib.sha256)
        self.post('/api/webhooks/user-modified',
                  data=as_json,
                  content_type='application/json',
                  headers={'X-Webhook-HMAC': mac.hexdigest()},
                  expected_status=204)

        # Check that the user has been created, and the existing user has not been touched.
        db_user = self.fetch_user_from_db(self.uid)
        self.assertEqual('old@email.address', db_user['email'])
        self.assertEqual('คนรักของผัดไทย', db_user['full_name'])
        self.assertEqual({'subscriber'}, set(db_user['roles']))

        users_coll = self.app.db('users')
        new_user = users_coll.find_one({'email': 'new@email.address'})
        self.assertIsNotNone(new_user)
        self.assertEqual('new', new_user['username'])
        self.assertEqual('ကြယ်ဆွတ်', new_user['full_name'])
        self.assertEqual(['has_subscription'], new_user['roles'])

    def test_no_full_name(self):
        """Blender ID doesn't enforce full names on creation."""
        payload = {'id': 1112333,
                   'old_email': 'unknown@email.address',
                   'full_name': '',
                   'email': 'new@email.address',
                   'roles': ['cloud_subscriber', 'cloud_has_subscription']}
        as_json = json.dumps(payload).encode()
        mac = hmac.new(self.hmac_secret,
                       as_json, hashlib.sha256)
        self.post('/api/webhooks/user-modified',
                  data=as_json,
                  content_type='application/json',
                  headers={'X-Webhook-HMAC': mac.hexdigest()},
                  expected_status=204)

        # Check that the user has been created correctly.
        users_coll = self.app.db('users')
        new_user = users_coll.find_one({'email': 'new@email.address'})
        self.assertIsNotNone(new_user)
        self.assertEqual('new', new_user['username'])
        self.assertEqual('new', new_user['full_name'])  # defaults to username
        self.assertEqual(['subscriber', 'has_subscription'], new_user['roles'])

    def test_no_create_when_not_subscriber(self):
        """Don't create local users when they are not subscriber."""
        payload = {'id': 1112333,
                   'old_email': 'unknown@email.address',
                   'full_name': 'ကြယ်ဆွတ်',
                   'email': 'new@email.address',
                   'roles': ['blender_network']}
        as_json = json.dumps(payload).encode()
        mac = hmac.new(self.hmac_secret,
                       as_json, hashlib.sha256)
        self.post('/api/webhooks/user-modified',
                  data=as_json,
                  content_type='application/json',
                  headers={'X-Webhook-HMAC': mac.hexdigest()},
                  expected_status=204)

        # Check that the user has been not been created, and the existing user has not been touched.
        db_user = self.fetch_user_from_db(self.uid)
        self.assertEqual('old@email.address', db_user['email'])
        self.assertEqual('คนรักของผัดไทย', db_user['full_name'])
        self.assertEqual({'subscriber'}, set(db_user['roles']))

        users_coll = self.app.db('users')
        new_user = users_coll.find_one({'email': 'new@email.address'})
        self.assertIsNone(new_user)
