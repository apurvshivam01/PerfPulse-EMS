import os
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
load_dotenv()

class Config:
    """Application configuration."""
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-super-secret-key-employee-performance-2026')
    
    # Database configuration
    # Can be 'mysql' or 'sqlite'
    DB_TYPE = os.environ.get('DB_TYPE', 'mysql').lower()
    
    # MySQL Settings
    MYSQL_HOST = os.environ.get('MYSQL_HOST', 'localhost')
    MYSQL_PORT = int(os.environ.get('MYSQL_PORT', 3306))
    MYSQL_USER = os.environ.get('MYSQL_USER', 'root')
    MYSQL_PASSWORD = os.environ.get('MYSQL_PASSWORD', '')
    MYSQL_DB = os.environ.get('MYSQL_DB', 'employee_performance_db')
    
    # SQLite fallback file path
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    SQLITE_PATH = os.path.join(BASE_DIR, 'employee_performance.db')
    
    # Performance Evaluation Weights
    WEIGHT_TASK_COMPLETION = 0.30
    WEIGHT_QUALITY_OF_WORK = 0.25
    WEIGHT_ATTENDANCE = 0.15
    WEIGHT_TEAMWORK = 0.15
    WEIGHT_MANAGER_RATING = 0.15

def calculate_performance_score(task_completion, quality_of_work, attendance, teamwork, manager_rating):
    """
    Calculate weighted performance score (0 to 100) and rating category.
    Formula:
      (Task Completion × 0.30)
      + (Quality of Work × 0.25)
      + (Attendance × 0.15)
      + (Teamwork × 0.15)
      + (Manager Rating × 0.15)
    """
    try:
        t = float(task_completion)
        q = float(quality_of_work)
        a = float(attendance)
        tw = float(teamwork)
        m = float(manager_rating)
    except (ValueError, TypeError):
        return 0.0, "Needs Improvement"

    score = (
        (t * Config.WEIGHT_TASK_COMPLETION) +
        (q * Config.WEIGHT_QUALITY_OF_WORK) +
        (a * Config.WEIGHT_ATTENDANCE) +
        (tw * Config.WEIGHT_TEAMWORK) +
        (m * Config.WEIGHT_MANAGER_RATING)
    )
    score = round(score, 2)
    category = get_rating_category(score)
    return score, category

def get_rating_category(score):
    """Return category based on score thresholds."""
    if score >= 90:
        return "Outstanding"
    elif score >= 80:
        return "Excellent"
    elif score >= 70:
        return "Good"
    elif score >= 60:
        return "Average"
    else:
        return "Needs Improvement"
