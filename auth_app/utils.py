import django_rq
from django.conf import settings
from django.contrib.auth.models import User
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken

from auth_app.tasks import send_activation_email

ACCESS_COOKIE = 'access_token'
REFRESH_COOKIE = 'refresh_token'
COOKIE_SAMESITE = 'Lax'
COOKIE_SECURE = False  # Switched to True for production in step 8.


def build_frontend_link(page, user, token):
    """Return the frontend URL with uid and token as query parameters."""
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    return f'{settings.FRONTEND_URL}/pages/auth/{page}?uid={uid}&token={token}'


def queue_activation_email(user, token):
    """Put the activation email for the user into the task queue."""
    link = build_frontend_link('activate.html', user, token)
    django_rq.enqueue(send_activation_email, user.email, link)


def get_user_from_uidb64(uidb64):
    """Return the user encoded in uidb64, or None if it is invalid."""
    try:
        user_id = force_str(urlsafe_base64_decode(uidb64))
        return User.objects.get(pk=user_id)
    except (ValueError, TypeError, OverflowError, User.DoesNotExist):
        return None


def set_token_cookie(response, name, token, lifetime):
    """Attach a JWT to the response as an HttpOnly cookie."""
    response.set_cookie(
        key=name,
        value=str(token),
        max_age=int(lifetime.total_seconds()),
        httponly=True,
        secure=COOKIE_SECURE,
        samesite=COOKIE_SAMESITE,
    )


def blacklist_refresh_token(raw_token):
    """Blacklist the refresh token and return True if it was valid."""
    try:
        RefreshToken(raw_token).blacklist()
    except TokenError:
        return False
    return True


def delete_token_cookies(response):
    """Remove both JWT cookies from the browser."""
    for name in (ACCESS_COOKIE, REFRESH_COOKIE):
        response.delete_cookie(name, samesite=COOKIE_SAMESITE)
