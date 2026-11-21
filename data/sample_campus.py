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
    "CSE-II-B":  "Room 202 (CSE Block)",
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

# 1. Standardized Department Curriculum (Every department sums to 30 hrs/week)
CURRICULUM = {
    "AIDS-II": [
        ("Data Structures",     "lecture", 5),
        ("Linear Algebra",      "lecture", 5),
        ("Machine Learning",    "lecture", 5),
        ("Probability & Stats", "lecture", 5),
        ("Database Systems",    "lecture", 4),
        ("ML Practical Lab",    "lab",     3),
        ("DBMS Practical Lab",  "lab",     3),
    ],
    "CSE-II": [
        ("Design & Analysis Algo", "lecture", 5),
        ("Discrete Mathematics",   "lecture", 5),
        ("Operating Systems",      "lecture", 5),
        ("Computer Architecture",  "lecture", 5),
        ("Object Oriented Prog",   "lecture", 4),
        ("OS & Linux Lab",         "lab",     3),
        ("OOP Java Lab",           "lab",     3),
    ],
    "IT-II": [
        ("Web Technologies",      "lecture", 5),
        ("Database Systems",      "lecture", 5),
        ("Data Structures",       "lecture", 5),
        ("Discrete Mathematics",  "lecture", 5),
        ("Cyber Security Basics", "lecture", 4),
        ("Full Stack Web Lab",    "lab",     3),
        ("DBMS Practical Lab",    "lab",     3),
    ],
    "ECE-II": [
        ("Signals & Systems",   "lecture", 5),
        ("Digital Electronics", "lecture", 5),
        ("Microprocessors",     "lecture", 5),
        ("Linear Algebra",      "lecture", 5),
        ("Embedded Systems",    "lecture", 4),
        ("Digital & VLSI Lab",  "lab",     3),
        ("Microprocessor Lab",  "lab",     3),
    ],
}

# 2. Section-to-Faculty Mapping (Same subjects per department, distinct staff per section)
SECTION_STAFF = {
    "AIDS-II-A": {
        "Data Structures":     "Dr. A. Verma",
        "Linear Algebra":      "Dr. P. Sharma",
        "Machine Learning":    "Dr. K. Singh",
        "Probability & Stats": "Dr. S. Iyer",
        "Database Systems":    "Dr. R. Mehta",
        "ML Practical Lab":    "Dr. K. Singh",
        "DBMS Practical Lab":  "Dr. R. Mehta",
    },
    "AIDS-II-B": {
        "Data Structures":     "Prof. M. Nair",
        "Linear Algebra":      "Dr. P. Sharma",
        "Machine Learning":    "Dr. R. Menon",
        "Probability & Stats": "Dr. S. Iyer",
        "Database Systems":    "Dr. R. Mehta",
        "ML Practical Lab":    "Dr. R. Menon",
        "DBMS Practical Lab":  "Prof. M. Nair",
    },
    "CSE-II-A": {
        "Design & Analysis Algo": "Dr. V. Krishnan",
        "Discrete Mathematics":   "Prof. T. Das",
        "Operating Systems":      "Prof. N. Rao",
        "Computer Architecture":  "Dr. G. Subramanian",
        "Object Oriented Prog":   "Prof. L. Priya",
        "OS & Linux Lab":         "Prof. N. Rao",
        "OOP Java Lab":           "Prof. L. Priya",
    },
    "CSE-II-B": {
        "Design & Analysis Algo": "Dr. A. Verma",
        "Discrete Mathematics":   "Prof. T. Das",
        "Operating Systems":      "Dr. R. Menon",
        "Computer Architecture":  "Dr. G. Subramanian",
        "Object Oriented Prog":   "Prof. D. Karthik",
        "OS & Linux Lab":         "Dr. R. Menon",
        "OOP Java Lab":           "Prof. D. Karthik",
    },
    "IT-II-A": {
        "Web Technologies":      "Prof. D. Karthik",
        "Database Systems":      "Prof. M. Nair",
        "Data Structures":       "Dr. V. Krishnan",
        "Discrete Mathematics":  "Prof. T. Das",
        "Cyber Security Basics": "Dr. G. Subramanian",
        "Full Stack Web Lab":    "Prof. D. Karthik",
        "DBMS Practical Lab":    "Prof. M. Nair",
    },
    "ECE-II-A": {
        "Signals & Systems":   "Dr. H. Shankar",
        "Digital Electronics": "Prof. K. Anitha",
        "Microprocessors":     "Dr. B. Balaji",
        "Linear Algebra":      "Dr. P. Sharma",
        "Embedded Systems":    "Prof. K. Anitha",
        "Digital & VLSI Lab":  "Prof. K. Anitha",
        "Microprocessor Lab":  "Dr. B. Balaji",
    },
}

# 3. Auto-generate COURSES list from Curriculum + Staff Mapping
COURSES = []
for sec, staff_map in SECTION_STAFF.items():
    dept_key = sec.rsplit("-", 1)[0]  # e.g., "CSE-II-A" -> "CSE-II"
    for subj, r_type, hrs in CURRICULUM[dept_key]:
        COURSES.append((sec, subj, staff_map[subj], r_type, hrs))