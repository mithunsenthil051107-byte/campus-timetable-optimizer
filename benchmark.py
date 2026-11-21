# benchmark.py
import pandas as pd
from data.sample_campus import DAYS, PERIODS, ROOMS, COURSES
from solver.greedy_baseline import solve_greedy
from solver.cpsat_optimizer import solve_cpsat


def compute_metrics(df, total_rooms, total_slots):
    if df is None or df.empty:
        return 0.0, 0

    total_capacity_slots = total_rooms * total_slots
    utilization = round((len(df) / total_capacity_slots) * 100, 1)

    # Calculate total student idle gaps across all sections and days
    gaps = 0
    for (sec, d), group in df.groupby(["Section", "Day_Idx"]):
        p_list = sorted(group["Period_Idx"].tolist())
        if len(p_list) > 1:
            gaps += (p_list[-1] - p_list[0] + 1) - len(p_list)

    return utilization, gaps


def run_experiments():
    extra_courses_s2 = [
        ("CSE-III-B", "Algorithms", "Dr. P. Sharma", "lecture", 4),
        ("CSE-III-B", "Operating Systems", "Dr. A. Verma", "lecture", 4),
        ("CSE-III-B", "Computer Networks", "Dr. K. Singh", "lecture", 4),
        ("CSE-III-B", "CN Lab", "Dr. R. Mehta", "lab", 2),
    ]

    extra_courses_s3 = [
        ("AIDS-III-A", "Deep Learning", "Dr. K. Singh", "lecture", 4),
        ("AIDS-III-A", "NLP", "Dr. P. Sharma", "lecture", 4),
        ("AIDS-III-A", "Big Data", "Dr. S. Iyer", "lecture", 4),
        ("AIDS-III-A", "DL Lab", "Dr. K. Singh", "lab", 2),
    ]

    extra_courses_s4 = [
        ("CSE-IV-A", "Cloud Computing", "Dr. A. Verma", "lecture", 4),
        ("CSE-IV-A", "Cyber Security", "Dr. R. Mehta", "lecture", 4),
        ("CSE-IV-A", "Compiler Design", "Dr. P. Sharma", "lecture", 4),
        ("CSE-IV-A", "Cloud Lab", "Dr. S. Iyer", "lab", 2),
    ]

    scenarios = [
        (
            "1. Base Load (3 Sections)",
            ["AIDS-II-A", "AIDS-II-B", "CSE-III-A"],
            COURSES,
        ),
        (
            "2. Medium Load (4 Sections)",
            ["AIDS-II-A", "AIDS-II-B", "CSE-III-A", "CSE-III-B"],
            COURSES + extra_courses_s2,
        ),
        (
            "3. High Load (5 Sections)",
            ["AIDS-II-A", "AIDS-II-B", "CSE-III-A", "CSE-III-B", "AIDS-III-A"],
            COURSES + extra_courses_s2 + extra_courses_s3,
        ),
        (
            "4. Bottleneck Stress (6 Sections)",
            ["AIDS-II-A", "AIDS-II-B", "CSE-III-A", "CSE-III-B", "AIDS-III-A", "CSE-IV-A"],
            COURSES + extra_courses_s2 + extra_courses_s3 + extra_courses_s4,
        ),
    ]

    total_slots = len(DAYS) * len(PERIODS)
    results = []

    for name, secs, crs in scenarios:
        # 1. Run Greedy Baseline
        g_df, g_ms, g_clashes, _ = solve_greedy(DAYS, PERIODS, secs, ROOMS, crs)
        g_util, g_gaps = compute_metrics(g_df, len(ROOMS), total_slots)

        # 2. Run Google OR-Tools CP-SAT
        cp_df, cp_ms, cp_clashes, status = solve_cpsat(DAYS, PERIODS, secs, ROOMS, crs)
        cp_util, cp_gaps = compute_metrics(cp_df, len(ROOMS), total_slots)

        results.append({
            "Scenario": name,
            "Algorithm": "Greedy Baseline",
            "Hard_Conflicts": g_clashes,
            "Student_Idle_Gaps": g_gaps,
            "Room_Utilization_%": g_util,
            "Solve_Time_ms": g_ms,
        })
        results.append({
            "Scenario": name,
            "Algorithm": "Google OR-Tools (CP-SAT)",
            "Hard_Conflicts": cp_clashes,
            "Student_Idle_Gaps": cp_gaps,
            "Room_Utilization_%": cp_util,
            "Solve_Time_ms": cp_ms,
        })

    res_df = pd.DataFrame(results)
    res_df.to_csv("benchmark_results.csv", index=False)
    print("\n=== RESEARCH BENCHMARK RESULTS ===")
    print(res_df.to_string(index=False))


if __name__ == "__main__":
    run_experiments()