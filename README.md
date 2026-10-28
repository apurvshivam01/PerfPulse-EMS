# PerfPulse EMS

Employee Performance Management System

A modern, responsive, and full-stack **Employee Performance Management System** built with **Python Flask**, **MySQL**, **Bootstrap 5**, and **Chart.js**.

---

## 📌 Project Overview

**PerfPulse** enables organizations to manage employees, assign and track goals (OKRs), conduct quantitative performance reviews with weighted calculation formulas, deliver structured manager feedback, automatically categorize performance ratings, and highlight high-achieving employees on an organization-wide leaderboard.

The system features three distinct roles with tailored dashboards and granular access control:
1. **Admin**: Oversees organization metrics, manages employees (full CRUD), creates managers, manages departments, and reviews organizational analytics.
2. **Manager**: Manages assigned direct reports, tracks goal completion, conducts quantitative performance evaluations, and delivers structured coaching feedback.
3. **Employee**: Self-service portal to track personal performance trends, review manager feedback, and update assigned goal progress in real time.

---

## 🚀 Key Features

### 1. Role-Based Authentication & Security
- Secure session-based authentication using **Flask Sessions**.
- **Sign Up / Self-Service Registration** (`/signup`) for new employees with email format validation, duplicate checks, minimum 8-character password enforcement, and show/hide password toggles.
- Password hashing with **PBKDF2-HMAC-SHA256** via Werkzeug.
- Role-based route guards (`@roles_required('Admin')`, `@roles_required('Manager')`).
- SQL injection protection using parameterized queries (`%s`).
- One-click demo credentials switcher on the login page for effortless live presentations and viva demonstrations.

### 2. Multi-Role Interactive Dashboards
- **Admin Dashboard**:
  - Key statistic cards (Total Employees, Total Managers, Average Performance, Needs Improvement Count).
  - Top-performing employee spotlight banner.
  - Department performance comparison (Bar chart).
  - Rating category distribution (Doughnut chart).
  - Company-wide quarterly performance trend (Line chart).
  - Recent performance evaluations table.
- **Manager Dashboard**:
  - Scoped strictly to direct reports under the logged-in manager.
  - Team average score, team size, pending evaluations, and coaching flags.
  - Team member performance comparison chart.
  - Live team goals progress list.
- **Employee Dashboard**:
  - Welcome banner with personalized greeting, position, department, and reporting manager.
  - Current performance score card & rating category badge.
  - Goal completion rate progress indicator.
  - Latest qualitative feedback from manager.
  - Historical evaluations trend chart.

### 3. Employee Management (Full CRUD)
- **Fields**: Employee ID/Code, Full Name, Email, Phone, Department, Job Position, Joining Date, Reporting Manager, Employment Status.
- Full CRUD operations with modals:
  - Add employee (automatically generates a login account with default password).
  - Edit employee details.
  - Delete employee with confirmation dialog.
  - Search and filter by name, code, job position, and department.

### 4. Employee Profile
- Comprehensive employee overview page displaying:
  - Personal & contact details.
  - Department, job position, and reporting manager.
  - Assigned goals tab with status and progress bars.
  - Evaluation history tab with full breakdown across all 5 criteria.
  - Manager feedback tab with strengths, growth areas, comments, and recommendations.

### 5. Goal Management (OKRs)
- Managers and Admins can assign goals with:
  - Title, Description, Priority (High, Medium, Low), Assigned Date, Deadline.
  - Statuses: `Not Started`, `In Progress`, `Completed`.
- Employees can update their goal status and completion percentage (0% to 100%) via an interactive modal with a live percentage slider.

### 6. Quantitative Performance Evaluation
- Managers evaluate employees across 5 weighted criteria (0 to 100 points each):
  $$\text{Score} = (\text{Task} \times 0.30) + (\text{Quality} \times 0.25) + (\text{Attendance} \times 0.15) + (\text{Teamwork} \times 0.15) + (\text{Manager} \times 0.15)$$
