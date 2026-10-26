#!/usr/bin/env python3
"""
Populate Full Dataset
=====================
Loads the full multi-domain dataset (100 students, expanded courses, enrollments,
products, customers, orders, and employees) harvested from the Yale Spider benchmark
into the active database (`backend/text2sql.db`) and updates `database/init.sql`.

Preserves the original 10 ground-truth students (IDs 1-10) for benchmark consistency
while expanding the table to 100+ fully-qualified student records.
"""

import os
import random
import re
import sqlite3
import sys

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SPIDER_DIR = os.path.join(PROJECT_ROOT, "datasets", "spider")
SQLITE_DB_PATH = os.path.join(PROJECT_ROOT, "backend", "text2sql.db")
INIT_SQL_PATH = os.path.join(PROJECT_ROOT, "database", "init.sql")

random.seed(42)


def harvest_spider_students(limit=90):
    """Harvests real student names from Spider SQLite databases."""
    names = []
    spider_db_dir = os.path.join(SPIDER_DIR, "database")

    sources = [
        ("student_transcripts_tracking", "Students", "first_name", "last_name"),
        ("behavior_monitoring", "Students", "first_name", "last_name"),
        ("activity_1", "Student", "Fname", "LName"),
        ("allergy_1", "Student", "Fname", "LName"),
    ]

    for db_name, tbl, col_f, col_l in sources:
        p = os.path.join(spider_db_dir, db_name, f"{db_name}.sqlite")
        if os.path.exists(p):
            conn = sqlite3.connect(p)
            cur = conn.cursor()
            cur.execute(f"SELECT {col_f}, {col_l} FROM {tbl}")
            for fn, ln in cur.fetchall():
                if fn and ln and str(fn).isalpha() and str(ln).isalpha():
                    names.append((str(fn).strip(), str(ln).strip()))
            conn.close()

    # Also pull from college_2
    p_col = os.path.join(spider_db_dir, "college_2", "college_2.sqlite")
    if os.path.exists(p_col):
        conn = sqlite3.connect(p_col)
        cur = conn.cursor()
        cur.execute("SELECT name FROM student LIMIT 150;")
        for row in cur.fetchall():
            parts = str(row[0]).strip().split()
            if len(parts) >= 2 and parts[0].isalpha() and parts[1].isalpha():
                names.append((parts[0], parts[1]))
            elif len(parts) == 1 and parts[0].isalpha():
                names.append((parts[0], "Student"))
        conn.close()

    # Deduplicate
    seen = set()
    unique = []
    for fn, ln in names:
        key = (fn.lower(), ln.lower())
        if key not in seen:
            seen.add(key)
            unique.append((fn, ln))

    return unique[:limit]


def generate_additional_students(count=90):
    harvested = harvest_spider_students(limit=count)
    students = []
    # Starting ID 11
    for idx, (fn, ln) in enumerate(harvested, start=11):
        email = f"{fn.lower()}.{ln.lower()}{idx}@student.edu"
        dept_id = ((idx - 1) % 5) + 1
        # Realistic CGPA distribution
        cgpa = round(random.uniform(6.5, 9.8), 2)
        year = random.choice([2020, 2021, 2022, 2023, 2024])
        students.append((idx, fn, ln, email, dept_id, cgpa, year))
    return students


def generate_additional_courses():
    return [
        (6, "CS301", "Operating Systems & Concurrency", 4, 1, 1),
        (7, "CS302", "Distributed Cloud Architecture", 4, 1, 2),
        (8, "DS201", "Applied Natural Language Processing", 4, 2, 3),
        (9, "DS202", "Big Data Analytics & Spark", 4, 2, 3),
        (10, "EE201", "Digital Signal Processing", 3, 3, 4),
        (11, "EE202", "Embedded IoT Systems", 3, 3, 4),
        (12, "MATH201", "Probability & Applied Statistics", 4, 4, 5),
        (13, "MATH202", "Discrete Optimization & Graphs", 3, 4, 5),
        (14, "MGMT101", "Principles of Modern Management", 3, 5, 2),
        (15, "MGMT201", "Financial Econometrics", 3, 5, 5),
    ]


