from datetime import datetime, date, timezone, timedelta

MYT = timezone(timedelta(hours=8))
from functools import wraps

from flask import Flask, render_template, redirect, url_for, flash, request, jsonify
from flask_login import (
    LoginManager, login_user, logout_user, login_required, current_user,
)

from config import Config
from models import db, Department, Employee, Attendance, LeaveRequest
from forms import (
    LoginForm, EmployeeForm, DepartmentForm, LeaveRequestForm,
    LeaveReviewForm, ChangePasswordForm, ProfileForm,
)

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"
login_manager.login_message_category = "warning"


@login_manager.user_loader
def load_user(user_id):
    return Employee.query.get(int(user_id))


def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if current_user.role not in ("admin", "hr"):
            flash("Access denied. Admin or HR privileges required.", "danger")
            return redirect(url_for("dashboard"))
        return f(*args, **kwargs)
    return decorated


# ── Authentication ──────────────────────────────────────────────

@app.route("/")
def index():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))
    form = LoginForm()
    if form.validate_on_submit():
        employee = Employee.query.filter_by(email=form.email.data).first()
        if employee and employee.check_password(form.password.data):
            if not employee.is_active:
                flash("Your account has been deactivated. Contact HR.", "danger")
                return render_template("login.html", form=form)
            login_user(employee, remember=form.remember.data)
            flash(f"Welcome back, {employee.first_name}!", "success")
            return redirect(url_for("dashboard"))
        flash("Invalid email or password.", "danger")
    return render_template("login.html", form=form)


@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("login"))


# ── Dashboard ───────────────────────────────────────────────────

@app.route("/dashboard")
@login_required
def dashboard():
    today = date.today()
    today_attendance = current_user.get_today_attendance()
    monthly_stats = current_user.get_monthly_stats()

    if current_user.role in ("admin", "hr"):
        total_employees = Employee.query.filter_by(is_active=True).count()
        today_present = Attendance.query.filter(
            Attendance.date == today,
            Attendance.status.in_(["present", "late"]),
        ).count()
        today_late = Attendance.query.filter_by(date=today, status="late").count()
        pending_leaves = LeaveRequest.query.filter_by(status="pending").count()
        recent_attendance = (
            Attendance.query.filter_by(date=today)
            .join(Employee)
            .order_by(Attendance.clock_in.desc())
            .limit(10)
            .all()
        )
        return render_template(
            "dashboard_admin.html",
            today_attendance=today_attendance,
            monthly_stats=monthly_stats,
            total_employees=total_employees,
            today_present=today_present,
            today_late=today_late,
            pending_leaves=pending_leaves,
            recent_attendance=recent_attendance,
            today=today,
        )

    pending_leaves = LeaveRequest.query.filter_by(
        employee_id=current_user.id, status="pending"
    ).count()
    return render_template(
        "dashboard_employee.html",
        today_attendance=today_attendance,
        monthly_stats=monthly_stats,
        pending_leaves=pending_leaves,
        today=today,
    )


# ── Clock In / Out ──────────────────────────────────────────────

@app.route("/clock-in", methods=["POST"])
@login_required
def clock_in():
    today = date.today()
    existing = Attendance.query.filter_by(
        employee_id=current_user.id, date=today
    ).first()

    if existing and existing.clock_in:
        flash("You have already clocked in today.", "warning")
        return redirect(url_for("dashboard"))

    now = datetime.now(MYT).replace(tzinfo=None)
    work_start = now.replace(
        hour=app.config["WORK_START_HOUR"],
        minute=app.config["LATE_THRESHOLD_MINUTES"],
        second=0,
        microsecond=0,
    )
    status = "late" if now > work_start else "present"

    if existing:
        existing.clock_in = now
        existing.status = status
    else:
        record = Attendance(
            employee_id=current_user.id,
            date=today,
            clock_in=now,
            status=status,
        )
        db.session.add(record)

    db.session.commit()
    if status == "late":
        flash("Clocked in — you are marked as late.", "warning")
    else:
        flash("Clocked in successfully!", "success")
    return redirect(url_for("dashboard"))


