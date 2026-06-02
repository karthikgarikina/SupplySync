from .base import *

DEBUG = True

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ.get("DB_NAME", "supplysync_db"),
        "USER": os.environ.get("DB_USER", "supplysync_user"),
        "PASSWORD": os.environ.get("DB_PASSWORD", "supplysync_pass"),
        "HOST": os.environ.get("DB_HOST", "localhost"),
        "PORT": os.environ.get("DB_PORT", "5432"),
        "OPTIONS": {
            "options": "-c search_path=supplysync,public",
        },
    }
}

