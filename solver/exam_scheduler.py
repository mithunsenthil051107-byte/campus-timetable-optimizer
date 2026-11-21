# solver/exam_scheduler.py
import time
import pandas as pd
from ortools.sat.python import cp_model
from data.sample_campus import (
    CURRICULUM,
    SECTION_STAFF,
    DEPARTMENTS,
    YEARS,
    SECTION_LETTERS,
)

EXAM_HALLS = []
for b_idx in range(1, 51):
    EXAM_HALLS.append({
        "name": f"Main Hall {b_idx:02d} (Long Bench)",
        "bench_type": "Long Bench (2-Seater)",
        "benches": 20,
        "seats_per_bench": 2,
    })
for s_idx in range(1, 21):
    EXAM_HALLS.append({
        "name": f"Seminar Hall {s_idx:02d} (Single Desk)",
        "bench_type": "Small Bench (1-Seater)",
        "benches": 20,
        "seats_per_bench": 1,
    })

YEAR_BATCH_PREFIX = {"I": "26", "II": "25", "III": "24", "IV": "23"}
DEPT_CODE = {"AIDS": "AID", "CSE": "CSE", "IT": "IT", "ECE": "ECE"}

SECTION_ROLL_INFO = {}
for dept in DEPARTMENTS:
    for yr in YEARS:
        for idx, letter in enumerate(SECTION_LETTERS):
            sec = f"{dept}-{yr}-{letter}"
            prefix = f"{YEAR_BATCH_PREFIX[yr]}{DEPT_CODE[dept]}"
            SECTION_ROLL_INFO[sec] = (prefix, idx * 60 + 1, (idx + 1) * 60)


def generate_hall_seating_plan(hall_info, allocations):
    benches = hall_info["benches"]
    spb = hall_info["seats_per_bench"]
    rows = []

    if spb == 2:
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
                "Anti_Malpractice_Check": (
                    "✅ Different Subjects"
                    if (seat_a[2] != seat_b[2] and seat_b[2] != "-")
                    else "✅ Single/Empty"
                ),
            })
    else:
        streams = [
            [(r_num, alloc["section"], alloc["subject"]) for r_num in alloc["roll_list"]]
            for alloc in allocations
        ]
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
        dept: [subj for subj, mode, _, _ in subjects if mode in ("lecture", "tcl")]
        for dept, subjects in CURRICULUM.items()
    }

    sections = list(SECTION_STAFF.keys())
    all_faculty = sorted(list({fac for m in SECTION_STAFF.values() for fac in m.values()} - unavailable_faculty))

    e = {}
    for dept_yr, subjs in dept_exams.items():
        for s_idx in range(len(subjs)):
            for d in range(num_days):
                for s in range(num_sessions):
                    e[(dept_yr, s_idx, d, s)] = model.NewBoolVar(f"exam_{dept_yr}_{s_idx}_{d}_{s}")

    for dept_yr, subjs in dept_exams.items():
        for s_idx in range(len(subjs)):
            model.Add(sum(e[(dept_yr, s_idx, d, s)] for d in range(num_days) for s in range(num_sessions)) == 1)

    for dept_yr, subjs in dept_exams.items():
        for d in range(num_days):
            model.Add(sum(e[(dept_yr, s_idx, d, s)] for s_idx in range(len(subjs)) for s in range(num_sessions)) <= 1)

    total_campus_seats = sum(h["benches"] * h["seats_per_bench"] for h in EXAM_HALLS)
    for d in range(num_days):
        for s in range(num_sessions):
            total_students_slot = []
            for sec in sections:
                dept_yr = sec.rsplit("-", 1)[0]
                _, start_r, end_r = SECTION_ROLL_INFO[sec]
                strength = end_r - start_r + 1
                for s_idx in range(len(dept_exams[dept_yr])):
                    total_students_slot.append(e[(dept_yr, s_idx, d, s)] * strength)
            model.Add(sum(total_students_slot) <= total_campus_seats)

    start_time = time.time()
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 15.0
    status = solver.Solve(model)

    if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        return None, round((time.time() - start_time) * 1000, 2), solver.StatusName(status), {}

    schedule_rows = []
    seating_plans = {}
    fac_duty_count = {f: 0 for f in all_faculty}

    for d in range(num_days):
        for s in range(num_sessions):
            day_name = exam_days[d]
            sess_name = sessions[s]

            subject_queues = {}
            for sec in sections:
                dept_yr = sec.rsplit("-", 1)[0]
                for s_idx, subj in enumerate(dept_exams[dept_yr]):
                    if solver.Value(e[(dept_yr, s_idx, d, s)]) == 1:
                        prefix, r_start, r_end = SECTION_ROLL_INFO[sec]
                        rolls = [f"{prefix}{r:03d}" for r in range(r_start, r_end + 1)]
                        subject_queues.setdefault(subj, []).append({
                            "section": sec,
                            "subject": subj,
                            "rolls": rolls,
                        })

            if not subject_queues:
                continue

            pools = {}
            for subj, sec_list in subject_queues.items():
                pools[subj] = []
                for item in sec_list:
                    for r in item["rolls"]:
                        pools[subj].append((r, item["section"], subj))

            used_fac_this_slot = set()

            for hall in EXAM_HALLS:
                active_subjs = [sub for sub, q in pools.items() if len(q) > 0]
                if not active_subjs:
                    break

                benches = hall["benches"]
                spb = hall["seats_per_bench"]
                allocations = []

                if spb == 2:
                    active_subjs.sort(key=lambda sub: len(pools[sub]), reverse=True)
                    subj_left = active_subjs[0]
                    take_left = pools[subj_left][:benches]
                    pools[subj_left] = pools[subj_left][benches:]

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

                avail_inv = [f for f in all_faculty if f not in used_fac_this_slot]
                avail_inv.sort(key=lambda f: fac_duty_count[f])
                chosen_inv = avail_inv[0] if avail_inv else "Reserve Staff"
                if avail_inv:
                    used_fac_this_slot.add(chosen_inv)
                    fac_duty_count[chosen_inv] += 1

                seating_df = generate_hall_seating_plan(hall, allocations)
                seating_plans[(day_name, sess_name, hall["name"])] = seating_df

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