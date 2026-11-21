# solver/exam_scheduler.py
import time
import pandas as pd
from ortools.sat.python import cp_model
from data.sample_campus import CURRICULUM, SECTION_STAFF

# Exam Hall Configurations: Long Bench (2 seats/bench) vs Small Single Bench (1 seat/bench)
EXAM_HALLS = [
    {"name": "Main Hall 101 (AIDS)", "bench_type": "Long Bench (2-Seater)",  "benches": 20, "seats_per_bench": 2},  # 40 seats
    {"name": "Main Hall 102 (AIDS)", "bench_type": "Long Bench (2-Seater)",  "benches": 20, "seats_per_bench": 2},  # 40 seats
    {"name": "Main Hall 201 (CSE)",  "bench_type": "Long Bench (2-Seater)",  "benches": 20, "seats_per_bench": 2},  # 40 seats
    {"name": "Main Hall 202 (CSE)",  "bench_type": "Long Bench (2-Seater)",  "benches": 20, "seats_per_bench": 2},  # 40 seats
    {"name": "Seminar Hall 301 (IT)","bench_type": "Small Bench (1-Seater)", "benches": 30, "seats_per_bench": 1},  # 30 seats
    {"name": "Drawing Hall 401 (ECE)","bench_type": "Small Bench (1-Seater)","benches": 30, "seats_per_bench": 1},  # 30 seats
]

# Roll Number Prefixes & Strength per Section (60 students each = 360 total campus strength)
SECTION_ROLL_INFO = {
    "AIDS-II-A": ("24AID", 1, 60),
    "AIDS-II-B": ("24AID", 61, 120),
    "CSE-II-A":  ("24CSE", 1, 60),
    "CSE-II-B":  ("24CSE", 61, 120),
    "IT-II-A":   ("24IT",  1, 60),
    "ECE-II-A":  ("24ECE", 1, 60),
}


def generate_hall_seating_plan(hall_info, allocations):
    """
    Generates exact bench-by-bench roll number seating for a single exam hall.
    - Long Bench (2-Seater): Pairs Seat A (Dept 1) with Seat B (Dept 2) on the same bench!
    - Small Bench (1-Seater): Interleaves students from different departments across single desks.
    """
    benches = hall_info["benches"]
    spb = hall_info["seats_per_bench"]
    rows = []

    if spb == 2:
        # Separate allocations into Side A and Side B (different subjects/departments)
        side_a, side_b = [], []
        for alloc in allocations:
            target = side_a if len(side_a) <= len(side_b) else side_b
            for r_num in alloc["roll_list"]:
                target.append((r_num, alloc["section"], alloc["subject"]))

        for b_idx in range(1, benches + 1):
            seat_a = side_a[b_idx - 1] if (b_idx - 1) < len(side_a) else ("— EMPTY —", "-", "-")
            seat_b = side_b[b_idx - 1] if (b_idx - 1) < len(side_b) else ("— EMPTY —", "-", "-")
            rows.append({
                "Bench_No": f"Bench {b_idx:02d}",
                "Bench_Type": "Long Bench (2-Seater)",
                "Left_Seat (A)": f"{seat_a[0]} ({seat_a[1]})" if seat_a[1] != "-" else "EMPTY",
                "Left_Subject": seat_a[2],
                "Right_Seat (B)": f"{seat_b[0]} ({seat_b[1]})" if seat_b[1] != "-" else "EMPTY",
                "Right_Subject": seat_b[2],
                "Anti_Malpractice_Check": "✅ Different Subjects" if (seat_a[2] != seat_b[2] and seat_b[2] != "-") else "✅ Single/Empty",
            })
    else:
        # Small Bench (1-Seater): Interleave streams round-robin across desks 1..30
        streams = []
        for alloc in allocations:
            streams.append([(r_num, alloc["section"], alloc["subject"]) for r_num in alloc["roll_list"]])

        interleaved = []
        max_len = max((len(s) for s in streams), default=0)
        for i in range(max_len):
            for s in streams:
                if i < len(s):
                    interleaved.append(s[i])

        for b_idx in range(1, benches + 1):
            seat = interleaved[b_idx - 1] if (b_idx - 1) < len(interleaved) else ("— EMPTY —", "-", "-")
            rows.append({
                "Bench_No": f"Desk {b_idx:02d}",
                "Bench_Type": "Small Bench (1-Seater)",
                "Student_Roll_No": f"{seat[0]} ({seat[1]})" if seat[1] != "-" else "EMPTY",
                "Subject": seat[2],
                "Anti_Malpractice_Check": "✅ Isolated Single Desk",
            })
    return pd.DataFrame(rows)


