"""
Comprehensive Test Suite for PerfPulse Employee Performance Management System
Tests authentication, role-based access, calculations, CRUD flows, and redesigned pages.
"""

import unittest
from config import calculate_performance_score, get_rating_category
import db
from app import app

class TestPerformanceSystem(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        cls.client = app.test_client()
        with app.app_context():
            db.init_db()

    def setUp(self):
        # Ensure fresh session before every test
        with self.client.session_transaction() as sess:
            sess.clear()

    def tearDown(self):
        # Clean up session after test
        self.client.get('/logout')

    # 1. Calculation Tests
    def test_performance_calculation(self):
        # Formula: (Task*0.30) + (Quality*0.25) + (Attendance*0.15) + (Teamwork*0.15) + (Manager*0.15)
        
        # Test Case 1: Outstanding (90+)
        # (95*0.30) + (92*0.25) + (95*0.15) + (90*0.15) + (94*0.15)
        # = 28.5 + 23.0 + 14.25 + 13.5 + 14.1 = 93.35
        score, cat = calculate_performance_score(95, 92, 95, 90, 94)
        self.assertEqual(score, 93.35)
        self.assertEqual(cat, "Outstanding")

        # Test Case 2: Excellent (80 - 89)
        # (85*0.30) + (85*0.25) + (85*0.15) + (85*0.15) + (85*0.15) = 85.0
        score, cat = calculate_performance_score(85, 85, 85, 85, 85)
        self.assertEqual(score, 85.0)
        self.assertEqual(cat, "Excellent")

        # Test Case 3: Good (70 - 79)
        score, cat = calculate_performance_score(75, 75, 75, 75, 75)
        self.assertEqual(score, 75.0)
        self.assertEqual(cat, "Good")

        # Test Case 4: Average (60 - 69)
        score, cat = calculate_performance_score(65, 65, 65, 65, 65)
        self.assertEqual(score, 65.0)
        self.assertEqual(cat, "Average")

        # Test Case 5: Needs Improvement (< 60)
        score, cat = calculate_performance_score(50, 50, 50, 50, 50)
        self.assertEqual(score, 50.0)
        self.assertEqual(cat, "Needs Improvement")

    # 2. Authentication Tests
    def test_login_page_renders(self):
        response = self.client.get('/login')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'PerfPulse', response.data)
        self.assertIn(b'Create Account', response.data)

    def test_signup_page_renders(self):
        response = self.client.get('/signup')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Create Account', response.data)
        self.assertIn(b'Already have an account?', response.data)

    def test_signup_validations(self):
        # 1. Password mismatch
        res = self.client.post('/signup', data={
            'full_name': 'Beta Tester',
            'username': 'beta.tester',
            'email': 'beta@company.com',
            'department_id': '1',
            'job_position': 'QA',
            'password': 'Password123',
            'confirm_password': 'MismatchPassword'
        }, follow_redirects=True)
        self.assertIn(b'Passwords do not match', res.data)

        # 2. Password < 8 characters
        res = self.client.post('/signup', data={
            'full_name': 'Beta Tester',
            'username': 'beta.tester',
            'email': 'beta@company.com',
            'department_id': '1',
            'job_position': 'QA',
            'password': 'short',
            'confirm_password': 'short'
        }, follow_redirects=True)
        self.assertIn(b'at least 8 characters long', res.data)

        # 3. Duplicate username
        res = self.client.post('/signup', data={
            'full_name': 'Admin Clone',
            'username': 'admin',
            'email': 'clone@company.com',
            'department_id': '1',
            'job_position': 'QA',
            'password': 'Password123',
            'confirm_password': 'Password123'
        }, follow_redirects=True)
        self.assertIn(b'Username is already taken', res.data)

    def test_signup_and_login_flow(self):
        # Register a new employee with unique username
        import time
        unique_suffix = int(time.time())
        res = self.client.post('/signup', data={
            'full_name': 'Sophia Loren',
            'username': f'sophia_{unique_suffix}',
            'email': f'sophia_{unique_suffix}@company.com',
            'department_id': '1',
            'job_position': 'Site Reliability Engineer',
            'password': 'Password123',
            'confirm_password': 'Password123'
        }, follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Account created successfully! Please sign in.', res.data)

        # Login with newly registered credentials
        login_res = self.client.post('/login', data={
            'username': f'sophia_{unique_suffix}',
            'password': 'Password123'
        }, follow_redirects=True)
        self.assertEqual(login_res.status_code, 200)
        self.assertIn(b'Sophia', login_res.data)

    def test_invalid_login(self):
        response = self.client.post('/login', data={
            'username': 'admin',
            'password': 'wrongpassword'
        }, follow_redirects=True)
        self.assertIn(b'Invalid credentials', response.data)

    def test_admin_flow(self):
        # Login as Admin
        response = self.client.post('/login', data={
            'username': 'admin',
            'password': 'admin123'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Alexander', response.data)

        # Admin can access Admin Dashboard
        res = self.client.get('/admin/dashboard')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Average Performance', res.data)

        # Admin can access Employees Directory
        res = self.client.get('/employees')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Employee Directory', res.data)

        # Admin can access Departments
        res = self.client.get('/departments')
        self.assertEqual(res.status_code, 200)

        # Admin can access Managers
        res = self.client.get('/managers')
        self.assertEqual(res.status_code, 200)

        # Admin can access Leaderboard
        res = self.client.get('/leaderboard')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'High Achievers Leaderboard', res.data)

        # Admin can access Reports
        res = self.client.get('/reports')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Executive Performance Report', res.data)

        # Admin can access Evaluations
        res = self.client.get('/evaluations')
        self.assertEqual(res.status_code, 200)

        # Admin can access Feedback
        res = self.client.get('/feedback')
        self.assertEqual(res.status_code, 200)

    def test_manager_flow(self):
        # Login as Manager Sarah
        response = self.client.post('/login', data={
            'username': 'manager.sarah',
            'password': 'manager123'
        }, follow_redirects=True)
        self.assertIn(b'Team Performance Hub', response.data)

        # Manager can view their team dashboard
        res = self.client.get('/manager/dashboard')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Team Members', res.data)

        # Manager can access Give Feedback form
        res = self.client.get('/feedback/new')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Performance Coaching', res.data)

        # Manager cannot access Admin Dashboard (restricted)
        res = self.client.get('/admin/dashboard', follow_redirects=True)
        self.assertIn(b'Access denied', res.data)

        # Manager cannot manage departments (Admin only)
        res = self.client.get('/departments', follow_redirects=True)
        self.assertIn(b'Access denied', res.data)

    def test_employee_flow(self):
        # Login as Employee John Doe
        response = self.client.post('/login', data={
            'username': 'emp.john',
            'password': 'employee123'
        }, follow_redirects=True)
        self.assertIn(b'John Doe', response.data)

        # Employee Dashboard
        res = self.client.get('/employee/dashboard')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Current Performance', res.data)

        # Employee can view their own profile (with redirect follow)
        res = self.client.get('/my-profile', follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'John Doe', res.data)

        # Employee can view their feedback
        res = self.client.get('/feedback')
        self.assertEqual(res.status_code, 200)

        # Employee cannot access Admin or Manager Dashboards
        res = self.client.get('/admin/dashboard', follow_redirects=True)
        self.assertIn(b'Access denied', res.data)

        res = self.client.get('/manager/dashboard', follow_redirects=True)
        self.assertIn(b'Access denied', res.data)

    def test_goal_progress_update(self):
        # Login as Employee
        self.client.post('/login', data={'username': 'emp.john', 'password': 'employee123'})
        res = self.client.post('/goals/update-progress/1', data={
            'status': 'Completed',
            'completion_percentage': '100'
        }, follow_redirects=True)
        self.assertEqual(res.status_code, 200)

    def test_custom_404_page(self):
        res = self.client.get('/nonexistent-page-url')
        self.assertEqual(res.status_code, 404)
        self.assertIn(b'Page Not Found', res.data)
        self.assertIn(b'404', res.data)

if __name__ == '__main__':
    unittest.main()
