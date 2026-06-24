from flask_wtf import FlaskForm
from wtforms import (
    StringField, PasswordField, SelectField, TextAreaField,
    DateField, BooleanField, SubmitField,
)
from wtforms.validators import DataRequired, Email, Length, EqualTo, Optional


class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])
    remember = BooleanField("Remember Me")
    submit = SubmitField("Sign In")


class EmployeeForm(FlaskForm):
    employee_id = StringField("Employee ID", validators=[DataRequired(), Length(max=20)])
    first_name = StringField("First Name", validators=[DataRequired(), Length(max=50)])
    last_name = StringField("Last Name", validators=[DataRequired(), Length(max=50)])
    email = StringField("Email", validators=[DataRequired(), Email()])
    phone = StringField("Phone", validators=[Optional(), Length(max=20)])
    position = StringField("Position", validators=[Optional(), Length(max=100)])
    department_id = SelectField("Department", coerce=int, validators=[DataRequired()])
    role = SelectField(
        "Role",
        choices=[("employee", "Employee"), ("hr", "HR"), ("admin", "Admin")],
        validators=[DataRequired()],
    )
    password = PasswordField("Password", validators=[Optional(), Length(min=6)])
    confirm_password = PasswordField(
        "Confirm Password", validators=[Optional(), EqualTo("password")]
    )
    submit = SubmitField("Save")


class DepartmentForm(FlaskForm):
    name = StringField("Department Name", validators=[DataRequired(), Length(max=100)])
    description = StringField("Description", validators=[Optional(), Length(max=255)])
    submit = SubmitField("Save")


class LeaveRequestForm(FlaskForm):
    leave_type = SelectField(
        "Leave Type",
        choices=[
            ("annual", "Annual Leave"),
            ("medical", "Medical Leave"),
            ("emergency", "Emergency Leave"),
            ("unpaid", "Unpaid Leave"),
        ],
        validators=[DataRequired()],
    )
    start_date = DateField("Start Date", validators=[DataRequired()])
    end_date = DateField("End Date", validators=[DataRequired()])
    reason = TextAreaField("Reason", validators=[DataRequired(), Length(max=500)])
    submit = SubmitField("Submit Request")


class LeaveReviewForm(FlaskForm):
    status = SelectField(
        "Decision",
        choices=[("approved", "Approve"), ("rejected", "Reject")],
        validators=[DataRequired()],
    )
    review_notes = StringField("Notes", validators=[Optional(), Length(max=255)])
    submit = SubmitField("Submit Review")


class ChangePasswordForm(FlaskForm):
    current_password = PasswordField("Current Password", validators=[DataRequired()])
    new_password = PasswordField(
        "New Password", validators=[DataRequired(), Length(min=6)]
    )
    confirm_password = PasswordField(
        "Confirm New Password",
        validators=[DataRequired(), EqualTo("new_password")],
    )
    submit = SubmitField("Change Password")


class ProfileForm(FlaskForm):
    phone = StringField("Phone", validators=[Optional(), Length(max=20)])
    submit = SubmitField("Update Profile")
