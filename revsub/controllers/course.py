# -*- coding: utf-8 -*-
from tg import expose, flash, redirect, require, request
from tg.i18n import ugettext as _, lazy_ugettext as l_
from tg.predicates import has_permission

from revsub.lib.base import BaseController
from revsub.model import DeclarativeBase, metadata, DBSession, Group, User, Course, Paper, PaperSummary


__all__ = ['CourseController']

class CourseController(BaseController):
    
    # The predicate that must be met for all the actions in this controller:
    #allow_only = has_permission('student')
    
    @expose('revsub.templates.courses')
    def index(self):
        login = request.environ.get('repoze.who.identity').get('repoze.who.userid')
        user = DBSession.query(User).filter(User.user_name == login).one()
        courses = {}
        for course in user.courses_enrolled_in:
            courses[course.name] = []
            for paper, summary in DBSession.query(Paper, PaperSummary).outerjoin(PaperSummary).all():
                courses[course.name].append((paper, summary))
        return dict(page="course", courses=courses)
        