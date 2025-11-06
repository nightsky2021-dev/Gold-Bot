"""
Django settings for gold_shop project.
"""
import environ
import os
from pathlib import Path

# Build paths inside the project
BASE_DIR = Path(__file__).resolve().parent.parent

# Initialize environment variables
env = environ.Env(
    DEBUG=(bool, False),
    ALLOWED_HOSTS=(list, []),
)

# Read .env file (tolerate malformed lines)
env_file = BASE_DIR / '.env'
if env_file.exists():
    try:
        environ.Env.read_env(env_file)
    except Exception:
        # Ignore invalid .env lines to avoid crashing management commands
        pass

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-change-this-in-production')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env('DEBUG')

ALLOWED_HOSTS = env.list('ALLOWED_HOSTS') or ['localhost', '127.0.0.1']

# Application definition
INSTALLED_APPS = [
    # Admin enhancements (must be before django.contrib.admin)
    'jazzmin',
    
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Third-party apps for admin enhancements
    'import_export',
    'rangefilter',
    'adminactions',
    'auditlog',
    'django_filters',
    
    # Local apps
    'users.apps.UsersConfig',
    'trading.apps.TradingConfig',
    'bot.apps.BotConfig',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    # Audit logging middleware
    'auditlog.middleware.AuditlogMiddleware',
]

ROOT_URLCONF = 'gold_shop.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
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

WSGI_APPLICATION = 'gold_shop.wsgi.application'

# Database (force SQLite regardless of DATABASE_URL)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': str(BASE_DIR / 'db.sqlite3'),
    }
}

# Password validation
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
LANGUAGE_CODE = os.getenv('LANGUAGE_CODE', 'fa-ir')
TIME_ZONE = os.getenv('TIME_ZONE', 'Asia/Tehran')
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]

# Media files
MEDIA_URL = 'media/'
MEDIA_ROOT = BASE_DIR / 'mediafiles'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '')

# Price Provider Configuration
# Options: 'anigold' or 'navasan'
PRICE_PROVIDER_TYPE = os.getenv('PRICE_PROVIDER_TYPE', 'anigold')

# Anigold API Configuration (Default)
ANIGOLD_API_KEY = os.getenv('ANIGOLD_API_KEY', '1a233fab-04d1-47b2-b732-813d93795c43')

# Navasan API Configuration (Legacy)
NAVASAN_API_KEY = os.getenv('NAVASAN_API_KEY', 'freeTET7c1g57cU7kPnjQa4KAMP7BWaS')

# ============================================
# ADMIN PANEL ENHANCEMENTS
# ============================================

# Jazzmin Admin Theme Configuration
JAZZMIN_SETTINGS = {
    # Title on the login screen and browser tab
    "site_title": "پنل مدیریت طلا",
    "site_header": "سامانه معاملات طلا",
    "site_brand": "مدیریت طلا",
    "site_logo": None,
    "login_logo": None,
    "site_logo_classes": "img-circle",
    "site_icon": None,
    
    # Welcome text on the login screen
    "welcome_sign": "خوش آمدید به پنل مدیریت",
    
    # Copyright on the footer
    "copyright": "سامانه معاملات طلا",
    
    # Links to put along the top menu
    "topmenu_links": [
        {"name": "خانه", "url": "admin:index", "permissions": ["auth.view_user"]},
        {"name": "داشبورد", "url": "/admin/dashboard/", "permissions": ["auth.view_user"]},
        {"model": "auth.User"},
        {"app": "trading"},
    ],
    
    # Whether to display the side menu
    "show_sidebar": True,
    
    # Whether to aut expand the menu
    "navigation_expanded": True,
    
    # Hide these apps when generating side menu
    "hide_apps": [],
    
    # Hide these models when generating side menu
    "hide_models": [],
    
    # Order of apps and models in side menu
    "order_with_respect_to": ["users", "trading", "auth"],
    
    # Custom icons for apps/models
    "icons": {
        "auth": "fas fa-users-cog",
        "auth.user": "fas fa-user",
        "auth.Group": "fas fa-users",
        "users.profile": "fas fa-user-circle",
        "users.bankaccount": "fas fa-university",
        "trading.product": "fas fa-coins",
        "trading.order": "fas fa-shopping-cart",
        "trading.transaction": "fas fa-exchange-alt",
        "trading.withdrawrequest": "fas fa-money-check-alt",
    },
    
    # Icons that are used when one is not manually specified
    "default_icon_parents": "fas fa-chevron-circle-right",
    "default_icon_children": "fas fa-circle",
    
    # UI Customizer Options
    "show_ui_builder": False,
    
    # Change view button behavior
    "changeform_format": "horizontal_tabs",
    "changeform_format_overrides": {
        "auth.user": "collapsible",
        "auth.group": "vertical_tabs",
    },
    
    # Language chooser
    "language_chooser": False,
    
    # Custom CSS/JS
    "custom_css": "css/persian_fonts.css",
    "custom_js": None,
    
    # Theme settings
    "theme": "flatly",  # Options: default, darkly, flatly, journal, litera, lux, materia, minty, pulse, sandstone, simplex, slate, spacelab, superhero, united, yeti
    
    # Color theme for navigation bar
    "navbar": "navbar-dark",  # navbar-dark or navbar-light
    "navbar_fixed": True,
    "footer_fixed": False,
    "body_small_text": False,
    
    # Sidebar settings
    "sidebar": "sidebar-dark-primary",
    "sidebar_nav_small_text": False,
    "sidebar_disable_expand": False,
    "sidebar_nav_child_indent": True,
    "sidebar_nav_compact_style": False,
    "sidebar_nav_legacy_style": False,
    "sidebar_nav_flat_style": False,
    
    # Additional links in user menu
    "usermenu_links": [
        {"name": "پشتیبانی", "url": "https://example.com/support", "new_window": True},
        {"model": "auth.user"}
    ],
}

JAZZMIN_UI_TWEAKS = {
    "navbar_small_text": False,
    "footer_small_text": False,
    "body_small_text": False,
    "brand_small_text": False,
    "brand_colour": "navbar-primary",
    "accent": "accent-primary",
    "navbar": "navbar-dark navbar-primary",
    "no_navbar_border": False,
    "navbar_fixed": True,
    "layout_boxed": False,
    "footer_fixed": False,
    "sidebar_fixed": True,
    "sidebar": "sidebar-dark-primary",
    "sidebar_nav_small_text": False,
    "sidebar_disable_expand": False,
    "sidebar_nav_child_indent": True,
    "sidebar_nav_compact_style": False,
    "sidebar_nav_legacy_style": False,
    "sidebar_nav_flat_style": False,
    "theme": "flatly",
    "dark_mode_theme": None,
    "button_classes": {
        "primary": "btn-primary",
        "secondary": "btn-secondary",
        "info": "btn-info",
        "warning": "btn-warning",
        "danger": "btn-danger",
        "success": "btn-success"
    }
}

# Import/Export Settings
IMPORT_EXPORT_USE_TRANSACTIONS = True

# Admin Actions Settings
ADMINACTIONS_MERGE_DUPLICATE = True

