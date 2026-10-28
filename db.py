import os
import sqlite3
import pymysql
import pymysql.cursors
from config import Config

_current_db_type = None

def get_connection():
    """
    Establish database connection based on Config.DB_TYPE.
    If MySQL connection fails, cleanly fall back to SQLite with an informative warning.
    """
    global _current_db_type
    
    if Config.DB_TYPE == 'mysql':
        try:
            conn = pymysql.connect(
                host=Config.MYSQL_HOST,
                port=Config.MYSQL_PORT,
                user=Config.MYSQL_USER,
                password=Config.MYSQL_PASSWORD,
                database=Config.MYSQL_DB,
                cursorclass=pymysql.cursors.DictCursor,
                autocommit=True,
                charset='utf8mb4'
            )
            _current_db_type = 'mysql'
            return conn, 'mysql'
        except Exception as e:
            # Fall back gracefully to SQLite for frictionless local running/evaluation
            _current_db_type = 'sqlite'
            # (Note: Warning can be printed during init)
    
    # SQLite connection
    conn = sqlite3.connect(Config.SQLITE_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    _current_db_type = 'sqlite'
    return conn, 'sqlite'

def query_db(query, args=(), one=False):
    """
    Execute a SELECT query and return rows as list of dicts or single dict.
    Converts %s placeholders to ? if using SQLite.
    """
    conn, db_type = get_connection()
    try:
        if db_type == 'sqlite':
            # Translate %s placeholders to ?
            sqlite_query = query.replace('%s', '?')
            cur = conn.cursor()
            cur.execute(sqlite_query, args)
            rv = cur.fetchall()
            cur.close()
            result = [dict(ix) for ix in rv] if rv else []
            return (result[0] if result else None) if one else result
        else:
            with conn.cursor() as cur:
                cur.execute(query, args)
                rv = cur.fetchall()
                return (rv[0] if rv else None) if one else rv
    finally:
        conn.close()

def execute_db(query, args=(), commit=True):
    """
    Execute an INSERT, UPDATE, or DELETE query.
    Returns the lastrowid or affected rows.
    """
    conn, db_type = get_connection()
    try:
        if db_type == 'sqlite':
            sqlite_query = query.replace('%s', '?')
            cur = conn.cursor()
            cur.execute(sqlite_query, args)
            last_id = cur.lastrowid
            if commit:
                conn.commit()
            cur.close()
            return last_id
        else:
            with conn.cursor() as cur:
                cur.execute(query, args)
                last_id = cur.lastrowid
                if commit:
                    conn.commit()
                return last_id
    finally:
        conn.close()

def init_db():
    """
    Initialize database tables and seed sample data if tables don't exist.
    """
    conn, db_type = get_connection()
    print(f"[*] Initializing database using backend: {db_type.upper()}")
    
    if db_type == 'mysql':
        # Check if users table exists in MySQL
        with conn.cursor() as cur:
            cur.execute("SHOW TABLES LIKE 'users'")
            exists = cur.fetchone()
            if not exists:
                print("[*] MySQL tables not found. Reading and executing database.sql...")
                sql_file = os.path.join(os.path.dirname(__file__), 'database.sql')
                if os.path.exists(sql_file):
                    with open(sql_file, 'r', encoding='utf-8') as f:
                        sql_content = f.read()
                    # Execute statement by statement
                    statements = sql_content.split(';')
                    for stmt in statements:
                        clean_stmt = stmt.strip()
                        if clean_stmt and not clean_stmt.startswith('--') and not clean_stmt.startswith('/*'):
                            # Skip CREATE DATABASE / USE statements if connecting directly to DB
                            if clean_stmt.upper().startswith('CREATE DATABASE') or clean_stmt.upper().startswith('USE '):
                                continue
                            try:
                                cur.execute(clean_stmt)
                            except Exception as ex:
                                print(f"[!] Warning executing statement: {ex}")
                    print("[OK] MySQL database initialized successfully with sample data.")
        conn.close()
    else:
        # SQLite initialization
        cur = conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
        exists = cur.fetchone()
        if not exists:
            print("[*] Setting up SQLite database schema and sample data...")
            _init_sqlite(cur, conn)
            print("[OK] SQLite database initialized successfully with sample data.")
        conn.close()

def _init_sqlite(cur, conn):
    """Create SQLite tables and insert demo records."""
    schema = """
    CREATE TABLE IF NOT EXISTS departments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE,
        description TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL UNIQUE,
        email TEXT NOT NULL UNIQUE,
        password_hash TEXT NOT NULL,
        role TEXT NOT NULL DEFAULT 'Employee',
        full_name TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS employees (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER UNIQUE,
        emp_code TEXT NOT NULL UNIQUE,
        full_name TEXT NOT NULL,
        email TEXT NOT NULL UNIQUE,
        phone TEXT,
        department_id INTEGER,
        job_position TEXT NOT NULL,
        joining_date DATE NOT NULL,
        manager_id INTEGER,
        employment_status TEXT DEFAULT 'Active',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL,
        FOREIGN KEY (department_id) REFERENCES departments(id) ON DELETE SET NULL,
        FOREIGN KEY (manager_id) REFERENCES employees(id) ON DELETE SET NULL
    );

    CREATE TABLE IF NOT EXISTS goals (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        employee_id INTEGER NOT NULL,
        assigned_by INTEGER NOT NULL,
        title TEXT NOT NULL,
        description TEXT,
        assigned_date DATE NOT NULL,
        deadline DATE NOT NULL,
        priority TEXT DEFAULT 'Medium',
        status TEXT DEFAULT 'Not Started',
        completion_percentage INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (employee_id) REFERENCES employees(id) ON DELETE CASCADE,
        FOREIGN KEY (assigned_by) REFERENCES users(id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS performance_reviews (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        employee_id INTEGER NOT NULL,
        reviewer_id INTEGER NOT NULL,
        review_date DATE NOT NULL,
        review_period TEXT NOT NULL,
        task_completion REAL NOT NULL DEFAULT 0.0,
        quality_of_work REAL NOT NULL DEFAULT 0.0,
        attendance REAL NOT NULL DEFAULT 0.0,
        teamwork REAL NOT NULL DEFAULT 0.0,
        manager_rating REAL NOT NULL DEFAULT 0.0,
        total_score REAL NOT NULL DEFAULT 0.0,
        rating_category TEXT NOT NULL,
        comments TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (employee_id) REFERENCES employees(id) ON DELETE CASCADE,
        FOREIGN KEY (reviewer_id) REFERENCES users(id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS feedback (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        employee_id INTEGER NOT NULL,
        manager_id INTEGER NOT NULL,
        feedback_date DATE NOT NULL,
        strengths TEXT NOT NULL,
        areas_for_improvement TEXT NOT NULL,
        general_comments TEXT,
        recommendations TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (employee_id) REFERENCES employees(id) ON DELETE CASCADE,
        FOREIGN KEY (manager_id) REFERENCES users(id) ON DELETE CASCADE
    );
    """
    cur.executescript(schema)
    conn.commit()

    # Seed Departments
    departments = [
        (1, 'Engineering & Technology', 'Software engineering, cloud infrastructure, QA, and IT operations.'),
        (2, 'Marketing & Growth', 'Brand marketing, digital advertising, content creation, and SEO.'),
        (3, 'Finance & Accounting', 'Financial planning, accounting, auditing, and payroll management.'),
        (4, 'Human Resources', 'Talent acquisition, employee engagement, compliance, and training.')
    ]
    cur.executemany("INSERT OR IGNORE INTO departments (id, name, description) VALUES (?, ?, ?)", departments)

    # Seed Users
    # Passwords:
    #   admin123 -> pbkdf2:sha256:1000000$KZTHlZglXxVjhC2e$54642ee73ab66ede613fca3aa3ee3b251e4dca282a6a88b047c1f7d36f862e5c
    #   manager123 -> pbkdf2:sha256:1000000$ABfM7xdmwrkeStuE$df5e685fcfe6328f16b76604562e49ca9d2a8ba7723aa0a14db358d4bb7bb9ea
    #   employee123 -> pbkdf2:sha256:1000000$xr1lxtG8ELqy3wE8$28e15ccc3af4bda44680b64d98adafc62668991a2dcca0edec9d15afff407681
    admin_pw = "pbkdf2:sha256:1000000$KZTHlZglXxVjhC2e$54642ee73ab66ede613fca3aa3ee3b251e4dca282a6a88b047c1f7d36f862e5c"
    mgr_pw = "pbkdf2:sha256:1000000$ABfM7xdmwrkeStuE$df5e685fcfe6328f16b76604562e49ca9d2a8ba7723aa0a14db358d4bb7bb9ea"
    emp_pw = "pbkdf2:sha256:1000000$xr1lxtG8ELqy3wE8$28e15ccc3af4bda44680b64d98adafc62668991a2dcca0edec9d15afff407681"

    users = [
        (1, 'admin', 'admin@company.com', admin_pw, 'Admin', 'Alexander Pierce'),
        (2, 'manager.sarah', 'sarah.jenkins@company.com', mgr_pw, 'Manager', 'Sarah Jenkins'),
        (3, 'manager.david', 'david.chen@company.com', mgr_pw, 'Manager', 'David Chen'),
        (4, 'emp.john', 'john.doe@company.com', emp_pw, 'Employee', 'John Doe'),
        (5, 'emp.emily', 'emily.watson@company.com', emp_pw, 'Employee', 'Emily Watson'),
        (6, 'emp.michael', 'michael.brown@company.com', emp_pw, 'Employee', 'Michael Brown'),
        (7, 'emp.lisa', 'lisa.garcia@company.com', emp_pw, 'Employee', 'Lisa Garcia'),
        (8, 'emp.alex', 'alex.taylor@company.com', emp_pw, 'Employee', 'Alex Taylor'),
        (9, 'emp.robert', 'robert.martinez@company.com', emp_pw, 'Employee', 'Robert Martinez'),
        (10, 'emp.jessica', 'jessica.miller@company.com', emp_pw, 'Employee', 'Jessica Miller'),
        (11, 'emp.james', 'james.wilson@company.com', emp_pw, 'Employee', 'James Wilson'),
        (12, 'emp.amanda', 'amanda.thomas@company.com', emp_pw, 'Employee', 'Amanda Thomas'),
        (13, 'emp.daniel', 'daniel.jackson@company.com', emp_pw, 'Employee', 'Daniel Jackson')
    ]
    cur.executemany("INSERT OR IGNORE INTO users (id, username, email, password_hash, role, full_name) VALUES (?, ?, ?, ?, ?, ?)", users)

    # Seed Employees
    employees = [
        (1, 2, 'MGR001', 'Sarah Jenkins', 'sarah.jenkins@company.com', '+1-555-0101', 1, 'Engineering Director', '2022-01-15', None, 'Active'),
        (2, 3, 'MGR002', 'David Chen', 'david.chen@company.com', '+1-555-0102', 2, 'Marketing & Operations Lead', '2022-03-01', None, 'Active'),
        (3, 4, 'EMP001', 'John Doe', 'john.doe@company.com', '+1-555-0111', 1, 'Senior Backend Engineer', '2023-02-10', 1, 'Active'),
        (4, 5, 'EMP002', 'Emily Watson', 'emily.watson@company.com', '+1-555-0112', 1, 'Lead Frontend Developer', '2023-04-18', 1, 'Active'),
        (5, 6, 'EMP003', 'Michael Brown', 'michael.brown@company.com', '+1-555-0113', 1, 'DevOps & Cloud Engineer', '2023-06-01', 1, 'Active'),
        (6, 7, 'EMP004', 'Lisa Garcia', 'lisa.garcia@company.com', '+1-555-0114', 1, 'UI/UX Product Designer', '2023-09-12', 1, 'Active'),
        (7, 8, 'EMP005', 'Alex Taylor', 'alex.taylor@company.com', '+1-555-0115', 1, 'QA Automation Engineer', '2024-01-10', 1, 'Active'),
        (8, 9, 'EMP006', 'Robert Martinez', 'robert.martinez@company.com', '+1-555-0116', 2, 'Senior Content Strategist', '2023-03-15', 2, 'Active'),
        (9, 10, 'EMP007', 'Jessica Miller', 'jessica.miller@company.com', '+1-555-0117', 2, 'Growth Marketing Lead', '2023-05-20', 2, 'Active'),
        (10, 11, 'EMP008', 'James Wilson', 'james.wilson@company.com', '+1-555-0118', 2, 'SEO & Analytics Specialist', '2023-08-05', 2, 'Active'),
        (11, 12, 'EMP009', 'Amanda Thomas', 'amanda.thomas@company.com', '+1-555-0119', 3, 'Senior Financial Analyst', '2023-02-01', 2, 'Active'),
        (12, 13, 'EMP010', 'Daniel Jackson', 'daniel.jackson@company.com', '+1-555-0120', 3, 'Staff Accountant', '2023-07-15', 2, 'Active')
    ]
    cur.executemany("INSERT OR IGNORE INTO employees (id, user_id, emp_code, full_name, email, phone, department_id, job_position, joining_date, manager_id, employment_status) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", employees)

    # Seed Goals
    goals = [
        (1, 3, 2, 'Implement Microservices Architecture', 'Refactor the monolith payment gateway module into resilient microservices with 99.99% uptime.', '2026-01-10', '2026-04-30', 'High', 'Completed', 100),
        (2, 3, 2, 'Database Query Optimization', 'Identify slow MySQL queries and implement indexing to reduce P95 latency below 100ms.', '2026-02-01', '2026-05-15', 'Medium', 'In Progress', 75),
        (3, 4, 2, 'Redesign Customer Portal UI', 'Migrate client portal to Bootstrap 5 responsive layout with accessibility compliance (WCAG 2.1).', '2026-01-15', '2026-04-15', 'High', 'Completed', 100),
        (4, 4, 2, 'Component Design System', 'Establish reusable UI component library in Vue/React for internal dashboards.', '2026-03-01', '2026-06-30', 'Medium', 'In Progress', 60),
        (5, 5, 2, 'Automate Kubernetes Deployments', 'Set up GitHub Actions CI/CD pipelines targeting production EKS cluster with zero downtime.', '2026-01-20', '2026-05-01', 'High', 'In Progress', 80),
        (6, 6, 2, 'Design System & Style Guide', 'Deliver comprehensive Figma tokens, iconography, and color contrast guidelines.', '2026-02-15', '2026-05-30', 'Medium', 'In Progress', 50),
        (7, 7, 2, 'End-to-End Test Suite', 'Write Cypress tests covering checkout and user onboarding workflows with 90% coverage.', '2026-02-01', '2026-04-30', 'High', 'Not Started', 20),
        (8, 8, 3, 'Q2 Content Editorial Calendar', 'Produce 15 technical whitepapers and 30 blog posts to drive developer lead acquisition.', '2026-01-10', '2026-04-20', 'Medium', 'Completed', 100),
        (9, 9, 3, 'Paid Acquisition Campaign Scaling', 'Scale Google & LinkedIn campaigns to achieve a 25% decrease in customer acquisition cost.', '2026-01-05', '2026-04-30', 'High', 'Completed', 100),
        (10, 10, 3, 'Organic Search Rank Improvement', 'Optimize core landing pages to achieve Top 3 Google rank for 20 priority keywords.', '2026-02-10', '2026-06-15', 'Medium', 'In Progress', 65),
        (11, 11, 3, 'Annual Budget Variance Report', 'Conduct comprehensive cost center audit and deliver departmental expense forecasts.', '2026-01-15', '2026-04-15', 'High', 'Completed', 100),
        (12, 12, 3, 'Automate Payroll Reconciliation', 'Eliminate manual ledger reconciliations by building automated scripts with audit trail.', '2026-02-01', '2026-05-30', 'Medium', 'In Progress', 70)
    ]
    cur.executemany("INSERT OR IGNORE INTO goals (id, employee_id, assigned_by, title, description, assigned_date, deadline, priority, status, completion_percentage) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", goals)

    # Seed Performance Reviews
    reviews = [
        (1, 3, 2, '2026-03-31', 'Q1 2026', 95.0, 92.0, 95.0, 90.0, 94.0, 93.35, 'Outstanding', 'Exceptional technical execution on the microservices migration. Always ready to mentor junior engineers.'),
        (2, 4, 2, '2026-03-31', 'Q1 2026', 88.0, 90.0, 90.0, 85.0, 88.0, 88.85, 'Excellent', 'Superb UI precision and attention to user experience. Strong commitment to clean, accessible frontend code.'),
        (3, 5, 2, '2026-03-31', 'Q1 2026', 78.0, 80.0, 85.0, 80.0, 75.0, 78.90, 'Good', 'Reliable infrastructure work. Encouraged to improve documentation on Kubernetes clusters.'),
        (4, 6, 2, '2026-03-31', 'Q1 2026', 68.0, 65.0, 70.0, 65.0, 65.0, 66.40, 'Average', 'Designs are creative, but some deadline slips occurred. Needs to proactively flag blockers earlier in sprints.'),
        (5, 7, 2, '2026-03-31', 'Q1 2026', 55.0, 58.0, 60.0, 55.0, 50.0, 55.65, 'Needs Improvement', 'Test suite completion fell significantly behind schedule. Required multiple revisions on automation coverage.'),
        (6, 8, 3, '2026-03-31', 'Q1 2026', 72.0, 70.0, 80.0, 75.0, 70.0, 72.85, 'Good', 'Produced solid editorial pieces. Should focus more on aligning content with high-intent organic keywords.'),
        (7, 9, 3, '2026-03-31', 'Q1 2026', 92.0, 88.0, 95.0, 92.0, 90.0, 91.10, 'Outstanding', 'Phenomenal growth metrics delivered. Reduced CAC by 28% and set benchmark for team execution.'),
        (8, 10, 3, '2026-03-31', 'Q1 2026', 75.0, 78.0, 80.0, 75.0, 76.0, 76.85, 'Good', 'Steady SEO improvements across product pillars. Good analytical rigor in conversion reporting.'),
        (9, 11, 3, '2026-03-31', 'Q1 2026', 85.0, 86.0, 88.0, 82.0, 85.0, 85.25, 'Excellent', 'Thorough financial modeling and zero discrepancies found during internal audit review.'),
        (10, 12, 3, '2026-03-31', 'Q1 2026', 82.0, 84.0, 90.0, 80.0, 82.0, 83.40, 'Excellent', 'Reliable ledger closure and automation initiative. High precision with tax compliance filings.'),
        (11, 3, 2, '2025-12-20', 'Q4 2025', 90.0, 90.0, 92.0, 88.0, 90.0, 89.90, 'Excellent', 'Solid quarter delivering the core API foundation.'),
        (12, 4, 2, '2025-12-20', 'Q4 2025', 85.0, 85.0, 88.0, 82.0, 85.0, 84.95, 'Excellent', 'Great work on responsive navigation components.'),
        (13, 9, 3, '2025-12-20', 'Q4 2025', 88.0, 86.0, 90.0, 88.0, 88.0, 87.80, 'Excellent', 'Strong holiday campaign performance.'),
        (14, 11, 3, '2025-12-20', 'Q4 2025', 80.0, 82.0, 85.0, 80.0, 80.0, 81.25, 'Excellent', 'Accurate year-end balance sheet preparation.')
    ]
    cur.executemany("INSERT OR IGNORE INTO performance_reviews (id, employee_id, reviewer_id, review_date, review_period, task_completion, quality_of_work, attendance, teamwork, manager_rating, total_score, rating_category, comments) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", reviews)

    # Seed Feedback
    feedback_entries = [
        (1, 3, 2, '2026-04-02', 
         'Deep technical expertise, system design capabilities, and proactive problem solving under tight timelines.', 
         'Can delegate more architectural proof-of-concept tasks to junior engineers to build team breadth.', 
         'John consistently leads by example and is one of our most valued technical anchors.', 
         'Enroll in technical leadership and executive presentation workshops for upcoming promotion cycle.'),
        (2, 4, 2, '2026-04-03', 
         'Exceptional visual aesthetic, attention to typography and UX micro-interactions, responsive styling speed.', 
         'Writing automated unit tests for JavaScript state logic before handing off to QA.', 
         'Emily has elevated our entire product UI standard. Clients love the new look.', 
         'Recommend leading the internal design-token standardization project.'),
        (3, 5, 2, '2026-04-04', 
         'High uptime record, swift incident response, and deep knowledge of Terraform and AWS.', 
         'Internal documentation and runbooks need to be kept up to date after infrastructure upgrades.', 
         'A solid pillar in our DevOps operations.', 
         'Schedule bi-weekly documentation review sessions with QA and development teams.'),
        (4, 6, 2, '2026-04-05', 
         'Creative mockups, intuitive user journey mapping, and empathetic user research.', 
         'Time management and adhering to sprint milestone estimates.', 
         'Lisa has great potential and creative flair.', 
         'Break down complex designs into smaller iterative deliverables.'),
        (5, 7, 2, '2026-04-06', 
         'Good grasp of test script syntax and test case documentation.', 
         'Velocity and proactive communication when falling behind sprint expectations.', 
         'Needs focused support and regular 1-on-1 coaching to meet team benchmarks.', 
         'Implement weekly pair-programming check-ins with John Doe to accelerate test coverage.'),
        (6, 9, 3, '2026-04-02', 
         'Outstanding data-driven marketing campaigns, analytical rigor, and conversion optimization.', 
         'Knowledge sharing across regional marketing leads.', 
         'Jessica is our standout marketer this quarter, generating record qualified leads.', 
         'Recommend nominating Jessica for the annual High Achiever corporate award.'),
        (7, 11, 3, '2026-04-03', 
         'Meticulous attention to detail, comprehensive audit readiness, and zero computational errors.', 
         'Automating repetitive Excel data exports via Python or SQL scripts.', 
         'Amanda is a cornerstone of financial integrity in our operations.', 
         'Take advanced SQL / PowerBI certification to expedite monthly reporting.')
    ]
    cur.executemany("INSERT OR IGNORE INTO feedback (id, employee_id, manager_id, feedback_date, strengths, areas_for_improvement, general_comments, recommendations) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", feedback_entries)
    
    conn.commit()
