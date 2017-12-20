import hashlib
import hmac
import json
from abstract_cloud_test import AbstractCloudTest


class UserModifiedTest(AbstractCloudTest):
    def setUp(self, **kwargs):
        super().setUp(**kwargs)
        self.enter_app_context()
        self.hmac_secret = b'1234 je moeder'
        self.app.config['BLENDER_ID_WEBHOOK_USER_CHANGED_SECRET'] = self.hmac_secret.decode()
        self.uid = self.create_user(24 * 'a',
                                    roles={'subscriber'},
                                    email='old@email.address')

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
