-- =======================================================
-- Employee Performance Management System
-- Database Schema and Sample Data for MySQL
-- Database: employee_performance_db
-- =======================================================

CREATE DATABASE IF NOT EXISTS `employee_performance_db` 
  DEFAULT CHARACTER SET utf8mb4 
  COLLATE utf8mb4_unicode_ci;

USE `employee_performance_db`;

-- -------------------------------------------------------
-- Table: departments
-- -------------------------------------------------------
DROP TABLE IF EXISTS `feedback`;
DROP TABLE IF EXISTS `performance_reviews`;
DROP TABLE IF EXISTS `goals`;
DROP TABLE IF EXISTS `employees`;
DROP TABLE IF EXISTS `users`;
DROP TABLE IF EXISTS `departments`;

CREATE TABLE `departments` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `name` VARCHAR(100) NOT NULL UNIQUE,
  `description` TEXT,
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- -------------------------------------------------------
-- Table: users
-- Roles: 'Admin', 'Manager', 'Employee'
-- -------------------------------------------------------
CREATE TABLE `users` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `username` VARCHAR(80) NOT NULL UNIQUE,
  `email` VARCHAR(120) NOT NULL UNIQUE,
  `password_hash` VARCHAR(255) NOT NULL,
  `role` ENUM('Admin', 'Manager', 'Employee') NOT NULL DEFAULT 'Employee',
  `full_name` VARCHAR(120) NOT NULL,
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- -------------------------------------------------------
-- Table: employees
-- -------------------------------------------------------
CREATE TABLE `employees` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `user_id` INT NULL UNIQUE,
  `emp_code` VARCHAR(30) NOT NULL UNIQUE,
  `full_name` VARCHAR(120) NOT NULL,
  `email` VARCHAR(120) NOT NULL UNIQUE,
  `phone` VARCHAR(30),
  `department_id` INT NULL,
  `job_position` VARCHAR(100) NOT NULL,
  `joining_date` DATE NOT NULL,
  `manager_id` INT NULL,
  `employment_status` ENUM('Active', 'On Leave', 'Terminated') DEFAULT 'Active',
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT `fk_emp_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE SET NULL,
  CONSTRAINT `fk_emp_department` FOREIGN KEY (`department_id`) REFERENCES `departments` (`id`) ON DELETE SET NULL,
  CONSTRAINT `fk_emp_manager` FOREIGN KEY (`manager_id`) REFERENCES `employees` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- -------------------------------------------------------
-- Table: goals
-- -------------------------------------------------------
CREATE TABLE `goals` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `employee_id` INT NOT NULL,
  `assigned_by` INT NOT NULL,
  `title` VARCHAR(200) NOT NULL,
  `description` TEXT,
  `assigned_date` DATE NOT NULL,
  `deadline` DATE NOT NULL,
  `priority` ENUM('Low', 'Medium', 'High') DEFAULT 'Medium',
  `status` ENUM('Not Started', 'In Progress', 'Completed') DEFAULT 'Not Started',
  `completion_percentage` INT DEFAULT 0,
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  CONSTRAINT `fk_goal_employee` FOREIGN KEY (`employee_id`) REFERENCES `employees` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_goal_assigner` FOREIGN KEY (`assigned_by`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- -------------------------------------------------------
-- Table: performance_reviews
-- -------------------------------------------------------
CREATE TABLE `performance_reviews` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `employee_id` INT NOT NULL,
  `reviewer_id` INT NOT NULL,
  `review_date` DATE NOT NULL,
  `review_period` VARCHAR(50) NOT NULL,
  `task_completion` DECIMAL(5,2) NOT NULL DEFAULT 0.00,
  `quality_of_work` DECIMAL(5,2) NOT NULL DEFAULT 0.00,
  `attendance` DECIMAL(5,2) NOT NULL DEFAULT 0.00,
  `teamwork` DECIMAL(5,2) NOT NULL DEFAULT 0.00,
  `manager_rating` DECIMAL(5,2) NOT NULL DEFAULT 0.00,
  `total_score` DECIMAL(5,2) NOT NULL DEFAULT 0.00,
  `rating_category` VARCHAR(50) NOT NULL,
  `comments` TEXT,
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT `fk_rev_employee` FOREIGN KEY (`employee_id`) REFERENCES `employees` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_rev_reviewer` FOREIGN KEY (`reviewer_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- -------------------------------------------------------
-- Table: feedback
-- -------------------------------------------------------
CREATE TABLE `feedback` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `employee_id` INT NOT NULL,
  `manager_id` INT NOT NULL,
  `feedback_date` DATE NOT NULL,
  `strengths` TEXT NOT NULL,
  `areas_for_improvement` TEXT NOT NULL,
  `general_comments` TEXT,
  `recommendations` TEXT,
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT `fk_fb_employee` FOREIGN KEY (`employee_id`) REFERENCES `employees` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_fb_manager` FOREIGN KEY (`manager_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =======================================================
-- INSERT SAMPLE DATA
-- Passwords:
--   Admin:    admin123    (hash: pbkdf2:sha256:1000000$KZTHlZglXxVjhC2e$54642ee73ab66ede613fca3aa3ee3b251e4dca282a6a88b047c1f7d36f862e5c)
--   Managers: manager123  (hash: pbkdf2:sha256:1000000$ABfM7xdmwrkeStuE$df5e685fcfe6328f16b76604562e49ca9d2a8ba7723aa0a14db358d4bb7bb9ea)
--   Employees: employee123 (hash: pbkdf2:sha256:1000000$xr1lxtG8ELqy3wE8$28e15ccc3af4bda44680b64d98adafc62668991a2dcca0edec9d15afff407681)
-- =======================================================

-- 1. Departments
INSERT INTO `departments` (`id`, `name`, `description`) VALUES
(1, 'Engineering & Technology', 'Software engineering, cloud infrastructure, QA, and IT operations.'),
(2, 'Marketing & Growth', 'Brand marketing, digital advertising, content creation, and SEO.'),
(3, 'Finance & Accounting', 'Financial planning, accounting, auditing, and payroll management.'),
(4, 'Human Resources', 'Talent acquisition, employee engagement, compliance, and training.');

-- 2. Users (Admin, 2 Managers, 10 Employees)
INSERT INTO `users` (`id`, `username`, `email`, `password_hash`, `role`, `full_name`) VALUES
-- Admin
(1, 'admin', 'admin@company.com', 'pbkdf2:sha256:1000000$KZTHlZglXxVjhC2e$54642ee73ab66ede613fca3aa3ee3b251e4dca282a6a88b047c1f7d36f862e5c', 'Admin', 'Alexander Pierce'),

-- Managers
(2, 'manager.sarah', 'sarah.jenkins@company.com', 'pbkdf2:sha256:1000000$ABfM7xdmwrkeStuE$df5e685fcfe6328f16b76604562e49ca9d2a8ba7723aa0a14db358d4bb7bb9ea', 'Manager', 'Sarah Jenkins'),
(3, 'manager.david', 'david.chen@company.com', 'pbkdf2:sha256:1000000$ABfM7xdmwrkeStuE$df5e685fcfe6328f16b76604562e49ca9d2a8ba7723aa0a14db358d4bb7bb9ea', 'Manager', 'David Chen'),

-- Employees
(4, 'emp.john', 'john.doe@company.com', 'pbkdf2:sha256:1000000$xr1lxtG8ELqy3wE8$28e15ccc3af4bda44680b64d98adafc62668991a2dcca0edec9d15afff407681', 'Employee', 'John Doe'),
(5, 'emp.emily', 'emily.watson@company.com', 'pbkdf2:sha256:1000000$xr1lxtG8ELqy3wE8$28e15ccc3af4bda44680b64d98adafc62668991a2dcca0edec9d15afff407681', 'Employee', 'Emily Watson'),
(6, 'emp.michael', 'michael.brown@company.com', 'pbkdf2:sha256:1000000$xr1lxtG8ELqy3wE8$28e15ccc3af4bda44680b64d98adafc62668991a2dcca0edec9d15afff407681', 'Employee', 'Michael Brown'),
(7, 'emp.lisa', 'lisa.garcia@company.com', 'pbkdf2:sha256:1000000$xr1lxtG8ELqy3wE8$28e15ccc3af4bda44680b64d98adafc62668991a2dcca0edec9d15afff407681', 'Employee', 'Lisa Garcia'),
(8, 'emp.alex', 'alex.taylor@company.com', 'pbkdf2:sha256:1000000$xr1lxtG8ELqy3wE8$28e15ccc3af4bda44680b64d98adafc62668991a2dcca0edec9d15afff407681', 'Employee', 'Alex Taylor'),
(9, 'emp.robert', 'robert.martinez@company.com', 'pbkdf2:sha256:1000000$xr1lxtG8ELqy3wE8$28e15ccc3af4bda44680b64d98adafc62668991a2dcca0edec9d15afff407681', 'Employee', 'Robert Martinez'),
(10, 'emp.jessica', 'jessica.miller@company.com', 'pbkdf2:sha256:1000000$xr1lxtG8ELqy3wE8$28e15ccc3af4bda44680b64d98adafc62668991a2dcca0edec9d15afff407681', 'Employee', 'Jessica Miller'),
(11, 'emp.james', 'james.wilson@company.com', 'pbkdf2:sha256:1000000$xr1lxtG8ELqy3wE8$28e15ccc3af4bda44680b64d98adafc62668991a2dcca0edec9d15afff407681', 'Employee', 'James Wilson'),
(12, 'emp.amanda', 'amanda.thomas@company.com', 'pbkdf2:sha256:1000000$xr1lxtG8ELqy3wE8$28e15ccc3af4bda44680b64d98adafc62668991a2dcca0edec9d15afff407681', 'Employee', 'Amanda Thomas'),
(13, 'emp.daniel', 'daniel.jackson@company.com', 'pbkdf2:sha256:1000000$xr1lxtG8ELqy3wE8$28e15ccc3af4bda44680b64d98adafc62668991a2dcca0edec9d15afff407681', 'Employee', 'Daniel Jackson');

-- 3. Employees (Managers also have employee records, plus 10 staff employees)
INSERT INTO `employees` (`id`, `user_id`, `emp_code`, `full_name`, `email`, `phone`, `department_id`, `job_position`, `joining_date`, `manager_id`, `employment_status`) VALUES
-- Manager 1 (Sarah Jenkins)
(1, 2, 'MGR001', 'Sarah Jenkins', 'sarah.jenkins@company.com', '+1-555-0101', 1, 'Engineering Director', '2022-01-15', NULL, 'Active'),
-- Manager 2 (David Chen)
(2, 3, 'MGR002', 'David Chen', 'david.chen@company.com', '+1-555-0102', 2, 'Marketing & Operations Lead', '2022-03-01', NULL, 'Active'),

-- Engineering Team (Managed by Sarah Jenkins - employee id 1)
(3, 4, 'EMP001', 'John Doe', 'john.doe@company.com', '+1-555-0111', 1, 'Senior Backend Engineer', '2023-02-10', 1, 'Active'),
(4, 5, 'EMP002', 'Emily Watson', 'emily.watson@company.com', '+1-555-0112', 1, 'Lead Frontend Developer', '2023-04-18', 1, 'Active'),
(5, 6, 'EMP003', 'Michael Brown', 'michael.brown@company.com', '+1-555-0113', 1, 'DevOps & Cloud Engineer', '2023-06-01', 1, 'Active'),
(6, 7, 'EMP004', 'Lisa Garcia', 'lisa.garcia@company.com', '+1-555-0114', 1, 'UI/UX Product Designer', '2023-09-12', 1, 'Active'),
(7, 8, 'EMP005', 'Alex Taylor', 'alex.taylor@company.com', '+1-555-0115', 1, 'QA Automation Engineer', '2024-01-10', 1, 'Active'),

-- Marketing & Finance Team (Managed by David Chen - employee id 2)
(8, 9, 'EMP006', 'Robert Martinez', 'robert.martinez@company.com', '+1-555-0116', 2, 'Senior Content Strategist', '2023-03-15', 2, 'Active'),
(9, 10, 'EMP007', 'Jessica Miller', 'jessica.miller@company.com', '+1-555-0117', 2, 'Growth Marketing Lead', '2023-05-20', 2, 'Active'),
(10, 11, 'EMP008', 'James Wilson', 'james.wilson@company.com', '+1-555-0118', 2, 'SEO & Analytics Specialist', '2023-08-05', 2, 'Active'),
(11, 12, 'EMP009', 'Amanda Thomas', 'amanda.thomas@company.com', '+1-555-0119', 3, 'Senior Financial Analyst', '2023-02-01', 2, 'Active'),
(12, 13, 'EMP010', 'Daniel Jackson', 'daniel.jackson@company.com', '+1-555-0120', 3, 'Staff Accountant', '2023-07-15', 2, 'Active');

-- 4. Goals
INSERT INTO `goals` (`id`, `employee_id`, `assigned_by`, `title`, `description`, `assigned_date`, `deadline`, `priority`, `status`, `completion_percentage`) VALUES
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
(12, 12, 3, 'Automate Payroll Reconciliation', 'Eliminate manual ledger reconciliations by building automated scripts with audit trail.', '2026-02-01', '2026-05-30', 'Medium', 'In Progress', 70);

-- 5. Performance Reviews
-- Formula: (Task*0.30) + (Quality*0.25) + (Attendance*0.15) + (Teamwork*0.15) + (Manager*0.15)
INSERT INTO `performance_reviews` (`id`, `employee_id`, `reviewer_id`, `review_date`, `review_period`, `task_completion`, `quality_of_work`, `attendance`, `teamwork`, `manager_rating`, `total_score`, `rating_category`, `comments`) VALUES
-- John Doe (Outstanding: 93.35)
(1, 3, 2, '2026-03-31', 'Q1 2026', 95.00, 92.00, 95.00, 90.00, 94.00, 93.35, 'Outstanding', 'Exceptional technical execution on the microservices migration. Always ready to mentor junior engineers.'),
-- Emily Watson (Excellent: 88.85)
(2, 4, 2, '2026-03-31', 'Q1 2026', 88.00, 90.00, 90.00, 85.00, 88.00, 88.85, 'Excellent', 'Superb UI precision and attention to user experience. Strong commitment to clean, accessible frontend code.'),
-- Michael Brown (Good: 78.90)
(3, 5, 2, '2026-03-31', 'Q1 2026', 78.00, 80.00, 85.00, 80.00, 75.00, 78.90, 'Good', 'Reliable infrastructure work. Encouraged to improve documentation on Kubernetes clusters.'),
-- Lisa Garcia (Average: 66.40)
(4, 6, 2, '2026-03-31', 'Q1 2026', 68.00, 65.00, 70.00, 65.00, 65.00, 66.40, 'Average', 'Designs are creative, but some deadline slips occurred. Needs to proactively flag blockers earlier in sprints.'),
-- Alex Taylor (Needs Improvement: 55.65)
(5, 7, 2, '2026-03-31', 'Q1 2026', 55.00, 58.00, 60.00, 55.00, 50.00, 55.65, 'Needs Improvement', 'Test suite completion fell significantly behind schedule. Required multiple revisions on automation coverage.'),
-- Robert Martinez (Good: 72.85)
(6, 8, 3, '2026-03-31', 'Q1 2026', 72.00, 70.00, 80.00, 75.00, 70.00, 72.85, 'Good', 'Produced solid editorial pieces. Should focus more on aligning content with high-intent organic keywords.'),
-- Jessica Miller (Outstanding: 91.10)
(7, 9, 3, '2026-03-31', 'Q1 2026', 92.00, 88.00, 95.00, 92.00, 90.00, 91.10, 'Outstanding', 'Phenomenal growth metrics delivered. Reduced CAC by 28% and set benchmark for team execution.'),
-- James Wilson (Good: 76.85)
(8, 10, 3, '2026-03-31', 'Q1 2026', 75.00, 78.00, 80.00, 75.00, 76.00, 76.85, 'Good', 'Steady SEO improvements across product pillars. Good analytical rigor in conversion reporting.'),
-- Amanda Thomas (Excellent: 85.25)
(9, 11, 3, '2026-03-31', 'Q1 2026', 85.00, 86.00, 88.00, 82.00, 85.00, 85.25, 'Excellent', 'Thorough financial modeling and zero discrepancies found during internal audit review.'),
-- Daniel Jackson (Excellent: 83.40)
(10, 12, 3, '2026-03-31', 'Q1 2026', 82.00, 84.00, 90.00, 80.00, 82.00, 83.40, 'Excellent', 'Reliable ledger closure and automation initiative. High precision with tax compliance filings.'),

-- Historical Reviews for Trend Analysis (Q4 2025)
(11, 3, 2, '2025-12-20', 'Q4 2025', 90.00, 90.00, 92.00, 88.00, 90.00, 89.90, 'Excellent', 'Solid quarter delivering the core API foundation.'),
(12, 4, 2, '2025-12-20', 'Q4 2025', 85.00, 85.00, 88.00, 82.00, 85.00, 84.95, 'Excellent', 'Great work on responsive navigation components.'),
(13, 9, 3, '2025-12-20', 'Q4 2025', 88.00, 86.00, 90.00, 88.00, 88.00, 87.80, 'Excellent', 'Strong holiday campaign performance.'),
(14, 11, 3, '2025-12-20', 'Q4 2025', 80.00, 82.00, 85.00, 80.00, 80.00, 81.25, 'Excellent', 'Accurate year-end balance sheet preparation.');

-- 6. Feedback
INSERT INTO `feedback` (`id`, `employee_id`, `manager_id`, `feedback_date`, `strengths`, `areas_for_improvement`, `general_comments`, `recommendations`) VALUES
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
 'Take advanced SQL / PowerBI certification to expedite monthly reporting.');

-- =======================================================
-- End of database.sql
-- =======================================================
