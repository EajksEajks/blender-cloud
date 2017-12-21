import functools
import logging

import flask

from pillar.auth import UserClass

log = logging.getLogger(__name__)


def queue_welcome_mail(user: UserClass):
    """Queue a welcome email for execution by Celery."""
    assert user.email
    log.info('queueing welcome email to %s', user.email)

    subject = 'Welcome to Blender Cloud'
    render = functools.partial(flask.render_template, subject=subject, user=user)
    text = render('emails/welcome.txt')
    html = render('emails/welcome.html')

    from pillar.celery import email_tasks
    email_tasks.send_email.delay(user.full_name, user.email, subject, text, html)


def user_subscription_changed(user: UserClass, *, grant_roles: set, revoke_roles: set):
    if user.has_cap('subscriber') and 'has_subscription' in grant_roles:
        log.info('user %s just got a new subscription', user.email)
        queue_welcome_mail(user)


def setup_app(app):
    from pillar.api.blender_cloud import subscription
    subscription.user_subscription_updated.connect(user_subscription_changed)
