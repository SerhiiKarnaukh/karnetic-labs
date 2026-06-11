from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from accounts.models import Account
from social_notification.models import Notification
from social_profiles.models import Profile


class NotificationsViewTest(TestCase):
    def setUp(self):
        self.client = APIClient()

        self.user = Account.objects.create_user(
            email="notify@example.com",
            username="notifier",
            password="pass123",
            first_name="Notify",
            last_name="User",
        )
        self.user.is_active = True
        self.user.save()
        self.profile = Profile.objects.create(user=self.user)

        self.unread1 = Notification.objects.create(
            created_for=self.profile,
            created_by=self.profile,
            type_of_notification="post_like",
            body="Test body 1",
            is_read=False,
        )
        self.unread2 = Notification.objects.create(
            created_for=self.profile,
            created_by=self.profile,
            type_of_notification="post_comment",
            body="Test body 2",
            is_read=False,
        )
        self.read = Notification.objects.create(
            created_for=self.profile,
            created_by=self.profile,
            type_of_notification="chat_message",
            body="Test body 3",
            is_read=True,
        )

    def test_returns_only_unread_notifications(self):
        self.client.login(username="notify@example.com", password="pass123")

        response = self.client.get(reverse("social_notification:notifications"))
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertIsInstance(data, list)
        self.assertEqual(len(data), 2)

        returned_ids = {item["id"] for item in data}
        self.assertIn(str(self.unread1.id), returned_ids)
        self.assertIn(str(self.unread2.id), returned_ids)
        self.assertNotIn(str(self.read.id), returned_ids)


class ReadNotificationTest(TestCase):
    def setUp(self):
        self.client = APIClient()

        self.user = Account.objects.create_user(
            email="read@example.com",
            username="reader",
            password="pass123",
            first_name="Read",
            last_name="User",
        )
        self.user.is_active = True
        self.user.save()

        self.profile = Profile.objects.create(user=self.user)

        self.notification = Notification.objects.create(
            created_for=self.profile,
            created_by=self.profile,
            type_of_notification="chat_message",
            body="Test notification",
            is_read=False,
        )

    def test_read_notification_marks_as_read(self):
        self.client.login(username="read@example.com", password="pass123")

        url = reverse(
            "social_notification:read_notification",
            args=[self.notification.pk],
        )
        response = self.client.post(url)

        self.assertEqual(response.status_code, 200)
        self.notification.refresh_from_db()
        self.assertTrue(self.notification.is_read)

        data = response.json()
        self.assertEqual(data["message"], "notification read")
