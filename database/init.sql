-- Initial schema and seed data for AI-Powered Text-to-SQL System (Spider Dataset inspired)

-- -------------------------------------------------------------
-- DOMAIN 1: UNIVERSITY & EDUCATION
-- -------------------------------------------------------------

CREATE TABLE IF NOT EXISTS departments (
    department_id SERIAL PRIMARY KEY,
    department_name VARCHAR(100) NOT NULL UNIQUE,
    building VARCHAR(50),
    budget DECIMAL(12, 2)
);

CREATE TABLE IF NOT EXISTS instructors (
    instructor_id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE,
    department_id INT REFERENCES departments(department_id) ON DELETE SET NULL,
    salary DECIMAL(10, 2)
);

CREATE TABLE IF NOT EXISTS students (
    student_id SERIAL PRIMARY KEY,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    email VARCHAR(100) UNIQUE,
    department_id INT REFERENCES departments(department_id) ON DELETE SET NULL,
    cgpa DECIMAL(3, 2) CHECK (cgpa >= 0.0 AND cgpa <= 10.0),
    enrollment_year INT
);

CREATE TABLE IF NOT EXISTS courses (
    course_id SERIAL PRIMARY KEY,
    course_code VARCHAR(20) UNIQUE NOT NULL,
    course_title VARCHAR(150) NOT NULL,
    credits INT DEFAULT 3,
    department_id INT REFERENCES departments(department_id) ON DELETE SET NULL,
    instructor_id INT REFERENCES instructors(instructor_id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS enrollments (
    enrollment_id SERIAL PRIMARY KEY,
    student_id INT REFERENCES students(student_id) ON DELETE CASCADE,
    course_id INT REFERENCES courses(course_id) ON DELETE CASCADE,
    grade VARCHAR(5),
    grade_point DECIMAL(3, 1),
    semester VARCHAR(20)
);

-- Seed Data: University
INSERT INTO departments (department_name, building, budget) VALUES
('Computer Science', 'Turing Hall', 1200000.00),
('Data Science', 'Ada Lovelace Tower', 950000.00),
('Electrical Engineering', 'Tesla Center', 1100000.00),
('Mathematics', 'Ramanujan Block', 600000.00),
('Business & Management', 'Smith Hall', 850000.00)
ON CONFLICT DO NOTHING;

INSERT INTO instructors (name, email, department_id, salary) VALUES
('Dr. Alan Turing', 'alan.turing@univ.edu', 1, 125000.00),
('Dr. Grace Hopper', 'grace.hopper@univ.edu', 1, 130000.00),
('Dr. Andrew Ng', 'andrew.ng@univ.edu', 2, 140000.00),
('Dr. Nikola Tesla', 'nikola.tesla@univ.edu', 3, 115000.00),
('Dr. Katherine Johnson', 'katherine.j@univ.edu', 4, 110000.00)
ON CONFLICT DO NOTHING;

INSERT INTO students (first_name, last_name, email, department_id, cgpa, enrollment_year) VALUES
('Aarav', 'Sharma', 'aarav.sharma@student.edu', 1, 9.2, 2022),
('Ananya', 'Roy', 'ananya.roy@student.edu', 2, 8.8, 2022),
('Rohan', 'Verma', 'rohan.verma@student.edu', 1, 7.5, 2023),
('Priya', 'Nair', 'priya.nair@student.edu', 3, 9.5, 2021),
('Vikram', 'Singh', 'vikram.singh@student.edu', 2, 8.1, 2023),
('Sneha', 'Patel', 'sneha.patel@student.edu', 4, 9.7, 2021),
('Rahul', 'Deshmukh', 'rahul.d@student.edu', 5, 6.9, 2022),
('Kavya', 'Iyer', 'kavya.iyer@student.edu', 1, 8.9, 2023),
('Arjun', 'Mehta', 'arjun.mehta@student.edu', 3, 7.8, 2022),
('Diya', 'Gupta', 'diya.gupta@student.edu', 2, 9.4, 2021)
ON CONFLICT DO NOTHING;

INSERT INTO courses (course_code, course_title, credits, department_id, instructor_id) VALUES
('CS101', 'Database Management Systems', 4, 1, 1),
('CS102', 'Machine Learning Foundations', 4, 2, 3),
('CS201', 'Algorithms & Data Structures', 4, 1, 2),
('EE101', 'Circuit Analysis', 3, 3, 4),
('MATH101', 'Linear Algebra & Calculus', 3, 4, 5)
ON CONFLICT DO NOTHING;

INSERT INTO enrollments (student_id, course_id, grade, grade_point, semester) VALUES
(1, 1, 'A+', 10.0, 'Fall 2023'),
(1, 2, 'A', 9.0, 'Fall 2023'),
(2, 2, 'A', 9.0, 'Fall 2023'),
(3, 1, 'B', 7.0, 'Fall 2023'),
(4, 4, 'A+', 10.0, 'Fall 2023'),
(5, 2, 'B+', 8.0, 'Fall 2023'),
(6, 5, 'A+', 10.0, 'Fall 2023'),
(8, 1, 'A', 9.0, 'Fall 2023'),
(10, 2, 'A+', 10.0, 'Fall 2023')
ON CONFLICT DO NOTHING;

-- -------------------------------------------------------------
-- DOMAIN 2: E-COMMERCE & SALES
-- -------------------------------------------------------------

CREATE TABLE IF NOT EXISTS customers (
    customer_id SERIAL PRIMARY KEY,
    customer_name VARCHAR(100) NOT NULL,
    city VARCHAR(50),
    country VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS products (
    product_id SERIAL PRIMARY KEY,
    product_name VARCHAR(150) NOT NULL,
    category VARCHAR(50),
    unit_price DECIMAL(10, 2) NOT NULL,
    stock_quantity INT DEFAULT 0
);

CREATE TABLE IF NOT EXISTS orders (
    order_id SERIAL PRIMARY KEY,
    customer_id INT REFERENCES customers(customer_id) ON DELETE CASCADE,
    order_date DATE DEFAULT CURRENT_DATE,
    total_amount DECIMAL(12, 2),
    status VARCHAR(20) DEFAULT 'Completed'
);

CREATE TABLE IF NOT EXISTS order_items (
    item_id SERIAL PRIMARY KEY,
    order_id INT REFERENCES orders(order_id) ON DELETE CASCADE,
    product_id INT REFERENCES products(product_id),
    quantity INT NOT NULL,
    price_per_unit DECIMAL(10, 2) NOT NULL
);

-- Seed Data: E-Commerce
INSERT INTO customers (customer_name, city, country) VALUES
('TechCorp Inc', 'San Francisco', 'USA'),
('Global Retail', 'London', 'UK'),
('Innovate LLC', 'Berlin', 'Germany'),
('Apex Solutions', 'Tokyo', 'Japan'),
('Nexus Traders', 'Mumbai', 'India')
ON CONFLICT DO NOTHING;

INSERT INTO products (product_name, category, unit_price, stock_quantity) VALUES
('UltraBook Pro 15', 'Laptops', 1299.99, 45),
('AI Developer Workstation', 'Desktops', 2499.00, 20),
('4K Curved Monitor 32"', 'Displays', 499.50, 80),
('Ergonomic Mechanical Keyboard', 'Accessories', 129.00, 150),
('Wireless Precision Mouse', 'Accessories', 79.99, 200)
ON CONFLICT DO NOTHING;

INSERT INTO orders (customer_id, order_date, total_amount, status) VALUES
(1, '2024-01-15', 5098.98, 'Completed'),
(2, '2024-01-18', 1299.99, 'Completed'),
(3, '2024-02-01', 999.00, 'Completed'),
(4, '2024-02-10', 2499.00, 'Processing'),
(5, '2024-02-14', 387.00, 'Completed')
ON CONFLICT DO NOTHING;

INSERT INTO order_items (order_id, product_id, quantity, price_per_unit) VALUES
(1, 2, 2, 2499.00),
(1, 4, 1, 100.98),
(2, 1, 1, 1299.99),
(3, 3, 2, 499.50),
(4, 2, 1, 2499.00),
(5, 4, 3, 129.00)
ON CONFLICT DO NOTHING;

-- -------------------------------------------------------------
-- DOMAIN 3: CORPORATE & EMPLOYEES
-- -------------------------------------------------------------

CREATE TABLE IF NOT EXISTS corp_departments (
    dept_id SERIAL PRIMARY KEY,
    dept_name VARCHAR(100) NOT NULL,
    location VARCHAR(100)
);

CREATE TABLE IF NOT EXISTS employees (
    emp_id SERIAL PRIMARY KEY,
    emp_name VARCHAR(100) NOT NULL,
    job_title VARCHAR(100),
    dept_id INT REFERENCES corp_departments(dept_id),
    hire_date DATE,
    salary DECIMAL(12, 2)
);

INSERT INTO corp_departments (dept_name, location) VALUES
('Engineering', 'Building A - Floor 4'),
('Product Management', 'Building A - Floor 3'),
('Sales & Marketing', 'Building B - Floor 2'),
('Human Resources', 'Building B - Floor 1')
ON CONFLICT DO NOTHING;

INSERT INTO employees (emp_name, job_title, dept_id, hire_date, salary) VALUES
('Siddharth Rao', 'Senior AI Engineer', 1, '2021-03-15', 145000.00),
('Neha Sharma', 'Lead Data Scientist', 1, '2020-07-01', 155000.00),
('Michael Scott', 'Regional Director', 3, '2018-05-20', 120000.00),
('Pam Beesly', 'Office Administrator', 4, '2019-11-10', 65000.00),
('Jim Halpert', 'Sales Account Manager', 3, '2020-01-15', 95000.00),
('Dwight Schrute', 'Assistant to Regional Director', 3, '2019-04-01', 98000.00)
ON CONFLICT DO NOTHING;
