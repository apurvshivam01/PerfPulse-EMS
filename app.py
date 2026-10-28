import os
import datetime
import re
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, session, flash, abort
from werkzeug.security import generate_password_hash, check_password_hash

from config import Config, calculate_performance_score, get_rating_category
import db

app = Flask(__name__)
app.config.from_object(Config)

# ---------------------------------------------------------
# Authentication & Authorization Helpers
# ---------------------------------------------------------

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash("Please sign in to access this page.", "warning")
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def roles_required(*allowed_roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                flash("Please sign in to access this page.", "warning")
                return redirect(url_for('login'))
            current_role = session.get('user_role')
            if current_role not in allowed_roles:
                flash("Access denied: You do not have permission to view this resource.", "danger")
                if current_role == 'Admin':
                    return redirect(url_for('admin_dashboard'))
                elif current_role == 'Manager':
                    return redirect(url_for('manager_dashboard'))
                else:
                    return redirect(url_for('employee_dashboard'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def get_current_employee_id():
    """Retrieve employee ID associated with the current user session."""
    user_id = session.get('user_id')
    if not user_id:
        return None
    emp = db.query_db("SELECT id FROM employees WHERE user_id = %s", (user_id,), one=True)
    return emp['id'] if emp else None

def generate_next_employee_code():
    """Generate sequential employee code formatted as EMP###."""
    rows = db.query_db("SELECT emp_code FROM employees WHERE emp_code LIKE 'EMP%'")
    max_num = 0
    for r in rows:
        code = r['emp_code']
        num_part = code.replace('EMP', '')
        if num_part.isdigit():
            max_num = max(max_num, int(num_part))
    return f"EMP{max_num + 1:03d}"

# ---------------------------------------------------------
# Authentication Routes
# ---------------------------------------------------------

@app.route('/')
def index():
    if 'user_id' in session:
        role = session.get('user_role')
        if role == 'Admin':
            return redirect(url_for('admin_dashboard'))
        elif role == 'Manager':
            return redirect(url_for('manager_dashboard'))
        else:
            return redirect(url_for('employee_dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        identifier = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        if not identifier or not password:
            flash("Please enter both username/email and password.", "danger")
            return render_template('login.html')

        # Find user by username or email
        user = db.query_db(
            "SELECT * FROM users WHERE username = %s OR email = %s", 
            (identifier, identifier), 
            one=True
        )

        if user and check_password_hash(user['password_hash'], password):
            # Login successful
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['user_role'] = user['role']
            session['full_name'] = user['full_name']

            # Lookup employee record if available
            emp = db.query_db("SELECT id FROM employees WHERE user_id = %s", (user['id'],), one=True)
            session['emp_id'] = emp['id'] if emp else None

            flash(f"Welcome back, {user['full_name']}!", "success")
            
            # Redirect to appropriate dashboard
            if user['role'] == 'Admin':
                return redirect(url_for('admin_dashboard'))
            elif user['role'] == 'Manager':
                return redirect(url_for('manager_dashboard'))
            else:
                return redirect(url_for('employee_dashboard'))
        else:
            flash("Invalid credentials. Please verify username and password.", "danger")

    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if 'user_id' in session:
        return redirect(url_for('index'))

    departments = db.query_db("SELECT id, name FROM departments ORDER BY name ASC")

    if request.method == 'POST':
        full_name = request.form.get('full_name', '').strip()
        username = request.form.get('username', '').strip().lower()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        department_id = request.form.get('department_id', '').strip()
        job_position = request.form.get('job_position', '').strip()
        role = 'Employee'  # Strictly enforced: only Employee registration is allowed via public signup

        form_data = {
            'full_name': full_name,
            'username': username,
            'email': email,
            'department_id': department_id,
            'job_position': job_position
        }

        # 1. Required field validation
        if not full_name or not username or not email or not password or not confirm_password or not department_id or not job_position:
            flash("All fields marked with an asterisk (*) are required.", "danger")
            return render_template('signup.html', departments=departments, form_data=form_data)

        # 2. Email format validation
        if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email):
            flash("Please enter a valid email address.", "danger")
            return render_template('signup.html', departments=departments, form_data=form_data)

        # 3. Username format validation
        if len(username) < 3 or not re.match(r"^[a-zA-Z0-9._-]+$", username):
            flash("Username must be at least 3 characters and contain only letters, numbers, dots, hyphens, or underscores.", "danger")
            return render_template('signup.html', departments=departments, form_data=form_data)

        # 4. Minimum password length
        if len(password) < 8:
            flash("Password must be at least 8 characters long.", "danger")
            return render_template('signup.html', departments=departments, form_data=form_data)

        # 5. Password confirmation validation
        if password != confirm_password:
            flash("Password and Confirm Password do not match.", "danger")
            return render_template('signup.html', departments=departments, form_data=form_data)

        # 6. Duplicate username check
        existing_user = db.query_db("SELECT id FROM users WHERE username = %s", (username,), one=True)
        if existing_user:
            flash("Username is already taken. Please choose a different username.", "danger")
            return render_template('signup.html', departments=departments, form_data=form_data)

        # 7. Duplicate email check
        existing_email_user = db.query_db("SELECT id FROM users WHERE email = %s", (email,), one=True)
        existing_email_emp = db.query_db("SELECT id FROM employees WHERE email = %s", (email,), one=True)
        if existing_email_user or existing_email_emp:
            flash("An account with this email address already exists. Please sign in.", "danger")
            return render_template('signup.html', departments=departments, form_data=form_data)

        # 8. Check department exists
        dept = db.query_db("SELECT id FROM departments WHERE id = %s", (department_id,), one=True)
        if not dept:
            flash("Selected department is invalid.", "danger")
            return render_template('signup.html', departments=departments, form_data=form_data)

        # 9. Auto-assign manager for this department if one exists
        mgr = db.query_db("""
            SELECT e.id FROM employees e
            JOIN users u ON e.user_id = u.id
            WHERE u.role = 'Manager' AND e.department_id = %s
            LIMIT 1
        """, (department_id,), one=True)
        manager_id = mgr['id'] if mgr else None

        # 10. Generate sequential unique employee code
        emp_code = generate_next_employee_code()

        # 11. Securely hash password with Werkzeug PBKDF2
        password_hash = generate_password_hash(password, method='pbkdf2:sha256')

        try:
            # Insert into users table
            user_id = db.execute_db("""
                INSERT INTO users (username, email, password_hash, role, full_name)
                VALUES (%s, %s, %s, %s, %s)
            """, (username, email, password_hash, role, full_name))

            # Insert into employees table
            today_date = datetime.date.today().strftime('%Y-%m-%d')
            db.execute_db("""
                INSERT INTO employees (user_id, emp_code, full_name, email, phone, department_id, job_position, joining_date, manager_id, employment_status)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 'Active')
            """, (user_id, emp_code, full_name, email, '', department_id, job_position, today_date, manager_id))

            flash("Account created successfully! Please sign in.", "success")
            return redirect(url_for('login'))
        except Exception as e:
            flash(f"Error creating account: {str(e)}", "danger")
            return render_template('signup.html', departments=departments, form_data=form_data)

    return render_template('signup.html', departments=departments, form_data=None)

@app.route('/logout')
def logout():
    session.clear()
    flash("You have been signed out successfully.", "info")
    return redirect(url_for('login'))

# ---------------------------------------------------------
# 1. Admin Dashboard
# ---------------------------------------------------------

@app.route('/admin/dashboard')
@roles_required('Admin')
def admin_dashboard():
    # 1. Total employees (excluding top-level managers if desired, or all staff)
    total_employees_row = db.query_db("SELECT COUNT(*) as count FROM employees WHERE user_id IN (SELECT id FROM users WHERE role = 'Employee')", one=True)
    total_employees = total_employees_row['count'] if total_employees_row else 0

    # 2. Total managers
    total_managers_row = db.query_db("SELECT COUNT(*) as count FROM users WHERE role = 'Manager'", one=True)
    total_managers = total_managers_row['count'] if total_managers_row else 0

    # 3. Total departments
    total_dept_row = db.query_db("SELECT COUNT(*) as count FROM departments", one=True)
    total_departments = total_dept_row['count'] if total_dept_row else 0

    # 4. Average employee performance & Count needing improvement (< 60)
    score_stats = db.query_db("""
        SELECT 
            AVG(total_score) as avg_score,
            SUM(CASE WHEN total_score < 60 THEN 1 ELSE 0 END) as needs_improvement_count
        FROM performance_reviews
    """, one=True)

    raw_avg = score_stats['avg_score'] if score_stats and score_stats['avg_score'] is not None else 0.0
    avg_score = round(float(raw_avg), 2)
    avg_category = get_rating_category(avg_score)
    needs_improvement_count = score_stats['needs_improvement_count'] if score_stats and score_stats['needs_improvement_count'] is not None else 0

    # Category badge class
    category_badge_map = {
        'Outstanding': 'outstanding',
        'Excellent': 'excellent',
        'Good': 'good',
        'Average': 'average',
        'Needs Improvement': 'improvement'
    }
    avg_category_badge = category_badge_map.get(avg_category, 'secondary')

    # 5. Top-performing employee
    top_employee = db.query_db("""
        SELECT 
            e.id, e.full_name, e.emp_code, e.job_position,
            d.name as dept_name,
            r.total_score, r.rating_category
        FROM performance_reviews r
        JOIN employees e ON r.employee_id = e.id
        LEFT JOIN departments d ON e.department_id = d.id
        ORDER BY r.total_score DESC, r.review_date DESC
        LIMIT 1
    """, one=True)

    # 6. Recent performance evaluations
    recent_reviews = db.query_db("""
        SELECT 
            r.*,
            e.full_name as emp_name, e.emp_code,
            d.name as dept_name
        FROM performance_reviews r
        JOIN employees e ON r.employee_id = e.id
        LEFT JOIN departments d ON e.department_id = d.id
        ORDER BY r.review_date DESC, r.id DESC
        LIMIT 7
    """)

    # 7. Chart Data: Department Average Scores
    dept_chart_rows = db.query_db("""
        SELECT 
            d.name as dept_name,
            ROUND(AVG(r.total_score), 2) as avg_score
        FROM departments d
        JOIN employees e ON e.department_id = d.id
        JOIN performance_reviews r ON r.employee_id = e.id
        GROUP BY d.id, d.name
        ORDER BY avg_score DESC
    """)
    chart_dept_data = {
        'labels': [row['dept_name'] for row in dept_chart_rows],
        'scores': [float(row['avg_score']) for row in dept_chart_rows]
    }

    # 8. Chart Data: Rating Category Distribution
    category_rows = db.query_db("""
        SELECT rating_category, COUNT(*) as count
        FROM performance_reviews
        GROUP BY rating_category
    """)
    cat_counts = {row['rating_category']: row['count'] for row in category_rows}
    chart_category_data = {
        'outstanding': cat_counts.get('Outstanding', 0),
        'excellent': cat_counts.get('Excellent', 0),
        'good': cat_counts.get('Good', 0),
        'average': cat_counts.get('Average', 0),
        'needs_improvement': cat_counts.get('Needs Improvement', 0)
    }

    # 9. Chart Data: Performance Trends across Review Periods
    trend_rows = db.query_db("""
        SELECT review_period, ROUND(AVG(total_score), 2) as avg_score
        FROM performance_reviews
        GROUP BY review_period
        ORDER BY MIN(review_date) ASC
    """)
    chart_trend_data = {
        'labels': [row['review_period'] for row in trend_rows],
        'scores': [float(row['avg_score']) for row in trend_rows]
    }

    # 10. Goals KPI Metrics
    goals_row = db.query_db("SELECT COUNT(*) as total, SUM(CASE WHEN status = 'Completed' THEN 1 ELSE 0 END) as completed FROM goals", one=True)
    total_goals = goals_row['total'] if goals_row and goals_row['total'] else 0
    completed_goals = goals_row['completed'] if goals_row and goals_row['completed'] else 0
    goals_pct = int(round((completed_goals / total_goals * 100), 0)) if total_goals > 0 else 0

    stats = {
        'total_employees': total_employees,
        'total_managers': total_managers,
        'total_departments': total_departments,
        'avg_score': avg_score,
        'avg_category': avg_category,
        'avg_category_badge': avg_category_badge,
        'needs_improvement_count': needs_improvement_count,
        'total_goals': total_goals,
        'completed_goals': completed_goals,
        'goals_pct': goals_pct
    }

    # 11. Greeting and Date
    now = datetime.datetime.now()
    hour = now.hour
    if hour < 12:
        greeting = "Good morning"
    elif hour < 17:
        greeting = "Good afternoon"
    else:
        greeting = "Good evening"
    current_date = now.strftime("%a, %b %d, %Y")

    # 12. Department Performance List with Progress Values
    dept_perf_rows = db.query_db("""
        SELECT 
            d.id, d.name,
            COUNT(e.id) as emp_count,
            ROUND(COALESCE(AVG(r.total_score), 0), 1) as avg_score
        FROM departments d
        LEFT JOIN employees e ON e.department_id = d.id
        LEFT JOIN performance_reviews r ON r.employee_id = e.id
        GROUP BY d.id, d.name
        ORDER BY avg_score DESC
    """)

    # 13. Top Employee Spotlight Goals Progress
    top_emp_goals_pct = 90
    if top_employee:
        top_goals = db.query_db("""
            SELECT COUNT(*) as total, SUM(CASE WHEN status = 'Completed' THEN 1 ELSE 0 END) as completed
            FROM goals WHERE employee_id = %s
        """, (top_employee['id'],), one=True)
        if top_goals and top_goals['total']:
            top_emp_goals_pct = int(round((top_goals['completed'] / top_goals['total']) * 100))

    # 14. Employees Needing Attention List
    needs_attention_rows = db.query_db("""
        SELECT 
            e.id, e.full_name, e.job_position, e.emp_code,
            r.total_score, r.rating_category,
            d.name as dept_name
        FROM employees e
        JOIN performance_reviews r ON r.employee_id = e.id
        LEFT JOIN departments d ON e.department_id = d.id
        WHERE r.id = (
            SELECT id FROM performance_reviews WHERE employee_id = e.id ORDER BY review_date DESC, id DESC LIMIT 1
        ) AND (r.total_score < 60 OR r.rating_category = 'Needs Improvement')
    """)

    # 15. Team Overview Table List
    team_overview_rows = db.query_db("""
        SELECT 
            e.id, e.emp_code, e.full_name, e.email, e.job_position, e.employment_status,
            d.name as dept_name,
            (SELECT COUNT(*) FROM goals g WHERE g.employee_id = e.id AND g.status != 'Completed') as active_goals_count,
            (SELECT r.total_score FROM performance_reviews r WHERE r.employee_id = e.id ORDER BY r.review_date DESC, r.id DESC LIMIT 1) as latest_score,
            (SELECT r.rating_category FROM performance_reviews r WHERE r.employee_id = e.id ORDER BY r.review_date DESC, r.id DESC LIMIT 1) as rating_category
        FROM employees e
        LEFT JOIN departments d ON e.department_id = d.id
        ORDER BY e.full_name ASC
    """)

    # 16. Recent Activity Timeline
    recent_activities = [
        {'title': 'Microservices Architecture goal completed', 'user': 'John Doe', 'dept': 'Tech', 'time': '2h ago', 'icon': 'bi-check2-circle', 'theme': 'sage'},
        {'title': 'Received Outstanding evaluation (93.4)', 'user': 'Jessica Miller', 'dept': 'Marketing', 'time': '5h ago', 'icon': 'bi-star-fill', 'theme': 'indigo'},
        {'title': 'New employee joined as QA Engineer', 'user': 'Alex Taylor', 'dept': 'QA Team', 'time': 'Yesterday', 'icon': 'bi-person-plus', 'theme': 'peach'},
        {'title': 'Quarterly budget variance review finalized', 'user': 'Amanda Thomas', 'dept': 'Finance', 'time': '2d ago', 'icon': 'bi-file-earmark-check', 'theme': 'sky'}
    ]

    return render_template(
        'admin/dashboard.html',
        active_page='admin_dashboard',
        stats=stats,
        top_employee=top_employee,
        top_emp_goals_pct=top_emp_goals_pct,
        recent_reviews=recent_reviews,
        chart_dept_data=chart_dept_data,
        chart_category_data=chart_category_data,
        chart_trend_data=chart_trend_data,
        greeting=greeting,
        current_date=current_date,
        today_date=now.strftime('%Y-%m-%d'),
        dept_perf_rows=dept_perf_rows,
        needs_attention_rows=needs_attention_rows,
        team_overview_rows=team_overview_rows,
        recent_activities=recent_activities
    )

# ---------------------------------------------------------
# 2. Manager Dashboard
# ---------------------------------------------------------

@app.route('/manager/dashboard')
@roles_required('Manager')
def manager_dashboard():
    manager_emp_id = get_current_employee_id()
    if not manager_emp_id:
        flash("Manager employee record not found.", "danger")
        return redirect(url_for('logout'))

    # 1. Team size
    team_count_row = db.query_db(
        "SELECT COUNT(*) as count FROM employees WHERE manager_id = %s", 
        (manager_emp_id,), 
        one=True
    )
    team_size = team_count_row['count'] if team_count_row else 0

    # 2. Team average performance & needs improvement
    team_stats = db.query_db("""
        SELECT 
            AVG(r.total_score) as avg_score,
            SUM(CASE WHEN r.total_score < 60 THEN 1 ELSE 0 END) as needs_improvement_count
        FROM performance_reviews r
        JOIN employees e ON r.employee_id = e.id
        WHERE e.manager_id = %s
    """, (manager_emp_id,), one=True)

    raw_avg = team_stats['avg_score'] if team_stats and team_stats['avg_score'] is not None else 0.0
    team_avg_score = round(float(raw_avg), 2)
    team_category = get_rating_category(team_avg_score)
    needs_improvement_count = team_stats['needs_improvement_count'] if team_stats and team_stats['needs_improvement_count'] is not None else 0

    category_badge_map = {
        'Outstanding': 'outstanding',
        'Excellent': 'excellent',
        'Good': 'good',
        'Average': 'average',
        'Needs Improvement': 'improvement'
    }
    team_category_badge = category_badge_map.get(team_category, 'secondary')

    # 3. Pending Evaluations: team members without an evaluation in the current year/period
    pending_count_row = db.query_db("""
        SELECT COUNT(*) as count 
        FROM employees e
        WHERE e.manager_id = %s 
          AND e.id NOT IN (
              SELECT employee_id FROM performance_reviews WHERE review_period = 'Q1 2026'
          )
    """, (manager_emp_id,), one=True)
    pending_reviews = pending_count_row['count'] if pending_count_row else 0

    # 4. Top team performer
    top_team_member = db.query_db("""
        SELECT 
            e.id, e.full_name, e.emp_code, e.job_position,
            r.total_score, r.rating_category
        FROM performance_reviews r
        JOIN employees e ON r.employee_id = e.id
        WHERE e.manager_id = %s
        ORDER BY r.total_score DESC, r.review_date DESC
        LIMIT 1
    """, (manager_emp_id,), one=True)

    # 5. Team goals progress
    team_goals = db.query_db("""
        SELECT 
            g.*,
            e.full_name as emp_name
        FROM goals g
        JOIN employees e ON g.employee_id = e.id
        WHERE e.manager_id = %s
        ORDER BY g.deadline ASC
    """, (manager_emp_id,))

    # 6. Team members list with latest evaluation score
    team_members = db.query_db("""
        SELECT 
            e.id, e.emp_code, e.full_name, e.email, e.job_position,
            (
                SELECT r.total_score 
                FROM performance_reviews r 
                WHERE r.employee_id = e.id 
                ORDER BY r.review_date DESC, r.id DESC 
                LIMIT 1
            ) as latest_score,
            (
                SELECT r.rating_category 
                FROM performance_reviews r 
                WHERE r.employee_id = e.id 
                ORDER BY r.review_date DESC, r.id DESC 
                LIMIT 1
            ) as rating_category,
            (
                SELECT COUNT(*) 
                FROM goals g 
                WHERE g.employee_id = e.id AND g.status != 'Completed'
            ) as active_goals_count
        FROM employees e
        WHERE e.manager_id = %s
        ORDER BY e.full_name ASC
    """, (manager_emp_id,))

    # Chart data for team
    chart_team_names = [m['full_name'] for m in team_members if m['latest_score'] is not None]
    chart_team_scores = [float(m['latest_score']) for m in team_members if m['latest_score'] is not None]

    stats = {
        'team_size': team_size,
        'team_avg_score': team_avg_score,
        'team_category': team_category,
        'team_category_badge': team_category_badge,
        'pending_reviews': pending_reviews,
        'needs_improvement_count': needs_improvement_count
    }

    return render_template(
        'manager/dashboard.html',
        active_page='manager_dashboard',
        stats=stats,
        top_team_member=top_team_member,
        team_goals=team_goals,
        team_members=team_members,
        chart_team_names=chart_team_names,
        chart_team_scores=chart_team_scores
    )

# ---------------------------------------------------------
# 3. Employee Dashboard
# ---------------------------------------------------------

@app.route('/employee/dashboard')
@roles_required('Employee')
def employee_dashboard():
    emp_id = get_current_employee_id()
    if not emp_id:
        flash("Employee profile not linked to this account.", "warning")
        return redirect(url_for('logout'))

    # Employee record
    employee = db.query_db("""
        SELECT 
            e.*,
            d.name as dept_name,
            m.full_name as manager_name
        FROM employees e
        LEFT JOIN departments d ON e.department_id = d.id
        LEFT JOIN employees m ON e.manager_id = m.id
        WHERE e.id = %s
    """, (emp_id,), one=True)

    # Latest Performance Review
    latest_review = db.query_db("""
        SELECT * FROM performance_reviews
        WHERE employee_id = %s
        ORDER BY review_date DESC, id DESC
        LIMIT 1
    """, (emp_id,), one=True)

    # Previous Reviews
    reviews = db.query_db("""
        SELECT * FROM performance_reviews
        WHERE employee_id = %s
        ORDER BY review_date DESC
    """, (emp_id,))

    # Assigned Goals & Stats
    goals = db.query_db("""
        SELECT * FROM goals
        WHERE employee_id = %s
        ORDER BY deadline ASC
    """, (emp_id,))

    total_goals_count = len(goals)
    completed_goals_count = sum(1 for g in goals if g['status'] == 'Completed')
    active_goals_count = total_goals_count - completed_goals_count
    avg_goal_completion = round(sum(g['completion_percentage'] for g in goals) / total_goals_count, 1) if total_goals_count > 0 else 0

    # Latest Feedback from Manager
    latest_feedback = db.query_db("""
        SELECT 
            f.*,
            u.full_name as manager_name
        FROM feedback f
        JOIN users u ON f.manager_id = u.id
        WHERE f.employee_id = %s
        ORDER BY f.feedback_date DESC, f.id DESC
        LIMIT 1
    """, (emp_id,), one=True)

    # Chart data: historical scores
    history_reviews = sorted(reviews, key=lambda x: x['review_date'])
    chart_periods = [r['review_period'] for r in history_reviews]
    chart_scores = [float(r['total_score']) for r in history_reviews]

    return render_template(
        'employee/dashboard.html',
        active_page='employee_dashboard',
        employee=employee,
        latest_review=latest_review,
        reviews=reviews,
        goals=goals,
        total_goals_count=total_goals_count,
        completed_goals_count=completed_goals_count,
        active_goals_count=active_goals_count,
        avg_goal_completion=avg_goal_completion,
        latest_feedback=latest_feedback,
        chart_periods=chart_periods,
        chart_scores=chart_scores
    )

# ---------------------------------------------------------
# 4. Employee Profile
# ---------------------------------------------------------

@app.route('/employees/profile/<int:emp_id>')
@login_required
def employee_profile(emp_id):
    current_role = session.get('user_role')
    current_emp_id = get_current_employee_id()

    # Access control: Employee can only view own profile
    if current_role == 'Employee' and current_emp_id != emp_id:
        flash("You are only authorized to view your own employee profile.", "danger")
        return redirect(url_for('employee_profile', emp_id=current_emp_id))

    # Manager can only view their own team members (or themselves)
    if current_role == 'Manager':
        is_subordinate = db.query_db(
            "SELECT id FROM employees WHERE id = %s AND (manager_id = %s OR id = %s)", 
            (emp_id, current_emp_id, current_emp_id), 
            one=True
        )
        if not is_subordinate:
            flash("You can only view profiles of employees assigned under your management.", "danger")
            return redirect(url_for('employees_list'))

    # Load Employee Information
    emp = db.query_db("""
        SELECT 
            e.*,
            d.name as dept_name,
            m.full_name as manager_name
        FROM employees e
        LEFT JOIN departments d ON e.department_id = d.id
        LEFT JOIN employees m ON e.manager_id = m.id
        WHERE e.id = %s
    """, (emp_id,), one=True)

    if not emp:
        flash("Employee not found.", "danger")
        return redirect(url_for('index'))

    # Load goals
    goals = db.query_db("SELECT * FROM goals WHERE employee_id = %s ORDER BY deadline ASC", (emp_id,))

    # Load evaluations
    reviews = db.query_db("""
        SELECT 
            r.*,
            u.full_name as reviewer_name
        FROM performance_reviews r
        JOIN users u ON r.reviewer_id = u.id
        WHERE r.employee_id = %s
        ORDER BY r.review_date DESC
    """, (emp_id,))

    latest_review = reviews[0] if reviews else None

    # Load feedback
    feedbacks = db.query_db("""
        SELECT 
            f.*,
            u.full_name as manager_name
        FROM feedback f
        JOIN users u ON f.manager_id = u.id
        WHERE f.employee_id = %s
        ORDER BY f.feedback_date DESC
    """, (emp_id,))

    return render_template(
        'employees/profile.html',
        active_page='my_profile' if current_role == 'Employee' else 'employees',
        emp=emp,
        goals=goals,
        reviews=reviews,
        latest_review=latest_review,
        feedbacks=feedbacks
    )

@app.route('/my-profile')
@login_required
def my_profile():
    emp_id = get_current_employee_id()
    if not emp_id:
        flash("Employee profile not found.", "warning")
        return redirect(url_for('index'))
    return redirect(url_for('employee_profile', emp_id=emp_id))

# ---------------------------------------------------------
# 5. Employee Management (CRUD)
# ---------------------------------------------------------

@app.route('/employees')
@roles_required('Admin', 'Manager')
def employees_list():
    current_role = session.get('user_role')
    search_query = request.args.get('search', '').strip()
    selected_dept = request.args.get('dept', '').strip()

    # Build query
    sql = """
        SELECT 
            e.*,
            d.name as dept_name,
            m.full_name as manager_name,
            (
                SELECT r.total_score 
                FROM performance_reviews r 
                WHERE r.employee_id = e.id 
                ORDER BY r.review_date DESC, r.id DESC 
                LIMIT 1
            ) as latest_score,
            (
                SELECT r.rating_category 
                FROM performance_reviews r 
                WHERE r.employee_id = e.id 
                ORDER BY r.review_date DESC, r.id DESC 
                LIMIT 1
            ) as rating_category
        FROM employees e
        LEFT JOIN departments d ON e.department_id = d.id
        LEFT JOIN employees m ON e.manager_id = m.id
        WHERE 1=1
    """
    params = []

    # If manager, scope to team
    if current_role == 'Manager':
        mgr_id = get_current_employee_id()
        sql += " AND e.manager_id = %s"
        params.append(mgr_id)

    # Search filter
    if search_query:
        sql += " AND (e.full_name LIKE %s OR e.emp_code LIKE %s OR e.job_position LIKE %s OR e.email LIKE %s)"
        like_term = f"%{search_query}%"
        params.extend([like_term, like_term, like_term, like_term])

    # Department filter
    if selected_dept:
        sql += " AND e.department_id = %s"
        params.append(selected_dept)

    sql += " ORDER BY e.full_name ASC"

    employees = db.query_db(sql, tuple(params))
    departments = db.query_db("SELECT * FROM departments ORDER BY name ASC")
    
    # Managers list for the add/edit dropdown
    managers = db.query_db("""
        SELECT e.id, e.full_name, e.job_position
        FROM employees e
        JOIN users u ON e.user_id = u.id
        WHERE u.role = 'Manager'
        ORDER BY e.full_name ASC
    """)

    return render_template(
        'employees/index.html',
        active_page='employees',
        employees=employees,
        departments=departments,
        managers=managers,
        search_query=search_query,
        selected_dept=selected_dept
    )

@app.route('/employees/create', methods=['POST'])
@roles_required('Admin')
def employee_create():
    emp_code = request.form.get('emp_code', '').strip().upper()
    full_name = request.form.get('full_name', '').strip()
    email = request.form.get('email', '').strip().lower()
    phone = request.form.get('phone', '').strip()
    department_id = request.form.get('department_id') or None
    job_position = request.form.get('job_position', '').strip()
    manager_id = request.form.get('manager_id') or None
    joining_date = request.form.get('joining_date', '').strip()

    # Validation
    if not emp_code or not full_name or not email or not job_position or not joining_date:
        flash("Please fill in all required fields.", "danger")
        return redirect(url_for('employees_list'))

    # Check for duplicate email or employee code
    existing = db.query_db(
        "SELECT id FROM employees WHERE email = %s OR emp_code = %s",
        (email, emp_code),
        one=True
    )
    if existing:
        flash("An employee with this email or employee code already exists.", "danger")
        return redirect(url_for('employees_list'))

    # Auto create login username
    username = f"emp.{emp_code.lower()}"
    default_password_hash = generate_password_hash('employee123', method='pbkdf2:sha256')

    try:
        user_id = db.execute_db(
            "INSERT INTO users (username, email, password_hash, role, full_name) VALUES (%s, %s, %s, 'Employee', %s)",
            (username, email, default_password_hash, full_name)
        )

        db.execute_db("""
            INSERT INTO employees (user_id, emp_code, full_name, email, phone, department_id, job_position, joining_date, manager_id, employment_status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 'Active')
        """, (user_id, emp_code, full_name, email, phone, department_id, job_position, joining_date, manager_id))

        flash(f"Employee {full_name} ({emp_code}) created successfully! Login username: {username}, Password: employee123", "success")
    except Exception as e:
        flash(f"Error creating employee: {str(e)}", "danger")

    return redirect(url_for('employees_list'))

@app.route('/employees/edit/<int:emp_id>', methods=['POST'])
@roles_required('Admin')
def employee_edit(emp_id):
    emp_code = request.form.get('emp_code', '').strip().upper()
    full_name = request.form.get('full_name', '').strip()
    email = request.form.get('email', '').strip().lower()
    phone = request.form.get('phone', '').strip()
    department_id = request.form.get('department_id') or None
    job_position = request.form.get('job_position', '').strip()
    manager_id = request.form.get('manager_id') or None
    joining_date = request.form.get('joining_date', '').strip()
    employment_status = request.form.get('employment_status', 'Active')

    # Duplicate check excluding current employee
    existing = db.query_db(
        "SELECT id FROM employees WHERE (email = %s OR emp_code = %s) AND id != %s",
        (email, emp_code, emp_id),
        one=True
    )
    if existing:
        flash("Email or Employee Code already in use by another record.", "danger")
        return redirect(url_for('employees_list'))

    try:
        emp = db.query_db("SELECT user_id FROM employees WHERE id = %s", (emp_id,), one=True)
        if emp and emp['user_id']:
            db.execute_db(
                "UPDATE users SET email = %s, full_name = %s WHERE id = %s",
                (email, full_name, emp['user_id'])
            )

        db.execute_db("""
            UPDATE employees 
            SET emp_code = %s, full_name = %s, email = %s, phone = %s,
                department_id = %s, job_position = %s, manager_id = %s,
                joining_date = %s, employment_status = %s
            WHERE id = %s
        """, (emp_code, full_name, email, phone, department_id, job_position, manager_id, joining_date, employment_status, emp_id))

        flash(f"Employee {full_name} updated successfully.", "success")
    except Exception as e:
        flash(f"Error updating employee: {str(e)}", "danger")

    return redirect(url_for('employees_list'))

@app.route('/employees/delete/<int:emp_id>', methods=['POST'])
@roles_required('Admin')
def employee_delete(emp_id):
    emp = db.query_db("SELECT user_id, full_name FROM employees WHERE id = %s", (emp_id,), one=True)
    if not emp:
        flash("Employee not found.", "danger")
        return redirect(url_for('employees_list'))

    try:
        # Delete employee (cascades or cleans up)
        db.execute_db("DELETE FROM employees WHERE id = %s", (emp_id,))
        if emp['user_id']:
            db.execute_db("DELETE FROM users WHERE id = %s", (emp['user_id'],))
        flash(f"Employee {emp['full_name']} and all associated records deleted.", "success")
    except Exception as e:
        flash(f"Error deleting employee: {str(e)}", "danger")

    return redirect(url_for('employees_list'))

# ---------------------------------------------------------
# 6. Departments Management (Admin)
# ---------------------------------------------------------

@app.route('/departments')
@roles_required('Admin')
def departments_list():
    departments = db.query_db("""
        SELECT 
            d.*,
            (SELECT COUNT(*) FROM employees WHERE department_id = d.id) as emp_count
        FROM departments d
        ORDER BY d.name ASC
    """)
    return render_template('departments/index.html', active_page='departments', departments=departments)

@app.route('/departments/create', methods=['POST'])
@roles_required('Admin')
def department_create():
    name = request.form.get('name', '').strip()
    description = request.form.get('description', '').strip()

    if not name:
        flash("Department name is required.", "danger")
        return redirect(url_for('departments_list'))

    existing = db.query_db("SELECT id FROM departments WHERE name = %s", (name,), one=True)
    if existing:
        flash("Department with this name already exists.", "danger")
        return redirect(url_for('departments_list'))

    try:
        db.execute_db("INSERT INTO departments (name, description) VALUES (%s, %s)", (name, description))
        flash(f"Department '{name}' created successfully.", "success")
    except Exception as e:
        flash(f"Error creating department: {str(e)}", "danger")

    return redirect(url_for('departments_list'))

@app.route('/departments/edit/<int:dept_id>', methods=['POST'])
@roles_required('Admin')
def department_edit(dept_id):
    name = request.form.get('name', '').strip()
    description = request.form.get('description', '').strip()

    if not name:
        flash("Department name is required.", "danger")
        return redirect(url_for('departments_list'))

    try:
        db.execute_db("UPDATE departments SET name = %s, description = %s WHERE id = %s", (name, description, dept_id))
        flash("Department updated successfully.", "success")
    except Exception as e:
        flash(f"Error updating department: {str(e)}", "danger")

    return redirect(url_for('departments_list'))

@app.route('/departments/delete/<int:dept_id>', methods=['POST'])
@roles_required('Admin')
def department_delete(dept_id):
    try:
        db.execute_db("DELETE FROM departments WHERE id = %s", (dept_id,))
        flash("Department deleted successfully.", "success")
    except Exception as e:
        flash(f"Error deleting department: {str(e)}", "danger")

    return redirect(url_for('departments_list'))

# ---------------------------------------------------------
# 7. Managers Management (Admin)
# ---------------------------------------------------------

@app.route('/managers')
@roles_required('Admin')
def managers_list():
    managers = db.query_db("""
        SELECT 
            e.*,
            d.name as dept_name,
            (SELECT COUNT(*) FROM employees WHERE manager_id = e.id) as team_size
        FROM employees e
        JOIN users u ON e.user_id = u.id
        LEFT JOIN departments d ON e.department_id = d.id
        WHERE u.role = 'Manager'
        ORDER BY e.full_name ASC
    """)
    departments = db.query_db("SELECT * FROM departments ORDER BY name ASC")
    return render_template('managers/index.html', active_page='managers', managers=managers, departments=departments)

@app.route('/managers/create', methods=['POST'])
@roles_required('Admin')
def manager_create():
    emp_code = request.form.get('emp_code', '').strip().upper()
    full_name = request.form.get('full_name', '').strip()
    email = request.form.get('email', '').strip().lower()
    phone = request.form.get('phone', '').strip()
    department_id = request.form.get('department_id') or None
    job_position = request.form.get('job_position', '').strip()
    joining_date = request.form.get('joining_date', '').strip()

    if not emp_code or not full_name or not email or not job_position or not joining_date:
        flash("Please fill in all required manager fields.", "danger")
        return redirect(url_for('managers_list'))

    existing = db.query_db("SELECT id FROM users WHERE email = %s", (email,), one=True)
    if existing:
        flash("A user with this email address already exists.", "danger")
        return redirect(url_for('managers_list'))

    username = f"manager.{emp_code.lower()}"
    default_pw_hash = generate_password_hash('manager123', method='pbkdf2:sha256')

    try:
        user_id = db.execute_db(
            "INSERT INTO users (username, email, password_hash, role, full_name) VALUES (%s, %s, %s, 'Manager', %s)",
            (username, email, default_pw_hash, full_name)
        )

        db.execute_db("""
            INSERT INTO employees (user_id, emp_code, full_name, email, phone, department_id, job_position, joining_date, employment_status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'Active')
        """, (user_id, emp_code, full_name, email, phone, department_id, job_position, joining_date))

        flash(f"Manager {full_name} registered successfully! Username: {username}, Password: manager123", "success")
    except Exception as e:
        flash(f"Error registering manager: {str(e)}", "danger")

    return redirect(url_for('managers_list'))

# ---------------------------------------------------------
# 8. Goal Management
# ---------------------------------------------------------

@app.route('/goals')
@login_required
def goals_list():
    current_role = session.get('user_role')
    current_emp_id = get_current_employee_id()
    search_query = request.args.get('search', '').strip()
    selected_status = request.args.get('status', '').strip()
    target_emp_id = request.args.get('emp_id', '').strip()

    sql = """
        SELECT 
            g.*,
            e.full_name as emp_name, e.emp_code,
            d.name as dept_name,
            u.full_name as assigner_name
        FROM goals g
        JOIN employees e ON g.employee_id = e.id
        LEFT JOIN departments d ON e.department_id = d.id
        JOIN users u ON g.assigned_by = u.id
        WHERE 1=1
    """
    params = []

    # Role Scoping
    if current_role == 'Employee':
        sql += " AND g.employee_id = %s"
        params.append(current_emp_id)
    elif current_role == 'Manager':
        sql += " AND e.manager_id = %s"
        params.append(current_emp_id)

    # Filters
    if target_emp_id:
        sql += " AND g.employee_id = %s"
        params.append(target_emp_id)

    if search_query:
        sql += " AND (g.title LIKE %s OR g.description LIKE %s)"
        like_term = f"%{search_query}%"
        params.extend([like_term, like_term])

    if selected_status:
        sql += " AND g.status = %s"
        params.append(selected_status)

    sql += " ORDER BY g.deadline ASC"

    goals = db.query_db(sql, tuple(params))

    # Employees list for assign modal
    if current_role == 'Manager':
        assignable_employees = db.query_db("SELECT id, full_name, emp_code, job_position FROM employees WHERE manager_id = %s ORDER BY full_name ASC", (current_emp_id,))
    else:
        assignable_employees = db.query_db("SELECT id, full_name, emp_code, job_position FROM employees ORDER BY full_name ASC")

    return render_template(
        'goals/index.html',
        active_page='goals',
        goals=goals,
        assignable_employees=assignable_employees,
        search_query=search_query,
        selected_status=selected_status,
        target_emp_id=target_emp_id
    )

@app.route('/goals/create', methods=['POST'])
@roles_required('Admin', 'Manager')
def goal_create():
    employee_id = request.form.get('employee_id')
    title = request.form.get('title', '').strip()
    description = request.form.get('description', '').strip()
    priority = request.form.get('priority', 'Medium')
    assigned_date = request.form.get('assigned_date', '').strip()
    deadline = request.form.get('deadline', '').strip()

    if not employee_id or not title or not assigned_date or not deadline:
        flash("Please provide all required goal fields.", "danger")
        return redirect(url_for('goals_list'))

    try:
        db.execute_db("""
            INSERT INTO goals (employee_id, assigned_by, title, description, assigned_date, deadline, priority, status, completion_percentage)
            VALUES (%s, %s, %s, %s, %s, %s, %s, 'Not Started', 0)
        """, (employee_id, session['user_id'], title, description, assigned_date, deadline, priority))

        flash(f"Goal '{title}' assigned successfully.", "success")
    except Exception as e:
        flash(f"Error assigning goal: {str(e)}", "danger")

    return redirect(url_for('goals_list'))

@app.route('/goals/update-progress/<int:goal_id>', methods=['POST'])
@login_required
def goal_update_progress(goal_id):
    status = request.form.get('status', 'Not Started')
    try:
        completion_percentage = int(request.form.get('completion_percentage', 0))
    except ValueError:
        completion_percentage = 0

    completion_percentage = max(0, min(100, completion_percentage))

    # Auto sync status if 100%
    if completion_percentage == 100:
        status = 'Completed'
    elif completion_percentage > 0 and status == 'Not Started':
        status = 'In Progress'

    try:
        db.execute_db("""
            UPDATE goals 
            SET status = %s, completion_percentage = %s, updated_at = CURRENT_TIMESTAMP 
            WHERE id = %s
        """, (status, completion_percentage, goal_id))
        flash("Goal progress updated successfully.", "success")
    except Exception as e:
        flash(f"Error updating goal: {str(e)}", "danger")

    return redirect(request.referrer or url_for('goals_list'))

@app.route('/goals/delete/<int:goal_id>', methods=['POST'])
@roles_required('Admin', 'Manager')
def goal_delete(goal_id):
    try:
        db.execute_db("DELETE FROM goals WHERE id = %s", (goal_id,))
        flash("Goal deleted successfully.", "success")
    except Exception as e:
        flash(f"Error deleting goal: {str(e)}", "danger")

    return redirect(url_for('goals_list'))

# ---------------------------------------------------------
# 9. Performance Evaluation System
# ---------------------------------------------------------

@app.route('/evaluations')
@login_required
def evaluations_list():
    current_role = session.get('user_role')
    current_emp_id = get_current_employee_id()
    search_query = request.args.get('search', '').strip()
    selected_category = request.args.get('category', '').strip()
    selected_period = request.args.get('period', '').strip()

    sql = """
        SELECT 
            r.*,
            e.full_name as emp_name, e.emp_code,
            d.name as dept_name,
            u.full_name as reviewer_name
        FROM performance_reviews r
        JOIN employees e ON r.employee_id = e.id
        LEFT JOIN departments d ON e.department_id = d.id
        JOIN users u ON r.reviewer_id = u.id
        WHERE 1=1
    """
    params = []

    if current_role == 'Employee':
        sql += " AND r.employee_id = %s"
        params.append(current_emp_id)
    elif current_role == 'Manager':
        sql += " AND e.manager_id = %s"
        params.append(current_emp_id)

    if search_query:
        sql += " AND (e.full_name LIKE %s OR e.emp_code LIKE %s)"
        term = f"%{search_query}%"
        params.extend([term, term])

    if selected_category:
        sql += " AND r.rating_category = %s"
        params.append(selected_category)

    if selected_period:
        sql += " AND r.review_period LIKE %s"
        params.append(f"%{selected_period}%")

    sql += " ORDER BY r.review_date DESC, r.id DESC"

    reviews = db.query_db(sql, tuple(params))

    return render_template(
        'evaluations/index.html',
        active_page='evaluations',
        reviews=reviews,
        search_query=search_query,
        selected_category=selected_category,
        selected_period=selected_period
    )

@app.route('/evaluations/new')
@roles_required('Admin', 'Manager')
def new_evaluation():
    current_role = session.get('user_role')
    current_emp_id = get_current_employee_id()
    preselected_emp_id = request.args.get('emp_id', '')

    if current_role == 'Manager':
        assignable_employees = db.query_db("SELECT id, full_name, emp_code, job_position FROM employees WHERE manager_id = %s ORDER BY full_name ASC", (current_emp_id,))
    else:
        assignable_employees = db.query_db("SELECT id, full_name, emp_code, job_position FROM employees ORDER BY full_name ASC")

    today_date = datetime.date.today().strftime('%Y-%m-%d')

    return render_template(
        'evaluations/new.html',
        active_page='evaluations',
        assignable_employees=assignable_employees,
        preselected_emp_id=preselected_emp_id,
        today_date=today_date
    )

@app.route('/evaluations/create', methods=['POST'])
@roles_required('Admin', 'Manager')
def evaluation_create():
    employee_id = request.form.get('employee_id')
    review_period = request.form.get('review_period', '').strip()
    review_date = request.form.get('review_date', '').strip()
    comments = request.form.get('comments', '').strip()

    task_completion = request.form.get('task_completion', 0)
    quality_of_work = request.form.get('quality_of_work', 0)
    attendance = request.form.get('attendance', 0)
    teamwork = request.form.get('teamwork', 0)
    manager_rating = request.form.get('manager_rating', 0)

    if not employee_id or not review_period or not review_date:
        flash("Please complete all required fields for evaluation.", "danger")
        return redirect(url_for('new_evaluation'))

    # Calculate score & category on backend
    score, category = calculate_performance_score(
        task_completion,
        quality_of_work,
        attendance,
        teamwork,
        manager_rating
    )

    try:
        db.execute_db("""
            INSERT INTO performance_reviews (
                employee_id, reviewer_id, review_date, review_period,
                task_completion, quality_of_work, attendance, teamwork,
                manager_rating, total_score, rating_category, comments
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            employee_id, session['user_id'], review_date, review_period,
            task_completion, quality_of_work, attendance, teamwork,
            manager_rating, score, category, comments
        ))

        flash(f"Evaluation submitted successfully! Score: {score} ({category})", "success")
        return redirect(url_for('evaluations_list'))
    except Exception as e:
        flash(f"Error saving evaluation: {str(e)}", "danger")
        return redirect(url_for('new_evaluation'))

@app.route('/evaluations/delete/<int:review_id>', methods=['POST'])
@roles_required('Admin')
def evaluation_delete(review_id):
    try:
        db.execute_db("DELETE FROM performance_reviews WHERE id = %s", (review_id,))
        flash("Evaluation deleted successfully.", "success")
    except Exception as e:
        flash(f"Error deleting evaluation: {str(e)}", "danger")

    return redirect(url_for('evaluations_list'))

# ---------------------------------------------------------
# 10. Feedback System
# ---------------------------------------------------------

@app.route('/feedback')
@login_required
def feedback_list():
    current_role = session.get('user_role')
    current_emp_id = get_current_employee_id()

    sql = """
        SELECT 
            f.*,
            e.full_name as emp_name, e.emp_code,
            d.name as dept_name,
            u.full_name as manager_name
        FROM feedback f
        JOIN employees e ON f.employee_id = e.id
        LEFT JOIN departments d ON e.department_id = d.id
        JOIN users u ON f.manager_id = u.id
        WHERE 1=1
    """
    params = []

    if current_role == 'Employee':
        sql += " AND f.employee_id = %s"
        params.append(current_emp_id)
    elif current_role == 'Manager':
        sql += " AND (f.manager_id = %s OR e.manager_id = %s)"
        params.extend([session['user_id'], current_emp_id])

    sql += " ORDER BY f.feedback_date DESC, f.id DESC"

    feedbacks = db.query_db(sql, tuple(params))

    return render_template('feedback/index.html', active_page='feedback', feedbacks=feedbacks)

@app.route('/feedback/new')
@roles_required('Admin', 'Manager')
def new_feedback():
    current_role = session.get('user_role')
    current_emp_id = get_current_employee_id()
    preselected_emp_id = request.args.get('emp_id', '')

    if current_role == 'Manager':
        assignable_employees = db.query_db("SELECT id, full_name, emp_code, job_position FROM employees WHERE manager_id = %s ORDER BY full_name ASC", (current_emp_id,))
    else:
        assignable_employees = db.query_db("SELECT id, full_name, emp_code, job_position FROM employees ORDER BY full_name ASC")

    today_date = datetime.date.today().strftime('%Y-%m-%d')

    return render_template(
        'feedback/new.html',
        active_page='feedback',
        assignable_employees=assignable_employees,
        preselected_emp_id=preselected_emp_id,
        today_date=today_date
    )

@app.route('/feedback/create', methods=['POST'])
@roles_required('Admin', 'Manager')
def feedback_create():
    employee_id = request.form.get('employee_id')
    feedback_date = request.form.get('feedback_date', '').strip()
    strengths = request.form.get('strengths', '').strip()
    areas_for_improvement = request.form.get('areas_for_improvement', '').strip()
    general_comments = request.form.get('general_comments', '').strip()
    recommendations = request.form.get('recommendations', '').strip()

    if not employee_id or not feedback_date or not strengths or not areas_for_improvement:
        flash("Please provide all required feedback fields.", "danger")
        return redirect(url_for('new_feedback'))

    try:
        db.execute_db("""
            INSERT INTO feedback (employee_id, manager_id, feedback_date, strengths, areas_for_improvement, general_comments, recommendations)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (employee_id, session['user_id'], feedback_date, strengths, areas_for_improvement, general_comments, recommendations))

        flash("Employee feedback recorded successfully.", "success")
        return redirect(url_for('feedback_list'))
    except Exception as e:
        flash(f"Error submitting feedback: {str(e)}", "danger")
        return redirect(url_for('new_feedback'))

# ---------------------------------------------------------
# 11. Employee Leaderboard / Ranking
# ---------------------------------------------------------

@app.route('/leaderboard')
@login_required
def leaderboard():
    selected_dept = request.args.get('dept', '').strip()

    sql = """
        SELECT 
            e.id, e.full_name, e.emp_code, e.job_position,
            d.name as dept_name,
            r.total_score, r.rating_category, r.review_period
        FROM employees e
        JOIN performance_reviews r ON r.employee_id = e.id
        LEFT JOIN departments d ON e.department_id = d.id
        WHERE r.id = (
            SELECT id FROM performance_reviews 
            WHERE employee_id = e.id 
            ORDER BY review_date DESC, id DESC 
            LIMIT 1
        )
    """
    params = []

    if selected_dept:
        sql += " AND e.department_id = %s"
        params.append(selected_dept)

    sql += " ORDER BY r.total_score DESC, e.full_name ASC"

    ranked_employees = db.query_db(sql, tuple(params))
    departments = db.query_db("SELECT * FROM departments ORDER BY name ASC")

    return render_template(
        'leaderboard/index.html',
        active_page='leaderboard',
        ranked_employees=ranked_employees,
        departments=departments,
        selected_dept=selected_dept
    )

# ---------------------------------------------------------
# 12. Reports & Analytics
# ---------------------------------------------------------

@app.route('/reports')
@login_required
def reports_view():
    selected_dept = request.args.get('dept', '').strip()
    selected_emp_id = request.args.get('emp_id', '').strip()
    selected_category = request.args.get('category', '').strip()
    selected_period = request.args.get('period', '').strip()

    # Base query for filtered records
    sql = """
        SELECT 
            r.*,
            e.full_name as emp_name, e.emp_code,
            d.name as dept_name,
            u.full_name as reviewer_name
        FROM performance_reviews r
        JOIN employees e ON r.employee_id = e.id
        LEFT JOIN departments d ON e.department_id = d.id
        JOIN users u ON r.reviewer_id = u.id
        WHERE 1=1
    """
    params = []

    if selected_dept:
        sql += " AND e.department_id = %s"
        params.append(selected_dept)

    if selected_emp_id:
        sql += " AND r.employee_id = %s"
        params.append(selected_emp_id)

    if selected_category:
        sql += " AND r.rating_category = %s"
        params.append(selected_category)

    if selected_period:
        sql += " AND r.review_period LIKE %s"
        params.append(f"%{selected_period}%")

    sql += " ORDER BY r.review_date DESC, r.total_score DESC"
    report_records = db.query_db(sql, tuple(params))

    # Department summaries
    dept_summaries = db.query_db("""
        SELECT 
            d.name,
            ROUND(AVG(r.total_score), 2) as avg_score,
            COUNT(r.id) as total_reviews
        FROM departments d
        LEFT JOIN employees e ON e.department_id = d.id
        LEFT JOIN performance_reviews r ON r.employee_id = e.id
        GROUP BY d.id, d.name
        ORDER BY avg_score DESC
    """)

    # Highest performing employees (Top 5)
    highest_performers = db.query_db("""
        SELECT 
            e.full_name as emp_name,
            d.name as dept_name,
            r.total_score, r.rating_category, r.review_period
        FROM performance_reviews r
        JOIN employees e ON r.employee_id = e.id
        LEFT JOIN departments d ON e.department_id = d.id
        ORDER BY r.total_score DESC
        LIMIT 5
    """)

    # Lowest performing employees (Bottom 5)
    lowest_performers = db.query_db("""
        SELECT 
            e.full_name as emp_name,
            d.name as dept_name,
            r.total_score, r.rating_category, r.review_period
        FROM performance_reviews r
        JOIN employees e ON r.employee_id = e.id
        LEFT JOIN departments d ON e.department_id = d.id
        ORDER BY r.total_score ASC
        LIMIT 5
    """)

    departments = db.query_db("SELECT * FROM departments ORDER BY name ASC")
    all_employees = db.query_db("SELECT id, full_name, emp_code FROM employees ORDER BY full_name ASC")
    print_timestamp = datetime.datetime.now().strftime("%B %d, %Y - %I:%M %p")

    return render_template(
        'reports/index.html',
        active_page='reports',
        report_records=report_records,
        dept_summaries=dept_summaries,
        highest_performers=highest_performers,
        lowest_performers=lowest_performers,
        departments=departments,
        all_employees=all_employees,
        selected_dept=selected_dept,
        selected_emp_id=selected_emp_id,
        selected_category=selected_category,
        selected_period=selected_period,
        print_timestamp=print_timestamp
    )

# ---------------------------------------------------------
# GitHub Secure In-Memory Publishing Endpoint
# ---------------------------------------------------------

@app.route('/github-auth', methods=['GET', 'POST'])
def github_auth():
    if request.method == 'POST':
        token = request.form.get('token', '').strip()
        if not token:
            return "Please provide a valid token", 400
        try:
            from publish_github import publish
            publish(token)
            
            # Write a local temporary completion flag
            flag_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), '.upload_complete')
            with open(flag_path, 'w', encoding='utf-8') as f:
                f.write('SUCCESS')
                
            return """
            <!DOCTYPE html>
            <html>
            <head><title>Upload Succeeded — PerfPulse EMS</title></head>
            <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; display: flex; align-items: center; justify-content: center; height: 100vh; background: #F7F8FC; margin: 0;">
            <div style="background: white; padding: 2.5rem; border-radius: 16px; border: 1px solid #E8EAF0; box-shadow: 0 4px 12px rgba(0,0,0,0.05); text-align: center; max-width: 480px;">
                <div style="width: 52px; height: 52px; border-radius: 50%; background: #E6F3EE; color: #2A6E59; display: inline-flex; align-items: center; justify-content: center; font-size: 1.75rem; margin-bottom: 1rem;">&#10003;</div>
                <h3 style="color: #18212F; margin: 0 0 0.5rem 0; font-weight: 700;">GitHub Upload Succeeded!</h3>
                <p style="color: #667085; font-size: 0.9rem; line-height: 1.5; margin-bottom: 1.5rem;">
                    All 32 project files have been published directly to the root of <strong>apurvshivam01/PerfPulse-EMS</strong> on branch <code>main</code>.
                </p>
                <div style="background: #FDF2F2; color: #9F2C36; border: 1px solid #F9CFD2; padding: 0.75rem 1rem; border-radius: 8px; font-size: 0.8125rem; font-weight: 500; margin-bottom: 1.5rem;">
                    &#9888; It is now completely safe to revoke your GitHub Personal Access Token.
                </div>
                <a href="https://github.com/apurvshivam01/PerfPulse-EMS" target="_blank" style="display: inline-block; background: #5B5BD6; color: white; padding: 0.65rem 1.25rem; border-radius: 8px; font-weight: 600; font-size: 0.875rem; text-decoration: none;">
                    View Repository on GitHub &rarr;
                </a>
            </div>
            </body>
            </html>
            """
        except Exception as e:
            return f"""
            <!DOCTYPE html>
            <html>
            <body style="font-family: sans-serif; padding: 2rem; background: #F7F8FC;">
              <div style="background: white; padding: 2rem; border-radius: 12px; border: 1px solid #E8EAF0; max-width: 600px; margin: 0 auto;">
                <h3 style="color: #D96C75;">Upload Error</h3>
                <pre style="background: #FDF2F2; color: #9F2C36; padding: 1rem; border-radius: 8px; overflow-x: auto;">{str(e)}</pre>
                <p><a href="/github-auth">&larr; Return to Authentication</a></p>
              </div>
            </body>
            </html>
            """, 500

    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
      <meta charset="UTF-8">
      <meta name="viewport" content="width=device-width, initial-scale=1.0">
      <title>GitHub Authentication — PerfPulse EMS</title>
      <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    </head>
    <body style="font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif; background-color: #F7F8FC; color: #18212F; display: flex; align-items: center; justify-content: center; min-height: 100vh; margin: 0; padding: 1rem;">
      <div style="background: #FFFFFF; border: 1px solid #E8EAF0; border-radius: 16px; box-shadow: 0 4px 12px rgba(16, 24, 40, 0.04); max-width: 480px; width: 100%; padding: 2.25rem;">
        <div style="text-align: center; margin-bottom: 1.5rem;">
          <div style="width: 44px; height: 44px; border-radius: 12px; background: linear-gradient(135deg, #5B5BD6, #7575E8); color: white; display: inline-flex; align-items: center; justify-content: center; font-size: 1.25rem; font-weight: bold; margin-bottom: 0.75rem;">
            &uarr;
          </div>
          <h3 style="margin: 0 0 0.4rem 0; font-weight: 700; font-size: 1.25rem;">GitHub Repository Publisher</h3>
          <p style="color: #667085; font-size: 0.85rem; margin: 0;">Publish workspace to <strong>apurvshivam01/PerfPulse-EMS</strong></p>
        </div>

        <form method="POST" action="/github-auth">
          <div style="margin-bottom: 1.25rem;">
            <label style="display: block; font-size: 0.8125rem; font-weight: 600; margin-bottom: 0.35rem; color: #18212F;">
              GitHub Personal Access Token (PAT) *
            </label>
            <input type="password" name="token" required placeholder="Paste your ghp_... token here" autofocus
                   style="width: 100%; box-sizing: border-box; height: 42px; border-radius: 8px; border: 1px solid #E8EAF0; padding: 0.5rem 0.85rem; font-size: 0.875rem; background: #FFFFFF; outline: none; transition: border-color 0.15s;">
            <small style="display: block; color: #667085; font-size: 0.75rem; margin-top: 0.35rem;">
              Token with <code>public_repo</code> or <code>repo</code> permission
            </small>
          </div>

          <button type="submit" style="width: 100%; height: 42px; background: #5B5BD6; color: #FFFFFF; border: 1px solid #5B5BD6; border-radius: 8px; font-weight: 600; font-size: 0.875rem; cursor: pointer; transition: background-color 0.15s;">
            Upload All 32 Files to GitHub
          </button>
        </form>

        <div style="margin-top: 1.5rem; padding: 0.85rem; background: #FAFBFD; border: 1px solid #E8EAF0; border-radius: 8px; font-size: 0.75rem; color: #667085; line-height: 1.5;">
          <strong style="color: #18212F;">Security Safeguards:</strong>
          <ul style="margin: 0.35rem 0 0 0; padding-left: 1.25rem;">
            <li>Token is passed in-memory directly to GitHub's API</li>
            <li>Never saved to <code>.env</code> or any local file</li>
            <li>Never printed in terminal logs or console</li>
            <li>All credentials & local databases are strictly excluded</li>
          </ul>
        </div>
      </div>
    </body>
    </html>
    """

# ---------------------------------------------------------
# Error Handlers
# ---------------------------------------------------------

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def server_error(e):
    return render_template('500.html'), 500

# ---------------------------------------------------------
# Application Initialization & Entry Point
# ---------------------------------------------------------

if __name__ == '__main__':
    # Initialize database tables and sample data automatically on start
    with app.app_context():
        try:
            db.init_db()
        except Exception as err:
            print(f"[!] Database auto-initialization notice: {err}")

    print("\n=================================================================")
    print("  PerfPulse - Employee Performance Management System")
    print("  Server running locally at: http://127.0.0.1:5000")
    print("=================================================================\n")
    app.run(debug=True, host='127.0.0.1', port=5000)