@app.route("/clock-out", methods=["POST"])
@login_required
def clock_out():
    today = date.today()
    record = Attendance.query.filter_by(
        employee_id=current_user.id, date=today
    ).first()

    if not record or not record.clock_in:
        flash("You haven't clocked in today.", "warning")
        return redirect(url_for("dashboard"))
    if record.clock_out:
        flash("You have already clocked out today.", "warning")
        return redirect(url_for("dashboard"))

    record.clock_out = datetime.now(MYT).replace(tzinfo=None)
    record.calculate_work_hours()
    db.session.commit()
    flash(
        f"Clocked out. You worked {record.work_hours:.1f} hours today.",
        "success",
    )
    return redirect(url_for("dashboard"))


# ── Attendance Records ──────────────────────────────────────────

@app.route("/attendance")
@login_required
def attendance_list():
    page = request.args.get("page", 1, type=int)
    month = request.args.get("month", date.today().month, type=int)
    year = request.args.get("year", date.today().year, type=int)

    if current_user.role in ("admin", "hr"):
        query = (
            Attendance.query.join(Employee)
            .filter(
                db.extract("month", Attendance.date) == month,
                db.extract("year", Attendance.date) == year,
            )
            .order_by(Attendance.date.desc(), Employee.first_name)
        )
    else:
        query = (
            Attendance.query.filter_by(employee_id=current_user.id)
            .filter(
                db.extract("month", Attendance.date) == month,
                db.extract("year", Attendance.date) == year,
            )
            .order_by(Attendance.date.desc())
        )

    records = query.paginate(page=page, per_page=20, error_out=False)
    return render_template(
        "attendance_list.html",
        records=records,
        month=month,
        year=year,
    )


# ── Employee Management (Admin/HR) ─────────────────────────────

@app.route("/employees")
@login_required
@admin_required
def employee_list():
    page = request.args.get("page", 1, type=int)
    search = request.args.get("search", "")
    query = Employee.query
    if search:
        query = query.filter(
            db.or_(
                Employee.first_name.ilike(f"%{search}%"),
                Employee.last_name.ilike(f"%{search}%"),
                Employee.employee_id.ilike(f"%{search}%"),
            )
        )
    employees = query.order_by(Employee.first_name).paginate(
        page=page, per_page=15, error_out=False
    )
    return render_template(
        "employee_list.html", employees=employees, search=search
    )


@app.route("/employees/add", methods=["GET", "POST"])
@login_required
@admin_required
def employee_add():
    form = EmployeeForm()
    form.department_id.choices = [
        (d.id, d.name) for d in Department.query.order_by(Department.name).all()
    ]
    if form.validate_on_submit():
        if Employee.query.filter_by(email=form.email.data).first():
            flash("Email already registered.", "danger")
            return render_template("employee_form.html", form=form, title="Add Employee")
        if Employee.query.filter_by(employee_id=form.employee_id.data).first():
            flash("Employee ID already exists.", "danger")
            return render_template("employee_form.html", form=form, title="Add Employee")
        emp = Employee(
            employee_id=form.employee_id.data,
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            email=form.email.data,
            phone=form.phone.data,
            position=form.position.data,
            department_id=form.department_id.data,
            role=form.role.data,
        )
        emp.set_password(form.password.data or "password123")
        db.session.add(emp)
        db.session.commit()
        flash(f"Employee {emp.full_name} added successfully.", "success")
        return redirect(url_for("employee_list"))
    return render_template("employee_form.html", form=form, title="Add Employee")


@app.route("/employees/<int:emp_id>/edit", methods=["GET", "POST"])
@login_required
@admin_required
def employee_edit(emp_id):
    emp = Employee.query.get_or_404(emp_id)
    form = EmployeeForm(obj=emp)
    form.department_id.choices = [
        (d.id, d.name) for d in Department.query.order_by(Department.name).all()
    ]
    if form.validate_on_submit():
        existing_email = Employee.query.filter(
            Employee.email == form.email.data, Employee.id != emp_id
        ).first()
        if existing_email:
            flash("Email already in use by another employee.", "danger")
            return render_template("employee_form.html", form=form, title="Edit Employee")
        emp.employee_id = form.employee_id.data
        emp.first_name = form.first_name.data
        emp.last_name = form.last_name.data
        emp.email = form.email.data
        emp.phone = form.phone.data
        emp.position = form.position.data
        emp.department_id = form.department_id.data
        emp.role = form.role.data
        if form.password.data:
            emp.set_password(form.password.data)
        db.session.commit()
        flash(f"Employee {emp.full_name} updated.", "success")
        return redirect(url_for("employee_list"))
    return render_template("employee_form.html", form=form, title="Edit Employee")


