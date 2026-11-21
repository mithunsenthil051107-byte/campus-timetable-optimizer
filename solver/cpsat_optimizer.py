# solver/cpsat_optimizer.py
import time
import pandas as pd
from ortools.sat.python import cp_model
from data.sample_campus import DAYS, PERIODS, SECTIONS, ROOMS, COURSES


def solve_cpsat(
    days=DAYS,
    periods=PERIODS,
    sections=SECTIONS,
    rooms=ROOMS,
    courses=COURSES,
    unavailable_faculty=None,
):
    model = cp_model.CpModel()
    unavailable_faculty = set(unavailable_faculty or [])

    num_days = len(days)
    num_periods = len(periods)

    # 1. Decision Variables
    x = {}
    for c_idx, (sec, subj, fac, r_type, hrs) in enumerate(courses):
        for r_idx, room in enumerate(rooms):
            if room["type"] != r_type:
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

    # D: No student section clash + Exact Daily Span Tracking
    gap_penalties = []
    for sec in sections:
        for d in range(num_days):
            day_active = []
            for p in range(num_periods):
                sec_vars = [
                    x[(c_idx, r_idx, d, p)]
                    for c_idx, c in enumerate(courses)
                    if c[0] == sec
                    for r_idx in range(len(rooms))
                    if (c_idx, r_idx, d, p) in x
                ]
                model.Add(sum(sec_vars) <= 1)
                act = model.NewBoolVar(f"act_{sec}_{d}_{p}")
                model.Add(sum(sec_vars) == act)
                day_active.append(act)

            # Exact Idle Gap Calculation: (last_busy - first_busy + 1) - total_busy
            has_classes = model.NewBoolVar(f"has_{sec}_{d}")
            model.Add(sum(day_active) >= 1).OnlyEnforceIf(has_classes)
            model.Add(sum(day_active) == 0).OnlyEnforceIf(has_classes.Not())

            first_p = model.NewIntVar(0, num_periods - 1, f"first_{sec}_{d}")
            last_p = model.NewIntVar(0, num_periods - 1, f"last_{sec}_{d}")
            gaps = model.NewIntVar(0, num_periods, f"gaps_{sec}_{d}")

            for p in range(num_periods):
                model.Add(first_p <= p).OnlyEnforceIf(day_active[p])
                model.Add(last_p >= p).OnlyEnforceIf(day_active[p])

            model.Add(gaps == last_p - first_p + 1 - sum(day_active)).OnlyEnforceIf(has_classes)
            model.Add(gaps == 0).OnlyEnforceIf(has_classes.Not())
            gap_penalties.append(gaps * 20)

    # E: Max 1 session of the same subject per day
    for c_idx in range(len(courses)):
        for d in range(num_days):
            day_vars = [
                x[(c_idx, r_idx, d, p)]
                for r_idx in range(len(rooms))
                for p in range(num_periods)
                if (c_idx, r_idx, d, p) in x
            ]
            model.Add(sum(day_vars) <= 1)

    # 3. Objective: Zero idle gaps + pack into morning periods & primary rooms
    slot_penalties = [var * (p + r_idx) for (c_idx, r_idx, d, p), var in x.items()]
    model.Minimize(sum(gap_penalties) + sum(slot_penalties))

    # 4. Solve
    start_time = time.time()
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 10.0
    status = solver.Solve(model)
    solve_ms = round((time.time() - start_time) * 1000, 2)

    if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        schedule = []
        for (c_idx, r_idx, d, p), var in x.items():
            if solver.Value(var) == 1:
                sec, subj, fac, _, _ = courses[c_idx]
                schedule.append({
                    "Section": sec,
                    "Day": days[d],
                    "Day_Idx": d,
                    "Period": periods[p],
                    "Period_Idx": p,
                    "Subject": subj,
                    "Faculty": fac,
                    "Room": rooms[r_idx]["name"],
                    "Conflict": False,
                })
        df = pd.DataFrame(schedule).sort_values(["Section", "Day_Idx", "Period_Idx"])
        return df, solve_ms, 0, solver.StatusName(status)
    return None, solve_ms, -1, solver.StatusName(status)