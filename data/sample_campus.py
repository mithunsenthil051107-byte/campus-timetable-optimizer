# data/sample_campus.py

DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri"]
DEPARTMENTS = ["AIDS", "CSE", "IT", "ECE"]
YEARS = ["I", "II", "III", "IV"]
SECTION_LETTERS = ["A", "B", "C", "D", "E"]


def _to_min(t_str):
    h, m = map(int, t_str.split(":"))
    return h * 60 + m


YEAR_SCHEDULES = {
    "I": {
        "label": "I-Year Shift (08:00 AM – 02:20 PM | Break: 09:40 | Lunch: 11:40–12:30)",
        "periods": [
            {"idx": 0, "label": "08:00-08:50", "start": _to_min("08:00"), "end": _to_min("08:50")},
            {"idx": 1, "label": "08:50-09:40", "start": _to_min("08:50"), "end": _to_min("09:40")},
            {"idx": 2, "label": "10:00-10:50", "start": _to_min("10:00"), "end": _to_min("10:50")},
            {"idx": 3, "label": "10:50-11:40", "start": _to_min("10:50"), "end": _to_min("11:40")},
            {"idx": 4, "label": "12:30-01:25", "start": _to_min("12:30"), "end": _to_min("13:25")},
            {"idx": 5, "label": "01:25-02:20", "start": _to_min("13:25"), "end": _to_min("14:20")},
        ],
    },
    "II": {
        "label": "II-Year Shift (08:30 AM – 02:50 PM | Break: 10:10 | Lunch: 12:10–01:00)",
        "periods": [
            {"idx": 0, "label": "08:30-09:20", "start": _to_min("08:30"), "end": _to_min("09:20")},
            {"idx": 1, "label": "09:20-10:10", "start": _to_min("09:20"), "end": _to_min("10:10")},
            {"idx": 2, "label": "10:30-11:20", "start": _to_min("10:30"), "end": _to_min("11:20")},
            {"idx": 3, "label": "11:20-12:10", "start": _to_min("11:20"), "end": _to_min("12:10")},
            {"idx": 4, "label": "01:00-01:55", "start": _to_min("13:00"), "end": _to_min("13:55")},
            {"idx": 5, "label": "01:55-02:50", "start": _to_min("13:55"), "end": _to_min("14:50")},
        ],
    },
    "III": {
        "label": "III-Year Shift (09:00 AM – 03:20 PM | Break: 10:40 | Lunch: 12:40–01:30)",
        "periods": [
            {"idx": 0, "label": "09:00-09:50", "start": _to_min("09:00"), "end": _to_min("09:50")},
            {"idx": 1, "label": "09:50-10:40", "start": _to_min("09:50"), "end": _to_min("10:40")},
            {"idx": 2, "label": "11:00-11:50", "start": _to_min("11:00"), "end": _to_min("11:50")},
            {"idx": 3, "label": "11:50-12:40", "start": _to_min("11:50"), "end": _to_min("12:40")},
            {"idx": 4, "label": "01:30-02:25", "start": _to_min("13:30"), "end": _to_min("14:25")},
            {"idx": 5, "label": "02:25-03:20", "start": _to_min("14:25"), "end": _to_min("15:20")},
        ],
    },
    "IV": {
        "label": "IV-Year Shift (09:30 AM – 03:50 PM | Break: 11:10 | Lunch: 01:10–02:00)",
        "periods": [
            {"idx": 0, "label": "09:30-10:20", "start": _to_min("09:30"), "end": _to_min("10:20")},
            {"idx": 1, "label": "10:20-11:10", "start": _to_min("10:20"), "end": _to_min("11:10")},
            {"idx": 2, "label": "11:30-12:20", "start": _to_min("11:30"), "end": _to_min("12:20")},
            {"idx": 3, "label": "12:20-01:10", "start": _to_min("12:20"), "end": _to_min("13:10")},
            {"idx": 4, "label": "02:00-02:55", "start": _to_min("14:00"), "end": _to_min("14:55")},
            {"idx": 5, "label": "02:55-03:50", "start": _to_min("14:55"), "end": _to_min("15:50")},
        ],
    },
}

PERIODS = [p["label"] for p in YEAR_SCHEDULES["II"]["periods"]]


def get_section_year(sec):
    return sec.split("-")[1]


