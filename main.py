from datetime import datetime
from flask import Flask, render_template, redirect, request
from data import db_session
from data.users import User
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms import TextAreaField
from wtforms.fields.html5 import EmailField
from wtforms.validators import DataRequired
from flask_login import LoginManager, login_user, login_required, logout_user
import flask_login
from werkzeug.security import generate_password_hash, check_password_hash
from PIL import Image
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'yandexlyceum_secret_key'
login_manager = LoginManager()
login_manager.init_app(app)


class RegisterForm(FlaskForm):
    email = EmailField('Почта', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    password_again = PasswordField('Повторите пароль', 
                                   validators=[DataRequired()])
    name = StringField('Имя пользователя', validators=[DataRequired()])
    about = TextAreaField("Немного о себе")
    submit = SubmitField('Регистрация')


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


@app.route('/book')
def book_main():
    return render_template('book.html', title='Книга')


@app.route('/users')
def users_main():
    return render_template('users.html', title='Пользователи')


@app.route('/pages')
def pages_main():
    return render_template('pages.html', title='Статьи')


@app.route('/news')
def news_main():
    return render_template('news.html', title='Новости')


@app.route('/register', methods=['GET', 'POST'])
def reqister():
    form = RegisterForm()
    if form.validate_on_submit():
        if form.password.data != form.password_again.data:
            return render_template('register.html', title='Регистрация',
                                           form=form,
                                           message="Пароли не совпадают!") 
        if '@' not in form.email.data:
            return render_template('register.html', title='Регистрация',
                                           form=form,
                                           message="Проверьте правильность ввода адреса электронной почты!") 
        return redirect('/login')
    return render_template('register.html', title='Регистрация', form=form)


def main():  
    app.run(port=8080, host='127.0.0.1')
    # db_session.global_init("db/mars.db")
    # db_sess = db_session.create_session()    


if __name__ == '__main__':
    main()
