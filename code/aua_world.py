"""aua_world.py — World generation for The OH Race Project.

This module defines:
- World geometry (Main, PAB, Bridge)
- Cell IDs and Grid structure
- Placement dataclass storing special locations
- Helper functions (neighbors, BFS, coordinate transforms)
- The world builder that creates a valid, solvable map according to CONFIG

The logic is kept identical to the original version; only formatting,
documentation, and comment cleanup were performed.
"""

from __future__ import annotations
import random
from typing import List, Tuple, Set, Dict, Optional, Iterable
from dataclasses import dataclass

# ----------------------------
# World geometry (base defaults)
# (MAIN_W and PAB_W updated dynamically in build_world via CONFIG)
# ----------------------------
MAIN_W, MAIN_H = 10, 7
PAB_W, PAB_H = 7, 5
BRIDGE_LEN = 3
WORLD_W = MAIN_W + BRIDGE_LEN + PAB_W
WORLD_H = MAIN_H

BRIDGE_ROW = 3
PAB_ROW_OFFSET = 2  # local PAB rows 0..4 → world rows 2..6

BRIDGE_ENTRANCE_MAIN: Tuple[int, int] = (MAIN_W - 1, BRIDGE_ROW)
BRIDGE_ENTRANCE_PAB: Tuple[int, int] = (MAIN_W + BRIDGE_LEN, BRIDGE_ROW)

# ----------------------------
# Cell IDs
# ----------------------------
EMPTY = 0
WALL = 1
BRIDGE = 2
ANGRY = 3
CHAIR = 4
OFFICE = 5
START = 9  # overlay only

Cell = int
Grid = List[List[Cell]]
Pos = Tuple[int, int]


@dataclass
class Placement:
    start: Pos
    walls_main: Set[Pos]
    walls_pab: Set[Pos]
    angry_main: Set[Pos]
    angry_pab: Set[Pos]
    chair: Pos
    office: Pos
    bridge: Set[Pos]


# ----------------------------
# Coordinate helpers
# ----------------------------
def pab_local_to_world(px: int, py: int) -> Pos:
    """Convert PAB-local coords to world coords."""
    return (MAIN_W + BRIDGE_LEN + px, PAB_ROW_OFFSET + py)


def all_main_cells() -> List[Pos]:
    return [(x, y) for x in range(MAIN_W) for y in range(MAIN_H)]


def all_pab_cells() -> List[Pos]:
    return [pab_local_to_world(x, y) for x in range(PAB_W) for y in range(PAB_H)]


def bridge_cells() -> Set[Pos]:
    return {(c, BRIDGE_ROW) for c in range(MAIN_W, MAIN_W + BRIDGE_LEN)}


def empty_world() -> Grid:
    return [[EMPTY for _ in range(WORLD_W)] for _ in range(WORLD_H)]


def neighbors4(p: Pos) -> Iterable[Pos]:
    x, y = p
    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        nx, ny = x + dx, y + dy
        if 0 <= nx < WORLD_W and 0 <= ny < WORLD_H:
            yield (nx, ny)


def bfs_path_exists(grid: Grid, start: Pos, goal: Pos, blocked: Set[int]) -> bool:
    """Check for a valid BFS path avoiding blocked cell types."""
    from collections import deque

    q = deque([start])
    seen = {start}

    while q:
        x, y = q.popleft()
        if (x, y) == goal:
            return True
        for nx, ny in neighbors4((x, y)):
            if (nx, ny) in seen:
                continue
            if grid[ny][nx] in blocked:
                continue
            seen.add((nx, ny))
            q.append((nx, ny))
    return False


def sample_unique(
    candidates: List[Pos],
    k: int,
    rng: random.Random,
    exclude: Set[Pos],
) -> Set[Pos]:
    """Sample k unique positions from candidates minus exclude set."""
    pool = [c for c in candidates if c not in exclude]
    if len(pool) < k:
        raise RuntimeError("Not enough free cells to sample.")
    rng.shuffle(pool)
    return set(pool[:k])


