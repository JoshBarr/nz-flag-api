import datetime
import arrow
import sqlalchemy as sql

from flask import Flask, request, url_for, render_template, abort, redirect
from sqlalchemy.orm import sessionmaker, scoped_session
from flask.ext.jsontools import JsonSerializableBase, DynamicJSONEncoder, jsonapi

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, DateTime
from flask.ext.jsontools import JsonSerializableBase, DynamicJSONEncoder
import sqlalchemy as sql


from urlparse import urlparse

app = Flask(__name__)
app.config.from_object('config')
app.config.from_object('env')


from sqlalchemy.orm import sessionmaker, scoped_session

Base = declarative_base(cls=(JsonSerializableBase,))

engine = sql.create_engine(app.config['DATABASE'], echo=False)
session = scoped_session(sessionmaker(bind=engine,
                        autocommit=False,
                        autoflush=False))

from models import Submission, ApiJSONEncoder

app.json_encoder = ApiJSONEncoder
Base.metadata.create_all(engine)


# Get the URL for the static assets
def prepare(model):
    data = model.__json__()
    data['image_path'] = "http://" + request.host + "/static/" + data['image_path']
    data['tags'] = model.tags.split(',')
    return data

@app.route('/api/', methods=['GET'])
@jsonapi
def get_all_submissions():
    items = session.query(Submission).all()
    json_models = [prepare(item) for item in items]
    return json_models


@app.route('/api/<int:id>', methods=['GET'])
@jsonapi
def get_submission(id):
    item = session.query(Submission).filter_by(id=id).first()
    if not item:
        abort(404)
    return prepare(item)

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


if __name__ == '__main__':
    app.run(debug=True, port=5000)

