from datetime import datetime
from sqlalchemy import *
from sqlalchemy.orm import mapper, relation
from sqlalchemy import Table, ForeignKey, Column
from sqlalchemy.types import Integer, Unicode, UnicodeText
from sqlalchemy.orm import relation, backref
from revsub.model import DeclarativeBase, metadata, DBSession, Group, User

class Course(DeclarativeBase):
    __tablename__ = 'courses'
    
    id = Column(Integer, primary_key=True)
    name = Column(Unicode(255), nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)
    instructors_id = Column(Integer, ForeignKey('groups.id'))
    students_id = Column(Integer, ForeignKey('groups.id'))
    
    instructors = relation(Group, backref='courses_taught',
                    primaryjoin="Course.instructors_id == Group.id")
    students = relation(Group, backref='courses_enrolled_in', 
                    primaryjoin="Course.students_id == Group.id")

@property
def get_courses_enrolled_in(self):
    return DBSession.query(Course).join(Course.students).filter(User.id == self.id)
    
User.courses_enrolled_in = get_courses_enrolled_in