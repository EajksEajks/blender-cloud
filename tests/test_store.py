import requests.exceptions
import responses

from abstract_cloud_test import AbstractCloudTest


class SubscriptionInfoTest(AbstractCloudTest):
    def setUp(self, **kwargs):
        super().setUp(**kwargs)
        self.enter_app_context()
        self.srv = self.app.config['EXTERNAL_SUBSCRIPTIONS_MANAGEMENT_SERVER']

    @responses.activate
    def test_happy(self):
        api_payload = {"shop_id": 14447,
                       "cloud_access": 1,
                       "paid_balance": 198,
                       "balance_currency": "USD",
                       "start_date": "2016-01-09 17:24:27",
                       "expiration_date": "2018-01-09 16:25:04",
                       "subscription_status": "wc-active"}
        responses.add('GET', self.srv, json=api_payload)

        from cloud.store import fetch_subscription_info

        resp = fetch_subscription_info('exampleuser@example.com')
        self.assertEqual(resp, api_payload)

    @responses.activate
    def test_trouble_connecting(self):
        responses.add('GET', self.srv, body=requests.exceptions.ConnectionError('mocked i/o err'))

        from cloud.store import fetch_subscription_info

        resp = fetch_subscription_info('exampleuser@example.com')
        self.assertIsNone(resp)  # should not bubble the exception but just return None

    @responses.activate
    def test_bad_response_code(self):
        responses.add('GET', self.srv, status=500)

        from cloud.store import fetch_subscription_info

        resp = fetch_subscription_info('exampleuser@example.com')
        self.assertIsNone(resp)  # should not raise exception but just return None
