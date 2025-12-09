import math
import random
from typing import List, Tuple, Optional, Dict
import aua_world as world

Pos = Tuple[int, int]
Metrics = Dict[str, int]


# ---------------------------
# VALIDITY & MOVEMENT HELPERS
# ---------------------------

def is_in_main(x, y):
    return (0 <= x < world.MAIN_W) and (0 <= y < world.WORLD_H)

def is_in_bridge(x, y):
    bx0 = world.MAIN_W
    bx1 = world.MAIN_W + world.BRIDGE_LEN - 1
    return (bx0 <= x <= bx1) and (y == world.BRIDGE_ROW)

def is_in_pab(x, y):
    pab_x_min = world.MAIN_W + world.BRIDGE_LEN
    pab_x_max = pab_x_min + world.PAB_W - 1
    pab_y_min = world.PAB_ROW_OFFSET
    pab_y_max = pab_y_min + world.PAB_H - 1
    return (pab_x_min <= x <= pab_x_max) and (pab_y_min <= y <= pab_y_max)

def is_valid_region(x, y):
    return is_in_main(x, y) or is_in_bridge(x, y) or is_in_pab(x, y)

def is_walkable(grid, x, y):
    if not is_valid_region(x, y):
        return False
    try:
        return grid[y][x] not in (world.WALL,)
    except Exception:
        return False

# 4-connected neighbors
def get_neighbors(grid, pos: Pos) -> List[Pos]:
    x, y = pos
    out = []

    for nx, ny in [(x+1,y), (x-1,y), (x,y+1), (x,y-1)]:

        # must be walkable tile
        if not is_walkable(grid, nx, ny):
            continue

        # CASE 1 — currently inside MAIN
        if is_in_main(x, y):
            if is_in_main(nx, ny):
                out.append((nx, ny))
                continue
            # allowed: MAIN → BRIDGE
            if is_in_bridge(nx, ny):
                out.append((nx, ny))
                continue
            continue  # main → pab not allowed

        # CASE 2 — currently inside PAB
        if is_in_pab(x, y):
            if is_in_pab(nx, ny):
                out.append((nx, ny))
                continue
            # allowed: PAB → BRIDGE
            if is_in_bridge(nx, ny):
                out.append((nx, ny))
                continue
            continue  # pab → main not allowed

        # CASE 3 — currently on the BRIDGE
        if is_in_bridge(x, y):
            # bridge can go to main, pab, or still bridge
            if is_in_main(nx, ny) or is_in_pab(nx, ny) or is_in_bridge(nx, ny):
                out.append((nx, ny))

    return out




def manhattan(a: Pos, b: Pos) -> int:
    return abs(a[0] - b[0]) + abs(a[1] - b[1])

def sanitize_path(grid, path: List[Pos]) -> List[Pos]:
    clean = []
    for (x, y) in path:
        try:
            xi, yi = int(x), int(y)
        except Exception:
            break
        if not (0 <= yi < len(grid) and 0 <= xi < len(grid[0])):
            break
        if not is_walkable(grid, xi, yi):
            break
        clean.append((xi, yi))
        cell = grid[yi][xi]
        if cell in (world.CHAIR, world.OFFICE):
            break
    return clean


