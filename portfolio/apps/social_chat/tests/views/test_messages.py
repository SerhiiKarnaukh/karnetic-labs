from unittest.mock import AsyncMock, patch

from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from core.utils import create_active_user
from social_chat.models import Conversation, ConversationMessage
from social_profiles.models import Profile


class ConversationSendMessageViewTest(TestCase):
    def setUp(self):
        self.client = APIClient()

        self.user1 = create_active_user(
            email="user1@example.com",
            username="user1",
            password="pass123",
            first_name="User",
            last_name="One"
        )
        self.user2 = create_active_user(
            email="user2@example.com",
            username="user2",
            password="pass123",
            first_name="User",
            last_name="Two"
        )

        self.profile1 = Profile.objects.create(user=self.user1, first_name="User", last_name="One")
        self.profile2 = Profile.objects.create(user=self.user2, first_name="User", last_name="Two")

        self.conversation = Conversation.objects.create()
        self.conversation.users.add(self.profile1, self.profile2)

    @patch("social_chat.views.messages.create_notification")
    @patch("social_chat.views.messages.get_channel_layer")
    def test_user_can_send_message(self, mock_get_channel_layer, mock_create_notification):
        self.client.login(username="user1@example.com", password="pass123")

        mock_group_send = AsyncMock()
        mock_get_channel_layer.return_value.group_send = mock_group_send

        url = reverse("conversation_send_message", args=[self.conversation.pk])
        data = {"body": "Hello, how are you?"}
        response = self.client.post(url, data=data, format="json")

        self.assertEqual(response.status_code, 200)
        message_data = response.json()

        self.assertEqual(message_data["body"], data["body"])
        self.assertEqual(message_data["created_by"]["username"], self.profile1.username)
        self.assertEqual(message_data["sent_to"]["username"], self.profile2.username)

        self.assertEqual(ConversationMessage.objects.count(), 1)
        msg = ConversationMessage.objects.first()
        self.assertEqual(msg.conversation, self.conversation)
        self.assertEqual(msg.created_by, self.profile1)
        self.assertEqual(msg.sent_to, self.profile2)
        self.assertEqual(msg.body, data["body"])

        mock_create_notification.assert_called_once()
        args, kwargs = mock_create_notification.call_args
        self.assertEqual(args[1], "chat_message")
        self.assertEqual(kwargs, {"conversation_message_id": msg.id})

        mock_group_send.assert_awaited_once()
