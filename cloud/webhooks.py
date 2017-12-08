"""Blender ID webhooks."""

import hashlib
import hmac
import json
import logging

from flask_login import request
from flask import Blueprint
import werkzeug.exceptions as wz_exceptions

from pillar import current_app
from pillar.api.blender_cloud import subscription
from pillar.auth import UserClass

blueprint = Blueprint('cloud-webhooks', __name__)
log = logging.getLogger(__name__)
WEBHOOK_MAX_BODY_SIZE = 1024 * 10  # 10 kB is large enough for


def webhook_payload(hmac_secret: str) -> dict:
    """Obtains the webhook payload from the request, verifying its HMAC.

    :returns the webhook payload as dictionary.
    """
    # Check the content type
    if request.content_type != 'application/json':
        log.info('request from %s to %s had bad content type %s',
                 request.remote_addr, request, request.content_type)
        raise wz_exceptions.BadRequest('Content type not supported')

    # Check the length of the body
    if request.content_length > WEBHOOK_MAX_BODY_SIZE:
        raise wz_exceptions.BadRequest('Request too large')
    body = request.get_data()
    if len(body) > request.content_length:
        raise wz_exceptions.BadRequest('Larger body than Content-Length header')

    # Validate the request
    mac = hmac.new(hmac_secret.encode(), body, hashlib.sha256)
    req_hmac = request.headers.get('X-Webhook-HMAC', '')
    our_hmac = mac.hexdigest()
    if not hmac.compare_digest(req_hmac, our_hmac):
        log.info('request from %s to %s had bad HMAC %r, expected %r',
                 request.remote_addr, request, req_hmac, our_hmac)
        raise wz_exceptions.BadRequest('Bad HMAC')

    try:
        return json.loads(body)
    except json.JSONDecodeError as ex:
        log.warning('request from %s to %s had bad JSON: %s',
                    request.remote_addr, request, ex)
        raise wz_exceptions.BadRequest('Bad JSON')


@blueprint.route('/user-modified', methods=['POST'])
def user_modified():
    """Updates the local user based on the info from Blender ID."""
    my_log = log.getChild('user_modified')
    my_log.debug('Received request from %s', request.remote_addr)

    hmac_secret = current_app.config['BLENDER_ID_WEBHOOK_USER_CHANGED_SECRET']
    payload = webhook_payload(hmac_secret)

    my_log.info('payload: %s', payload)

    # Update the user
    users_coll = current_app.db('users')
    db_user = users_coll.find_one({'email': payload['old_email']})
    if not db_user:
        my_log.info('Received update for unknown user %r', payload['old_email'])
        return '', 204

    # Use direct database updates to change the email and full name.
    updates = {}
    if payload['old_email'] != payload['email']:
        my_log.info('User changed email from %s to %s', payload['old_email'], payload['email'])
        updates['email'] = payload['email']

    if payload['full_name'] != db_user['full_name']:
        my_log.info('User changed full name from %r to %r',
                    payload['full_name'], db_user['full_name'])
        if payload['full_name']:
            updates['full_name'] = payload['full_name']
        else:
            # Fall back to the username when the full name was erased.
            updates['full_name'] = db_user['username']

    if updates:
        update_res = users_coll.update_one({'_id': db_user['_id']},
                                           {'$set': updates})
        if update_res.matched_count != 1:
            my_log.error('Unable to find user %s to update, even though '
                         'we found them by email address %s',
                         db_user['_id'], payload['old_email'])

    # Defer to Pillar to do the role updates.
    local_user = UserClass.construct('', db_user)
    subscription.do_update_subscription(local_user, payload)

    return '', 204