# ------------------------------------------------------------
# 1) HILL-CLIMBING (basic greedy)
# ------------------------------------------------------------
# def hill_climbing(grid, placement, start: Pos,
#                         max_steps=2000, restarts=0) -> Tuple[List[Pos], Metrics]:
#     """
#     Basic greedy hill-climb: at each step choose neighbor with strictly smaller Manhattan distance.
#     Stops at local optimum or goal.
#     """
#     goal = placement.office
#     cur = start
#     path = [cur]
#     steps = 0
#
#     for _ in range(max_steps):
#         steps += 1
#         if cur == goal:
#             break
#         nbrs = get_neighbors(grid, cur)
#         if not nbrs:
#             break
#         d_cur = manhattan(cur, goal)
#         better = [(manhattan(n, goal), n) for n in nbrs if manhattan(n, goal) < d_cur]
#         if not better:
#             break
#         better.sort(key=lambda x: x[0])
#         _, nxt = better[0]
#         cur = nxt
#         path.append(cur)
#         if cur == goal:
#             break
#
#     return path, {"steps": steps, "restarts": 0, "failures": 0}
#
#
# # ------------------------------------------------------------
# # 2) STOCHASTIC HILL-CLIMBING (basic)
# # ------------------------------------------------------------
# def stochastic_hill_climbing(grid, placement, start: Pos,
#                                    max_steps=2000, restarts=0) -> Tuple[List[Pos], Metrics]:
#     """
#     Stochastic hill climb: pick randomly among strictly improving neighbors.
#     """
#     goal = placement.office
#     cur = start
#     path = [cur]
#     steps = 0
#
#     for _ in range(max_steps):
#         steps += 1
#         if cur == goal:
#             break
#         nbrs = get_neighbors(grid, cur)
#         if not nbrs:
#             break
#         d_cur = manhattan(cur, goal)
#         improving = [n for n in nbrs if manhattan(n, goal) < d_cur]
#         if not improving:
#             break
#         nxt = random.choice(improving)
#         cur = nxt
#         path.append(cur)
#         if cur == goal:
#             break
#
#     return path, {"steps": steps, "restarts": 0, "failures": 0}
#
# #
# # ------------------------------------------------------------
# # 3) SIMULATED ANNEALING (basic)
# # ------------------------------------------------------------
# def simulated_annealing(grid, placement, start: Pos,
#                               max_steps=4000, t0=10.0, alpha=0.995, restarts=0) -> Tuple[List[Pos], Metrics]:
#     """
#     Standard Simulated Annealing over 4-neighbors using Manhattan distance.
#     """
#     goal = placement.office
#     cur = start
#     path = [cur]
#     steps = 0
#     T = float(t0)
#
#     for _ in range(max_steps):
#         steps += 1
#         if cur == goal:
#             break
#         if T <= 1e-12:
#             break
#         nbrs = get_neighbors(grid, cur)
#         if not nbrs:
#             break
#         nxt = random.choice(nbrs)
#         d_cur = manhattan(cur, goal)
#         d_nxt = manhattan(nxt, goal)
#         delta = d_nxt - d_cur
#         accept = False
#         if delta <= 0:
#             accept = True
#         else:
#             try:
#                 prob = math.exp(-delta / T)
#             except OverflowError:
#                 prob = 0.0
#             if random.random() < prob:
#                 accept = True
#         if accept:
#             cur = nxt
#             path.append(cur)
#             if cur == goal:
#                 break
#         T *= alpha
#
#     return path, {"steps": steps, "restarts": 0, "failures": 0}


