from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from core.utils import create_active_user
from social_profiles.models import FriendshipRequest, Profile


class FriendshipViewTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = self.create_profile('owner')
        self.other = self.create_profile('other')
        self.client.force_authenticate(self.user.user)

    def create_profile(self, username):
        user = create_active_user(
            email=f'{username}@example.com',
            username=username,
            password='testpass123',
            first_name=username.title(),
            last_name='User',
        )
        return Profile.objects.create(user=user)

    def test_friends_includes_pending_requests_for_owner(self):
        FriendshipRequest.objects.create(created_by=self.other, created_for=self.user)

        response = self.client.get(
            reverse('social_profiles:friends', args=[self.user.slug])
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()['requests']), 1)

    def test_friends_hides_requests_for_another_profile(self):
        FriendshipRequest.objects.create(created_by=self.other, created_for=self.user)

        response = self.client.get(
            reverse('social_profiles:friends', args=[self.other.slug])
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['requests'], [])

    @patch('social_profiles.views.friendship.create_notification')
    def test_send_friendship_request_creates_request(self, mock_notification):
        response = self.client.post(
            reverse('social_profiles:send_friendship_request', args=[self.other.slug])
        )

        self.assertEqual(response.json()['message'], 'friendship request created')
        mock_notification.assert_called_once()

    def test_send_friendship_request_reports_existing_reciprocal_requests(self):
        FriendshipRequest.objects.create(created_by=self.user, created_for=self.other)
        FriendshipRequest.objects.create(created_by=self.other, created_for=self.user)

        response = self.client.post(
            reverse('social_profiles:send_friendship_request', args=[self.other.slug])
        )

        self.assertEqual(response.json()['message'], 'request already sent')

    @patch('social_profiles.views.friendship.create_notification')
    def test_handle_accepted_request_adds_friend_and_notifies(self, mock_notification):
        request = FriendshipRequest.objects.create(
            created_by=self.other, created_for=self.user
        )

        response = self.client.post(
            reverse(
                'social_profiles:handle_request',
                args=[self.other.slug, FriendshipRequest.ACCEPTED],
            )
        )

        self.assertEqual(response.json()['message'], 'friendship request updated')
        self.user.refresh_from_db()
        self.other.refresh_from_db()
        request.refresh_from_db()
        self.assertEqual(request.status, FriendshipRequest.ACCEPTED)
        self.assertTrue(self.user.friends.filter(pk=self.other.pk).exists())
        self.assertEqual((self.user.friends_count, self.other.friends_count), (1, 1))
        mock_notification.assert_called_once()

    @patch('social_profiles.views.friendship.create_notification')
    def test_handle_rejected_request_notifies(self, mock_notification):
        request = FriendshipRequest.objects.create(
            created_by=self.other, created_for=self.user
        )

        self.client.post(
            reverse(
                'social_profiles:handle_request',
                args=[self.other.slug, FriendshipRequest.REJECTED],
            )
        )

        request.refresh_from_db()
        self.assertEqual(request.status, FriendshipRequest.REJECTED)
        mock_notification.assert_called_once()

    def test_returns_friendship_suggestions(self):
        self.user.people_you_may_know.add(self.other)

        response = self.client.get(
            reverse('social_profiles:my_friendship_suggestions')
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()[0]['username'], 'other')
