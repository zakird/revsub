# -*- coding: utf-8 -*-
"""Main Controller"""

from tg import expose, flash, require, url, lurl, request, redirect, tmpl_context
from tg.predicates import has_permission, Any, is_user, not_anonymous
from tg.i18n import ugettext as _, lazy_ugettext as l_
from tg import predicates
from revsub import model
from revsub.model import DBSession, metadata, User
from tgext.admin.tgadminconfig import TGAdminConfig
from tgext.admin.controller import AdminController

from revsub.lib.base import BaseController
from revsub.controllers.error import ErrorController
from revsub.controllers.course import CourseController
from revsub.controllers.summary import SummaryController
from revsub.controllers.paper import PaperController
from revsub.controllers.student import StudentController

__all__ = ['RootController']

class RootController(BaseController):

    admin = AdminController(model, DBSession, config_type=TGAdminConfig)
    course = CourseController()
    error = ErrorController()
    summary = SummaryController()
    paper = PaperController()
    student = StudentController()

    def _before(self, *args, **kw):
        tmpl_context.project_name = "revsub"
        tmpl_context.version = "1.1.0"

    @expose('revsub.templates.index')
    def index(self, came_from=lurl('/courses')):
        login_counter = request.environ.get('repoze.who.logins', 0)
        if login_counter > 0:
            flash(_('Error! Invalid username or password.'), 'warning')
        return dict(page='index', login_counter=str(login_counter),
                    came_from=came_from)

    login = index

    @require(not_anonymous())
    @expose('revsub.templates.myaccount')
    def account(self):
        login = request.environ.get('repoze.who.identity')\
            .get('repoze.who.userid')
        user = DBSession.query(User).filter(User.user_name == login).one() 
        return dict(user=user)

    @expose()
    def _reset_password(self, password1, password2, old_password):
        if password1 != password2:
            redirect("/error")
        if len(password1) > 256 or len(password1) < 6:
            redirect("/error")
        login = request.environ.get('repoze.who.identity')\
            .get('repoze.who.userid')
        user = DBSession.query(User).filter(User.user_name == login).one()
        if not user.validate_password(old_password):
            flash(_('Error! Incorrect original password.'), 'warning')
            redirect('/account')
        user.password = password1
        redirect('/account')

    @expose()
    def post_login(self, came_from=lurl('/')):
        """
        Redirect the user to the initially requested page on successful
        authentication or redirect her back to the login page if login failed.

        """
        if not request.identity:
            login_counter = request.environ.get('repoze.who.logins', 0) + 1
            redirect('/index',
                params=dict(came_from=came_from, __logins=login_counter))
        redirect("/course")

    @expose()
    def post_logout(self, came_from=lurl('/')):
        redirect("/")
