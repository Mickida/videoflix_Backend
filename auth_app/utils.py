import django_rq
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken, OutstandingToken
from rest_framework_simplejwt.tokens import RefreshToken

from auth_app.tasks import send_activation_email, send_password_reset_email

ACCESS_COOKIE = 'access_token'
REFRESH_COOKIE = 'refresh_token'
COOKIE_SAMESITE = 'Lax'
# False, because the project runs locally over plain HTTP.
COOKIE_SECURE = False

LOGOUT_MESSAGE = 'Logout successful! All tokens will be deleted. Refresh token is now invalid.'
MISSING_REFRESH_TOKEN = 'Refresh token missing.'
INVALID_REFRESH_TOKEN = 'Invalid refresh token.'
RESET_EMAIL_SENT = 'An email has been sent to reset your password.'
INVALID_RESET_LINK = 'Invalid or expired reset link.'
PASSWORD_RESET_DONE = 'Your Password has been successfully reset.'


def build_frontend_link(page, user, token):
    """Return the frontend URL with uid and token as query parameters."""
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    return f'{settings.FRONTEND_URL}/pages/auth/{page}?uid={uid}&token={token}'


def queue_activation_email(user, token):
    """Put the activation email for the user into the task queue."""
    link = build_frontend_link('activate.html', user, token)
    django_rq.enqueue(send_activation_email, user.email, link)


def queue_password_reset_email(email):
    """Queue a reset email if an active user with this email exists."""
    user = User.objects.filter(username=email.lower(), is_active=True).first()
    if user is None:
        return
    token = default_token_generator.make_token(user)
    link = build_frontend_link('confirm_password.html', user, token)
    django_rq.enqueue(send_password_reset_email, user.email, link)


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


def blacklist_all_refresh_tokens(user):
    """Blacklist every refresh token that was issued to the user."""
    for token in OutstandingToken.objects.filter(user=user):
        BlacklistedToken.objects.get_or_create(token=token)
