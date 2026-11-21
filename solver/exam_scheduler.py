# solver/exam_scheduler.py
import time
import pandas as pd
from ortools.sat.python import cp_model
from data.sample_campus import DAYS, ROOMS, CURRICULUM, SECTION_STAFF


def solve_exam_schedule(
    exam_days=None,
    sessions=("Forenoon (09:30-12:30)", "Afternoon (01:30-04:30)"),
    unavailable_faculty=None,  # set of faculty names absent during exam week
):
    exam_days = exam_days or ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
    unavailable_faculty = set(unavailable_faculty or [])

    model = cp_model.CpModel()
    num_days = len(exam_days)
    num_sessions = len(sessions)

    # Extract theory subjects per department (exams are for theory subjects)
    dept_exams = {}
    for dept, subjects in CURRICULUM.items():
        dept_exams[dept] = [subj for subj, r_type, _ in subjects if r_type == "lecture"]

    sections = list(SECTION_STAFF.keys())
    exam_halls = [r["name"] for r in ROOMS]
    all_faculty = sorted(list({fac for m in SECTION_STAFF.values() for fac in m.values()} - unavailable_faculty))

    # 1. Decision Variables
    # e[(dept, subj_idx, d, s)] = 1 if department writes subject exam on day d, session s
    e = {}
    for dept, subjs in dept_exams.items():
        for s_idx in range(len(subjs)):
            for d in range(num_days):
                for s in range(num_sessions):
                    e[(dept, s_idx, d, s)] = model.NewBoolVar(f"exam_{dept}_{s_idx}_{d}_{s}")

    # inv[(sec, fac, d, s)] = 1 if faculty `fac` invigilates section `sec`'s exam hall on day d, session s
    inv = {}
    for sec in sections:
        for fac in all_faculty:
            for d in range(num_days):
                for s in range(num_sessions):
                    inv[(sec, fac, d, s)] = model.NewBoolVar(f"inv_{sec}_{fac}_{d}_{s}")

    # 2. Exam Scheduling Constraints
    # A: Every theory subject is scheduled exactly once
    for dept, subjs in dept_exams.items():
        for s_idx in range(len(subjs)):
            model.Add(sum(e[(dept, s_idx, d, s)] for d in range(num_days) for s in range(num_sessions)) == 1)

    # B: Max 1 exam per day per department (gives students preparation time)
    for dept, subjs in dept_exams.items():
        for d in range(num_days):
            model.Add(sum(e[(dept, s_idx, d, s)] for s_idx in range(len(subjs)) for s in range(num_sessions)) <= 1)

    # C: Total exams in any (day, session) cannot exceed available exam halls
    for d in range(num_days):
        for s in range(num_sessions):
            active_halls = []
            for sec in sections:
                dept = sec.rsplit("-", 1)[0]
                for s_idx in range(len(dept_exams[dept])):
                    active_halls.append(e[(dept, s_idx, d, s)])
            model.Add(sum(active_halls) <= len(exam_halls))

    # 3. Invigilation Duty Constraints
    # D: If section `sec` has an exam on (d, s), assign exactly 1 invigilator; otherwise 0
    for sec in sections:
        dept = sec.rsplit("-", 1)[0]
        for d in range(num_days):
            for s in range(num_sessions):
                has_exam = sum(e[(dept, s_idx, d, s)] for s_idx in range(len(dept_exams[dept])))
                model.Add(sum(inv[(sec, fac, d, s)] for fac in all_faculty) == has_exam)

    # E: A faculty member can invigilate at most 1 hall per session & max 1 duty per day
    for fac in all_faculty:
        for d in range(num_days):
            model.Add(sum(inv[(sec, fac, d, s)] for sec in sections for s in range(num_sessions)) <= 1)

    # 4. Objective: Balance total invigilation duties fairly across all available faculty
    max_duties = model.NewIntVar(0, num_days, "max_duties")
    min_duties = model.NewIntVar(0, num_days, "min_duties")
    for fac in all_faculty:
        total_fac_duties = sum(inv[(sec, fac, d, s)] for sec in sections for d in range(num_days) for s in range(num_sessions))
        model.Add(total_fac_duties <= max_duties)
        model.Add(total_fac_duties >= min_duties)

    # Prefer Forenoon exams slightly & minimize duty inequality (max_duties - min_duties)
    session_pen = [e[(dept, s_idx, d, s)] * s for (dept, s_idx, d, s) in e]
    model.Minimize((max_duties - min_duties) * 10 + sum(session_pen))

    # 5. Solve
    start_time = time.time()
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 10.0
    status = solver.Solve(model)
    solve_ms = round((time.time() - start_time) * 1000, 2)

    if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        rows = []
        for d in range(num_days):
            for s in range(num_sessions):
                hall_idx = 0
                for sec in sections:
                    dept = sec.rsplit("-", 1)[0]
                    for s_idx, subj in enumerate(dept_exams[dept]):
                        if solver.Value(e[(dept, s_idx, d, s)]) == 1:
                            assigned_inv = [fac for fac in all_faculty if solver.Value(inv[(sec, fac, d, s)]) == 1]
                            rows.append({
                                "Day_Idx": d,
                                "Day": exam_days[d],
                                "Session": sessions[s],
                                "Department": dept,
                                "Section": sec,
                                "Exam_Subject": subj,
                                "Exam_Hall": exam_halls[hall_idx % len(exam_halls)],
                                "Invigilator": assigned_inv[0] if assigned_inv else "Unassigned",
                            })
                            hall_idx += 1
        return pd.DataFrame(rows).sort_values(["Day_Idx", "Session", "Section"]), solve_ms, solver.StatusName(status)
    return None, solve_ms, solver.StatusName(status)
