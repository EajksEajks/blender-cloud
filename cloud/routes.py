import logging

from flask import Blueprint, render_template

blueprint = Blueprint('cloud', __name__)
log = logging.getLogger(__name__)


@blueprint.route('/about')
def about():
    return render_template('about.html')
