from datetime import datetime
from flask import Flask, render_template, redirect, request
from data import db_session
from data.users import User
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms import IntegerField
from wtforms.validators import DataRequired
from flask_login import LoginManager, login_user, login_required, logout_user
import flask_login
from PIL import Image
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'yandexlyceum_secret_key'
login_manager = LoginManager()
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    db_sess = db_session.create_session()
    return db_sess.query(User).get(user_id)


@app.route('/')
def index():
    db_session.global_init("db/mars.db")
    db_sess = db_session.create_session()
    users = [user for user in db_sess.query(User).all()]
    return render_template('index.html', title='Главная')

def main():  
    app.run(port=8080, host='127.0.0.1')


if __name__ == '__main__':
    main()
