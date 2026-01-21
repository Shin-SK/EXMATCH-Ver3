# settings
from pathlib import Path
from dotenv import load_dotenv
import environ, os
import dj_database_url
from email.utils import formataddr
from corsheaders.defaults import default_headers, default_methods



BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.getenv("DEBUG", "True") == "True"

BACKEND_DOMAIN      = os.getenv("BACKEND_DOMAIN", "localhost:8000")
FRONTEND_BASE_URL   = os.getenv("FRONTEND_BASE_URL", "http://localhost:5173").rstrip("/")


DEFAULT_FILE_STORAGE = "cloudinary_storage.storage.MediaCloudinaryStorage"

CLOUDINARY_STORAGE = {
    "CLOUD_NAME": os.getenv("CLOUDINARY_CLOUD_NAME"),
    "API_KEY":    os.getenv("CLOUDINARY_API_KEY"),
    "API_SECRET": os.getenv("CLOUDINARY_API_SECRET"),
    "MEDIA_ROOT": "media",
}


# ───────── Heroku など DATABASE_URL が定義されている環境では Postgres ─────────

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

# If DATABASE_URL is set (e.g. on Heroku/Render), override with Postgres
if os.getenv("DATABASE_URL"):
    ssl_require = os.getenv("DATABASE_SSL_REQUIRE", "True" if not DEBUG else "False") == "True"
    DATABASES["default"] = dj_database_url.config(conn_max_age=600, ssl_require=ssl_require)


STORAGES = {
    "default": {"BACKEND": "cloudinary_storage.storage.MediaCloudinaryStorage"},
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"},
}

MEDIA_ROOT = os.path.join(BASE_DIR, 'media')  
MEDIA_URL = '/media/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "insecure-dev-key")

ACCOUNT_DEFAULT_HTTP_PROTOCOL = os.getenv("ACCOUNT_PROTOCOL", "http" if DEBUG else "https")

ALLOWED_HOSTS = [ "127.0.0.1", "localhost", BACKEND_DOMAIN ]

# ACCOUNT_ADAPTER = 'core.adapters.MyAccountAdapter'    # ★allauthアダプタ有効化

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',
    'django_filters',
    'django_bootstrap5',
    'django_bootstrap_icons',
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'django_contact_form',
    'widget_tweaks',
    "django_browser_reload",
    'rest_framework.authtoken',
    'corsheaders',
    'rest_framework',
    'dj_rest_auth',
    
    'import_export', 
    "cloudinary",
    "cloudinary_storage",
    'post_office',
    
    'accounts',
    'core.apps.CoreConfig',
    'payments.apps.PaymentsConfig',
    'notifications',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware', 
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    "allauth.account.middleware.AccountMiddleware",
    "django_browser_reload.middleware.BrowserReloadMiddleware",
    'core.middleware.CurrentUserMiddleware',
]

STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

ROOT_URLCONF = 'config.urls'

SITE_ID = 1

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework.authentication.TokenAuthentication",
        # "rest_framework.authentication.SessionAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": ("rest_framework.permissions.IsAuthenticated",),
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 20,
}


AUTH_USER_MODEL = 'accounts.User'

from corsheaders.defaults import default_headers

CORS_ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "https://exmatch.netlify.app",
    FRONTEND_BASE_URL
]
CORS_ALLOW_CREDENTIALS = True  # Cookie運ぶなら必須（Tokenでも問題なし）

# 念のため明示（プリフライトでAuthorization等を許可）
CORS_ALLOW_HEADERS = list(default_headers) + [
    "authorization", "x-csrftoken", "x-requested-with", "x-silent",
]

# 既に入っていればOK
CSRF_TRUSTED_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "https://exmatch.netlify.app",
    f"{'http' if DEBUG else 'https'}://{BACKEND_DOMAIN}", FRONTEND_BASE_URL
]


TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],  # ★これでプロジェクト直下の templates を参照
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

TEMPLATES[0]["OPTIONS"]["context_processors"] += [
    "core.context_processors.matched_set",
]

WSGI_APPLICATION = 'config.wsgi.application'


# Database
# https://docs.djangoproject.com/en/5.1/ref/settings/#databases


# Password validation
# https://docs.djangoproject.com/en/5.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/5.1/topics/i18n/

