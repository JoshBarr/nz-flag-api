import os

# These are passed to the app constructor if running locally.
PORT = 5000
HOST = '0.0.0.0'
DEBUG = True

BASE_URL = 'https://www.govt.nz'
BASE_PATH = '/browse/engaging-with-government/the-nz-flag-your-chance-to-decide/gallery/'
STATIC_PATH = 'static'
IMAGE_PATH = 'submissions'
DATABASE = 'mysql://root@localhost/flag'

# If using sqlite, ensure the path exists!
DATABASE_PATH = 'var'

# memcached requires an absolute path. By default look for a memcached.sock in
# the home directory. You could redeclare your specific path in an env.py file
path = os.path.expanduser('~')
CACHE_BACKEND = 'unix:' + path + '/memcached.sock'
CACHE_TIME = 60 * 60
