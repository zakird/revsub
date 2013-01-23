# -*- coding: utf-8 -*-
import os
import sys
from datetime import datetime
from hashlib import sha256

from sqlalchemy import Table, ForeignKey, Column
from sqlalchemy.types import Unicode, Integer, DateTime
from sqlalchemy.orm import relation, synonym, column_property

from revsub.model import DeclarativeBase, metadata, DBSession

__all__ = ['User', 'Group', 'Permission']

group_permission_table = Table('group_permission', metadata,
    Column('group_id', Integer, ForeignKey('groups.id',
        onupdate="CASCADE", ondelete="CASCADE"), primary_key=True),
    Column('permission_id', Integer, ForeignKey('permissions.id',
        onupdate="CASCADE", ondelete="CASCADE"), primary_key=True)
)

user_group_table = Table('user_group', metadata,
    Column('user_id', Integer, ForeignKey('users.id',
        onupdate="CASCADE", ondelete="CASCADE"), primary_key=True),
    Column('group_id', Integer, ForeignKey('groups.id',
        onupdate="CASCADE", ondelete="CASCADE"), primary_key=True)
)


class Group(DeclarativeBase):
    __tablename__ = 'groups'

    id = Column(Integer, autoincrement=True, primary_key=True)
    group_id = synonym("id", map_column=True)
    group_name = Column(Unicode(16), unique=True, nullable=False)
    display_name = Column(Unicode(255))
    created = Column(DateTime, default=datetime.now)
    users = relation('User', secondary=user_group_table, backref='groups')

    def __repr__(self):
        return ('<Group: name=%s>' % self.group_name).encode('utf-8')

    def __unicode__(self):
        return self.group_name


class User(DeclarativeBase):
    __tablename__ = 'users'

    id = Column(Integer, autoincrement=True, primary_key=True)
    user_name = Column(Unicode(16), unique=True, nullable=False)
    email_address = Column(Unicode(255), unique=True, nullable=False)
    display_name = Column(Unicode(255))
    _password = Column('password', Unicode(128))
    created = Column(DateTime, default=datetime.now)
    
    def __repr__(self):
        return ('<User: name=%s, email=%s, display=%s>' % (
                self.user_name, self.email_address, self.display_name)).encode('utf-8')

    def __unicode__(self):
        return self.display_name or self.user_name

    @property
    def permissions(self):
        """Return a set with all permissions granted to the user."""
        perms = set()
        for g in self.groups:
            perms = perms | set(g.permissions)
        return perms

    @classmethod
    def by_email_address(cls, email):
        """Return the user object whose email address is ``email``."""
        return DBSession.query(cls).filter_by(email_address=email).first()

    @classmethod
    def by_user_name(cls, username):
        """Return the user object whose user name is ``username``."""
        return DBSession.query(cls).filter_by(user_name=username).first()

    @classmethod
    def _hash_password(cls, password):
        # Make sure password is a str because we cannot hash unicode objects
        if isinstance(password, unicode):
            password = password.encode('utf-8')
        salt = sha256()
        salt.update(os.urandom(60))
        hash = sha256()
        hash.update(password + salt.hexdigest())
        password = salt.hexdigest() + hash.hexdigest()
        # Make sure the hashed password is a unicode object at the end of the
        # process because SQLAlchemy _wants_ unicode objects for Unicode cols
        if not isinstance(password, unicode):
            password = password.decode('utf-8')
        return password

    def _set_password(self, password):
        """Hash ``password`` on the fly and store its hashed version."""
        self._password = self._hash_password(password)

    def _get_password(self):
        """Return the hashed version of the password."""
        return self._password

    password = synonym('_password', descriptor=property(_get_password,
                                                        _set_password))

    def validate_password(self, password):
        hash = sha256()
        if isinstance(password, unicode):
            password = password.encode('utf-8')
        hash.update(password + str(self.password[:64]))
        return self.password[64:] == hash.hexdigest()


class Permission(DeclarativeBase):
    __tablename__ = 'permissions'

    id = Column(Integer, autoincrement=True, primary_key=True)
    permission_name = Column(Unicode(63), unique=True, nullable=False)
    description = Column(Unicode(255))

    groups = relation(Group, secondary=group_permission_table,
                      backref='permissions')

    def __repr__(self):
        return ('<Permission: name=%s>' % self.permission_name).encode('utf-8')

    def __unicode__(self):
        return self.permission_name
