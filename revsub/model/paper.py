from datetime import datetime

from sqlalchemy import *
from sqlalchemy.orm import mapper, relation
from sqlalchemy import Table, ForeignKey, Column
from sqlalchemy.types import Integer, Unicode, UnicodeText
from sqlalchemy.orm import relation, backref

from revsub.model import DeclarativeBase, metadata, DBSession, Course, User

class Paper(DeclarativeBase):
    __tablename__ = 'papers'
    
    id = Column(Integer, primary_key=True)
    course_id = Column(Integer, ForeignKey('courses.id'), nullable=False)
    name = Column(Unicode(1024), nullable=False)
    abstract = Column(UnicodeText)
    download_url = Column(Unicode(1024))
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    created_by = Column(Integer, ForeignKey('users.id'), nullable=False)
    due_date = Column(DateTime, nullable=False)
    
    course = relation(Course, backref='papers')
    creator = relation(User, backref='created_papers')