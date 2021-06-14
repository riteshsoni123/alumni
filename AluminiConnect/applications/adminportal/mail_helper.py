from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from django.contrib.sites.shortcuts import get_current_site
from django.core import mail
from django.core.mail import EmailMultiAlternatives
from django.template import Context, Template
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes
from django.utils.html import strip_tags
from django.utils.http import urlsafe_base64_encode

from .models import EmailTemplate, BulkEmailHistory, SingleEmailHistory

ALLOWED_RECIPIENTS_PER_DAY = 500


def get_rendered_emails(from_email, email_template, recipients):
    subject = email_template.subject

    body = email_template.body
    body_template = Template(body)

    messages = []

    for profile in recipients:
        context = Context({
            "profile": profile,
        })
        html_message = body_template.render(context)
        plain_message = strip_tags(html_message)

        email = EmailMultiAlternatives(
            subject,
            plain_message,
            from_email,
            [profile.email],
            [settings.BCC_EMAIL_ID],
        )
        email.attach_alternative(html_message, "text/html")
        messages.append(email)

    return messages


def send_verification_email(request, profile):
    current_site = get_current_site(request)
    protocol = 'https' if request.is_secure() else 'http'

    rendered_url = render_to_string('registration/url_password_reset_email.html', {
        'uid': urlsafe_base64_encode(force_bytes(profile.user.pk)),
        'user': profile.user,
        'token': default_token_generator.make_token(profile.user),
        'domain': current_site.domain,
        'protocol': protocol,
    })

    from_email = settings.DEFAULT_FROM_EMAIL
    to = [profile.email]

    subject = 'SAC IIITDMJ Portal Registration Successful!'

    html_message = render_to_string('registration/account_verification_email.html', {
        "name": profile.name,
        "email": profile.email,
        "from": profile.year_of_admission,
        "to": profile.batch.batch,
        "prog": profile.programme,
        "branch": profile.branch,
        "reg_no": profile.reg_no,
        "roll_no": profile.roll_no,
        "pass": rendered_url,
    })
    plain_message = strip_tags(html_message)

    email = EmailMultiAlternatives(
        subject,
        plain_message,
        from_email,
        to,
        [settings.BCC_EMAIL_ID],
    )
    email.attach_alternative(html_message, "text/html")

    print("sending email to {}".format(to))
    delivered = False

    try:
        print(email.send())
        delivered = True
    except Exception as error:
        print("Exception while sending mail to {}".format(to))
        print(error)

    SingleEmailHistory.objects.create(
        email_template='registration success',
        recipient=profile.roll_no,
        programme=profile.programme,
        batch=profile.batch,
        delivered=delivered
    )


def send_birthday_wish(profile):
    from_email = settings.DEFAULT_FROM_EMAIL
    to = [profile.email]

    subject = 'Student Alumni Cell, IIITDMJ Wishes you a Very Happy Birthday!'

    html_message = render_to_string('registration/birthday_wishes_email.html', {
        "name": profile.name,
        "email": profile.email,
        "from": profile.year_of_admission,
        "to": profile.batch.batch,
        "prog": profile.programme,
        "branch": profile.branch,
        "reg_no": profile.reg_no,
        "roll_no": profile.roll_no,
    })
    plain_message = strip_tags(html_message)
    email = EmailMultiAlternatives(
        subject,
        plain_message,
        from_email,
        to,
        [settings.BCC_EMAIL_ID],
    )
    email.attach_alternative(html_message, "text/html")

    print("sending birthday email to {}".format(to))
    delivered = False

    try:
        print(email.send())
        delivered = True
    except Exception as error:
        print("Exception while sending mail to {}".format(to))
        print(error)

    SingleEmailHistory.objects.create(
        email_template='Birthday wish',
        recipient=profile.roll_no,
        programme=profile.programme,
        batch=profile.batch,
        delivered=delivered
    )


def send_bulk_mail(batches, branches, programmes, recipients, template_id):
    template = EmailTemplate.objects.get(template_id=template_id)
    email_messages = get_rendered_emails(settings.DEFAULT_FROM_EMAIL, template, recipients)
    connection = mail.get_connection()
    total_messages_delivered = connection.send_messages(email_messages)
    BulkEmailHistory.objects.create(
        email_template=template.name,
        programme=', '.join(programmes),
        batch=', '.join(map(str, batches)),
        branch=', '.join(branches),
        total_recipients=recipients.count(),
        total_delivered=total_messages_delivered,
    )
    return total_messages_delivered