def get_section_periods(sec):
    return YEAR_SCHEDULES[get_section_year(sec)]["periods"]


HOME_ROOMS = {}
ROOMS = []

BLOCK_MAP = {"AIDS": "AIDS Block", "CSE": "CSE Block", "IT": "IT Block", "ECE": "ECE Block"}
FLOOR_MAP = {"I": 1, "II": 2, "III": 3, "IV": 4}

for dept in DEPARTMENTS:
    for yr in YEARS:
        for idx, letter in enumerate(SECTION_LETTERS, start=1):
            sec = f"{dept}-{yr}-{letter}"
            room_no = f"{FLOOR_MAP[yr]}0{idx}"
            room_name = f"Room {room_no} ({BLOCK_MAP[dept]})"
            HOME_ROOMS[sec] = room_name
            ROOMS.append({"name": room_name, "type": "lecture", "capacity": 65})

SECTIONS = list(HOME_ROOMS.keys())

LAB_NAMES_BY_DEPT = {
    "AIDS": [
        "AI & Deep Learning Lab 1", "AI & Deep Learning Lab 2", "AI & Deep Learning Lab 3",
        "Data Science & Big Data Lab 1", "Data Science & Big Data Lab 2", "Data Science & Big Data Lab 3",
        "NLP & Vision Studio 1", "NLP & Vision Studio 2",
        "GPU Compute Lab 1", "GPU Compute Lab 2",
    ],
    "CSE": [
        "Core Computing Lab 1", "Core Computing Lab 2", "Core Computing Lab 3",
        "Systems & OS Lab 1", "Systems & OS Lab 2", "Systems & OS Lab 3",
        "Networks & Compiler Lab 1", "Networks & Compiler Lab 2",
        "Software Engg Studio 1", "Software Engg Studio 2",
    ],
    "IT": [
        "Full Stack Web Lab 1", "Full Stack Web Lab 2", "Full Stack Web Lab 3",
        "Cloud & DevOps Lab 1", "Cloud & DevOps Lab 2", "Cloud & DevOps Lab 3",
        "Cyber Security Lab 1", "Cyber Security Lab 2",
        "Mobile App Dev Studio 1", "Mobile App Dev Studio 2",
    ],
    "ECE": [
        "Digital & VLSI Lab 1", "Digital & VLSI Lab 2", "Digital & VLSI Lab 3",
        "Microprocessor & IoT Lab 1", "Microprocessor & IoT Lab 2", "Microprocessor & IoT Lab 3",
        "DSP & Communication Lab 1", "DSP & Communication Lab 2",
        "Embedded Robotics Lab 1", "Embedded Robotics Lab 2",
    ],
}

for dept, labs in LAB_NAMES_BY_DEPT.items():
    for l_name in labs:
        ROOMS.append({"name": l_name, "type": "lab", "capacity": 65})