# ---------------------------
# 4) HILL-CLIMBING w/ RANDOM RESTARTS (MAIN-only restarts)
# ---------------------------
# def hill_climbing(grid, placement, start: Pos,
#                   max_steps=3000) -> Tuple[List[Pos], Metrics]:
#     """
#     Pure greedy hill climbing:
#     - starts at the agent's actual start position
#     - moves only if Manhattan distance strictly decreases
#     - stops on plateau
#     """
#     goal = placement.office
#     cur = start
#     path = [cur]
#     steps = 0
#
#     for _ in range(max_steps):
#         steps += 1
#         if cur == goal:
#             break
#
#         nbrs = get_neighbors(grid, cur)
#         if not nbrs:
#             break
#
#         d_cur = manhattan(cur, goal)
#         better = [(manhattan(n, goal), n) for n in nbrs if manhattan(n, goal) < d_cur]
#
#         if not better:
#             break   # STOP — local optimum (plateau)
#
#         # choose best decreasing neighbour
#         better.sort(key=lambda x: x[0])
#         _, nxt = better[0]
#
#         cur = nxt
#         path.append(cur)
#
#     return path, {"steps": steps}
#
#
#
# # ------------------------------------------------------------
# # 5) STOCHASTIC w/ SIDEWAYS MOVES
# # ------------------------------------------------------------
# def stochastic_hill_climbing(grid, placement, start: Pos,
#                               max_steps=3000, max_sideways=40, restarts=0) -> Tuple[List[Pos], Metrics]:
#     """
#     Stochastic hill climb that allows sideways moves (equal-cost moves) up to a limit.
#     Sideways moves are chosen randomly among neighbours that do not improve distance.
#     """
#     goal = placement.office
#     cur = start
#     path = [cur]
#     steps = 0
#     sideways_used = 0
#
#     for _ in range(max_steps):
#         steps += 1
#         if cur == goal:
#             break
#         nbrs = get_neighbors(grid, cur)
#         if not nbrs:
#             break
#         d_cur = manhattan(cur, goal)
#         improving = [n for n in nbrs if manhattan(n, goal) < d_cur]
#         sideways = [n for n in nbrs if manhattan(n, goal) == d_cur]
#
#         if improving:
#             nxt = random.choice(improving)
#             cur = nxt
#             path.append(cur)
#             sideways_used = 0
#             continue
#
#         if sideways and sideways_used < max_sideways:
#             nxt = random.choice(sideways)
#             cur = nxt
#             path.append(cur)
#             sideways_used += 1
#             continue
#
#         # no improvement & sideways exhausted => stop
#         break
#
#     return path, {"steps": steps, "sideways_moves": sideways_used}
#
#
# # ------------------------------------------------------------
# # 6) SIMULATED ANNEALING w/ STAGNATION COUNTER + OSCILLATION GUARD
# # ------------------------------------------------------------
# def simulated_annealing(grid, placement, start: Pos,
#                                                max_steps=4000, t0=10.0, alpha=0.995,
#                                                stagnation_limit=200, oscillation_memory=16,
#                                                restarts=0) -> Tuple[List[Pos], Metrics]:
#     """
#     SA with:
#       - stagnation counter: if many neutral moves happen, we stop
# #       - oscillation guard: avoid repeating the same positions frequently
#    """
#     goal = placement.office
#     cur = start
#     path = [cur]
#     steps = 0
#     T = float(t0)
#
#     stagnation = 0
#     last_positions: List[Pos] = []
#     visited_counts: Dict[Pos, int] = {}
#
#     for _ in range(max_steps):
#         steps += 1
#         if cur == goal:
#             break
#         if T <= 1e-12:
#             break
#
#         nbrs = get_neighbors(grid, cur)
#         if not nbrs:
#             break
#
#         nxt = random.choice(nbrs)
#
#         # oscillation guard: skip move if it appears too often recently
#         if nxt in last_positions:
#             # try alternative neighbor if available
#             alt = [n for n in nbrs if n not in last_positions]
#             if alt:
#                 nxt = random.choice(alt)
#             else:
#                 # if all neighbors are in last_positions, just pick random but count as stagnation
#                 stagnation += 1
#
#         last_positions.append(nxt)
#         if len(last_positions) > oscillation_memory:
#             last_positions.pop(0)
#
#         d_cur = manhattan(cur, goal)
#         d_nxt = manhattan(nxt, goal)
#         delta = d_nxt - d_cur
#
#         accept = False
#         if delta <= 0:
#             accept = True
#         else:
#             try:
#                 prob = math.exp(-delta / max(T, 1e-12))
#             except OverflowError:
#                 prob = 0.0
#             if random.random() < prob:
#                 accept = True
#
#         if accept:
#             if d_nxt == d_cur:
#                 stagnation += 1
#             else:
#                 stagnation = 0
#
#             cur = nxt
#             path.append(cur)
#             visited_counts[cur] = visited_counts.get(cur, 0) + 1
#
#             if stagnation >= stagnation_limit:
#                 break
#
#             if cur == goal:
#                 break
#
#         T *= alpha
#
#     return path, {"steps": steps, "stagnation": stagnation, "osc_mem": len(last_positions)}


