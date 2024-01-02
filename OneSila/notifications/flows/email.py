from notifications.factories.email import SendWelcomeEmailFactory, SendUserInviteEmailFactory, \
    SendRecoveryLinkEmailFactory, SendLoginLinkEmailFactory, SendPasswordChangedEmailFactory


def send_welcome_email_flow(*, user):
    fac = SendWelcomeEmailFactory(user)
    fac.run()


def send_user_invite_email_flow(*, user):
    fac = SendUserInviteEmailFactory(user)
    fac.run()


def send_user_login_link_email_flow(*, token):
    fac = SendLoginLinkEmailFactory(token)
    fac.run()


def send_user_account_recovery_email_flow(*, token):
    fac = SendRecoveryLinkEmailFactory(token)
    fac.run()


def send_user_password_changed_email_flow(*, user):
    fac = SendPasswordChangedEmailFactory(user)
    fac.run()
