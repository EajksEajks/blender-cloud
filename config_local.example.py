import os

DEBUG = True

BLENDER_ID_ENDPOINT = 'http://id.local:8000'

SERVER_NAME = 'cloud.local:5001'
SCHEME = 'http'
PILLAR_SERVER_ENDPOINT = f'{SCHEME}://{SERVER_NAME}/api/'

os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = 'true'
os.environ['PILLAR_MONGO_DBNAME'] = 'cloud'
os.environ['PILLAR_MONGO_PORT'] = '27017'
os.environ['PILLAR_MONGO_HOST'] = 'mongo'

os.environ['PILLAR_SERVER_ENDPOINT'] = PILLAR_SERVER_ENDPOINT

SECRET_KEY = '##DEFINE##'

OAUTH_CREDENTIALS = {
    'blender-id': {
        'id': 'CLOUD-OF-SNOWFLAKES-42',
        'secret': '##DEFINE##',
    }
}

MAIN_PROJECT_ID = '##DEFINE##'
URLER_SERVICE_AUTH_TOKEN = '##DEFINE##'

ZENCODER_API_KEY = '##DEFINE##'
ZENCODER_NOTIFICATIONS_SECRET = '##DEFINE##'
ZENCODER_NOTIFICATIONS_URL = 'http://zencoderfetcher/'
