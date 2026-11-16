from django.contrib.auth.tokens import PasswordResetTokenGenerator


class AccountActivationTokenGenerator(PasswordResetTokenGenerator):
    """Create one-time tokens for account activation links."""

    key_salt = 'auth_app.tokens.AccountActivationTokenGenerator'

    def _make_hash_value(self, user, timestamp):
        """Include is_active so the token expires after activation."""
        return f'{user.pk}{timestamp}{user.is_active}'


account_activation_token = AccountActivationTokenGenerator()
