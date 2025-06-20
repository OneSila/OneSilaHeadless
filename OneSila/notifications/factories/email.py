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
            'multi_tenant_company': self.user.multi_tenant_company,
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

    def __init__(self, token):
        self.user = token.multi_tenant_user
        self.token = token

    def set_template_variables(self):
        super().set_template_variables()
        self.template_variables.update({
            'accept_invite_url': reverse_lazy('core:auth_register_accept_invite', kwargs={'token': self.token.token})
        })


class SendLoginLinkEmailFactory(SendUserInviteEmailFactory):
    subject = _("Your login link")
    template_path = 'notifications/email/login_link.html'

    def set_template_variables(self):
        super().set_template_variables()
        self.template_variables.update({
            'token_url': reverse_lazy('core:auth_token_login', kwargs={'token': self.token.token})
        })


class SendRecoveryLinkEmailFactory(SendUserInviteEmailFactory):
    subject = _("Your Account Recovery link")
    template_path = 'notifications/email/account_recovery_link.html'

    def set_template_variables(self):
        super().set_template_variables()
        self.template_variables.update({
            'token_url': reverse_lazy('core:auth_recover', kwargs={'token': self.token.token})
        })


class SendPasswordChangedEmailFactory(SendBrandedEmail):
    subject = _("Your password has been updated.")
    template_path = 'notifications/email/password_changed.html'

    def set_template_variables(self):
        super().set_template_variables()
        self.template_variables.update({
            'auth_change_password': reverse_lazy('core:auth_change_password')
        })


class SendImportReportEmailFactory:
    subject = _("Import report")
    template_path = 'notifications/email/import_report.html'

    def __init__(self, *, email, language, context):
        self.email = email
        self.language = language
        self.context = context

    def run(self):
        activate(self.language)
        html_body = render_to_string(self.template_path, self.context)
        send_branded_mail(self.subject, html_body, self.email)
        deactivate()