CURRICULUM = {
    "AIDS-I": [
        ("Engineering Mathematics I",  "lecture", 5, 0),
        ("Programming in C (TCL)",     "tcl",     3, 2),
        ("Engineering Physics",        "lecture", 5, 0),
        ("Digital Logic Design (TCL)", "tcl",     3, 2),
        ("Communicative English",      "lecture", 4, 0),
        ("Basic Electrical Engg",      "lecture", 4, 0),
        ("Python & Linux Lab",         "lab",     0, 2),
    ],
    "AIDS-II": [
        ("Data Structures (TCL)",      "tcl",     3, 2),
        ("Linear Algebra",             "lecture", 5, 0),
        ("Machine Learning (TCL)",     "tcl",     3, 2),
        ("Probability & Statistics",   "lecture", 5, 0),
        ("Database Systems (TCL)",     "tcl",     3, 2),
        ("Operating Systems",          "lecture", 5, 0),
    ],
    "AIDS-III": [
        ("Deep Learning (TCL)",        "tcl",     3, 2),
        ("Natural Language Proc",      "lecture", 5, 0),
        ("Big Data Analytics (TCL)",   "tcl",     3, 2),
        ("Reinforcement Learning",     "lecture", 5, 0),
        ("Computer Vision (TCL)",      "tcl",     3, 2),
        ("AI Ethics & Governance",     "lecture", 5, 0),
    ],
    "AIDS-IV": [
        ("Generative AI & LLMs (TCL)", "tcl",     3, 2),
        ("MLOps & Cloud Scale (TCL)",  "tcl",     3, 2),
        ("Edge AI & Robotics",         "lecture", 5, 0),
        ("AI Product Strategy",        "lecture", 5, 0),
        ("Distributed AI Systems",     "lecture", 4, 0),
        ("Research Seminar & Ethics",  "lecture", 4, 0),
        ("Capstone Research Lab",      "lab",     0, 2),
    ],
    "CSE-I": [
        ("Engineering Mathematics I",  "lecture", 5, 0),
        ("Problem Solving in C (TCL)", "tcl",     3, 2),
        ("Engineering Chemistry",      "lecture", 5, 0),
        ("Digital Principles (TCL)",   "tcl",     3, 2),
        ("Technical English",          "lecture", 4, 0),
        ("Engineering Graphics",       "lecture", 4, 0),
        ("IT Workshop & Git Lab",      "lab",     0, 2),
    ],
    "CSE-II": [
        ("Design & Analysis Algo",     "lecture", 5, 0),
        ("Discrete Mathematics",       "lecture", 5, 0),
        ("Operating Systems (TCL)",    "tcl",     3, 2),
        ("Computer Architecture",      "lecture", 5, 0),
        ("Object Oriented Prog (TCL)", "tcl",     3, 2),
        ("Database Management (TCL)",  "tcl",     3, 2),
    ],
    "CSE-III": [
        ("Computer Networks (TCL)",    "tcl",     3, 2),
        ("Theory of Computation",      "lecture", 5, 0),
        ("Compiler Design (TCL)",      "tcl",     3, 2),
        ("Artificial Intelligence",    "lecture", 5, 0),
        ("Software Engineering (TCL)", "tcl",     3, 2),
        ("Distributed Computing",      "lecture", 5, 0),
    ],
    "CSE-IV": [
        ("Cloud Architecture (TCL)",   "tcl",     3, 2),
        ("Cyber Security & Crypto",    "lecture", 5, 0),
        ("High Performance Comp (TCL)","tcl",     3, 2),
        ("Blockchain Systems",         "lecture", 5, 0),
        ("System Design & Scale",      "lecture", 4, 0),
        ("Enterprise Architecture",    "lecture", 4, 0),
        ("Capstone Engineering Lab",   "lab",     0, 2),
    ],
    "IT-I": [
        ("Engineering Mathematics I",  "lecture", 5, 0),
        ("Structured Prog in C (TCL)", "tcl",     3, 2),
        ("Applied Physics",            "lecture", 5, 0),
        ("Web Essentials (TCL)",       "tcl",     3, 2),
        ("Professional English",       "lecture", 4, 0),
        ("Environmental Science",      "lecture", 4, 0),
        ("Open Source Tools Lab",      "lab",     0, 2),
    ],
    "IT-II": [
        ("Full Stack Web Tech (TCL)",  "tcl",     3, 2),
        ("Database Systems (TCL)",     "tcl",     3, 2),
        ("Data Structures & Algo",     "lecture", 5, 0),
        ("Discrete Structures",        "lecture", 5, 0),
        ("Computer Networks (TCL)",    "tcl",     3, 2),
        ("Human Computer Interaction", "lecture", 5, 0),
    ],
    "IT-III": [
        ("Cloud & Virtualization(TCL)","tcl",     3, 2),
        ("Information Security",       "lecture", 5, 0),
        ("Mobile App Dev (TCL)",       "tcl",     3, 2),
        ("Service Oriented Arch",      "lecture", 5, 0),
        ("DevOps Engineering (TCL)",   "tcl",     3, 2),
        ("Data Warehousing",           "lecture", 5, 0),
    ],
    "IT-IV": [
        ("Enterprise Cloud Ops (TCL)", "tcl",     3, 2),
        ("Ethical Hacking (TCL)",      "tcl",     3, 2),
        ("Enterprise Resource Plan",   "lecture", 5, 0),
        ("Software Quality Assurance", "lecture", 5, 0),
        ("IT Service Management",      "lecture", 4, 0),
        ("Digital Governance",         "lecture", 4, 0),
        ("Industry Capstone Lab",      "lab",     0, 2),
    ],
    "ECE-I": [
        ("Engineering Mathematics I",  "lecture", 5, 0),
        ("Circuit Analysis (TCL)",     "tcl",     3, 2),
        ("Semiconductor Physics",      "lecture", 5, 0),
        ("C Programming & Logic (TCL)","tcl",     3, 2),
        ("Technical Communication",    "lecture", 4, 0),
        ("Engineering Mechanics",      "lecture", 4, 0),
        ("Electronics Workshop Lab",   "lab",     0, 2),
    ],
    "ECE-II": [
        ("Signals & Systems",          "lecture", 5, 0),
        ("Digital Electronics (TCL)",  "tcl",     3, 2),
        ("Microprocessors (TCL)",      "tcl",     3, 2),
        ("Linear Algebra & Transforms","lecture", 5, 0),
        ("Analog Circuits (TCL)",      "tcl",     3, 2),
        ("Electromagnetic Fields",     "lecture", 5, 0),
    ],
    "ECE-III": [
        ("VLSI Chip Design (TCL)",     "tcl",     3, 2),
        ("Wireless Communication",     "lecture", 5, 0),
        ("Digital Signal Proc (TCL)",  "tcl",     3, 2),
        ("Control Systems",            "lecture", 5, 0),
        ("Embedded IoT Systems (TCL)", "tcl",     3, 2),
        ("Antennas & Wave Prop",       "lecture", 5, 0),
    ],
    "ECE-IV": [
        ("5G & RF System Design (TCL)","tcl",     3, 2),
        ("Embedded Robotics (TCL)",    "tcl",     3, 2),
        ("Optical Communication",      "lecture", 5, 0),
        ("Satellite Communication",    "lecture", 5, 0),
        ("Avionics & Radar Systems",   "lecture", 4, 0),
        ("Biomedical Instrumentation", "lecture", 4, 0),
        ("Hardware Capstone Lab",      "lab",     0, 2),
    ],
}

