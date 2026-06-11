from django.contrib.auth.models import BaseUserManager


class MyAccountManager(BaseUserManager):

    def create_user(self,
                    first_name,
                    last_name,
                    username,
                    email,
                    password=None):
        if not email:
            raise ValueError('User must have an email address')

        if not username:
            raise ValueError('User must have an username')

        username = self.generate_unique_username(username)

        user = self.model(
            email=self.normalize_email(email),
            username=username,
            first_name=first_name,
            last_name=last_name,
        )

        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, first_name, last_name, email, username,
                         password):
        user = self.create_user(
            email=self.normalize_email(email),
            username=username,
            password=password,
            first_name=first_name,
            last_name=last_name,
        )
        user.is_admin = True
        user.is_active = True
        user.is_staff = True
        user.is_superadmin = True
        user.save(using=self._db)
        return user

    def generate_unique_username(self, base_username):
        base_username = base_username.lower()
        username = base_username
        counter = 1
        while self.model.objects.filter(username=username).exists():
            username = f"{base_username}_{counter}"
            counter += 1
        return username
