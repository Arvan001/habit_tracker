import os
import csv
import json
from datetime import datetime, date, timedelta
from io import StringIO, TextIOWrapper
from functools import wraps

from flask import Flask, render_template, request, jsonify, session, redirect, url_for, send_file
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import func

# Inisialisasi Flask
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key-here-change-in-production')

# Konfigurasi database untuk Windows
db_path = os.path.join(os.path.dirname(__file__), 'database')
os.makedirs(db_path, exist_ok=True)
sqlite_db_path = os.path.join(db_path, 'habits.db')
database_url = f'sqlite:///{sqlite_db_path}'

app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', database_url).replace('postgres://', 'postgresql://')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'connect_args': {'check_same_thread': False}
}

db = SQLAlchemy(app)

# ==================== MODELS ====================

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    full_name = db.Column(db.String(120), default='')
    dark_mode = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    tasks = db.relationship('Task', backref='user', lazy=True, cascade='all, delete-orphan')
    time_logs = db.relationship('TimeLog', backref='user', lazy=True, cascade='all, delete-orphan')
    routines = db.relationship('Routine', backref='user', lazy=True, cascade='all, delete-orphan')
    completions = db.relationship('TaskCompletion', backref='user', lazy=True, cascade='all, delete-orphan')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50), default='Custom')
    custom_category = db.Column(db.String(50))
    is_active = db.Column(db.Boolean, default=True)
    order_index = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class TaskCompletion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    task_id = db.Column(db.Integer, db.ForeignKey('task.id'), nullable=False)
    date = db.Column(db.Date, nullable=False, default=date.today)
    completed = db.Column(db.Boolean, default=False)

    task = db.relationship('Task')

class TimeLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    task_id = db.Column(db.Integer, db.ForeignKey('task.id'), nullable=True)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=True)
    duration_seconds = db.Column(db.Integer, default=0)

    task = db.relationship('Task')

class Routine(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50))
    start_time = db.Column(db.String(5), nullable=False)
    end_time = db.Column(db.String(5), nullable=False)
    days_of_week = db.Column(db.String(20), default='1,2,3,4,5')
    is_daily = db.Column(db.Boolean, default=True)
    is_active = db.Column(db.Boolean, default=True)

# ==================== HELPER FUNCTIONS ====================

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            if request.is_json:
                return jsonify({'error': 'Unauthorized - Please login first'}), 401
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def get_current_user():
    if 'user_id' in session:
        return User.query.get(session['user_id'])
    return None

# ==================== ROUTES HTML ====================

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login')
def login():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return render_template('login.html')

@app.route('/register')
def register():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return render_template('register.html')

@app.route('/dashboard')
@login_required
def dashboard():
    user = get_current_user()
    return render_template('dashboard.html', user=user)

@app.route('/settings')
@login_required
def settings():
    user = get_current_user()
    return render_template('settings.html', user=user)

# ==================== API AUTH ====================