# ------------------------------------------------------------
# 7) HILL-CLIMBING w/ BACKTRACKING PENALTY, SIDEWAYS, TWO-STEP LOOKAHEAD, LOCAL ESCAPE
# (combined HC variant)
# ------------------------------------------------------------
def hill_climbing(grid, placement, start: Pos,
                                    max_steps=4000,
                                    backtrack_penalty=5,
                                    sideways_limit=30,
                                    visited_limit=16,
                                    restarts=0) -> Tuple[List[Pos], Metrics]:
    """
    Combined hill-climb variant which includes:
      - backtracking penalty (discourage immediate backtracking)
      - sideways moves (limited)
      - two-step lookahead detours
      - local escape moves (small uphill within +2)
      - visited window to avoid loops
    """
    goal = placement.office
    cur = start
    path = [cur]
    steps = 0
    last = None
    sideways_used = 0
    visited = []
    visited_counts: Dict[Pos, int] = {}
    max_space = 0

    def two_step_best(pos: Pos) -> Optional[Pos]:
        nbrs1 = get_neighbors(grid, pos)
        best_score = float('inf')
        best_step = None
        for s1 in nbrs1:
            for s2 in get_neighbors(grid, s1):
                score = manhattan(s2, goal)
                if score < best_score:
                    best_score = score
                    best_step = s1
        return best_step

    for _ in range(max_steps):
        steps += 1
        if cur == goal:
            break
        nbrs = get_neighbors(grid, cur)
        if not nbrs:
            break
        d_cur = manhattan(cur, goal)

        # score neighbors with backtrack penalty and visited penalty
        scored = []
        for n in nbrs:
            d = manhattan(n, goal)
            if last is not None and n == last:
                d += backtrack_penalty
            # discourage revisited squares
            d += visited_counts.get(n, 0)
            scored.append((d, n))

        scored.sort(key=lambda x: x[0])

        # pick best non-recent (try to avoid immediate loop)
        best = None
        for dist, npos in scored:
            if npos not in visited:
                best = npos
                best_d = dist
                break
        if best is None:
            best_d, best = scored[0]

        best_manhattan = manhattan(best, goal)

        # improvement move
        if best_manhattan < d_cur:
            sideways_used = 0
            last = cur
            visited.append(cur)
            visited_counts[cur] = visited_counts.get(cur, 0) + 1
            max_space = max(max_space, len(visited))
            if len(visited) > visited_limit:
                visited.pop(0)
            cur = best
            path.append(cur)
            continue

        # sideways allowed
        if best_manhattan == d_cur and sideways_used < sideways_limit and random.random() < 0.35:
            sideways_used += 1
            last = cur
            visited.append(cur)
            visited_counts[cur] = visited_counts.get(cur, 0) + 1
            max_space = max(max_space, len(visited))
            if len(visited) > visited_limit:
                visited.pop(0)
            cur = best
            path.append(cur)
            continue

        # two-step lookahead detour
        detour = two_step_best(cur)
        if detour and detour != cur and detour not in visited:
            last = cur
            visited.append(cur)
            visited_counts[cur] = visited_counts.get(cur, 0) + 1
            max_space = max(max_space, len(visited))
            if len(visited) > visited_limit:
                visited.pop(0)
            cur = detour
            path.append(cur)
            continue

        # controlled small uphill escape (within +2)
        safe = [n for n in nbrs if manhattan(n, goal) <= d_cur + 2 and n != last]
        if safe:
            nxt = random.choice(safe)
            last = cur
            visited.append(cur)
            visited_counts[cur] = visited_counts.get(cur, 0) + 1
            max_space = max(max_space, len(visited))
            if len(visited) > visited_limit:
                visited.pop(0)
            cur = nxt
            path.append(cur)
            continue

        # try to break simple oscillation A-B-A-B by taking random alternative
        if len(path) >= 4 and path[-1] == path[-3] and path[-2] == path[-4]:
            cand = [n for n in nbrs if n != path[-2]]
            if cand:
                nxt = random.choice(cand)
                last = cur
                visited.append(cur)
                visited_counts[cur] = visited_counts.get(cur, 0) + 1
                max_space = max(max_space, len(visited))
                if len(visited) > visited_limit:
                    visited.pop(0)
                cur = nxt
                path.append(cur)
                continue

        # stuck
        break

    if not path:
        path = [start]
    if path[0] != start:
        path = [start] + path

    return path, {"steps": steps, "space": max_space, "sideways": sideways_used}


