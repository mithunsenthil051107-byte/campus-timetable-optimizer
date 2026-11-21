# app.py
import streamlit as st
import pandas as pd
import plotly.express as px
from data.sample_campus import (
    DAYS,
    DEPARTMENTS,
    YEARS,
    SECTIONS,
    ROOMS,
    COURSES,
    HOME_ROOMS,
    YEAR_SCHEDULES,
    get_section_year,
    get_section_periods,
)
from solver.cpsat_optimizer import solve_cpsat, intervals_overlap
from solver.greedy_baseline import solve_greedy
from solver.exam_scheduler import solve_exam_schedule

st.set_page_config(
    page_title="Campus Timetable & Exam Optimizer | Google OR-Tools",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- CUSTOM SaaS CSS STYLING ---
st.markdown(
    """
    <style>
    .stApp { background-color: #f8fafc; }
    div[data-testid="stMetric"] {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        padding: 16px 20px;
        border-radius: 12px;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
    }
    .tt-table { width: 100%; border-collapse: separate; border-spacing: 8px; table-layout: fixed; }
    .tt-table th {
        background-color: #ffffff; color: #334155; font-weight: 700; font-size: 0.9rem;
        padding: 12px 8px; border-radius: 10px; border: 1px solid #e2e8f0; text-align: center;
    }
    .tt-time {
        background-color: #ffffff; color: #475569; font-weight: 600; font-size: 0.82rem;
        padding: 12px 8px; border-radius: 10px; border: 1px solid #e2e8f0; text-align: center;
    }
    .tt-cell {
        background-color: #ffffff; border-radius: 10px; padding: 10px 12px;
        border: 1px solid #e2e8f0; vertical-align: top; height: 98px;
        box-shadow: 0 1px 2px rgba(0,0,0,0.03);
    }
    .tt-free {
        background-color: #f1f5f9; border: 1px dashed #cbd5e1; border-radius: 10px;
        color: #94a3b8; font-size: 0.8rem; text-align: center; vertical-align: middle; height: 98px;
    }
    .tt-subj { font-weight: 700; font-size: 0.86rem; color: #0f172a; margin-bottom: 4px; line-height: 1.25; }
    .tt-meta { font-size: 0.75rem; color: #475569; line-height: 1.35; }
    .badge-lab { display: inline-block; background-color: #fef3c7; color: #b45309; font-size: 0.66rem; font-weight: 700; padding: 1px 6px; border-radius: 4px; margin-bottom: 4px; }
    .badge-tcl { display: inline-block; background-color: #f3e8ff; color: #7e22ce; font-size: 0.66rem; font-weight: 700; padding: 1px 6px; border-radius: 4px; margin-bottom: 4px; }
    .badge-lec { display: inline-block; background-color: #e0e7ff; color: #4338ca; font-size: 0.66rem; font-weight: 700; padding: 1px 6px; border-radius: 4px; margin-bottom: 4px; }
    .badge-sub { display: inline-block; background-color: #dcfce7; color: #15803d; font-size: 0.66rem; font-weight: 700; padding: 1px 6px; border-radius: 4px; margin-bottom: 4px; }
    .badge-clash { display: inline-block; background-color: #fee2e2; color: #b91c1c; font-size: 0.66rem; font-weight: 700; padding: 1px 6px; border-radius: 4px; margin-bottom: 4px; }
    </style>
    """,
    unsafe_allow_html=True,
)

PALETTE = [
    ("#3b82f6", "#eff6ff"), ("#8b5cf6", "#f5f3ff"), ("#10b981", "#ecfdf5"),
    ("#f59e0b", "#fffbeb"), ("#ec4899", "#fdf2f8"), ("#06b6d4", "#ecfeff"), ("#6366f1", "#eef2ff"),
]
all_subjects = sorted(list(set(c[1] for c in COURSES)))
SUBJ_COLORS = {subj: PALETTE[i % len(PALETTE)] for i, subj in enumerate(all_subjects)}
all_faculty = sorted(list(set(c[2] for c in COURSES)))


@st.cache_data(show_spinner="Optimizing 80 sections (2,400 periods) with Google OR-Tools CP-SAT...")
def get_cached_cpsat(unavail_tuple):
    return solve_cpsat(unavailable_faculty=list(unavail_tuple))


@st.cache_data(show_spinner="Generating End-Semester Exam & Anti-Malpractice Bench Plan for 4,800 students...")
def get_cached_exam(unavail_tuple):
    return solve_exam_schedule(unavailable_faculty=list(unavail_tuple))


def assign_substitutes(df, absent_fac_list, leave_days):
    """Interval-overlap-aware, workload-capped & department-matched substitute rotation."""
    df = df.copy()
    df["Substitute"] = None
    if not absent_fac_list or not leave_days:
        return df, []

    fac_depts = {}
    for sec, _, fac, _, _, _ in COURSES:
        dept = sec.split("-")[0]
        fac_depts.setdefault(fac, set()).add(dept)

    daily_load = {}
    for _, r in df.iterrows():
        key = (r["Day"], r["Faculty"])
        daily_load[key] = daily_load.get(key, 0) + 1
    sub_count = {f: 0 for f in all_faculty}
    MAX_DAILY_CLASSES = 5

    sub_logs = []
    for d_name in leave_days:
        day_df = df[df["Day"] == d_name].sort_values("Start_Min")
        affected_rows = day_df[day_df["Faculty"].isin(absent_fac_list)]

        for idx, row in affected_rows.iterrows():
            s_req, e_req = row["Start_Min"], row["End_Min"]
            target_dept = row["Section"].split("-")[0]

            busy_overlapping = set(absent_fac_list)
            for _, other in day_df.iterrows():
                if intervals_overlap(s_req, e_req, other["Start_Min"], other["End_Min"]):
                    busy_overlapping.add(other["Faculty"])
                    if pd.notna(df.at[other.name, "Substitute"]):
                        busy_overlapping.add(df.at[other.name, "Substitute"])

            candidates = [
                f for f in all_faculty
                if f not in busy_overlapping and daily_load.get((d_name, f), 0) < MAX_DAILY_CLASSES
            ]

            if candidates:
                candidates.sort(
                    key=lambda f: (
                        0 if target_dept in fac_depts.get(f, set()) else 1,
                        sub_count[f],
                        daily_load.get((d_name, f), 0),
                    )
                )
                chosen = candidates[0]
                df.at[idx, "Substitute"] = chosen
                daily_load[(d_name, chosen)] = daily_load.get((d_name, chosen), 0) + 1
                sub_count[chosen] += 1

                sub_logs.append({
                    "Day": d_name,
                    "Shift_Timing": f"{row['Period']} (Year {row['Year']})",
                    "Section": row["Section"],
                    "Subject": row["Subject"],
                    "Absent_Faculty": row["Faculty"],
                    "Assigned_Substitute": chosen,
                    "Teacher_Daily_Total": f"{daily_load[(d_name, chosen)]}/{MAX_DAILY_CLASSES} hrs",
                })
            else:
                df.at[idx, "Substitute"] = "⚠️ No Eligible Staff (Self-Study)"
                sub_logs.append({
                    "Day": d_name,
                    "Shift_Timing": f"{row['Period']} (Year {row['Year']})",
                    "Section": row["Section"],
                    "Subject": row["Subject"],
                    "Absent_Faculty": row["Faculty"],
                    "Assigned_Substitute": "No Eligible Staff (Self-Study)",
                    "Teacher_Daily_Total": "-",
                })
    return df, sub_logs


# --- SIDEBAR CONTROLS ---
with st.sidebar:
    st.markdown("## 🗓️ Schedule Mode")
    schedule_mode = st.radio(
        "Select Academic Mode",
        ["Regular Classes (Weekly)", "Exam & Invigilation Schedule"],
    )

    st.divider()
    st.markdown("## 🎓 Select Academic Year & Shift")
    selected_sidebar_year = st.selectbox(
        "Choose Year (I – IV)",
        YEARS,
        format_func=lambda y: f"Year {y} — {YEAR_SCHEDULES[y]['label'].split('(')[1].split('|')[0].strip()}",
    )
    st.info(f"⏰ **{YEAR_SCHEDULES[selected_sidebar_year]['label']}**")

    st.divider()
    st.markdown("## 🩺 Multi-Faculty Leave Simulator")
    absent_fac_list = st.multiselect("Absent Faculty (Multi-Select)", all_faculty)
    leave_days = st.multiselect("Leave Day(s)", DAYS, default=["Mon"] if absent_fac_list else [])

    if schedule_mode == "Regular Classes (Weekly)":
        leave_strategy = st.radio(
            "Handling Strategy",
            ["Auto-Assign Free Substitutes (Keep Grid Fixed)", "Re-Optimize Entire Timetable (CP-SAT)"],
        )
        st.divider()
        algorithm_choice = st.radio(
            "Scheduling Engine",
            ["Google OR-Tools (CP-SAT)", "Greedy Heuristic Baseline"],
        )

# ==============================================================================
# MODE 1: EXAM & INVIGILATION SCHEDULER (80 SECTIONS • 4,800 STUDENTS)
# ==============================================================================
if schedule_mode == "Exam & Invigilation Schedule":
    st.markdown("### 📝 End-Semester Exam & Anti-Malpractice Seating Optimizer (80 Sections • 4,800 Students)")
    st.caption("Cross-Department Long-Bench Pairing (2-Seater) • Single-Desk Isolation (1-Seater) • Roll-Number Allocation")

    exam_df, exam_ms, exam_status, seating_plans = get_cached_exam(tuple(sorted(absent_fac_list)))

    if exam_df is None:
        st.error("No feasible exam schedule found! Try reducing absent faculty count.")
    else:
        e1, e2, e3, e4 = st.columns(4)
        e1.metric("Solver Status", exam_status)
        e2.metric("Solve Time", f"{exam_ms} ms")
        e3.metric("Exam Hall Sessions", len(exam_df))
        e4.metric("Total Students Seated", "4,800 (80 Secs)")

        st.markdown("<br>", unsafe_allow_html=True)
        ex_view = st.radio(
            "View Exam Plan By",
            ["🪑 Bench-by-Bench Roll Number Seating", "🏫 Master Hall & Roll Allocation", "📋 Invigilator Duty Roster"],
            horizontal=True,
        )

        if ex_view == "🪑 Bench-by-Bench Roll Number Seating":
            st.info(
                "**Anti-Malpractice Rule Active:** In **Long Bench (2-Seater)** halls, Left Seat (A) and Right Seat (B) are paired from "
                "**different departments/subjects**. In **Small Bench (1-Seater)** halls, 1 student is seated per desk."
            )
            c_day, c_sess, c_hall = st.columns(3)
            avail_days = list(dict.fromkeys(exam_df["Day"].tolist()))
            sel_day = c_day.selectbox("Select Exam Day", avail_days)

            day_filtered = exam_df[exam_df["Day"] == sel_day]
            avail_sess = list(dict.fromkeys(day_filtered["Session"].tolist()))
            sel_sess = c_sess.selectbox("Select Session", avail_sess)

            sess_filtered = day_filtered[day_filtered["Session"] == sel_sess]
            avail_halls = sess_filtered["Exam_Hall"].tolist()
            sel_hall = c_hall.selectbox("Select Exam Hall", avail_halls)

            hall_row = sess_filtered[sess_filtered["Exam_Hall"] == sel_hall].iloc[0]
            st.markdown(
                f"**Hall:** `{sel_hall}` | **Layout:** `{hall_row['Bench_Layout']}` | "
                f"**Occupancy:** `{hall_row['Occupancy']}` | **Invigilator:** `{hall_row['Invigilator']}`"
            )

            plan_df = seating_plans.get((sel_day, sel_sess, sel_hall))
            if plan_df is not None:
                st.dataframe(plan_df, use_container_width=True, hide_index=True, height=520)
                csv_bench = plan_df.to_csv(index=False).encode("utf-8")
                st.download_button(
                    f"⬇️ Download {sel_hall} Bench Door-Sheet (CSV)",
                    csv_bench,
                    f"seating_{sel_day}_{sel_hall.replace(' ', '_')}.csv",
                    "text/csv",
                )
        elif ex_view == "📋 Invigilator Duty Roster":
            duty_counts = exam_df["Invigilator"].value_counts().reset_index()
            duty_counts.columns = ["Faculty", "Total_Invigilation_Duties"]
            c_left, c_right = st.columns([1, 2])
            with c_left:
                st.subheader("Fairness Duty Count")
                st.dataframe(duty_counts, use_container_width=True, hide_index=True)
            with c_right:
                st.subheader("Detailed Duty Allocation")
                st.dataframe(
                    exam_df[["Day", "Session", "Exam_Hall", "Bench_Layout", "Occupancy", "Invigilator"]],
                    use_container_width=True,
                    hide_index=True,
                )
        else:
            st.dataframe(exam_df.drop(columns=["Day_Idx"]), use_container_width=True, hide_index=True)

        csv_exam = exam_df.drop(columns=["Day_Idx"]).to_csv(index=False).encode("utf-8")
        st.download_button("⬇️ Download Master Exam & Roll Allocation (CSV)", csv_exam, "master_exam_schedule.csv", "text/csv")

# ==============================================================================
# MODE 2: REGULAR CLASSES (80 SECTIONS • 4 YEARS • THEORY-CUM-LAB • MAX 1 LAB/DAY)
# ==============================================================================
else:
    unavailable_tuples = []
    if absent_fac_list and leave_days and leave_strategy == "Re-Optimize Entire Timetable (CP-SAT)":
        for fac in absent_fac_list:
            for d_name in leave_days:
                d_idx = DAYS.index(d_name)
                for p_idx in range(6):
                    unavailable_tuples.append((fac, d_idx, p_idx))

    if algorithm_choice == "Google OR-Tools (CP-SAT)":
        df, solve_ms, clashes, status = get_cached_cpsat(tuple(sorted(unavailable_tuples)))
    else:
        greedy_courses = [(c[0], c[1], c[2], c[3], c[4]) for c in COURSES]
        df, solve_ms, clashes, _ = solve_greedy(courses=greedy_courses, sections=SECTIONS, rooms=ROOMS)
        status = "GREEDY_BASELINE"

    sub_logs = []
    if df is not None and absent_fac_list and leave_days and leave_strategy == "Auto-Assign Free Substitutes (Keep Grid Fixed)":
        df, sub_logs = assign_substitutes(df, absent_fac_list, leave_days)

    hdr_left, hdr_right = st.columns([3, 1])
    with hdr_left:
        st.markdown("### 🎓 University Resource & Staggered-Shift Timetable Optimizer")
        st.caption("4 Years (I–IV) • 4 Departments (20 Sections/Dept) • Theory-cum-Lab • Max 1 Lab/Day Constraint")
    with hdr_right:
        if df is not None:
            csv_data = df.drop(columns=["Day_Idx", "Period_Idx", "Start_Min", "End_Min"], errors="ignore").to_csv(index=False).encode("utf-8")
            st.download_button("⬇️ Export Master Schedule (CSV)", csv_data, "university_80_sections_timetable.csv", "text/csv", use_container_width=True)

    tab1, tab2, tab3 = st.tabs(["📅 Timetable Builder", "📊 Room & Workload Analytics", "🔬 Research Benchmark"])

    with tab1:
        if df is None:
            st.error("No feasible schedule exists under these constraints! Switch Handling Strategy to Auto-Assign Free Substitutes.")
        else:
            lab_rows = df[df["Type"] == "Lab"]
            max_labs_per_day = int(lab_rows.groupby(["Section", "Day"]).size().max() // 2) if not lab_rows.empty else 0

            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Solver Status", status)
            c2.metric("Solve Latency", f"{solve_ms} ms")
            c3.metric("Max Labs / Day / Class", f"{max_labs_per_day} (Limit: 1)", delta="Strictly Enforced")
            c4.metric("Scheduled Periods", f"{len(df):,} (80 Secs)")

            if sub_logs:
                with st.expander(f"🔄 Substitutions Assigned ({len(sub_logs)} classes covered without time overlap)", expanded=True):
                    st.dataframe(pd.DataFrame(sub_logs), use_container_width=True, hide_index=True)

            st.markdown("<br>", unsafe_allow_html=True)
            v1, v2 = st.columns([2, 2])
            view_mode = v1.radio(
                "View Mode",
                ["Student Section", "Department Master View", "Faculty Schedule", "Classroom / Lab View"],
                horizontal=True,
            )

            if view_mode == "Department Master View":
                f_dept, f_yr = v2.columns(2)
                sel_dept = f_dept.selectbox("Filter Department", DEPARTMENTS)
                sel_yr = f_yr.selectbox("Filter Academic Year", YEARS, index=YEARS.index(selected_sidebar_year))
                target_secs = [s for s in SECTIONS if s.startswith(f"{sel_dept}-{sel_yr}-")]
                sub_df = df[df["Section"].isin(target_secs)]

                st.subheader(f"🏫 {sel_dept} Year-{sel_yr} Master Schedule (5 Sections • {YEAR_SCHEDULES[sel_yr]['label']})")
                pivot_master = (
                    sub_df.pivot_table(
                        index=["Day_Idx", "Day", "Period_Idx", "Period"],
                        columns="Section",
                        values="Subject",
                        aggfunc=lambda s: " / ".join(s),
                    )
                    .reset_index()
                    .sort_values(["Day_Idx", "Period_Idx"])
                    .drop(columns=["Day_Idx", "Period_Idx"])
                )
                st.dataframe(pivot_master, use_container_width=True, hide_index=True, height=620)
            else:
                if view_mode == "Student Section":
                    f_d, f_y, f_s = v2.columns(3)
                    sel_d = f_d.selectbox("Dept", DEPARTMENTS)
                    sel_y = f_y.selectbox("Year", YEARS, index=YEARS.index(selected_sidebar_year))
                    sec_opts = [s for s in SECTIONS if s.startswith(f"{sel_d}-{sel_y}-")]
                    selected_entity = f_s.selectbox("Section", sec_opts)

                    filtered_df = df[df["Section"] == selected_entity]
                    yr = get_section_year(selected_entity)
                    sec_periods = get_section_periods(selected_entity)
                    st.info(
                        f"🏠 **Home Room:** `{HOME_ROOMS[selected_entity]}` | "
                        f"⏰ **{YEAR_SCHEDULES[yr]['label']}** | **{len(filtered_df)}/30 Periods • Max 1 Lab/Day**"
                    )
                    row_slots = [(p["idx"], p["label"]) for p in sec_periods]

                elif view_mode == "Faculty Schedule":
                    selected_entity = v2.selectbox("Select Faculty Member (140 Staff)", all_faculty)
                    filtered_df = df[(df["Faculty"] == selected_entity) | (df["Substitute"] == selected_entity)]
                    unique_times = (
                        filtered_df[["Period_Idx", "Period", "Start_Min"]]
                        .drop_duplicates()
                        .sort_values("Start_Min")
                    )
                    row_slots = list(zip(unique_times["Period_Idx"], unique_times["Period"]))
                    if not row_slots:
                        row_slots = [(p["idx"], p["label"]) for p in YEAR_SCHEDULES[selected_sidebar_year]["periods"]]

                else:
                    room_names = [r["name"] for r in ROOMS]
                    selected_entity = v2.selectbox("Select Classroom / Lab (104 Rooms)", room_names)
                    filtered_df = df[df["Room"] == selected_entity]
                    unique_times = (
                        filtered_df[["Period_Idx", "Period", "Start_Min"]]
                        .drop_duplicates()
                        .sort_values("Start_Min")
                    )
                    row_slots = list(zip(unique_times["Period_Idx"], unique_times["Period"]))
                    if not row_slots:
                        row_slots = [(p["idx"], p["label"]) for p in YEAR_SCHEDULES[selected_sidebar_year]["periods"]]

                html = ['<table class="tt-table"><thead><tr><th style="width:12%;">Shift Timing</th>']
                for d in DAYS:
                    html.append(f"<th>{d}</th>")
                html.append("</tr></thead><tbody>")

                for p_idx, p_label in row_slots:
                    html.append(f'<tr><td class="tt-time"><b>Period {p_idx + 1}</b><br>{p_label}</td>')
                    for d in DAYS:
                        matches = filtered_df[(filtered_df["Day"] == d) & (filtered_df["Period"] == p_label)]
                        if matches.empty:
                            html.append('<td class="tt-free">Free / Other Shift</td>')
                        else:
                            row = matches.iloc[0]
                            subj = row["Subject"]
                            border_col, bg_col = SUBJ_COLORS.get(subj, ("#3b82f6", "#eff6ff"))
                            sub_teacher = row.get("Substitute")

                            if pd.notna(sub_teacher) and sub_teacher:
                                badge = '<span class="badge-sub">🔄 SUBSTITUTED</span>'
                                border_col, bg_col = "#16a34a", "#f0fdf4"
                            elif row.get("Category") == "Theory-cum-Lab":
                                if row["Type"] == "Lab":
                                    badge = '<span class="badge-tcl">🔗 TCL PRACTICAL</span>'
                                else:
                                    badge = '<span class="badge-tcl">🔗 TCL THEORY</span>'
                            elif row["Type"] == "Lab":
                                badge = '<span class="badge-lab">LAB SESSION</span>'
                            else:
                                badge = '<span class="badge-lec">HOME LECTURE</span>'

                            fac_display = f"🔄 {sub_teacher} (Sub)" if (pd.notna(sub_teacher) and sub_teacher) else f"👤 {row['Faculty']}"
                            if view_mode == "Student Section":
                                sub_line = f"{fac_display}<br>🏫 {row['Room']}"
                            elif view_mode == "Faculty Schedule":
                                sub_line = f"🎓 {row['Section']} (Yr {row['Year']})<br>🏫 {row['Room']}"
                            else:
                                sub_line = f"🎓 {row['Section']} (Yr {row['Year']})<br>{fac_display}"

                            html.append(
                                f'<td class="tt-cell" style="border-left: 4px solid {border_col}; background-color: {bg_col};">'
                                f"{badge}<div class='tt-subj'>{subj}</div><div class='tt-meta'>{sub_line}</div></td>"
                            )
                    html.append("</tr>")
                html.append("</tbody></table>")
                st.markdown("".join(html), unsafe_allow_html=True)

    with tab2:
        if df is not None:
            col_left, col_right = st.columns(2)
            with col_left:
                st.subheader("Course Category Split (Theory vs. Theory-cum-Lab vs. Lab)")
                type_counts = df["Category"].value_counts().reset_index()
                type_counts.columns = ["Course Category", "Periods"]
                fig_donut = px.pie(
                    type_counts,
                    names="Course Category",
                    values="Periods",
                    hole=0.6,
                    color="Course Category",
                    color_discrete_map={"Theory": "#4f46e5", "Theory-cum-Lab": "#9333ea", "Lab": "#f59e0b"},
                )
                st.plotly_chart(fig_donut, use_container_width=True)
            with col_right:
                st.subheader("Shared Lab Utilization (%) Across 24 Labs")
                lab_df = df[df["Type"] == "Lab"]
                slots_per_room = len(DAYS) * 6
                room_usage = lab_df["Room"].value_counts().reset_index()
                room_usage.columns = ["Lab Room", "Used_Slots"]
                room_usage["Utilization_%"] = (room_usage["Used_Slots"] / slots_per_room * 100).round(1)
                fig_bar = px.bar(
                    room_usage,
                    x="Utilization_%",
                    y="Lab Room",
                    orientation="h",
                    text="Utilization_%",
                    range_x=[0, 100],
                    color="Utilization_%",
                    color_continuous_scale="Blues",
                )
                fig_bar.update_traces(texttemplate="%{text}%", textposition="outside")
                fig_bar.update_layout(coloraxis_showscale=False, height=520)
                st.plotly_chart(fig_bar, use_container_width=True)

    with tab3:
        st.subheader("Empirical Evaluation: Greedy Heuristic vs. Google OR-Tools (CP-SAT)")
        try:
            bench_df = pd.read_csv("benchmark_results.csv")
            st.dataframe(bench_df, use_container_width=True, hide_index=True)
            b1, b2 = st.columns(2)
            color_map = {"Greedy Baseline": "#ef4444", "Google OR-Tools (CP-SAT)": "#2563eb"}
            with b1:
                st.plotly_chart(px.bar(bench_df, x="Scenario", y="Hard_Conflicts", color="Algorithm", barmode="group", title="Hard Scheduling Conflicts", color_discrete_map=color_map), use_container_width=True)
            with b2:
                st.plotly_chart(px.bar(bench_df, x="Scenario", y="Student_Idle_Gaps", color="Algorithm", barmode="group", title="Student Idle Gaps / Week", color_discrete_map=color_map), use_container_width=True)
        except FileNotFoundError:
            st.info("Run `python benchmark.py` first to generate `benchmark_results.csv`.")