@app.route('/api/register', methods=['POST'])
def api_register():
    try:
        data = request.json
        username = data.get('username', '').strip()
        password = data.get('password', '')
        full_name = data.get('full_name', '')

        if not username or not password:
            return jsonify({'error': 'Username dan password wajib diisi'}), 400

        if len(username) < 3:
            return jsonify({'error': 'Username minimal 3 karakter'}), 400

        if len(password) < 4:
            return jsonify({'error': 'Password minimal 4 karakter'}), 400

        if User.query.filter_by(username=username).first():
            return jsonify({'error': 'Username sudah terdaftar'}), 400

        user = User(username=username, full_name=full_name)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        return jsonify({'message': 'Registrasi berhasil! Silakan login.'}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/login', methods=['POST'])
def api_login():
    try:
        data = request.json
        username = data.get('username', '').strip()
        password = data.get('password', '')

        user = User.query.filter_by(username=username).first()
        if not user or not user.check_password(password):
            return jsonify({'error': 'Username atau password salah'}), 401

        session.clear()
        session['user_id'] = user.id
        session.permanent = True

        return jsonify({
            'message': 'Login sukses',
            'dark_mode': user.dark_mode,
            'username': user.username
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/logout', methods=['POST'])
@login_required
def api_logout():
    session.clear()
    return jsonify({'message': 'Logout sukses'}), 200

@app.route('/api/check-auth', methods=['GET'])
def check_auth():
    if 'user_id' in session:
        user = User.query.get(session['user_id'])
        if user:
            return jsonify({'authenticated': True, 'username': user.username}), 200
    return jsonify({'authenticated': False}), 200

@app.route('/api/user/profile', methods=['GET', 'PUT'])
@login_required
def api_profile():
    user = get_current_user()
    if request.method == 'GET':
        return jsonify({
            'id': user.id,
            'username': user.username,
            'full_name': user.full_name or '',
            'dark_mode': user.dark_mode
        })
    else:
        try:
            data = request.json
            if 'full_name' in data:
                user.full_name = data['full_name']
            if 'dark_mode' in data:
                user.dark_mode = data['dark_mode']
                # Update HTML class untuk dark mode
            db.session.commit()
            return jsonify({'message': 'Profil berhasil diperbarui'}), 200
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': str(e)}), 500

# ==================== API TASKS ====================

@app.route('/api/tasks', methods=['GET', 'POST'])
@login_required
def api_tasks():
    user = get_current_user()
    if request.method == 'GET':
        tasks = Task.query.filter_by(user_id=user.id, is_active=True).order_by(Task.order_index).all()
        today = date.today()
        completions = {c.task_id: c.completed for c in TaskCompletion.query.filter_by(user_id=user.id, date=today).all()}
        return jsonify([{
            'id': t.id,
            'name': t.name,
            'category': t.category,
            'custom_category': t.custom_category,
            'completed': completions.get(t.id, False),
            'order_index': t.order_index
        } for t in tasks])
    else:
        try:
            data = request.json
            name = data.get('name', '').strip()
            if not name:
                return jsonify({'error': 'Nama task wajib diisi'}), 400

            task = Task(
                user_id=user.id,
                name=name,
                category=data.get('category', 'Custom'),
                custom_category=data.get('custom_category'),
                order_index=data.get('order_index', 0)
            )
            db.session.add(task)
            db.session.commit()
            return jsonify({'id': task.id, 'message': 'Task berhasil ditambahkan'}), 201
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': str(e)}), 500

@app.route('/api/tasks/<int:task_id>', methods=['PUT', 'DELETE'])
@login_required
def api_task_detail(task_id):
    user = get_current_user()
    task = Task.query.filter_by(id=task_id, user_id=user.id).first()
    if not task:
        return jsonify({'error': 'Task tidak ditemukan'}), 404

    if request.method == 'PUT':
        try:
            data = request.json
            if 'name' in data and data['name'].strip():
                task.name = data['name'].strip()
            if 'category' in data:
                task.category = data['category']
            if 'custom_category' in data:
                task.custom_category = data['custom_category']
            if 'order_index' in data:
                task.order_index = data['order_index']
            db.session.commit()
            return jsonify({'message': 'Task berhasil diperbarui'})
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': str(e)}), 500
    else:
        try:
            # Hapus juga completions terkait
            TaskCompletion.query.filter_by(task_id=task_id).delete()
            db.session.delete(task)
            db.session.commit()
            return jsonify({'message': 'Task berhasil dihapus'})
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': str(e)}), 500

@app.route('/api/tasks/<int:task_id>/toggle', methods=['POST'])
@login_required
def api_toggle_task(task_id):
    user = get_current_user()
    today = date.today()
    
    completion = TaskCompletion.query.filter_by(user_id=user.id, task_id=task_id, date=today).first()
    if completion:
        completion.completed = not completion.completed
    else:
        completion = TaskCompletion(user_id=user.id, task_id=task_id, date=today, completed=True)
        db.session.add(completion)
    
    db.session.commit()
    return jsonify({'completed': completion.completed})

# ==================== API TIME TRACKER ====================

@app.route('/api/time-tracker/start', methods=['POST'])
@login_required
def api_start_timer():
    user = get_current_user()
    data = request.json
    task_id = data.get('task_id')
    
    # Cek apakah ada timer yang sedang berjalan
    active = TimeLog.query.filter_by(user_id=user.id, end_time=None).first()
    if active:
        return jsonify({'error': 'Timer sedang berjalan. Stop terlebih dahulu.'}), 400
    
    time_log = TimeLog(
        user_id=user.id,
        task_id=task_id if task_id else None,
        start_time=datetime.utcnow()
    )
    db.session.add(time_log)
    db.session.commit()
    
    return jsonify({
        'id': time_log.id,
        'start_time': time_log.start_time.isoformat()
    })

@app.route('/api/time-tracker/stop', methods=['POST'])
@login_required
def api_stop_timer():
    user = get_current_user()
    active = TimeLog.query.filter_by(user_id=user.id, end_time=None).first()
    if not active:
        return jsonify({'error': 'Tidak ada timer yang sedang berjalan'}), 400
    
    active.end_time = datetime.utcnow()
    active.duration_seconds = int((active.end_time - active.start_time).total_seconds())
    db.session.commit()
    
    return jsonify({
        'duration_seconds': active.duration_seconds,
        'task_id': active.task_id
    })

@app.route('/api/time-tracker/status', methods=['GET'])
@login_required
def api_timer_status():
    user = get_current_user()
    active = TimeLog.query.filter_by(user_id=user.id, end_time=None).first()
    if active:
        elapsed = int((datetime.utcnow() - active.start_time).total_seconds())
        return jsonify({
            'running': True,
            'start_time': active.start_time.isoformat(),
            'elapsed': elapsed,
            'task_id': active.task_id
        })
    return jsonify({'running': False})

# ==================== API STATISTICS ====================

@app.route('/api/stats/dashboard', methods=['GET'])
@login_required
def api_dashboard_stats():
    user = get_current_user()
    today = date.today()
    start_of_week = today - timedelta(days=today.weekday())
    start_of_month = today.replace(day=1)
    
    # Total jam hari ini
    today_logs = TimeLog.query.filter_by(user_id=user.id).filter(
        func.date(TimeLog.start_time) == today
    ).all()
    hours_today = sum(log.duration_seconds for log in today_logs if log.duration_seconds) / 3600
    
    # Progress harian
    total_tasks = Task.query.filter_by(user_id=user.id, is_active=True).count()
    completed_today = TaskCompletion.query.filter_by(user_id=user.id, date=today, completed=True).count()
    daily_progress = (completed_today / total_tasks * 100) if total_tasks > 0 else 0
    
    # Total jam mingguan
    week_logs = TimeLog.query.filter_by(user_id=user.id).filter(
        func.date(TimeLog.start_time) >= start_of_week
    ).all()
    hours_week = sum(log.duration_seconds for log in week_logs if log.duration_seconds) / 3600
    
    # Total jam bulanan
    month_logs = TimeLog.query.filter_by(user_id=user.id).filter(
        func.date(TimeLog.start_time) >= start_of_month
    ).all()
    hours_month = sum(log.duration_seconds for log in month_logs if log.duration_seconds) / 3600
    
    # Streak
    streak = calculate_streak(user.id)
    
    return jsonify({
        'hours_today': round(hours_today, 2),
        'daily_progress': round(daily_progress, 2),
        'hours_week': round(hours_week, 2),
        'hours_month': round(hours_month, 2),
        'streak': streak,
        'total_tasks': total_tasks,
        'completed_tasks': completed_today
    })

def calculate_streak(user_id):
    """Hitung berapa hari berturut-turut user menyelesaikan minimal 1 task"""
    completions = db.session.query(
        TaskCompletion.date
    ).filter_by(
        user_id=user_id, 
        completed=True
    ).distinct().order_by(TaskCompletion.date.desc()).all()
    
    if not completions:
        return 0
    
    streak = 0
    current_date = date.today()
    
    for comp in completions:
        if comp[0] == current_date:
            streak += 1
            current_date -= timedelta(days=1)
        else:
            break
    
    return streak

@app.route('/api/stats/charts', methods=['GET'])
@login_required
def api_charts_data():
    user = get_current_user()
    today = date.today()
    last_7_days = [(today - timedelta(days=i)).strftime('%Y-%m-%d') for i in range(6, -1, -1)]
    last_7_labels = [(today - timedelta(days=i)).strftime('%a') for i in range(6, -1, -1)]
    
    hours_per_day = []
    tasks_per_week = []
    
    for day in last_7_days:
        day_date = datetime.strptime(day, '%Y-%m-%d').date()
        logs = TimeLog.query.filter_by(user_id=user.id).filter(func.date(TimeLog.start_time) == day_date).all()
        hours = sum(l.duration_seconds for l in logs if l.duration_seconds) / 3600
        hours_per_day.append(round(hours, 2))
        
        completed = TaskCompletion.query.filter_by(user_id=user.id, date=day_date, completed=True).count()
        tasks_per_week.append(completed)
    
    return jsonify({
        'labels': last_7_labels,
        'dates': last_7_days,
        'hours_per_day': hours_per_day,
        'tasks_per_week': tasks_per_week
    })

# ==================== API CALENDAR ====================

@app.route('/api/calendar/data', methods=['GET'])
@login_required
def api_calendar_data():
    user = get_current_user()
    year = int(request.args.get('year', date.today().year))
    month = int(request.args.get('month', date.today().month))
    
    start_date = date(year, month, 1)
    if month == 12:
        end_date = date(year+1, 1, 1) - timedelta(days=1)
    else:
        end_date = date(year, month+1, 1) - timedelta(days=1)
    
    logs = db.session.query(
        func.date(TimeLog.start_time).label('log_date'),
        func.sum(TimeLog.duration_seconds).label('total_seconds')
    ).filter(
        TimeLog.user_id == user.id,
        func.date(TimeLog.start_time) >= start_date,
        func.date(TimeLog.start_time) <= end_date
    ).group_by('log_date').all()
    
    data = {}
    for log in logs:
        data[log.log_date] = round(log.total_seconds / 3600, 2)
    
    return jsonify({'data': data, 'year': year, 'month': month})

# ==================== API ROUTINES ====================

@app.route('/api/routines', methods=['GET', 'POST'])
@login_required
def api_routines():
    user = get_current_user()
    if request.method == 'GET':
        routines = Routine.query.filter_by(user_id=user.id, is_active=True).all()
        return jsonify([{
            'id': r.id,
            'name': r.name,
            'category': r.category or 'Umum',
            'start_time': r.start_time,
            'end_time': r.end_time,
            'days_of_week': r.days_of_week,
            'is_daily': r.is_daily
        } for r in routines])
    else:
        try:
            data = request.json
            routine = Routine(
                user_id=user.id,
                name=data['name'],
                category=data.get('category', 'Umum'),
                start_time=data['start_time'],
                end_time=data['end_time'],
                days_of_week=data.get('days_of_week', '1,2,3,4,5'),
                is_daily=data.get('is_daily', True)
            )
            db.session.add(routine)
            db.session.commit()
            return jsonify({'id': routine.id, 'message': 'Rutinitas berhasil ditambahkan'}), 201
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': str(e)}), 500

@app.route('/api/routines/<int:routine_id>', methods=['PUT', 'DELETE'])
@login_required
def api_routine_detail(routine_id):
    user = get_current_user()
    routine = Routine.query.filter_by(id=routine_id, user_id=user.id).first()
    if not routine:
        return jsonify({'error': 'Rutinitas tidak ditemukan'}), 404
    
    if request.method == 'PUT':
        try:
            data = request.json
            routine.name = data.get('name', routine.name)
            routine.category = data.get('category', routine.category)
            routine.start_time = data.get('start_time', routine.start_time)
            routine.end_time = data.get('end_time', routine.end_time)
            routine.days_of_week = data.get('days_of_week', routine.days_of_week)
            routine.is_daily = data.get('is_daily', routine.is_daily)
            db.session.commit()
            return jsonify({'message': 'Rutinitas berhasil diperbarui'})
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': str(e)}), 500
    else:
        try:
            db.session.delete(routine)
            db.session.commit()
            return jsonify({'message': 'Rutinitas berhasil dihapus'})
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': str(e)}), 500

# ==================== API SETTINGS ====================

@app.route('/api/export/csv', methods=['GET'])
@login_required
def api_export_csv():
    user = get_current_user()
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(['Type', 'ID', 'Name', 'Category', 'Date', 'Completed', 'Duration (Hours)', 'Start Time', 'End Time'])
    
    # Tasks
    tasks = Task.query.filter_by(user_id=user.id).all()
    for t in tasks:
        writer.writerow(['Task', t.id, t.name, t.category, '', '', '', '', ''])
    
    # Task Completions
    completions = TaskCompletion.query.filter_by(user_id=user.id).all()
    for c in completions:
        writer.writerow(['Completion', c.id, '', '', c.date, 'Yes' if c.completed else 'No', '', '', ''])
    
    # Time Logs
    logs = TimeLog.query.filter_by(user_id=user.id).all()
    for l in logs:
        duration_hours = round(l.duration_seconds / 3600, 2) if l.duration_seconds else 0
        writer.writerow(['TimeLog', l.id, '', '', '', '', duration_hours, l.start_time, l.end_time])
    
    # Routines
    routines = Routine.query.filter_by(user_id=user.id).all()
    for r in routines:
        writer.writerow(['Routine', r.id, r.name, r.category, '', '', '', r.start_time, r.end_time])
    
    output.seek(0)
    return send_file(
        StringIO(output.getvalue()),
        mimetype='text/csv',
        as_attachment=True,
        download_name=f'habit_tracker_export_{user.username}_{date.today()}.csv'
    )

@app.route('/api/import/csv', methods=['POST'])
@login_required
def api_import_csv():
    if 'file' not in request.files:
        return jsonify({'error': 'Tidak ada file yang diupload'}), 400
    
    file = request.files['file']
    if not file.filename.endswith('.csv'):
        return jsonify({'error': 'Hanya file CSV yang didukung'}), 400
    
    try:
        stream = TextIOWrapper(file.stream, encoding='utf-8')
        reader = csv.reader(stream)
        next(reader)  # Skip header
        
        imported_count = 0
        for row in reader:
            if len(row) < 3:
                continue
            if row[0] == 'Task' and len(row) >= 4:
                # Cek apakah task sudah ada
                existing = Task.query.filter_by(user_id=get_current_user().id, name=row[2]).first()
                if not existing:
                    task = Task(
                        user_id=get_current_user().id,
                        name=row[2],
                        category=row[3] if row[3] else 'Custom'
                    )
                    db.session.add(task)
                    imported_count += 1
        
        db.session.commit()
        return jsonify({'message': f'Import berhasil! {imported_count} data diimport.'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/reset-data', methods=['POST'])
@login_required
def api_reset_data():
    user = get_current_user()
    try:
        TaskCompletion.query.filter_by(user_id=user.id).delete()
        TimeLog.query.filter_by(user_id=user.id).delete()
        Routine.query.filter_by(user_id=user.id).delete()
        Task.query.filter_by(user_id=user.id).delete()
        db.session.commit()
        return jsonify({'message': 'Semua data berhasil direset'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# ==================== CREATE DATABASE ====================

with app.app_context():
    db.create_all()
    print(f"✅ Database created at: {sqlite_db_path}")
    print(f"✅ Server running at http://localhost:5000")

# ==================== RUN APP ====================

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)