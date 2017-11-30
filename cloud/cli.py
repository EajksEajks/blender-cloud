#!/usr/bin/env python

import logging
from urllib.parse import urljoin

from flask import current_app
from flask_script import Manager
import requests

from pillar.cli import manager
from pillar.api import service

log = logging.getLogger(__name__)

manager_cloud = Manager(
    current_app, usage="Blender Cloud scripts")


@manager_cloud.command
def create_groups():
    """Creates the admin/demo/subscriber groups."""

    import pprint

    group_ids = {}
    groups_coll = current_app.db('groups')

    for group_name in ['admin', 'demo', 'subscriber']:
        if groups_coll.find({'name': group_name}).count():
            log.info('Group %s already exists, skipping', group_name)
            continue
        result = groups_coll.insert_one({'name': group_name})
        group_ids[group_name] = result.inserted_id

    service.fetch_role_to_group_id_map()
    log.info('Created groups:\n%s', pprint.pformat(group_ids))


@manager_cloud.command
def reconcile_subscribers():
    """For every user, check their subscription status with the store."""

    import threading
    import concurrent.futures

    from pillar.auth import UserClass
    from pillar.api.blender_cloud.subscription import do_update_subscription

    sessions = threading.local()

    service.fetch_role_to_group_id_map()

    users_coll = current_app.data.driver.db['users']
    found = users_coll.find({'auth.provider': 'blender-id'})
    count_users = found.count()
    count_skipped = count_processed = 0
    log.info('Processing %i users', count_users)

    lock = threading.Lock()

    real_current_app = current_app._get_current_object()

    api_token = real_current_app.config['BLENDER_ID_USER_INFO_TOKEN']
    api_url = real_current_app.config['BLENDER_ID_USER_INFO_API']

    def do_user(idx, user):
        nonlocal count_skipped, count_processed

        log.info('Processing %i/%i %s', idx + 1, count_users, user['email'])

        # Get the Requests session for this thread.
        try:
            sess = sessions.session
        except AttributeError:
            sess = sessions.session = requests.Session()

        # Get the info from Blender ID
        bid_user_ids = [auth['user_id']
                        for auth in user['auth']
                        if auth['provider'] == 'blender-id']
        if not bid_user_ids:
            with lock:
                count_skipped += 1
            return
        bid_user_id = bid_user_ids[0]

        url = urljoin(api_url, bid_user_id)
        resp = sess.get(url, headers={'Authorization': f'Bearer {api_token}'})

        if resp.status_code == 404:
            log.info('User %s with Blender ID %s not found, skipping', user['email'], bid_user_id)
            with lock:
                count_skipped += 1
            return

        if resp.status_code != 200:
            log.error('Unable to reach Blender ID (code %d), aborting', resp.status_code)
            with lock:
                count_skipped += 1
            return

        bid_user = resp.json()
        if not bid_user:
            log.error('Unable to parse response for user %s, aborting', user['email'])
            with lock:
                count_skipped += 1
            return

        # Actually update the user, and do it thread-safe just to be sure.
        with real_current_app.app_context():
            local_user = UserClass.construct('', user)
            with lock:
                do_update_subscription(local_user, bid_user)
                count_processed += 1

    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        future_to_user = {executor.submit(do_user, idx, user): user
                          for idx, user in enumerate(found)}
        for future in concurrent.futures.as_completed(future_to_user):
            user = future_to_user[future]
            try:
                future.result()
            except Exception as ex:
                log.exception('Error updating user %s', user)

    log.info('Done reconciling %d subscribers', count_users)
    log.info('    processed: %d', count_processed)
    log.info('    skipped  : %d', count_skipped)


manager.add_command("cloud", manager_cloud)
