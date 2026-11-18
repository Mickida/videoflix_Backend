from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import IntegrityError, transaction
from rest_framework import serializers

GENERIC_ERROR = 'Please check your input and try again.'


def check_password_rules(password, user):
    """Apply AUTH_PASSWORD_VALIDATORS and answer with the generic error."""
    try:
        validate_password(password, user)
    except DjangoValidationError:
        raise serializers.ValidationError(GENERIC_ERROR)


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
        check_password_rules(data['password'], User(username=data['email'], email=data['email']))
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


class PasswordResetSerializer(serializers.Serializer):
    """Validate the email for a password reset request."""

    email = serializers.EmailField(max_length=150)


class PasswordConfirmSerializer(serializers.Serializer):
    """Validate the new password and its confirmation."""

    new_password = serializers.CharField(write_only=True, min_length=8, max_length=128, trim_whitespace=False)
    confirm_password = serializers.CharField(write_only=True, max_length=128, trim_whitespace=False)

    def validate(self, data):
        """Make sure both passwords match and follow the password rules."""
        if data['new_password'] != data['confirm_password']:
            raise serializers.ValidationError(GENERIC_ERROR)
        check_password_rules(data['new_password'], self.context['user'])
        return data
