"""
batch_runner.py

Batch runner for The OH Race Project — executes multiple headless simulations
(without opening any UI windows) and saves detailed per-run CSV logs.

Each run:
    • Builds the world deterministically from a fixed seed.
    • Runs all 3 search algorithms (HC / SHC / SA).
    • Executes movement simulation for each agent.
    • Saves a long-format CSV: one row per coordinate visited by each agent.

Usage:
    python3 batch_runner.py

Output:
    A folder "batch_results_YYYYMMDD_HHMMSS/"
    containing:
        run_01_seed_1.csv
        run_02_seed_2.csv
        ...
        run_30_seed_30.csv
"""

import os
import csv
import random
from datetime import datetime

import aua_setup
import aua_world
import search_algorithms as sa
import controller

# ============================================================
# USER PARAMETERS
# ============================================================

NUM_RUNS = 30

OUT_DIR = "batch_results_" + datetime.now().strftime("%Y%m%d_%H%M%S")

OVERRIDES = {
    # World geometry
    "main_w":        aua_setup.CONFIG.get("main_w", 20),
    "pab_w":         aua_setup.CONFIG.get("pab_w", 8),
    "bridge_len":    aua_setup.CONFIG.get("bridge_len", 6),

    # Wall distribution
    "walls_main":    aua_setup.CONFIG.get("walls_main", 10),
    "walls_pab":     aua_setup.CONFIG.get("walls_pab", 5),
    "walls_bridge":  aua_setup.CONFIG.get("walls_bridge", 3),

    # Angry student counts
    "angry_main":    aua_setup.CONFIG.get("angry_main", 4),
    "angry_pab":     aua_setup.CONFIG.get("angry_pab", 2),
    "angry_bridge":  aua_setup.CONFIG.get("angry_bridge", 1),

    # Algorithm overrides (optional)
    # "agent1_algo": "hc",
    # "agent2_algo": "shc",
    # "agent3_algo": "sa",
}

# ============================================================
# HELPER FUNCTIONS
# ============================================================

def ensure_outdir(path: str):
    """Ensure output directory exists."""
    os.makedirs(path, exist_ok=True)


def save_run_csv(out_dir, run_index, seed, grid, placement, agents):
    """
    Save one CSV per run in long format.
    Each row = one coordinate visited by a specific agent at a specific step.
    """

    fname = os.path.join(out_dir, f"run_{run_index:02d}_seed_{seed}.csv")

    with open(fname, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "agent_id", "algo", "score", "timer", "reason",
            "steps", "space",
            "step_index", "x", "y"
        ])

        for a in agents:
            aid = a["id"]
            algo = a["algo"]
            score = a["score"]
            timer = a["timer"]
            reason = a["reason"]
            metrics = a["metrics"]

            steps = metrics.get("steps", "")
            space = metrics.get("space", "")
            path = a["path"]

            for step_index, (x, y) in enumerate(path):
                writer.writerow([
                    aid, algo, score, timer, reason,
                    steps, space,
                    step_index, x, y
                ])

    print("Saved:", fname)

# ============================================================
# SINGLE RUN EXECUTION
# ============================================================

