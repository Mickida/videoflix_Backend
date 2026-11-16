from django.contrib.auth.models import User
from django.db import IntegrityError, transaction
from rest_framework import serializers

GENERIC_ERROR = 'Please check your input and try again.'


class RegistrationSerializer(serializers.Serializer):
    """Validate registration data and create an inactive user."""

    email = serializers.EmailField(max_length=150)
    password = serializers.CharField(write_only=True, min_length=8, max_length=128, trim_whitespace=False)
    confirmed_password = serializers.CharField(write_only=True, max_length=128, trim_whitespace=False)

    def validate_email(self, value):
        """Store emails in lowercase."""
        return value.lower()

    def validate(self, data):
        """Reject taken emails and mismatched passwords with the same error."""
        email_taken = User.objects.filter(username=data['email']).exists()
        if email_taken or data['password'] != data['confirmed_password']:
            raise serializers.ValidationError(GENERIC_ERROR)
        return data

    def create(self, validated_data):
        """Create the user with is_active set to False."""
        email = validated_data['email']
        try:
            with transaction.atomic():
                return User.objects.create_user(
                    username=email, email=email,
                    password=validated_data['password'], is_active=False,
                )
        except IntegrityError:
            raise serializers.ValidationError(GENERIC_ERROR)


class LoginSerializer(serializers.Serializer):
    """Validate the presence of login credentials."""

    email = serializers.EmailField(max_length=150)
    password = serializers.CharField(write_only=True, max_length=128, trim_whitespace=False)
