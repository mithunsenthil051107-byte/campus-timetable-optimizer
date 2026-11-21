# 🎓 AI-Based Campus Resource & Timetable Optimization

**Live Interactive Demo:** [Open Deployed Web App](https://YOUR-APP-LINK.streamlit.app)

An automated academic scheduling and resource optimization engine built with **Google OR-Tools (CP-SAT)** and **Python**. It formulates university course timetabling as a **Constraint Satisfaction & Multi-Objective Integer Programming** problem—eliminating scheduling clashes, minimizing student idle gaps, maximizing classroom utilization, and supporting real-time faculty leave substitutions.

---

## 1. Mathematical Formulation (CP-SAT Model)

### Decision Variables
$$X_{c, r, d, p} \in \{0, 1\}$$
Equals `1` if course $c$ is assigned to room $r$ on day $d$ during period $p$, and `0` otherwise.

### Hard Constraints (Zero-Tolerance)
1. **Weekly Hour Fulfillment:** $\sum_{r, d, p} X_{c, r, d, p} = H_c \quad \forall c \in \text{Courses}$
2. **Room Exclusivity & Type Matching:** $\sum_{c} X_{c, r, d, p} \le 1$ (Labs strictly assigned to lab rooms; at most one class per room per slot).
3. **Faculty Non-Overlap & Leave Enforcement:** $\sum_{c \in \text{Fac}(f), r} X_{c, r, d, p} \le 1$ (Zero double-booking; respects real-time faculty unavailability).
4. **Student Section Non-Overlap:** $\sum_{c \in \text{Sec}(s), r} X_{c, r, d, p} \le 1$
5. **Daily Subject Spread:** $\sum_{r, p} X_{c, r, d, p} \le 1 \quad \forall c, d$ (At most one session of a subject per day).

### Multi-Objective Function
$$\min \left( 20 \sum_{s, d} \text{IdleGaps}(s, d) + \sum_{c, r, d, p} (p + r) \cdot X_{c, r, d, p} \right)$$
* Minimizes isolated idle gaps between daily lectures for students.
* Consolidates classes into primary rooms and morning/mid-day time slots.

---

## 2. Empirical Research Benchmark: Greedy Baseline vs. Google OR-Tools

Evaluated across 4 progressively tighter campus load scenarios (scaling from 3 to 6 student sections under fixed room capacity):

* **Hard Conflicts:** Reduced to **0** across all scenarios (100% feasible schedules).
* **Student Idle Gaps:** Eliminated fragmented daily breaks via exact span-tracking constraints.
* **Sub-Second Dynamic Re-Optimization:** Computes conflict-free faculty leave substitutions in `< 1 second`.

*(Run `python benchmark.py` to reproduce `benchmark_results.csv`.)*

---

## 3. Tech Stack & Local Setup
* **Optimization Solver:** Google OR-Tools (`cp_model` CP-SAT)
* **Data & Analytics:** Python, Pandas, Plotly
* **Web Dashboard:** Streamlit

```bash
git clone [https://github.com/YOUR_USERNAME/campus-timetable-optimizer.git](https://github.com/YOUR_USERNAME/campus-timetable-optimizer.git)
cd campus-timetable-optimizer
pip install -r requirements.txt
python benchmark.py
streamlit run app.py