# ----------------------------
# World builder
# ----------------------------
def build_world(
    seed: Optional[int] = None,
    max_tries: int = 10_000
) -> Tuple[Grid, Placement]:
    """Generate a valid world satisfying all constraints required by the project:
    - Dynamic MAIN_W / PAB_W and obstacle counts from CONFIG
    - Safe 2-row corridor inside Main leading toward bridge entrance
    - Paths guaranteed:
        Start → Bridge entrance
        Start → Office
    """
    from aua_setup import CONFIG

    global MAIN_W, PAB_W, WORLD_W, WORLD_H
    global BRIDGE_ENTRANCE_MAIN, BRIDGE_ENTRANCE_PAB

    # Update geometry from CONFIG
    MAIN_W = int(CONFIG["main_w"])
    PAB_W = int(CONFIG["pab_w"])
    WORLD_W = MAIN_W + BRIDGE_LEN + PAB_W
    WORLD_H = MAIN_H

    BRIDGE_ENTRANCE_MAIN = (MAIN_W - 1, BRIDGE_ROW)
    BRIDGE_ENTRANCE_PAB = (MAIN_W + BRIDGE_LEN, BRIDGE_ROW)

    # Counts from config
    walls_main_n = int(CONFIG["walls_main"])
    walls_pab_n = int(CONFIG["walls_pab"])
    angry_main_n = int(CONFIG["angry_main"])
    angry_pab_n = int(CONFIG["angry_pab"])

    main_cells = all_main_cells()
    pab_cells = all_pab_cells()
    bridge = bridge_cells()

    rng = random.Random(seed)
    forbidden_bridge = set(bridge) | {BRIDGE_ENTRANCE_MAIN, BRIDGE_ENTRANCE_PAB}

    for _ in range(max_tries):
        grid = empty_world()

        # Mark bridge cells
        for bx, by in bridge:
            grid[by][bx] = BRIDGE

        # Choose start in Main
        start_candidates = [c for c in main_cells if c not in forbidden_bridge]
        if not start_candidates:
            raise RuntimeError("No valid start positions in Main.")
        start = rng.choice(start_candidates)

        # Build safe 2-row corridor toward Main-side bridge entrance
        safe_corridor = set()
        x0, y0 = start

        corridor_rows = {y0}
        if y0 + 1 < MAIN_H:
            corridor_rows.add(y0 + 1)
        elif y0 - 1 >= 0:
            corridor_rows.add(y0 - 1)

        for x in range(x0, MAIN_W):
            for ry in corridor_rows:
                if 0 <= ry < MAIN_H:
                    safe_corridor.add((x, ry))

        # Walls in Main
        try:
            walls_main = sample_unique(
                main_cells,
                walls_main_n,
                rng,
                exclude=forbidden_bridge | {start} | safe_corridor,
            )
        except RuntimeError:
            continue

        for x, y in walls_main:
            grid[y][x] = WALL

        # Walls in PAB
        try:
            walls_pab = sample_unique(
                pab_cells,
                walls_pab_n,
                rng,
                exclude=forbidden_bridge,
            )
        except RuntimeError:
            continue

        for x, y in walls_pab:
            grid[y][x] = WALL

        # Bridge entrances must remain open
        if grid[BRIDGE_ROW][BRIDGE_ENTRANCE_MAIN[0]] == WALL:
            continue
        if grid[BRIDGE_ROW][BRIDGE_ENTRANCE_PAB[0]] == WALL:
            continue

        # Angry in Main
        occupied_main = set(walls_main) | {start} | bridge | {BRIDGE_ENTRANCE_MAIN}
        try:
            angry_main = sample_unique(
                main_cells,
                angry_main_n,
                rng,
                exclude=occupied_main | safe_corridor,
            )
        except RuntimeError:
            continue

        for x, y in angry_main:
            grid[y][x] = ANGRY

        # PAB Office, Chair, Angry
        occupied_pab = set(walls_pab) | bridge | {BRIDGE_ENTRANCE_PAB}

        def adj_bad(wx: int, wy: int) -> bool:
            """True if (wx,wy) is adjacent to WALL or ANGRY."""
            for nx, ny in ((wx + 1, wy), (wx - 1, wy), (wx, wy + 1), (wx, wy - 1)):
                if 0 <= nx < WORLD_W and 0 <= ny < WORLD_H:
                    if grid[ny][nx] in (WALL, ANGRY):
                        return True
            return False

        pab_entrance_x = MAIN_W + BRIDGE_LEN
        pab_candidates = [
            p for p in pab_cells
            if p not in occupied_pab and p[0] != pab_entrance_x
        ]
        rng.shuffle(pab_candidates)

        # Office
        chosen_office = None
        for ox, oy in pab_candidates:
            if grid[oy][ox] != EMPTY:
                continue
            if adj_bad(ox, oy):
                continue
            chosen_office = (ox, oy)
            break
        if chosen_office is None:
            continue

        occ = {chosen_office}

        # Chair
        chair_candidates = [
            p for p in pab_candidates
            if p not in occ and grid[p[1]][p[0]] == EMPTY
        ]
        if not chair_candidates:
            continue
        chosen_chair = rng.choice(chair_candidates)
        occ.add(chosen_chair)

        # Angry in PAB
        ox, oy = chosen_office
        pab_free = [
            p for p in pab_candidates
            if p not in occ
            and grid[p[1]][p[0]] == EMPTY
            and abs(p[0] - ox) + abs(p[1] - oy) != 1
        ]
        if len(pab_free) < angry_pab_n:
            continue

        rng.shuffle(pab_free)
        chosen_angry_pab = pab_free[:angry_pab_n]

        # Paint PAB elements
        grid[chosen_office[1]][chosen_office[0]] = OFFICE
        grid[chosen_chair[1]][chosen_chair[0]] = CHAIR
        for ax, ay in chosen_angry_pab:
            grid[ay][ax] = ANGRY

        # Path checks
        if not bfs_path_exists(grid, start, BRIDGE_ENTRANCE_MAIN, blocked={WALL, CHAIR, ANGRY}):
            continue
        if not bfs_path_exists(grid, start, chosen_office, blocked={WALL, CHAIR, ANGRY}):
            continue

        placement = Placement(
            start=start,
            walls_main=set(walls_main),
            walls_pab=set(walls_pab),
            angry_main=set(angry_main),
            angry_pab=set(chosen_angry_pab),
            chair=chosen_chair,
            office=chosen_office,
            bridge=bridge,
        )
        return grid, placement

    raise RuntimeError("Failed to generate a solvable world with corridor.")


