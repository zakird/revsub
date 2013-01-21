# -*- coding: utf-8 -*-
"""Setup the revsub application"""

import logging
from tg import config
from revsub import model
import transaction

def bootstrap(command, conf, vars):
    """Place any commands to setup revsub here"""

    # <websetup.bootstrap.before.auth
    from sqlalchemy.exc import IntegrityError
    try:
        zakir = model.User()
        zakir.user_name = u'zakir'
        zakir.display_name = u'Zakir Durumeric'
        zakir.email_address = u'zakir@umich.edu'
        zakir.password = u'cisco123'
        model.DBSession.add(zakir)
        
        alex = model.User()
        alex.user_name = u'jhalderm'
        alex.display_name = u'J. Alex Halderman'
        alex.email_address = u'jhalderm@umich.edu'
        alex.password = u'cisco123'
        model.DBSession.add(alex)
        
        peter = model.User()
        peter.user_name = u'honey'
        peter.display_name = u'Peter Honeyman'
        peter.email_address = u'peter@umich.edu'
        peter.password = u'cisco123'
        model.DBSession.add(peter)
        
        pat = model.User()
        pat.user_name = u'ppannuto'
        pat.display_name = u'Pat Pannuto'
        pat.email_address = u'ppannuto@umich.edu'
        pat.password = u'cisco123'
        model.DBSession.add(pat)
        
        brad = model.User()
        brad.user_name = u'bradjc'
        brad.display_name = u'Brad Campbell'
        brad.email_address = u'bradjc@umich.edu'
        brad.password = u'cisco123'
        model.DBSession.add(brad)
        
        meghan = model.User()
        meghan.user_name = u'mclarkk'
        meghan.display_name = u"Meghan Clark"
        meghan.email_address = u'mclarkk@umich.edu'
        meghan.password = u'cisco123'
        model.DBSession.add(meghan)
        
        jenny = model.User()
        jenny.user_name = u'oneilj'
        jenny.display_name = u"Jenny O'Neil"
        jenny.email_address = u'oneilj@umich.edu'
        jenny.password = u'cisco123'

        model.DBSession.add(jenny)
        
        g = model.Group()
        g.group_name = u'managers'
        g.display_name = u'Administrators'
        g.users.append(zakir)
        g.users.append(alex)
        model.DBSession.add(g)
        
        g1 = model.Group()
        g1.group_name = u'eecs588w13_instructors'
        g1.display_name = u'EECS588 Winter 2013 Instructors'
        g1.users.append(zakir)
        g1.users.append(alex)
        model.DBSession.add(g1)
        
        g3 = model.Group()
        g3.group_name = u'eecs588w13_students'
        g3.display_name = u'EECS588 Winter 2013 Students'
        g3.users.append(pat)
        g3.users.append(meghan)
        g3.users.append(jenny)
        g3.users.append(brad)
        model.DBSession.add(g3)
        
        g2 = model.Group()
        g2.group_name = u'eecs589w13_instructors'
        g2.display_name = u'EECS589 Winter 2013 Instructors'
        g2.users.append(peter)
        model.DBSession.add(g2)
    
        g4 = model.Group()
        g4.group_name = u'eecs589w13_students'
        g4.display_name = u'EECS589 Winter 2013 Students'
        g4.users.append(zakir)
        g4.users.append(pat)
        model.DBSession.add(g2)
    
        p = model.Permission()
        p.permission_name = u'instructor'
        p.description = u'Instructor of any course'
        p.groups.append(g1)
        p.groups.append(g2)
        model.DBSession.add(p)
        
        p2 = model.Permission()
        p2.permission_name = u'student'
        p2.description = u'Student of any course'
        p2.groups.append(g3)
        p2.groups.append(g4)
        model.DBSession.add(p2)
    
        c = model.Course()
        c.name = "EECS588 Winter 2013"
        c.students = g3
        c.is_active = True
        c.instructors = g1
        model.DBSession.add(c)
        
        c1 = model.Course()
        c1.name = "EECS589 Winter 2013"
        c1.students = g4
        c1.is_active = True
        c1.instructors = g2
        model.DBSession.add(c1)
    
        model.DBSession.flush()
        transaction.commit()
    except IntegrityError:
        print 'Warning, there was a problem adding your auth data, it may have already been added:'
        import traceback
        print traceback.format_exc()
        transaction.abort()
        print 'Continuing with bootstrapping...'

    # <websetup.bootstrap.after.auth>
