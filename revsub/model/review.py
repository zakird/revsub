# -*- coding: utf-8 -*-
from datetime import datetime
from sqlalchemy import *
from sqlalchemy.orm import mapper, relation
from sqlalchemy import Table, ForeignKey, Column
from sqlalchemy.types import Integer, Unicode, UnicodeText
from sqlalchemy.orm import relation, backref

from revsub.model import DeclarativeBase, metadata, DBSession, PaperSummary, User

"""
questions for peer review

    1. Did this person read the paper?
    
        0. No/ only hte title
        1. Somewhat/ probably skimmed it
        2. Yes/read it pretty carefully
        3. Wow!/Must be one of the authors
        
    2. Did this person think carefully about the paper?
        0. No/Just spit back the contents
        1. Somewhat/this seems like shallow verbiage
        2. Yes/made some good points
        3. Wow!/this is really inciteful 
        
    3. Comments
    
    show them --
        your average score
        overall average score for course

"""

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
    insight_rating = Column(Integer)
    comments = Column(UnicodeText)
    
    def __init__(self, summary, reading_rating,
                    insight_rating, comments, creator):
        self.summary_id = summary.id
        self.rating = reading_rating
        self.insight_rating = insight_rating
        self.comments = comments
        self.creator_id = creator.id
    
    
class InstructorSummaryReview(SummaryReview):
    __mapper_args__ = {'polymorphic_identity': 'instructor_review'}
    
class StudentSummaryReview(SummaryReview):
    __mapper_args__ = {'polymorphic_identity': 'student_review'}