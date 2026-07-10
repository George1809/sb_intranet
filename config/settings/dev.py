from .base import *

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = "django-insecure-@gwtpu@7fowa7hu9dw2!)*!r!j54&iv1s4oj$64+v_45dwmz*)"

# SECURITY WARNING: define the correct hosts in production!
ALLOWED_HOSTS = ["*"]

# EMAIL_BACKEND e stabilit in base.py din variabilele EMAIL_* din .env:
# ramane pe consola daca EMAIL_HOST nu e completat, trece pe SMTP real daca e.


# try:
#     from .local import *
# except ImportError:
#     pass
