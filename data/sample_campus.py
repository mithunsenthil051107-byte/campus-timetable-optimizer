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

# Each section has a dedicated Home Classroom for all theory lectures
HOME_ROOMS = {
    "AIDS-II-A": "Room 101 (AIDS Block)",
    "AIDS-II-B": "Room 102 (AIDS Block)",
    "CSE-II-A":  "Room 201 (CSE Block)",
    "CSE-III-A": "Room 202 (CSE Block)",
    "IT-II-A":   "Room 301 (IT Block)",
    "ECE-II-A":  "Room 401 (ECE Block)",
}

SECTIONS = list(HOME_ROOMS.keys())

ROOMS = [
    {"name": "Room 101 (AIDS Block)", "type": "lecture", "capacity": 65},
    {"name": "Room 102 (AIDS Block)", "type": "lecture", "capacity": 65},
    {"name": "Room 201 (CSE Block)",  "type": "lecture", "capacity": 65},
    {"name": "Room 202 (CSE Block)",  "type": "lecture", "capacity": 65},
    {"name": "Room 301 (IT Block)",   "type": "lecture", "capacity": 65},
    {"name": "Room 401 (ECE Block)",  "type": "lecture", "capacity": 65},
    {"name": "AI & ML Lab",           "type": "lab",     "capacity": 65},
    {"name": "Systems & Networks Lab","type": "lab",     "capacity": 65},
    {"name": "Electronics & IoT Lab", "type": "lab",     "capacity": 65},
]

# Every section has EXACTLY 30 hours/week (5 days x 6 periods = 0 free slots!)
# Format: (section, subject, faculty, room_type_needed, hours_per_week)
COURSES = [
    # --- AIDS-II-A (30 hrs) ---
    ("AIDS-II-A", "Data Structures",      "Dr. A. Verma",    "lecture", 5),
    ("AIDS-II-A", "Linear Algebra",       "Dr. P. Sharma",   "lecture", 5),
    ("AIDS-II-A", "Machine Learning",     "Dr. K. Singh",    "lecture", 5),
    ("AIDS-II-A", "Probability & Stats",  "Dr. S. Iyer",     "lecture", 5),
    ("AIDS-II-A", "Operating Systems",    "Prof. N. Rao",    "lecture", 4),
    ("AIDS-II-A", "ML Practical Lab",     "Dr. K. Singh",    "lab",     3),
    ("AIDS-II-A", "DSA Coding Lab",       "Dr. A. Verma",    "lab",     3),

    # --- AIDS-II-B (30 hrs) ---
    ("AIDS-II-B", "Data Structures",      "Prof. M. Nair",   "lecture", 5),
    ("AIDS-II-B", "Linear Algebra",       "Dr. P. Sharma",   "lecture", 5),
    ("AIDS-II-B", "Machine Learning",     "Dr. R. Menon",    "lecture", 5),
    ("AIDS-II-B", "Probability & Stats",  "Dr. S. Iyer",     "lecture", 5),
    ("AIDS-II-B", "Database Systems",     "Dr. R. Mehta",    "lecture", 4),
    ("AIDS-II-B", "ML Practical Lab",     "Dr. R. Menon",    "lab",     3),
    ("AIDS-II-B", "DBMS Practical Lab",   "Dr. R. Mehta",    "lab",     3),

    # --- CSE-II-A (30 hrs) ---
    ("CSE-II-A",  "Design & Analysis Algo","Dr. V. Krishnan","lecture", 5),
    ("CSE-II-A",  "Discrete Mathematics", "Prof. T. Das",    "lecture", 5),
    ("CSE-II-A",  "Operating Systems",    "Prof. N. Rao",    "lecture", 5),
    ("CSE-II-A",  "Computer Architecture","Dr. G. Subramanian","lecture", 5),
    ("CSE-II-A",  "Object Oriented Prog", "Prof. L. Priya",  "lecture", 4),
    ("CSE-II-A",  "OS & Linux Lab",       "Prof. N. Rao",    "lab",     3),
    ("CSE-II-A",  "OOP Java Lab",         "Prof. L. Priya",  "lab",     3),

    # --- CSE-III-A (30 hrs) ---
    ("CSE-III-A", "Computer Networks",    "Dr. R. Mehta",    "lecture", 5),
    ("CSE-III-A", "Theory of Computation","Dr. V. Krishnan", "lecture", 5),
    ("CSE-III-A", "Compiler Design",      "Prof. T. Das",    "lecture", 5),
    ("CSE-III-A", "Artificial Intelligence","Dr. R. Menon",  "lecture", 5),
    ("CSE-III-A", "Software Engineering", "Prof. L. Priya",  "lecture", 4),
    ("CSE-III-A", "Networks Socket Lab",  "Dr. R. Mehta",    "lab",     3),
    ("CSE-III-A", "AI & Python Lab",      "Dr. R. Menon",    "lab",     3),

    # --- IT-II-A (30 hrs) ---
    ("IT-II-A",   "Web Technologies",     "Prof. D. Karthik","lecture", 5),
    ("IT-II-A",   "Database Systems",     "Prof. M. Nair",   "lecture", 5),
    ("IT-II-A",   "Data Structures",      "Dr. A. Verma",    "lecture", 5),
    ("IT-II-A",   "Discrete Mathematics", "Prof. T. Das",    "lecture", 5),
    ("IT-II-A",   "Cyber Security Basics","Dr. G. Subramanian","lecture", 4),
    ("IT-II-A",   "Full Stack Web Lab",   "Prof. D. Karthik","lab",     3),
    ("IT-II-A",   "DBMS Practical Lab",   "Prof. M. Nair",   "lab",     3),

    # --- ECE-II-A (30 hrs) ---
    ("ECE-II-A",  "Signals & Systems",    "Dr. H. Shankar",  "lecture", 5),
    ("ECE-II-A",  "Digital Electronics",  "Prof. K. Anitha", "lecture", 5),
    ("ECE-II-A",  "Microprocessors",      "Dr. B. Balaji",   "lecture", 5),
    ("ECE-II-A",  "Linear Algebra",       "Dr. P. Sharma",   "lecture", 5),
    ("ECE-II-A",  "Embedded Systems",     "Prof. D. Karthik","lecture", 4),
    ("ECE-II-A",  "Digital & VLSI Lab",   "Prof. K. Anitha", "lab",     3),
    ("ECE-II-A",  "Microprocessor Lab",   "Dr. B. Balaji",   "lab",     3),
]