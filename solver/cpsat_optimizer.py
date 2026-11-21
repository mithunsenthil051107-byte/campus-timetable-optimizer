# solver/cpsat_optimizer.py
import time
import pandas as pd
from ortools.sat.python import cp_model
from data.sample_campus import (
    DAYS, SECTIONS, ROOMS, COURSES, HOME_ROOMS,
    get_section_periods, get_section_year,
)

# Valid 2-period consecutive lab blocks (Periods 0-1, 2-3, or 4-5 — never spanning across break/lunch!)
LAB_BLOCKS = [(0, 1), (2, 3), (4, 5)]


def intervals_overlap(s1, e1, s2, e2):
    return max(s1, s2) < min(e1, e2)


def solve_cpsat(
    days=DAYS,
    periods=None,
    sections=SECTIONS,
    rooms=ROOMS,
    courses=COURSES,
    home_rooms=HOME_ROOMS,
    unavailable_faculty=None,
):
    model = cp_model.CpModel()
    unavailable_faculty = set(unavailable_faculty or [])
    num_days = len(days)

    course_periods = {c_idx: get_section_periods(c[0]) for c_idx, c in enumerate(courses)}

    # Separate theory courses (1-period slots) and lab courses (2-period consecutive blocks)
    x_lec = {}   # (c_idx, r_idx, d, p) -> BoolVar
    x_lab = {}   # (c_idx, r_idx, d, b_idx) -> BoolVar
    intervals_by_day = {d: [] for d in range(num_days)}  # (start_min, end_min, r_idx, fac, var)

    for c_idx, (sec, subj, fac, r_type, hrs, course_cat) in enumerate(courses):
        p_list = course_periods[c_idx]
        dept = sec.split("-")[0]

        if r_type == "lecture":
            target_room = home_rooms[sec]
            r_idx = next(i for i, r in enumerate(rooms) if r["name"] == target_room)
            for d in range(num_days):
                for p_info in p_list:
                    p = p_info["idx"]
                    if (fac, d, p) in unavailable_faculty:
                        continue
                    var = model.NewBoolVar(f"lec_{c_idx}_{d}_{p}")
                    x_lec[(c_idx, r_idx, d, p)] = var
                    intervals_by_day[d].append((p_info["start"], p_info["end"], r_idx, fac, var))

        elif r_type == "lab":
            # Restrict labs to department's 6 labs (fast & realistic)
            dept_lab_indices = [
                i for i, r in enumerate(rooms)
                if r["type"] == "lab" and (dept in r["name"] or _lab_belongs_to_dept(r["name"], dept))
            ]
            for r_idx in dept_lab_indices:
                for d in range(num_days):
                    for b_idx, (p1, p2) in enumerate(LAB_BLOCKS):
                        if (fac, d, p1) in unavailable_faculty or (fac, d, p2) in unavailable_faculty:
                            continue
                        var = model.NewBoolVar(f"lab_{c_idx}_{r_idx}_{d}_{b_idx}")
                        x_lab[(c_idx, r_idx, d, b_idx)] = var
                        s_min = p_list[p1]["start"]
                        e_min = p_list[p2]["end"]
                        intervals_by_day[d].append((s_min, e_min, r_idx, fac, var))

    # 2. Hard Constraints
    # A: Exact weekly hours per course
    for c_idx, (_, _, _, r_type, hrs, _) in enumerate(courses):
        if r_type == "lecture":
            vars_c = [v for (ci, _, _, _), v in x_lec.items() if ci == c_idx]
            model.Add(sum(vars_c) == hrs)
        else:
            # Each lab block is 2 hours
            vars_c = [v for (ci, _, _, _), v in x_lab.items() if ci == c_idx]
            model.Add(sum(vars_c) * 2 == hrs)

    # B: No student section clash per period (covers both theory & 2-period lab blocks)
    for sec in sections:
        for d in range(num_days):
            for p in range(6):
                lec_vars = [
                    v for (ci, _, di, pi), v in x_lec.items()
                    if di == d and pi == p and courses[ci][0] == sec
                ]
                lab_vars = [
                    v for (ci, _, di, bi), v in x_lab.items()
                    if di == d and p in LAB_BLOCKS[bi] and courses[ci][0] == sec
                ]
                model.Add(sum(lec_vars) + sum(lab_vars) <= 1)

            # C: STRICT HARD CONSTRAINT — At most 1 Lab session per day per class!
            all_day_labs = [
                v for (ci, _, di, _), v in x_lab.items()
                if di == d and courses[ci][0] == sec
            ]
            model.Add(sum(all_day_labs) <= 1)

    # D: Max 1 theory session of the same subject per day
    for c_idx, (_, _, _, r_type, _, _) in enumerate(courses):
        if r_type == "lecture":
            for d in range(num_days):
                day_vars = [v for (ci, _, di, _), v in x_lec.items() if ci == c_idx and di == d]
                model.Add(sum(day_vars) <= 1)

    # E: Clock-Minute Interval Non-Overlap for Faculty & Shared Labs across all 4 Year Shifts
    for d in range(num_days):
        day_items = intervals_by_day[d]

        # Group by Faculty
        fac_map = {}
        for item in day_items:
            fac_map.setdefault(item[3], []).append(item)
        for fac, items in fac_map.items():
            for i in range(len(items)):
                s1, e1, _, _, v1 = items[i]
                for j in range(i + 1, len(items)):
                    s2, e2, _, _, v2 = items[j]
                    if intervals_overlap(s1, e1, s2, e2):
                        model.Add(v1 + v2 <= 1)

        # Group by Shared Lab Room (Home rooms are already unique per section)
        lab_room_map = {}
        for item in day_items:
            if rooms[item[2]]["type"] == "lab":
                lab_room_map.setdefault(item[2], []).append(item)
        for r_idx, items in lab_room_map.items():
            for i in range(len(items)):
                s1, e1, _, _, v1 = items[i]
                for j in range(i + 1, len(items)):
                    s2, e2, _, _, v2 = items[j]
                    if intervals_overlap(s1, e1, s2, e2):
                        model.Add(v1 + v2 <= 1)

    # 3. Solve
    start_time = time.time()
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 20.0
    solver.parameters.num_search_workers = 8
    status = solver.Solve(model)
    solve_ms = round((time.time() - start_time) * 1000, 2)

    if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        schedule = []
        for (c_idx, r_idx, d, p), var in x_lec.items():
            if solver.Value(var) == 1:
                sec, subj, fac, _, _, course_cat = courses[c_idx]
                p_info = course_periods[c_idx][p]
                schedule.append({
                    "Section": sec,
                    "Year": get_section_year(sec),
                    "Day": days[d],
                    "Day_Idx": d,
                    "Period": p_info["label"],
                    "Period_Idx": p,
                    "Start_Min": p_info["start"],
                    "End_Min": p_info["end"],
                    "Subject": subj,
                    "Category": course_cat,
                    "Faculty": fac,
                    "Room": rooms[r_idx]["name"],
                    "Type": "Lecture",
                    "Conflict": False,
                })

        for (c_idx, r_idx, d, b_idx), var in x_lab.items():
            if solver.Value(var) == 1:
                sec, subj, fac, _, _, course_cat = courses[c_idx]
                for p in LAB_BLOCKS[b_idx]:
                    p_info = course_periods[c_idx][p]
                    schedule.append({
                        "Section": sec,
                        "Year": get_section_year(sec),
                        "Day": days[d],
                        "Day_Idx": d,
                        "Period": p_info["label"],
                        "Period_Idx": p,
                        "Start_Min": p_info["start"],
                        "End_Min": p_info["end"],
                        "Subject": subj,
                        "Category": course_cat,
                        "Faculty": fac,
                        "Room": rooms[r_idx]["name"],
                        "Type": "Lab",
                        "Conflict": False,
                    })

        df = pd.DataFrame(schedule).sort_values(["Section", "Day_Idx", "Period_Idx"])
        return df, solve_ms, 0, solver.StatusName(status)
    return None, solve_ms, -1, solver.StatusName(status)


def _lab_belongs_to_dept(lab_name, dept):
    mapping = {
        "AIDS": ("AI", "Data Science", "NLP", "GPU"),
        "CSE":  ("Core Computing", "Systems & OS", "Networks & Compiler", "Software Engg"),
        "IT":   ("Full Stack", "Cloud & DevOps", "Cyber Security", "Mobile App"),
        "ECE":  ("Digital & VLSI", "Microprocessor", "DSP & Communication", "Embedded Robotics"),
    }
    return any(k in lab_name for k in mapping.get(dept, ()))