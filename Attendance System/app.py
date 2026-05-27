from flask import Flask, render_template, request, redirect, url_for, session, flash
import os
from dotenv import load_dotenv
import pymysql.cursors
from datetime import datetime

# Load environment variables from the .env file if it exists
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'your-secret-key-here')  # Use environment secret for security

# Database configuration for MySQL
# You can set these values in .env for easy local startup.
DB_NAME = os.environ.get('DB_NAME', 'attendance_system')
DB_CONFIG = {
    'host': os.environ.get('DB_HOST', 'localhost'),
    'user': os.environ.get('DB_USER', 'root'),
    'password': os.environ.get('DB_PASSWORD', 'password'),
    'db': DB_NAME,
    'charset': 'utf8mb4',
    'cursorclass': pymysql.cursors.DictCursor
}

# Helper function to connect to the database
# This function returns a new connection each time it is called.
def get_db_connection():
    return pymysql.connect(**DB_CONFIG)

# Create the application database and tables if needed
# This makes the app easier to start without manual SQL setup.
def initialize_database():
    server_config = DB_CONFIG.copy()
    server_config.pop('db', None)
    try:
        with pymysql.connect(**server_config) as connection:
            with connection.cursor() as cursor:
                cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{DB_NAME}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
            connection.commit()

        with get_db_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    'CREATE TABLE IF NOT EXISTS students ('
                    'id INT AUTO_INCREMENT PRIMARY KEY,'
                    'full_name VARCHAR(255) NOT NULL,'
                    'email VARCHAR(255) NOT NULL,'
                    'course VARCHAR(255) NOT NULL,'
                    'attendance_percentage DECIMAL(5,2) DEFAULT 0'
                    ')'
                )
                cursor.execute(
                    'CREATE TABLE IF NOT EXISTS attendance ('
                    'attendance_id INT AUTO_INCREMENT PRIMARY KEY,'
                    'student_id INT NOT NULL,'
                    'attendance_date DATE NOT NULL,'
                    'status ENUM(\'Present\', \'Absent\') NOT NULL,'
                    'FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE'
                    ')'
                )
            connection.commit()

            # Clear previous data and seed 7 realistic, common student records
            with connection.cursor() as cursor:
                cursor.execute('DELETE FROM attendance')
                cursor.execute('DELETE FROM students')
                # Reset auto-increment counters (requires appropriate privileges)
                try:
                    cursor.execute('ALTER TABLE attendance AUTO_INCREMENT = 1')
                    cursor.execute('ALTER TABLE students AUTO_INCREMENT = 1')
                except Exception:
                    # If ALTER TABLE fails (permissions), continue — IDs will still be unique
                    pass

                sample_students = [
                    ('Amit Kumar', 'amit.kumar@example.com', 'B.Com', 92.50),
                    ('Priya Sharma', 'priya.sharma@example.com', 'B.Sc', 88.75),
                    ('Rahul Verma', 'rahul.verma@example.com', 'B.A', 76.00),
                    ('Neha Singh', 'neha.singh@example.com', 'B.Tech', 83.20),
                    ('Saurabh Patel', 'saurabh.patel@example.com', 'B.E', 69.50),
                    ('Anjali Gupta', 'anjali.gupta@example.com', 'BBA', 95.00),
                    ('Vikram Rao', 'vikram.rao@example.com', 'BCA', 81.40),
                ]
                cursor.executemany(
                    'INSERT INTO students (full_name, email, course, attendance_percentage) VALUES (%s, %s, %s, %s)',
                    sample_students
                )
            connection.commit()
    except Exception as error:
        print('ERROR: Unable to initialize database for attendance_system.')
        print('Check your MySQL connection settings and credentials.')
        print(f'Connection error: {error}')
        raise

# Simple admin credentials for login
ADMIN_CREDENTIALS = {
    'username': 'admin',
    'password': 'Admin1234'
}

# Route: Landing page for the application
@app.route('/')
def index():
    return render_template('index.html')

