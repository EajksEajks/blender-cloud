"""Commandline interface for Attract."""

from __future__ import print_function, division

import copy
import logging

from bson import ObjectId
from eve.methods.put import put_internal
from flask import current_app
from pillar.cli import manager

log = logging.getLogger(__name__)


def _get_project(project_url):
    """Find a project in the database, or SystemExit()s.

    :param project_url: UUID of the project
    :type: str
    :return: the project
    :rtype: dict
    """

    projects_collection = current_app.data.driver.db['projects']

    # Find the project in the database.
    project = projects_collection.find_one({'url': project_url})
    if not project:
        log.error('Project %s does not exist.', project_url)
        raise SystemExit()

    return project


def _update_project(project):
    """Updates a project in the database, or SystemExit()s.

    :param project: the project data, should be the entire project document
    :type: dict
    :return: the project
    :rtype: dict
    """

    from pillar.api.utils import remove_private_keys
    from pillar.api.utils import authentication

    authentication.force_cli_user()

    project_id = ObjectId(project['_id'])
    project = remove_private_keys(project)
    result, _, _, status_code = put_internal('projects', project, _id=project_id)

    if status_code != 200:
        log.error("Can't update project %s, issues: %s", project_id, result)
        raise SystemExit()


@manager.command
@manager.option('-r', '--replace', dest='replace', action='store_true', default=False)
def setup_for_attract(project_url, replace=False):
    """Adds Attract node types to the project.

    Use --replace to replace pre-existing Attract node types
    (by default already existing Attract node types are skipped).
    """

    from .node_types import NODE_TYPES

    # Copy permissions from the project, then give everyone with PUT
    # access also DELETE access.
    project = _get_project(project_url)
    permissions = copy.deepcopy(project['permissions'])

    for perms in permissions.values():
        for perm in perms:
            methods = set(perm['methods'])
            if 'PUT' not in perm['methods']:
                continue
            methods.add('DELETE')
            perm['methods'] = list(methods)

    # Make a copy of the node types when setting the permissions, as
    # we don't want to mutate the global node type objects.
    node_types = (dict(permissions=permissions, **nt) for nt in NODE_TYPES)

    # Add the missing node types.
    for node_type in node_types:
        found = [nt for nt in project['node_types']
                 if nt['name'] == node_type['name']]
        if found:
            assert len(found) == 1, 'node type name should be unique (found %ix)' % len(found)

            # TODO: validate that the node type contains all the properties Attract needs.
            if replace:
                log.info('Replacing existing node type %s', node_type['name'])
                project['node_types'].remove(found[0])
            else:
                continue

        project['node_types'].append(node_type)

    _update_project(project)

    log.info('Project %s was updated for Attract.', project_url)
