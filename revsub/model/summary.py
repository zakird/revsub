from datetime import datetime
from sqlalchemy import *
from sqlalchemy.orm import mapper, relation
from sqlalchemy import Table, ForeignKey, Column
from sqlalchemy.types import Integer, Unicode, UnicodeText
from sqlalchemy.orm import relation, backref

from revsub.model.paper import Paper
from revsub.model.course import Course

from revsub.model import DeclarativeBase, metadata, DBSession, Group, User

class PaperSummary(DeclarativeBase):
    __tablename__ = 'paper_summaries'
    
    id = Column(Integer, primary_key=True)
    paper_id = Column(Integer, ForeignKey('papers.id'), nullable=False)
    student_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    summary = Column(UnicodeText)
    submitted_at = Column(DateTime, default=datetime.now)
    
    student = relation(User, backref='submitted_summaries')
    paper = relation(Paper, backref = 'submitted_summaries')
    