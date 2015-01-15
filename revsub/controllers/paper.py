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
                LEFT JOIN (SELECT s.id, round(avg((r.rating + r.insight_rating)/2),2) as avg_rating 
                    FROM paper_summaries s
                    JOIN summary_reviews r on s.id = r.summary_id
                    WHERE s.paper_id = :paper_id AND r.status = 'complete'
                    GROUP BY s.id
                ) z on s.id = z.id
                WHERE p.id = :paper_id"""
        summaries = DBSession.execute(sql_s, dict(paper_id=paper_id)).fetchall()
        return dict(page="viewpaper", paper=paper, summaries=summaries)

    @expose('revsub.templates.editpaper') 
    def new(self, course_id):
        login = request.environ.get('repoze.who.identity')\
                        .get('repoze.who.userid')
        user = DBSession.query(User)\
                        .filter(User.user_name == login).one()
        course = DBSession.query(Course).filter(Course.id == int(course_id)).one()
        if user not in course.instructors.users:
            redirect('/error', params=dict(msg="invalid permissions to view course"))
        return dict(page="createpaper", course=course, paper=None)

    @expose('revsub.templates.editpaper') 
    def edit(self, paper_id):
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
        return dict(page="editpaper", paper=paper, course=paper.course)

    @expose()
    def save(self, paper_id, title, downloadurl, abstract, course_id, duedate):
        login = request.environ.get('repoze.who.identity')\
                        .get('repoze.who.userid')
        user = DBSession.query(User)\
                        .filter(User.user_name == login).one()
        course = DBSession.query(Course).filter(Course.id == int(course_id)).one()

        if paper_id != '':
       	    paper = DBSession.query(Paper)\
                        .filter(Paper.id == int(paper_id)).first()
            if not paper:
                redirect('/error',
                        params=dict(msg="invalid paper"))
            if not self._can_view_paper(user, paper):
                redirect('/error',
                        params=dict(msg="invalid permissions to view paper"))
            paper.name = str(title)
            paper.download_url = str(downloadurl)
            paper.abstract = str(abstract)
            paper.due_date = duedate
        else:
            paper = Paper()
            punctuation = { 0x2018:0x27, 0x2019:0x27, 0x201C:0x22, 0x201D:0x22 }
            paper.name = title.translate(punctuation).encode('ascii', 'replace')
            paper.download_url = downloadurl
            paper.abstract = abstract.encode('ascii', 'replace')
            paper.created_by = user.id
            paper.due_date = duedate

            paper.course_id = course_id
            DBSession.add(paper)
            DBSession.flush()
        redirect('/paper/view?paper_id=%i' % paper.id)
 
