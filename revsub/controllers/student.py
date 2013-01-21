# -*- coding: utf-8 -*-
from tg import expose, flash, redirect, require, request
from tg.i18n import ugettext as _, lazy_ugettext as l_
from tg.predicates import has_permission

from revsub.lib.base import BaseController
from revsub.model import DeclarativeBase, metadata, DBSession, Group, User, Course, Paper, PaperSummary


__all__ = ['StudentController']

class StudentController(BaseController):
    
    # The predicate that must be met for all the actions in this controller:
    allow_only = has_permission('instructor')
    
    def _get_courses_taught(self, user):
        return DBSession.query(Course)\
                        .join(Course.instructors)\
                        .join(Group.users)\
                        .filter(User.id == user.id).all()
    
    @expose('revsub.templates.viewstudent')
    def view(self, student_id):
        login = request.environ.get('repoze.who.identity').get('repoze.who.userid')
        l_user = DBSession.query(User).filter(User.user_name == login).one()
        user = DBSession.query(User).filter(User.id == int(student_id)).first()
        if not user:
            redirect('/error', params=dict(msg="invalid user"))
        courses_results = {}
        courses_taught = self._get_courses_taught(l_user)
        sql_s = """
            SELECT p.id as paper_id_p, u.*, s.id as summary_id, s.*, p.*, z.avg_rating
            FROM users u 
                JOIN user_group ug on u.id = ug.user_id
                JOIN groups g on ug.group_id = g.id
                JOIN courses c on c.students_id = g.id
                JOIN papers p on c.id = p.course_id
                LEFT JOIN paper_summaries s ON s.paper_id = p.id
                LEFT JOIN (SELECT s.id, avg(r.rating) as avg_rating 
                    FROM paper_summaries s
                    JOIN summary_reviews r on s.id = r.summary_id
                    WHERE s.student_id = :user_id
                    GROUP BY s.id
                ) z on s.id = z.id
                WHERE u.id = :user_id and c.id = :course_id and (s.student_id =:user_id or s.student_id is null)"""
        for course in courses_taught:
            summaries = DBSession.execute(sql_s, 
                            dict(course_id=course.id, 
                                    user_id=user.id)).fetchall()
            courses_results[course] = summaries
        return dict(page="viewstudent", student=user,
                        courses=courses_results)
