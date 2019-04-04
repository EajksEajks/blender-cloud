import functools
import json
import logging
import typing

import bson
from flask_login import login_required
import flask
import werkzeug.exceptions as wz_exceptions
from flask import Blueprint, render_template, redirect, session, url_for, abort, flash, request
from pillarsdk import Node, Project, User, exceptions as sdk_exceptions, Group
from pillarsdk.exceptions import ResourceNotFound

import pillar
import pillarsdk
from pillar import current_app
from pillar.api.utils import authorization
from pillar.auth import current_user
from pillar.web.users import forms
from pillar.web.utils import system_util, get_file, current_user_is_authenticated
from pillar.web.utils import attach_project_pictures
from pillar.web.settings import blueprint as blueprint_settings
from pillar.web.nodes.routes import url_for_node
from pillar.web.projects.routes import render_project
from pillar.web.projects.routes import find_project_or_404
from pillar.web.projects.routes import project_view

from cloud import current_cloud
from cloud.forms import FilmProjectForm
from . import EXTENSION_NAME

blueprint = Blueprint('cloud', __name__)
log = logging.getLogger(__name__)


@blueprint.route('/')
def homepage():
    if current_user.is_anonymous:
        return redirect(url_for('cloud.welcome'))

    return render_template(
        'homepage.html',
        api=system_util.pillar_api(),
        **_homepage_context(),
    )


def _homepage_context() -> dict:
    """Returns homepage template context variables."""

    # Get latest blog posts
    api = system_util.pillar_api()

    # Get latest comments to any node
    latest_comments = Node.latest('comments', api=api)

    # Get a list of random featured assets
    random_featured = get_random_featured_nodes()

    # Parse results for replies
    to_remove = []

    @functools.lru_cache()
    def _find_parent(parent_node_id) -> Node:
        return Node.find(parent_node_id,
                         {'projection': {
                             '_id': 1,
                             'name': 1,
                             'node_type': 1,
                             'project': 1,
                             'parent': 1,
                             'properties.url': 1,
                         }},
                         api=api)

    for idx, comment in enumerate(latest_comments._items):
        if comment.properties.is_reply:
            try:
                comment.attached_to = _find_parent(comment.parent.parent)
            except ResourceNotFound:
                # Remove this comment
                to_remove.append(idx)
        else:
            comment.attached_to = comment.parent

    for idx in reversed(to_remove):
        del latest_comments._items[idx]

    for comment in latest_comments._items:
        if not comment.attached_to:
            continue
        comment.attached_to.url = url_for_node(node=comment.attached_to)
        comment.url = url_for_node(node=comment)

    main_project = Project.find(current_app.config['MAIN_PROJECT_ID'], api=api)
    main_project.picture_header = get_file(main_project.picture_header, api=api)

    return dict(
        main_project=main_project,
        latest_comments=latest_comments._items,
        random_featured=random_featured)


@blueprint.route('/login')
def login():
    from flask import request

    if request.args.get('force'):
        log.debug('Forcing logout of user before rendering login page.')
        pillar.auth.logout_user()

    next_after_login = request.args.get('next')

    if not next_after_login:
        next_after_login = request.referrer

    session['next_after_login'] = next_after_login
    return redirect(url_for('users.oauth_authorize', provider='blender-id'))


@blueprint.route('/welcome')
def welcome():
    # Workaround to cache rendering of a page if user not logged in
    @current_app.cache.cached(timeout=3600, unless=current_user_is_authenticated)
    def render_page():
        return render_template('welcome.html')

    return render_page()


@blueprint.route('/about')
def about():
    return render_template('about.html')


@blueprint.route('/services')
def services():
    return render_template('services.html')


@blueprint.route('/learn')
def learn():
    return render_template('learn.html')


@blueprint.route('/libraries')
def libraries():
    return render_template('libraries.html')


@blueprint.route('/stats')
def stats():
    return render_template('stats.html')


@blueprint.route('/join')
def join():
    """Join page"""
    return redirect('https://store.blender.org/product/membership/')


@blueprint.route('/renew')
def renew_subscription():
    return render_template('renew_subscription.html')


def get_projects(category):
    """Utility to get projects based on category. Should be moved on the API
    and improved with more extensive filtering capabilities.
    """
    api = system_util.pillar_api()
    projects = Project.all({
        'where': {
            'category': category,
            'is_private': False},
        'sort': '-_created',
    }, api=api)
    for project in projects._items:
        attach_project_pictures(project, api)
    return projects


