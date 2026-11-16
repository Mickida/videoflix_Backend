from django.conf import settings
from django.contrib.auth import authenticate
from django.contrib.auth.models import update_last_login
from django.db import transaction
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from auth_app.api.serializers import GENERIC_ERROR, LoginSerializer, RegistrationSerializer
from auth_app.tokens import account_activation_token
from auth_app.utils import (
    ACCESS_COOKIE,
    REFRESH_COOKIE,
    get_user_from_uidb64,
    queue_activation_email,
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
