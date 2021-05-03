from datetime import datetime
from flask import Flask, render_template, redirect, request
from data import db_session
from data.users import User
from data.pages import Page
from data.images import Image
from data.news import News
from flask_wtf import FlaskForm, Form
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms import TextAreaField, FieldList, FormField
from wtforms.fields.html5 import EmailField
from wtforms.validators import DataRequired, InputRequired
from flask_login import LoginManager, login_user, login_required, logout_user
from flask_login import current_user
from werkzeug.security import generate_password_hash, check_password_hash
from flask_wtf.file import FileField, FileRequired
from werkzeug.utils import secure_filename
# from PIL import Image
import os
import json
import shutil

app = Flask(__name__)
app.config['SECRET_KEY'] = 'yandexlyceum_secret_key'
login_manager = LoginManager()
login_manager.init_app(app)


class LoadImageForm(FlaskForm):
    load_image = FileField('Прикрепите изображения к разделу', 
                           validators=[])
    submit = SubmitField('Добавить изображение')


class ProfileEditForm(FlaskForm):
    login = StringField('Логин', validators=[])
    old_password = PasswordField('Старый пароль', validators=[])
    new_password = PasswordField('Новый пароль', validators=[])
    email = StringField('Email', validators=[])
    about = TextAreaField("Обо мне", 
                          validators=[])
    load_image = FileField('Прикрепите фотографию профиля')
    submit = SubmitField('Обновить профиль')


class NewsCreatePageForm(FlaskForm):
    header = StringField('Название страницы',
                        validators=[DataRequired()])
    about = TextAreaField("Краткая информация о странице", 
                          validators=[DataRequired()])
    submit = SubmitField('Опубликовать новость.')


class NewsPartForm(FlaskForm):
    part_header = StringField('Название раздела',
                        validators=[DataRequired()])
    img_lst = []
    load_image = FileField('Прикрепите изображения к разделу', 
                           validators=[])
    content = TextAreaField("Текст раздела", 
                          validators=[DataRequired()])
    submit = SubmitField('Опубликовать новость.')


class PartForm(FlaskForm):
    part_header = StringField('Название раздела',
                        validators=[DataRequired()])
    img_lst = []
    load_image = FileField('Прикрепите изображения к разделу', 
                           validators=[])
    content = TextAreaField("Текст раздела", 
                          validators=[DataRequired()])
    submit = SubmitField('Сохранить изменения')


class CreatePageForm(FlaskForm):
    header = StringField('Название страницы',
                        validators=[DataRequired()])
    about = TextAreaField("Краткая информация о странице", 
                          validators=[DataRequired()])
    submit = SubmitField('Сохранить изменения.')


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


@app.route('/user_info/<int:user_id>')
@login_required
def user_info(user_id):
    db_sess = db_session.create_session()
    user = db_sess.query(User).filter(User.id == user_id).first()
    user_image = db_sess.query(Image).filter(Image.id == user.image).first()
    lst = []
    for elem in db_sess.query(Page).filter(
        Page.author == user.id):
        lst.append(elem)    
    pages = [elem for elem in lst if elem.type == 'page_of_book']
    articles = [elem for elem in lst if elem.type == 'article']
    history = [elem for elem in lst if elem.type == 'story']        
    return render_template('user_info.html', title='Информация о пользователе', 
                           user=user, profile_image=user_image.path, 
                           pages=pages, articles=articles, history=history)


@app.route('/moderation_panel')
@login_required
def moder_menu():
    if current_user.type != 'admin':
        return redirect('/')
    db_sess = db_session.create_session()
    edited_pages = db_sess.query(Page).filter(Page.edit_type == 'edited')
    publicated_pages = db_sess.query(Page).filter(
        Page.edit_type == 'publicated')
    return render_template('moder_menu.html', title='Панель модерации.', 
                           edited_pages=edited_pages, 
                           publicated_pages=publicated_pages)


@app.route('/public_page/<int:page_id>')
@login_required
def public_page(page_id):
    if current_user.type != 'admin':
        return redirect('/')
    db_sess = db_session.create_session()
    page = db_sess.query(Page).filter(Page.id == page_id).first()
    page.edit_type = 'publicated'
    db_sess.commit()
    return redirect('/moderation_panel')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect("/")


