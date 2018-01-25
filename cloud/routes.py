import functools
import json
import logging
import typing

from flask_login import current_user, login_required
import flask
from flask import Blueprint, render_template, redirect, session, url_for, abort, flash
from pillarsdk import Node, Project, User, exceptions as sdk_exceptions, Group
from pillarsdk.exceptions import ResourceNotFound

from pillar import current_app
import pillar.api
from pillar.web.users import forms
from pillar.web.utils import system_util, get_file, current_user_is_authenticated
from pillar.web.utils import attach_project_pictures
from pillar.web.settings import blueprint as blueprint_settings
from pillar.web.nodes.routes import url_for_node
from pillar.web.nodes.custom.comments import render_comments_for_node


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
    latest_posts = Node.all({
        'projection': {
            'name': 1,
            'project': 1,
            'node_type': 1,
            'picture': 1,
            'properties.url': 1,
            'properties.content': 1,
            'properties.attachments': 1
        },

        'where': {'node_type': 'post', 'properties.status': 'published'},
        'embedded': {'project': 1},
        'sort': '-_created',
        'max_results': '3'
    }, api=api)

    # Append picture Files to last_posts
    for post in latest_posts._items:
        post.picture = get_file(post.picture, api=api)
        post.url = url_for_node(node=post)

        # Render attachments
        try:
            post_contents = post['properties']['content']
        except KeyError:
            log.warning('Blog post %s has no content', post._id)
        else:
            post['properties']['content'] = pillar.web.nodes.attachments.render_attachments(
                post, post_contents)

    # Get latest assets added to any project
    latest_assets = Node.latest('assets', api=api)

    # Append picture Files to latest_assets
    for asset in latest_assets._items:
        asset.picture = get_file(asset.picture, api=api)
        asset.url = url_for_node(node=asset)

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

    # Merge latest assets and comments into one activity stream.
    def sort_key(item):
        return item._created

    activity_stream = sorted(latest_assets._items, key=sort_key, reverse=True)

    for node in activity_stream:
        node.url = url_for_node(node=node)

    return dict(
        main_project=main_project,
        latest_posts=latest_posts._items,
        latest_comments=latest_comments._items,
        activity_stream=activity_stream,
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
        projects = get_projects('film')
        return render_template(
            'projects_index_collection.html',
            title='open-projects',
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
        {'$project': {'url': True,
                      'name': True,
                      'summary': True,
                      'picture_square': True,
                      'node._id': True,
                      'node.name': True,
                      'node.permissions': True,
                      'node.picture': True,
                      'node.properties.content_type': True,
                      'node.properties.url': True}},
    ])

    featured_node_documents = []
    api = system_util.pillar_api()
    for node_info in featured_nodes:
        # Turn the project-with-node doc into a node-with-project doc.
        node_document = node_info.pop('node')
        node_document['project'] = node_info

        node = Node(node_document)
        node.picture = get_file(node.picture, api=api)
        node.url = url_for_node(node=node)
        node.project.url = url_for('projects.view', project_url=node.project.url)
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


@blueprint.route('/nodes/<string(length=24):node_id>/comments')
def comments_for_node(node_id):
    """Overrides the default render_comments_for_node.

    This is done in order to extend can_post_comments by requiring the
    subscriber capability.
    """

    api = system_util.pillar_api()

    node = Node.find(node_id, api=api)
    project = Project({'_id': node.project})
    can_post_comments = project.node_type_has_method('comment', 'POST', api=api)
    can_comment_override = flask.request.args.get('can_comment', 'True') == 'True'
    can_post_comments = can_post_comments and can_comment_override and current_user.has_cap(
        'subscriber')

    return render_comments_for_node(node_id, can_post_comments=can_post_comments)


def setup_app(app):
    global _homepage_context
    cached = app.cache.cached(timeout=300)
    _homepage_context = cached(_homepage_context)
