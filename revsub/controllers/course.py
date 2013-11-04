# -*- coding: utf-8 -*-
from tg import expose, flash, redirect, require, request
from tg.i18n import ugettext as _, lazy_ugettext as l_
from tg.predicates import has_permission, Any, is_user 
from sqlalchemy import or_
from revsub.lib.base import BaseController
from revsub.model import DeclarativeBase, metadata, DBSession, Group, User, Course, Paper, PaperSummary, SummaryReview


__all__ = ['CourseController']

import math

class StdDevCalculator(object):
    def __init__(self, x, skip_zero=False):
        if skip_zero:
            x = filter(lambda x: x != 0, x)
        n, mean, std = len(filter(lambda x: x is not None, x)), float(0), float(0)
        for a in x:
            if a is None:
                continue
            if skip_zero and a == 0:
                continue
            a = float(a)
            mean += a
        mean = float(mean) / float(n)
        for a in x:
            if a is None:
                continue
            if skip_zero and a == 0:
                continue

            a = float(a)
            std = std + (a - mean)**2
        std = math.sqrt(float(std) / float(n-1))
        self.mean = mean
        self.stddev = std
        
    def get_stddev(self, value):
        if value is None:
            return None
        value = float(value)
        x =  math.ceil(float(abs(value - self.mean)) / self.stddev)
        return x if value > self.mean else (0 - x)

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
            papers = DBSession.execute("""SELECT s.id as summary_id, s.*, p.*, p.id as p_paper_id, z.avg_rating,
                z.num_reviews as num_reviews
            FROM papers p LEFT JOIN (
                    SELECT id, paper_id from paper_summaries WHERE student_id = :user_id) s ON p.id = s.paper_id
            LEFT JOIN (
                SELECT s2.id as id, round(avg((r.rating+r.insight_rating)/2),2) as avg_rating,
                    count(r.id) as num_reviews
                FROM paper_summaries s2 JOIN summary_reviews r
                ON s2.id = r.summary_id
                WHERE r.status = 'complete'
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
        students = DBSession.execute("SELECT * FROM enrolled_students_overview where course_id = :course_id order by display_name", dict(course_id=course.id)).fetchall()

        s_avg_rating = StdDevCalculator(map(lambda x: x.avg_rating, students), True)
        s_avg_reading = StdDevCalculator(map(lambda x: x.avg_reading, students), True)
        s_avg_insight = StdDevCalculator(map(lambda x: x.avg_insight, students), True)
        s_avg_nz_rating = StdDevCalculator(map(lambda x: x.avg_nonzero_rating, students))
        s_avg_nz_reading = StdDevCalculator(map(lambda x: x.avg_nonzero_reading, students))
        s_avg_nz_insight = StdDevCalculator(map(lambda x: x.avg_nonzero_insight, students))
        s_avg_submitted = StdDevCalculator(map(lambda x: x.submitted_papers, students), True)

        instructors = course.instructors.users
        reviews = DBSession.query(SummaryReview, User, Paper)\
                .join(SummaryReview.summary).join(PaperSummary.student)\
                .join(PaperSummary.paper)\
                .filter(SummaryReview.comments != '').all()
        sql_s = """select * from (select user_id, display_name, avg(av) as avg_, variance(av) as var_, avg(length(comments)) as avg_len, count(distinct comments)-1 num_nonnull from (
select sr.comments, sr.id, u.id as user_id, u.display_name, u.user_name, (rating+insight_rating)/2 as av 
from summary_reviews sr join paper_summaries ps on sr.summary_id = ps.id 
join papers p on ps.paper_id = p.id join users u on sr.creator_id = u.id
where course_id = :course_id) z group by user_id, display_name) a left join
(select creator_id, avg(diff) as avg_diff from (select creator_id, avg_rating, (insight_rating+rating)/2, abs(avg_rating-(insight_rating+rating)/2) as diff
 from graded_paper_summaries gps join summary_reviews sr on gps.summary_id = sr.summary_id join papers p on p.id = gps.paper_id
 where p.course_id = :course_id and  status = 'complete') z group by creator_id) z 
on a.user_id = z.creator_id;"""
        feedback = DBSession.execute(sql_s, dict(course_id = course.id)).fetchall()
        s_f_avg = StdDevCalculator(map(lambda x: x.avg_, feedback))
        s_f_var = StdDevCalculator(map(lambda x: x.var_, feedback))
        s_f_avglen = StdDevCalculator(map(lambda x: x.avg_len, feedback))
        s_f_nonnull = StdDevCalculator(map(lambda x: x.num_nonnull, feedback))
        s_f_distavg = StdDevCalculator(map(lambda x: x.avg_diff, feedback))
        return dict(page="course",course=course, students=students, feedback=feedback,
                        instructors=instructors, papers=papers, reviews=reviews,
                        s_f_avg=s_f_avg, s_f_var=s_f_var, s_f_avglen=s_f_avglen,
                        s_f_nonnull=s_f_nonnull, s_f_distavg=s_f_distavg,
                        s_avg_rating=s_avg_rating, s_avg_reading=s_avg_reading, s_avg_insight=s_avg_insight,
                        s_avg_nz_rating = s_avg_nz_rating, s_avg_nz_reading=s_avg_nz_reading, s_avg_nz_insight=s_avg_nz_insight,
                        s_avg_submitted=s_avg_submitted
        )

    def get_cdf(self, course_id, name):
        raw = DBSession.execute("select %s, count(user_id) as count from enrolled_students_overview where %s > 0 and course_id = :course_id group by %s order by %s" % (name, name, name, name), dict(course_id=course_id)).fetchall()
        total = sum(map(lambda raw: getattr(raw, "count"), raw))
        total_so_far = 0
        cdf = []
        for r in raw:
          total_so_far = total_so_far + r.count
          cdf.append(dict(x=getattr(r, name), y=float(total_so_far)/float(total), size=5))
        return cdf

    @expose('json')
    def score_cdf(self, course_id):
        login = request.environ.get('repoze.who.identity').get('repoze.who.userid')
        user = DBSession.query(User).filter(User.user_name == login).one()
        course = DBSession.query(Course).filter(Course.id == int(course_id)).first()
        if not course:
            redirect('/error', params=dict(msg="invalid course"))
        if not self._check_instructor_for_course(user, course):
            redirect('/error', params=dict(msg="user is not an instructor for course"))
        d = [
          {'key':'Avg', 'values':self.get_cdf(course.id, 'avg_rating')},
          {'key':'Reading', 'values':self.get_cdf(course.id, 'avg_reading')},
          {'key':'Insight', 'values':self.get_cdf(course.id, 'avg_insight')},
          {'key':'NZAvg', 'values':self.get_cdf(course.id, 'avg_nonzero_rating')},
          {'key':'NZRead', 'values':self.get_cdf(course.id, 'avg_nonzero_reading')},
          {'key':'NZInght', 'values':self.get_cdf(course.id, 'avg_nonzero_insight')},

        ]
        return dict(r=d)

    def cdf_user_course_given(self, course_id, user_id):
        sql_s = """select av, count(id) as count from (
select sr.id, u.id as user_id, u.display_name, u.user_name, (rating+insight_rating)/2 as av from summary_reviews sr join paper_summaries ps on sr.summary_id = ps.id 
join papers p on ps.paper_id = p.id join users u on sr.creator_id = u.id
where course_id = :course_id and sr.creator_id = :user_id) z group by av order by av;"""
        raw = DBSession.execute(sql_s, dict(course_id=course_id, user_id=user_id)).fetchall()
        total = sum(map(lambda raw: getattr(raw, "count"), raw))
        total_so_far = 0
        cdf = []
        for r in raw:
          total_so_far = total_so_far + r.count
          cdf.append(dict(x=getattr(r, "av"), y=float(total_so_far)/float(total)))
        return cdf

    @expose('json')
    def scores_given_cdf(self, course_id):
        login = request.environ.get('repoze.who.identity').get('repoze.who.userid')
        user = DBSession.query(User).filter(User.user_name == login).one()
        course = DBSession.query(Course).filter(Course.id == int(course_id)).first()
        if not course:
            redirect('/error', params=dict(msg="invalid course"))
        if not self._check_instructor_for_course(user, course):
            redirect('/error', params=dict(msg="user is not an instructor for course"))
        d = []
        i = 0
        for student in course.students.users:
            d.append(dict(key=student.display_name, values=self.cdf_user_course_given(course.id, student.id)))
            i += 1
            if i > 9:
                break
        return dict(r=d) 