# ------------------------------------------------------------
# 8) STOCHASTIC HILL-CLIMBING w/ RANDOM RESTARTS, 2-STEP LOOKAHEAD,
#    RANDOM UPHILL MOVES, LOOP ESCAPE, OSCILLATION BREAK
# ------------------------------------------------------------
def stochastic_hill_climbing(grid, placement, start: Pos,
                                      max_steps=4000, restarts=6,
                                      visited_limit=12) -> Tuple[List[Pos], Metrics]:
    """
    Enhanced stochastic hill-climb that:
      - runs one primary attempt from 'start'
      - then performs several random-restart attempts (picked inside MAIN)
      - each run uses:
          * stochastic improving moves
          * 2-step lookahead detours
          * occasional random uphill moves (small escapes)
          * loop escapes (if a tile is visited too often)
          * oscillation breaking (A-B-A-B)
    Keeps best trial (closest to goal).
    """
    goal = placement.office
    total_steps = 0
    max_space = 0
    best_path: List[Pos] = [start]
    best_dist = manhattan(start, goal)

    def run_once(start_pos):
        nonlocal total_steps, max_space
        cur = start_pos
        last = None
        path = [cur]
        visited = {}
        visited_list: List[Pos] = []

        for _ in range(max_steps):
            total_steps += 1
            if cur == goal:
                break

            visited[cur] = visited.get(cur, 0) + 1
            visited_list.append(cur)
            max_space = max(max_space, len(visited_list))
            if visited[cur] >= 5:
                # loop escape: pick a random neighbor that isn't last
                nbrs = get_neighbors(grid, cur)
                random.shuffle(nbrs)
                for n in nbrs:
                    total_steps += 1
                    if n != last and is_walkable(grid, n[0], n[1]):
                        last, cur = cur, n
                        path.append(cur)
                        break
                continue

            nbrs = get_neighbors(grid, cur)
            if not nbrs:
                break

            d_cur = manhattan(cur, goal)

            # strictly improving neighbors
            improving = [n for n in nbrs if manhattan(n, goal) < d_cur]

            filtered = [n for n in improving if visited.get(n, 0) < 3] or improving

            if filtered:
                non_back = [n for n in filtered if n != last]
                nxt = random.choice(non_back or filtered)
                last, cur = cur, nxt
                path.append(cur)
                continue

            # 2-step lookahead
            best_score = float('inf')
            detour = None
            for s1 in nbrs:
                if visited.get(s1, 0) > 3:
                    continue
                for s2 in get_neighbors(grid, s1):
                    sc = manhattan(s2, goal)
                    if sc < best_score:
                        best_score = sc
                        detour = s1
            if detour:
                last, cur = cur, detour
                path.append(cur)
                continue

            # occasional small random uphill escape
            if random.random() < 0.25:
                cand = [n for n in nbrs if n != last]
                if cand:
                    nxt = random.choice(cand)
                    last, cur = cur, nxt
                    path.append(cur)
                    continue

            # oscillation break (A-B-A-B)
            if len(path) >= 4 and path[-1] == path[-3] and path[-2] == path[-4]:
                cand = [n for n in nbrs if n != path[-2]]
                if cand:
                    nxt = random.choice(cand)
                    last, cur = cur, nxt
                    path.append(cur)
                    continue

            break

        return path

    # primary run from start
    primary = run_once(start)
    primary_dist = manhattan(primary[-1], goal) if primary else float('inf')
    best_path = primary
    best_dist = primary_dist

    # restarts inside MAIN only
    candidates = [(x, y) for y in range(len(grid)) for x in range(len(grid[0]))
                  if is_walkable(grid, x, y) and is_in_main(x, y)]
    if not candidates:
        candidates = [start]

    for r in range(restarts):
        picked = random.choice(candidates)
        trial = run_once(picked)
        trial_d = manhattan(trial[-1], goal) if trial else float('inf')
        if trial and trial_d < best_dist:
            best_path = trial
            best_dist = trial_d

    # ensure start leads the path
    if best_path and best_path[0] != start:
        best_path = [start] + [p for p in best_path if p != start]

    return best_path, {"steps": total_steps, "restarts": restarts, "space": max_space}


