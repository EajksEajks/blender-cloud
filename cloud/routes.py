import itertools
import json
import logging

import pillar.api
from pillar.web.users import forms

from pillarsdk import Node, Project, User, exceptions as sdk_exceptions, Group
from pillarsdk.exceptions import ResourceNotFound
from flask_login import current_user, login_required
from flask import Blueprint, current_app, render_template, redirect, session, url_for, abort, flash
from pillar.web.utils import system_util, get_file, current_user_is_authenticated
from pillar.web.utils import attach_project_pictures
from pillar.web.settings import blueprint as blueprint_settings

blueprint = Blueprint('cloud', __name__)
log = logging.getLogger(__name__)


@blueprint.route('/')
def homepage():

    if current_user.is_anonymous:
        return redirect(url_for('cloud.welcome'))

    # Get latest blog posts
    api = system_util.pillar_api()
    latest_posts = Node.all({
        'projection': {'name': 1, 'project': 1, 'node_type': 1,
                       'picture': 1, 'properties.status': 1, 'properties.url': 1},
        'where': {'node_type': 'post', 'properties.status': 'published'},
        'embedded': {'project': 1},
        'sort': '-_created',
        'max_results': '5'
        }, api=api)

    # Append picture Files to last_posts
    for post in latest_posts._items:
        post.picture = get_file(post.picture, api=api)

    # Get latest assets added to any project
    latest_assets = Node.latest('assets', api=api)

    # Append picture Files to latest_assets
    for asset in latest_assets._items:
        asset.picture = get_file(asset.picture, api=api)

    # Get latest comments to any node
    latest_comments = Node.latest('comments', api=api)

    # Get a list of random featured assets
    random_featured = get_random_featured_nodes()

    # Parse results for replies
    to_remove = []
    for idx, comment in enumerate(latest_comments._items):
        if comment.properties.is_reply:
            try:
                comment.attached_to = Node.find(comment.parent.parent,
                                                {'projection': {
                                                    '_id': 1,
                                                    'name': 1,
                                                }},
                                                api=api)
            except ResourceNotFound:
                # Remove this comment
                to_remove.append(idx)
        else:
            comment.attached_to = comment.parent

    for idx in reversed(to_remove):
        del latest_comments._items[idx]

    main_project = Project.find(current_app.config['MAIN_PROJECT_ID'], api=api)
    main_project.picture_header = get_file(main_project.picture_header, api=api)

    # Merge latest assets and comments into one activity stream.
    def sort_key(item):
        return item._created

    activities = itertools.chain(latest_assets._items,
                                 latest_comments._items)
    activity_stream = sorted(activities, key=sort_key, reverse=True)

    return render_template(
        'homepage.html',
        main_project=main_project,
        latest_posts=latest_posts._items,
        activity_stream=activity_stream,
        random_featured=random_featured,
        api=api)


@blueprint.route('/login')
def login():
    from flask import request

    next_after_login = request.args.get('next')

    # Redirect to /welcome if explicitly given, but not when falling back to the referrer.
    if not next_after_login:
        url_for_welcome = url_for('cloud.welcome', _external=True)
        if request.referrer == url_for_welcome:
            next_after_login = '/'
        else:
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


@blueprint.route('/join')
def join():
    """Join page"""
    return redirect('https://store.blender.org/product/membership/')


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


def get_random_featured_nodes():

    import random

    api = system_util.pillar_api()
    projects = Project.all({
        'projection': {'nodes_featured': 1},
        'where': {'is_private': False},
        'max_results': '15'
        }, api=api)

    featured_nodes = (p.nodes_featured for p in projects._items if p.nodes_featured)
    featured_nodes = [item for sublist in featured_nodes for item in sublist]
    if len(featured_nodes) > 3:
        featured_nodes = random.sample(featured_nodes, 3)

    featured_node_documents = []

    for node in featured_nodes:
        node_document = Node.find(node, {
                'projection': {'name': 1, 'project': 1, 'picture': 1,
                                'properties.content_type': 1, 'properties.url': 1},
                'embedded': {'project': 1}
            }, api=api)

        node_document.picture = get_file(node_document.picture, api=api)
        featured_node_documents.append(node_document)

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
    if current_user.has_role('protected'):
        return abort(404)  # TODO: make this 403, handle template properly
    api = system_util.pillar_api()
    user = User.find(current_user.objectid, api=api)
    groups = []
    if user.groups:
        for group_id in user.groups:
            group = Group.find(group_id, api=api)
            groups.append(group.name)

    store_user = pillar.api.blender_cloud.subscription.fetch_subscription_info(user.email)

    return render_template(
        'users/settings/billing.html',
        store_user=store_user, groups=groups, title='billing')
