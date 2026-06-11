from social_chat.models import ConversationMessage
from social_notification.models import Notification
from social_notification.utils.websocket import send_notification
from social_posts.models import Post
from social_profiles.models import FriendshipRequest, Profile


def create_notification(
    request,
    type_of_notification,
    post_id=None,
    friendrequest_id=None,
    conversation_message_id=None,
):
    created_for = None
    request_user = Profile.objects.get(user=request.user)

    if type_of_notification == 'post_like':
        body = f'{request_user.full_name()} liked one of your posts!'
        post = Post.objects.get(pk=post_id)
        created_for = post.created_by
    elif type_of_notification == 'post_comment':
        body = f'{request_user.full_name()} commented on one of your posts!'
        post = Post.objects.get(pk=post_id)
        created_for = post.created_by
    elif type_of_notification == 'new_friendrequest':
        friendrequest = FriendshipRequest.objects.get(pk=friendrequest_id)
        created_for = friendrequest.created_for
        body = f'{request_user.full_name()} sent you a friend request!'
    elif type_of_notification == 'accepted_friendrequest':
        friendrequest = FriendshipRequest.objects.get(pk=friendrequest_id)
        created_for = friendrequest.created_by
        body = f'{request_user.full_name()} accepted your friend request!'
    elif type_of_notification == 'rejected_friendrequest':
        friendrequest = FriendshipRequest.objects.get(pk=friendrequest_id)
        created_for = friendrequest.created_by
        body = f'{request_user.full_name()} rejected your friend request!'
    elif type_of_notification == 'chat_message':
        conversation_message = ConversationMessage.objects.get(
            pk=conversation_message_id,
        )
        created_for = conversation_message.sent_to
        body = f'{request_user.full_name()} sent you a message!'

    notification = Notification.objects.create(
        body=body,
        type_of_notification=type_of_notification,
        created_by=request_user,
        post_id=post_id,
        created_for=created_for,
    )

    if created_for:
        send_notification(created_for, type_of_notification)

    return notification
