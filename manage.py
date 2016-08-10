#!/usr/bin/env python

import logging

import os
from eve.methods.post import post_internal
from eve.methods.put import put_internal
from flask.ext.script import Manager

from pillar import PillarServer

app = PillarServer('.')
app.process_extensions()

# Use a sensible default when running manage.py commands.
if not os.environ.get('EVE_SETTINGS'):
    settings_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                 'pillar', 'eve_settings.py')
    os.environ['EVE_SETTINGS'] = settings_path

manager = Manager(app)
log = logging.getLogger('manage')
log.setLevel(logging.INFO)


def put_item(collection, item):
    item_id = item['_id']
    internal_fields = ['_id', '_etag', '_updated', '_created']
    for field in internal_fields:
        item.pop(field, None)
    # print item
    # print type(item_id)
    p = put_internal(collection, item, **{'_id': item_id})
    if p[0]['_status'] == 'ERR':
        print(p)
        print(item)


@manager.command
def setup_db(admin_email):
    """Setup the database
    - Create admin, subscriber and demo Group collection
    - Create admin user (must use valid blender-id credentials)
    - Create one project
    """

    # Create default groups
    groups_list = []
    for group in ['admin', 'subscriber', 'demo']:
        g = {'name': group}
        g = post_internal('groups', g)
        groups_list.append(g[0]['_id'])
        print("Creating group {0}".format(group))

    # Create admin user
    user = {'username': admin_email,
            'groups': groups_list,
            'roles': ['admin', 'subscriber', 'demo'],
            'settings': {'email_communications': 1},
            'auth': [],
            'full_name': admin_email,
            'email': admin_email}
    result, _, _, status = post_internal('users', user)
    if status != 201:
        raise SystemExit('Error creating user {}: {}'.format(admin_email, result))
    user.update(result)
    print("Created user {0}".format(user['_id']))

    # Create a default project by faking a POST request.
    with app.test_request_context(data={'project_name': u'Default Project'}):
        from flask import g
        from pillar.api.projects.routes import create_project

        g.current_user = {'user_id': user['_id'],
                          'groups': user['groups'],
                          'roles': set(user['roles'])}

        create_project(overrides={'url': 'default-project',
                                  'is_private': False})


@manager.command
def register_local_user(email, password):
    from pillar.api.local_auth import create_local_user
    create_local_user(email, password)


if __name__ == '__main__':
    manager.run()
