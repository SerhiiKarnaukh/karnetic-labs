from django.db.models.signals import pre_save
from django.dispatch import receiver

from social_profiles.models import Profile


@receiver(pre_save, sender=Profile)
def delete_old_avatar(sender, instance, **kwargs):
    if instance.pk:
        try:
            old_avatar = Profile.objects.get(pk=instance.pk).avatar
        except Profile.DoesNotExist:
            return

        new_avatar = instance.avatar
        if (old_avatar and old_avatar != new_avatar
                and old_avatar.name != 'social/avatars/avatar.png'):
            old_avatar.delete(save=False)