def generate_additional_instructors():
    return [
        (6, "Dr. Claude Shannon", "claude.shannon@univ.edu", 3, 135000.00),
        (7, "Dr. Geoffrey Hinton", "geoff.hinton@univ.edu", 2, 160000.00),
        (8, "Dr. Donald Knuth", "donald.knuth@univ.edu", 1, 145000.00),
        (9, "Dr. John von Neumann", "von.neumann@univ.edu", 4, 150000.00),
        (10, "Dr. Peter Drucker", "peter.drucker@univ.edu", 5, 120000.00),
    ]


def generate_additional_enrollments(student_ids, course_ids):
    enrollments = []
    grades = [
        ("A+", 10.0), ("A", 9.0), ("A-", 8.5),
        ("B+", 8.0), ("B", 7.5), ("B-", 7.0),
        ("O", 10.0), ("A", 9.0), ("B+", 8.0)
    ]
    semesters = ["Fall 2022", "Spring 2023", "Fall 2023", "Spring 2024"]

    eid = 10
    for sid in student_ids:
        # Each student takes 1-3 courses
        num_courses = random.randint(1, 3)
        selected_courses = random.sample(course_ids, num_courses)
        for cid in selected_courses:
            g, gp = random.choice(grades)
            sem = random.choice(semesters)
            enrollments.append((eid, sid, cid, g, gp, sem))
            eid += 1
    return enrollments


def generate_additional_products():
    return [
        (6, 'Noise Cancelling Headphones', 'Audio', 349.99, 120),
        (7, 'Smart Standing Desk 60"', 'Furniture', 599.00, 35),
        (8, '4K Webcam Pro', 'Accessories', 199.99, 85),
        (9, 'Thunderbolt 4 Docking Station', 'Accessories', 279.50, 60),
        (10, 'Curved Gaming Monitor 27"', 'Displays', 389.00, 50),
        (11, 'Ergonomic Mesh Chair', 'Furniture', 450.00, 40),
        (12, 'Studio Condenser Microphone', 'Audio', 149.00, 95),
        (13, 'Portable SSD 2TB', 'Storage', 189.99, 150),
        (14, 'Server Rack 24U', 'Infrastructure', 899.00, 15),
        (15, 'Smart LED Desk Lamp', 'Accessories', 69.99, 210),
    ]


def generate_additional_customers():
    return [
        (6, 'Quantum Dynamics', 'Boston', 'USA'),
        (7, 'CyberWave Solutions', 'Toronto', 'Canada'),
        (8, 'FinTech Pioneers', 'Zurich', 'Switzerland'),
        (9, 'Starlight Logistics', 'Singapore', 'Singapore'),
        (10, 'BluePeak Systems', 'Sydney', 'Australia'),
        (11, 'Vanguard Analytics', 'Austin', 'USA'),
        (12, 'Nordic Cloud Oy', 'Helsinki', 'Finland'),
        (13, 'Atlas Aerospace', 'Toulouse', 'France'),
        (14, 'Solaria Renewable Labs', 'Madrid', 'Spain'),
        (15, 'Kyoto Robotics Corp', 'Kyoto', 'Japan'),
    ]


def generate_additional_orders():
    return [
        (6, 6, '2024-02-20', 3249.50, 'Completed'),
        (7, 7, '2024-02-24', 1420.00, 'Completed'),
        (8, 8, '2024-03-01', 4890.00, 'Completed'),
        (9, 9, '2024-03-05', 899.00, 'Completed'),
        (10, 10, '2024-03-12', 2150.00, 'Processing'),
        (11, 11, '2024-03-15', 680.00, 'Completed'),
        (12, 12, '2024-03-20', 1890.50, 'Completed'),
        (13, 13, '2024-03-22', 4500.00, 'Shipped'),
        (14, 14, '2024-03-28', 1200.00, 'Completed'),
        (15, 15, '2024-04-02', 3100.00, 'Completed'),
    ]


