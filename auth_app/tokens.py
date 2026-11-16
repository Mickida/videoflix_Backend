from django.contrib.auth.tokens import PasswordResetTokenGenerator


class AccountActivationTokenGenerator(PasswordResetTokenGenerator):
    """Create one-time tokens for account activation links."""

    key_salt = 'auth_app.tokens.AccountActivationTokenGenerator'

    def _make_hash_value(self, user, timestamp):
        """Include is_active and last_login so the link works only once."""
        login = '' if user.last_login is None else user.last_login.replace(microsecond=0, tzinfo=None)
        return f'{user.pk}{timestamp}{user.is_active}{login}'


account_activation_token = AccountActivationTokenGenerator()
