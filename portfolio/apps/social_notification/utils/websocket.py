from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer


def send_notification(account, message):
    channel_layer = get_channel_layer()
    user_id = account.id
    group_name = f'notifications_{user_id}'
    async_to_sync(channel_layer.group_send)(group_name, {
        'type': 'send_notification',
        'message': message,
    })
