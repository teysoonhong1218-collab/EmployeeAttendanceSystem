from datetime import datetime, date, timedelta
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


class Department(db.Model):
    __tablename__ = "departments"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    employees = db.relationship("Employee", backref="department", lazy=True)

    def __repr__(self):
        return f"<Department {self.name}>"


class Employee(UserMixin, db.Model):
    __tablename__ = "employees"
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    phone = db.Column(db.String(20))
    position = db.Column(db.String(100))
    department_id = db.Column(db.Integer, db.ForeignKey("departments.id"))
    role = db.Column(db.String(20), default="employee")  # admin, hr, employee
    is_active = db.Column(db.Boolean, default=True)
    date_joined = db.Column(db.Date, default=date.today)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    attendance_records = db.relationship("Attendance", backref="employee", lazy=True)
    leave_requests = db.relationship(
        "LeaveRequest", backref="employee", lazy=True,
        foreign_keys="LeaveRequest.employee_id",
    )

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    def get_today_attendance(self):
        return Attendance.query.filter_by(
            employee_id=self.id, date=date.today()
        ).first()

    def get_monthly_stats(self, year=None, month=None):
        today = date.today()
        if not year:
            year = today.year
        if not month:
            month = today.month
        records = Attendance.query.filter(
            Attendance.employee_id == self.id,
            db.extract("year", Attendance.date) == year,
            db.extract("month", Attendance.date) == month,
        ).all()
        present = sum(1 for r in records if r.status == "present")
        late = sum(1 for r in records if r.status == "late")
        absent = sum(1 for r in records if r.status == "absent")
        total_hours = sum(r.work_hours or 0 for r in records)
        return {
            "present": present,
            "late": late,
            "absent": absent,
            "total_hours": round(total_hours, 1),
            "total_days": present + late + absent,
        }

    def __repr__(self):
        return f"<Employee {self.employee_id}: {self.full_name}>"


class Attendance(db.Model):
    __tablename__ = "attendance"
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey("employees.id"), nullable=False)
    date = db.Column(db.Date, nullable=False, default=date.today)
    clock_in = db.Column(db.DateTime)
    clock_out = db.Column(db.DateTime)
    status = db.Column(db.String(20), default="present")  # present, late, absent, half-day
    work_hours = db.Column(db.Float)
    notes = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint("employee_id", "date", name="unique_attendance_per_day"),
    )

    def calculate_work_hours(self):
        if self.clock_in and self.clock_out:
            ci = self.clock_in.replace(tzinfo=None)
            co = self.clock_out.replace(tzinfo=None)
            delta = co - ci
            self.work_hours = round(delta.total_seconds() / 3600, 2)
        return self.work_hours

    def __repr__(self):
        return f"<Attendance {self.employee_id} on {self.date}>"


class LeaveRequest(db.Model):
    __tablename__ = "leave_requests"
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey("employees.id"), nullable=False)
    leave_type = db.Column(db.String(30), nullable=False)  # annual, medical, emergency, unpaid
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    reason = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), default="pending")  # pending, approved, rejected
    reviewed_by = db.Column(db.Integer, db.ForeignKey("employees.id"))
    reviewed_at = db.Column(db.DateTime)
    review_notes = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    reviewer = db.relationship("Employee", foreign_keys=[reviewed_by])

    @property
    def duration_days(self):
        return (self.end_date - self.start_date).days + 1

    def __repr__(self):
        return f"<LeaveRequest {self.id} by Employee {self.employee_id}>"
