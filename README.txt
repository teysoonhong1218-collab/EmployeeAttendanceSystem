============================================================
  EMPLOYEE ATTENDANCE SYSTEM
  TechVenture Solutions Sdn Bhd
  TSE6223 Software Engineering Fundamentals
============================================================

SETUP INSTRUCTIONS
------------------
1. Ensure Python 3.9+ is installed on your system.

2. Open terminal/command prompt in this directory.

3. Install dependencies:
   pip install -r requirements.txt

4. Run the application:
   python app.py

5. Open a web browser and navigate to:
   http://127.0.0.1:5000

DEFAULT LOGIN CREDENTIALS
--------------------------
Admin Account:
  Email:    admin@techventure.com
  Password: admin123

HR Account:
  Email:    hr@techventure.com
  Password: hr1234

Employee Accounts (all use password: password123):
  raj@techventure.com
  meiling@techventure.com
  ali@techventure.com
  priya@techventure.com
  weijie@techventure.com
  nurul@techventure.com

SYSTEM FEATURES
----------------
1. Authentication & Authorization
   - Role-based access: Admin, HR, Employee
   - Secure password hashing
   - Session management with remember-me

2. Clock In / Clock Out
   - Real-time clock display
   - Automatic late detection (after 9:15 AM)
   - Work hours calculation

3. Employee Management (Admin/HR)
   - Add, edit, view employee profiles
   - Activate/deactivate employee accounts
   - Search and filter employees

4. Department Management (Admin/HR)
   - Create, edit, delete departments
   - View employee count per department

5. Leave Management
   - Apply for leave (annual, medical, emergency, unpaid)
   - Leave review and approval workflow (Admin/HR)
   - Status tracking (pending, approved, rejected)

6. Attendance Reports (Admin/HR)
   - Monthly attendance summary
   - Department-wise statistics
   - Per-employee attendance breakdown

7. Dashboard
   - Admin: company-wide overview with stats and charts
   - Employee: personal attendance stats and details

8. Profile Management
   - Update contact information
   - Change password

TECHNOLOGY STACK
-----------------
- Language:   Python 3
- Framework:  Flask (Web Framework)
- Database:   SQLite
- Frontend:   Bootstrap 5, Font Awesome, Chart.js
- ORM:        Flask-SQLAlchemy
- Auth:       Flask-Login
- Forms:      Flask-WTF / WTForms

PROJECT STRUCTURE
------------------
EmployeeAttendanceSystem/
  app.py              - Main application with routes
  config.py           - Configuration settings
  models.py           - Database models (Employee, Attendance, etc.)
  forms.py            - Form definitions
  requirements.txt    - Python dependencies
  attendance.db       - SQLite database (auto-generated)
  static/
    css/style.css     - Custom stylesheet
    js/main.js        - JavaScript (clock, charts)
  templates/
    base.html                - Base template with sidebar
    login.html               - Login page
    dashboard_admin.html     - Admin/HR dashboard
    dashboard_employee.html  - Employee dashboard
    attendance_list.html     - Attendance records
    employee_list.html       - Employee management
    employee_form.html       - Add/Edit employee
    employee_detail.html     - Employee profile view
    department_list.html     - Department management
    department_form.html     - Add/Edit department
    leave_list.html          - Employee leave requests
    leave_list_admin.html    - Admin leave management
    leave_form.html          - Apply for leave
    leave_review.html        - Review leave request
    reports.html             - Attendance reports
    profile.html             - User profile
    change_password.html     - Change password