# ------------------------------------------------------------
# 9) SIMULATED ANNEALING — FULL (stagnation counter, oscillation guard, flexible cooling)
# ------------------------------------------------------------
def simulated_annealing(grid, placement, start: Pos,
                             max_steps=6000, t0=15.0, alpha=0.995,
                             stagnation_limit=250, oscillation_memory=20,
                             cooling_schedule: str = "exp") -> Tuple[List[Pos], Metrics]:
    """
    Full-featured SA combining:
      - stagnation counter & visited frequency cutoff
      - oscillation guard (memory of recent positions)
      - selectable cooling schedule: 'exp' (geometric), 'linear', or 'adaptive'
    """
    goal = placement.office
    cur = start
    path = [cur]
    steps = 0
    T = float(t0)

    stagnation = 0
    visited = {}
    last_positions: List[Pos] = []

    def update_temperature(t, step):
        if cooling_schedule == "exp":
            return t * alpha
        if cooling_schedule == "linear":
            return max(1e-12, t - (t0 * (1.0 / max_steps)))
        if cooling_schedule == "adaptive":
            # reduce faster when stagnating
            factor = alpha ** (1 + stagnation / 50.0)
            return max(1e-12, t * factor)
        # default fallback
        return t * alpha

    for i in range(max_steps):
        steps += 1
        if cur == goal:
            break
        if T <= 1e-12:
            break

        nbrs = get_neighbors(grid, cur)
        if not nbrs:
            break

        # avoid immediate backtracking candidate when possible
        options = [n for n in nbrs if n != (path[-2] if len(path) >= 2 else None)]
        if not options:
            options = nbrs

        nxt = random.choice(options)

        # oscillation guard: if nxt appears often in recent sequence, prefer alternative
        if nxt in last_positions:
            alt = [n for n in options if n not in last_positions]
            if alt:
                nxt = random.choice(alt)

        last_positions.append(nxt)
        if len(last_positions) > oscillation_memory:
            last_positions.pop(0)

        d_cur = manhattan(cur, goal)
        d_nxt = manhattan(nxt, goal)
        delta = d_nxt - d_cur

        accept = False
        if delta <= 0:
            accept = True
        else:
            try:
                prob = math.exp(-delta / max(T, 1e-12))
            except OverflowError:
                prob = 0.0
            if random.random() < prob:
                accept = True

        if accept:
            if d_nxt == d_cur:
                stagnation += 1
            else:
                stagnation = 0

            visited[cur] = visited.get(cur, 0) + 1
            cur = nxt
            path.append(cur)

            if visited.get(cur, 0) > 12:
                # too revisited -> break as stagnation
                break

            if stagnation >= stagnation_limit:
                break

            if cur == goal:
                break

        # update temperature by chosen schedule
        T = update_temperature(T, i)

    # final cleaning
    cleaned = []
    for p in path:
        if not cleaned or cleaned[-1] != p:
            cleaned.append(p)
    if not cleaned:
        cleaned = [start]
    if cleaned[0] != start:
        cleaned = [start] + cleaned

    return cleaned, {"steps": steps, "stagnation": stagnation, "osc_mem": len(last_positions), "t_final": T}


# ------------------------------------------------------------
# run_with_metrics — fallback helper for controller compatibility
# kept minimal (controller prefers to use sa.run_with_metrics if available)
# ------------------------------------------------------------
def run_with_metrics(grid, placement, path, start_points, start_time):
    results = []
    for (x, y) in path:
        results.append({
            "pos": (x, y),
            "score": start_points,
            "timer": start_time,
            "time": start_time,
            "reason": "normal"
        })
    return results

