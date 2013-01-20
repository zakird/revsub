# -*- coding: utf-8 -*-

from zope.sqlalchemy import ZopeTransactionExtension
from sqlalchemy.orm import scoped_session, sessionmaker
#from sqlalchemy import MetaData
from sqlalchemy.ext.declarative import declarative_base

# Global session manager: DBSession() returns the Thread-local
# session object appropriate for the current web request.
maker = sessionmaker(autoflush=True, autocommit=False,
                     extension=ZopeTransactionExtension())
DBSession = scoped_session(maker)

DeclarativeBase = declarative_base()

metadata = DeclarativeBase.metadata

def init_model(engine):
    """Call me before using any of the tables or classes in the model."""
    DBSession.configure(bind=engine)

# Import your model modules here.
from revsub.model.auth import User, Group, Permission
from revsub.model.course import Course
from revsub.model.summary import PaperSummary
from revsub.model.review import SummaryReview, InstructorSummaryReview, StudentSummaryReview
from revsub.model.paper import Paper