@blueprint.route('/courses')
def courses():
    @current_app.cache.cached(timeout=3600, unless=current_user_is_authenticated)
    def render_page():
        projects = get_projects('course')
        return render_template(
            'projects_index_collection.html',
            title='courses',
            projects=projects._items,
            api=system_util.pillar_api())

    return render_page()


@blueprint.route('/open-projects')
def open_projects():
    @current_app.cache.cached(timeout=3600, unless=current_user_is_authenticated)
    def render_page():
        api = system_util.pillar_api()
        projects = Project.all({
            'where': {
                'category': 'film',
                'is_private': False
            },
            'sort': '-_created',
        }, api=api)
        for project in projects._items:
            # Attach poster file (ensure the extension_props.cloud.poster
            # attributes exists)
            try:
                # If the attribute exists, but is None, continue
                if not project['extension_props'][EXTENSION_NAME]['poster']:
                    continue
                # Fetch the file and embed it in the document
                project.extension_props.cloud.poster = get_file(
                    project.extension_props.cloud.poster, api=api)
                # Add convenience attribute that specifies the presence of the
                # poster file
                project.has_poster = True
            # If there was a key error because one of the nested attributes is
            # missing,
            except KeyError:
                continue

        return render_template(
            'films.html',
            title='films',
            projects=projects._items,
            api=system_util.pillar_api())

    return render_page()


@blueprint.route('/workshops')
def workshops():
    @current_app.cache.cached(timeout=3600, unless=current_user_is_authenticated)
    def render_page():
        projects = get_projects('workshop')
        return render_template(
            'projects_index_collection.html',
            title='workshops',
            projects=projects._items,
            api=system_util.pillar_api())

    return render_page()


def get_random_featured_nodes() -> typing.List[dict]:
    """Returns a list of project/node combinations for featured nodes.

    A random subset of 3 featured nodes from all public projects is returned.
    Assumes that the user actually has access to the public projects' nodes.

    The dict is a node, with a 'project' key that contains a projected project.
    """

    proj_coll = current_app.db('projects')
    featured_nodes = proj_coll.aggregate([
        {'$match': {'is_private': False}},
        {'$project': {'nodes_featured': True,
                      'url': True,
                      'name': True,
                      'summary': True,
                      'picture_square': True}},
        {'$unwind': {'path': '$nodes_featured'}},
        {'$sample': {'size': 3}},
        {'$lookup': {'from': 'nodes',
                     'localField': 'nodes_featured',
                     'foreignField': '_id',
                     'as': 'node'}},
        {'$unwind': {'path': '$node'}},
        {'$match': {'node._deleted': {'$ne': True}}},
        {'$project': {'url': True,
                      'name': True,
                      'summary': True,
                      'picture_square': True,
                      'node._id': True,
                      'node.name': True,
                      'node.permissions': True,
                      'node.picture': True,
                      'node.properties.content_type': True,
                      'node.properties.duration_seconds': True,
                      'node.properties.url': True,
                      'node._created': True,
                      }
         },
    ])

    featured_node_documents = []
    api = system_util.pillar_api()
    for node_info in featured_nodes:
        # Turn the project-with-node doc into a node-with-project doc.
        node_document = node_info.pop('node')
        node_document['project'] = node_info
        node_document['_id'] = str(node_document['_id'])

        node = Node(node_document)
        node.picture = get_file(node.picture, api=api)
        node.project.picture_square = get_file(node.project.picture_square, api=api)
        featured_node_documents.append(node)

    return featured_node_documents


@blueprint_settings.route('/emails', methods=['GET', 'POST'])
@login_required
def emails():
    """Main email settings.
    """
    if current_user.has_role('protected'):
        return abort(404)  # TODO: make this 403, handle template properly
    api = system_util.pillar_api()
    user = User.find(current_user.objectid, api=api)

    # Force creation of settings for the user (safely remove this code once
    # implemented on account creation level, and after adding settings to all
    # existing users)
    if not user.settings:
        user.settings = dict(email_communications=1)
        user.update(api=api)

    if user.settings.email_communications is None:
        user.settings.email_communications = 1
        user.update(api=api)

    # Generate form
    form = forms.UserSettingsEmailsForm(
        email_communications=user.settings.email_communications)

    if form.validate_on_submit():
        try:
            user.settings.email_communications = form.email_communications.data
            user.update(api=api)
            flash("Profile updated", 'success')
        except sdk_exceptions.ResourceInvalid as e:
            message = json.loads(e.content)
            flash(message)

    return render_template('users/settings/emails.html', form=form, title='emails')