# ------------------------------------------------------------
# run_with_metrics for batch_runner.py
# uncomment only when running batch_runner.py
# ------------------------------------------------------------

# def run_with_metrics(grid, placement, path, start_points, start_time):
#     """
#     Reconstruct a *synthetic* per-step metric trace for batch_runner output.
#
#     This function is **not** used by the interactive UI and **not** used for
#     the real simulation loop inside the controller. It is exclusively used by
#     the batch_runner to reinterpret an algorithm-produced path and convert it
#     into a step-by-step record suitable for CSV export (score, time, reason).
#
#     Its purpose is to give the batch runner a consistent, controller-like
#     interpretation of movement effects **without running the UI engine**.
#     In other words, it emulates the controller’s cost rules so that offline
#     runs produce correct and comparable CSVs.
#
#     Returned trace:
#         A list of dicts, one entry per simulated step:
#         {
#             "pos": (x, y),
#             "score": int,
#             "timer": int,
#             "reason": str,
#         }
#
#     Interpretation rules (mirrors controller.fallback_run_with_metrics):
#         • Each step applies a base movement cost:
#               timer -= 1
#               score -= 1
#         • Stepping on world.ANGRY costs an additional -150 (reason="angry")
#         • Stepping on world.CHAIR immediately zeroes score (reason="chair")
#         • Stepping on placement.office or world.OFFICE marks reason="goal"
#         • score <= 0 → stop, last step reason="no_points"
#         • timer <= 0 → stop, last step reason="no_time"
#
#     Additional notes:
#         • Path entries may be tuples or dicts; coordinates are extracted
#           defensively and clamped to grid bounds.
#         • If the provided path is empty or all steps are invalid, the trace
#           falls back to a single record at the starting tile.
#         • This function does *not* simulate collisions, animations or
#           multi-agent rules — it only produces a metric timeline for CSV.
#     """
#     trace = []
#     score = int(start_points)
#     timer = int(start_time)

#     if not path:
#         sx, sy = placement.start
#         return [{"pos": (sx, sy), "score": score, "timer": timer, "reason": "done"}]

#     for p in path:
#         try:
#             if isinstance(p, dict):
#                 pos = p.get("pos") or p.get("position") or p.get("p")
#                 if pos and isinstance(pos, (list, tuple)):
#                     x, y = int(pos[0]), int(pos[1])
#                 else:
#                     x, y = int(p.get("x", placement.start[0])), int(p.get("y", placement.start[1]))
#             else:
#                 x, y = int(p[0]), int(p[1])
#         except Exception:
#             continue

#         if y < 0 or y >= len(grid) or x < 0 or x >= len(grid[0]):
#             continue

#         timer = max(0, timer - 1)
#         score = max(0, score - 1)

#         reason = "normal"
#         cell = grid[y][x]

#         try:
#             if cell == world.ANGRY:
#                 score = max(0, score - 150)
#                 reason = "angry"
#             if cell == world.CHAIR:
#                 score = 0
#                 reason = "chair"
#             if (x, y) == getattr(placement, "office", None) or cell == world.OFFICE:
#                 reason = "goal"
#         except Exception:
#             pass

#         trace.append({"pos": (x, y), "score": score, "timer": timer, "reason": reason})

#         if reason in ("chair", "goal") or score <= 0 or timer <= 0:
#             # if reason was set by office/chair/angry and should terminate, break
#             # ensure final reason is descriptive for CSV
#             if score <= 0 and reason not in ("chair", "goal"):
#                 trace[-1]["reason"] = "no_points"
#             if timer <= 0 and reason not in ("chair", "goal"):
#                 trace[-1]["reason"] = "no_time"
#             break

#     if not trace:
#         sx, sy = placement.start
#         trace.append({"pos": (sx, sy), "score": start_points, "timer": start_time, "reason": "done"})

#     return trace
