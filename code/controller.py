"""
controller.py — Main simulation controller for The OH Race Project.

This module:
• Loads configuration selected by the user (or defaults).
• Builds the world and sets agent starting positions.
• Calls the selected search algorithms (HC, SHC, SA).
• Converts algorithm paths into animation-friendly traces.
• Computes per-agent performance metrics (steps, space, final score).
• Hands everything to the UI (aua_ui or aua_ui_patched) for visualization.

The logic here is intentionally defensive: if an algorithm fails or returns
an invalid path, the controller gracefully cleans the path and generates a
fallback per-tile trace to ensure the simulation always runs without crashing.
"""

import random
import tkinter as tk
import aua_world as world
from aua_setup import CONFIG, open_setup_window
import search_algorithms as sa
import aua_ui_patched as ui


# ========================
# GLOBAL CONFIG
# ========================
START_POINTS = 1000
START_TIME = 300
TICK_RATE = 0.05
SEED = 18

DEFAULT_ALGOS = {1: "hc", 2: "shc", 3: "sa"}


# ========================
# Algorithm Dispatcher
# ========================
def compute_path(name, grid, placement, start):
    """
    Call the appropriate search algorithm.
    All algorithms return (path, metrics).
    """
    if name == "hc":
        return sa.hill_climbing(grid, placement, start)
    if name == "shc":
        return sa.stochastic_hill_climbing(grid, placement, start)
    if name == "sa":
        return sa.simulated_annealing(grid, placement, start)
    raise ValueError(f"Unknown algorithm: {name}")


# ========================
# Validate selected algorithms
# ========================
def validate_algos(raw):
    """
    Ensure:
    • algorithms are among ["hc", "shc", "sa"]
    • no duplicates (unique per agent)
    • fall back to unused algorithms when needed
    """
    allowed = ["hc", "shc", "sa"]
    used, out = set(), {}
    for aid in (1, 2, 3):
        a = raw.get(aid)
        if a in allowed and a not in used:
            out[aid] = a
            used.add(a)
        else:
            for x in allowed:
                if x not in used:
                    out[aid] = x
                    used.add(x)
                    break
    return out


# ========================
# Fallback path execution (if algorithm is broken)
# ========================
def fallback_run_with_metrics(grid, placement, path, start_points, start_time):
    """
    Simulates walking the planned path.
    Produces a reliable tile-by-tile trace used for animation.
    A single step looks like:
        {"pos": (x,y), "score": int, "timer": int, "reason": str}
    """
    trace = []
    score = int(start_points)
    timer = int(start_time)
    prev = None

    # ensure at least starting tile
    if not path:
        path = [placement.start]

    for p in path:
        try:
            x, y = int(p[0]), int(p[1])
        except Exception:
            continue

        # clamp
        if y < 0 or y >= len(grid) or x < 0 or x >= len(grid[0]):
            continue

        score = max(0, score - 1)
        timer = max(0, timer - 1)

        reason = "normal"
        cell = grid[y][x]
        if cell == world.ANGRY:
            score = max(0, score - 150)
            reason = "angry"
        if cell == world.CHAIR:
            score = 0
            reason = "chair"
        if cell == world.OFFICE:
            reason = "goal"

        trace.append({"pos": (x, y), "score": score, "timer": timer, "reason": reason})

        if reason in ("chair", "goal") or score <= 0 or timer <= 0:
            break
        prev = (x, y)

    if not trace:
        sx, sy = placement.start
        trace.append({"pos": (sx, sy), "score": start_points, "timer": start_time, "reason": "done"})

    return trace


# ========================
# Backward-compat helper (kept for reference)
# ========================
def select_winner_and_optimal(agents):
    goal_agents = [a for a in agents if a.get("reason") == "goal"]
    if not goal_agents:
        return None, None
    optimal = max(goal_agents, key=lambda a: (a["score"], -a["metrics"]["steps"]))
    winner = max(goal_agents, key=lambda a: (a["score"], -a["metrics"]["steps"]))
    return winner, optimal


