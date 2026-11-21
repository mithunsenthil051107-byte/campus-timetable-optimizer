# app.py
import streamlit as st
import pandas as pd
import plotly.express as px
from data.sample_campus import DAYS, PERIODS, SECTIONS, ROOMS, COURSES, HOME_ROOMS
from solver.cpsat_optimizer import solve_cpsat
from solver.greedy_baseline import solve_greedy

st.set_page_config(
    page_title="Campus Timetable Optimizer | Google OR-Tools",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- CUSTOM SaaS CSS STYLING ---
st.markdown(
    """
    <style>
    .stApp {
        background-color: #f8fafc;
    }
    div[data-testid="stMetric"] {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        padding: 16px 20px;
        border-radius: 12px;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
    }
    div[data-testid="stMetricLabel"] {
        font-size: 0.85rem;
        font-weight: 600;
        color: #64748b;
    }
    div[data-testid="stMetricValue"] {
        font-size: 1.75rem;
        font-weight: 700;
        color: #0f172a;
    }
    .tt-table {
        width: 100%;
        border-collapse: separate;
        border-spacing: 8px;
        table-layout: fixed;
    }
    .tt-table th {
        background-color: #ffffff;
        color: #334155;
        font-weight: 700;
        font-size: 0.9rem;
        padding: 12px 8px;
        border-radius: 10px;
        border: 1px solid #e2e8f0;
        text-align: center;
    }
    .tt-time {
        background-color: #ffffff;
        color: #475569;
        font-weight: 600;
        font-size: 0.82rem;
        padding: 12px 8px;
        border-radius: 10px;
        border: 1px solid #e2e8f0;
        text-align: center;
        vertical-align: middle;
    }
    .tt-cell {
        background-color: #ffffff;
        border-radius: 10px;
        padding: 10px 12px;
        border: 1px solid #e2e8f0;
        vertical-align: top;
        height: 94px;
        box-shadow: 0 1px 2px rgba(0,0,0,0.03);
    }
    .tt-free {
        background-color: #f1f5f9;
        border: 1px dashed #cbd5e1;
        border-radius: 10px;
        color: #94a3b8;
        font-size: 0.8rem;
        text-align: center;
        vertical-align: middle;
        height: 94px;
    }
    .tt-subj {
        font-weight: 700;
        font-size: 0.88rem;
        color: #0f172a;
        margin-bottom: 4px;
        line-height: 1.25;
    }
    .tt-meta {
        font-size: 0.76rem;
        color: #475569;
        line-height: 1.35;
    }
    .badge-lab {
        display: inline-block;
        background-color: #fef3c7;
        color: #b45309;
        font-size: 0.68rem;
        font-weight: 700;
        padding: 1px 6px;
        border-radius: 4px;
        margin-bottom: 4px;
    }
    .badge-lec {
        display: inline-block;
        background-color: #e0e7ff;
        color: #4338ca;
        font-size: 0.68rem;
        font-weight: 700;
        padding: 1px 6px;
        border-radius: 4px;
        margin-bottom: 4px;
    }
    .badge-clash {
        display: inline-block;
        background-color: #fee2e2;
        color: #b91c1c;
        font-size: 0.68rem;
        font-weight: 700;
        padding: 1px 6px;
        border-radius: 4px;
        margin-bottom: 4px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# Color palette for subjects
PALETTE = [
    ("#3b82f6", "#eff6ff"),  # Blue
    ("#8b5cf6", "#f5f3ff"),  # Violet
    ("#10b981", "#ecfdf5"),  # Emerald
    ("#f59e0b", "#fffbeb"),  # Amber
    ("#ec4899", "#fdf2f8"),  # Pink
    ("#06b6d4", "#ecfeff"),  # Cyan
    ("#6366f1", "#eef2ff"),  # Indigo
]
all_subjects = sorted(list(set(c[1] for c in COURSES)))
SUBJ_COLORS = {subj: PALETTE[i % len(PALETTE)] for i, subj in enumerate(all_subjects)}

# --- SIDEBAR CONTROLS ---
with st.sidebar:
    st.markdown("## ⚙️ Solver Controls")
    algorithm_choice = st.radio(
        "Scheduling Engine",
        ["Google OR-Tools (CP-SAT)", "Greedy Heuristic Baseline"],
        help="Compare mathematical constraint optimization against a naive first-come-first-served heuristic.",
    )

    st.divider()
    st.markdown("## 🩺 Faculty Leave Simulator")
    st.caption("Simulate sudden faculty unavailability and re-optimize dynamically.")
    all_faculty = sorted(list(set(c[2] for c in COURSES)))
    absent_fac = st.selectbox("Absent Faculty", ["None"] + all_faculty)
    col_d, col_p = st.columns(2)
    absent_day = col_d.selectbox("Day", DAYS)
    absent_period = col_p.selectbox("Slot", [p.split("-")[0] for p in PERIODS])

    unavailable = []
    if absent_fac != "None":
        d_idx = DAYS.index(absent_day)
        p_idx = [p.split("-")[0] for p in PERIODS].index(absent_period)
        unavailable.append((absent_fac, d_idx, p_idx))
        st.warning(f"**Leave Active:** {absent_fac} blocked on {absent_day} ({PERIODS[p_idx]})")

# --- RUN SOLVER ---
if algorithm_choice == "Google OR-Tools (CP-SAT)":
    df, solve_ms, clashes, status = solve_cpsat(unavailable_faculty=unavailable)
else:
    df, solve_ms, clashes, _ = solve_greedy()
    status = "GREEDY_BASELINE"

# --- TOP HEADER BAR ---
hdr_left, hdr_right = st.columns([3, 1])
with hdr_left:
    st.markdown("### 🎓 Campus Resource & Timetable Optimization Engine")
    st.caption("Full-College Constraint Satisfaction & Home-Room Binding • Google OR-Tools CP-SAT")
with hdr_right:
    if df is not None:
        csv_data = df.drop(columns=["Day_Idx", "Period_Idx"], errors="ignore").to_csv(index=False).encode("utf-8")
        st.download_button(
            label="⬇️ Export Master Schedule (CSV)",
            data=csv_data,
            file_name="entire_college_timetable.csv",
            mime="text/csv",
            use_container_width=True,
        )

# --- TABS ---
tab1, tab2, tab3 = st.tabs(["📅 Timetable Builder", "📊 Room & Workload Analytics", "🔬 Research Benchmark"])

with tab1:
    if df is None:
        st.error("No feasible schedule exists under these constraints! Try relaxing faculty unavailability.")
    else:
        # KPI Cards
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Solver Status", status)
        c2.metric("Solve Latency", f"{solve_ms} ms")
        c3.metric(
            "Hard Conflicts",
            clashes,
            delta="0 Clashes (Valid)" if clashes == 0 else f"{clashes} Conflicts",
            delta_color="normal" if clashes == 0 else "inverse",
        )
        total_slots = len(ROOMS) * len(DAYS) * len(PERIODS)
        c4.metric("Campus Utilization", f"{round((len(df)/total_slots)*100, 1)}%")

        st.markdown("<br>", unsafe_allow_html=True)

        # Multi-Perspective View Switcher
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
            )
            pivot_master = pivot_master.drop(columns=["Day_Idx", "Period_Idx"])
            st.dataframe(pivot_master, use_container_width=True, hide_index=True, height=620)
        else:
            if view_mode == "Student Section":
                selected_entity = v2.selectbox("Select Student Section", SECTIONS)
                filtered_df = df[df["Section"] == selected_entity]
                st.info(
                    f"🏠 **Designated Home Classroom:** `{HOME_ROOMS[selected_entity]}` "
                    f"(Students remain in their home room for all theory lectures and move only for Labs • "
                    f"**{len(filtered_df)}/30 Periods Filled**)"
                )
            elif view_mode == "Faculty Schedule":
                selected_entity = v2.selectbox("Select Faculty Member", all_faculty)
                filtered_df = df[df["Faculty"] == selected_entity]
            else:
                room_names = [r["name"] for r in ROOMS]
                selected_entity = v2.selectbox("Select Classroom / Lab", room_names)
                filtered_df = df[df["Room"] == selected_entity]

            # Build Rich HTML Timetable Grid
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

                        if is_clash:
                            badge = '<span class="badge-clash">⚠️ HARD CLASH</span>'
                            border_col, bg_col = "#ef4444", "#fef2f2"
                        elif "Lab" in subj:
                            badge = '<span class="badge-lab">LAB SESSION</span>'
                        else:
                            badge = '<span class="badge-lec">HOME LECTURE</span>'

                        if view_mode == "Student Section":
                            sub_line = f"👤 {row['Faculty']}<br>🏫 {row['Room']}"
                        elif view_mode == "Faculty Schedule":
                            sub_line = f"🎓 {row['Section']}<br>🏫 {row['Room']}"
                        else:
                            sub_line = f"🎓 {row['Section']}<br>👤 {row['Faculty']}"

                        html.append(
                            f'<td class="tt-cell" style="border-left: 4px solid {border_col}; background-color: {bg_col};">'
                            f"{badge}"
                            f'<div class="tt-subj">{subj}</div>'
                            f'<div class="tt-meta">{sub_line}</div>'
                            f"</td>"
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
            fig_donut = px.pie(
                type_counts,
                names="Session Type",
                values="Hours",
                hole=0.6,
                color="Session Type",
                color_discrete_map={"Theory Lecture": "#4f46e5", "Practical Lab": "#f59e0b"},
            )
            fig_donut.update_layout(margin=dict(t=20, b=20, l=20, r=20), paper_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig_donut, use_container_width=True)

        with col_right:
            st.subheader("Classroom & Lab Utilization (%)")
            slots_per_room = len(DAYS) * len(PERIODS)
            room_usage = df["Room"].value_counts().reset_index()
            room_usage.columns = ["Room", "Used_Slots"]
            room_usage["Utilization_%"] = (room_usage["Used_Slots"] / slots_per_room * 100).round(1)
            fig_bar = px.bar(
                room_usage,
                x="Utilization_%",
                y="Room",
                orientation="h",
                text="Utilization_%",
                range_x=[0, 100],
                color="Utilization_%",
                color_continuous_scale="Blues",
            )
            fig_bar.update_traces(texttemplate="%{text}%", textposition="outside")
            fig_bar.update_layout(
                margin=dict(t=20, b=20, l=20, r=20),
                paper_bgcolor="rgba(0,0,0,0)",
                coloraxis_showscale=False,
            )
            st.plotly_chart(fig_bar, use_container_width=True)

        st.subheader("Faculty Weekly Teaching Load (Hours)")
        fac_load = df["Faculty"].value_counts().reset_index()
        fac_load.columns = ["Faculty", "Assigned_Hours"]
        fig_fac = px.bar(
            fac_load,
            x="Faculty",
            y="Assigned_Hours",
            text="Assigned_Hours",
            color_discrete_sequence=["#0ea5e9"],
        )
        fig_fac.update_traces(textposition="outside")
        fig_fac.update_layout(margin=dict(t=20, b=20, l=20, r=20), paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig_fac, use_container_width=True)

with tab3:
    st.subheader("Empirical Evaluation: Greedy Heuristic vs. Google OR-Tools (CP-SAT)")
    st.caption("Stress-tested across increasing student section loads under fixed room constraints.")
    try:
        bench_df = pd.read_csv("benchmark_results.csv")
        st.dataframe(bench_df, use_container_width=True, hide_index=True)

        b1, b2 = st.columns(2)
        color_map = {"Greedy Baseline": "#ef4444", "Google OR-Tools (CP-SAT)": "#2563eb"}
        with b1:
            fig_conflicts = px.bar(
                bench_df,
                x="Scenario",
                y="Hard_Conflicts",
                color="Algorithm",
                barmode="group",
                title="Hard Scheduling Conflicts (Lower is Better)",
                color_discrete_map=color_map,
            )
            fig_conflicts.update_layout(paper_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig_conflicts, use_container_width=True)

        with b2:
            fig_gaps = px.bar(
                bench_df,
                x="Scenario",
                y="Student_Idle_Gaps",
                color="Algorithm",
                barmode="group",
                title="Student Idle Gaps / Week (Lower is Better)",
                color_discrete_map=color_map,
            )
            fig_gaps.update_layout(paper_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig_gaps, use_container_width=True)
    except FileNotFoundError:
        st.info("Run `python benchmark.py` first to generate `benchmark_results.csv`.")