# Attendance Management System

This is a beginner-friendly full-stack attendance management system built with Flask, MySQL, HTML, CSS, and JavaScript.

## Features

- Admin login and session handling
- Dashboard with attendance analytics
- Student CRUD operations
- Attendance marking by date
- Automatic attendance percentage calculation
- Responsive dark UI with glassmorphism style
- MySQL database initialization support

## Setup

1. Create and activate the virtual environment (already configured here):

```powershell
cd "c:\Users\Harsh\OneDrive\Desktop\Attendance System"
.venv\Scripts\Activate.ps1
```

2. Install dependencies:

```powershell
python -m pip install -r requirements.txt
```

3. Configure your MySQL credentials.

The easiest way is to create a `.env` file once from `.env.example`:

```powershell
copy .env.example .env
notepad .env
```

Then update the values inside `.env` with your MySQL settings.

4. Run the app:

```powershell
python app.py
```

Or use the helper batch file so you don't need to set anything manually:

```powershell
run_app.bat
```

5. Open your browser at `http://127.0.0.1:5000`

## Demo Login

- Username: `admin`
- Password: `Admin1234`

## Database Initialization

The app includes `initialize_database()` on startup. It will automatically create:

- database: `attendance_system`
- table: `students`
- table: `attendance`

> Note: Your MySQL user must have permission to create databases and tables.

## Troubleshooting

If you see an access denied error, verify your MySQL username and password.

If you see an authentication plugin error, make sure `cryptography` is installed and your MySQL server supports the connection method.
