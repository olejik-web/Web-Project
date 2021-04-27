from datetime import datetime
from flask import Flask, render_template, redirect, request
from data import db_session
from data.users import User
from data.pages import Page
from flask_wtf import FlaskForm
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


class PartForm(FlaskForm):
    header = StringField('�������� �������',
                        validators=[DataRequired()])
    img_lst = []
    load_image = FileField('���������� ����������� � �������', 
                           validators=[FileRequired()])
    content = TextAreaField("����� �������", 
                          validators=[DataRequired()])


class CreatePageForm(FlaskForm):
    header = StringField('�������� ��������',
                        validators=[DataRequired()])
    about = TextAreaField("������� ���������� � ��������", 
                          validators=[DataRequired()])
    parts = FieldList(FormField(PartForm))
    submit = SubmitField('���������')


class LoginForm(FlaskForm):
    email = StringField('����� ������������',
                        validators=[DataRequired()])
    password = PasswordField('������', validators=[DataRequired()])
    submit = SubmitField('�����')


class RegisterForm(FlaskForm):
    email = EmailField('�����', validators=[DataRequired()])
    password = PasswordField('������', validators=[DataRequired()])
    password_again = PasswordField('��������� ������',
                                   validators=[DataRequired()])
    name = StringField('��� ������������', validators=[DataRequired()])
    about = TextAreaField("������� � ����", validators=[DataRequired()])
    submit = SubmitField('�����������')


@login_manager.user_loader
def load_user(user_id):
    db_sess = db_session.create_session()
    return db_sess.query(User).get(user_id)


@app.route('/')
def index():
    return render_template('index.html', title='�������')


@app.route('/edit_page/<page_info>', methods=['GET', 'POST'])
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
        for elem in page_json['content']:
            form.parts.append_entry()
            form.parts[len(form.parts) - 1].header.data = elem['header']
            form.parts[len(form.parts) - 1].img_lst = elem['imgs']
            form.parts[len(form.parts) - 1].content.data = elem['content']
        if form.validate_on_submit():
            page.header = form.header.data
            page.about = form.about.data
            for i in range(page_json['content']):
                page_json[i]['header'] = form.parts[i].header.data
                page_json[i]['imgs'] = form.parts[i].img_lst
                page_json[i]['content'] = form.parts[i].content.data
            with open(page.json_page) as file:
                file.dump(page_json)
            db_sess.commit()
            return redirect('/users')
        else:
            return render_template('edit_page_of_book.html', 
                               title='�������������� �������� �����', 
                               form=form, page=page)
        
        
@app.route('/book')
def book_main():
    return render_template('book.html', title='�����')


@app.route('/users')
def users_main():
    db_sess = db_session.create_session()
    lst = []
    for elem in db_sess.query(Page).filter(Page.author == current_user.id):
        lst.append(elem)
    return render_template('users.html', title='������������', pages=lst)


@app.route('/pages')
def pages_main():
    return render_template('pages.html', title='������')


@app.route('/news')
def news_main():
    return render_template('news.html', title='�������')


@app.route('/register', methods=['GET', 'POST'])
def reqister():
    form = RegisterForm()
    if form.validate_on_submit():
        if form.password.data != form.password_again.data:
            return render_template('register.html', title='�����������',
                                   form=form,
                                   message="������ �� ���������!")
        db_sess = db_session.create_session()
        if db_sess.query(User).filter(User.email == form.email.data).first():
            return render_template('register.html', title='�����������',
                                   form=form,
                                   message="����� ������������ ��� ����")
        user = User(
            name=form.name.data,
            email=form.email.data,
            about=form.about.data
        )
        user.set_password(form.password.data)
        db_sess.add(user)
        db_sess.commit()
        return redirect('/login')
    return render_template('register.html', title='�����������', form=form,
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
                               message="������������ ����� ��� ������",
                               form=form)
    return render_template('login.html', title='�����������', form=form,
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
        'content': [
            {
                'header': '�������� 1',
                'imgs': [],
                'content': '����� 1',
            }            
        ]
    }
    with open('book_pages/directory{}/json_file.json'.format(
        page.id), 
              'w') as file:
        json.dump(json_page, file)
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
    pages = db_sess.query(Page).all()
    right_num = pages[len(pages) - 1]
    with open(page.json_page) as file:
        page_json = json.load(file)
    tmp = page_json['content'][part_num:]
    page_json['content'] = page_json['content'][:part_num] + [
        {'header': '������{}'.format(right_num + 1), 'imgs': [], 
         'content': '����� ������� {}'.format(right_num + 1)}] + tmp
    with open(page.json_page, 'w') as file:
        json.dump(page_json, file)
    return redirect('/edit_page/page_of_book$1')


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