@blueprint_settings.route('/billing')
@login_required
def billing():
    """View the subscription status of a user
    """
    from . import store

    log.debug('START OF REQUEST')

    if current_user.has_role('protected'):
        return abort(404)  # TODO: make this 403, handle template properly

    expiration_date = 'No subscription to expire'

    # Classify the user based on their roles and capabilities
    cap_subs = current_user.has_cap('subscriber')
    if current_user.has_role('demo'):
        user_cls = 'demo'
    elif not cap_subs and current_user.has_cap('can-renew-subscription'):
        # This user has an inactive but renewable subscription.
        user_cls = 'subscriber-expired'
    elif cap_subs:
        if current_user.has_role('subscriber'):
            # This user pays for their own subscription. Only in this case do we need to fetch
            # the expiration date from the Store.
            user_cls = 'subscriber'
            store_user = store.fetch_subscription_info(current_user.email)
            if store_user is None:
                expiration_date = 'Unable to reach Blender Store to check'
            else:
                expiration_date = store_user['expiration_date'][:10]

        elif current_user.has_role('org-subscriber'):
            # An organisation pays for this subscription.
            user_cls = 'subscriber-org'
        else:
            # This user gets the subscription cap from somewhere else (like an organisation).
            user_cls = 'subscriber-other'
    else:
        user_cls = 'outsider'

    return render_template(
        'users/settings/billing.html',
        user_cls=user_cls,
        expiration_date=expiration_date,
        title='billing')


@blueprint.route('/terms-and-conditions')
def terms_and_conditions():
    return render_template('terms_and_conditions.html')


@blueprint.route('/privacy')
def privacy():
    return render_template('privacy.html')


@blueprint.route('/production')
def production():
    return render_template(
        'production.html',
        title='production')


@blueprint.route('/emails/welcome.send')
@login_required
def emails_welcome_send():
    from cloud import email
    email.queue_welcome_mail(current_user)
    return f'queued mail to {current_user.email}'


@blueprint.route('/emails/welcome.html')
@login_required
def emails_welcome_html():
    return render_template('emails/welcome.html',
                           subject='Welcome to Blender Cloud',
                           user=current_user)


@blueprint.route('/emails/welcome.txt')
@login_required
def emails_welcome_txt():
    txt = render_template('emails/welcome.txt',
                          subject='Welcome to Blender Cloud',
                          user=current_user)
    return flask.Response(txt, content_type='text/plain; charset=utf-8')


@blueprint.route('/p/<project_url>')
def project_landing(project_url):
    """Override Pillar project_view endpoint completely.

    The first part of the function is identical to the one in Pillar, but the
    second part (starting with 'Load custom project properties') extends the
    behaviour to support film project landing pages.
    """

    template_name = None
    if request.args.get('format') == 'jstree':
        log.warning('projects.view(%r) endpoint called with format=jstree, '
                    'redirecting to proper endpoint. URL is %s; referrer is %s',
                    project_url, request.url, request.referrer)
        return redirect(url_for('projects.jstree', project_url=project_url))

    api = system_util.pillar_api()
    project = find_project_or_404(project_url,
                                  embedded={'header_node': 1},
                                  api=api)

    # Load the header video file, if there is any.
    header_video_file = None
    header_video_node = None
    if project.header_node and project.header_node.node_type == 'asset' and \
            project.header_node.properties.content_type == 'video':
        header_video_node = project.header_node
        header_video_file = get_file(project.header_node.properties.file)
        header_video_node.picture = get_file(header_video_node.picture)

    extra_context = {
        'header_video_file': header_video_file,
        'header_video_node': header_video_node}

    # Load custom project properties. If the project has a 'cloud' extension prop,
    # render it using the projects/landing.html template and try to attach a
    # number of additional attributes (pages, images, etc.).
    if 'extension_props' in project and EXTENSION_NAME in project['extension_props']:
        extension_props = project['extension_props'][EXTENSION_NAME]
        file_props = {'picture_16_9', 'logo'}
        for f in file_props:
            if f in extension_props:
                extension_props[f] = get_file(extension_props[f])

        pages = Node.all({
            'where': {
                'project': project._id,
                'node_type': 'page',
                '_deleted': {'$ne': True}},
            'projection': {'name': 1}}, api=api)

        extra_context.update({'pages': pages._items})
        template_name = 'projects/landing.html'

    return render_project(project, api,
                          extra_context=extra_context,
                          template_name=template_name)


