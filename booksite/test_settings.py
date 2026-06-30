from .settings import *

SECRET_KEY = 'django-insecure-test-key-not-for-production'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
STRIPE_SECRET_KEY = 'sk_test_fake'
STRIPE_PUBLIC_KEY = 'pk_test_fake'

PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.MD5PasswordHasher',
]

LOGGING_CONFIG = None