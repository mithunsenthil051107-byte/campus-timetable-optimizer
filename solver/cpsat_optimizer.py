# solver/cpsat_optimizer.py
import time
import pandas as pd
from ortools.sat.python import cp_model
from data.sample_campus import (
    DAYS, SECTIONS, ROOMS, COURSES, HOME_ROOMS,
    get_section_periods, get_section_year,
)

LAB_BLOCKS = [(0, 1), (2, 3), (4, 5)]


def intervals_overlap(s1, e1, s2, e2):
    return max(s1, s2) < min(e1, e2)


def _lab_belongs_to_dept(lab_name, dept):
    mapping = {
        "AIDS": ("AI", "Data Science", "NLP", "GPU"),
        "CSE":  ("Core Computing", "Systems & OS", "Networks & Compiler", "Software Engg"),
        "IT":   ("Full Stack", "Cloud & DevOps", "Cyber Security", "Mobile App"),
        "ECE":  ("Digital & VLSI", "Microprocessor", "DSP & Communication", "Embedded Robotics"),
    }
    return any(k in lab_name for k in mapping.get(dept, ()))


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

    x_lec = {}
    x_lab = {}
    intervals_by_day = {d: [] for d in range(num_days)}

    # Index courses by section for fast O(N) constraint building
    sec_lec_courses = {s: [] for s in sections}
    sec_lab_courses = {s: [] for s in sections}

    for c_idx, (sec, subj, fac, r_type, hrs, course_cat) in enumerate(courses):
        p_list = course_periods[c_idx]
        dept = sec.split("-")[0]

        if r_type == "lecture":
            sec_lec_courses[sec].append(c_idx)
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
            sec_lab_courses[sec].append(c_idx)
            dept_lab_indices = [
                i for i, r in enumerate(rooms)
                if r["type"] == "lab" and _lab_belongs_to_dept(r["name"], dept)
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

    # A: Exact weekly hours per course
    for c_idx, (sec, _, _, r_type, hrs, _) in enumerate(courses):
        if r_type == "lecture":
            target_room = home_rooms[sec]
            r_idx = next(i for i, r in enumerate(rooms) if r["name"] == target_room)
            vars_c = [x_lec[(c_idx, r_idx, d, p)] for d in range(num_days) for p in range(6) if (c_idx, r_idx, d, p) in x_lec]
            model.Add(sum(vars_c) == hrs)
        else:
            dept = sec.split("-")[0]
            dept_lab_indices = [i for i, r in enumerate(rooms) if r["type"] == "lab" and _lab_belongs_to_dept(r["name"], dept)]
            vars_c = [x_lab[(c_idx, ri, d, bi)] for ri in dept_lab_indices for d in range(num_days) for bi in range(3) if (c_idx, ri, d, bi) in x_lab]
            model.Add(sum(vars_c) * 2 == hrs)

    # B & C: Section period non-overlap + STRICT Max 1 Lab per day per class
    for sec in sections:
        dept = sec.split("-")[0]
        target_room = home_rooms[sec]
        r_lec = next(i for i, r in enumerate(rooms) if r["name"] == target_room)
        dept_lab_indices = [i for i, r in enumerate(rooms) if r["type"] == "lab" and _lab_belongs_to_dept(r["name"], dept)]

        for d in range(num_days):
            for p in range(6):
                b_idx = p // 2
                lec_vars = [x_lec[(ci, r_lec, d, p)] for ci in sec_lec_courses[sec] if (ci, r_lec, d, p) in x_lec]
                lab_vars = [x_lab[(ci, ri, d, b_idx)] for ci in sec_lab_courses[sec] for ri in dept_lab_indices if (ci, ri, d, b_idx) in x_lab]
                model.Add(sum(lec_vars) + sum(lab_vars) <= 1)

            # Max 1 Lab session per day per class
            all_day_labs = [
                x_lab[(ci, ri, d, bi)]
                for ci in sec_lab_courses[sec]
                for ri in dept_lab_indices
                for bi in range(3)
                if (ci, ri, d, bi) in x_lab
            ]
            model.Add(sum(all_day_labs) <= 1)

    # D: Max 1 theory session of the same subject per day
    for sec in sections:
        target_room = home_rooms[sec]
        r_lec = next(i for i, r in enumerate(rooms) if r["name"] == target_room)
        for ci in sec_lec_courses[sec]:
            for d in range(num_days):
                day_vars = [x_lec[(ci, r_lec, d, p)] for p in range(6) if (ci, r_lec, d, p) in x_lec]
                model.Add(sum(day_vars) <= 1)

    # E: Clock-Minute Interval Non-Overlap for Faculty & Shared Labs
    for d in range(num_days):
        day_items = intervals_by_day[d]

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

    # Solve
    start_time = time.time()
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 30.0
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