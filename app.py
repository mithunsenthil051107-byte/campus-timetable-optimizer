# app.py
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from data.sample_campus import DAYS, PERIODS, SECTIONS, ROOMS, COURSES
from solver.cpsat_optimizer import solve_cpsat
from solver.greedy_baseline import solve_greedy

st.set_page_config(page_title="Campus Timetable Optimizer (OR-Tools)", layout="wide")

st.title("🎓 AI-Based Campus Resource & Timetable Optimization")
st.caption("Powered by Google OR-Tools (CP-SAT) • Constraint Satisfaction & Multi-Objective Scheduling")

# Sidebar Controls (Inspired by Timetable Builder UI)
st.sidebar.header("⚙️ Solver & Constraint Controls")
algorithm_choice = st.sidebar.radio(
    "Select Scheduling Engine",
    ["Google OR-Tools (CP-SAT)", "Greedy Heuristic Baseline"],
)

st.sidebar.subheader("🩺 Faculty Leave / Substitution Simulator")
all_faculty = sorted(list(set(c[2] for c in COURSES)))
absent_fac = st.sidebar.selectbox("Absent Faculty (Optional)", ["None"] + all_faculty)
absent_day = st.sidebar.selectbox("Absent Day", DAYS)
absent_period = st.sidebar.selectbox("Absent Period", PERIODS)

unavailable = []
if absent_fac != "None":
    d_idx = DAYS.index(absent_day)
    p_idx = PERIODS.index(absent_period)
    unavailable.append((absent_fac, d_idx, p_idx))
    st.sidebar.warning(f"Constraint Active: {absent_fac} unavailable on {absent_day} ({absent_period})")

# Run Solver
if algorithm_choice == "Google OR-Tools (CP-SAT)":
    df, solve_ms, clashes, status = solve_cpsat(unavailable_faculty=unavailable)
else:
    df, solve_ms, clashes, _ = solve_greedy()
    status = "GREEDY_HEURISTIC"

# Tabs
tab1, tab2, tab3 = st.tabs(["📅 Timetable Builder", "📊 Resource & Room Analytics", "🔬 Research Benchmark"])

with tab1:
    if df is None:
        st.error("No feasible schedule exists under these constraints! Try relaxing faculty unavailability.")
    else:
        # Top KPI Metrics Row
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Solver Status", status)
        c2.metric("Solve Time", f"{solve_ms} ms")
        c3.metric("Hard Conflicts", clashes, delta="Conflict-Free" if clashes == 0 else f"{clashes} Clashes", delta_color="normal" if clashes == 0 else "inverse")
        total_slots = len(ROOMS) * len(DAYS) * len(PERIODS)
        c4.metric("Room Utilization", f"{round((len(df)/total_slots)*100, 1)}%")

        st.divider()

        # Section Filter & Weekly Grid
        selected_section = st.selectbox("Select Student Section View", SECTIONS)
        sec_df = df[df["Section"] == selected_section]

        # Build Weekly Pivot Grid (Rows = Periods, Columns = Days)
        grid = pd.DataFrame(index=PERIODS, columns=DAYS).fillna("— Free Slot —")
        for _, row in sec_df.iterrows():
            cell_text = f"**{row['Subject']}**\n\n👤 {row['Faculty']} | 🏫 {row['Room']}"
            if row.get("Conflict", False):
                cell_text = f"⚠️ CLASH: {cell_text}"
            grid.loc[row["Period"], row["Day"]] = cell_text

        st.subheader(f"Weekly Schedule — {selected_section}")
        st.table(grid)

with tab2:
    if df is not None:
        col_left, col_right = st.columns(2)

        with col_left:
            st.subheader("Workload Summary (Lectures vs Labs)")
            df["Type"] = df["Subject"].apply(lambda s: "Lab" if "Lab" in s else "Lecture")
            type_counts = df["Type"].value_counts().reset_index()
            type_counts.columns = ["Session Type", "Hours"]
            fig_donut = px.pie(type_counts, names="Session Type", values="Hours", hole=0.55)
            st.plotly_chart(fig_donut, use_container_width=True)

        with col_right:
            st.subheader("Room Utilization (%)")
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
            )
            st.plotly_chart(fig_bar, use_container_width=True)

with tab3:
    st.subheader("Greedy Baseline vs. Google OR-Tools (CP-SAT)")
    try:
        bench_df = pd.read_csv("benchmark_results.csv")
        st.dataframe(bench_df, use_container_width=True)

        b1, b2 = st.columns(2)
        with b1:
            fig_conflicts = px.bar(
                bench_df,
                x="Scenario",
                y="Hard_Conflicts",
                color="Algorithm",
                barmode="group",
                title="Hard Scheduling Conflicts (Lower is Better)",
            )
            st.plotly_chart(fig_conflicts, use_container_width=True)

        with b2:
            fig_gaps = px.bar(
                bench_df,
                x="Scenario",
                y="Student_Idle_Gaps",
                color="Algorithm",
                barmode="group",
                title="Student Idle Gaps per Week (Lower is Better)",
            )
            st.plotly_chart(fig_gaps, use_container_width=True)
    except FileNotFoundError:
        st.info("Run `python benchmark.py` in your terminal first to generate `benchmark_results.csv`.")