# Route: Login page and authentication
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()

        # Basic login validation
        if username == ADMIN_CREDENTIALS['username'] and password == ADMIN_CREDENTIALS['password']:
            session['admin_logged_in'] = True
            flash('Welcome back, Admin!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password.', 'danger')
            return redirect(url_for('login'))

    return render_template('login.html')

# Decorator helper for protected routes
def login_required(route_function):
    def wrapper(*args, **kwargs):
        if not session.get('admin_logged_in'):
            flash('Please login to access this page.', 'warning')
            return redirect(url_for('login'))
        return route_function(*args, **kwargs)
    wrapper.__name__ = route_function.__name__
    return wrapper

# Route: Dashboard view with analytics metrics
@app.route('/dashboard')
@login_required
def dashboard():
    # Current date for attendance calculations
    today = datetime.now().date()

    with get_db_connection() as connection:
        with connection.cursor() as cursor:
            # Total number of students
            cursor.execute('SELECT COUNT(*) AS total_students FROM students')
            total_students = cursor.fetchone()['total_students']

            # Count present students today
            cursor.execute(
                'SELECT COUNT(*) AS present_today FROM attendance WHERE attendance_date = %s AND status = %s',
                (today, 'Present')
            )
            present_today = cursor.fetchone()['present_today']

            # Count absent students today
            cursor.execute(
                'SELECT COUNT(*) AS absent_today FROM attendance WHERE attendance_date = %s AND status = %s',
                (today, 'Absent')
            )
            absent_today = cursor.fetchone()['absent_today']

            # Calculate average attendance percentage for all students
            cursor.execute('SELECT AVG(attendance_percentage) AS average_attendance FROM students')
            average_attendance = cursor.fetchone()['average_attendance'] or 0

    return render_template(
        'dashboard.html',
        total_students=total_students,
        present_today=present_today,
        absent_today=absent_today,
        average_attendance=round(average_attendance, 2),
        today=today.strftime('%Y-%m-%d')
    )

# Route: Student management page with add/edit/delete/search
@app.route('/students', methods=['GET', 'POST'])
@login_required
def students():
    edit_student = None
    search_query = request.args.get('search', '').strip()

    with get_db_connection() as connection:
        with connection.cursor() as cursor:
            if request.method == 'POST':
                student_id = request.form.get('student_id')
                full_name = request.form.get('full_name', '').strip()
                email = request.form.get('email', '').strip()
                course = request.form.get('course', '').strip()

                # Ensure required fields are present
                if not full_name or not email or not course:
                    flash('Please fill in all student fields.', 'danger')
                    return redirect(url_for('students'))

                if student_id:
                    # Update existing student
                    cursor.execute(
                        'UPDATE students SET full_name = %s, email = %s, course = %s WHERE id = %s',
                        (full_name, email, course, student_id)
                    )
                    flash('Student updated successfully.', 'success')
                else:
                    # Add a new student record
                    cursor.execute(
                        'INSERT INTO students (full_name, email, course, attendance_percentage) VALUES (%s, %s, %s, %s)',
                        (full_name, email, course, 0)
                    )
                    flash('New student added successfully.', 'success')
                connection.commit()
                return redirect(url_for('students'))

            if 'edit_id' in request.args:
                edit_id = request.args.get('edit_id')
                cursor.execute('SELECT * FROM students WHERE id = %s', (edit_id,))
                edit_student = cursor.fetchone()

            if search_query:
                cursor.execute(
                    "SELECT * FROM students WHERE full_name LIKE %s OR email LIKE %s OR course LIKE %s ORDER BY id DESC",
                    (f'%{search_query}%', f'%{search_query}%', f'%{search_query}%')
                )
            else:
                cursor.execute('SELECT * FROM students ORDER BY id DESC')
            student_list = cursor.fetchall()

    return render_template('students.html', students=student_list, edit_student=edit_student, search_query=search_query)

