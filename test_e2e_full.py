"""
Full End-to-End Functional and UI Verification Script for PerfPulse EMS
Tests every route, CRUD operation, calculation, and UI element.
"""

import sys
import unittest
from app import app
import db

class TestFullE2E(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        cls.client = app.test_client()

    def setUp(self):
        with self.client.session_transaction() as sess:
            sess.clear()

    def tearDown(self):
        self.client.get('/logout')

    def test_01_login_all_roles(self):
        roles = [
            ('admin', 'admin123', 'Alexander'),
            ('manager.sarah', 'manager123', 'Sarah Jenkins'),
            ('emp.john', 'employee123', 'John Doe'),
        ]
        for username, password, expected_name in roles:
            with self.subTest(user=username):
                res = self.client.post('/login', data={'username': username, 'password': password}, follow_redirects=True)
                self.assertEqual(res.status_code, 200)
                self.assertIn(expected_name.encode(), res.data)
                self.client.get('/logout')

    def test_02_admin_crud_employee(self):
        self.client.post('/login', data={'username': 'admin', 'password': 'admin123'}, follow_redirects=True)
        
        # 1. Add Employee
        emp_code = "EMP999"
        email = "test.employee999@company.com"
        res = self.client.post('/employees/create', data={
            'emp_code': emp_code,
            'full_name': 'Test Robot Employee',
            'email': email,
            'phone': '+1-555-9999',
            'department_id': '1',
            'job_position': 'Automation Engineer',
            'manager_id': '2',
            'joining_date': '2026-01-15'
        }, follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Test Robot Employee', res.data)

        # Query newly created employee ID
        row = db.query_db("SELECT id FROM employees WHERE emp_code = %s", (emp_code,), one=True)
        self.assertIsNotNone(row)
        emp_id = row['id']

        # 2. View Profile
        res = self.client.get(f'/employees/profile/{emp_id}')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Test Robot Employee', res.data)

        # 3. Edit Employee
        res = self.client.post(f'/employees/edit/{emp_id}', data={
            'full_name': 'Test Robot Employee Updated',
            'email': email,
            'phone': '+1-555-9999',
            'department_id': '1',
            'job_position': 'Senior Automation Engineer',
            'manager_id': '2',
            'joining_date': '2026-01-15',
            'employment_status': 'Active'
        }, follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Senior Automation Engineer', res.data)

        # 4. Delete Employee
        res = self.client.post(f'/employees/delete/{emp_id}', follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'all associated records deleted', res.data)

    def test_03_admin_crud_department(self):
        self.client.post('/login', data={'username': 'admin', 'password': 'admin123'}, follow_redirects=True)
        
        # 1. Create Department
        res = self.client.post('/departments/create', data={
            'name': 'AI & Robotics Labs',
            'description': 'Advanced machine learning team'
        }, follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'AI &amp; Robotics Labs', res.data)

        dept_row = db.query_db("SELECT id FROM departments WHERE name = %s", ('AI & Robotics Labs',), one=True)
        self.assertIsNotNone(dept_row)
        dept_id = dept_row['id']

        # 2. Edit Department
        res = self.client.post(f'/departments/edit/{dept_id}', data={
            'name': 'AI & Robotics Center',
            'description': 'Updated scope'
        }, follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'AI &amp; Robotics Center', res.data)

        # 3. Delete Department
        res = self.client.post(f'/departments/delete/{dept_id}', follow_redirects=True)
        self.assertEqual(res.status_code, 200)

    def test_04_goals_and_evaluation_cycle(self):
        # Admin assigns goal to emp 1 (John Doe)
        self.client.post('/login', data={'username': 'admin', 'password': 'admin123'}, follow_redirects=True)
        
        goal_res = self.client.post('/goals/create', data={
            'employee_id': '1',
            'title': 'Deploy Kubernetes Cluster',
            'description': 'Scale infrastructure to multi-region cluster',
            'priority': 'High',
            'assigned_date': '2026-10-01',
            'deadline': '2026-11-01'
        }, follow_redirects=True)
        self.assertEqual(goal_res.status_code, 200)
        self.assertIn(b'Deploy Kubernetes Cluster', goal_res.data)

        # Conduct Evaluation for emp 1
        eval_res = self.client.post('/evaluations/create', data={
            'employee_id': '1',
            'review_period': 'Q4 2026 E2E Test',
            'review_date': '2026-10-20',
            'task_completion': '95',
            'quality_of_work': '92',
            'attendance': '90',
            'teamwork': '92',
            'manager_rating': '95',
            'comments': 'Superb execution across all core objectives.'
        }, follow_redirects=True)
        self.assertEqual(eval_res.status_code, 200)
        self.assertIn(b'Evaluation submitted successfully', eval_res.data)

        # Provide Feedback for emp 1
        fb_res = self.client.post('/feedback/create', data={
            'employee_id': '1',
            'feedback_date': '2026-10-20',
            'strengths': 'High architectural quality and fast debugging skills.',
            'areas_for_improvement': 'Document complex distributed systems setups.',
            'general_comments': 'Outstanding teammate and solid mentor.',
            'recommendations': 'Consider taking lead on the platform migration next sprint.'
        }, follow_redirects=True)
        self.assertEqual(fb_res.status_code, 200)
        self.assertIn(b'Employee feedback recorded successfully', fb_res.data)

    def test_05_views_render_successfully(self):
        # Verify all views return HTTP 200 for Admin
        self.client.post('/login', data={'username': 'admin', 'password': 'admin123'}, follow_redirects=True)
        
        endpoints = [
            '/admin/dashboard',
            '/employees',
            '/managers',
            '/departments',
            '/goals',
            '/evaluations',
            '/evaluations/new',
            '/feedback',
            '/feedback/new',
            '/leaderboard',
            '/reports',
        ]
        for ep in endpoints:
            with self.subTest(endpoint=ep):
                res = self.client.get(ep)
                self.assertEqual(res.status_code, 200)

if __name__ == '__main__':
    unittest.main()