LANGUAGE_CODE = 'ja'
TIME_ZONE = 'Asia/Tokyo'
USE_I18N = True
USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.1/howto/static-files/

STATIC_URL = '/static/'
STATICFILES_DIRS = [
    BASE_DIR / 'static',  # 例
]

# Default primary key field type
# https://docs.djangoproject.com/en/5.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'




# ---------- メール設定 ----------
EMAIL_BACKEND = os.getenv(
	"DJANGO_EMAIL_BACKEND",          # ← 環境変数があればそれを優先
	"post_office.EmailBackend"       # ← ない場合は post_office を使う
)

EMAIL_HOST = os.getenv("DJANGO_EMAIL_HOST", "")
EMAIL_PORT = int(os.getenv("DJANGO_EMAIL_PORT", "587"))
EMAIL_HOST_USER = os.getenv("DJANGO_EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.getenv("DJANGO_EMAIL_HOST_PASSWORD", "")
EMAIL_USE_TLS = os.getenv("DJANGO_EMAIL_USE_TLS", "True") == "True"
EMAIL_USE_SSL = os.getenv("DJANGO_EMAIL_USE_SSL", "False") == "True"

RAW_FROM_EMAIL = os.getenv("DJANGO_DEFAULT_FROM_EMAIL", "webmaster@localhost")
DEFAULT_FROM_EMAIL = formataddr(("EXMATCH", RAW_FROM_EMAIL))

CONTACT_EMAIL = os.getenv("CONTACT_EMAIL", "support@exmatch.jp")

# == 認証周り ==
AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
    "allauth.account.auth_backends.AuthenticationBackend",
]

ACCOUNT_LOGIN_METHODS = {"email", "username"}  # セットで指定
ACCOUNT_SIGNUP_FIELDS = ["email*", "username*", "password1*", "password2*"]


# --- Sign-Up / 認証設定 -------------------------------
LOGIN_REDIRECT_URL = "/mypage/"
ACCOUNT_LOGOUT_ON_GET = True

ACCOUNT_EMAIL_SUBJECT_PREFIX = "" 

ACCOUNT_EMAIL_VERIFICATION     = "mandatory"

ACCOUNT_LOGIN_ON_EMAIL_CONFIRMATION        = True
ACCOUNT_EMAIL_CONFIRMATION_USER_ACTIVATION = True

ACCOUNT_FORMS = { "signup": "core.forms.CustomSignupForm" }

ACCOUNT_CONFIRM_EMAIL_ON_GET = True                        # クリックだけで確定

ACCOUNT_EMAIL_CONFIRMATION_ANONYMOUS_REDIRECT_URL     = f"{FRONTEND_BASE_URL}/login?verified=1"
ACCOUNT_EMAIL_CONFIRMATION_AUTHENTICATED_REDIRECT_URL = f"{FRONTEND_BASE_URL}/login?verified=1"


# --- STRIPE -------------------------------

STRIPE_PUBLIC_KEY = os.getenv("STRIPE_PUBLIC_KEY")
STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY")
STRIPE_ENDPOINT_SECRET = os.getenv("STRIPE_ENDPOINT_SECRET")

# --- キャンペーン設定 -------------------------------

CAMPAIGN_BONUS_ACTIVE = True
OPTION_DISCOUNT_ACTIVE = True

# --- 垢BAN通報 -------------------------------
REPORT_REASONS = [
	("abuse",   "暴言・ハラスメント"),
	("spam",    "スパム行為"),
	("scam",    "詐欺・金銭要求"),
	("harass",  "ストーカー・しつこい連絡"),
	("illegal", "違法・不適切コンテンツ"),
]
REPORT_BAN_THRESHOLD = 4


# --- settings.py (末尾あたり) ---
NG_WORDS = [
    # 罵倒・蔑称
    "ばか", "バカ", "馬鹿", "アホ", "あほ", "死ね", "しね",
    "クズ", "くず", "ゴミ", "ごみ", "キモい", "きもい",
    "消えろ", "カス", "かす", "ブス", "ぶす", "デブ", "でぶ",
    # 差別・ヘイト
    "障害者", "池沼", "チョン", "在日", "死刑", "殺す",
    # 性的ハラスメント
    "やらせろ", "裸送って", "エロい", "まんこ", "ちんこ",
    # 伏字・変形例
    "ｼﾈ", "氏ね", "ﾀﾋね",
]