@app.route('/')
def index():
    db_sess = db_session.create_session()
    news = db_sess.query(News).all()
    pages = db_sess.query(Page).filter(Page.type == 'page_of_book', 
                                       Page.edit_type == 'publicated')
    articles = db_sess.query(Page).filter(Page.type == 'article', 
                                          Page.edit_type == 'publicated')
    history = db_sess.query(Page).filter(Page.type == 'story', 
                                         Page.edit_type == 'publicated')
    users = db_sess.query(User).all()
    tmp = [user.image for user in db_sess.query(User).all()]
    images = []
    for image_id in tmp:
        try:
            images.append(db_sess.query(Image).filter(
                Image.id == image_id).first().path)
        except Exception:
            images.append(None)            
    return render_template('index.html', title='Главная', news=news, 
                           pages=pages, articles=articles, 
                           history=history, users=users, user_images=images)


@app.route('/edit_user/<int:user_id>', methods=['GET', 'POST'])
@login_required
def edit_user(user_id):
    if current_user.id != user_id:
        return redirect('/users')
    db_sess = db_session.create_session()
    user = db_sess.query(User).filter(User.id == user_id).first()
    form = ProfileEditForm()    
    if form.validate_on_submit():
        if user.check_password(form.old_password.data):
            if form.new_password.data:
                user.name = form.login.data
                user.about = form.about.data
                user.email = form.email.data
                if form.load_image.data:
                    image_data = form.load_image.data
                    db_image = Image()
                    db_sess.add(db_image)
                    db_sess.commit()
                    filename = secure_filename(image_data.filename)
                    db_image.path = os.path.join(
                        'static/profile_images/image' 
                        + str(db_image.id) + '.jpg')
                    image_data.save(db_image.path)
                    user.image = db_image.id
                    db_sess.commit()
                user.set_password(form.new_password.data)
                db_sess.commit()
                return redirect('/users')
            else:
                return render_template(
                    'edit_user.html', form=form, 
                    message='Новый пароль не может быть пустым!', 
                    title='Изменение профиля')
        else:
            return render_template('edit_user.html', form=form,
                                   message='Старый пароль введен неверно!', 
                                   title='Изменение профиля')
    form.login.data = user.name
    form.about.data = user.about
    form.email.data = user.email
    return render_template('edit_user.html', form=form)


@app.route('/edit_news/<params>', methods=['GET', 'POST'])
@login_required
def edit_news(params):
    news_id = int(params.split('$')[0])
    part_num = int(params.split('$')[1])
    db_sess = db_session.create_session()
    news = db_sess.query(News).filter(News.id == news_id).first()
    main_form = NewsCreatePageForm()
    part_form = NewsPartForm()    
    with open(news.json_page) as file:
        page_json = json.load(file)    
    if main_form.is_submitted():
        news.header = main_form.header.data
        news.about = main_form.about.data
        try:
            page_json['content'][part_num]['header'] = part_form.part_header.data
            page_json['content'][part_num]['content'] = part_form.content.data
            if part_form.load_image.data:
                image_data = part_form.load_image.data
                db_image = Image()
                db_sess.add(db_image)
                db_sess.commit()
                filename = secure_filename(image_data.filename)
                db_image.path = os.path.join(
                    'static/news_images/image' 
                    + str(db_image.id) + '.jpg')
                image_data.save(db_image.path)
                page_json['content'][part_num]['imgs'].append(db_image.id)
            db_sess.commit()            
        except Exception:
            pass
        with open(news.json_page, 'w') as file:
            json.dump(page_json, file, ensure_ascii=False, indent=2)        
        db_sess.commit()
        return redirect('/edit_news/{}'.format(params))
    main_form.header.data = news.header
    main_form.about.data = news.about
    if news.author != current_user.id:
        return redirect('/users')
    try:
        part_form.part_header.data = page_json['content'][part_num]['header']
        part_form.content.data = page_json['content'][part_num]['content']
        part_form.img_lst = [db_sess.query(Image).filter(
            Image.id == elem).first().path
                             for elem in page_json['content'][part_num]['imgs']]
    except:
        pass
    return render_template('edit_news.html', title='Редактирование новости', 
                           news=news, main_form=main_form, part_form=part_form, 
                           json=page_json)


