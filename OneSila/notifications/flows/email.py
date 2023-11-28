from notifications.factories.email import SendWelcomeEmailFactory, SendUserInviteEmailFactory


def send_welcome_email_flow(*, user):
    fac = SendWelcomeEmailFactory(user)
    fac.run()


def send_user_invite_email_flow(*, user):
    fac = SendUserInviteEmailFactory(user)
    fac.run()
