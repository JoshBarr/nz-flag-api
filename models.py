from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, DateTime
from flask.ext.jsontools import JsonSerializableBase, DynamicJSONEncoder
import sqlalchemy as sql
import arrow
import datetime

from sqlalchemy.orm import sessionmaker, scoped_session

Base = declarative_base(cls=(JsonSerializableBase,))

engine = sql.create_engine('sqlite:///var/submissions-test.sqlite', echo=False)
session = scoped_session(sessionmaker(bind=engine,
                        autocommit=False,
                        autoflush=False))


class ApiJSONEncoder(DynamicJSONEncoder):
    def default(self, o):
        if isinstance(o, arrow.Arrow):
            return str(o)
        if isinstance(o, datetime.date):
            t = arrow.Arrow.fromdatetime(o)
            return str(t)
        if isinstance(o, set):
            return list(o)

        return super(DynamicJSONEncoder, self).default(o)


class Submission(Base):
    __tablename__ = 'submissions'
    id = Column(Integer, primary_key=True)
    title = Column(String)
    designer = Column(String)
    designer_location = Column(String)
    suggested_by = Column(String)
    suggested_by_location = Column(String)
    url = Column(String)
    last_scraped = Column(DateTime)
    description = Column(String)
    image_path = Column(String)
    tags = Column(String)

    def __repr__(self):
        return "<Submission(id='%s', designer='%s', title='%s')>" % (
                            self.id, self.designer.encode('utf-8'), self.title.encode('utf-8'))