@app.route('/edit_page/<page_info>', methods=['GET', 'POST'])
@login_required
def edit_page(page_info):
    print(page_info)
    db_sess = db_session.create_session()
    main_form = CreatePageForm()
    part_form = PartForm()
    page_id = int(page_info.split('$')[1])
    page_type = page_info.split('$')[0]
    part_num = int(page_info.split('$')[2])
    page = db_sess.query(Page).filter(Page.id == page_id).first()
    print('user_type =', current_user.type )
    if current_user.type != 'admin':
        if page.author != current_user.id:
            return redirect('/users')
    with open(page.json_page) as file:
        page_json = json.load(file)    
    if main_form.is_submitted():
        page.header = main_form.header.data
        page.about = main_form.about.data
        try:
            page_json['content'][part_num]['header'] = part_form.part_header.data
            page_json['content'][part_num]['content'] = part_form.content.data
            if part_form.load_image.data:
                image_data = part_form.load_image.data
                db_image = Image()
                db_sess.add(db_image)
                db_sess.commit()
                filename = secure_filename(image_data.filename)
                if page_type == 'article':
                    db_image.path = os.path.join(
                        'static/article_images/image' 
                        + str(db_image.id) + '.jpg')
                elif page_type == 'story':
                    db_image.path = os.path.join(
                        'static/history_images/image' 
                        + str(db_image.id) + '.jpg')
                else:
                    db_image.path = os.path.join(
                        'static/book_images/image' 
                        + str(db_image.id) + '.jpg')
                image_data.save(db_image.path)
                page_json['content'][part_num]['imgs'].append(db_image.id)
            db_sess.commit()            
        except Exception:
            pass
        with open(page.json_page, 'w') as file:
            json.dump(page_json, file, ensure_ascii=False, indent=2)        
        db_sess.commit()
        return redirect('/edit_page/{}'.format(page_info))
    main_form.header.data = page.header
    main_form.about.data = page.about
    try:
        part_form.part_header.data = page_json['content'][part_num]['header']
        part_form.content.data = page_json['content'][part_num]['content']
        part_form.img_lst = [db_sess.query(Image).filter(
            Image.id == elem).first().path
                             for elem in page_json['content'][part_num]['imgs']]
    except:
        pass
    title = 'страницы книги'
    if page_type == 'article':
        title = 'статьи'
    if page_type == 'story':
        title = 'истории'
    return render_template('edit_page.html', 
                           title='Редактирование {}'.format(title), 
                           page=page, main_form=main_form, part_form=part_form, 
                           json=page_json)


@app.route('/read_page/<int:page_id>')
def read_page(page_id):
    db_sess = db_session.create_session()
    page = db_sess.query(Page).filter(Page.id == page_id).first()
    json_path = page.json_page
    with open(json_path) as file:
        json_file = json.load(file)
    images = [ [db_sess.query(Image).filter(
            Image.id == elem).first().path 
                for elem in json_file['content'][part_num]['imgs']] 
               for part_num in range(len(json_file['content']))]
    return render_template('read_page.html', 
                           title='Читать страницу книги памяти', 
                           page=page, json=json_file, images=images)
        
        
@app.route('/book')
def book_main():
    db_sess = db_session.create_session()
    pages = db_sess.query(Page).filter(Page.type == 'page_of_book', 
                                       Page.edit_type == 'publicated')
    return render_template('book.html', title='Книга', pages=pages)


@app.route('/history')
def history_main():
    db_sess = db_session.create_session()
    history = db_sess.query(Page).filter(Page.type == 'story', 
                                       Page.edit_type == 'publicated')
    return render_template('history.html', title='История', history=history)


