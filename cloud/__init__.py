import logging

import flask
from werkzeug.local import LocalProxy

import pillarsdk
import pillar.auth
from pillar.api.utils import authorization
from pillar.extension import PillarExtension

EXTENSION_NAME = 'cloud'


class CloudExtension(PillarExtension):
    has_context_processor = True
    user_roles = {'subscriber-pro', 'has_subscription'}
    user_roles_indexable = {'subscriber-pro', 'has_subscription'}

    user_caps = {
        'has_subscription': {'can-renew-subscription'},
    }

    def __init__(self):
        self._log = logging.getLogger('%s.CloudExtension' % __name__)

    @property
    def name(self):
        return EXTENSION_NAME

    def flask_config(self):
        """Returns extension-specific defaults for the Flask configuration.

        Use this to set sensible default values for configuration settings
        introduced by the extension.

        :rtype: dict
        """

        # Just so that it registers the management commands.
        from . import cli

        return {
            'EXTERNAL_SUBSCRIPTIONS_MANAGEMENT_SERVER': 'https://store.blender.org/api/',
            'EXTERNAL_SUBSCRIPTIONS_TIMEOUT_SECS': 10,
            'BLENDER_ID_WEBHOOK_USER_CHANGED_SECRET': 'oos9wah1Zoa0Yau6ahThohleiChephoi',
            'NODE_TAGS': ['animation', 'modeling', 'rigging', 'sculpting', 'shading', 'texturing', 'lighting',
                          'character-pipeline',  'effects', 'video-editing', 'digital-painting', 'production-design',
                          'walk-through'],
        }

    def eve_settings(self):
        """Returns extensions to the Eve settings.

        Currently only the DOMAIN key is used to insert new resources into
        Eve's configuration.

        :rtype: dict
        """

        return {}

    def blueprints(self):
        """Returns the list of top-level blueprints for the extension.

        These blueprints will be mounted at the url prefix given to
        app.load_extension().

        :rtype: list of flask.Blueprint objects.
        """
        from . import routes
        import cloud.stats.routes
        return [
            routes.blueprint,
            cloud.stats.routes.blueprint,
        ]

    @property
    def template_path(self):
        import os.path
        return os.path.join(os.path.dirname(__file__), 'templates')

    @property
    def static_path(self):
        import os.path
        return os.path.join(os.path.dirname(__file__), 'static')

    def context_processor(self):
        return {
            'current_user_is_subscriber': authorization.user_has_cap('subscriber')
        }

    def is_cloud_project(self, project):
        """Returns whether the project is set up for Blender Cloud.

        Requires the presence of the 'cloud' key in extension_props
        """

        if project.extension_props is None:
            # There are no extension_props on this project
            return False

        try:
            pprops = project.extension_props[EXTENSION_NAME]
        except AttributeError:
            self._log.warning("is_cloud_project: Project url=%r doesn't have any "
                              "extension properties.", project['url'])
            if self._log.isEnabledFor(logging.DEBUG):
                import pprint
                self._log.debug('Project: %s', pprint.pformat(project.to_dict()))
            return False
        except KeyError:
            # Not set up for Blender Cloud
            return False

        if pprops is None:
            self._log.debug("is_cloud_project: Project url=%r doesn't have Blender Cloud"
                            " extension properties.", project['url'])
            return False
        return True

    @property
    def has_project_settings(self) -> bool:
        # Only available for admins
        return pillar.auth.current_user.has_cap('admin')

    def project_settings(self, project: pillarsdk.Project, **template_args: dict) -> flask.Response:
        """Renders the project settings page for this extension.

        Set YourExtension.has_project_settings = True and Pillar will call this function.

        :param project: the project for which to render the settings.
        :param template_args: additional template arguments.
        :returns: a Flask HTTP response
        """

        from cloud.routes import project_settings

        return project_settings(project, **template_args)

    def setup_app(self, app):
        from . import routes, webhooks, eve_hooks, email

        routes.setup_app(app)
        app.register_api_blueprint(webhooks.blueprint, '/webhooks')
        eve_hooks.setup_app(app)
        email.setup_app(app)


def _get_current_cloud():
    """Returns the Cloud extension of the current application."""
    return flask.current_app.pillar_extensions[EXTENSION_NAME]


current_cloud = LocalProxy(_get_current_cloud)
"""Cloud extension of the current app."""
