from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timezone
from flask_login import UserMixin, login_user, LoginManager, login_required, logout_user
from flask_bcrypt import Bcrypt
from dotenv import load_dotenv
import os

load_dotenv()
DatabaseURI=os.getenv("DatabaseURI")
app = Flask(__name__)
app.secret_key = 'krptos'
app.config['SQLALCHEMY_DATABASE_URI']=f'{DatabaseURI}'
db=SQLAlchemy()
db.init_app(app)
bcrypt= Bcrypt(app)


login_manger=LoginManager()
login_manger.init_app(app)
login_manger.login_view="login"


@login_manger.user_loader
def load_user(user_id):
    return User.session.get(int(user_id))


class User(db.Model, UserMixin):
    id=db.Column(db.Integer, primary_key=True)
    user_name=db.Column(db.String(40), nullable=False, unique=True)
    password=db.Column(db.String(100), nullable=False)


class Todo(db.Model):
    id=db.Column(db.Integer, primary_key=True)
    task_id=db.Column(db.String(40))
    content=db.Column(db.String(200), nullable=False)
    status=db.Column(db.String(30), default='In Progress')
    date_created=db.Column(db.DateTime, default=datetime.now(timezone.utc))
    
    def __repr__(self):
        return '<Task %r>' % self.id

with app.app_context():
    db.create_all()


def validate_username(uname):
    existing_user_name=User.session.filter_by(user_name=uname).first()
    if existing_user_name:
        return 2


@app.route('/',methods=['GET','POST'])
def login():
    if request.method=='POST':
        user=request.form.get('user')
        password=request.form.get('password')
        session['uid']=user
        chk_user=User.session.filter_by(user_name=user).first()
        if chk_user:
            if bcrypt.check_password_hash(chk_user.password,password):
                login_user(chk_user)
                return redirect(url_for('index'))
            else:
                return render_template('login.html',error="Incorrect password!",uname=user)
        else:
                return render_template('login.html',error="User name dosen't exist",uname=user)
        
    return render_template('login.html')


@app.route('/logout',methods=['GET','POST'])
@login_required
def logout():
    session.pop('uid', None)
    logout_user()
    return redirect(url_for('login'))


@app.route('/register',methods=['GET','POST'])
def register():
    if request.method=='POST':
        user=request.form.get('user')
        password=request.form.get('password')
        if validate_username(user)==2:
            return render_template('register.html',error='User name already exists try another one',password=password)        
        hashed_password=bcrypt.generate_password_hash(password).decode('utf-8')
        new_user=User(user_name=user, password=hashed_password)
        try:
            db.session.add(new_user)
            db.session.commit()
            return redirect(url_for('login'))
        except:
            return render_template('register.html',error='There was an issue signing you in',user=user,password=password)
    
    return render_template('register.html')


@app.route("/index",methods=['POST','GET'])
def index():
    if "uid" in session:
        uid=session['uid']
        print(f"uid: {uid}")
        if request.method=='POST':
            task_content=request.form['content']
            new_task=Todo(content=task_content,task_id=uid)
            try:
                db.session.add(new_task)
                db.session.commit()
                return redirect(url_for('index'))
            except:
                return "There was a problem in adding your task"
                
        else:
            tasks=Todo.session.order_by(Todo.date_created).filter(Todo.task_id==uid).all()
            return render_template('index.html',tasks=tasks)
    else:
        return redirect(url_for('login'))


@app.route('/delete/<int:id>')
def delete(id):
    task_to_delete=Todo.session.get_or_404(id)
    try:
        db.session.delete(task_to_delete)
        db.session.commit()
        return redirect(url_for('index'))
    except:
        return "There was a problem deleting that task"


@app.route('/update/<int:id>',methods=['GET','POST'])
def update(id):
    uid=session.get('uid')
    task=Todo.session.get_or_404(id)
    if request.method=='POST':
        task.content=request.form.get('content')
        task.status='In Progress'
        try:
            db.session.commit()
            return redirect(url_for('index'))
        except:
            return 'There was an issue updating your task'
    else:
        tasks=Todo.session.order_by(Todo.date_created).filter(Todo.task_id==uid).all()
        return render_template('index.html', task=task, tasks=tasks, update='UPD')


@app.route('/complete/<int:id>',methods=['POST','GET'])
def complete(id):
    task_to_complete=Todo.session.get_or_404(id)
    task_to_complete.status='Completed'
    try:
        db.session.commit()
        return redirect(url_for('index'))
    except:
        return "There was an error in changing the status of your task"


if __name__=="__main__":
    app.run(host='0.0.0.0')