@app.route('/users')
def users_main():
    db_sess = db_session.create_session()
    users = db_sess.query(User).all()
    tmp = [user.image for user in db_sess.query(User).all()]
    images = []
    for image_id in tmp:
        try:
            images.append(db_sess.query(Image).filter(
                Image.id == image_id).first().path)
        except Exception:
            images.append(None)            
    lst = []
    if current_user.is_authenticated:
        for elem in db_sess.query(Page).filter(
            Page.author == current_user.id):
            lst.append(elem)
        image = db_sess.query(Image).filter(
            Image.id == current_user.image).first()
        if not image:
            image = Image()
            image.path = '/static/profile_images/standart_user.png'
            db_sess.add(image)
            db_sess.commit()
            current_user.image = image.id
        if current_user.type != 'admin':
            pages = [elem for elem in lst if elem.type == 'page_of_book' 
                     and elem.edit_type == 'edited']
            articles = [elem for elem in lst if elem.type == 'article' 
                        and elem.edit_type == 'edited']
            history = [elem for elem in lst if elem.type == 'story' 
                        and elem.edit_type == 'edited']
        else:
            pages = [elem for elem in lst if elem.type == 'page_of_book']
            articles = [elem for elem in lst if elem.type == 'article']
            history = [elem for elem in lst if elem.type == 'story']       
        return render_template('users.html', title='Пользователи', 
                               pages=pages, articles=articles, history=history, 
                               profile_image=image.path, users=users, 
                               user_images=images)
    else:
        return render_template('users.html', title='Пользователи', users=users, 
                               user_images=images)


@app.route('/pages')
def pages_main():
    db_sess = db_session.create_session()
    articles = db_sess.query(Page).filter(Page.type == 'article', 
                                       Page.edit_type == 'publicated')
    return render_template('pages.html', title='Статьи', articles=articles)


@app.route('/news')
def news_main():
    db_sess = db_session.create_session()
    news = db_sess.query(News).all()
    return render_template('news.html', title='Новости', news=news)


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
            about=form.about.data,
            image=30,
            type='user'
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
    if page_type == 'article' or page_type == 'story':
        db_sess = db_session.create_session()
        page = Page()
        page.author = current_user.id
        page.type = page_type
        page.edit_type = 'edited'
        db_sess.add(page)
        db_sess.commit()
        if page_type == 'article':
            os.mkdir('article_pages/directory{}'.format(page.id))
            page.directory = 'article_pages/directory{}'.format(page.id)
            json_page = {
                'content': [
                    {
                        'header': 'Раздел1',
                        'imgs': [],
                        'content': 'Текст раздела 1',
                    }
                ]
            }
            with open('article_pages/directory{}/json_file.json'.format(
                page.id), 
                      'w') as file:
                json.dump(json_page, file, ensure_ascii=False, indent=2)
            page.json_page = 'article_pages/directory{}/json_file.json'.format(
                page.id)    
            db_sess.commit()  
        else:
            os.mkdir('history_pages/directory{}'.format(page.id))
            page.directory = 'history_pages/directory{}'.format(page.id)
            json_page = {
                'content': [
                    {
                        'header': 'Раздел1',
                        'imgs': [],
                        'content': 'Текст раздела 1',
                    }
                ]
            }
            with open('history_pages/directory{}/json_file.json'.format(
                page.id), 
                      'w') as file:
                json.dump(json_page, file, ensure_ascii=False, indent=2)
            page.json_page = 'history_pages/directory{}/json_file.json'.format(
                page.id)    
            db_sess.commit()  
        return redirect('/edit_page/{}${}$0'.format(page_type, page.id))
    if page_type == 'page_of_book':
        db_sess = db_session.create_session()
        page = Page()
        page.author = current_user.id
        page.type = page_type
        page.edit_type = 'edited'
        db_sess.add(page)
        db_sess.commit()
        os.mkdir('book_pages/directory{}'.format(page.id))
        page.directory = 'book_pages/directory{}'.format(page.id)
        json_page = {
            'content': [
                {
                    'header': 'Раздел1',
                    'imgs': [],
                    'content': 'Текст раздела 1',                
                }
            ]
        }
        with open('book_pages/directory{}/json_file.json'.format(
            page.id), 
                  'w') as file:
            json.dump(json_page, file, ensure_ascii=False, indent=2)
        page.json_page = 'book_pages/directory{}/json_file.json'.format(
            page.id)    
        db_sess.commit()    
        return redirect('/edit_page/page_of_book${}$0'.format(page.id))
    elif page_type == 'news':
        if current_user.id != 1:
            return redirect('/users')        
        db_sess = db_session.create_session()
        page = News()
        page.author = current_user.id
        page.edit_type = 'edited'
        db_sess.add(page)
        db_sess.commit()
        os.mkdir('news/directory{}'.format(page.id))
        page.directory = 'news/directory{}'.format(page.id)
        json_page = {
            'content': [
                {
                    'header': 'Раздел1',
                    'imgs': [],
                    'content': 'Текст раздела 1',
                }
            ]
        }
        with open('news/directory{}/json_file.json'.format(
            page.id), 
                  'w') as file:
            json.dump(json_page, file, ensure_ascii=False, indent=2)
        page.json_page = 'news/directory{}/json_file.json'.format(
            page.id)    
        db_sess.commit()    
        return redirect('/edit_news/{}$0'.format(page.id))        


