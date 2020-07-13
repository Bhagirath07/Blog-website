"""
Created on Fri July 03 2020
@author: BhagiraTh Desani
@discription: Provide you to Information about programming languages as well as latest news about New Technologies on this Blog Website by Admin.
              

"""

from flask import Flask, render_template, request , session , redirect , flash
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail
from datetime import datetime
from werkzeug.utils import secure_filename
import math
import os
import json


with open('config.json','r') as c:
    params = json.load(c)["params"]

local_server = True
app = Flask(__name__)
app.secret_key = 'super-secret-key'
app.config['UPLOAD_FOLDER'] = params['upload_location']

app.config.update(
    MAIL_SERVER = 'smtp.gmail.com',
    MAIL_PORT = '465',
    MAIL_USE_SSL = True,
    MAIL_USERNAME = params['gmail-user'],
    MAIL_PASSWORD = params['gmail-pwd']
)

mail = Mail(app)                    # Passing Mail from the Client To Server DataBase

if(local_server) :
    app.config['SQLALCHEMY_DATABASE_URI'] = params['local_uri']
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = params['prod_uri']
db = SQLAlchemy(app)


class Contacts(db.Model):
    s_no = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    phone_num = db.Column(db.String(12), nullable=False)
    msg = db.Column(db.String(120), nullable=False)
    date = db.Column(db.String(12), nullable=True)
    email = db.Column(db.String(20), nullable=False)

class Posts(db.Model):
    s_no = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(80), nullable=False)
    slug = db.Column(db.String(25), nullable=False)
    content = db.Column(db.String(120), nullable=False)
    tag_line = db.Column(db.String(120), nullable=False)
    date = db.Column(db.String(12), nullable=True)
    img_file = db.Column(db.String(12), nullable=True)

@app.route("/")
def home():
    posts = Posts.query.filter_by().all()
    last = math.ceil(len(posts)/int(params['no_of_posts']))

    page = request.args.get('page')
    if (not str(page).isnumeric()):
        page = 1
    page = int(page)
    posts = posts[ (page-1)*int(params['no_of_posts']) : (page-1)*int(params['no_of_posts']) + int(params['no_of_posts']) ]
    # Pagination Logic

    if (page == 1):
        prev = "#"
        next = "/?page=" + str(page+1)
    elif (page == last):
        prev = "/?page=" + str(page - 1)
        next = "#"
    else:
        prev = "/?page=" + str(page - 1)
        next = "/?page=" + str(page + 1)

    return render_template('index.html' , params = params , posts = posts , prev = prev , next = next )

@app.route("/about")
def about():
    return render_template('about.html' , params = params)

@app.route("/post/<string:post_slug>", methods=['GET'])
def post_block(post_slug):
    post = Posts.query.filter_by(slug=post_slug).first()
    return render_template('post.html', params=params, post=post)


@app.route("/dashboard" , methods = ['GET','POST'])
def dashboard():
    if ('user' in session and session['user'] == params['admin-user']) :
        posts = Posts.query.all()
        return render_template('dashboard.html' , params = params , posts = posts)

    if request.method == 'POST' :
        username = request.form.get('uname')                    #Redirect to Admin Panel
        userpass = request.form.get('pass')
        if (username == params['admin-user'] and userpass == params['admin-pwd']) :
            session['user'] = username    # set the session variables
            posts = Posts.query.all()

            return render_template('dashboard.html' , params = params , posts = posts)

    return render_template('login.html' , params = params )

@app.route("/edit/<string:s_no>", methods = ['GET', 'POST'])
def edit(s_no):
    if ('user' in session and session['user'] == params['admin-user']):
        if request.method == 'POST':
            block_title = request.form.get('title')
            block_tline = request.form.get('tag_line')
            block_slug = request.form.get('slug')
            block_content = request.form.get('content')
            block_img = request.form.get('img_file')
            date = datetime.now()

            if s_no == '0':
                post = Posts(title = block_title , tag_line = block_tline , slug = block_slug ,
                             content = block_content , img_file = block_img , date = date )
                db.session.add(post)
                db.session.commit()
            else:
                post = Posts.query.filter_by(s_no = s_no).first()
                post.title = block_title
                post.tag_line = block_tline
                post.slug = block_slug
                post.content = block_content
                post.img_file = block_img
                post.date = date

                db.session.commit()
                return redirect('/edit/' + s_no)

        post = Posts.query.filter_by(s_no=s_no).first()
        return render_template('edit.html' , params = params , post = post , s_no = s_no)

@app.route("/logout")
def logout():
    session.pop('user')
    return redirect('/dashboard')

@app.route("/delete/<string:s_no>", methods = ['GET', 'POST'])
def delete(s_no):
    if ('user' in session and session['user'] == params['admin-user']):
        post = Posts.query.filter_by(s_no=s_no).first()
        db.session.delete(post)
        db.session.commit()
    return redirect('/dashboard')

@app.route("/uploader", methods = ['GET', 'POST'])
def uploader():
    if ('user' in session and session['user'] == params['admin-user']):
        if (request.method == 'POST'):
            f = request.files['file1']
            f.save(os.path.join(app.config['UPLOAD_FOLDER'] , secure_filename(f.filename)))
            return "Uploaded Successfully"

@app.route("/contact", methods = ['GET', 'POST'])
def contact():
    if(request.method=='POST'):
        '''Add entry to the database'''
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        message = request.form.get('message')

        entry = Contacts(name=name, phone_num = phone, msg = message, date= datetime.now(), email = email )
        db.session.add(entry)
        db.session.commit()
        # mail.send_message('New message from ' + name,
        #                   sender=email,
        #                   recipients = [params['gmail-user']],
        #                   body = message + "\n" + phone
        #                   )
        flash("Thanks for submitting your Details.","success")

    return render_template('contact.html' , params = params)


app.run(debug=True)