# ========================
# MAIN CONTROLLER
# ========================
def main():
    random.seed(SEED)

    # Attempt to open the configuration selection window
    try:
        open_setup_window()
    except tk.TclError:
        print("[Setup] Tkinter already closed safely.")
    except Exception as e:
        print("[Setup] Ignored exception in setup:", e)

    # Read user algorithm selections (with defensive parsing)
    user = {}
    for aid in (1, 2, 3):
        raw = CONFIG.get(f"agent{aid}_algo")
        if not raw:
            continue
        L = raw.lower()
        if "stochastic" in L:
            user[aid] = "shc"
        elif "anneal" in L:
            user[aid] = "sa"
        else:
            user[aid] = "hc"

    algos = validate_algos({**DEFAULT_ALGOS, **user})

    # Build world and initial placement
    grid, placement = world.build_world(seed=SEED)
    start = placement.start

    agents = []
    traces = {}

    # ======== RUN ALL AGENTS ========
    for aid in (1, 2, 3):
        algo = algos[aid]
        placement.algo = algo

        # Run selected algorithm
        try:
            ret = compute_path(algo, grid, placement, start)
        except Exception as e:
            print(f"[Controller] Algorithm {algo} crashed for agent {aid}: {e}")
            ret = ([], {"steps": 0, "space": 0})

        # normalize return
        if isinstance(ret, tuple) and len(ret) == 2 and isinstance(ret[1], dict):
            raw_path, metrics = ret
        else:
            raw_path = ret
            metrics = {"steps": 0, "space": 0}

        # sanitize incoming path
        if raw_path is None:
            raw_path = []
        if not isinstance(raw_path, list):
            try:
                raw_path = list(raw_path)
            except Exception:
                raw_path = [raw_path]

        try:
            path = sa.sanitize_path(grid, raw_path)
            if path is None:
                path = []
        except Exception:
            # backup sanitization
            path = []
            for item in raw_path:
                try:
                    x, y = int(item[0]), int(item[1])
                except Exception:
                    continue
                if 0 <= y < len(grid) and 0 <= x < len(grid[0]) and grid[y][x] != world.WALL:
                    path.append((x, y))

        # ensure starting tile is first
        if not path or path[0] != start:
            path = [start] + [p for p in path if p != start]

        # ======== GET EXECUTION TRACE ========
        try:
            mtrace = sa.run_with_metrics(grid, placement, path, START_POINTS, START_TIME)
            if not isinstance(mtrace, list) or not mtrace:
                raise ValueError("empty or invalid mtrace")
        except Exception:
            mtrace = fallback_run_with_metrics(grid, placement, path, START_POINTS, START_TIME)

        if not mtrace:
            mtrace = [{"pos": start, "score": START_POINTS, "timer": START_TIME, "reason": "done"}]

        # animation trace
        try:
            anim_trace = []
            for step in mtrace:
                px = int(step["pos"][0])
                py = int(step["pos"][1])
                if 0 <= py < len(grid) and 0 <= px < len(grid[0]):
                    anim_trace.append((px, py))
            if not anim_trace:
                anim_trace = [start]
        except Exception:
            anim_trace = [start]

        traces[aid] = anim_trace

        # ======== FINAL METRICS ========
        metrics = metrics or {"steps": 0, "space": 0}
        metrics.setdefault("steps", 0)
        metrics.setdefault("space", 0)

        try:
            derived_steps = max(0, len(mtrace) - 1)
            if metrics["steps"] <= 0:
                metrics["steps"] = derived_steps
        except Exception:
            pass

        try:
            metrics["space"] = int(metrics.get("space", 0))
        except Exception:
            metrics["space"] = 0

        state = mtrace[-1]
        final_score = int(state.get("score", START_POINTS))
        final_time = int(state.get("timer", START_TIME))
        reason = state.get("reason")

        if not reason:
            if final_score <= 0:
                reason = "no_points"
            elif final_time <= 0:
                reason = "no_time"
            elif anim_trace and anim_trace[-1] == placement.office:
                reason = "goal"
            else:
                reason = "done"

        # ======== BUILD AGENT OBJECT ========
        agents.append({
            "id": aid,
            "algo": algo,
            "pos": start,
            "score": final_score,
            "timer": final_time,
            "reason": reason,
            "path": anim_trace,
            "trace_index": 0,
            "alive": True,
            "time_complexity": f"steps = {metrics['steps']}",
            "space_complexity": f"peak = {metrics['space']}",
            "metrics": {"steps": metrics["steps"], "space": metrics["space"]},
            "ops": metrics["steps"],
            "peak": metrics["space"]
        })

    # Determine winner, optimal, efficient
    if agents:
        winner = max(agents, key=lambda a: (a["score"], a["timer"]))
        efficient = max(agents, key=lambda a: a["timer"])
        for a in agents:
            a["winner"] = (a["id"] == winner["id"])
            a["optimal"] = (a["id"] == winner["id"])
            a["efficient"] = (a["id"] == efficient["id"])
    else:
        for a in agents:
            a["winner"] = a["optimal"] = a["efficient"] = False

    # ========================
    # START VISUALIZATION
    # ========================
    ui.start_visualization(grid, placement, agents, traces, tick_rate=TICK_RATE)


if __name__ == "__main__":
    main()
