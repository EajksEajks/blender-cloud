import logging
import datetime
import functools

from flask import Blueprint, jsonify
from cloud.stats import count_nodes, count_users, count_blender_sync

blueprint = Blueprint('cloud.stats', __name__, url_prefix='/s')

log = logging.getLogger(__name__)


@functools.lru_cache()
def get_stats(before: datetime.datetime):
    query_comments = {'node_type': 'comment'}
    query_assets = {'node_type': 'asset'}

    if before:
        d = {'_created': {'$lt': before}}
        query_comments.update(d)
        query_assets.update(d)

    stats = {
        'comments': count_nodes(query_comments),
        'assets': count_nodes(query_assets),
        'users_total': count_users(),
        'users_blender_sync': count_blender_sync(),
    }
    return stats


@blueprint.route('/')
@blueprint.route('/before/<int:before>')
def index(before: int=0):
    """
    This endpoint is queried on a daily basis by grafista to retrieve cloud usage
    stats. For assets and comments we take into considerations only those who belong
    to public projects.

    These is the data we retrieve

    - Comments count
    - Assets count (video, images and files)
    - Users count (subscribers count goes via store)
    - Blender Sync users
    """

    # TODO: Implement project-level metrics (and update ad every child update)
    if before:
        before = datetime.datetime.strptime(str(before), '%Y%m%d')
    else:
        today = datetime.date.today()
        before = datetime.datetime(today.year, today.month, today.day)

    return jsonify(get_stats(before))
