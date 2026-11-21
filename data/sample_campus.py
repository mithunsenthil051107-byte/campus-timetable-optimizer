# data/sample_campus.py

DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri"]

PERIODS = [
    "09:00-09:50",
    "09:50-10:40",
    "10:55-11:45",
    "11:45-12:35",
    "01:15-02:05",
    "02:05-02:55",
]

SECTIONS = ["AIDS-II-A", "AIDS-II-B", "CSE-III-A"]

ROOMS = [
    {"name": "Room 301", "type": "lecture", "capacity": 65},
    {"name": "Room 302", "type": "lecture", "capacity": 65},
    {"name": "Room 305", "type": "lecture", "capacity": 65},
    {"name": "AI Lab 1", "type": "lab", "capacity": 65},
]

# Format: (section, subject, faculty, room_type_needed, hours_per_week)
COURSES = [
    ("AIDS-II-A", "Data Structures", "Dr. A. Verma", "lecture", 4),
    ("AIDS-II-A", "Linear Algebra", "Dr. P. Sharma", "lecture", 4),
    ("AIDS-II-A", "Machine Learning", "Dr. K. Singh", "lecture", 4),
    ("AIDS-II-A", "Probability & Stats", "Dr. S. Iyer", "lecture", 4),
    ("AIDS-II-A", "Professional Ethics", "Dr. R. Mehta", "lecture", 4),
    ("AIDS-II-A", "ML Lab", "Dr. K. Singh", "lab", 2),

    ("AIDS-II-B", "Data Structures", "Dr. A. Verma", "lecture", 4),
    ("AIDS-II-B", "Probability & Stats", "Dr. S. Iyer", "lecture", 4),
    ("AIDS-II-B", "DBMS", "Dr. R. Mehta", "lecture", 4),
    ("AIDS-II-B", "Linear Algebra", "Dr. P. Sharma", "lecture", 4),
    ("AIDS-II-B", "Optimization Tech", "Dr. K. Singh", "lecture", 4),
    ("AIDS-II-B", "DBMS Lab", "Dr. R. Mehta", "lab", 2),

    ("CSE-III-A", "Algorithms", "Dr. K. Singh", "lecture", 4),
    ("CSE-III-A", "Operating Systems", "Dr. S. Iyer", "lecture", 4),
    ("CSE-III-A", "Computer Networks", "Dr. R. Mehta", "lecture", 4),
    ("CSE-III-A", "Theory of Comp", "Dr. P. Sharma", "lecture", 4),
    ("CSE-III-A", "Software Engg", "Dr. A. Verma", "lecture", 4),
    ("CSE-III-A", "OS Lab", "Dr. S. Iyer", "lab", 2),
]