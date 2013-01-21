# -*- coding: utf-8 -*-
from tg import expose, flash, redirect, require, request
from tg.i18n import ugettext as _, lazy_ugettext as l_
from tg.predicates import has_permission, Any, is_user 

from revsub.lib.base import BaseController
from revsub.model import DeclarativeBase, metadata, DBSession, Group, User, Course, Paper, PaperSummary


__all__ = ['SummaryController']

class SummaryController(BaseController):

    allow_only = Any(has_permission('student'), has_permission('instructor'))
    
    def _generate_peer_review_hmac(self, user, paper):
        return None
        
    def _check_peer_review_hmac(self, user, paper, hmac):
        return True
    
    def _check_valid_paper(self, paper_id):
        return DBSession.query(Paper).filter(Paper.id == paper_id).first()
    
    def _check_eligible_submit(self, user, paper):
        return bool(DBSession.query(User).join(User.groups)\
                .join(Group.courses_enrolled_in)\
                .join(Course.papers).filter(Paper.id == paper.id)\
                .filter(User.id == user.id).first())
                
    def _check_user_submitted_paper(self, user, paper):
        return bool(DBSession.query(PaperSummary)\
                        .filter(PaperSummary.student_id == User.id)\
                        .filter(PaperSummary.paper_id == paper.id).first())
                
    def _get_summaries_to_peer_review(self, user, num_summaries=2):
        # restrictions we want:
        #   1. Already submitted review for the paper
        #   2. Did not write summary themselves
        #
        # orderings we want
        #   1. papers with the least number of reviews
        #
        # because we're doing a join back to themselves... sqlalchemy
        # is going to be obnoxious, so let's just write some sql ourselves
        sql_s = """select s.*, count from paper_summaries s join 
        (select s.id, count(r.id) as count from paper_summaries s
        JOIN summary_reviews r on s.id = r.summary_id
        where s.paper_id in (select paper_id
            FROM paper_summaries WHERE student_id = :user_id)
        AND s.student_id <> :user_id
        GROUP BY s.id ORDER BY count(r.id) DESC LIMIT %i) z ON
        s.id = z.id""" % num_summaries
        return DBSession.query(PaperSummary)\
                        .from_statement(sql_s).params(user_id=user.id).all()
    
    @expose('revsub.templates.newreview')
    def create(self, paper_id):
        login = request.environ.get('repoze.who.identity').get('repoze.who.userid')
        user = DBSession.query(User).filter(User.user_name == login).one()
        
        # does this paper even exist?
        paper = self._check_valid_paper(int(paper_id))
        if not paper:
            redirect('/error', params=dict(msg="invalid paper supplied"))
         # does this user have access to this paper?
        if not self._check_eligible_submit(user, paper):
            redirect('/error', params=dict(
                            msg="user does not have access to paper"))
        # has this user already submitted this paper?
        if self._check_user_submitted_paper(user, paper):
            redirect('/error', params=dict(
                            msg="user already submitted summary for this paper"))
        summaries_to_review = self._get_summaries_to_peer_review(user)
        return dict(page="newreview", paper=paper, peer_review=summaries_to_review)
        
    @expose()
        
       
    @expose('revsub.templates.mysummaries') 
    def index(self):
        login = request.environ.get('repoze.who.identity').get('repoze.who.userid')
        user = DBSession.query(User).filter(User.user_name == login).one()
        summaries = DBSession.execute("""
            SELECT s.id as summary_id, s.*, p.*, z.avg_rating,
                z.num_reviews as num_reviews
            FROM papers p join paper_summaries s on p.id = s.paper_id
            LEFT JOIN (
                SELECT s.id as id, avg(r.rating) as avg_rating,
                    count(r.id) as num_reviews
                FROM paper_summaries s JOIN summary_reviews r
                ON s.id = r.summary_id
                GROUP BY s.id
            ) z on s.id = z.id""")
        return dict(page="summaries", summaries=summaries)
        
    def _can_view_summary(self, summary, user):
        if summary.student == user:
            return True
        elif user in summary.paper.course.instructors.users:
            return True
        return False
        
    @expose('revsub.templates.viewsummary') 
    def view(self, summary_id):
        login = request.environ.get('repoze.who.identity').get('repoze.who.userid')
        user = DBSession.query(User).filter(User.user_name == login).one()
        summary = DBSession.query(PaperSummary).filter(PaperSummary.id == int(summary_id)).first()
        if not summary:
            redirect('/error', params=dict(msg="invalid paper summary"))
        if not self._can_view_summary(summary, user):
            redirect('/error', params=dict(msg="invalid permissions to view summary"))
        paper = summary.paper
        return dict(page="viewreview", paper=paper, summary=summary)
               
        