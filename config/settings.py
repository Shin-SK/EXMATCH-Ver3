# settings
from pathlib import Path
from dotenv import load_dotenv
import os
import environ, os
import dj_database_url
from email.utils import formataddr


BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")   


DEFAULT_FILE_STORAGE = "cloudinary_storage.storage.MediaCloudinaryStorage"

CLOUDINARY_STORAGE = {
    "CLOUD_NAME": os.getenv("CLOUDINARY_CLOUD_NAME"),
    "API_KEY":    os.getenv("CLOUDINARY_API_KEY"),
    "API_SECRET": os.getenv("CLOUDINARY_API_SECRET"),
    "MEDIA_ROOT": "media",
}

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "exmatch_local",
        "USER": "exuser",
        "PASSWORD": "admin",
        "HOST": "localhost",
        "PORT": "",
    }
}

STORAGES = {
    "default": {"BACKEND": "cloudinary_storage.storage.MediaCloudinaryStorage"},
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"},
}


# ───────── Heroku など DATABASE_URL が定義されている環境では Postgres ─────────
if "DATABASE_URL" in os.environ:
    DATABASES["default"] = dj_database_url.config(
        conn_max_age=600,
        ssl_require=True,  # Heroku 用
    )

MEDIA_ROOT = os.path.join(BASE_DIR, 'media')  
MEDIA_URL = '/media/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-l!yk$4c0m_*3c_j2lc*zijw(0bcf@3io%gkop&%852)^=_j3p4'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['127.0.0.1', 'localhost', 'testserver' , 'exmatch-ddcece3ee103.herokuapp.com']

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django_filters',
    'channels',
    'django_bootstrap5',
    'django_bootstrap_icons',
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'django_contact_form',
    'widget_tweaks',
    "django_browser_reload",
    "cloudinary",
    "cloudinary_storage",
    'post_office',

    'core.apps.CoreConfig',
    'payments.apps.PaymentsConfig',
    'notifications',
]

MIDDLEWARE = [
    'core.middleware.CurrentUserMiddleware',
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
]

STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

ROOT_URLCONF = 'config.urls'

SITE_ID = 1

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

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

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


ASGI_APPLICATION = 'config.asgi.application'
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {"hosts": [("127.0.0.1", 6379)]},
    },
}


# ---------- メール設定 ----------
EMAIL_BACKEND = 'post_office.EmailBackend'

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


# --- Sign-Up / 認証設定 -------------------------------
LOGIN_REDIRECT_URL = "/mypage/"
ACCOUNT_LOGOUT_ON_GET = True

ACCOUNT_EMAIL_SUBJECT_PREFIX = "" 

ACCOUNT_USERNAME_REQUIRED      = True
ACCOUNT_EMAIL_REQUIRED         = True
ACCOUNT_EMAIL_VERIFICATION     = "mandatory"
ACCOUNT_AUTHENTICATION_METHOD  = "username_email"

ACCOUNT_EMAIL_CONFIRMATION_AUTHENTICATED_REDIRECT_URL = "/signup/profile/"
ACCOUNT_LOGIN_ON_EMAIL_CONFIRMATION        = True
ACCOUNT_EMAIL_CONFIRMATION_USER_ACTIVATION = True

ACCOUNT_FORMS = { "signup": "core.forms.CustomSignupForm" }


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