from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Index, Integer, String, Table, text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from database import Base


class Role(Base):
    __tablename__ = 'roles'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(30), unique=True, nullable=False)


# relationship table many-to-many
user_roles = Table(
    'user_roles',
    Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id', ondelete='CASCADE'), primary_key=True),
    Column('role_id', Integer, ForeignKey('roles.id', ondelete='CASCADE'), primary_key=True),
)


class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, index=True, nullable=False)
    password = Column(String, nullable=False)
    first_name = Column(String(30), nullable=True)
    last_name = Column(String(30), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)
    last_activity_at = Column(DateTime(timezone=True), server_default=func.now())
    balance = Column(Integer, default=0)
    block_status = Column(Boolean, default=False)
    is_superuser = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True, nullable=False)

    __table_args__ = (
        Index(
            'unique_active_email', 'email', unique=True, postgresql_where=text('is_active = true')
        ),
    )

    # Connection with roles
    roles = relationship('Role', secondary=user_roles, backref='users', lazy='selectin')
