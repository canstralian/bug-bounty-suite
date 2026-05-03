from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from urllib.parse import urlparse
from app import db
from models import User, BugReport, Comment
from forms import LoginForm, RegistrationForm, BugReportForm, CommentForm
from utils import export_to_csv
import csv
from io import StringIO

# Blueprint definitions
auth_bp = Blueprint('auth', __name__)
main_bp = Blueprint('main', __name__)

def register_blueprints(app):
    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)

# Auth routes
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password', 'danger')
            return redirect(url_for('auth.login'))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or urlparse(next_page).netloc != '':
            next_page = url_for('main.dashboard')
        return redirect(next_page)
    return render_template('login.html', form=form)

@auth_bp.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('main.index'))

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Registration successful!', 'success')
        return redirect(url_for('auth.login'))
    return render_template('register.html', form=form)

# Main routes
@main_bp.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    return render_template('login.html', form=LoginForm())

@main_bp.route('/dashboard')
@login_required
def dashboard():
    total_reports = BugReport.query.count()
    open_reports = BugReport.query.filter_by(status='open').count()
    my_reports = BugReport.query.filter_by(user_id=current_user.id).count()
    recent_reports = BugReport.query.order_by(BugReport.created_at.desc()).limit(5).all()
    return render_template('dashboard.html', 
                           total_reports=total_reports, 
                           open_reports=open_reports, 
                           my_reports=my_reports, 
                           recent_reports=recent_reports)

@main_bp.route('/reports')
@login_required
def report_list():
    page = request.args.get('page', 1, type=int)
    status_filter = request.args.get('status', '')
    search = request.args.get('search', '')
    
    query = BugReport.query
    if status_filter:
        query = query.filter_by(status=status_filter)
    if search:
        query = query.filter(BugReport.title.ilike(f'%{search}%'))
    
    reports = query.order_by(BugReport.created_at.desc()).paginate(page=page, per_page=10)
    return render_template('report_list.html', reports=reports)

@main_bp.route('/reports/new', methods=['GET', 'POST'])
@login_required
def new_report():
    form = BugReportForm()
    if form.validate_on_submit():
        report = BugReport(
            title=form.title.data,
            description=form.description.data,
            severity=form.severity.data,
            user_id=current_user.id
        )
        db.session.add(report)
        db.session.commit()
        flash('Bug report submitted successfully!', 'success')
        return redirect(url_for('main.report_list'))
    return render_template('report_form.html', form=form)

@main_bp.route('/reports/<int:id>')
@login_required
def report_detail(id):
    report = BugReport.query.get_or_404(id)
    comment_form = CommentForm()
    return render_template('report_detail.html', report=report, comment_form=comment_form)

@main_bp.route('/reports/<int:id>/comment', methods=['POST'])
@login_required
def add_comment(id):
    report = BugReport.query.get_or_404(id)
    form = CommentForm()
    if form.validate_on_submit():
        comment = Comment(
            content=form.content.data,
            report_id=report.id,
            user_id=current_user.id
        )
        db.session.add(comment)
        db.session.commit()
        flash('Comment added successfully!', 'success')
    return redirect(url_for('main.report_detail', id=id))

@main_bp.route('/reports/export')
@login_required
def export_reports():
    reports = BugReport.query.all()
    si = StringIO()
    writer = csv.writer(si)
    writer.writerow(['ID', 'Title', 'Severity', 'Status', 'Created At', 'Author'])
    
    for report in reports:
        writer.writerow([
            report.id,
            report.title,
            report.severity,
            report.status,
            report.created_at,
            report.author.username
        ])
    
    output = si.getvalue()
    si.close()
    
    return export_to_csv(output)