@blueprint.route('/p/<project_url>/browse')
@project_view()
def project_browse(project: pillarsdk.Project):
    """Project view displaying all top-level nodes.

    We render a regular project view, but we introduce an additional template
    variable: browse. By doing that we prevent the regular project view
    from loading and fetch via AJAX a "group" node-like view instead (see
    project_browse_view_nodes).
    """
    return render_template(
        'projects/view.html',
        api=system_util.pillar_api(),
        project=project,
        node=None,
        show_project=True,
        browse=True,
        og_picture=None,
        navigation_links=[],
        extension_sidebar_links=None,)


@blueprint.route('/p/<project_url>/browse/nodes')
@project_view()
def project_browse_view_nodes(project: pillarsdk.Project):
    """Display top-level nodes for a Project.

    This view is always meant to be served embedded, as part of project_browse.
    """
    api = system_util.pillar_api()
    # Get top level nodes
    projection = {
        'project': 1,
        'name': 1,
        'picture': 1,
        'node_type': 1,
        'properties.order': 1,
        'properties.status': 1,
        'user': 1,
        'properties.content_type': 1,
        'permissions.world': 1}
    where = {
        'project': project['_id'],
        'parent': {'$exists': False},
        'properties.status': 'published',
        '_deleted': {'$ne': True}
    }

    try:
        nodes = Node.all({
            'projection': projection,
            'where': where,
            'sort': [('properties.order', 1), ('name', 1)]}, api=api)
    except pillarsdk.exceptions.ForbiddenAccess:
        return render_template('errors/403_embed.html')
    nodes = nodes._items

    for child in nodes:
        child.picture = get_file(child.picture, api=api)
    return render_template(
        'projects/browse_embed.html',
        nodes=nodes)


def project_settings(project: pillarsdk.Project, **template_args: dict):
    """Renders the project settings page for Blender Cloud projects.

    If the project has been setup for Blender Cloud, check for the cloud.project_type
    property, to render the proper form.
    """

    # Based on the project state, we can render a different template.
    if not current_cloud.is_cloud_project(project):
        return render_template('project_settings/offer_setup.html',
                               project=project, **template_args)

    cloud_props = project['extension_props'][EXTENSION_NAME]

    project_type = cloud_props['project_type']
    if project_type != 'film':
        log.error('No interface available to edit %s projects, yet' % project_type)

    form = FilmProjectForm()

    # Iterate over the form fields and set the data if exists in the project document
    for field_name in form.data:
        if field_name not in cloud_props:
            continue
        # Skip csrf_token field
        if field_name == 'csrf_token':
            continue
        form_field = getattr(form, field_name)
        form_field.data = cloud_props[field_name]

    return render_template('project_settings/settings.html',
                           project=project,
                           form=form,
                           **template_args)


@blueprint.route('/<project_url>/settings/film', methods=['POST'])
@authorization.require_login(require_cap='admin')
@project_view()
def save_film_settings(project: pillarsdk.Project):
    # Ensure that the project is setup for Cloud (see @attract_project_view for example)
    form = FilmProjectForm()
    if not form.validate_on_submit():
        log.debug('Form submission failed')
        # Return list of validation errors

    updated_extension_props = {}
    for field_name in form.data:
        # Skip csrf_token field
        if field_name == 'csrf_token':
            continue
        form_field = getattr(form, field_name)
        # TODO(fsiddi) if form_field type is FileSelectField, convert it to ObjectId
        # Currently this raises TypeError: Object of type 'ObjectId' is not JSON serializable

        if form_field.data == '':
            form_field.data = None
        updated_extension_props[field_name] = form_field.data

    # Update extension props and save project
    extension_props = project['extension_props'][EXTENSION_NAME]
    # Project is a Resource, so we update properties iteratively
    for k, v in updated_extension_props.items():
        extension_props[k] = v
    project.update(api=system_util.pillar_api())
    return '', 204


@blueprint.route('/<project_url>/setup-for-film', methods=['POST'])
@login_required
@project_view()
def setup_for_film(project: pillarsdk.Project):
    import cloud.setup

    project_id = project._id

    if not project.has_method('PUT'):
        log.warning('User %s tries to set up project %s for Blender Cloud, but has no PUT rights.',
                    current_user, project_id)
        raise wz_exceptions.Forbidden()

    log.info('User %s sets up project %s for Blender Cloud', current_user, project_id)
    cloud.setup.setup_for_film(project.url)

    return '', 204


def setup_app(app):
    global _homepage_context
    cached = app.cache.cached(timeout=300)
    _homepage_context = cached(_homepage_context)
