"""Setting up projects for Blender Cloud."""

import logging

from bson import ObjectId
from eve.methods.put import put_internal
from flask import current_app

from pillar.api.utils import remove_private_keys
from . import EXTENSION_NAME

log = logging.getLogger(__name__)


def setup_for_film(project_url):
    """Add Blender Cloud extension_props specific for film projects.

    Returns the updated project.
    """

    projects_collection = current_app.data.driver.db['projects']

    # Find the project in the database.
    project = projects_collection.find_one({'url': project_url})
    if not project:
        raise RuntimeError('Project %s does not exist.' % project_url)

    # Set default extension properties. Be careful not to overwrite any properties that
    # are already there.
    all_extension_props = project.setdefault('extension_props', {})
    cloud_extension_props = {
        'category': 'film',
        'theme_css': '',
        # The accent color (can be 'blue' or '#FFBBAA' or 'rgba(1, 1, 1, 1)
        'theme_color': '',
        'is_in_production': False,
        'video_url': '',  # Oembeddable url
        'poster': None,  # File ObjectId
        'logo': None,  # File ObjectId
        # TODO(fsiddi) when we introduce other setup_for_* in Blender Cloud, make available
        # at a higher scope
        'is_featured': False,
    }

    all_extension_props.setdefault(EXTENSION_NAME, cloud_extension_props)

    project_id = ObjectId(project['_id'])
    project = remove_private_keys(project)
    result, _, _, status_code = put_internal('projects', project, _id=project_id)

    if status_code != 200:
        raise RuntimeError("Can't update project %s, issues: %s", project_id, result)

    log.info('Project %s was updated for Blender Cloud.', project_url)
