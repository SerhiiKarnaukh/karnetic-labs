"""Test-specific settings for faster test execution.

Used via: DJANGO_SETTINGS_MODULE=portfolio.settings_test
Imports everything from the main settings and overrides only
performance-related options. Zero impact on production/dev.
"""

from portfolio.settings import *  # noqa: F401,F403

PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]

EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

AUTH_PASSWORD_VALIDATORS = []