# Route: Delete student record safely
@app.route('/delete_student/<int:student_id>', methods=['POST'])
@login_required
def delete_student(student_id):
    with get_db_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute('DELETE FROM attendance WHERE student_id = %s', (student_id,))
            cursor.execute('DELETE FROM students WHERE id = %s', (student_id,))
        connection.commit()
    flash('Student record deleted successfully.', 'success')
    return redirect(url_for('students'))

# Route: Attendance management page
@app.route('/attendance', methods=['GET', 'POST'])
@login_required
def attendance():
    selected_date = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
    selected_date_obj = datetime.strptime(selected_date, '%Y-%m-%d').date()
    status_map = {}
    attendance_records = []

    with get_db_connection() as connection:
        with connection.cursor() as cursor:
            if request.method == 'POST':
                attendance_date = request.form.get('attendance_date')
                attendance_date_obj = datetime.strptime(attendance_date, '%Y-%m-%d').date()
                student_ids = request.form.getlist('student_id')
                statuses = request.form.getlist('status')

                for student_id, status in zip(student_ids, statuses):
                    # Check if record exists for the student on the selected date
                    cursor.execute(
                        'SELECT attendance_id FROM attendance WHERE student_id = %s AND attendance_date = %s',
                        (student_id, attendance_date_obj)
                    )
                    existing_record = cursor.fetchone()
                    if existing_record:
                        cursor.execute(
                            'UPDATE attendance SET status = %s WHERE attendance_id = %s',
                            (status, existing_record['attendance_id'])
                        )
                    else:
                        cursor.execute(
                            'INSERT INTO attendance (student_id, attendance_date, status) VALUES (%s, %s, %s)',
                            (student_id, attendance_date_obj, status)
                        )

                # Recalculate attendance percentage for all students
                cursor.execute('SELECT id FROM students')
                all_students = cursor.fetchall()
                for student in all_students:
                    cursor.execute(
                        'SELECT COUNT(*) AS total, SUM(status = %s) AS present_count FROM attendance WHERE student_id = %s',
                        ('Present', student['id'])
                    )
                    stats = cursor.fetchone()
                    total = stats['total'] or 0
                    present_count = stats['present_count'] or 0
                    percentage = round((present_count / total) * 100, 2) if total else 0
                    cursor.execute(
                        'UPDATE students SET attendance_percentage = %s WHERE id = %s',
                        (percentage, student['id'])
                    )
                connection.commit()
                flash('Attendance saved and percentages updated.', 'success')
                return redirect(url_for('attendance', date=attendance_date))

            # Fetch student list and existing attendance for selected date
            cursor.execute('SELECT * FROM students ORDER BY full_name ASC')
            student_list = cursor.fetchall()
            cursor.execute(
                'SELECT student_id, status FROM attendance WHERE attendance_date = %s',
                (selected_date_obj,)
            )
            attendance_today = cursor.fetchall()
            status_map = {row['student_id']: row['status'] for row in attendance_today}

            for student in student_list:
                attendance_records.append({
                    'student': student,
                    'status': status_map.get(student['id'], 'Absent')
                })

            # Attendance summary for statistics
            cursor.execute(
                'SELECT status, COUNT(*) AS count FROM attendance WHERE attendance_date = %s GROUP BY status',
                (selected_date_obj,)
            )
            summary = cursor.fetchall()
            present_count = next((row['count'] for row in summary if row['status'] == 'Present'), 0)
            absent_count = next((row['count'] for row in summary if row['status'] == 'Absent'), 0)

    return render_template(
        'attendance.html',
        attendance_records=attendance_records,
        selected_date=selected_date_obj.strftime('%Y-%m-%d'),
        present_count=present_count,
        absent_count=absent_count
    )

# Route: Logout admin session
@app.route('/logout')
def logout():
    session.pop('admin_logged_in', None)
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('login'))

# Main runner for development mode
if __name__ == '__main__':
    initialize_database()  # Create database and tables automatically if they are missing
    app.run(debug=True)
