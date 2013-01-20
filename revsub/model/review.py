# -*- coding: utf-8 -*-
from datetime import datetime
from sqlalchemy import *
from sqlalchemy.orm import mapper, relation
from sqlalchemy import Table, ForeignKey, Column
from sqlalchemy.types import Integer, Unicode, UnicodeText
from sqlalchemy.orm import relation, backref

from revsub.model import DeclarativeBase, metadata, DBSession, PaperSummary, User

class SummaryReview(DeclarativeBase):
    __tablename__ = 'summary_reviews'
    
    
    id = Column(Integer, primary_key=True)
    type = Column(Unicode(255), nullable=False)
    __mapper_args__ = {'polymorphic_on': type, 'polymorphic_identity': 'review'}
    summary_id = Column(Integer, ForeignKey('paper_summaries.id'))
    summary = relation(PaperSummary, backref="reviews")
    
    creator_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    created_at = Column(DateTime, default=datetime.now)
    creator = relation(User)
    
    rating = Column(Integer)
    comments = Column(UnicodeText)
    
class InstructorSummaryReview(SummaryReview):
    __mapper_args__ = {'polymorphic_identity': 'instructor_review'}
    
class StudentSummaryReview(SummaryReview):
    __mapper_args__ = {'polymorphic_identity': 'student_review'}