def generate_additional_employees():
    return [
        (7, 'Sarah Connor', 'Principal Systems Architect', 1, '2019-06-15', 165000.00),
        (8, 'David Chen', 'Cloud Infrastructure Lead', 1, '2021-01-10', 150000.00),
        (9, 'Elena Rostova', 'Senior Product Designer', 2, '2022-04-01', 125000.00),
        (10, 'Marcus Vance', 'VP of Global Sales', 3, '2017-09-01', 180000.00),
        (11, 'Lisa Wang', 'Senior Financial Analyst', 4, '2020-08-15', 110000.00),
        (12, 'James Holden', 'Operations Manager', 2, '2021-11-20', 115000.00),
        (13, 'Amara Okafor', 'HR Business Partner', 4, '2022-02-14', 85000.00),
        (14, 'Klaus Mueller', 'Director of DevOps', 1, '2018-10-01', 170000.00),
        (15, 'Rachel Green', 'Brand Marketing Specialist', 3, '2021-05-18', 88000.00),
    ]


def populate_sqlite_database():
    """Populates the expanded dataset into backend/text2sql.db."""
    print(f"Connecting to SQLite database: {SQLITE_DB_PATH}")
    conn = sqlite3.connect(SQLITE_DB_PATH)
    cur = conn.cursor()

    # 1. Students (100 total)
    new_students = generate_additional_students(count=90)
    for s in new_students:
        cur.execute(
            """INSERT OR IGNORE INTO students 
               (student_id, first_name, last_name, email, department_id, cgpa, enrollment_year)
               VALUES (?, ?, ?, ?, ?, ?, ?);""",
            s
        )

    # 2. Instructors
    for inst in generate_additional_instructors():
        cur.execute(
            """INSERT OR IGNORE INTO instructors 
               (instructor_id, name, email, department_id, salary)
               VALUES (?, ?, ?, ?, ?);""",
            inst
        )

    # 3. Courses
    for c in generate_additional_courses():
        cur.execute(
            """INSERT OR IGNORE INTO courses 
               (course_id, course_code, course_title, credits, department_id, instructor_id)
               VALUES (?, ?, ?, ?, ?, ?);""",
            c
        )

    # 4. Enrollments
    all_student_ids = list(range(11, 101))
    all_course_ids = list(range(1, 16))
    new_enrollments = generate_additional_enrollments(all_student_ids, all_course_ids)
    for e in new_enrollments:
        cur.execute(
            """INSERT OR IGNORE INTO enrollments 
               (enrollment_id, student_id, course_id, grade, grade_point, semester)
               VALUES (?, ?, ?, ?, ?, ?);""",
            e
        )

    # 5. Products
    for p in generate_additional_products():
        cur.execute(
            """INSERT OR IGNORE INTO products 
               (product_id, product_name, category, unit_price, stock_quantity)
               VALUES (?, ?, ?, ?, ?);""",
            p
        )

    # 6. Customers
    for cust in generate_additional_customers():
        cur.execute(
            """INSERT OR IGNORE INTO customers 
               (customer_id, customer_name, city, country)
               VALUES (?, ?, ?, ?);""",
            cust
        )

    # 7. Orders
    for o in generate_additional_orders():
        cur.execute(
            """INSERT OR IGNORE INTO orders 
               (order_id, customer_id, order_date, total_amount, status)
               VALUES (?, ?, ?, ?, ?);""",
            o
        )

    # 8. Employees
    for emp in generate_additional_employees():
        cur.execute(
            """INSERT OR IGNORE INTO employees 
               (emp_id, emp_name, job_title, dept_id, hire_date, salary)
               VALUES (?, ?, ?, ?, ?, ?);""",
            emp
        )

    conn.commit()

    # Verify counts
    tables = [
        "students", "departments", "instructors", "courses", "enrollments",
        "customers", "products", "orders", "order_items",
        "corp_departments", "employees"
    ]
    print("\n✓ Updated SQLite text2sql.db row counts:")
    for t in tables:
        cur.execute(f"SELECT COUNT(*) FROM {t};")
        cnt = cur.fetchone()[0]
        print(f"  • {t:18}: {cnt:>4} rows")

    conn.close()


