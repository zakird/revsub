# -*- coding: utf-8 -*-
from tg import expose, flash, redirect, require, request
from tg.i18n import ugettext as _, lazy_ugettext as l_
from tg.predicates import has_permission, Any, is_user 
from sqlalchemy import or_
from revsub.lib.base import BaseController
from revsub.model import DeclarativeBase, metadata, DBSession, Group, User, Course, Paper, PaperSummary


__all__ = ['CourseController']

class CourseController(BaseController):
    
    # The predicate that must be met for all the actions in this controller:
    allow_only = Any(has_permission('student'), has_permission('instructor'))
    
    @expose('revsub.templates.courses')
    def index(self):
        login = request.environ.get('repoze.who.identity')\
                        .get('repoze.who.userid')
        user = DBSession.query(User).filter(User.user_name == login).one()
        courses_e = {}
        for course in user.courses_enrolled_in:
            courses_e[course] = []
            for paper, summary in DBSession.query(Paper, PaperSummary)\
                            .outerjoin(PaperSummary)\
                            .filter(or_(PaperSummary.student_id == user.id,PaperSummary.student_id == None))\
                            .filter(Paper.course_id == course.id).all():
                courses_e[course].append((paper, summary))
        return dict(page="course", courses_enrolled=courses_e,
                        courses_taught=user.courses_taught)
        
    def _check_instructor_for_course(self, user, course):
        return user in course.instructors.users
        
    @require(has_permission('instructor'))
    @expose('revsub.templates.viewcourse')
    def view(self, course_id):
        login = request.environ.get('repoze.who.identity').get('repoze.who.userid')
        user = DBSession.query(User).filter(User.user_name == login).one()
        course = DBSession.query(Course).filter(Course.id == int(course_id)).first()
        if not course:
            redirect('/error', params=dict(msg="invalid course"))
        if not self._check_instructor_for_course(user, course):
            redirect('/error', params=dict(msg="user is not an instructor for course"))
        papers = course.papers
        students = course.students.users
        instructors = course.instructors.users
        return dict(page="course",course=course, students=students,
                        instructors=instructors, papers=papers)