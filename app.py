from flask import Flask, render_template, request, redirect
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO

app = Flask(__name__)
socketio = SocketIO(app)

app.config['SECRET_KEY'] = 'secret123'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tasks.db'

db = SQLAlchemy(app)


# User Model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100))
    password = db.Column(db.String(100))


# Task Model
class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200))
    description = db.Column(db.String(500))
    status = db.Column(db.String(50))
    priority = db.Column(db.String(20))
    due_date = db.Column(db.String(50))


@app.route('/')
def home():
    return redirect('/register')


# Register
@app.route('/register', methods=['GET', 'POST'])
def register():

    if request.method == 'POST':

        username = request.form['username']
        password = request.form['password']

        user = User(
            username=username,
            password=password
        )

        db.session.add(user)
        db.session.commit()

        return redirect('/login')

    return render_template('register.html')


# Login
@app.route('/login', methods=['GET', 'POST'])
def login():

    if request.method == 'POST':

        username = request.form['username']
        password = request.form['password']

        user = User.query.filter_by(
            username=username,
            password=password
        ).first()

        if user:
            return redirect('/dashboard')

    return render_template('login.html')


# Dashboard
@app.route('/dashboard')
def dashboard():

    search = request.args.get('search')
    status = request.args.get('status')

    tasks = Task.query

    if search:
        tasks = tasks.filter(
            Task.title.contains(search)
        )

    if status:
        tasks = tasks.filter_by(
            status=status
        )

    tasks = tasks.all()

    return render_template(
        'dashboard.html',
        tasks=tasks
    )


# Add Task
@app.route('/add-task', methods=['GET', 'POST'])
def add_task():

    if request.method == 'POST':

        title = request.form['title']
        description = request.form['description']
        priority = request.form['priority']
        due_date = request.form['due_date']

        task = Task(
            title=title,
            description=description,
            status='Pending',
            priority=priority,
            due_date=due_date
        )

        db.session.add(task)
        db.session.commit()

        socketio.emit('task_updated')

        return redirect('/dashboard')

    return render_template('add_task.html')


# Edit Task
@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit(id):

    task = Task.query.get(id)

    if request.method == 'POST':

        task.title = request.form['title']
        task.description = request.form['description']
        task.status = request.form['status']
        task.priority = request.form['priority']
        task.due_date = request.form['due_date']

        db.session.commit()

        socketio.emit('task_updated')

        return redirect('/dashboard')

    return render_template(
        'edit_task.html',
        task=task
    )


# Delete Task
@app.route('/delete/<int:id>')
def delete(id):

    task = Task.query.get(id)

    db.session.delete(task)
    db.session.commit()

    socketio.emit('task_updated')

    return redirect('/dashboard')


# Logout
@app.route('/logout')
def logout():
    return redirect('/login')


# Create Database
with app.app_context():
    db.create_all()


if __name__ == "__main__":
    socketio.run(app, debug=True)