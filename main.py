from datetime import datetime
from flask import Flask, render_template, redirect, request
from data import db_session
from data.users import User
from data.pages import Page
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms import TextAreaField
from wtforms.fields.html5 import EmailField
from wtforms.validators import DataRequired
from flask_login import LoginManager, login_user, login_required, logout_user
from flask_login import current_user
from werkzeug.security import generate_password_hash, check_password_hash
from flask_wtf.file import FileField, FileRequired
from werkzeug.utils import secure_filename
from PIL import Image
import os
import json

app = Flask(__name__)
app.config['SECRET_KEY'] = 'yandexlyceum_secret_key'
login_manager = LoginManager()
login_manager.init_app(app)


class PartForm(FlaskForm):
    header = StringField('Название раздела',
                        validators=[DataRequired()])
    imgs = 


class CreatePageForm(FlaskForm):
    header = StringField('Название страницы',
                        validators=[DataRequired()])
    about = TextAreaField("Краткая информация о странице", 
                          validators=[DataRequired()])
    parts = FieldList(FormField(PartForm))
    submit = SubmitField('Сохранить')


class LoginForm(FlaskForm):
    email = StringField('Почта пользователя',
                        validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    submit = SubmitField('Войти')


class RegisterForm(FlaskForm):
    email = EmailField('Почта', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    password_again = PasswordField('Повторите пароль',
                                   validators=[DataRequired()])
    name = StringField('Имя пользователя', validators=[DataRequired()])
    about = TextAreaField("Немного о себе", validators=[DataRequired()])
    submit = SubmitField('Регистрация')


@login_manager.user_loader
def load_user(user_id):
    db_sess = db_session.create_session()
    return db_sess.query(User).get(user_id)


@app.route('/')
def index():
    return render_template('index.html', title='Главная')


@app.route('/edit_page/<page_info>')
@login_required
def edit_page(page_info):
    db_sess = db_session.create_session()
    form = CreatePageForm()
    page_id = int(page_info.split('$')[1])
    page_type = page_info.split('$')[0]
    page = db_sess.query(Page).filter(Page.id == page_id).first()
    if page_type == 'page_of_book':
        form = CreatePageForm()
        db_sess = db_session.create_session()
        page = db_sess.query(Page).filter(Page.id == page_id).first()
        form.header.data = page.header
        form.about.data = page.about
        with open(page.json_page) as file:
            page_json = json.load(file)
        form.content = page_json['content']
        for elem in form.content:
            elem['header'] = StringField('123',
                        validators=[DataRequired()])
            elem['imgs'] = (FileField('Прикрепите изображения к статье', 
                       validators=[FileRequired()]), elem['imgs'])
            elem['content'] = TextAreaField("Текст раздела", 
                          validators=[DataRequired()])
        print(StringField('123',
                        validators=[DataRequired()]))
        print(form.content[0]['header'])
        print(form.header)
        
        if form.validate_on_submit():
            return redirect('/users')
        else:
            return render_template('edit_page_of_book.html', 
                               title='Редактирование страницы книги', 
                               form=form, page=page)
        
        
@app.route('/book')
def book_main():
    return render_template('book.html', title='Книга')


@app.route('/users')
def users_main():
    db_sess = db_session.create_session()
    lst = []
    for elem in db_sess.query(Page).filter(Page.author == current_user.id):
        lst.append(elem)
    return render_template('users.html', title='Пользователи', pages=lst)


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
        db_sess = db_session.create_session()
        if db_sess.query(User).filter(User.email == form.email.data).first():
            return render_template('register.html', title='Регистрация',
                                   form=form,
                                   message="Такой пользователь уже есть")
        user = User(
            name=form.name.data,
            email=form.email.data,
            about=form.about.data
        )
        user.set_password(form.password.data)
        db_sess.add(user)
        db_sess.commit()
        return redirect('/login')
    return render_template('register.html', title='Регистрация', form=form,
                           message='')


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(
            User.email == form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            return redirect("/")
        return render_template('login.html',
                               message="Неправильный логин или пароль",
                               form=form)
    return render_template('login.html', title='Авторизация', form=form,
                           message='')


@app.route('/create_page/<page_type>')
@login_required
def create_page(page_type):
    db_sess = db_session.create_session()
    page = Page()
    page.author = current_user.id
    page.type = page_type
    page.edit_type = 'edited'
    db_sess.add(page)
    db_sess.commit()
    db_sess = db_session.create_session()
    for elem in db_sess.query(Page).all():
        page = elem
    os.mkdir('static/img/book_pages/directory{}'.format(page.id))
    json_page = {
        'content': [
            {
                'header': 'Название 1',
                'imgs': [],
                'content': 'Текст 1',
            }            
        ]
    }
    with open('static/img/book_pages/directory{}/json_file.json'.format(
        page.id), 
              'w') as file:
        json.dump(json_page, file)
    page.json_page = 'static/img/book_pages/directory{}/json_file.json'.format(
        page.id)    
    db_sess.commit()    
    return redirect('/edit_page/page_of_book${}'.format(page.id))


'''def delete_page():
    pass'''


def clear_database():
    db_sess = db_session.create_session()
    db_sess.query(Page).delete()
    db_sess.commit()
    
    
def main():
    db_session.global_init("db/database.db")
    # clear_database()
    app.run(port=8080, host='127.0.0.1')


if __name__ == '__main__':
    main()