def update_init_sql_file():
    """Appends additional seed records into database/init.sql so Docker Postgres also has them."""
    new_students = generate_additional_students(count=90)
    new_courses = generate_additional_courses()
    new_instructors = generate_additional_instructors()
    new_products = generate_additional_products()
    new_customers = generate_additional_customers()
    new_orders = generate_additional_orders()
    new_employees = generate_additional_employees()
    all_student_ids = list(range(11, 101))
    all_course_ids = list(range(1, 16))
    new_enrollments = generate_additional_enrollments(all_student_ids, all_course_ids)

    # Check if already appended
    with open(INIT_SQL_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    if "-- EXPANDED SPIDER BENCHMARK DATASET" in content:
        print("database/init.sql already contains expanded dataset.")
        return

    sql_append = ["\n-- -------------------------------------------------------------"]
    sql_append.append("-- EXPANDED SPIDER BENCHMARK DATASET (100 Students & Extended Entities)")
    sql_append.append("-- -------------------------------------------------------------\n")

    # Additional instructors
    sql_append.append("INSERT INTO instructors (instructor_id, name, email, department_id, salary) VALUES")
    inst_lines = [f"({i[0]}, '{i[1]}', '{i[2]}', {i[3]}, {i[4]:.2f})" for i in new_instructors]
    sql_append.append(",\n".join(inst_lines) + "\nON CONFLICT DO NOTHING;\n")

    # Additional courses
    sql_append.append("INSERT INTO courses (course_id, course_code, course_title, credits, department_id, instructor_id) VALUES")
    course_lines = [f"({c[0]}, '{c[1]}', '{c[2]}', {c[3]}, {c[4]}, {c[5]})" for c in new_courses]
    sql_append.append(",\n".join(course_lines) + "\nON CONFLICT DO NOTHING;\n")

    # Additional students (11 to 100)
    sql_append.append("INSERT INTO students (student_id, first_name, last_name, email, department_id, cgpa, enrollment_year) VALUES")
    student_lines = [f"({s[0]}, '{s[1]}', '{s[2]}', '{s[3]}', {s[4]}, {s[5]}, {s[6]})" for s in new_students]
    sql_append.append(",\n".join(student_lines) + "\nON CONFLICT DO NOTHING;\n")

    # Additional enrollments
    sql_append.append("INSERT INTO enrollments (enrollment_id, student_id, course_id, grade, grade_point, semester) VALUES")
    enroll_lines = [f"({e[0]}, {e[1]}, {e[2]}, '{e[3]}', {e[4]}, '{e[5]}')" for e in new_enrollments]
    sql_append.append(",\n".join(enroll_lines) + "\nON CONFLICT DO NOTHING;\n")

    # Additional products
    sql_append.append("INSERT INTO products (product_id, product_name, category, unit_price, stock_quantity) VALUES")
    prod_lines = [f"({p[0]}, '{p[1]}', '{p[2]}', {p[3]:.2f}, {p[4]})" for p in new_products]
    sql_append.append(",\n".join(prod_lines) + "\nON CONFLICT DO NOTHING;\n")

    # Additional customers
    sql_append.append("INSERT INTO customers (customer_id, customer_name, city, country) VALUES")
    cust_lines = [f"({c[0]}, '{c[1]}', '{c[2]}', '{c[3]}')" for c in new_customers]
    sql_append.append(",\n".join(cust_lines) + "\nON CONFLICT DO NOTHING;\n")

    # Additional orders
    sql_append.append("INSERT INTO orders (order_id, customer_id, order_date, total_amount, status) VALUES")
    ord_lines = [f"({o[0]}, {o[1]}, '{o[2]}', {o[3]:.2f}, '{o[4]}')" for o in new_orders]
    sql_append.append(",\n".join(ord_lines) + "\nON CONFLICT DO NOTHING;\n")

    # Additional employees
    sql_append.append("INSERT INTO employees (emp_id, emp_name, job_title, dept_id, hire_date, salary) VALUES")
    emp_lines = [f"({e[0]}, '{e[1]}', '{e[2]}', {e[3]}, '{e[4]}', {e[5]:.2f})" for e in new_employees]
    sql_append.append(",\n".join(emp_lines) + "\nON CONFLICT DO NOTHING;\n")

    with open(INIT_SQL_PATH, "a", encoding="utf-8") as f:
        f.write("\n".join(sql_append))

    print(f"✓ Updated {INIT_SQL_PATH} with 100+ student records and extended entities.")


if __name__ == "__main__":
    populate_sqlite_database()
    update_init_sql_file()
