"""Blender ID webhooks."""

import functools
import hashlib
import hmac
import json
import logging
import typing

from flask_login import request
from flask import Blueprint
import werkzeug.exceptions as wz_exceptions

from pillar import current_app
from pillar.api.blender_cloud import subscription
from pillar.api.utils.authentication import create_new_user_document, make_unique_username
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


def score(wh_payload: dict, user: dict) -> int:
    """Determine how likely it is that this is the correct user to modify.

    :param wh_payload: the info we received from Blender ID;
        see user_modified()
    :param user: the user in our database
    :return: the score for this user
    """

    bid_str = str(wh_payload['id'])
    try:
        match_on_bid = any((auth['provider'] == 'blender-id' and auth['user_id'] == bid_str)
                           for auth in user['auth'])
    except KeyError:
        match_on_bid = False

    match_on_old_email = user.get('email', 'none') == wh_payload.get('old_email', 'nothere')
    match_on_new_email = user.get('email', 'none') == wh_payload.get('email', 'nothere')
    return match_on_bid * 10 + match_on_old_email + match_on_new_email * 2


def insert_or_fetch_user(wh_payload: dict) -> typing.Optional[dict]:
    """Fetch the user from the DB or create it.

    Only creates it if the webhook payload indicates they could actually use
    Blender Cloud (i.e. demo or subscriber). This prevents us from creating
    Cloud accounts for Blender Network users.

    :returns the user document, or None when not created.
    """

    users_coll = current_app.db('users')
    my_log = log.getChild('insert_or_fetch_user')

    bid_str = str(wh_payload['id'])
    email = wh_payload['email']

    # Find the user by their Blender ID, or any of their email addresses.
    # We use one query to find all matching users. This is done as a
    # consistency check; if more than one user is returned, we know the
    # database is inconsistent with Blender ID and can emit a warning
    # about this.
    query = {'$or': [
        {'auth.provider': 'blender-id', 'auth.user_id': bid_str},
        {'email': {'$in': [wh_payload['old_email'], email]}},
    ]}
    db_users = users_coll.find(query)
    user_count = db_users.count()
    if user_count > 1:
        # Now we have to pay the price for finding users in one query; we
        # have to prioritise them and return the one we think is most reliable.
        calc_score = functools.partial(score, wh_payload)
        best_score = max(db_users, key=calc_score)

        my_log.error('%d users found for query %s, picking user %s (%s)',
                     user_count, query, best_score['_id'], best_score['email'])
        return best_score
    if user_count:
        db_user = db_users[0]
        my_log.debug('found user %s', db_user['email'])
        return db_user

    # Pretend to create the user, so that we can inspect the resulting
    # capabilities. This is more future-proof than looking at the list
    # of roles in the webhook payload.
    username = make_unique_username(email)
    user_doc = create_new_user_document(email, bid_str, username,
                                        provider='blender-id',
                                        full_name=wh_payload['full_name'])

    # Figure out the user's eventual roles. These aren't stored in the document yet,
    # because that's handled by the badger service.
    eventual_roles = [subscription.ROLES_BID_TO_PILLAR[r]
                      for r in wh_payload.get('roles', [])
                      if r in subscription.ROLES_BID_TO_PILLAR]
    user_ob = UserClass.construct('', user_doc)
    user_ob.roles = eventual_roles
    user_ob.collect_capabilities()
    create = (user_ob.has_cap('subscriber') or
              user_ob.has_cap('can-renew-subscription') or
              current_app.org_manager.user_is_unknown_member(email))
    if not create:
        my_log.info('Received update for unknown user %r without Cloud access (caps=%s)',
                    wh_payload['old_email'], user_ob.capabilities)
        return None

    # Actually create the user in the database.
    r, _, _, status = current_app.post_internal('users', user_doc)
    if status != 201:
        my_log.error('unable to create user %s: : %r %r', email, status, r)
        raise wz_exceptions.InternalServerError('unable to create user')

    user_doc.update(r)
    my_log.info('created user %r = %s to allow immediate Cloud access', email, user_doc['_id'])
    return user_doc


@blueprint.route('/user-modified', methods=['POST'])
def user_modified():
    """Update the local user based on the info from Blender ID.

    If the payload indicates the user has access to Blender Cloud (or at least
    a renewable subscription), create the user if not already in our DB.

    The payload we expect is a dictionary like:
    {'id': 12345,  # the user's ID in Blender ID
     'old_email': 'old@example.com',
     'full_name': 'Harry',
     'email': 'new@example'com,
     'roles': ['role1', 'role2', …]}
    """
    my_log = log.getChild('user_modified')
    my_log.debug('Received request from %s', request.remote_addr)

    hmac_secret = current_app.config['BLENDER_ID_WEBHOOK_USER_CHANGED_SECRET']
    payload = webhook_payload(hmac_secret)

    my_log.info('payload: %s', payload)

    # Update the user
    db_user = insert_or_fetch_user(payload)
    if not db_user:
        my_log.info('Received update for unknown user %r', payload['old_email'])
        return '', 204

    # Use direct database updates to change the email and full name.
    # Also updates the db_user dict so that local_user below will have
    # the updated information.
    updates = {}
    if db_user['email'] != payload['email']:
        my_log.info('User changed email from %s to %s', payload['old_email'], payload['email'])
        updates['email'] = payload['email']
        db_user['email'] = payload['email']

    if db_user['full_name'] != payload['full_name']:
        my_log.info('User changed full name from %r to %r',
                    db_user['full_name'], payload['full_name'])
        if payload['full_name']:
            updates['full_name'] = payload['full_name']
        else:
            # Fall back to the username when the full name was erased.
            updates['full_name'] = db_user['username']
        db_user['full_name'] = updates['full_name']

    if updates:
        users_coll = current_app.db('users')
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
