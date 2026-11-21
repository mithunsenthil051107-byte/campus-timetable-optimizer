# solver/greedy_baseline.py
import time
import pandas as pd
from data.sample_campus import DAYS, PERIODS, SECTIONS, ROOMS, COURSES


def solve_greedy(days=DAYS, periods=PERIODS, sections=SECTIONS, rooms=ROOMS, courses=COURSES):
    start_time = time.time()
    num_days = len(days)
    num_periods = len(periods)

    # Track occupied slots: (entity_type, entity_id, day, period)
    occupied_room = set()
    occupied_faculty = set()
    occupied_section = set()

    schedule = []
    conflicts = 0
    unscheduled_hours = 0

    for c_idx, (sec, subj, fac, r_type, hrs) in enumerate(courses):
        valid_rooms = [r["name"] for r in rooms if r["type"] == r_type]
        if not valid_rooms:
            unscheduled_hours += hrs
            continue

        assigned = 0
        used_days = set()

        # Pass 1: Try to assign cleanly without any conflicts (max 1 per day)
        for d in range(num_days):
            if assigned >= hrs:
                break
            if d in used_days:
                continue
            for p in range(num_periods):
                if assigned >= hrs:
                    break
                if (fac, d, p) in occupied_faculty or (sec, d, p) in occupied_section:
                    continue
                for r_name in valid_rooms:
                    if (r_name, d, p) not in occupied_room:
                        occupied_room.add((r_name, d, p))
                        occupied_faculty.add((fac, d, p))
                        occupied_section.add((sec, d, p))
                        used_days.add(d)
                        schedule.append({
                            "Section": sec,
                            "Day": days[d],
                            "Day_Idx": d,
                            "Period": periods[p],
                            "Period_Idx": p,
                            "Subject": subj,
                            "Faculty": fac,
                            "Room": r_name,
                            "Conflict": False,
                        })
                        assigned += 1
                        break

        # Pass 2: If hours remain, force-assign into least-conflicting slot (simulating manual rush)
        while assigned < hrs:
            best_slot = None
            min_clash = 999
            for d in range(num_days):
                for p in range(num_periods):
                    for r_name in valid_rooms:
                        clash = (
                            int((r_name, d, p) in occupied_room)
                            + int((fac, d, p) in occupied_faculty)
                            + int((sec, d, p) in occupied_section)
                        )
                        if clash < min_clash:
                            min_clash = clash
                            best_slot = (r_name, d, p)

            r_name, d, p = best_slot
            occupied_room.add((r_name, d, p))
            occupied_faculty.add((fac, d, p))
            occupied_section.add((sec, d, p))
            if min_clash > 0:
                conflicts += min_clash
            schedule.append({
                "Section": sec,
                "Day": days[d],
                "Day_Idx": d,
                "Period": periods[p],
                "Period_Idx": p,
                "Subject": subj,
                "Faculty": fac,
                "Room": r_name,
                "Conflict": min_clash > 0,
            })
            assigned += 1

    solve_ms = round((time.time() - start_time) * 1000, 2)
    df = pd.DataFrame(schedule).sort_values(["Section", "Day_Idx", "Period_Idx"])
    return df, solve_ms, conflicts, unscheduled_hours


if __name__ == "__main__":
    df, ms, clashes, unsched = solve_greedy()
    print(f"Greedy Finished in {ms} ms | Hard Conflicts: {clashes} | Unscheduled Hours: {unsched}")