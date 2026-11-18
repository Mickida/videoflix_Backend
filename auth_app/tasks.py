from email.message import MIMEPart
from pathlib import Path

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string

LOGO_PATH = Path(__file__).resolve().parent / 'assets' / 'logo.png'


def build_logo_attachment():
    """Return the Videoflix logo as an inline image for HTML emails."""
    logo = MIMEPart()
    logo.set_content(
        LOGO_PATH.read_bytes(), maintype='image', subtype='png',
        disposition='inline', filename='logo.png', cid='<logo>',
    )
    return logo


def send_html_email(subject, recipient, template_name, context):
    """Send an email with an HTML body, a text fallback and the logo."""
    text_body = render_to_string(f'emails/{template_name}.txt', context)
    html_body = render_to_string(f'emails/{template_name}.html', context)
    message = EmailMultiAlternatives(
        subject, text_body, settings.DEFAULT_FROM_EMAIL, [recipient]
    )
    message.attach_alternative(html_body, 'text/html')
    message.attach(build_logo_attachment())
    message.send()


def send_activation_email(email, activation_link):
    """Send the account activation email."""
    context = {'name': email.split('@')[0], 'link': activation_link}
    send_html_email('Confirm your email', email, 'activation', context)


def send_password_reset_email(email, reset_link):
    """Send the password reset email."""
    send_html_email('Reset your Password', email, 'password_reset', {'link': reset_link})
