"""Blender Store interface."""

import logging
import typing

from pillar import current_app

log = logging.getLogger(__name__)


def fetch_subscription_info(email: str) -> typing.Optional[dict]:
    """Returns the user info dict from the external subscriptions management server.

    :returns: the store user info, or None if the user can't be found or there
        was an error communicating. A dict like this is returned:
        {
            "shop_id": 700,
            "cloud_access": 1,
            "paid_balance": 314.75,
            "balance_currency": "EUR",
            "start_date": "2014-08-25 17:05:46",
            "expiration_date": "2016-08-24 13:38:45",
            "subscription_status": "wc-active",
            "expiration_date_approximate": true
        }
    """

    from requests.adapters import HTTPAdapter
    import requests.exceptions

    external_subscriptions_server = current_app.config['EXTERNAL_SUBSCRIPTIONS_MANAGEMENT_SERVER']

    if log.isEnabledFor(logging.DEBUG):
        import urllib.parse

        log_email = urllib.parse.quote(email)
        log.debug('Connecting to store at %s?blenderid=%s',
                  external_subscriptions_server, log_email)

    # Retry a few times when contacting the store.
    s = requests.Session()
    s.mount(external_subscriptions_server, HTTPAdapter(max_retries=5))

    try:
        r = s.get(external_subscriptions_server,
                  params={'blenderid': email},
                  verify=current_app.config['TLS_CERT_FILE'],
                  timeout=current_app.config.get('EXTERNAL_SUBSCRIPTIONS_TIMEOUT_SECS', 10))
    except requests.exceptions.ConnectionError as ex:
        log.error('Error connecting to %s: %s', external_subscriptions_server, ex)
        return None
    except requests.exceptions.Timeout as ex:
        log.error('Timeout communicating with %s: %s', external_subscriptions_server, ex)
        return None
    except requests.exceptions.RequestException as ex:
        log.error('Some error communicating with %s: %s', external_subscriptions_server, ex)
        return None

    if r.status_code != 200:
        log.warning("Error communicating with %s, code=%i, unable to check "
                    "subscription status of user %s",
                    external_subscriptions_server, r.status_code, email)
        return None

    store_user = r.json()

    if log.isEnabledFor(logging.DEBUG):
        import json
        log.debug('Received JSON from store API: %s',
                  json.dumps(store_user, sort_keys=False, indent=4))

    return store_user
