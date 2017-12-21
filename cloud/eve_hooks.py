import logging
import typing

from pillar.auth import UserClass

from . import email

log = logging.getLogger(__name__)


def welcome_new_user(user_doc: dict):
    """Sends a welcome email to a new user."""

    user_email = user_doc.get('email')
    if not user_email:
        log.warning('user %s has no email address', user_doc.get('_id', '-no-id-'))
        return

    # Only send mail to new users when they actually are subscribers.
    user = UserClass.construct('', user_doc)
    if not (user.has_cap('subscriber') or user.has_cap('can-renew-subscription')):
        log.debug('user %s is new, but not a subscriber, so no email for them.', user_email)
        return

    email.queue_welcome_mail(user)


def welcome_new_users(user_docs: typing.List[dict]):
    """Sends a welcome email to new users."""

    for user_doc in user_docs:
        try:
            welcome_new_user(user_doc)
        except Exception:
            log.exception('error sending welcome mail to user %s', user_doc)


def setup_app(app):
    app.on_inserted_users += welcome_new_users
