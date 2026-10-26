-- Initial schema and seed data for AI-Powered Text-to-SQL System (Spider Dataset inspired)

-- -------------------------------------------------------------
-- PERSISTENT QUERY HISTORY LOG
-- -------------------------------------------------------------

CREATE TABLE IF NOT EXISTS query_history (
    id SERIAL PRIMARY KEY,
    prompt TEXT NOT NULL,
    sql_query TEXT NOT NULL,
    row_count INT DEFAULT 0,
    execution_time_ms REAL DEFAULT 0,
    status VARCHAR(20) DEFAULT 'success',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

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

-- -------------------------------------------------------------
-- EXPANDED SPIDER BENCHMARK DATASET (100 Students & Extended Entities)
-- -------------------------------------------------------------

INSERT INTO instructors (instructor_id, name, email, department_id, salary) VALUES
(6, 'Dr. Claude Shannon', 'claude.shannon@univ.edu', 3, 135000.00),
(7, 'Dr. Geoffrey Hinton', 'geoff.hinton@univ.edu', 2, 160000.00),
(8, 'Dr. Donald Knuth', 'donald.knuth@univ.edu', 1, 145000.00),
(9, 'Dr. John von Neumann', 'von.neumann@univ.edu', 4, 150000.00),
(10, 'Dr. Peter Drucker', 'peter.drucker@univ.edu', 5, 120000.00)
ON CONFLICT DO NOTHING;

INSERT INTO courses (course_id, course_code, course_title, credits, department_id, instructor_id) VALUES
(6, 'CS301', 'Operating Systems & Concurrency', 4, 1, 1),
(7, 'CS302', 'Distributed Cloud Architecture', 4, 1, 2),
(8, 'DS201', 'Applied Natural Language Processing', 4, 2, 3),
(9, 'DS202', 'Big Data Analytics & Spark', 4, 2, 3),
(10, 'EE201', 'Digital Signal Processing', 3, 3, 4),
(11, 'EE202', 'Embedded IoT Systems', 3, 3, 4),
(12, 'MATH201', 'Probability & Applied Statistics', 4, 4, 5),
(13, 'MATH202', 'Discrete Optimization & Graphs', 3, 4, 5),
(14, 'MGMT101', 'Principles of Modern Management', 3, 5, 2),
(15, 'MGMT201', 'Financial Econometrics', 3, 5, 5)
ON CONFLICT DO NOTHING;

INSERT INTO students (student_id, first_name, last_name, email, department_id, cgpa, enrollment_year) VALUES
(11, 'Timmothy', 'Ward', 'timmothy.ward11@student.edu', 1, 7.09, 2020),
(12, 'Hobart', 'Balistreri', 'hobart.balistreri12@student.edu', 2, 8.84, 2021),
(13, 'Warren', 'Gleichner', 'warren.gleichner13@student.edu', 3, 7.41, 2020),
(14, 'Jarvis', 'Carroll', 'jarvis.carroll14@student.edu', 4, 8.33, 2021),
(15, 'Milton', 'Christiansen', 'milton.christiansen15@student.edu', 5, 8.6, 2023),
(16, 'Stanford', 'Rogahn', 'stanford.rogahn16@student.edu', 1, 6.84, 2020),
(17, 'Frida', 'Huel', 'frida.huel17@student.edu', 2, 8.39, 2023),
(18, 'Delaney', 'Ankunding', 'delaney.ankunding18@student.edu', 3, 8.08, 2022),
(19, 'Reva', 'Osinski', 'reva.osinski19@student.edu', 4, 7.11, 2020),
(20, 'Helga', 'Mohr', 'helga.mohr20@student.edu', 5, 7.33, 2023),
(21, 'Gregg', 'Schuppe', 'gregg.schuppe21@student.edu', 1, 6.88, 2020),
(22, 'Orrin', 'Kemmer', 'orrin.kemmer22@student.edu', 2, 7.82, 2020),
(23, 'Deon', 'Weimann', 'deon.weimann23@student.edu', 3, 8.4, 2020),
(24, 'Jordy', 'Rempel', 'jordy.rempel24@student.edu', 4, 7.0, 2024),
(25, 'Jett', 'Jaskolski', 'jett.jaskolski25@student.edu', 5, 9.63, 2020),
(26, 'Emma', 'Rohan', 'emma.rohan26@student.edu', 1, 9.78, 2020),
(27, 'Louvenia', 'Hansen', 'louvenia.hansen27@student.edu', 2, 8.34, 2023),
(28, 'Rhea', 'Bergnaum', 'rhea.bergnaum28@student.edu', 3, 8.5, 2024),
(29, 'David', 'Gorczany', 'david.gorczany29@student.edu', 4, 7.24, 2024),
(30, 'Lucile', 'Gottlieb', 'lucile.gottlieb30@student.edu', 5, 7.76, 2023),
(31, 'Antonietta', 'Fahey', 'antonietta.fahey31@student.edu', 1, 7.48, 2024),
(32, 'Rupert', 'Marks', 'rupert.marks32@student.edu', 2, 9.77, 2022),
(33, 'Julia', 'Balistreri', 'julia.balistreri33@student.edu', 3, 8.38, 2020),
(34, 'Christy', 'Huels', 'christy.huels34@student.edu', 4, 8.51, 2020),
(35, 'Adella', 'Krajcik', 'adella.krajcik35@student.edu', 5, 9.63, 2021),
(36, 'Isac', 'Fadel', 'isac.fadel36@student.edu', 1, 8.56, 2022),
(37, 'Ferne', 'Weimann', 'ferne.weimann37@student.edu', 2, 8.68, 2021),
(38, 'Misael', 'Will', 'misael.will38@student.edu', 3, 7.29, 2024),
(39, 'Fanny', 'Haley', 'fanny.haley39@student.edu', 4, 6.75, 2020),
(40, 'Eugene', 'Tremblay', 'eugene.tremblay40@student.edu', 5, 7.85, 2024),
(41, 'Linda', 'Smith', 'linda.smith41@student.edu', 1, 8.05, 2020),
(42, 'Tracy', 'Kim', 'tracy.kim42@student.edu', 2, 7.26, 2022),
(43, 'Shiela', 'Jones', 'shiela.jones43@student.edu', 3, 8.82, 2023),
(44, 'Dinesh', 'Kumar', 'dinesh.kumar44@student.edu', 4, 6.73, 2021),
(45, 'Paul', 'Gompers', 'paul.gompers45@student.edu', 5, 9.55, 2024),
(46, 'Andy', 'Schultz', 'andy.schultz46@student.edu', 1, 8.68, 2021),
(47, 'Lisa', 'Apap', 'lisa.apap47@student.edu', 2, 7.9, 2024),
(48, 'Jandy', 'Nelson', 'jandy.nelson48@student.edu', 3, 7.24, 2021),
(49, 'Eric', 'Tai', 'eric.tai49@student.edu', 4, 9.5, 2021),
(50, 'Derek', 'Lee', 'derek.lee50@student.edu', 5, 6.74, 2021),
(51, 'David', 'Adams', 'david.adams51@student.edu', 1, 9.12, 2024),
(52, 'Steven', 'Davis', 'steven.davis52@student.edu', 2, 8.97, 2024),
(53, 'Charles', 'Norris', 'charles.norris53@student.edu', 3, 9.54, 2023),
(54, 'Susan', 'Lee', 'susan.lee54@student.edu', 4, 6.91, 2022),
(55, 'Mark', 'Schwartz', 'mark.schwartz55@student.edu', 5, 8.81, 2022),
(56, 'Bruce', 'Wilson', 'bruce.wilson56@student.edu', 1, 8.15, 2023),
(57, 'Michael', 'Leighton', 'michael.leighton57@student.edu', 2, 7.94, 2024),
(58, 'Arthur', 'Pang', 'arthur.pang58@student.edu', 3, 6.63, 2023),
(59, 'Ian', 'Thornton', 'ian.thornton59@student.edu', 4, 8.92, 2024),
(60, 'George', 'Andreou', 'george.andreou60@student.edu', 5, 7.33, 2020),
(61, 'Michael', 'Woods', 'michael.woods61@student.edu', 1, 7.26, 2024),
(62, 'David', 'Shieber', 'david.shieber62@student.edu', 2, 8.44, 2020),
(63, 'Stacy', 'Prater', 'stacy.prater63@student.edu', 3, 9.8, 2022),
(64, 'Mark', 'Goldman', 'mark.goldman64@student.edu', 4, 8.4, 2021),
(65, 'Eric', 'Pang', 'eric.pang65@student.edu', 5, 8.05, 2023),
(66, 'Paul', 'Brody', 'paul.brody66@student.edu', 1, 9.52, 2021),
(67, 'Eric', 'Rugh', 'eric.rugh67@student.edu', 2, 9.79, 2023),
(68, 'Jun', 'Han', 'jun.han68@student.edu', 3, 8.59, 2023),
(69, 'Lisa', 'Cheng', 'lisa.cheng69@student.edu', 4, 9.7, 2023),
(70, 'Sarah', 'Smith', 'sarah.smith70@student.edu', 5, 7.65, 2022),
(71, 'Eric', 'Brown', 'eric.brown71@student.edu', 1, 7.56, 2020),
(72, 'William', 'Simms', 'william.simms72@student.edu', 2, 9.33, 2022),
(73, 'Eric', 'Epp', 'eric.epp73@student.edu', 3, 7.86, 2023),
(74, 'Sarah', 'Schmidt', 'sarah.schmidt74@student.edu', 4, 7.45, 2023),
(75, 'Schrefl', 'Student', 'schrefl.student75@student.edu', 5, 9.18, 2024),
(76, 'Rumat', 'Student', 'rumat.student76@student.edu', 1, 6.62, 2020),
(77, 'Miliko', 'Student', 'miliko.student77@student.edu', 2, 7.54, 2022),
(78, 'Moszkowski', 'Student', 'moszkowski.student78@student.edu', 3, 6.88, 2023),
(79, 'Prieto', 'Student', 'prieto.student79@student.edu', 4, 9.35, 2020),
(80, 'Marcol', 'Student', 'marcol.student80@student.edu', 5, 8.67, 2024),
(81, 'Quimby', 'Student', 'quimby.student81@student.edu', 1, 8.02, 2020),
(82, 'Sowerby', 'Student', 'sowerby.student82@student.edu', 2, 7.12, 2022),
(83, 'Coppens', 'Student', 'coppens.student83@student.edu', 3, 8.55, 2023),
(84, 'Cirsto', 'Student', 'cirsto.student84@student.edu', 4, 8.56, 2020),
(85, 'Velikovs', 'Student', 'velikovs.student85@student.edu', 5, 7.17, 2024),
(86, 'Marek', 'Student', 'marek.student86@student.edu', 1, 6.93, 2022),
(87, 'Guerra', 'Student', 'guerra.student87@student.edu', 2, 7.95, 2023),
(88, 'Hawthorne', 'Student', 'hawthorne.student88@student.edu', 3, 6.9, 2024),
(89, 'Leuen', 'Student', 'leuen.student89@student.edu', 4, 9.14, 2021),
(90, 'Eguchi', 'Student', 'eguchi.student90@student.edu', 5, 7.53, 2020),
(91, 'Moei', 'Student', 'moei.student91@student.edu', 1, 8.32, 2020),
(92, 'Alfaro', 'Student', 'alfaro.student92@student.edu', 2, 7.24, 2020),
(93, 'Krishnakumar', 'Student', 'krishnakumar.student93@student.edu', 3, 8.02, 2020),
(94, 'Inoue', 'Student', 'inoue.student94@student.edu', 4, 8.64, 2021),
(95, 'Sahm', 'Student', 'sahm.student95@student.edu', 5, 8.14, 2022),
(96, 'Tomason', 'Student', 'tomason.student96@student.edu', 1, 8.18, 2022),
(97, 'Karande', 'Student', 'karande.student97@student.edu', 2, 7.87, 2023),
(98, 'Wunderli', 'Student', 'wunderli.student98@student.edu', 3, 9.73, 2021),
(99, 'Greve', 'Student', 'greve.student99@student.edu', 4, 8.01, 2021),
(100, 'Cerime', 'Student', 'cerime.student100@student.edu', 5, 7.77, 2024)
ON CONFLICT DO NOTHING;

INSERT INTO enrollments (enrollment_id, student_id, course_id, grade, grade_point, semester) VALUES
(10, 11, 12, 'B', 7.5, 'Spring 2024'),
(11, 11, 3, 'B-', 7.0, 'Fall 2023'),
(12, 11, 2, 'A+', 10.0, 'Fall 2023'),
(13, 12, 5, 'A', 9.0, 'Spring 2023'),
(14, 12, 14, 'A', 9.0, 'Spring 2024'),
(15, 12, 10, 'B-', 7.0, 'Fall 2023'),
(16, 13, 13, 'A', 9.0, 'Fall 2023'),
(17, 13, 9, 'B+', 8.0, 'Spring 2023'),
(18, 13, 7, 'O', 10.0, 'Spring 2023'),
(19, 14, 1, 'A', 9.0, 'Spring 2024'),
(20, 14, 6, 'O', 10.0, 'Spring 2023'),
(21, 15, 1, 'B+', 8.0, 'Fall 2023'),
(22, 15, 3, 'A', 9.0, 'Spring 2024'),
(23, 16, 9, 'A', 9.0, 'Fall 2022'),
(24, 17, 3, 'A-', 8.5, 'Fall 2022'),
(25, 17, 7, 'A', 9.0, 'Fall 2023'),
(26, 17, 11, 'B-', 7.0, 'Spring 2024'),
(27, 18, 2, 'B+', 8.0, 'Spring 2024'),
(28, 18, 14, 'B-', 7.0, 'Spring 2024'),
(29, 18, 6, 'B+', 8.0, 'Fall 2022'),
(30, 19, 2, 'B', 7.5, 'Spring 2023'),
(31, 19, 4, 'A', 9.0, 'Spring 2024'),
(32, 19, 11, 'A', 9.0, 'Fall 2022'),
(33, 20, 3, 'B', 7.5, 'Fall 2022'),
(34, 20, 12, 'A+', 10.0, 'Fall 2023'),
(35, 21, 5, 'B-', 7.0, 'Fall 2023'),
(36, 22, 3, 'B+', 8.0, 'Spring 2024'),
(37, 22, 4, 'A-', 8.5, 'Spring 2023'),
(38, 23, 2, 'O', 10.0, 'Spring 2023'),
(39, 24, 15, 'A-', 8.5, 'Spring 2023'),
(40, 24, 10, 'A', 9.0, 'Fall 2023'),
(41, 25, 5, 'A+', 10.0, 'Spring 2024'),
(42, 25, 11, 'B', 7.5, 'Spring 2023'),
(43, 26, 8, 'B-', 7.0, 'Fall 2023'),
(44, 27, 7, 'A', 9.0, 'Fall 2023'),
(45, 27, 12, 'B+', 8.0, 'Spring 2024'),
(46, 27, 5, 'A', 9.0, 'Fall 2022'),
(47, 28, 7, 'B-', 7.0, 'Fall 2023'),
(48, 29, 5, 'O', 10.0, 'Fall 2023'),
(49, 29, 1, 'A+', 10.0, 'Fall 2022'),
(50, 29, 11, 'A', 9.0, 'Fall 2023'),
(51, 30, 10, 'B-', 7.0, 'Spring 2023'),
(52, 31, 4, 'A-', 8.5, 'Fall 2022'),
(53, 31, 10, 'A+', 10.0, 'Fall 2023'),
(54, 31, 5, 'A', 9.0, 'Fall 2022'),
(55, 32, 6, 'A', 9.0, 'Fall 2023'),
(56, 32, 12, 'B-', 7.0, 'Spring 2024'),
(57, 32, 3, 'A-', 8.5, 'Spring 2023'),
(58, 33, 13, 'B+', 8.0, 'Fall 2023'),
(59, 34, 9, 'B', 7.5, 'Spring 2024'),
(60, 34, 5, 'B', 7.5, 'Fall 2023'),
(61, 34, 3, 'A', 9.0, 'Spring 2024'),
(62, 35, 3, 'B+', 8.0, 'Spring 2024'),
(63, 36, 6, 'O', 10.0, 'Fall 2022'),
(64, 36, 2, 'B', 7.5, 'Fall 2022'),
(65, 36, 13, 'A', 9.0, 'Fall 2023'),
(66, 37, 12, 'O', 10.0, 'Fall 2023'),
(67, 37, 11, 'A', 9.0, 'Spring 2023'),
(68, 37, 5, 'A', 9.0, 'Fall 2022'),
(69, 38, 15, 'B+', 8.0, 'Fall 2022'),
(70, 38, 9, 'A', 9.0, 'Fall 2023'),
(71, 38, 6, 'O', 10.0, 'Fall 2022'),
(72, 39, 1, 'A+', 10.0, 'Fall 2023'),
(73, 40, 2, 'B+', 8.0, 'Spring 2023'),
(74, 40, 15, 'O', 10.0, 'Spring 2024'),
(75, 41, 11, 'B+', 8.0, 'Spring 2024'),
(76, 41, 12, 'A-', 8.5, 'Spring 2024'),
(77, 42, 2, 'O', 10.0, 'Fall 2023'),
(78, 42, 14, 'A+', 10.0, 'Fall 2023'),
(79, 42, 8, 'B+', 8.0, 'Spring 2024'),
(80, 43, 4, 'B-', 7.0, 'Fall 2022'),
(81, 43, 14, 'B-', 7.0, 'Fall 2023'),
(82, 44, 7, 'B', 7.5, 'Spring 2023'),
(83, 45, 14, 'A', 9.0, 'Fall 2022'),
(84, 46, 4, 'A+', 10.0, 'Fall 2022'),
(85, 46, 11, 'B-', 7.0, 'Spring 2023'),
(86, 46, 14, 'A-', 8.5, 'Spring 2023'),
(87, 47, 14, 'B+', 8.0, 'Spring 2023'),
(88, 48, 4, 'B-', 7.0, 'Spring 2023'),
(89, 48, 14, 'A+', 10.0, 'Fall 2023'),
(90, 48, 15, 'A-', 8.5, 'Spring 2023'),
(91, 49, 5, 'A', 9.0, 'Fall 2022'),
(92, 49, 13, 'A-', 8.5, 'Fall 2022'),
(93, 49, 3, 'B-', 7.0, 'Spring 2023'),
(94, 50, 6, 'B', 7.5, 'Fall 2022'),
(95, 50, 1, 'A-', 8.5, 'Spring 2024'),
(96, 50, 3, 'B+', 8.0, 'Fall 2022'),
(97, 51, 2, 'B-', 7.0, 'Fall 2022'),
(98, 51, 8, 'A', 9.0, 'Spring 2023'),
(99, 51, 14, 'A+', 10.0, 'Fall 2023'),
(100, 52, 11, 'A+', 10.0, 'Spring 2024'),
(101, 52, 1, 'O', 10.0, 'Spring 2024'),
(102, 53, 2, 'A', 9.0, 'Fall 2022'),
(103, 53, 8, 'A', 9.0, 'Fall 2023'),
(104, 53, 12, 'A-', 8.5, 'Fall 2022'),
(105, 54, 5, 'B+', 8.0, 'Fall 2023'),
(106, 55, 10, 'B', 7.5, 'Spring 2024'),
(107, 55, 9, 'B+', 8.0, 'Spring 2024'),
(108, 56, 13, 'A', 9.0, 'Spring 2023'),
(109, 57, 8, 'O', 10.0, 'Fall 2023'),
(110, 57, 4, 'A', 9.0, 'Spring 2024'),
(111, 58, 12, 'B-', 7.0, 'Spring 2024'),
(112, 58, 2, 'B-', 7.0, 'Fall 2023'),
(113, 59, 3, 'A', 9.0, 'Fall 2022'),
(114, 59, 11, 'A', 9.0, 'Fall 2022'),
(115, 60, 7, 'A', 9.0, 'Fall 2023'),
(116, 61, 9, 'A+', 10.0, 'Fall 2023'),
(117, 62, 2, 'O', 10.0, 'Fall 2022'),
(118, 62, 7, 'B', 7.5, 'Fall 2023'),
(119, 62, 6, 'B-', 7.0, 'Fall 2022'),
(120, 63, 9, 'A', 9.0, 'Spring 2023'),
(121, 63, 4, 'A', 9.0, 'Fall 2023'),
(122, 63, 3, 'B+', 8.0, 'Fall 2023'),
(123, 64, 13, 'B', 7.5, 'Spring 2023'),
(124, 65, 14, 'B+', 8.0, 'Fall 2022'),
(125, 65, 9, 'B', 7.5, 'Fall 2022'),
(126, 66, 5, 'B', 7.5, 'Fall 2023'),
(127, 67, 1, 'A-', 8.5, 'Spring 2024'),
(128, 67, 3, 'A', 9.0, 'Spring 2023'),
(129, 68, 11, 'B+', 8.0, 'Spring 2023'),
(130, 68, 1, 'O', 10.0, 'Spring 2024'),
(131, 68, 2, 'A', 9.0, 'Fall 2023'),
(132, 69, 6, 'B', 7.5, 'Fall 2023'),
(133, 70, 10, 'A-', 8.5, 'Spring 2023'),
(134, 70, 2, 'A+', 10.0, 'Fall 2022'),
(135, 70, 1, 'B', 7.5, 'Spring 2024'),
(136, 71, 7, 'A', 9.0, 'Spring 2024'),
(137, 71, 8, 'B', 7.5, 'Spring 2023'),
(138, 71, 10, 'B+', 8.0, 'Fall 2022'),
(139, 72, 7, 'B', 7.5, 'Spring 2024'),
(140, 72, 2, 'B+', 8.0, 'Fall 2023'),
(141, 73, 4, 'O', 10.0, 'Fall 2022'),
(142, 74, 4, 'B', 7.5, 'Spring 2023'),
(143, 75, 13, 'B', 7.5, 'Fall 2023'),
(144, 76, 2, 'A', 9.0, 'Spring 2024'),
(145, 76, 1, 'A-', 8.5, 'Spring 2023'),
(146, 77, 9, 'B+', 8.0, 'Fall 2023'),
(147, 77, 12, 'A', 9.0, 'Spring 2024'),
(148, 78, 1, 'A', 9.0, 'Fall 2022'),
(149, 78, 7, 'B-', 7.0, 'Spring 2024'),
(150, 78, 15, 'O', 10.0, 'Spring 2024'),
(151, 79, 2, 'A+', 10.0, 'Fall 2023'),
(152, 79, 7, 'A-', 8.5, 'Spring 2024'),
(153, 80, 15, 'O', 10.0, 'Fall 2022'),
(154, 80, 6, 'B+', 8.0, 'Spring 2024'),
(155, 80, 2, 'O', 10.0, 'Fall 2022'),
(156, 81, 14, 'B-', 7.0, 'Spring 2023'),
(157, 81, 5, 'B-', 7.0, 'Spring 2023'),
(158, 82, 9, 'A', 9.0, 'Spring 2023'),
(159, 83, 6, 'A-', 8.5, 'Spring 2023'),
(160, 83, 12, 'A', 9.0, 'Spring 2023'),
(161, 84, 4, 'A-', 8.5, 'Fall 2022'),
(162, 84, 3, 'A-', 8.5, 'Spring 2024'),
(163, 85, 13, 'A', 9.0, 'Fall 2023'),
(164, 85, 10, 'B-', 7.0, 'Spring 2023'),
(165, 86, 2, 'A', 9.0, 'Fall 2023'),
(166, 86, 8, 'B', 7.5, 'Fall 2022'),
(167, 87, 9, 'B', 7.5, 'Spring 2024'),
(168, 87, 2, 'A', 9.0, 'Fall 2022'),
(169, 88, 6, 'B', 7.5, 'Fall 2022'),
(170, 89, 14, 'B+', 8.0, 'Spring 2024'),
(171, 89, 15, 'A', 9.0, 'Fall 2022'),
(172, 89, 2, 'A', 9.0, 'Spring 2023'),
(173, 90, 10, 'B+', 8.0, 'Spring 2023'),
(174, 90, 8, 'A+', 10.0, 'Spring 2024'),
(175, 91, 13, 'B-', 7.0, 'Fall 2022'),
(176, 92, 11, 'B+', 8.0, 'Spring 2024'),
(177, 92, 3, 'A', 9.0, 'Spring 2023'),
(178, 92, 1, 'B-', 7.0, 'Fall 2023'),
(179, 93, 7, 'B-', 7.0, 'Fall 2022'),
(180, 93, 15, 'B-', 7.0, 'Fall 2022'),
(181, 94, 2, 'O', 10.0, 'Fall 2023'),
(182, 94, 9, 'B', 7.5, 'Spring 2023'),
(183, 95, 2, 'A-', 8.5, 'Fall 2023'),
(184, 95, 10, 'B', 7.5, 'Spring 2024'),
(185, 96, 10, 'A', 9.0, 'Fall 2023'),
(186, 97, 7, 'B-', 7.0, 'Spring 2023'),
(187, 97, 11, 'B+', 8.0, 'Fall 2022'),
(188, 97, 13, 'O', 10.0, 'Fall 2023'),
(189, 98, 6, 'B', 7.5, 'Spring 2023'),
(190, 99, 6, 'A', 9.0, 'Spring 2023'),
(191, 100, 3, 'A-', 8.5, 'Fall 2022')
ON CONFLICT DO NOTHING;

INSERT INTO products (product_id, product_name, category, unit_price, stock_quantity) VALUES
(6, 'Noise Cancelling Headphones', 'Audio', 349.99, 120),
(7, 'Smart Standing Desk 60"', 'Furniture', 599.00, 35),
(8, '4K Webcam Pro', 'Accessories', 199.99, 85),
(9, 'Thunderbolt 4 Docking Station', 'Accessories', 279.50, 60),
(10, 'Curved Gaming Monitor 27"', 'Displays', 389.00, 50),
(11, 'Ergonomic Mesh Chair', 'Furniture', 450.00, 40),
(12, 'Studio Condenser Microphone', 'Audio', 149.00, 95),
(13, 'Portable SSD 2TB', 'Storage', 189.99, 150),
(14, 'Server Rack 24U', 'Infrastructure', 899.00, 15),
(15, 'Smart LED Desk Lamp', 'Accessories', 69.99, 210)
ON CONFLICT DO NOTHING;

INSERT INTO customers (customer_id, customer_name, city, country) VALUES
(6, 'Quantum Dynamics', 'Boston', 'USA'),
(7, 'CyberWave Solutions', 'Toronto', 'Canada'),
(8, 'FinTech Pioneers', 'Zurich', 'Switzerland'),
(9, 'Starlight Logistics', 'Singapore', 'Singapore'),
(10, 'BluePeak Systems', 'Sydney', 'Australia'),
(11, 'Vanguard Analytics', 'Austin', 'USA'),
(12, 'Nordic Cloud Oy', 'Helsinki', 'Finland'),
(13, 'Atlas Aerospace', 'Toulouse', 'France'),
(14, 'Solaria Renewable Labs', 'Madrid', 'Spain'),
(15, 'Kyoto Robotics Corp', 'Kyoto', 'Japan')
ON CONFLICT DO NOTHING;

INSERT INTO orders (order_id, customer_id, order_date, total_amount, status) VALUES
(6, 6, '2024-02-20', 3249.50, 'Completed'),
(7, 7, '2024-02-24', 1420.00, 'Completed'),
(8, 8, '2024-03-01', 4890.00, 'Completed'),
(9, 9, '2024-03-05', 899.00, 'Completed'),
(10, 10, '2024-03-12', 2150.00, 'Processing'),
(11, 11, '2024-03-15', 680.00, 'Completed'),
(12, 12, '2024-03-20', 1890.50, 'Completed'),
(13, 13, '2024-03-22', 4500.00, 'Shipped'),
(14, 14, '2024-03-28', 1200.00, 'Completed'),
(15, 15, '2024-04-02', 3100.00, 'Completed')
ON CONFLICT DO NOTHING;

INSERT INTO employees (emp_id, emp_name, job_title, dept_id, hire_date, salary) VALUES
(7, 'Sarah Connor', 'Principal Systems Architect', 1, '2019-06-15', 165000.00),
(8, 'David Chen', 'Cloud Infrastructure Lead', 1, '2021-01-10', 150000.00),
(9, 'Elena Rostova', 'Senior Product Designer', 2, '2022-04-01', 125000.00),
(10, 'Marcus Vance', 'VP of Global Sales', 3, '2017-09-01', 180000.00),
(11, 'Lisa Wang', 'Senior Financial Analyst', 4, '2020-08-15', 110000.00),
(12, 'James Holden', 'Operations Manager', 2, '2021-11-20', 115000.00),
(13, 'Amara Okafor', 'HR Business Partner', 4, '2022-02-14', 85000.00),
(14, 'Klaus Mueller', 'Director of DevOps', 1, '2018-10-01', 170000.00),
(15, 'Rachel Green', 'Brand Marketing Specialist', 3, '2021-05-18', 88000.00)
ON CONFLICT DO NOTHING;
