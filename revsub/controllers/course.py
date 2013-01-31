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
            papers = DBSession.execute("""SELECT s.id as summary_id, s.*, p.*, p.paper_id as p_paper_id, z.avg_rating,
                z.num_reviews as num_reviews
            FROM papers p LEFT JOIN (
                    SELECT id, paper_id from paper_summaries WHERE student_id = :user_id) s ON p.id = s.paper_id
            LEFT JOIN (
                SELECT s2.id as id, round(avg((r.rating+r.insight_rating)/2),2) as avg_rating,
                    count(r.id) as num_reviews
                FROM paper_summaries s2 JOIN summary_reviews r
                ON s2.id = r.summary_id
                GROUP BY s2.id
            ) z on s.id = z.id WHERE p.course_id = :course_id""",
                            dict(user_id=user.id, course_id = course.id)).fetchall()
            courses_e[course] = papers
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