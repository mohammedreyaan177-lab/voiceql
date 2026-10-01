from .settings import *

MIDDLEWARE = ["config.cors.CorsMiddleware", *MIDDLEWARE]

STATICFILES_DIRS = [BASE_DIR.parent / "frontend"]
