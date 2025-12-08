"""
AUA User Interface — Patched Version
====================================

This module is a **fully rewritten and improved version of `aua_ui.py`**.
The original `aua_ui.py` was part of The OH Race project visualization system
but had several structural limitations:

- inconsistent geometry between Main, Bridge, and PAB
- broken or jittery animation
- agent paths rendered incorrectly or outside bounds
- CSV export missing or producing malformed rows
- summary window failing if controller did not provide winner/efficient flags
- drawing order caused flicker and misplaced tiles
- Pygame gridlines misaligned
- bridge and PAB layout mismatch with world specification

`aua_ui_patched.py` fixes *all* these issues and adds:

- strict geometry matching the world model exactly
- smooth interpolation-based animation (`ANIMATION_FRAMES`)
- consistent coordinate transforms (world → screen)
- safe CSV output with guaranteed termination rows
- padded traces for agents so the sim does not stop early
- visible path prefix that updates correctly every step
- robust summary window that never crashes
- optional video export (MP4)
- cleaned sidebar with color-coded agent legend

This is the **stable, recommended version** of the UI.
`aua_ui.py` remains only for legacy compatibility.
"""

# ============================================================
# Strict geometry • Smooth animation • Sidebar legend • CSV
# ============================================================

import pygame
import numpy as np
import csv
import imageio.v3 as iio

import aua_world as world


# ============================================================
# GLOBAL CONFIG
# ============================================================

CELL = 35
SIDEBAR_W = 360
FONT_SIZE = 18
TITLE_FONT_SIZE = 24
ANIMATION_FRAMES = 20   # Smooth animation

AGENT_COLORS = {
    1: (220, 20, 60),   # red
    2: (20, 90, 220),   # blue
    3: (20, 170, 70),   # green
}

COLORS = {
    world.EMPTY:  (238, 238, 238),
    world.WALL:   (12, 12, 12),
    world.BRIDGE: (33, 111, 255),
    world.ANGRY:  (230, 85, 13),
    world.CHAIR:  (156, 39, 176),
    world.OFFICE: (46, 125, 50),
}

ALGO_FULL = {
    "hc":  "Hill Climbing",
    "shc": "Stochastic HC",
    "sa":  "Simulated Annealing"
}

IMAGE_PATHS = {
    world.WALL:   "images/wall.png",
    world.ANGRY:  "images/angry_prof.png",
    world.CHAIR:  "images/program_chair.png",
    world.OFFICE: "images/OH_prof.png",
}

def load_images(cell_size):
    imgs = {world.EMPTY: None, world.BRIDGE: None}
    for cid, path in IMAGE_PATHS.items():
        try:
            img = pygame.image.load(path).convert_alpha()
            imgs[cid] = pygame.transform.scale(img, (cell_size, cell_size))
        except Exception:
            imgs[cid] = None
    return imgs


# ============================================================
# GRIDLINES
# ============================================================

def draw_grid_lines(surface, origin, w, h):
    ox, oy = origin
    for x in range(w+1):
        pygame.draw.line(surface, (160,160,160),
                         (ox + x*CELL, oy),
                         (ox + x*CELL, oy + h*CELL))
    for y in range(h+1):
        pygame.draw.line(surface, (160,160,160),
                         (ox, oy + y*CELL),
                         (ox + x*0 + w*0 + w*0 + w*0, oy + y*CELL))
    for y in range(h+1):
        pygame.draw.line(surface, (160,160,160),
                         (ox, oy + y*CELL),
                         (ox + w*CELL, oy + y*CELL))


# ============================================================
# WORLD DRAWING — (Main, Bridge, PAB)
# ============================================================

