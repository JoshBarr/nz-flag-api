from sqlalchemy.ext.declarative import declarative_base
from flask.ext.jsontools import JsonSerializableBase
from sqlalchemy import Column, Integer, String, DateTime, Table, ForeignKey, Text
from sqlalchemy.orm import relationship, backref
from flask.ext.jsontools import DynamicJSONEncoder
import arrow
import datetime


Base = declarative_base(cls=(JsonSerializableBase,))


class ApiJSONEncoder(DynamicJSONEncoder):
    def default(self, o):
        if isinstance(o, Designer):
            return "Designer"
        if isinstance(o, Tag):
            return ["some", "tags"]
        if isinstance(o, Location):
            return {}
        if isinstance(o, arrow.Arrow):
            return str(o)
        if isinstance(o, datetime.date):
            t = arrow.Arrow.fromdatetime(o)
            return str(t)
        if isinstance(o, set):
            return list(o)

        return super(DynamicJSONEncoder, self).default(o)


submissions_to_tags = Table('submissions_to_tags', Base.metadata,
    Column('submission_id', Integer, ForeignKey('submission.id')),
    Column('tag_id', Integer, ForeignKey('tag.id'))
)


class Submission(Base):
    __tablename__ = 'submission'
    id = Column(Integer, primary_key=True)
    # submission_id = Column(Integer)
    designer_id = Column(Integer, ForeignKey('designer.id'))
    title = Column(String(128))
    suggested_by = Column(String(128))
    suggested_by_location = Column(String(128))
    url = Column(String(128))
    last_scraped = Column(DateTime)
    description = Column(Text)
    image_path = Column(String(128))
    tags = relationship("Tag",
                    secondary=submissions_to_tags,
                    backref="submission")

    def __repr__(self):
        return "<Submission(id='%s', designer='%s', title='%s')>" % (
               self.id, self.designer_id, self.title.encode('utf-8'))


class Designer(Base):
    __tablename__ = 'designer'
    id = Column(Integer, primary_key=True)
    name = Column(String(128), unique=True)
    location_id = Column(Integer, ForeignKey('location.id'))
    location = relationship("Location")
    submissions = relationship('Submission', backref='designer')

class Location(Base):
    __tablename__ = 'location'
    id = Column(Integer, primary_key=True)
    name = Column(String(128), unique=True)



class Tag(Base):
    __tablename__ = 'tag'
    id = Column(Integer, primary_key=True)
    name = Column(String(128), unique=True)

