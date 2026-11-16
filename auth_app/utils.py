import django_rq
from django.conf import settings
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from auth_app.tasks import send_activation_email


def build_frontend_link(page, user, token):
    """Return the frontend URL with uid and token as query parameters."""
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    return f'{settings.FRONTEND_URL}/pages/auth/{page}?uid={uid}&token={token}'


def queue_activation_email(user, token):
    """Put the activation email for the user into the task queue."""
    link = build_frontend_link('activate.html', user, token)
    django_rq.enqueue(send_activation_email, user.email, link)