# ----------------------------
# ASCII preview (for debugging)
# ----------------------------
SYMBOLS = {
    EMPTY: '.',
    WALL: '#',
    BRIDGE: '=',
    ANGRY: 'A',
    CHAIR: 'P',
    OFFICE: 'O',
}


def render_ascii(grid: Grid, placement: Placement) -> str:
    """Render the grid as ASCII, overlaying the start position."""
    overlay: Dict[Pos, str] = {placement.start: 'S'}
    rows = []
    for y in reversed(range(WORLD_H)):
        line = []
        for x in range(WORLD_W):
            if (x, y) in overlay:
                ch = overlay[(x, y)]
            else:
                ch = SYMBOLS.get(grid[y][x], '?')
            line.append(ch)
        rows.append(' '.join(line))
    return '\n'.join(rows)


if __name__ == "__main__":
    g, pl = build_world(seed=42)
    print(render_ascii(g, pl))
    print("\nPlacements:")
    print(" Start:", pl.start)
    print(" Walls(Main):", len(pl.walls_main))
    print(" Walls(PAB):", len(pl.walls_pab))
    print(" Angry(Main):", len(pl.angry_main))
    print(" Angry(PAB):", len(pl.angry_pab))
    print(" Chair:", pl.chair)
    print(" Office:", pl.office)
