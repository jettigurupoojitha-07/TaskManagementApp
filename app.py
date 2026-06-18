from flask import Flask, render_template, request, redirect
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO
import os

# ---------------- APP SETUP ----------------
app = Flask(__name__)

app.config['SECRET_KEY'] = 'secret123'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tasks.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
socketio = SocketIO(app, cors_allowed_origins="*")

# ---------------- MODELS ----------------
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False)
    password = db.Column(db.String(100), nullable=False)

class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.String(500))
    status = db.Column(db.String(50))
    priority = db.Column(db.String(20))
    due_date = db.Column(db.String(50))

# ---------------- ROUTES ----------------
@app.route('/')
def home():
    return redirect('/register')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        user = User(
            username=request.form['username'],
            password=request.form['password']
        )
        db.session.add(user)
        db.session.commit()
        return redirect('/login')

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(
            username=request.form['username'],
            password=request.form['password']
        ).first()

        if user:
            return redirect('/dashboard')

    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    search = request.args.get('search')
    status = request.args.get('status')

    tasks = Task.query

    if search:
        tasks = tasks.filter(Task.title.contains(search))

    if status:
        tasks = tasks.filter_by(status=status)

    tasks = tasks.all()

    return render_template('dashboard.html', tasks=tasks)

@app.route('/add-task', methods=['GET', 'POST'])
def add_task():
    if request.method == 'POST':
        task = Task(
            title=request.form['title'],
            description=request.form['description'],
            status='Pending',
            priority=request.form['priority'],
            due_date=request.form['due_date']
        )

        db.session.add(task)
        db.session.commit()

        socketio.emit('task_updated')

        return redirect('/dashboard')

    return render_template('add_task.html')

@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit(id):
    task = Task.query.get_or_404(id)

    if request.method == 'POST':
        task.title = request.form['title']
        task.description = request.form['description']
        task.status = request.form['status']
        task.priority = request.form['priority']
        task.due_date = request.form['due_date']

        db.session.commit()
        socketio.emit('task_updated')

        return redirect('/dashboard')

    return render_template('edit_task.html', task=task)

@app.route('/delete/<int:id>')
def delete(id):
    task = Task.query.get_or_404(id)

    db.session.delete(task)
    db.session.commit()

    socketio.emit('task_updated')

    return redirect('/dashboard')

@app.route('/logout')
def logout():
    return redirect('/login')

# ---------------- CREATE DB ----------------
with app.app_context():
    db.create_all()

# ---------------- RENDER FIX (IMPORTANT) ----------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    socketio.run(app, host="0.0.0.0", port=port, debug=False)