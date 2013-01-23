# -*- coding: utf-8 -*-
from tg import expose, flash, redirect, require, request
from tg.i18n import ugettext as _, lazy_ugettext as l_
from tg.predicates import has_permission

from revsub.lib.base import BaseController
from revsub.model import DeclarativeBase, metadata, DBSession, \
                Group, User, Course, Paper, PaperSummary


__all__ = ['PaperController']

class PaperController(BaseController):

    allow_only = has_permission('instructor')
    
    def _can_view_paper(self, user, paper):
        return user in paper.course.instructors.users
    
    @expose('revsub.templates.viewpaper') 
    def view(self, paper_id):
        login = request.environ.get('repoze.who.identity')\
                        .get('repoze.who.userid')
        user = DBSession.query(User)\
                .filter(User.user_name == login).one()
        paper = DBSession.query(Paper)\
                .filter(Paper.id == int(paper_id)).first()
        if not paper:
            redirect('/error',
                    params=dict(msg="invalid paper"))
        if not self._can_view_paper(user, paper):
            redirect('/error',
                    params=dict(msg="invalid permissions to view paper"))
        # submissions and their avg ratings
        sql_s = """
            SELECT u.id as user_id, u.*, s.id as summary_id, s.*, z.avg_rating
            FROM users u 
                JOIN user_group ug on u.id = ug.user_id
                JOIN groups g on ug.group_id = g.id
                JOIN courses c on c.students_id = g.id
                JOIN papers p on c.id = p.course_id
                LEFT JOIN paper_summaries s ON s.paper_id = p.id and s.student_id = u.id
                LEFT JOIN (SELECT s.id, avg((r.rating + r.insight_rating)/2) as avg_rating 
                    FROM paper_summaries s
                    JOIN summary_reviews r on s.id = r.summary_id
                    WHERE s.paper_id = :paper_id
                    GROUP BY s.id
                ) z on s.id = z.id
                WHERE p.id = :paper_id"""
        summaries = DBSession.execute(sql_s, dict(paper_id=paper_id)).fetchall()
        return dict(page="viewpaper", paper=paper, summaries=summaries)
               