- **Automatic Rating Categorization**:
  - **90 – 100**: Outstanding (Emerald)
  - **80 – 89**: Excellent (Blue)
  - **70 – 79**: Good (Cyan)
  - **60 – 69**: Average (Amber)
  - **Below 60**: Needs Improvement (Red)
- **Interactive UI**: Live JavaScript calculator dynamically updates the score and rating category badge in real time as the manager adjusts criteria inputs.

### 7. Structured Feedback System
- Managers provide structured, qualitative coaching feedback:
  - Core Strengths
  - Areas for Improvement
  - General Comments
  - Actionable Recommendations
- Employees have read-only access to feedback received from their supervisors.

### 8. Organization Leaderboard
- Real-time leaderboard ranking employees by overall evaluation scores.
- Top 3 performers highlighted with **Gold**, **Silver**, and **Bronze** podium cards and trophy badges.
- Filter rankings by department.

### 9. Reports & Analytics (With Print View)
- Filterable by Employee, Department, Rating Category, and Review Period.
- Department performance summary cards with average scores and total review counts.
- Top 5 Highest-Performing vs. Bottom 5 Lowest-Performing employees comparison.
- Full evaluation history table.
- **Print / Export PDF**: Built-in `@media print` stylesheet generates clean, printable reports hiding navigation controls.

---

## 🛠️ Technology Stack

| Layer | Technology |
|---|---|
| **Frontend** | HTML5, CSS3, JavaScript (ES6+) |
| **Styling Framework** | Bootstrap 5.3.3 & Bootstrap Icons |
| **Data Visualization** | Chart.js 4.4.2 |
| **Backend Framework** | Python 3 Flask |
| **Database** | MySQL 8.0 (with zero-config SQLite auto-fallback for local evaluation) |
| **Database Driver** | PyMySQL |
| **Authentication** | Flask Sessions & Werkzeug Security |

---

## 📂 Project Structure

```
employee-performance-system/
│
├── app.py                      # Main Flask application & routes
├── config.py                   # App configuration & calculation algorithms
├── db.py                       # Database connection manager (MySQL + SQLite)
├── database.sql                # Complete MySQL DDL schema and seed data
├── requirements.txt            # Python dependencies
├── test_system.py              # Automated test suite
├── .env.example                # Sample environment variables
├── README.md                   # Project documentation
│
├── static/
│   ├── css/
│   │   └── style.css           # Custom corporate UI styling & print CSS
│   └── js/
│       ├── main.js             # Real-time score calculator, sidebar toggle, filters
│       └── charts.js           # Chart.js initialization for dashboards
│
└── templates/
    ├── base.html               # Master layout with sidebar and top navbar
    ├── login.html              # Login page with demo credentials quick-fill
    ├── signup.html             # New Employee registration page
    ├── admin/
    │   └── dashboard.html      # Admin metrics, charts, and quick actions
    ├── manager/
    │   └── dashboard.html      # Manager team hub & pending evaluations
    ├── employee/
    │   └── dashboard.html      # Employee self-service dashboard
    ├── employees/
    │   ├── index.html          # Employee directory & CRUD modals
    │   └── profile.html        # Comprehensive employee profile view
    ├── departments/
    │   └── index.html          # Department CRUD management
    ├── managers/
    │   └── index.html          # Manager registration directory
    ├── goals/
    │   └── index.html          # Goal assignment & progress updater
    ├── evaluations/
    │   ├── index.html          # Evaluation history list
    │   └── new.html            # Evaluation form with real-time score calculator
    ├── feedback/
    │   ├── index.html          # Feedback log
    │   └── new.html            # Feedback submission form
    ├── leaderboard/
    │   └── index.html          # Top performers leaderboard & podium
    └── reports/
        └── index.html          # Reports with filters & print view
```

---

## 🔑 Demo Login Credentials

The login screen features **one-click quick-fill buttons** for each role, or you can enter credentials manually:

