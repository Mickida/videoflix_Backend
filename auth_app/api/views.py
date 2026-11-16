from django.db import transaction
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from auth_app.api.serializers import RegistrationSerializer
from auth_app.tokens import account_activation_token
from auth_app.utils import queue_activation_email


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
