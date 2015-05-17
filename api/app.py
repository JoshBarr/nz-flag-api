import sqlalchemy as sql
import os
from flask import Flask, request, url_for, abort, redirect
from sqlalchemy.orm import sessionmaker, scoped_session
from flask.ext.jsontools import jsonapi
from models import Base, Submission, ApiJSONEncoder
from werkzeug.contrib.cache import MemcachedCache


app = Flask(__name__)
app.config.from_object('config')

# Load some env config if it's there
env_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'env.py'))

if os.path.exists(env_path):
    app.config.from_object('env')

# This is dirty. Ensuring some directories exist, because who reads the manual?
db_path = app.config["DATABASE_PATH"]
if db_path:
    if not os.path.exists(db_path):
        os.makedirs(db_path)

static_path = app.config["STATIC_PATH"]
if static_path:
    if not os.path.exists(static_path):
        os.makedirs(static_path)


engine = sql.create_engine(app.config['DATABASE'], echo=False)
session = scoped_session(sessionmaker(bind=engine,
                         autocommit=False,
                         autoflush=False))


app.json_encoder = ApiJSONEncoder
Base.metadata.create_all(engine)

cache = MemcachedCache([app.config['CACHE_BACKEND']])


# Get the URL for the static assets
def prepare(model):
    data = model.__json__()
    data['image_path'] = "http://" + request.host + "/static/" + data['image_path']
    data['tags'] = model.tags.split(',')
    return data


@app.route('/api/', methods=['GET'])
@jsonapi
def get_all_submissions():
    items = cache.get('get_all_submissions')

    if items is None:
        print "not from cache"
        items = session.query(Submission).order_by(Submission.id.desc()).all()
        cache.set('get_all_submissions', items, timeout=app.config['CACHE_TIME'])

    return [prepare(item) for item in items]


@app.route('/api/<int:id>', methods=['GET'])
@jsonapi
def get_submission(id):
    item = cache.get('get_submission_%d' % id)

    if item is None:
        item = session.query(Submission).filter_by(id=id).first()
        cache.set('get_submission_%d' % id, item, timeout=app.config['CACHE_TIME'])

    if not item:
        abort(404)

    return prepare(item)


@app.route('/api/tag/<string:name>', methods=['GET'])
@jsonapi
def get_by_tag(name):
    """
    This would probably benefit from being refactored as a many-to-many
    relationship instead of a comma separated string
    """
    items = session.query(Submission)\
                   .filter(Submission.tags.like('%' + name + '%'))\
                   .order_by(Submission.id.desc()).all()
    if not items:
        abort(404)

    return [prepare(item) for item in items]


@app.route('/api/description/<string:name>', methods=['GET'])
@jsonapi
def get_by_desc(name):
    items = session.query(Submission)\
                   .filter(Submission.description.like('%' + name + '%'))\
                   .order_by(Submission.id.desc()).all()
    if not items:
        abort(404)

    return [prepare(item) for item in items]


@app.errorhandler(404)
@jsonapi
def page_not_found(e):
    return {
        'code': 404,
        'message': 'Page not found'
    }


@app.route('/', methods=['GET'])
def index():
    return redirect(url_for('get_all_submissions'))