@app.route('/adding_part/<params>')
@login_required
def adding_part(params):
    db_sess = db_session.create_session()
    page_type = params.split('$')[0]
    if page_type != 'news':
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
            json.dump(page_json, file, ensure_ascii=False, indent=2)
        return redirect('/edit_page/{}${}${}'.format(page_type,
            page_id, part_num))
    else:
        news_id = int(params.split('$')[1])
        part_num = int(params.split('$')[2])
        news = db_sess.query(News).filter(News.id == news_id).first()
        with open(news.json_page) as file:
            page_json = json.load(file)
        right_num = len(page_json['content'])
        tmp = page_json['content'][part_num:]
        page_json['content'] = page_json['content'][:part_num] + [
            {'header': 'Раздел{}'.format(right_num + 1), 'imgs': [], 
             'content': 'Текст раздела {}'.format(right_num + 1)}] + tmp
        with open(news.json_page, 'w') as file:
            json.dump(page_json, file, ensure_ascii=False, indent=2)
        return redirect('/edit_news/{}${}'.format(news_id, part_num))


@app.route('/delete_part/<params>')
@login_required
def delete_part(params):
    db_sess = db_session.create_session()
    page_type = params.split('$')[0]
    if page_type != 'news':
        page_id = int(params.split('$')[1])
        part_num = int(params.split('$')[2])
        page = db_sess.query(Page).filter(Page.id == page_id).first()
        with open(page.json_page) as file:
            page_json = json.load(file)
        del page_json['content'][part_num - 1]
        with open(page.json_page, 'w') as file:
            json.dump(page_json, file)
        return redirect('/edit_page/{}${}${}'.format(page_type, page_id, 0))
    else:
        page_id = int(params.split('$')[1])
        part_num = int(params.split('$')[2])
        page = db_sess.query(News).filter(News.id == page_id).first()
        with open(page.json_page) as file:
            page_json = json.load(file)
        del page_json['content'][part_num - 1]
        with open(page.json_page, 'w') as file:
            json.dump(page_json, file)
        return redirect('/edit_news/{}${}'.format(page_id, 0))


@app.route('/read_news/<int:news_id>')
def read_news(news_id):
    db_sess = db_session.create_session()
    news = db_sess.query(News).filter(News.id == news_id).first()
    json_path = news.json_page
    with open(json_path) as file:
        json_file = json.load(file)
    images = [ [db_sess.query(Image).filter(
            Image.id == elem).first().path 
                for elem in json_file['content'][part_num]['imgs']] 
               for part_num in range(len(json_file['content']))]
    print(images)
    return render_template('read_news.html', title='Читать новость', 
                           news=news, json=json_file, images=images)


@app.route('/delete_page/<page_id>')
@login_required
def delete_page(page_id):
    db_sess = db_session.create_session()
    page = db_sess.query(Page).filter(Page.id == page_id).first()
    shutil.rmtree(page.directory)
    db_sess.delete(page)
    db_sess.commit()
    return redirect('/users')


@app.route('/delete_news/<int:news_id>')
@login_required
def delete_news(news_id):
    if current_user.id != 1:
        return redirect('/')    
    db_sess = db_session.create_session()
    news = db_sess.query(News).filter(News.id == news_id).first()
    shutil.rmtree(news.directory)
    db_sess.delete(news)
    db_sess.commit()
    return redirect('/')


def clear_database():
    db_sess = db_session.create_session()
    db_sess.query(User).delete()
    db_sess.commit()
    
    
def main():
    db_session.global_init("db/database.db")
    # clear_database()
    app.run(port=8080, host='127.0.0.1')


if __name__ == '__main__':
    main()
