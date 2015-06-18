import sqlalchemy as sql
import os
from flask import Flask, request, url_for, abort, redirect
from sqlalchemy.orm import sessionmaker, scoped_session
from flask.ext.jsontools import jsonapi
from models import Base, Submission, Tag, Designer, Location, ApiJSONEncoder
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
    data['tags'] = [x.__json__() for x in model.tags]
    data['designer'] = model.designer.__json__()
    data['designer']['location'] = model.designer.location.__json__()
    del data['designer']['location_id']
    return data


@app.route('/api/', methods=['GET'])
@jsonapi
def api_index():
    return [{
        "available_methods": [
            {
                "name": "flags",
                "path": "http://" + request.host + "/api/flags/",
                "available_methods": [
                    "http://" + request.host + "/api/flags/filter/designer/",
                    "http://" + request.host + "/api/flags/filter/designer-name/",
                    "http://" + request.host + "/api/flags/filter/tag-name/",
                    "http://" + request.host + "/api/flags/filter/location-name/",
                    "http://" + request.host + "/api/flags/filter/description/"
                ]
            },
            {
                "name": "designers",
                "path": "http://" + request.host + "/api/designers/"
            },
            {
                "name": "locations",
                "path": "http://" + request.host + "/api/locations/"
            },
            {
                "name": "tags",
                "path": "http://" + request.host + "/api/tags/"
            }
        ]
    }]



@app.route('/api/designers/', methods=['GET'])
@jsonapi
def get_all_designers():
    # items = cache.get('get_all_submissions')

    # if items is None:
    print "not from cache"
    items = session.query(Designer).order_by(Designer.id.asc()).all()
    return [x.__json__() for x in items]


@app.route('/api/tags/', methods=['GET'])
@jsonapi
def get_all_tags():
    # items = cache.get('get_all_submissions')

    # if items is None:
    # print "not from cache"
    items = session.query(Tag).order_by(Tag.id.asc()).all()
    return [x.__json__() for x in items]


@app.route('/api/locations/', methods=['GET'])
@jsonapi
def get_all_locations():
    # items = cache.get('get_all_submissions')

    # if items is None:
    # print "not from cache"
    items = session.query(Location).order_by(Location.id.asc()).all()
    return [x.__json__() for x in items]


@app.route('/api/flags/', methods=['GET'])
@jsonapi
def get_all_submissions():
    items = cache.get('get_submissions')

    if items is None:
        print "not from cache"
        items = session.query(Submission).join(Submission.designer).join(Submission.tags).all()
        cache.set('get_submissions', items, timeout=app.config['CACHE_TIME'])

    if not items:
        abort(404)

    return [prepare(item) for item in items]


@app.route('/api/flags/<int:id>', methods=['GET'])
@jsonapi
def get_submission(id):
    item = cache.get('get_submission_%d' % id)

    if item is None:
        item = session.query(Submission).filter_by(id=id).join(Submission.designer).join(Submission.tags).first()
        cache.set('get_submission_%d' % id, item, timeout=app.config['CACHE_TIME'])

    if not item:
        abort(404)

    return prepare(item)


@app.route('/api/flags/filter/designer/<int:id>', methods=['GET'])
@jsonapi
def get_by_designer(id):
    """
    This would probably benefit from being refactored as a many-to-many
    relationship instead of a comma separated string
    """
    items = session.query(Submission).join(Submission.designer, aliased=True)\
                   .filter_by(id=id)\
                   .order_by(Submission.id.desc()).all()
                   # .filter_by.like('%' + name + '%'))\
    if not items:
        abort(404)

    return [prepare(item) for item in items]

@app.route('/api/flags/filter/designer-name/<string:name>', methods=['GET'])
@jsonapi
def get_by_designer_name(name):
    """
    This would probably benefit from being refactored as a many-to-many
    relationship instead of a comma separated string
    """
    items = session.query(Submission).join(Submission.designer, aliased=True)\
                   .filter_by(name=name)\
                   .order_by(Submission.id.desc()).all()
    if not items:
        abort(404)

    return [prepare(item) for item in items]

@app.route('/api/flags/filter/tag-name/<string:name>', methods=['GET'])
@jsonapi
def get_by_tag_name(name):
    """
    This would probably benefit from being refactored as a many-to-many
    relationship instead of a comma separated string
    """
    items = session.query(Submission).join(Submission.tags, aliased=True)\
                   .filter_by(name=name)\
                   .order_by(Submission.id.desc()).all()
    if not items:
        abort(404)

    return [prepare(item) for item in items]



@app.route('/api/flags/filter/location-name/<string:name>', methods=['GET'])
@jsonapi
def get_by_location(name):
    """
    This would probably benefit from being refactored as a many-to-many
    relationship instead of a comma separated string
    """
    items = session.query(Submission).join(Submission.designer, aliased=True).join(Designer.location)\
                   .filter_by(name=name)\
                   .order_by(Submission.id.desc()).all()
    if not items:
        abort(404)

    return [prepare(item) for item in items]


@app.route('/api/flags/filter/description/<string:name>', methods=['GET'])
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
