# This is your project's main settings file that can be committed to your
# repo. If you need to override a setting locally, use settings_local.py

from funfactory.settings_base import *

# Name of the top-level module where you put all your apps.
# If you did not install Playdoh with the funfactory installer script
# you may need to edit this value. See the docs about installing from a
# clone.
PROJECT_MODULE = 'rockit'

# Bundles is a dictionary of two dictionaries, css and js, which list css files
# and js files that can be bundled together by the minify app.
MINIFY_BUNDLES = {
    'css': {
        'example_css': (
            'css/examples/main.css',
        ),
        'example_mobile_css': (
            'css/examples/mobile.css',
        ),
    },
    'js': {
        'example_js': (
            'js/examples/libs/jquery-1.4.4.min.js',
            'js/examples/libs/jquery.cookie.js',
            'js/examples/init.js',
        ),
    }
}

# Defines the views served for root URLs.
ROOT_URLCONF = '%s.urls' % PROJECT_MODULE

INSTALLED_APPS = list(INSTALLED_APPS) + [
    # Application base, containing global templates.
    '%s.base' % PROJECT_MODULE,
    'rockit.sync',
    'rockit.music',
    'django.contrib.admin',
]


MIDDLEWARE_CLASSES = list(MIDDLEWARE_CLASSES) + [
    'rockit.base.middleware.LogExceptionsMiddleware'
]


# Because Jinja2 is the default template loader, add any non-Jinja templated
# apps here:
JINGO_EXCLUDE_APPS = [
    'admin',
    'registration',
]

# Tells the extract script what files to look for L10n in and what function
# handles the extraction. The Tower library expects this.
DOMAIN_METHODS['messages'] = [
    ('%s/**.py' % PROJECT_MODULE,
        'tower.management.commands.extract.extract_tower_python'),
    ('%s/**/templates/**.html' % PROJECT_MODULE,
        'tower.management.commands.extract.extract_tower_template'),
    ('templates/**.html',
        'tower.management.commands.extract.extract_tower_template'),
],

# # Use this if you have localizable HTML files:
# DOMAIN_METHODS['lhtml'] = [
#    ('**/templates/**.lhtml',
#        'tower.management.commands.extract.extract_tower_template'),
# ]

# # Use this if you have localizable JS files:
# DOMAIN_METHODS['javascript'] = [
#    # Make sure that this won't pull in strings from external libraries you
#    # may use.
#    ('media/js/**.js', 'javascript'),
# ]

# Paths that don't require a locale code in the URL.
SUPPORTED_NONLOCALES = [
    'media',
    'admin',
    'upload',
    'checkfiles',
    'music',
]

# Time limit in seconds for background tasks.
CELERYD_TASK_SOFT_TIME_LIMIT = 60 * 5

# Used for JWT signature verification.
SITE_URL = 'http://localhost:8000'

# Client / access_key for signed JWT API requests.
# Each client in this list will be authorized to interact with the service.
API_CLIENTS = {'client1': '<secret key>'}

LOGGING = {'loggers': {'playdoh': {'level': logging.INFO,
                                   'handlers': ['console']},
                       'rockit': {'level': logging.DEBUG,
                                  'handlers': ['console']}}}

UPLOAD_TEMP_DIR = os.path.join(ROOT, 'tmp')

S3_ACCESS_ID = '<set in local>'
S3_SECRET_KEY = '<set in local>'
S3_BUCKET = 'rockitscratch'

LAST_FM_KEY = '<set in local>'
