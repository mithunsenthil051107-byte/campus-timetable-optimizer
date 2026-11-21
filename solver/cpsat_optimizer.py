# solver/cpsat_optimizer.py
import time
import pandas as pd
from ortools.sat.python import cp_model
from data.sample_campus import DAYS, PERIODS, SECTIONS, ROOMS, COURSES, HOME_ROOMS


def solve_cpsat(
    days=DAYS,
    periods=PERIODS,
    sections=SECTIONS,
    rooms=ROOMS,
    courses=COURSES,
    home_rooms=HOME_ROOMS,
    unavailable_faculty=None,
):
    model = cp_model.CpModel()
    unavailable_faculty = set(unavailable_faculty or [])

    num_days = len(days)
    num_periods = len(periods)

    # 1. Decision Variables with Home-Room Binding
    x = {}
    for c_idx, (sec, subj, fac, r_type, hrs) in enumerate(courses):
        for r_idx, room in enumerate(rooms):
            if room["type"] != r_type:
                continue
            # If it's a lecture and section has a designated Home Room, bind strictly to that room!
            if r_type == "lecture" and home_rooms and sec in home_rooms:
                if room["name"] != home_rooms[sec]:
                    continue

            for d in range(num_days):
                for p in range(num_periods):
                    if (fac, d, p) in unavailable_faculty:
                        continue
                    x[(c_idx, r_idx, d, p)] = model.NewBoolVar(f"x_{c_idx}_{r_idx}_{d}_{p}")

    # 2. Hard Constraints
    # A: Exact weekly hours per course
    for c_idx, (_, _, _, _, hrs) in enumerate(courses):
        valid_vars = [
            x[(c_idx, r_idx, d, p)]
            for r_idx in range(len(rooms))
            for d in range(num_days)
            for p in range(num_periods)
            if (c_idx, r_idx, d, p) in x
        ]
        model.Add(sum(valid_vars) == hrs)

    # B: At most 1 class per room per slot
    for r_idx in range(len(rooms)):
        for d in range(num_days):
            for p in range(num_periods):
                room_vars = [
                    x[(c_idx, r_idx, d, p)]
                    for c_idx in range(len(courses))
                    if (c_idx, r_idx, d, p) in x
                ]
                model.Add(sum(room_vars) <= 1)

    # C: No faculty clash
    for fac in set(c[2] for c in courses):
        for d in range(num_days):
            for p in range(num_periods):
                fac_vars = [
                    x[(c_idx, r_idx, d, p)]
                    for c_idx, c in enumerate(courses)
                    if c[2] == fac
                    for r_idx in range(len(rooms))
                    if (c_idx, r_idx, d, p) in x
                ]
                model.Add(sum(fac_vars) <= 1)

    # D: No student section clash (and fills all 30 slots when 30 hrs assigned)
    for sec in sections:
        for d in range(num_days):
            for p in range(num_periods):
                sec_vars = [
                    x[(c_idx, r_idx, d, p)]
                    for c_idx, c in enumerate(courses)
                    if c[0] == sec
                    for r_idx in range(len(rooms))
                    if (c_idx, r_idx, d, p) in x
                ]
                model.Add(sum(sec_vars) <= 1)

    # E: Max 1 session of the same subject per day (spreads 5-hr subjects 1/day across Mon-Fri!)
    for c_idx in range(len(courses)):
        for d in range(num_days):
            day_vars = [
                x[(c_idx, r_idx, d, p)]
                for r_idx in range(len(rooms))
                for p in range(num_periods)
                if (c_idx, r_idx, d, p) in x
            ]
            model.Add(sum(day_vars) <= 1)

    # 3. Soft Objective: Balance faculty workload across morning/afternoon & pack shared labs
    penalty = [var * (p + r_idx) for (c_idx, r_idx, d, p), var in x.items()]
    model.Minimize(sum(penalty))

    # 4. Solve
    start_time = time.time()
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 15.0
    status = solver.Solve(model)
    solve_ms = round((time.time() - start_time) * 1000, 2)

    if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        schedule = []
        for (c_idx, r_idx, d, p), var in x.items():
            if solver.Value(var) == 1:
                sec, subj, fac, r_type, _ = courses[c_idx]
                schedule.append({
                    "Section": sec,
                    "Day": days[d],
                    "Day_Idx": d,
                    "Period": periods[p],
                    "Period_Idx": p,
                    "Subject": subj,
                    "Faculty": fac,
                    "Room": rooms[r_idx]["name"],
                    "Type": "Lab" if r_type == "lab" else "Lecture",
                    "Conflict": False,
                })
        df = pd.DataFrame(schedule).sort_values(["Section", "Day_Idx", "Period_Idx"])
        return df, solve_ms, 0, solver.StatusName(status)
    return None, solve_ms, -1, solver.StatusName(status)