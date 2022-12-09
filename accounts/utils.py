from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import EmailMessage
from django.conf import settings
import threading

def detectUser(user):
    if user.role == 1:
        redirectUrl = 'vendorDashboard'
        return redirectUrl
    elif user.role == 2:
        redirectUrl = 'custDashboard'
        return redirectUrl
    elif user.role == None and user.is_superadmin:
        redirectUrl = '/admin'
        return redirectUrl


def send_verification_email(request, user, mail_subject, email_template):
    from_email = settings.DEFAULT_FROM_EMAIL
    current_site = get_current_site(request)
    message = render_to_string(email_template, {
        'user' : user,
        'domain' : current_site,
        'uid' : urlsafe_base64_encode(force_bytes(user.pk)),
        'token' : default_token_generator.make_token(user),
    })
    to_email = user.email
    mail = EmailMessage(mail_subject, message, from_email, to=[to_email])
    mail.content_subtype = "html"
    mail.send()


def send_notification(mail_subject, mail_template, context):
    from_email = settings.DEFAULT_FROM_EMAIL
    message = render_to_string(mail_template, context)
    to_email = context['to_email']
    if(isinstance(context['to_email'], str)):
        to_email = []
        to_email.append(context['to_email'])
    else:
        to_email = context['to_email']
    mail = EmailMessage(mail_subject, message, from_email, to=to_email)
    mail.content_subtype = "html"
    mail.send()


class SendVerificationEmailThread(threading.Thread):

    def __init__(self, request, user, mail_subject, email_template):
        self.request = request
        self.user = user
        self.mail_subject = mail_subject
        self.email_template = email_template
        threading.Thread.__init__(self)

    def run(self):
        try:
            from_email = settings.DEFAULT_FROM_EMAIL
            current_site = get_current_site(self.request)
            message = render_to_string(self.email_template, {
                'user' : self.user,
                'domain' : current_site,
                'uid' : urlsafe_base64_encode(force_bytes(self.user.pk)),
                'token' : default_token_generator.make_token(self.user),
            })
            to_email = self.user.email
            mail = EmailMessage(self.mail_subject, message, from_email, to=[to_email])
            mail.content_subtype = "html"
            mail.send()
        except:
            pass



class SendNotificationThread(threading.Thread):

    def __init__(self, mail_subject, mail_template, context):
        self.mail_subject = mail_subject
        self.mail_template = mail_template
        self.context = context
        threading.Thread.__init__(self)

    def run(self):
        try:
            from_email = settings.DEFAULT_FROM_EMAIL
            message = render_to_string(self.mail_template, self.context)
            to_email = self.context['to_email']
            if(isinstance(self.context['to_email'], str)):
                to_email = []
                to_email.append(self.context['to_email'])
            else:
                to_email = self.context['to_email']
            mail = EmailMessage(self.mail_subject, message, from_email, to=to_email)
            mail.content_subtype = "html"
            mail.send()
        except:
            pass



