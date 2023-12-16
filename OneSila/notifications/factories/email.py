from notifications.helpers import send_branded_mail

from django.utils.translation import activate, get_language_info, deactivate
from django.utils.translation import gettext_lazy as _
from django.template.loader import render_to_string

from core.helpers import reverse_lazy


class SendBrandedEmail:
    subject = ''
    template_path = ''

    def __init__(self, user):
        self.user = user

    def set_template_variables(self):
        self.template_variables = {
            'user': self.user,
            'multi_tenant_company': self.user.multi_tenant_company
        }

    def compile_html_body(self):
        self.html_body = render_to_string(self.template_path, self.template_variables)

    def send_email(self):
        send_branded_mail(self.subject, self.html_body, self.user.email)

    def run(self):
        activate(self.user.language)
        self.set_template_variables()
        self.compile_html_body()
        self.send_email()
        deactivate()


class SendWelcomeEmailFactory(SendBrandedEmail):
    subject = _("Welcome to OneSila. Let's kickstart your productivity.")
    template_path = 'notifications/email/welcome.html'

    def set_template_variables(self):
        super().set_template_variables()
        self.template_variables.update({
            'dashboard_url': reverse_lazy('core:dashboard')
        })


class SendUserInviteEmailFactory(SendBrandedEmail):
    subject = _("Accept your invitation to OneSila.")
    template_path = 'notifications/email/invite_user.html'

    def set_template_variables(self):
        super().set_template_variables()
        self.template_variables.update({
            'accept_invite_url': reverse_lazy('core:auth_register_accept_invite')
        })