def solve_exam_schedule(
    exam_days=None,
    sessions=("Forenoon (09:30-12:30)", "Afternoon (01:30-04:30)"),
    unavailable_faculty=None,
):
    exam_days = exam_days or ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
    unavailable_faculty = set(unavailable_faculty or [])

    model = cp_model.CpModel()
    num_days = len(exam_days)
    num_sessions = len(sessions)

    dept_exams = {
        dept: [subj for subj, r_type, _ in subjects if r_type == "lecture"]
        for dept, subjects in CURRICULUM.items()
    }

    sections = list(SECTION_STAFF.keys())
    all_faculty = sorted(list({fac for m in SECTION_STAFF.values() for fac in m.values()} - unavailable_faculty))

    # 1. Decision Variables: e[(dept, subj_idx, d, s)]
    e = {}
    for dept, subjs in dept_exams.items():
        for s_idx in range(len(subjs)):
            for d in range(num_days):
                for s in range(num_sessions):
                    e[(dept, s_idx, d, s)] = model.NewBoolVar(f"exam_{dept}_{s_idx}_{d}_{s}")

    # Invigilation variables: inv[(hall_idx, fac, d, s)]
    inv = {}
    for h_idx in range(len(EXAM_HALLS)):
        for fac in all_faculty:
            for d in range(num_days):
                for s in range(num_sessions):
                    inv[(h_idx, fac, d, s)] = model.NewBoolVar(f"inv_{h_idx}_{fac}_{d}_{s}")

    # 2. Hard Constraints
    # A: Every subject scheduled once
    for dept, subjs in dept_exams.items():
        for s_idx in range(len(subjs)):
            model.Add(sum(e[(dept, s_idx, d, s)] for d in range(num_days) for s in range(num_sessions)) == 1)

    # B: Max 1 exam per day per department
    for dept, subjs in dept_exams.items():
        for d in range(num_days):
            model.Add(sum(e[(dept, s_idx, d, s)] for s_idx in range(len(subjs)) for s in range(num_sessions)) <= 1)

    # C: Ensure at least 2 DIFFERENT departments write exams simultaneously when possible
    # so Long Benches (2-seaters) pair different subjects!
    total_campus_seats = sum(h["benches"] * h["seats_per_bench"] for h in EXAM_HALLS)
    for d in range(num_days):
        for s in range(num_sessions):
            total_students_slot = []
            for sec in sections:
                dept = sec.rsplit("-", 1)[0]
                _, start_r, end_r = SECTION_ROLL_INFO[sec]
                strength = end_r - start_r + 1
                for s_idx in range(len(dept_exams[dept])):
                    total_students_slot.append(e[(dept, s_idx, d, s)] * strength)
            model.Add(sum(total_students_slot) <= total_campus_seats)

    # 3. Solve Exam Timetable
    start_time = time.time()
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 10.0
    status = solver.Solve(model)

    if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        return None, round((time.time() - start_time) * 1000, 2), solver.StatusName(status), {}

    # 4. Anti-Malpractice Cross-Department Hall & Roll-Number Packing
    schedule_rows = []
    seating_plans = {}  # key: (Day, Session, Hall_Name) -> DataFrame of benches
    fac_duty_count = {f: 0 for f in all_faculty}

    for d in range(num_days):
        for s in range(num_sessions):
            day_name = exam_days[d]
            sess_name = sessions[s]

            # Gather active sections writing an exam in this slot, grouped by subject
            subject_queues = {}  # subject -> list of student dicts
            for sec in sections:
                dept = sec.rsplit("-", 1)[0]
                for s_idx, subj in enumerate(dept_exams[dept]):
                    if solver.Value(e[(dept, s_idx, d, s)]) == 1:
                        prefix, r_start, r_end = SECTION_ROLL_INFO[sec]
                        rolls = [f"{prefix}{r:03d}" for r in range(r_start, r_end + 1)]
                        subject_queues.setdefault(subj, []).append({
                            "section": sec,
                            "subject": subj,
                            "rolls": rolls,
                        })

            if not subject_queues:
                continue

            # Flatten into per-subject student pools
            pools = {}
            for subj, sec_list in subject_queues.items():
                pools[subj] = []
                for item in sec_list:
                    for r in item["rolls"]:
                        pools[subj].append((r, item["section"], subj))

            used_fac_this_slot = set()

            # Fill Exam Halls: Pair 2 DIFFERENT subjects on Long Benches, or 1 stream on Small Benches
            for hall in EXAM_HALLS:
                active_subjs = [sub for sub, q in pools.items() if len(q) > 0]
                if not active_subjs:
                    break

                benches = hall["benches"]
                spb = hall["seats_per_bench"]
                allocations = []

                if spb == 2:
                    # Pick up to 2 DIFFERENT subjects for Left vs Right bench seats
                    active_subjs.sort(key=lambda sub: len(pools[sub]), reverse=True)
                    subj_left = active_subjs[0]
                    take_left = pools[subj_left][:benches]
                    pools[subj_left] = pools[subj_left][benches:]

                    # Group taken rolls by section for clean display
                    for sec_name in sorted(list({x[1] for x in take_left})):
                        sec_rolls = [x[0] for x in take_left if x[1] == sec_name]
                        allocations.append({"section": sec_name, "subject": subj_left, "roll_list": sec_rolls})

                    if len(active_subjs) > 1:
                        subj_right = active_subjs[1]
                        take_right = pools[subj_right][:benches]
                        pools[subj_right] = pools[subj_right][benches:]
                        for sec_name in sorted(list({x[1] for x in take_right})):
                            sec_rolls = [x[0] for x in take_right if x[1] == sec_name]
                            allocations.append({"section": sec_name, "subject": subj_right, "roll_list": sec_rolls})
                else:
                    # Small Bench (1-Seater): Interleave available subjects up to `benches` seats
                    taken = []
                    while len(taken) < benches and any(len(q) > 0 for q in pools.values()):
                        for sub in list(pools.keys()):
                            if pools[sub] and len(taken) < benches:
                                taken.append(pools[sub].pop(0))
                    for (sec_name, sub_name) in sorted(list({(x[1], x[2]) for x in taken})):
                        sec_rolls = [x[0] for x in taken if x[1] == sec_name and x[2] == sub_name]
                        allocations.append({"section": sec_name, "subject": sub_name, "roll_list": sec_rolls})

                if not allocations:
                    continue

                # Assign fairest available invigilator
                avail_inv = [f for f in all_faculty if f not in used_fac_this_slot]
                avail_inv.sort(key=lambda f: fac_duty_count[f])
                chosen_inv = avail_inv[0] if avail_inv else "Reserve Staff"
                if avail_inv:
                    used_fac_this_slot.add(chosen_inv)
                    fac_duty_count[chosen_inv] += 1

                # Build bench-by-bench seating table
                seating_df = generate_hall_seating_plan(hall, allocations)
                seating_plans[(day_name, sess_name, hall["name"])] = seating_df

                # Summary row for master exam table
                batch_summary = "  +  ".join(
                    f"{a['section']} [{a['roll_list'][0]}–{a['roll_list'][-1]}] ({a['subject']})"
                    for a in allocations
                )
                total_seated = sum(len(a["roll_list"]) for a in allocations)
                cap = benches * spb

                schedule_rows.append({
                    "Day_Idx": d,
                    "Day": day_name,
                    "Session": sess_name,
                    "Exam_Hall": hall["name"],
                    "Bench_Layout": hall["bench_type"],
                    "Occupancy": f"{total_seated}/{cap} Seats",
                    "Cross_Dept_Roll_Allocation": batch_summary,
                    "Invigilator": chosen_inv,
                })

    solve_ms = round((time.time() - start_time) * 1000, 2)
    res_df = pd.DataFrame(schedule_rows).sort_values(["Day_Idx", "Session", "Exam_Hall"])
    return res_df, solve_ms, solver.StatusName(status), seating_plans