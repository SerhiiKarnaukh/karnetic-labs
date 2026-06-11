import os
import shutil

from celery import shared_task
from django.conf import settings


@shared_task(name='ai_lab.tasks.delete_generated_media')
def delete_generated_media():
    folders_to_clean = ['generated_images', 'generated_voices', 'vision_images']

    for folder_name in folders_to_clean:
        folder_path = os.path.join(settings.MEDIA_ROOT, folder_name)
        if os.path.exists(folder_path):
            for filename in os.listdir(folder_path):
                file_path = os.path.join(folder_path, filename)
                try:
                    if os.path.isfile(file_path):
                        os.remove(file_path)
                    elif os.path.isdir(file_path):
                        shutil.rmtree(file_path)
                except Exception as e:
                    print(f"Error deleting {file_path}: {e}")
