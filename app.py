# app.py
import streamlit as st
import pandas as pd
import plotly.express as px
from data.sample_campus import DAYS, PERIODS, SECTIONS, ROOMS, COURSES, HOME_ROOMS
from solver.cpsat_optimizer import solve_cpsat
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
        border: 1px solid #e2e8f0; vertical-align: top; height: 96px;
        box-shadow: 0 1px 2px rgba(0,0,0,0.03);
    }
    .tt-free {
        background-color: #f1f5f9; border: 1px dashed #cbd5e1; border-radius: 10px;
        color: #94a3b8; font-size: 0.8rem; text-align: center; vertical-align: middle; height: 96px;
    }
    .tt-subj { font-weight: 700; font-size: 0.88rem; color: #0f172a; margin-bottom: 4px; line-height: 1.25; }
    .tt-meta { font-size: 0.76rem; color: #475569; line-height: 1.35; }
    .badge-lab { display: inline-block; background-color: #fef3c7; color: #b45309; font-size: 0.68rem; font-weight: 700; padding: 1px 6px; border-radius: 4px; margin-bottom: 4px; }
    .badge-lec { display: inline-block; background-color: #e0e7ff; color: #4338ca; font-size: 0.68rem; font-weight: 700; padding: 1px 6px; border-radius: 4px; margin-bottom: 4px; }
    .badge-sub { display: inline-block; background-color: #dcfce7; color: #15803d; font-size: 0.68rem; font-weight: 700; padding: 1px 6px; border-radius: 4px; margin-bottom: 4px; }
    .badge-clash { display: inline-block; background-color: #fee2e2; color: #b91c1c; font-size: 0.68rem; font-weight: 700; padding: 1px 6px; border-radius: 4px; margin-bottom: 4px; }
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


def assign_substitutes(df, absent_fac_list, leave_days):
    """Fair, workload-capped & department-aware substitute faculty assignment."""
    df = df.copy()
    df["Substitute"] = None
    if not absent_fac_list or not leave_days:
        return df, []

    # Map each faculty member to the departments they teach
    fac_depts = {}
    for sec, _, fac, _, _ in COURSES:
        dept = sec.split("-")[0]  # e.g., "CSE-II-A" -> "CSE"
        fac_depts.setdefault(fac, set()).add(dept)

    # Track daily total load (regular classes + assigned substitutes) & weekly sub count
    daily_load = {}
    for _, r in df.iterrows():
        key = (r["Day"], r["Faculty"])
        daily_load[key] = daily_load.get(key, 0) + 1
    sub_count = {f: 0 for f in all_faculty}

    MAX_DAILY_CLASSES = 4  # Hard cap: no teacher teaches > 4 periods/day total

    sub_logs = []
    for d_name in leave_days:
        for p_label in PERIODS:
            slot_df = df[(df["Day"] == d_name) & (df["Period"] == p_label)]
            busy_now = set(slot_df["Faculty"].tolist()) | set(absent_fac_list)
            # Exclude teachers already substituting in this exact period
            busy_now |= set(slot_df["Substitute"].dropna().tolist())

            affected_rows = slot_df[slot_df["Faculty"].isin(absent_fac_list)]
            for idx, row in affected_rows.iterrows():
                target_dept = row["Section"].split("-")[0]

                # Filter candidates: free right now AND under daily workload cap
                candidates = [
                    f for f in all_faculty
                    if f not in busy_now and daily_load.get((d_name, f), 0) < MAX_DAILY_CLASSES
                ]

                if candidates:
                    # Rank by: (1) Same department first, (2) Fewest subs so far, (3) Lowest daily load
                    candidates.sort(
                        key=lambda f: (
                            0 if target_dept in fac_depts.get(f, set()) else 1,
                            sub_count[f],
                            daily_load.get((d_name, f), 0),
                        )
                    )
                    chosen = candidates[0]
                    df.at[idx, "Substitute"] = chosen
                    busy_now.add(chosen)
                    daily_load[(d_name, chosen)] = daily_load.get((d_name, chosen), 0) + 1
                    sub_count[chosen] += 1

                    sub_logs.append({
                        "Day": d_name,
                        "Period": p_label,
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
                        "Period": p_label,
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
    st.markdown("## 🩺 Multi-Faculty Leave Simulator")
    st.caption("Select multiple absent teachers & leave days simultaneously.")
    absent_fac_list = st.multiselect("Absent Faculty (Multi-Select)", all_faculty)
    leave_days = st.multiselect("Leave Day(s)", DAYS, default=["Mon"] if absent_fac_list else [])

    if schedule_mode == "Regular Classes (Weekly)":
        leave_strategy = st.radio(
            "Handling Strategy",
            ["Auto-Assign Free Substitutes (Keep Grid Fixed)", "Re-Optimize Entire Timetable (CP-SAT)"],
            help="When multiple teachers are absent on a 30/30 full schedule, Auto-Assign finds free teachers for those periods.",
        )
        st.divider()
        algorithm_choice = st.radio(
            "Scheduling Engine",
            ["Google OR-Tools (CP-SAT)", "Greedy Heuristic Baseline"],
        )

# ==============================================================================
# MODE 1: EXAM & INVIGILATION SCHEDULER
# ==============================================================================
if schedule_mode == "Exam & Invigilation Schedule":
    st.markdown("### 📝 Semester / Internal Exam & Invigilation Scheduler")
    st.caption("Common department exams • Zero back-to-back daily exams • Fair invigilation duty balancing (CP-SAT)")

    exam_df, exam_ms, exam_status = solve_exam_schedule(unavailable_faculty=absent_fac_list)

    if exam_df is None:
        st.error("No feasible exam schedule found! Try reducing absent faculty count.")
    else:
        e1, e2, e3, e4 = st.columns(4)
        e1.metric("Solver Status", exam_status)
        e2.metric("Solve Time", f"{exam_ms} ms")
        e3.metric("Total Exam Sessions", len(exam_df))
        e4.metric("Excluded Absent Staff", len(absent_fac_list))

        st.markdown("<br>", unsafe_allow_html=True)
        ex_view = st.radio("View Exam Schedule By", ["All Departments Master", "Filter by Section", "Invigilator Duty Roster"], horizontal=True)

        if ex_view == "Filter by Section":
            sec_pick = st.selectbox("Select Section", SECTIONS)
            st.dataframe(exam_df[exam_df["Section"] == sec_pick].drop(columns=["Day_Idx"]), use_container_width=True, hide_index=True)
        elif ex_view == "Invigilator Duty Roster":
            duty_counts = exam_df["Invigilator"].value_counts().reset_index()
            duty_counts.columns = ["Faculty", "Total_Invigilation_Duties"]
            c_left, c_right = st.columns([1, 2])
            with c_left:
                st.subheader("Fairness Duty Count")
                st.dataframe(duty_counts, use_container_width=True, hide_index=True)
            with c_right:
                st.subheader("Detailed Duty Allocation")
                st.dataframe(exam_df[["Day", "Session", "Exam_Hall", "Section", "Exam_Subject", "Invigilator"]], use_container_width=True, hide_index=True)
        else:
            st.dataframe(exam_df.drop(columns=["Day_Idx"]), use_container_width=True, hide_index=True)

        csv_exam = exam_df.drop(columns=["Day_Idx"]).to_csv(index=False).encode("utf-8")
        st.download_button("⬇️ Download Exam & Invigilation Schedule (CSV)", csv_exam, "exam_schedule.csv", "text/csv")

# ==============================================================================
# MODE 2: REGULAR CLASSES (WEEKLY TIMETABLE)
# ==============================================================================
else:
    unavailable_tuples = []
    if absent_fac_list and leave_days and leave_strategy == "Re-Optimize Entire Timetable (CP-SAT)":
        for fac in absent_fac_list:
            for d_name in leave_days:
                d_idx = DAYS.index(d_name)
                for p_idx in range(len(PERIODS)):
                    unavailable_tuples.append((fac, d_idx, p_idx))

    if algorithm_choice == "Google OR-Tools (CP-SAT)":
        df, solve_ms, clashes, status = solve_cpsat(unavailable_faculty=unavailable_tuples)
    else:
        df, solve_ms, clashes, _ = solve_greedy()
        status = "GREEDY_BASELINE"

    sub_logs = []
    if df is not None and absent_fac_list and leave_days and leave_strategy == "Auto-Assign Free Substitutes (Keep Grid Fixed)":
        df, sub_logs = assign_substitutes(df, absent_fac_list, leave_days)

    hdr_left, hdr_right = st.columns([3, 1])
    with hdr_left:
        st.markdown("### 🎓 Campus Resource & Timetable Optimization Engine")
        st.caption("Full-College Constraint Satisfaction • Multi-Teacher Leave Substitution • Google OR-Tools CP-SAT")
    with hdr_right:
        if df is not None:
            csv_data = df.drop(columns=["Day_Idx", "Period_Idx"], errors="ignore").to_csv(index=False).encode("utf-8")
            st.download_button("⬇️ Export Master Schedule (CSV)", csv_data, "entire_college_timetable.csv", "text/csv", use_container_width=True)

    tab1, tab2, tab3 = st.tabs(["📅 Timetable Builder", "📊 Room & Workload Analytics", "🔬 Research Benchmark"])

    with tab1:
        if df is None:
            st.error(
                "No feasible full-grid re-optimization exists when multiple teachers take full-day leave on a 30/30 schedule! "
                "Switch **Handling Strategy** in the sidebar to **Auto-Assign Free Substitutes (Keep Grid Fixed)**."
            )
        else:
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Solver Status", status)
            c2.metric("Solve Latency", f"{solve_ms} ms")
            c3.metric("Hard Conflicts", clashes, delta="0 Clashes (Valid)" if clashes == 0 else f"{clashes} Conflicts", delta_color="normal" if clashes == 0 else "inverse")
            total_slots = len(ROOMS) * len(DAYS) * len(PERIODS)
            c4.metric("Campus Utilization", f"{round((len(df)/total_slots)*100, 1)}%")

            if sub_logs:
                with st.expander(f"🔄 Substitutions Assigned ({len(sub_logs)} classes covered automatically)", expanded=True):
                    st.dataframe(pd.DataFrame(sub_logs), use_container_width=True, hide_index=True)

            st.markdown("<br>", unsafe_allow_html=True)
            v1, v2 = st.columns([2, 2])
            view_mode = v1.radio(
                "View Mode",
                ["Student Section", "Entire College (All Sections)", "Faculty Schedule", "Classroom / Lab View"],
                horizontal=True,
            )

            if view_mode == "Entire College (All Sections)":
                st.subheader(f"🏫 Master College Timetable ({len(SECTIONS)} Sections • {len(df)} Scheduled Periods)")
                pivot_master = (
                    df.pivot_table(
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
                    selected_entity = v2.selectbox("Select Student Section", SECTIONS)
                    filtered_df = df[df["Section"] == selected_entity]
                    st.info(f"🏠 **Designated Home Classroom:** `{HOME_ROOMS[selected_entity]}` • **{len(filtered_df)}/30 Periods Filled**")
                elif view_mode == "Faculty Schedule":
                    selected_entity = v2.selectbox("Select Faculty Member", all_faculty)
                    filtered_df = df[df["Faculty"] == selected_entity]
                else:
                    room_names = [r["name"] for r in ROOMS]
                    selected_entity = v2.selectbox("Select Classroom / Lab", room_names)
                    filtered_df = df[df["Room"] == selected_entity]

                html = ['<table class="tt-table"><thead><tr><th style="width:11%;">Time / Day</th>']
                for d in DAYS:
                    html.append(f"<th>{d}</th>")
                html.append("</tr></thead><tbody>")

                for p_idx, p_label in enumerate(PERIODS):
                    html.append(f'<tr><td class="tt-time"><b>Period {p_idx + 1}</b><br>{p_label}</td>')
                    for d in DAYS:
                        matches = filtered_df[(filtered_df["Day"] == d) & (filtered_df["Period"] == p_label)]
                        if matches.empty:
                            html.append('<td class="tt-free">Free Slot</td>')
                        else:
                            row = matches.iloc[0]
                            subj = row["Subject"]
                            border_col, bg_col = SUBJ_COLORS.get(subj, ("#3b82f6", "#eff6ff"))
                            is_clash = row.get("Conflict", False) or len(matches) > 1
                            sub_teacher = row.get("Substitute")

                            if is_clash:
                                badge = '<span class="badge-clash">⚠️ HARD CLASH</span>'
                                border_col, bg_col = "#ef4444", "#fef2f2"
                            elif pd.notna(sub_teacher) and sub_teacher:
                                badge = '<span class="badge-sub">🔄 SUBSTITUTED</span>'
                                border_col, bg_col = "#16a34a", "#f0fdf4"
                            elif "Lab" in subj:
                                badge = '<span class="badge-lab">LAB SESSION</span>'
                            else:
                                badge = '<span class="badge-lec">HOME LECTURE</span>'

                            fac_display = f"🔄 {sub_teacher} (Sub)" if (pd.notna(sub_teacher) and sub_teacher) else f"👤 {row['Faculty']}"
                            if view_mode == "Student Section":
                                sub_line = f"{fac_display}<br>🏫 {row['Room']}"
                            elif view_mode == "Faculty Schedule":
                                sub_line = f"🎓 {row['Section']}<br>🏫 {row['Room']}"
                            else:
                                sub_line = f"🎓 {row['Section']}<br>{fac_display}"

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
                st.subheader("Workload Split (Lectures vs. Labs)")
                df["Session_Type"] = df["Subject"].apply(lambda s: "Practical Lab" if "Lab" in s else "Theory Lecture")
                type_counts = df["Session_Type"].value_counts().reset_index()
                type_counts.columns = ["Session Type", "Hours"]
                fig_donut = px.pie(type_counts, names="Session Type", values="Hours", hole=0.6, color="Session Type", color_discrete_map={"Theory Lecture": "#4f46e5", "Practical Lab": "#f59e0b"})
                st.plotly_chart(fig_donut, use_container_width=True)
            with col_right:
                st.subheader("Classroom & Lab Utilization (%)")
                slots_per_room = len(DAYS) * len(PERIODS)
                room_usage = df["Room"].value_counts().reset_index()
                room_usage.columns = ["Room", "Used_Slots"]
                room_usage["Utilization_%"] = (room_usage["Used_Slots"] / slots_per_room * 100).round(1)
                fig_bar = px.bar(room_usage, x="Utilization_%", y="Room", orientation="h", text="Utilization_%", range_x=[0, 100], color="Utilization_%", color_continuous_scale="Blues")
                fig_bar.update_traces(texttemplate="%{text}%", textposition="outside")
                fig_bar.update_layout(coloraxis_showscale=False)
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