# 60 Faculty per department (15 per Year Group) so each professor has max 2 sections (~10 hrs/week)
FACULTY_POOL = {
    dept: [f"Prof. {dept}-F{i:02d}" for i in range(1, 61)]
    for dept in DEPARTMENTS
}
FACULTY_POOL["AIDS"][:6] = ["Dr. A. Verma", "Dr. P. Sharma", "Dr. K. Singh", "Dr. S. Iyer", "Dr. R. Mehta", "Dr. R. Menon"]
FACULTY_POOL["CSE"][:6]  = ["Dr. V. Krishnan", "Prof. T. Das", "Prof. N. Rao", "Dr. G. Subramanian", "Prof. L. Priya", "Prof. S. Vignesh"]
FACULTY_POOL["IT"][:6]   = ["Prof. D. Karthik", "Prof. V. Gayathri", "Prof. M. Nair", "Prof. P. Nandhini", "Prof. K. Mohan", "Prof. B. Harish"]
FACULTY_POOL["ECE"][:6]  = ["Dr. H. Shankar", "Prof. K. Anitha", "Dr. B. Balaji", "Dr. M. Senthil", "Prof. R. Pavithra", "Dr. S. Kavitha"]

COURSES = []
SECTION_STAFF = {}

for sec in SECTIONS:
    dept, yr, letter = sec.split("-")
    dept_yr_key = f"{dept}-{yr}"
    sec_idx = SECTION_LETTERS.index(letter)
    yr_idx = YEARS.index(yr)
    pool = FACULTY_POOL[dept]

    yr_slice = pool[yr_idx * 15 : (yr_idx + 1) * 15]

    SECTION_STAFF[sec] = {}
    for subj_idx, (subj, mode, th_hrs, lab_hrs) in enumerate(CURRICULUM[dept_yr_key]):
        fac = yr_slice[(sec_idx * 3 + subj_idx) % len(yr_slice)]
        SECTION_STAFF[sec][subj] = fac

        if mode == "lecture":
            COURSES.append((sec, subj, fac, "lecture", th_hrs, "Theory"))
        elif mode == "lab":
            COURSES.append((sec, subj, fac, "lab", lab_hrs, "Lab"))
        elif mode == "tcl":
            COURSES.append((sec, f"{subj} [Theory]", fac, "lecture", th_hrs, "Theory-cum-Lab"))
            COURSES.append((sec, f"{subj} [Lab]", fac, "lab", lab_hrs, "Theory-cum-Lab"))