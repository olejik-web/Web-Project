import datetime
import sqlalchemy
from sqlalchemy import orm
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash


from .db_session import SqlAlchemyBase


class News(SqlAlchemyBase, UserMixin):
    __tablename__ = 'news'
    id = sqlalchemy.Column(sqlalchemy.Integer,
                           primary_key=True, autoincrement=True)
    author = sqlalchemy.Column(sqlalchemy.Integer)
    header = sqlalchemy.Column(sqlalchemy.String)
    about = sqlalchemy.Column(sqlalchemy.String)
    json_page = sqlalchemy.Column(sqlalchemy.String)
    directory = sqlalchemy.Column(sqlalchemy.String)
    edit_type = sqlalchemy.Column(sqlalchemy.String)