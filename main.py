from datetime import datetime
from flask import Flask, render_template, redirect, request
from data import db_session
from data.users import User
from data.pages import Page
from flask_wtf import FlaskForm, Form
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms import TextAreaField, FieldList, FormField
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
import shutil

app = Flask(__name__)
app.config['SECRET_KEY'] = 'yandexlyceum_secret_key'
login_manager = LoginManager()
login_manager.init_app(app)


class PartForm(Form):
    header = StringField('Название раздела',
                        validators=[DataRequired()])
    img_lst = []
    load_image = FileField('Прикрепите изображения к разделу', 
                           validators=[FileRequired()])
    content = TextAreaField("Текст раздела", 
                          validators=[DataRequired()])


class CreatePageForm(FlaskForm):
    header = StringField('Название страницы',
                        validators=[DataRequired()])
    about = TextAreaField("Краткая информация о странице", 
                          validators=[DataRequired()])
    parts = FieldList(FormField(PartForm))
    submit = SubmitField('Сохранить страницу.')


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


@app.route('/edit_page/<page_info>', methods=['GET', 'POST'])
@login_required
def edit_page(page_info):
    db_sess = db_session.create_session()
    form = CreatePageForm()
    page_id = int(page_info.split('$')[1])
    page_type = page_info.split('$')[0]
    page = db_sess.query(Page).filter(Page.id == page_id).first()
    with open(page.json_page) as file:
        page_json = json.load(file)    
    if page_type == 'page_of_book':
        if form.is_submitted():
            page.header = form.header.data
            page.about = form.about.data
            print(len(form.parts))
            print(len(page_json['content']))
            for i in range(len(page_json['content'])):
                page_json[i]['header'] = form.parts[i].header.data
                page_json[i]['imgs'] = form.parts[i].img_lst
                page_json[i]['content'] = form.parts[i].content.data
            with open(page.json_page, 'w') as file:
                json.dump(page_json, file, ensure_ascii=False)
            db_sess.commit()
            return redirect('/edit_page/{}'.format(page_info))
        form.header.data = page.header
        form.about.data = page.about
        for elem in page_json['content'][len(form.parts):]:
            form.parts.append_entry()
            form.parts[len(form.parts) - 1].header.data = elem['header']
            form.parts[len(form.parts) - 1].img_lst = elem['imgs']
            form.parts[len(form.parts) - 1].content.data = elem['content']            
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
    os.mkdir('book_pages/directory{}'.format(page.id))
    page.directory = 'book_pages/directory{}'.format(page.id)
    json_page = {
        'content': []
    }
    with open('book_pages/directory{}/json_file.json'.format(
        page.id), 
              'w') as file:
        json.dump(json_page, file, ensure_ascii=False, indent=2)
    page.json_page = 'book_pages/directory{}/json_file.json'.format(
        page.id)    
    db_sess.commit()    
    return redirect('/edit_page/page_of_book${}'.format(page.id))


@app.route('/adding_part/<params>')
@login_required
def adding_part(params):
    db_sess = db_session.create_session()
    page_id = int(params.split('$')[1])
    part_num = int(params.split('$')[2])
    page = db_sess.query(Page).filter(Page.id == page_id).first()
    with open(page.json_page) as file:
        page_json = json.load(file)
    right_num = len(page_json['content'])
    tmp = page_json['content'][part_num:]
    page_json['content'] = page_json['content'][:part_num] + [
        {'header': 'Раздел{}'.format(right_num + 1), 'imgs': [], 
         'content': 'Текст раздела {}'.format(right_num + 1)}] + tmp
    with open(page.json_page, 'w') as file:
        json.dump(page_json, file)
    return redirect('/edit_page/page_of_book${}'.format(page_id))


@app.route('/delete_part/<params>')
@login_required
def delete_part(params):
    db_sess = db_session.create_session()
    page_id = int(params.split('$')[1])
    part_num = int(params.split('$')[2])
    page = db_sess.query(Page).filter(Page.id == page_id).first()
    with open(page.json_page) as file:
        page_json = json.load(file)
    del page_json['content'][part_num - 1]
    with open(page.json_page, 'w') as file:
        json.dump(page_json, file)
    return redirect('/edit_page/page_of_book${}'.format(page_id))


@app.route('/adding_image/<params>')
@login_required
def add_image(params):
    db_sess = db_session.create_session()
    page_id = int(params.split('$')[1])
    page = db_sess.query(Page).filter(Page.id == page_id).first()
    with open(page.json_page) as file:
        page_json = json.load(file)
    page_json['content']
    with open(page.json_page, 'w') as file:
        json.dump(page_json, file)
    return redirect('/edit_page/page_of_book${}'.format(page_id))


@app.route('/delete_page/<page_id>')
@login_required
def delete_page(page_id):
    db_sess = db_session.create_session()
    page = db_sess.query(Page).filter(Page.id == page_id).first()
    shutil.rmtree(page.directory)
    db_sess.delete(page)
    db_sess.commit()
    return redirect('/users')


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
