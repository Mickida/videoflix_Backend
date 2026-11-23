from pathlib import Path

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string

LOGO_PATH = Path(__file__).resolve().parent / 'assets' / 'logo.png'


class LogoEmail(EmailMultiAlternatives):
    """HTML email that carries the logo inside the HTML part, not as an attachment."""

    def message(self, **kwargs):
        """Build the email and embed the logo next to the HTML body."""
        msg = super().message(**kwargs)
        html_part = msg.get_body(preferencelist=('html',))
        html_part.add_related(
            LOGO_PATH.read_bytes(), maintype='image', subtype='png',
            disposition='inline', cid='<logo@videoflix>',
        )
        # RFC 2387: the related part names the type of its main part.
        html_part.set_param('type', 'text/html')
        return msg


def send_html_email(subject, recipient, template_name, context):
    """Send an email with an HTML body, a text fallback and the logo."""
    text_body = render_to_string(f'emails/{template_name}.txt', context)
    html_body = render_to_string(f'emails/{template_name}.html', context)
    message = LogoEmail(subject, text_body, settings.DEFAULT_FROM_EMAIL, [recipient])
    message.attach_alternative(html_body, 'text/html')
    message.send()


def send_activation_email(email, activation_link):
    """Send the account activation email."""
    context = {'name': email.split('@')[0], 'link': activation_link}
    send_html_email('Confirm your email', email, 'activation', context)


def send_password_reset_email(email, reset_link):
    """Send the password reset email."""
    send_html_email('Reset your Password', email, 'password_reset', {'link': reset_link})