def run_one(run_index: int, seed: int, out_dir: str):
    """
    Execute ONE full simulation run:
        • Apply configuration overrides
        • Build world with deterministic seed
        • Run each agent's search algorithm
        • Run movement simulation
        • Save results
    """
    print(f"\n[Run {run_index}] seed={seed}")

    for k, v in OVERRIDES.items():
        if v is None:
            if k == "main_w":        v = 20
            elif k == "pab_w":       v = 8
            elif k == "bridge_len":  v = 6
            elif k == "walls_main":  v = 10
            elif k == "walls_pab":   v = 5
            elif k == "walls_bridge": v = 3
            elif k == "angry_main":   v = 4
            elif k == "angry_pab":    v = 2
            elif k == "angry_bridge": v = 1

        aua_setup.CONFIG[k] = v

    aua_setup.CONFIG["SEED"] = seed
    random.seed(seed)

    # --------------------------------------
    # WORLD GENERATION
    # --------------------------------------
    grid, placement = aua_world.build_world(seed=seed)

    # --------------------------------------
    # Determine algorithms for agents
    # --------------------------------------
    user_algos = {}
    for aid in (1, 2, 3):
        raw = aua_setup.CONFIG.get(f"agent{aid}_algo")
        if raw:
            L = str(raw).lower()
            if "stochastic" in L or "shc" in L:
                user_algos[aid] = "shc"
            elif "anneal" in L or "sa" in L:
                user_algos[aid] = "sa"
            else:
                user_algos[aid] = "hc"

    algos = controller.validate_algos({**controller.DEFAULT_ALGOS, **user_algos})

    agents = []
    start = placement.start

    START_POINTS = getattr(controller, "START_POINTS", 1000)
    START_TIME = getattr(controller, "START_TIME", 300)

    # ============================================================
    # RUN ALL 3 AGENTS
    # ============================================================
    for aid in (1, 2, 3):

        algo = algos[aid]
        placement.algo = algo  # set algorithm name for logging

        # --------------------------------------
        # Compute path using HC/SHC/SA
        # --------------------------------------
        try:
            ret = controller.compute_path(algo, grid, placement, start)
        except Exception as e:
            print(f"[Controller] Algorithm {algo} crashed for agent {aid}: {e}")
            ret = ([], {"steps": 0, "space": 0})

        raw_path = []
        metrics = None
        if isinstance(ret, (tuple, list)):
            if len(ret) >= 1:
                raw_path = ret[0]
            if len(ret) >= 2:
                metrics = ret[1]
        else:
            raw_path = ret

        path = []
        try:
            for px, py in raw_path:
                px = int(px)
                py = int(py)
                if 0 <= py < len(grid) and 0 <= px < len(grid[0]):
                    if grid[py][px] != aua_world.WALL:
                        path.append((px, py))
        except Exception:
            path = []

        if not path or path[0] != start:
            path = [start] + [p for p in path if p != start]

        # --------------------------------------
        # Run movement simulation (metrics trace)
        # --------------------------------------
        try:
            mtrace = sa.run_with_metrics(grid, placement, path, START_POINTS, START_TIME)
            if not isinstance(mtrace, list) or not mtrace:
                mtrace = controller.fallback_run_with_metrics(grid, placement, path, START_POINTS, START_TIME)
        except Exception:
            mtrace = controller.fallback_run_with_metrics(grid, placement, path, START_POINTS, START_TIME)

        anim_trace = []
        for step in mtrace:
            px, py = step["pos"]
            anim_trace.append((int(px), int(py)))

        if not anim_trace:
            anim_trace = [start]

        # --------------------------------------
        # Finalize metrics
        # --------------------------------------
        if metrics is None:
            metrics = {"steps": 0, "space": 0}

        metrics.setdefault("steps", max(0, len(mtrace) - 1))
        metrics.setdefault("space", int(metrics.get("space", 0)))

        final_score = mtrace[-1].get("score", 0)
        final_time  = mtrace[-1].get("timer", 0)
        reason      = mtrace[-1].get("reason", "")

        agents.append({
            "id": aid,
            "algo": algo,
            "pos": start,
            "score": final_score,
            "timer": final_time,
            "reason": reason,
            "path": anim_trace,
            "metrics": {
                "steps": metrics["steps"],
                "space": metrics["space"],
            },
        })

    save_run_csv(out_dir, run_index, seed, grid, placement, agents)

    return agents

# ============================================================
# MAIN BATCH LOOP
# ============================================================

def main():
    ensure_outdir(OUT_DIR)
    print("Output folder:", OUT_DIR)

    for i in range(1, NUM_RUNS + 1):
        seed = i
        run_one(i, seed, OUT_DIR)

    print("\nBatch complete. CSV files are in:", OUT_DIR)


if __name__ == "__main__":
    main()
