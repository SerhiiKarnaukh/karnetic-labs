import io

from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image

from accounts.models import Account


def create_active_user(**kwargs):
    user = Account.objects.create_user(**kwargs)
    user.is_active = True
    user.save()
    return user


def create_test_image(name):
    buffer = io.BytesIO()
    image = Image.new("RGB", (100, 100), color="red")
    image.save(buffer, format="PNG")
    buffer.seek(0)
    return SimpleUploadedFile(name, buffer.read(), content_type="image/png")