@app.route("/employees/<int:emp_id>/toggle", methods=["POST"])
@login_required
@admin_required
def employee_toggle(emp_id):
    emp = Employee.query.get_or_404(emp_id)
    if emp.id == current_user.id:
        flash("You cannot deactivate your own account.", "danger")
        return redirect(url_for("employee_list"))
    emp.is_active = not emp.is_active
    db.session.commit()
    status = "activated" if emp.is_active else "deactivated"
    flash(f"Employee {emp.full_name} has been {status}.", "info")
    return redirect(url_for("employee_list"))


@app.route("/employees/<int:emp_id>")
@login_required
@admin_required
def employee_detail(emp_id):
    emp = Employee.query.get_or_404(emp_id)
    monthly_stats = emp.get_monthly_stats()
    recent_attendance = (
        Attendance.query.filter_by(employee_id=emp_id)
        .order_by(Attendance.date.desc())
        .limit(30)
        .all()
    )
    return render_template(
        "employee_detail.html",
        emp=emp,
        monthly_stats=monthly_stats,
        recent_attendance=recent_attendance,
    )


# ── Department Management ───────────────────────────────────────

@app.route("/departments")
@login_required
@admin_required
def department_list():
    departments = Department.query.order_by(Department.name).all()
    return render_template("department_list.html", departments=departments)


@app.route("/departments/add", methods=["GET", "POST"])
@login_required
@admin_required
def department_add():
    form = DepartmentForm()
    if form.validate_on_submit():
        if Department.query.filter_by(name=form.name.data).first():
            flash("Department already exists.", "danger")
            return render_template(
                "department_form.html", form=form, title="Add Department"
            )
        dept = Department(name=form.name.data, description=form.description.data)
        db.session.add(dept)
        db.session.commit()
        flash(f"Department '{dept.name}' created.", "success")
        return redirect(url_for("department_list"))
    return render_template(
        "department_form.html", form=form, title="Add Department"
    )


@app.route("/departments/<int:dept_id>/edit", methods=["GET", "POST"])
@login_required
@admin_required
def department_edit(dept_id):
    dept = Department.query.get_or_404(dept_id)
    form = DepartmentForm(obj=dept)
    if form.validate_on_submit():
        existing = Department.query.filter(
            Department.name == form.name.data, Department.id != dept_id
        ).first()
        if existing:
            flash("Department name already in use.", "danger")
            return render_template(
                "department_form.html", form=form, title="Edit Department"
            )
        dept.name = form.name.data
        dept.description = form.description.data
        db.session.commit()
        flash(f"Department '{dept.name}' updated.", "success")
        return redirect(url_for("department_list"))
    return render_template(
        "department_form.html", form=form, title="Edit Department"
    )


@app.route("/departments/<int:dept_id>/delete", methods=["POST"])
@login_required
@admin_required
def department_delete(dept_id):
    dept = Department.query.get_or_404(dept_id)
    if dept.employees:
        flash("Cannot delete department with assigned employees.", "danger")
        return redirect(url_for("department_list"))
    db.session.delete(dept)
    db.session.commit()
    flash(f"Department '{dept.name}' deleted.", "success")
    return redirect(url_for("department_list"))


# ── Leave Management ────────────────────────────────────────────

@app.route("/leave")
@login_required
def leave_list():
    page = request.args.get("page", 1, type=int)

    if current_user.role in ("admin", "hr"):
        status_filter = request.args.get("status", "all")
        query = LeaveRequest.query.join(Employee, LeaveRequest.employee_id == Employee.id)
        if status_filter != "all":
            query = query.filter(LeaveRequest.status == status_filter)
        leaves = query.order_by(LeaveRequest.created_at.desc()).paginate(
            page=page, per_page=15, error_out=False
        )
        return render_template(
            "leave_list_admin.html",
            leaves=leaves,
            status_filter=status_filter,
        )

    leaves = (
        LeaveRequest.query.filter_by(employee_id=current_user.id)
        .order_by(LeaveRequest.created_at.desc())
        .paginate(page=page, per_page=15, error_out=False)
    )
    return render_template("leave_list.html", leaves=leaves)


