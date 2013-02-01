# -*- coding: utf-8 -*-
import hmac
from tg import expose, flash, redirect, require, request
from tg.i18n import ugettext as _, lazy_ugettext as l_
from tg.predicates import has_permission, Any, is_user 

from revsub.lib.base import BaseController
from revsub.model import DeclarativeBase, metadata, DBSession,\
                Group, User, Course, Paper, PaperSummary, StudentSummaryReview


__all__ = ['SummaryController']

class SummaryController(BaseController):
    SECRET = "NtnAwmAKfLeL5vQnYdzzpdXMCJtzKHnRe3fttCzLKFmx4dJBYboZ752Ganc2EFx7"

    allow_only = Any(has_permission('student'), has_permission('instructor'))
    
    def _generate_peer_review_hmac(self, user, summary):
        h = hmac.new(self.SECRET)
        h.update(str(user.id))
        h.update(str(summary.id))
        return h.hexdigest()
        
    def _check_peer_review_hmac(self, user, summary, hmac):
        return self._generate_peer_review_hmac(user, summary) == hmac
    
    def _check_valid_paper(self, paper_id):
        return DBSession.query(Paper).filter(Paper.id == paper_id).first()
    
    def _check_eligible_submit(self, user, paper):
        return bool(DBSession.query(User).join(User.groups)\
                .join(Group.courses_enrolled_in)\
                .join(Course.papers).filter(Paper.id == paper.id)\
                .filter(User.id == user.id).first())
                
    def _check_user_submitted_paper(self, user, paper):
        return bool(DBSession.query(PaperSummary)\
                        .filter(PaperSummary.student_id == user.id)\
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
        sql_s = """select s.*, s.id as summary_id, count from paper_summaries s join 
        (select s.id, count(r.id) as count from paper_summaries s
        LEFT JOIN summary_reviews r on s.id = r.summary_id
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
        hmacs = {}
        for s in summaries_to_review:
            hmacs[s.id] = self._generate_peer_review_hmac(user, s)
        return dict(page="newreview", paper=paper, peer_review=summaries_to_review,
                        hmacs=hmacs)
    
    @expose()
    def _create(self, paper_id, summary, **kwargs):
        login = request.environ.get('repoze.who.identity').get('repoze.who.userid')
        user = DBSession.query(User).filter(User.user_name == login).one()
        paper = self._check_valid_paper(int(paper_id))
        if not paper:
            redirect('/error', params=dict(msg="invalid paper supplied"))
         # does this user have access to this paper?
        if not self._check_eligible_submit(user, paper):
            redirect('/error', params=dict(
                            msg="user does not have access to submit paper"))        
        if self._check_user_submitted_paper(user, paper):
            redirect('/error', params=dict(
                            msg="user already submitted summary for this paper"))
        
        # add summary
        summary_ = PaperSummary(paper, user, summary)      
        DBSession.add(summary_)           
            
        if kwargs:
            # we know that we have some summary reviews to grade
            # figure out how which summaries have been reviewed
            s = set()
            for arg in kwargs:
                name, val = arg.split("_")
                s.add(val)
            for summary_id in s:
                summary = DBSession.query(PaperSummary).filter(PaperSummary.id == summary_id).first()
                if not summary:
                    redirect('/error', params=dict(msg="invalid summary id received"))
                k_hmac = "_".join([summary_id,"hmac"])
                if k_hmac not in kwargs:
                    redirect('/error', params=dict(msg="incomplete requested received"))
                hmac = kwargs[k_hmac]
                if not self._check_peer_review_hmac(user, summary, str(hmac)):
                    redirect('/error', params=dict(msg="invalid peer hmac received"))
                k_rating_reading = "_".join(["reading", summary_id])
                if k_rating_reading not in kwargs:
                    redirect('/error', params=dict(msg="incomplete requested received"))
                rating_reading = int(kwargs[k_rating_reading])
                if rating_reading > 3 or rating_reading < 0:
                    redirect('/error', params=dict(msg="invalid value for reading rating"))
                k_rating_critique = "_".join(["critique", summary_id])  
                if k_rating_critique not in kwargs:
                    redirect('/error', params=dict(msg="incomplete requested received"))
                rating_critique = int(kwargs[k_rating_critique])
                if rating_critique > 3 or rating_critique < 0:
                    redirect('/error', params=dict(msg="invalid value for critique rating"))
                k_comments = "_".join([summary_id,"comments"])
                if k_comments not in kwargs:
                    redirect('/error', params=dict(msg="incomplete requested received"))
                comments = str(kwargs[k_comments])
                
                response = StudentSummaryReview(
                                summary = summary,
                                reading_rating = rating_reading,
                                insight_rating = rating_critique,
                                comments = comments,
                                creator = user
                )
                DBSession.add(response)
        redirect("/course")
                                
    @expose('revsub.templates.mysummaries') 
    def index(self):
        login = request.environ.get('repoze.who.identity').get('repoze.who.userid')
        user = DBSession.query(User).filter(User.user_name == login).one()
        summaries = DBSession.execute("""
            SELECT s.id as summary_id, s.*, p.*, z.avg_rating,
                z.num_reviews as num_reviews
            FROM papers p join paper_summaries s on p.id = s.paper_id
            LEFT JOIN (
                SELECT s.id as id, round(avg((r.rating+r.insight_rating)/2),2) as avg_rating,
                    count(r.id) as num_reviews
                FROM paper_summaries s JOIN summary_reviews r
                ON s.id = r.summary_id
                GROUP BY s.id
            ) z on s.id = z.id WHERE s.student_id = :user_id""", dict(user_id=user.id))
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
               
        