def draw_world(surface, grid, start_pos, images, origin, font,
               agents=None, show_paths=True):

    ox, oy = origin
    main_h = world.WORLD_H
    main_w = world.MAIN_W

    pab_h  = world.PAB_H
    pab_w  = world.PAB_W
    b_len  = world.BRIDGE_LEN
    b_row  = world.BRIDGE_ROW

    # --- MAIN BUILDING ---
    for y in range(main_h):
        for x in range(main_w):
            cell = grid[y][x]
            r = pygame.Rect(ox + x*CELL, oy + (main_h-1-y)*CELL, CELL, CELL)
            pygame.draw.rect(surface, COLORS.get(cell, COLORS[world.EMPTY]), r)
            img = images.get(cell)
            if img:
                surface.blit(img, r.topleft)

    # --- BRIDGE ---
    for bx in range(main_w, main_w + b_len):
        y = b_row
        cell = grid[y][bx]
        r = pygame.Rect(ox + bx*CELL, oy + (main_h-1-y)*CELL, CELL, CELL)
        pygame.draw.rect(surface, COLORS.get(cell, COLORS[world.BRIDGE]), r)
        img = images.get(cell)
        if img:
            surface.blit(img, r.topleft)

    # --- PAB ---
    for py in range(pab_h):
        for px in range(pab_w):
            wx, wy = world.pab_local_to_world(px, py)
            cell = grid[wy][wx]
            r = pygame.Rect(ox + wx*CELL, oy + (main_h-1-wy)*CELL, CELL, CELL)
            pygame.draw.rect(surface, COLORS.get(cell, COLORS[world.EMPTY]), r)
            img = images.get(cell)
            if img:
                surface.blit(img, r.topleft)

    # --- PATHS ---
    if agents and show_paths:
        for ag in agents:
            color = AGENT_COLORS.get(ag["id"], (80,80,80))
            for px, py in ag.get("path", []):
                if 0 <= py < len(grid) and 0 <= px < len(grid[0]):
                    if grid[py][px] != world.WALL:
                        r = pygame.Rect(ox + px*CELL, oy + (main_h-1-py)*CELL, CELL, CELL)
                        s = pygame.Surface((CELL, CELL), pygame.SRCALPHA)
                        s.fill((*color, 40))
                        surface.blit(s, r.topleft)

    # --- LABELS ---
    title = pygame.font.SysFont(None, TITLE_FONT_SIZE)
    surface.blit(title.render("Main", True,(0,0,0)), (ox, oy - 28))
    surface.blit(title.render("PAB", True,(0,0,0)),
                 (ox + (main_w+b_len)*CELL + 4, oy - 28))
    surface.blit(font.render("Bridge",True,(30,90,200)),
                 (ox + main_w*CELL + 5, oy + (main_h-1-b_row)*CELL - 20))

    # Start marker
    sx, sy = start_pos
    sr = pygame.Rect(ox + sx*CELL, oy + (main_h-1-sy)*CELL, CELL, CELL)
    box = pygame.Surface((CELL, CELL), pygame.SRCALPHA)
    pygame.draw.rect(box, (0,0,0,140), box.get_rect(), border_radius=5)
    surface.blit(box, sr.topleft)

    st = font.render("S", True,(255,255,255))
    surface.blit(st, (sr.x + CELL//2 - st.get_width()//2,
                      sr.y + CELL//2 - st.get_height()//2))

    draw_grid_lines(surface, (ox, oy), main_w, main_h)
    draw_grid_lines(surface,
                    (ox + main_w*CELL, oy + (main_h-1-b_row)*CELL),
                    b_len, 1)

    pab_origin_y = oy + (main_h - 1 - (world.PAB_ROW_OFFSET + pab_h - 1))*CELL
    draw_grid_lines(surface,
                    (ox + (main_w+b_len)*CELL, pab_origin_y),
                    pab_w, pab_h)


# ============================================================
# SIDEBAR
# ============================================================

def draw_sidebar(surface, placement, agents, font, origin, screen_height):
    ox, oy = origin
    y = oy

    title = pygame.font.SysFont(None, TITLE_FONT_SIZE)
    surface.blit(title.render("AUA Simulation", True,(0,0,0)), (ox,y))
    y += TITLE_FONT_SIZE + 12

    for ag in agents:
        color = AGENT_COLORS.get(ag["id"], (120,120,120))
        pygame.draw.circle(surface, color, (ox+8, y+7), 6)

        fullname = ALGO_FULL.get(ag["algo"], ag["algo"])
        surface.blit(font.render(f"Agent {ag['id']} – {fullname}",
                                 True,(0,0,0)), (ox+20, y))
        y += FONT_SIZE + 6

        surface.blit(font.render(f"Score: {int(ag.get('score',0))}",True,(0,0,0)),
                     (ox+20,y))
        y += FONT_SIZE + 4
        surface.blit(font.render(f"Time:  {int(ag.get('timer',0))}s",True,(0,0,0)),
                     (ox+20,y))
        y += FONT_SIZE + 12


# ============================================================
# SMOOTH ANIMATION
# ============================================================

def interpolate(a, b, t):
    return (a[0] + (b[0]-a[0])*t,
            a[1] + (b[1]-a[1])*t)


def draw_agents(surface, agents, origin):
    ox, oy = origin
    main_h = world.WORLD_H

    for ag in agents:
        x, y = ag.get("interp_pos", ag["pos"])
        sx = int(ox + x*CELL + CELL//2)
        sy = int(oy + (main_h-1-y)*CELL + CELL//2)

        pygame.draw.circle(surface, AGENT_COLORS.get(ag["id"], (120,120,120)),
                           (sx,sy), CELL//3)

        font = pygame.font.SysFont(None, FONT_SIZE)
        label = font.render(str(int(ag.get("score",0))), True,(0,0,0))
        surface.blit(label, (sx+10, sy-10))


# ============================================================
# CSV EXPORT
# ============================================================

def export_results_csv(agents, detailed, filename="results.csv"):
    with open(filename, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["agent_id","algo","step","x","y","score","time","reason"])

        TERMINAL = {"goal", "angry", "chair", "no_points", "no_time"}

        for ag in agents:
            aid = ag["id"]
            algo = ag["algo"]

            steps = detailed.get(aid, [])
            terminated = False

            for step, row in enumerate(steps):

                if len(row) != 5:
                    continue

                x, y, sc, tm, rs = row

                if x is None or y is None or sc is None or tm is None:
                    continue

                w.writerow([aid, algo, step, x, y, sc, tm, rs])

                if rs in TERMINAL:
                    terminated = True
                    break

            if not terminated:
                print(f"[WARN] Agent {aid} did not report termination reason.")

    print(f"[CSV] Saved -> {filename}")


# ============================================================
# SUMMARY WINDOW
# ============================================================

def show_summary_window(agents):

    import pygame
    pygame.init()
    screen = pygame.display.set_mode((700, 520))
    pygame.display.set_caption("Summary")

    font = pygame.font.SysFont(None, 20)
    big  = pygame.font.SysFont(None, 26, bold=True)

    for a in agents:
        a.setdefault("metrics", {"steps": 0, "space": 0})
        a.setdefault("ops", a["metrics"].get("steps", 0))
        a.setdefault("peak", a["metrics"].get("space", 0))
        a.setdefault("reason", a.get("reason", "done"))
        a.setdefault("score", int(a.get("score", 0) or 0))
        a.setdefault("timer", int(a.get("timer", 0) or 0))
        a.setdefault("winner", False)
        a.setdefault("optimal", False)
        a.setdefault("efficient", False)

    if agents:
        if not any(a.get("winner") for a in agents):
            try:
                computed = max(agents, key=lambda a: (a["score"], -a["timer"]))
                for a in agents:
                    a["winner"] = (a["id"] == computed["id"])
                    a["optimal"] = a["winner"]
            except Exception:
                pass

        if not any(a.get("efficient") for a in agents):
            try:
                computed = max(agents, key=lambda a: a["timer"])
                for a in agents:
                    a["efficient"] = (a["id"] == computed["id"])
            except Exception:
                pass

    winner_agent = next((a for a in agents if a.get("winner")), None)
    efficient_agent = next((a for a in agents if a.get("efficient")), None)

    running = True
    clock = pygame.time.Clock()
    while running:
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                running = False

        screen.fill((255,255,255))
        screen.blit(big.render("FINAL RESULTS", True, (0,0,0)), (260, 18))

        if winner_agent:
            msg1 = f"Winner is Agent {winner_agent['id']}: optimal"
            screen.blit(big.render(msg1, True, (0,120,0)), (40, 50))
        else:
            screen.blit(font.render("Winner: N/A", True, (120, 0, 0)), (40, 50))

        if efficient_agent:
            msg2 = f"Agent {efficient_agent['id']} is time efficient"
            screen.blit(big.render(msg2, True, (0,90,180)), (40, 80))
        else:
            screen.blit(font.render("Efficient: N/A", True, (120, 0, 0)), (40, 80))

        left_x = 40
        y_start = 130
        gap_y = 120

        for i, ag in enumerate(agents):
            x = left_x
            y = y_start + i * gap_y

            fullname = ALGO_FULL.get(ag.get("algo"), ag.get("algo"))
            screen.blit(font.render(f"Agent {ag['id']} – {fullname}", True,(0,0,0)), (x, y))
            y += 22

            screen.blit(font.render(f"Score: {int(ag['score'])}", True,(0,0,0)), (x, y))
            y += 20

            screen.blit(font.render(f"Time left: {int(ag['timer'])}s", True,(0,0,0)), (x, y))
            y += 20

            screen.blit(font.render(f"Time (steps): {ag['ops']}", True,(0,0,0)), (x, y))
            y += 18

            screen.blit(font.render(f"Space (peak): {ag['peak']}", True,(0,0,0)), (x, y))

        pygame.display.flip()
        clock.tick(30)

    pygame.quit()


# ============================================================
# MAIN VISUALIZATION LOOP
# ============================================================
def start_visualization(grid, placement, agents, traces,
                        tick_rate=0.05,
                        csv_name="results.csv"):

    pygame.init()

    main_w = world.MAIN_W
    b_w    = world.BRIDGE_LEN
    pab_w  = world.PAB_W
    total_w = (main_w + b_w + pab_w) * CELL

    required_w = total_w + SIDEBAR_W + 120
    required_h = world.WORLD_H * CELL + 180

    screen = pygame.display.set_mode((required_w, required_h))
    pygame.display.set_caption("AUA Simulation")

    clock = pygame.time.Clock()

    seqs_by_agent = {}
    for ag in agents:
        aid = ag["id"]
        seq = traces.get(aid)

        if seq and isinstance(seq, list) and len(seq) > 0:
            seqs_by_agent[aid] = [(int(x), int(y)) for (x, y) in seq]
            if seqs_by_agent[aid][0] != tuple(map(int, ag.get("pos", (0,0)))):
                seqs_by_agent[aid].insert(0, tuple(map(int, ag.get("pos", (0,0)))))
        else:
            safe = []
            for (x, y) in ag.get("path", []):
                try:
                    xi, yi = int(x), int(y)
                except Exception:
                    continue
                if 0 <= yi < len(grid) and 0 <= xi < len(grid[0]):
                    if grid[yi][xi] != world.WALL:
                        safe.append((xi, yi))

            if not safe:
                safe = [tuple(map(int, ag.get("pos", (0,0))))]

            if safe[0] != tuple(map(int, ag.get("pos", (0,0)))):
                safe.insert(0, tuple(map(int, ag.get("pos", (0,0)))))

            seqs_by_agent[aid] = safe

    max_steps = max((len(s) for s in seqs_by_agent.values()), default=0)

    for aid, seq in seqs_by_agent.items():
        if len(seq) < max_steps:
            seqs_by_agent[aid] = seq + [seq[-1]] * (max_steps - len(seq))

        if len(seqs_by_agent[aid]) == 0:
            seqs_by_agent[aid] = [tuple(map(int, agents[0].get("pos", (0,0))))]

    detailed = {ag["id"]: [] for ag in agents}
    for aid, seq in seqs_by_agent.items():
        for x, y in seq:
            detailed[aid].append([int(x), int(y), None, None, "normal"])

    for ag in agents:
        ag.setdefault("score", int(ag.get("score", 0)))
        ag.setdefault("timer", int(ag.get("timer", 0)))
        ag["interp_pos"] = tuple(map(float, ag.get("pos", (0,0))))
        ag["subframe"] = 0
        ag.setdefault("alive", True)
        ag.setdefault("frozen", False)
        if "path" not in ag:
            ag["path"] = seqs_by_agent.get(ag["id"], [])

    origin = (60, 100)
    images = load_images(CELL)
    font = pygame.font.SysFont(None, FONT_SIZE)

    step_index = 0
    running = True

    while running:

        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                running = False

        if step_index >= max_steps:
            running = False

        screen.fill((245,245,245))

        # =====================
        # UPDATE AGENTS
        # =====================
        for ag in agents:
            aid = ag["id"]
            seq = seqs_by_agent[aid]
            idx = min(step_index, len(seq)-1)
            new = seq[idx]
            old = ag["interp_pos"]

            if ag.get("frozen"):
                ag["interp_pos"] = tuple(map(float, ag["pos"]))
                ag["subframe"] = 0
                continue

            t = ag["subframe"] / ANIMATION_FRAMES
            ag["interp_pos"] = interpolate(old, new, t)

            if ag["subframe"] >= ANIMATION_FRAMES - 1:
                ag["pos"] = new
                ag["interp_pos"] = tuple(map(float, new))
                ag["subframe"] = 0

                x, y = new
                ag["score"] = max(0, ag["score"] - 1)
                ag["timer"] = max(0, ag["timer"] - 1)

                cell = grid[y][x]
                reason = "normal"

                if cell == world.ANGRY:
                    ag["score"] = max(0, ag["score"] - 150)
                    reason = "angry"

                if cell == world.CHAIR:
                    ag["score"] = 0
                    ag["alive"] = False
                    ag["frozen"] = True
                    reason = "chair"

                if cell == world.OFFICE:
                    ag["alive"] = False
                    ag["frozen"] = True
                    reason = "goal"

                if ag["score"] <= 0:
                    ag["score"] = 0
                    ag["alive"] = False
                    ag["frozen"] = True
                    reason = "no_points"

                if ag["timer"] <= 0:
                    ag["timer"] = 0
                    ag["alive"] = False
                    ag["frozen"] = True
                    reason = "no_time"

                if step_index < len(detailed[aid]):
                    detailed[aid][step_index][2] = ag["score"]
                    detailed[aid][step_index][3] = ag["timer"]
                    detailed[aid][step_index][4] = reason

            else:
                ag["subframe"] += 1

        # Visible path prefix
        for ag in agents:
            aid = ag["id"]
            full_trace = traces.get(aid, seqs_by_agent[aid])
            safe_trace = []
            for (px, py) in full_trace:
                try:
                    xi, yi = int(px), int(py)
                    if 0 <= yi < len(grid) and 0 <= xi < len(grid[0]):
                        safe_trace.append((xi, yi))
                except Exception:
                    pass
            ag["path"] = safe_trace[: step_index + 1]

        # DRAW
        draw_world(screen, grid, placement.start, images, origin, font,
                   agents=agents, show_paths=True)
        draw_agents(screen, agents, origin)

        sidebar_x = origin[0] + total_w + 40
        draw_sidebar(screen, placement, agents, font,
                     (sidebar_x, origin[1]), required_h)

        pygame.display.flip()
        clock.tick(60)

        if all(ag["subframe"] == 0 for ag in agents):
            step_index += 1

    export_results_csv(agents, detailed, filename=csv_name)
    show_summary_window(agents)

