from .common import *

SECRET_KEY = "{{ KEESHSTUDIO_SECRET_KEY }}"
ALLOWED_HOSTS = [
    "keeshstudio",
    "{{ KEESHSTUDIO_HOST }}",
]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        "HOST": "{{ MYSQL_HOST }}",
        "PORT": {{MYSQL_PORT}},
        "NAME": "{{ KEESHSTUDIO_MYSQL_DATABASE }}",
        "USER": "{{ KEESHSTUDIO_MYSQL_USERNAME }}",
        "PASSWORD": "{{ KEESHSTUDIO_MYSQL_PASSWORD }}",
        "OPTIONS": {
            "init_command": "SET sql_mode='STRICT_TRANS_TABLES'",
        },
    }
}

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {
            "level": "INFO",
            "class": "logging.StreamHandler",
        },
    },
    "loggers": {
        "": {
            "handlers": ["console"],
            "level": "INFO",
        },
    },
}

{{ patch("keeshstudio-settings") }}  # noqa