@app.route("/leave/apply", methods=["GET", "POST"])
@login_required
def leave_apply():
    form = LeaveRequestForm()
    if form.validate_on_submit():
        if form.end_date.data < form.start_date.data:
            flash("End date cannot be before start date.", "danger")
            return render_template("leave_form.html", form=form)
        leave = LeaveRequest(
            employee_id=current_user.id,
            leave_type=form.leave_type.data,
            start_date=form.start_date.data,
            end_date=form.end_date.data,
            reason=form.reason.data,
        )
        db.session.add(leave)
        db.session.commit()
        flash("Leave request submitted successfully.", "success")
        return redirect(url_for("leave_list"))
    return render_template("leave_form.html", form=form)


@app.route("/leave/<int:leave_id>/review", methods=["GET", "POST"])
@login_required
@admin_required
def leave_review(leave_id):
    leave = LeaveRequest.query.get_or_404(leave_id)
    if leave.status != "pending":
        flash("This leave request has already been reviewed.", "warning")
        return redirect(url_for("leave_list"))
    form = LeaveReviewForm()
    if form.validate_on_submit():
        leave.status = form.status.data
        leave.reviewed_by = current_user.id
        leave.reviewed_at = datetime.utcnow()
        leave.review_notes = form.review_notes.data
        db.session.commit()
        flash(
            f"Leave request {leave.status} for {leave.employee.full_name}.",
            "success",
        )
        return redirect(url_for("leave_list"))
    return render_template("leave_review.html", leave=leave, form=form)


# ── Reports ─────────────────────────────────────────────────────

@app.route("/reports")
@login_required
@admin_required
def reports():
    month = request.args.get("month", date.today().month, type=int)
    year = request.args.get("year", date.today().year, type=int)

    employees = Employee.query.filter_by(is_active=True).order_by(Employee.first_name).all()
    report_data = []
    for emp in employees:
        stats = emp.get_monthly_stats(year, month)
        report_data.append({"employee": emp, "stats": stats})

    dept_stats = {}
    for dept in Department.query.all():
        dept_employees = Employee.query.filter_by(
            department_id=dept.id, is_active=True
        ).all()
        total_present = 0
        total_late = 0
        total_absent = 0
        for emp in dept_employees:
            s = emp.get_monthly_stats(year, month)
            total_present += s["present"]
            total_late += s["late"]
            total_absent += s["absent"]
        dept_stats[dept.name] = {
            "employee_count": len(dept_employees),
            "present": total_present,
            "late": total_late,
            "absent": total_absent,
        }

    return render_template(
        "reports.html",
        report_data=report_data,
        dept_stats=dept_stats,
        month=month,
        year=year,
    )


# ── Profile ─────────────────────────────────────────────────────

@app.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    form = ProfileForm(obj=current_user)
    if form.validate_on_submit():
        current_user.phone = form.phone.data
        db.session.commit()
        flash("Profile updated.", "success")
        return redirect(url_for("profile"))
    monthly_stats = current_user.get_monthly_stats()
    return render_template(
        "profile.html", form=form, monthly_stats=monthly_stats
    )


@app.route("/change-password", methods=["GET", "POST"])
@login_required
def change_password():
    form = ChangePasswordForm()
    if form.validate_on_submit():
        if not current_user.check_password(form.current_password.data):
            flash("Current password is incorrect.", "danger")
            return render_template("change_password.html", form=form)
        current_user.set_password(form.new_password.data)
        db.session.commit()
        flash("Password changed successfully.", "success")
        return redirect(url_for("profile"))
    return render_template("change_password.html", form=form)


# ── API Endpoints (for dashboard charts) ────────────────────────

@app.route("/api/attendance-stats")
@login_required
def api_attendance_stats():
    month = request.args.get("month", date.today().month, type=int)
    year = request.args.get("year", date.today().year, type=int)

    if current_user.role in ("admin", "hr"):
        records = Attendance.query.filter(
            db.extract("month", Attendance.date) == month,
            db.extract("year", Attendance.date) == year,
        ).all()
    else:
        records = Attendance.query.filter(
            Attendance.employee_id == current_user.id,
            db.extract("month", Attendance.date) == month,
            db.extract("year", Attendance.date) == year,
        ).all()

    present = sum(1 for r in records if r.status == "present")
    late = sum(1 for r in records if r.status == "late")
    absent = sum(1 for r in records if r.status == "absent")
    return jsonify({"present": present, "late": late, "absent": absent})


# ── App Startup ─────────────────────────────────────────────────

if __name__ == "__main__":
    app.run(debug=True, port=5000)
