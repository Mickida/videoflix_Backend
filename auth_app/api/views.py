from django.conf import settings
from django.contrib.auth import authenticate
from django.contrib.auth.models import User, update_last_login
from django.contrib.auth.tokens import default_token_generator
from django.db import transaction
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken

from auth_app.api.serializers import (
    GENERIC_ERROR,
    LoginSerializer,
    PasswordConfirmSerializer,
    PasswordResetSerializer,
    RegistrationSerializer,
)
from auth_app.tokens import account_activation_token
from auth_app.utils import (
    ACCESS_COOKIE,
    INVALID_REFRESH_TOKEN,
    INVALID_RESET_LINK,
    LOGOUT_MESSAGE,
    MISSING_REFRESH_TOKEN,
    PASSWORD_RESET_DONE,
    REFRESH_COOKIE,
    RESET_EMAIL_SENT,
    blacklist_all_refresh_tokens,
    blacklist_refresh_token,
    delete_token_cookies,
    get_user_from_uidb64,
    queue_activation_email,
    queue_password_reset_email,
    set_token_cookie,
)


class RegistrationView(APIView):
    """Register a new user and send the activation email."""

    authentication_classes = []
    permission_classes = [AllowAny]
    throttle_scope = 'register'

    def post(self, request):
        """Create the inactive user and return it with its token."""
        serializer = RegistrationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        # Roll back the user if the email cannot be queued.
        with transaction.atomic():
            user = serializer.save()
            token = account_activation_token.make_token(user)
            queue_activation_email(user, token)
        return Response(
            {'user': {'id': user.id, 'email': user.email}, 'token': token},
            status=status.HTTP_201_CREATED,
        )


class ActivationView(APIView):
    """Activate an account with the link from the activation email."""

    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, request, uidb64, token):
        """Set the user active if uid and token are valid."""
        user = get_user_from_uidb64(uidb64)
        if user is None or not account_activation_token.check_token(user, token):
            return Response({'message': 'Activation failed.'}, status=status.HTTP_400_BAD_REQUEST)
        user.is_active = True
        user.save(update_fields=['is_active'])
        return Response({'message': 'Account successfully activated.'})


class LoginView(APIView):
    """Log a user in with email and password and set the JWT cookies."""

    authentication_classes = []
    permission_classes = [AllowAny]
    throttle_scope = 'login'

    def post(self, request):
        """Check the credentials and return the user data."""
        user = self.authenticate_user(request)
        if user is None:
            return Response({'detail': GENERIC_ERROR}, status=status.HTTP_400_BAD_REQUEST)
        return self.build_login_response(user)

    def authenticate_user(self, request):
        """Return the active user for valid credentials, otherwise None."""
        serializer = LoginSerializer(data=request.data)
        if not serializer.is_valid():
            return None
        return authenticate(
            request,
            username=serializer.validated_data['email'].lower(),
            password=serializer.validated_data['password'],
        )

    def build_login_response(self, user):
        """Return the success response with both token cookies set."""
        update_last_login(None, user)
        refresh = RefreshToken.for_user(user)
        response = Response({
            'detail': 'Login successful',
            'user': {'id': user.id, 'username': user.username},
        })
        jwt = settings.SIMPLE_JWT
        set_token_cookie(response, ACCESS_COOKIE, refresh.access_token, jwt['ACCESS_TOKEN_LIFETIME'])
        set_token_cookie(response, REFRESH_COOKIE, refresh, jwt['REFRESH_TOKEN_LIFETIME'])
        return response


class CookieTokenRefreshView(APIView):
    """Issue a new access token from the refresh_token cookie."""

    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        """Set a new access_token cookie if the refresh token is valid."""
        raw_token = request.COOKIES.get(REFRESH_COOKIE)
        if raw_token is None:
            return Response({'detail': MISSING_REFRESH_TOKEN}, status=status.HTTP_400_BAD_REQUEST)
        refresh = self.get_valid_refresh_token(raw_token)
        if refresh is None:
            return Response({'detail': INVALID_REFRESH_TOKEN}, status=status.HTTP_401_UNAUTHORIZED)
        access = refresh.access_token
        response = Response({'detail': 'Token refreshed', 'access': str(access)})
        set_token_cookie(response, ACCESS_COOKIE, access, settings.SIMPLE_JWT['ACCESS_TOKEN_LIFETIME'])
        return response

    def get_valid_refresh_token(self, raw_token):
        """Return the refresh token if it is valid and its user is active, otherwise None."""
        try:
            refresh = RefreshToken(raw_token)
        except TokenError:
            return None
        if not User.objects.filter(pk=refresh['user_id'], is_active=True).exists():
            return None
        return refresh


class LogoutView(APIView):
    """Blacklist the refresh token and delete both JWT cookies."""

    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        """Log the user out; the cookies are deleted in every case."""
        response = self.build_logout_response(request.COOKIES.get(REFRESH_COOKIE))
        delete_token_cookies(response)
        return response

    def build_logout_response(self, raw_token):
        """Return the response that matches the state of the refresh token."""
        if raw_token is None:
            return Response({'detail': MISSING_REFRESH_TOKEN}, status=status.HTTP_400_BAD_REQUEST)
        if not blacklist_refresh_token(raw_token):
            return Response({'detail': INVALID_REFRESH_TOKEN}, status=status.HTTP_400_BAD_REQUEST)
        return Response({'detail': LOGOUT_MESSAGE})


class PasswordResetView(APIView):
    """Send a password reset link without revealing if the email exists."""

    authentication_classes = []
    permission_classes = [AllowAny]
    throttle_scope = 'password_reset'

    def post(self, request):
        """Queue the reset email and always return the same answer."""
        serializer = PasswordResetSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        queue_password_reset_email(serializer.validated_data['email'])
        return Response({'detail': RESET_EMAIL_SENT})


class PasswordConfirmView(APIView):
    """Set a new password with the link from the reset email."""

    authentication_classes = []
    permission_classes = [AllowAny]
    throttle_scope = 'password_confirm'

    def post(self, request, uidb64, token):
        """Check the link and save the new password."""
        user = self.get_user_for_link(uidb64, token)
        if user is None:
            return Response({'detail': INVALID_RESET_LINK}, status=status.HTTP_400_BAD_REQUEST)
        serializer = PasswordConfirmSerializer(data=request.data, context={'user': user})
        serializer.is_valid(raise_exception=True)
        self.save_new_password(user, serializer.validated_data['new_password'])
        return Response({'detail': PASSWORD_RESET_DONE})

    def get_user_for_link(self, uidb64, token):
        """Return the active user of a valid reset link, otherwise None."""
        user = get_user_from_uidb64(uidb64)
        if user is None or not user.is_active:
            return None
        if not default_token_generator.check_token(user, token):
            return None
        return user

    def save_new_password(self, user, password):
        """Save the password and log the user out everywhere."""
        with transaction.atomic():
            user.set_password(password)
            user.save(update_fields=['password'])
            blacklist_all_refresh_tokens(user)
