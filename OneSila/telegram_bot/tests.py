from unittest.mock import Mock, patch

from django.test import TestCase, override_settings

from core.models.multi_tenant import MultiTenantCompany, MultiTenantUser
from core.signals import multi_tenant_company_created
from telegram_bot.factories import TelegramAdminNotificationFactory
from telegram_bot.models import TelegramUser


class TelegramAdminNotificationFactoryTests(TestCase):
    def setUp(self):
        self.company = MultiTenantCompany.objects.create(name="Widgets Inc.")
        self.user = MultiTenantUser.objects.create(
            username="new-user@example.com",
            multi_tenant_company=self.company,
        )
        self.admin_user = MultiTenantUser.objects.create(username="sascha-admin@example.com")

    # @TODO: FIX THIS AFTER DEPLOY
    # @override_settings(ADMINS=[("Sascha", "sascha@example.com"), ("Other", "other@example.com")])
    # def test_factory_sends_notifications_to_admin_telegram_users(self):
    #     TelegramUser.objects.create(
    #         telegram_user_id="sascha@example.com",
    #         chat_id="12345",
    #         user=self.admin_user,
    #     )
    #
    #     with patch("telegram_bot.factories.admin_notifications.async_to_sync") as async_to_sync_mock:
    #         sender_mock = Mock()
    #         async_to_sync_mock.return_value = sender_mock
    #
    #         factory = TelegramAdminNotificationFactory(user=self.user)
    #         factory.run()
    #
    #     sender_mock.assert_called_once_with(chat_id="12345", user=self.user)


class TelegramReceiversTests(TestCase):
    def setUp(self):
        self.company = MultiTenantCompany.objects.create(name="Acme Corp")
        self.user = MultiTenantUser.objects.create(
            username="receiver-test@example.com",
            multi_tenant_company=self.company,
        )

    def test_post_create_signal_triggers_factory(self):
        with patch("telegram_bot.receivers.TelegramAdminNotificationFactory") as factory_mock:
            multi_tenant_company_created.send(
                sender=MultiTenantUser,
                instance=self.user,
                multi_tenant_company=self.company,
            )

        factory_mock.assert_called_once_with(user=self.user)
        factory_mock.return_value.run.assert_called_once()


class TelegramUserModelTests(TestCase):
    def test_chat_id_defaults_to_user_id_on_save(self):
        admin_user = MultiTenantUser.objects.create(username="admin@example.com")
        telegram_user = TelegramUser.objects.create(
            telegram_user_id="admin@example.com",
            user=admin_user,
        )
        self.assertEqual(telegram_user.chat_id, "admin@example.com")

    def test_set_chat_id_updates_and_persists(self):
        owner_user = MultiTenantUser.objects.create(username="owner@example.com")
        telegram_user = TelegramUser.objects.create(
            telegram_user_id="owner@example.com",
            chat_id="42",
            user=owner_user,
        )
        telegram_user.chat_id = None
        telegram_user.set_chat_id(save=True)
        telegram_user.refresh_from_db()

        self.assertEqual(telegram_user.chat_id, "owner@example.com")

    def test_multi_tenant_user_optional(self):
        telegram_user = TelegramUser.objects.create(telegram_user_id="no-company@example.com")
        self.assertIsNone(telegram_user.user)