| Role | Username / Email | Password | Full Name | Notes |
|---|---|---|---|---|
| **Admin** | `admin` or `admin@company.com` | `admin123` | Alexander Pierce | Full system administrator access |
| **Manager** | `manager.sarah` or `sarah.jenkins@company.com` | `manager123` | Sarah Jenkins | Manages Engineering team |
| **Manager** | `manager.david` or `david.chen@company.com` | `manager123` | David Chen | Manages Marketing & Finance |
| **Employee** | `emp.john` or `john.doe@company.com` | `employee123` | John Doe | Senior Backend Engineer (Outstanding) |
| **Employee** | `emp.emily` or `emily.watson@company.com` | `employee123` | Emily Watson | Lead Frontend Developer (Excellent) |
| **Employee** | `emp.alex` or `alex.taylor@company.com` | `employee123` | Alex Taylor | QA Automation (Needs Improvement) |

*(All 10 employees can log in using `emp.<firstname>` with password `employee123`)*

---

## ⚙️ Installation & Running Locally

### Step 1: Clone or Navigate to the Project Directory
```powershell
cd employee-performance-system
```

### Step 2: Install Python Dependencies
```powershell
pip install -r requirements.txt
```

### Step 3: Database Setup

You have **two options** to run the database:

#### Option A: MySQL (Default Recommended)
1. Open your MySQL command line client or MySQL Workbench.
2. Import the included `database.sql` file:
   ```powershell
   mysql -u root -p < database.sql
   ```
3. Set your MySQL credentials in `.env` (or set environment variables):
   ```env
   DB_TYPE=mysql
   MYSQL_HOST=localhost
   MYSQL_PORT=3306
   MYSQL_USER=root
   MYSQL_PASSWORD=your_password
   MYSQL_DB=employee_performance_db
   ```

#### Option B: Zero-Config SQLite Fallback
If you are presenting the project on a computer without MySQL installed or configured, the system **automatically detects and falls back to SQLite** with pre-seeded sample data. No manual database setup is required.

### Step 4: Run the Application
```powershell
python app.py
```

Open your browser and navigate to:
```
http://127.0.0.1:5000
```

---

## 🧪 Running the Test Suite

Run the automated test suite verifying authentication, role scoping, calculations, and database integrity:
```powershell
python test_system.py
```

---

## 📸 Screenshots Overview (Placeholders)

- **Login Page**: Clean dark aesthetic with one-click demo credentials picker.
- **Admin Dashboard**: Stat widgets, department comparison bar chart, rating breakdown doughnut chart, quarterly trends line chart.
- **Leaderboard**: Podium with Gold, Silver, Bronze badges and employee rank standings.
- **Evaluation Form**: Interactive sliders with live weighted score and category calculation.
- **Printable Report**: Clean document view optimized for paper or PDF export.

---

## 🎓 College Viva / Project Q&A Guide

- **Q: Why was Flask chosen?**  
  *A: Flask is lightweight, modular, and does not impose unnecessary boilerplate, making it ideal for demonstrating full-stack architecture, clean routing, session management, and SQL integration.*
- **Q: How is the performance score calculated?**  
  *A: It uses a weighted linear combination: Task Completion (30%), Quality of Work (25%), Attendance (15%), Teamwork (15%), and Manager Rating (15%).*
- **Q: How is SQL injection prevented?**  
  *A: Parameterized SQL queries are used throughout all database calls (`%s` placeholders separated from data arguments).*
- **Q: How does role-based access work?**  
  *A: Custom Python decorators (`@login_required` and `@roles_required`) inspect the secure server-side session before granting access to route handlers.*

---

## 🔮 Future Enhancements

- PDF export via WeasyPrint / ReportLab.
- 360-degree peer-to-peer feedback.
- Automated email notifications when goals are assigned or evaluations completed.
- Skill matrix & certification tracking.

---

## 📄 License
Open source for educational and college project evaluation.
