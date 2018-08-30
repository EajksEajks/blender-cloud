import os
from collections import defaultdict

DEBUG = False

SCHEME = 'https'
PREFERRED_URL_SCHEME = 'https'
SERVER_NAME = 'cloud.blender.org'

# os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = 'true'
os.environ['PILLAR_MONGO_DBNAME'] = 'cloud'
os.environ['PILLAR_MONGO_PORT'] = '27017'
os.environ['PILLAR_MONGO_HOST'] = 'mongo'

USE_X_SENDFILE = True

STORAGE_BACKEND = 'gcs'

CDN_SERVICE_DOMAIN = 'blendercloud-pro.r.worldssl.net'
CDN_CONTENT_SUBFOLDER = ''
CDN_STORAGE_ADDRESS = 'push-11.cdnsun.com'

CACHE_TYPE = 'redis'  # null
CACHE_KEY_PREFIX = 'pw_'
CACHE_REDIS_HOST = 'redis'
CACHE_REDIS_PORT = '6379'
CACHE_REDIS_URL = 'redis://redis:6379'

PILLAR_SERVER_ENDPOINT = 'https://cloud.blender.org/api/'

BLENDER_ID_ENDPOINT = 'https://www.blender.org/id/'

GCLOUD_APP_CREDENTIALS = '/data/config/google_app.json'
GCLOUD_PROJECT = 'blender-cloud'

MAIN_PROJECT_ID = '563a9c8cf0e722006ce97b03'
# MAIN_PROJECT_ID = '57aa07c088bef606e89078bd'

ALGOLIA_INDEX_USERS = 'pro_Users'
ALGOLIA_INDEX_NODES = 'pro_Nodes'

ZENCODER_NOTIFICATIONS_URL = 'https://cloud.blender.org/api/encoding/zencoder/notifications'

FILE_LINK_VALIDITY = defaultdict(
    lambda: 3600 * 24 * 30,  # default of 1 month.
    gcs=3600 * 23,  # 23 hours for Google Cloud Storage.
    cdnsun=3600 * 23
)

LOGGING = {
    'version': 1,
    'formatters': {
        'default': {'format': '%(levelname)8s %(name)s %(message)s'}
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'default',
            'stream': 'ext://sys.stderr',
        }
    },
    'loggers': {
        'pillar': {'level': 'INFO'},
        # 'pillar.auth': {'level': 'DEBUG'},
        # 'pillar.api.blender_id': {'level': 'DEBUG'},
        # 'pillar.api.blender_cloud.subscription': {'level': 'DEBUG'},
        'bcloud': {'level': 'INFO'},
        'cloud': {'level': 'INFO'},
        'attract': {'level': 'INFO'},
        'flamenco': {'level': 'INFO'},
        # 'pillar.api.file_storage': {'level': 'DEBUG'},
        # 'pillar.api.file_storage.ensure_valid_link': {'level': 'INFO'},
        'pillar.api.file_storage.refresh_links_for_backend': {'level': 'DEBUG'},
        'werkzeug': {'level': 'DEBUG'},
        'eve': {'level': 'WARNING'},
        # 'elasticsearch': {'level': 'DEBUG'},
    },
    'root': {
        'level': 'WARNING',
        'handlers': [
            'console',
        ],
    }
}

REDIRECTS = {
    # For old links, refer to the services page (hopefully it refreshes then)
    'downloads/blender_cloud-latest-bundle.zip': 'https://cloud.blender.org/services#blender-addon',

    # Latest Blender Cloud add-on; remember to update BLENDER_CLOUD_ADDON_VERSION.
    'downloads/blender_cloud-latest-addon.zip':
        'https://storage.googleapis.com/institute-storage/addons/blender_cloud-1.8.0.addon.zip',

    # Redirect old Grafista endpoint to /stats
    '/stats/': '/stats',
}

# Latest version of the add-on; remember to update REDIRECTS.
BLENDER_CLOUD_ADDON_VERSION = '1.8.0'

UTM_LINKS = {
    'cartoon_brew': {
        'image': 'https://imgur.com/13nQTi3.png',
        'link': 'https://store.blender.org/product/membership/'
    }
}

# Disabled until we have regenerated the majority of the links.
CELERY_BEAT_SCHEDULE = {
    'regenerate-expired-links': {
        'task': 'pillar.celery.file_link_tasks.regenerate_all_expired_links',
        'schedule': 600,  # every N seconds
        'args': ('gcs', 500)
    },
}

SVNMAN_REPO_URL = 'https://svn.blender.cloud/repo/'
SVNMAN_API_URL = 'https://svn.blender.cloud/api/'

# Mail options, see pillar.celery.email_tasks.
SMTP_HOST = 'proog.blender.org'
SMTP_PORT = 25
SMTP_USERNAME = 'server@blender.cloud'
SMTP_TIMEOUT = 30  # timeout in seconds, https://docs.python.org/3/library/smtplib.html#smtplib.SMTP
MAIL_RETRY = 180  # in seconds, delay until trying to send an email again.
MAIL_DEFAULT_FROM_NAME = 'Blender Cloud'
MAIL_DEFAULT_FROM_ADDR = 'cloudsupport@blender.org'

# MUST be 8 characters long, see pillar.flask_extra.HashedPathConverter
# STATIC_FILE_HASH = '12345678'
# The value used in production is appended from Dockerfile.
