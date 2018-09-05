import logging
import datetime
import functools

from flask import Blueprint, jsonify

blueprint = Blueprint('cloud.tagged', __name__, url_prefix='/tagged')

log = logging.getLogger(__name__)


@blueprint.route('/')
def index():
    """Return all tagged assets as JSON, grouped by tag."""


