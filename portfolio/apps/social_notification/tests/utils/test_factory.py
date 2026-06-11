from django.test import RequestFactory, TestCase
from unittest.mock import AsyncMock, patch

from core.utils import create_active_user
from social_chat.models import Conversation, ConversationMessage
from social_notification.utils import create_notification, send_notification
from social_posts.models import Post
from social_profiles.models import FriendshipRequest, Profile


class SendNotificationTest(TestCase):
    def setUp(self):
        self.user = create_active_user(
            email="notify@example.com",
            username="notifier",
            password="pass123",
            first_name="Notify",
            last_name="User",
        )

        self.profile = Profile.objects.create(user=self.user)

    @patch("social_notification.utils.websocket.get_channel_layer")
    def test_send_notification_sends_correct_message(self, mock_get_channel_layer):
        mock_group_send = AsyncMock()
        mock_get_channel_layer.return_value.group_send = mock_group_send

        message = "chat_message"
        group_name = f"notifications_{self.profile.id}"

        send_notification(self.profile, message)

        mock_group_send.assert_called_once_with(group_name, {
            "type": "send_notification",
            "message": message,
        })


class CreateNotificationUtilsTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.sender = create_active_user(
            email="sender@example.com",
            username="sender",
            password="testpass",
            first_name="Sender",
            last_name="User",
        )
        self.receiver = create_active_user(
            email="receiver@example.com",
            username="receiver",
            password="testpass",
            first_name="Receiver",
            last_name="User",
        )
        self.sender_profile = Profile.objects.create(
            user=self.sender,
            first_name="Sender",
            last_name="User",
        )
        self.receiver_profile = Profile.objects.create(
            user=self.receiver,
            first_name="Receiver",
            last_name="User",
        )

        self.request = self.factory.get("/")
        self.request.user = self.sender

    @patch("social_notification.utils.factory.send_notification")
    def test_post_like_notification(self, mock_send_notification):
        post = Post.objects.create(body="Test", created_by=self.receiver_profile)
        notification = create_notification(self.request, "post_like", post_id=post.id)
        self.assertEqual(notification.type_of_notification, "post_like")
        self.assertEqual(notification.created_for, self.receiver_profile)
        self.assertIn("liked", notification.body)
        mock_send_notification.assert_called_once_with(
            self.receiver_profile,
            "post_like",
        )

    @patch("social_notification.utils.factory.send_notification")
    def test_post_comment_notification(self, mock_send_notification):
        post = Post.objects.create(body="Test", created_by=self.receiver_profile)
        notification = create_notification(
            self.request,
            "post_comment",
            post_id=post.id,
        )
        self.assertEqual(notification.type_of_notification, "post_comment")
        self.assertEqual(notification.created_for, self.receiver_profile)
        self.assertIn("commented", notification.body)
        mock_send_notification.assert_called_once_with(
            self.receiver_profile,
            "post_comment",
        )

    @patch("social_notification.utils.factory.send_notification")
    def test_new_friend_request_notification(self, mock_send_notification):
        friend_request = FriendshipRequest.objects.create(
            created_by=self.sender_profile,
            created_for=self.receiver_profile,
        )
        notification = create_notification(
            self.request,
            "new_friendrequest",
            friendrequest_id=friend_request.id,
        )
        self.assertEqual(notification.type_of_notification, "new_friendrequest")
        self.assertEqual(notification.created_for, self.receiver_profile)
        self.assertIn("sent you a friend request", notification.body)
        mock_send_notification.assert_called_once_with(
            self.receiver_profile,
            "new_friendrequest",
        )

    @patch("social_notification.utils.factory.send_notification")
    def test_accepted_friend_request_notification(self, mock_send_notification):
        friend_request = FriendshipRequest.objects.create(
            created_by=self.receiver_profile,
            created_for=self.sender_profile,
        )
        notification = create_notification(
            self.request,
            "accepted_friendrequest",
            friendrequest_id=friend_request.id,
        )
        self.assertEqual(notification.type_of_notification, "accepted_friendrequest")
        self.assertEqual(notification.created_for, self.receiver_profile)
        self.assertIn("accepted your friend request", notification.body)
        mock_send_notification.assert_called_once_with(
            self.receiver_profile,
            "accepted_friendrequest",
        )

    @patch("social_notification.utils.factory.send_notification")
    def test_rejected_friend_request_notification(self, mock_send_notification):
        friend_request = FriendshipRequest.objects.create(
            created_by=self.receiver_profile,
            created_for=self.sender_profile,
        )
        notification = create_notification(
            self.request,
            "rejected_friendrequest",
            friendrequest_id=friend_request.id,
        )
        self.assertEqual(notification.type_of_notification, "rejected_friendrequest")
        self.assertEqual(notification.created_for, self.receiver_profile)
        self.assertIn("rejected your friend request", notification.body)
        mock_send_notification.assert_called_once_with(
            self.receiver_profile,
            "rejected_friendrequest",
        )

    @patch("social_notification.utils.factory.send_notification")
    def test_chat_message_notification(self, mock_send_notification):
        conversation = Conversation.objects.create()
        conversation.users.set([self.sender_profile, self.receiver_profile])
        msg = ConversationMessage.objects.create(
            conversation=conversation,
            created_by=self.sender_profile,
            sent_to=self.receiver_profile,
            body="Yo!",
        )
        notification = create_notification(
            self.request,
            "chat_message",
            conversation_message_id=msg.id,
        )
        self.assertEqual(notification.type_of_notification, "chat_message")
        self.assertEqual(notification.created_for, self.receiver_profile)
        self.assertIn("sent you a message", notification.body)
        mock_send_notification.assert_called_once_with(
            self.receiver_profile,
            "chat_message",
        )
