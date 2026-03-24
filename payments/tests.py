from django.test import TestCase
from django.contrib.auth import get_user_model
from payments.models import ProcessedWebhookEvent, Payment

User = get_user_model()


class WebhookIdempotencyTestCase(TestCase):
    """Stripe webhook の冪等性テスト"""

    def setUp(self):
        self.user = User.objects.create_user(username="payuser", password="pass")

    def test_duplicate_event_id_rejected(self):
        """同一 event_id は2回目以降無視される"""
        ProcessedWebhookEvent.objects.create(
            event_id="evt_test_123",
            event_type="checkout.session.completed",
        )
        exists = ProcessedWebhookEvent.objects.filter(event_id="evt_test_123").exists()
        self.assertTrue(exists)

        # get_or_create で created=False になることを確認
        _, created = ProcessedWebhookEvent.objects.get_or_create(
            event_id="evt_test_123",
            defaults={"event_type": "checkout.session.completed"},
        )
        self.assertFalse(created)

    def test_unique_constraint_on_event_id(self):
        """event_id の unique 制約が効く"""
        ProcessedWebhookEvent.objects.create(
            event_id="evt_unique_test",
            event_type="checkout.session.completed",
        )
        from django.db import IntegrityError
        with self.assertRaises(IntegrityError):
            ProcessedWebhookEvent.objects.create(
                event_id="evt_unique_test",
                event_type="checkout.session.completed",
            )
