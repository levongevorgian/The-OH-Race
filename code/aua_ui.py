"""
aua_ui.py — Original User Interface (UI) for the AUA AI Course Project.

This module implements the **first version of the graphical user interface**
for the artificial world used in the project. It displays the grid environment,
tiles, agents, the sidebar with useful information, and allows interactive
scrolling and regeneration of the world using keyboard/mouse input.

The later module `aua_ui_patched.py` was developed as an **improved version**
of this UI to address functional limitations discovered after testing,
including responsiveness issues, world-size scaling problems, and rendering
bugs when combined with multiple agents or algorithmic animations.

Both files are included in the project submission to demonstrate the
development history and the evolution from the original UI design
(this file) to the patched, enhanced version.
"""

import sys
import argparse
import pygame
from typing import Tuple

import aua_world as world
from aua_setup import open_setup_window, CONFIG


# ============================
# Global UI Configuration
# ============================
CELL = None
SIDEBAR_W = None
MARGIN = 16
FONT_SIZE = None
TITLE_FONT_SIZE = None


# ============================
# Image Loading
# ============================
def load_images(cell_size):
    """Load and scale tile images based on the cell size."""
    def load(path):
        img = pygame.image.load(path).convert_alpha()
        return pygame.transform.scale(img, (cell_size, cell_size))

    return {
        world.WALL:   load("/Users/levongevorgyan/Downloads/AUA_AI_Project 4/images/wall.png"),
        world.ANGRY:  load("/Users/levongevorgyan/Downloads/AUA_AI_Project 4/images/angry_prof.png"),
        world.CHAIR:  load("/Users/levongevorgyan/Downloads/AUA_AI_Project 4/images/program_chair.png"),
        world.OFFICE: load("/Users/levongevorgyan/Downloads/AUA_AI_Project 4/images/OH_prof.png"),
    }


COLORS = {
    world.EMPTY:  (238, 238, 238),
    world.WALL:   (12, 12, 12),
    world.BRIDGE: (33, 111, 255),
    world.ANGRY:  (230, 85, 13),
    world.CHAIR:  (156, 39, 176),
    world.OFFICE: (46, 125, 50),
}


# ============================
# Drawing Helpers
# ============================
def draw_grid_lines(surface: pygame.Surface, origin: Tuple[int, int], w: int, h: int):
    """Draw grid lines for tiles."""
    ox, oy = origin
    for x in range(w + 1):
        X = ox + x * CELL
        pygame.draw.line(surface, (180, 180, 180), (X, oy), (X, oy + h * CELL), 1)

    for y in range(h + 1):
        Y = oy + y * CELL
        pygame.draw.line(surface, (180, 180, 180), (ox, Y), (ox + w * CELL, Y), 1)


def draw_world(
    surface,
    grid,
    start_pos,
    images,
    origin,
    font,
    scroll_x=0,
    agents=None
):
    """Draw the entire world including buildings, labels, and agents."""
    ox, oy = origin
    main_h, main_w = world.WORLD_H, world.MAIN_W
    pab_h, pab_w = world.PAB_H, world.PAB_W
    bridge_len = world.BRIDGE_LEN
    bridge_row = world.BRIDGE_ROW

    # --- MAIN BUILDING ---
    for y in range(main_h):
        for x in range(main_w):
            cell_id = grid[y][x]
            rect = pygame.Rect(
                ox + x * CELL - scroll_x,
                oy + (main_h - 1 - y) * CELL,
                CELL, CELL
            )
            pygame.draw.rect(surface, COLORS.get(cell_id, (200, 200, 200)), rect)
            img = images.get(cell_id)
            if img:
                surface.blit(img, rect.topleft)

    # --- BRIDGE ---
    for bx in range(main_w, main_w + bridge_len):
        y = bridge_row
        cell_id = grid[y][bx]
        rect = pygame.Rect(
            ox + bx * CELL - scroll_x,
            oy + (main_h - 1 - y) * CELL,
            CELL, CELL
        )
        pygame.draw.rect(surface, COLORS.get(cell_id, (120, 120, 255)), rect)
        img = images.get(cell_id)
        if img:
            surface.blit(img, rect.topleft)

    # --- PAB BUILDING ---
    for py in range(pab_h):
        for px in range(pab_w):
            wx, wy = world.pab_local_to_world(px, py)
            cell_id = grid[wy][wx]
            rect = pygame.Rect(
                ox + wx * CELL - scroll_x,
                oy + (main_h - 1 - wy) * CELL,
                CELL, CELL
            )
            pygame.draw.rect(surface, COLORS.get(cell_id, (200, 200, 200)), rect)
            img = images.get(cell_id)
            if img:
                surface.blit(img, rect.topleft)

    # --- LABELS ---
    title_font = pygame.font.SysFont(None, TITLE_FONT_SIZE)
    surface.blit(title_font.render("Main Building", True, (0, 0, 0)),
                 (ox + 2 - scroll_x, oy - 26))

    pab_start_x = main_w + bridge_len
    surface.blit(title_font.render("PAB", True, (0, 0, 0)),
                 (ox + pab_start_x * CELL - scroll_x + 6, oy - 26))

    surface.blit(
        font.render("Bridge", True, (30, 90, 200)),
        (ox + main_w * CELL - scroll_x + 5,
         oy + (main_h - 1 - bridge_row) * CELL - 20)
    )

    # --- START MARKER ---
    sx, sy = start_pos
    start_rect = pygame.Rect(
        ox + sx * CELL - scroll_x,
        oy + (main_h - 1 - sy) * CELL,
        CELL, CELL
    )
    badge = pygame.Surface((CELL, CELL), pygame.SRCALPHA)
    pygame.draw.rect(badge, (0, 0, 0, 100), badge.get_rect(), border_radius=6)
    surface.blit(badge, start_rect.topleft)

    txt = font.render("S", True, (255, 255, 255))
    surface.blit(
        txt,
        (
            start_rect.x + CELL // 2 - txt.get_width() // 2,
            start_rect.y + CELL // 2 - txt.get_height() // 2
        )
    )

    # --- AGENTS ---
    if agents is not None:
        agent_colors = {1: (220, 20, 60), 2: (20, 90, 220), 3: (20, 170, 70)}
        offsets = {1: (-6, -6), 2: (6, -6), 3: (0, 6)}

        for ag in agents:
            ax, ay = ag["pos"]
            sx = ox + ax * CELL - scroll_x + CELL // 2
            sy = oy + (main_h - 1 - ay) * CELL + CELL // 2
            dx, dy = offsets.get(ag["id"], (0, 0))

            pygame.draw.circle(
                surface,
                agent_colors.get(ag["id"], (0, 0, 0)),
                (sx + dx, sy + dy),
                CELL // 3
            )

    # --- GRID LINES ---
    draw_grid_lines(surface, (ox - scroll_x, oy), main_w, main_h)

    draw_grid_lines(
        surface,
        (ox + main_w * CELL - scroll_x,
         oy + (main_h - 1 - bridge_row) * CELL),
        bridge_len, 1
    )

    pab_origin = (
        ox + (main_w + bridge_len) * CELL - scroll_x,
        oy + (main_h - 1 - (world.PAB_ROW_OFFSET + world.PAB_H - 1)) * CELL
    )
    draw_grid_lines(surface, pab_origin, pab_w, pab_h)


# ============================
# Sidebar Rendering
# ============================
def draw_sidebar(
    surface,
    placement,
    seed,
    origin,
    font,
    scroll_x=0,
    measure_only=False,
    agents=None
):
    """Draw sidebar with seed, legend, placement details, and agent status."""
    ox, oy = origin
    actual_grid_w = (world.MAIN_W + world.BRIDGE_LEN + world.PAB_W) * CELL
    x0 = ox + actual_grid_w + 140 - scroll_x

    sidebar_y = oy
    max_text_width = 0

    def text_width(text, font_obj=font):
        nonlocal max_text_width
        w = font_obj.render(text, True, (0, 0, 0)).get_width()
        max_text_width = max(max_text_width, w)
        return w

    def line(text, color=(20, 20, 20), bump=4):
        nonlocal sidebar_y
        text_width(text)
        if not measure_only:
            surface.blit(font.render(text, True, color), (x0, sidebar_y))
        sidebar_y += FONT_SIZE + bump

    # Title
    title_font = pygame.font.SysFont(None, TITLE_FONT_SIZE)
    text_width("AUA Grid Viewer", title_font)

    if not measure_only:
        surface.blit(
            title_font.render("AUA Grid Viewer", True, (10, 10, 10)),
            (x0, sidebar_y)
        )
    sidebar_y += TITLE_FONT_SIZE + 10

    # Seed
    if seed is not None:
        line(f"Seed: {seed}")

    sidebar_y += 10
    line("Keys:", (0, 0, 0))
    line("  R – regenerate")
    line("  S – save screenshot")
    line("  Esc / Q – quit")

    sidebar_y += 12
    line("Legend:", (0, 0, 0))

    legend_swatches = [
        ("Empty", world.EMPTY), ("Wall", world.WALL), ("Bridge", world.BRIDGE),
        ("Angry Prof", world.ANGRY), ("Program Chair", world.CHAIR),
        ("Office Hour", world.OFFICE),
    ]

    for label, cid in legend_swatches:
        text_width(label)
        if not measure_only:
            sw = pygame.Rect(x0, sidebar_y + 3, 18, 18)
            pygame.draw.rect(surface, COLORS.get(cid, (200, 200, 200)), sw)
            surface.blit(font.render(label, True, (20, 20, 20)),
                         (x0 + 26, sidebar_y))
        sidebar_y += FONT_SIZE + 6

    # Agent scores
    if agents is not None:
        sidebar_y += 20
        if not measure_only:
            surface.blit(font.render("Agent Scores:", True, (0, 0, 0)),
                         (x0, sidebar_y))
        sidebar_y += FONT_SIZE + 6

        for ag in agents:
            text = f"Agent {ag['id']}: {ag['score']}"
            if not measure_only:
                surface.blit(font.render(text, True, (0, 0, 0)),
                             (x0, sidebar_y))
            sidebar_y += FONT_SIZE + 6

    sidebar_y += 12
    line("Placements:", (0, 0, 0))

    placement_lines = [
        f"Start: {placement.start}",
        f"Walls(Main): {len(placement.walls_main)}",
        f"Walls(PAB):  {len(placement.walls_pab)}",
        f"Angry(Main): {len(placement.angry_main)}",
        f"Angry(PAB):  {len(placement.angry_pab)}",
        f"Chair: {placement.chair}",
        f"Office: {placement.office}",
    ]
    for t in placement_lines:
        text_width(t)
        line(t)

    # Agent timers
    if agents is not None:
        sidebar_y += 20
        if not measure_only:
            surface.blit(font.render("Agent Timers:", True, (0, 0, 0)),
                         (x0, sidebar_y))
        sidebar_y += FONT_SIZE + 6

        for ag in agents:
            t = max(0, int(ag["timer"]))
            mm, ss = t // 60, t % 60
            text = f"Agent {ag['id']}: {mm:02d}:{ss:02d}"

            if not measure_only:
                surface.blit(font.render(text, True, (0, 0, 0)),
                             (x0, sidebar_y))
            sidebar_y += FONT_SIZE + 6

    return {"height": sidebar_y - oy, "width": max_text_width + 80}


# ============================
# Main Event Loop
# ============================
def main():
    """Run the interactive scrollable viewer UI."""
    open_setup_window()

    # Update world width values based on setup selection
    world.MAIN_W = int(CONFIG["main_w"])
    world.PAB_W = int(CONFIG["pab_w"])
    world.WORLD_W = world.MAIN_W + world.BRIDGE_LEN + world.PAB_W

    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=None)
    args = parser.parse_args()

    pygame.init()
    info = pygame.display.Info()
    screen_w, screen_h = info.current_w, info.current_h

    world_w_tiles = world.MAIN_W + world.BRIDGE_LEN + world.PAB_W
    world_h_tiles = world.WORLD_H

    global CELL, SIDEBAR_W, FONT_SIZE, TITLE_FONT_SIZE
    CELL = 35
    SIDEBAR_W = 360
    FONT_SIZE = 18
    TITLE_FONT_SIZE = 24

    PADDING_X = int(CELL * 1.5)
    PADDING_Y = int(CELL * 0.4)

    actual_grid_w = world_w_tiles * CELL
    actual_grid_h = world_h_tiles * CELL
    font = pygame.font.SysFont(None, FONT_SIZE)

    # Build world
    def build(seed=None):
        return world.build_world(seed=seed)

    current_seed = args.seed
    grid, placement = build(current_seed)

    # Agents
    start_pos = placement.start
    agents = [
        {"id": 1, "timer": 300, "score": 1000, "pos": start_pos},
        {"id": 2, "timer": 300, "score": 1000, "pos": start_pos},
        {"id": 3, "timer": 300, "score": 1000, "pos": start_pos},
    ]

    # Measure sidebar
    measurement = draw_sidebar(
        pygame.Surface((1, 1)),
        placement,
        current_seed,
        (PADDING_X, PADDING_Y),
        font,
        scroll_x=0,
        measure_only=True,
        agents=agents
    )

    estimated_sidebar_height = measurement["height"]
    SIDEBAR_W = measurement["width"]

    grid_h_px = actual_grid_h + PADDING_Y * 2
    sidebar_h_px = estimated_sidebar_height + PADDING_Y * 2
    world_surface_h = max(grid_h_px, sidebar_h_px)

    viewer_w = int(screen_w * 0.85)
    viewer_h = min(world_surface_h, screen_h)

    screen = pygame.display.set_mode((viewer_w, viewer_h))
    pygame.display.set_caption("AUA Scrollable Viewer")

    world_surface_w = actual_grid_w + SIDEBAR_W + PADDING_X * 2
    world_surface = pygame.Surface((world_surface_w, world_surface_h))

    origin = (PADDING_X, (world_surface_h - actual_grid_h) // 2)
    sidebar_origin = (PADDING_X, PADDING_Y)

    images = load_images(CELL)

    # Scrolling
    scroll_x = 0
    SCROLL_SPEED = int(CELL * 2.5)

    dragging_world = False
    drag_start_x = 0
    scroll_start_x = 0

    # Scrollbar
    SCROLLBAR_HEIGHT = 10
    SCROLLBAR_BG = (220, 220, 220)
    SCROLLBAR_FG = (120, 120, 120)
    SCROLLBAR_MARGIN = 8

    scrollbar_y = viewer_h - SCROLLBAR_HEIGHT - SCROLLBAR_MARGIN
    scrollbar_x = 10
    scrollbar_w = viewer_w - 20

    dragging_thumb = False
    thumb_drag_offset = 0

    clock = pygame.time.Clock()
    running = True

    while running:
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                running = False

            elif ev.type == pygame.KEYDOWN:
                if ev.key in (pygame.K_ESCAPE, pygame.K_q):
                    running = False
                elif ev.key == pygame.K_RIGHT:
                    scroll_x += SCROLL_SPEED
                elif ev.key == pygame.K_LEFT:
                    scroll_x -= SCROLL_SPEED
                elif ev.key == pygame.K_r:
                    current_seed = (current_seed or 0) + 1
                    grid, placement = build(current_seed)

            mx, my = pygame.mouse.get_pos()

            # Mouse interactions
            if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                if (
                    scrollbar_y <= my <= scrollbar_y + SCROLLBAR_HEIGHT
                    and "thumb_x" in locals()
                    and thumb_x <= mx <= thumb_x + thumb_w
                ):
                    dragging_thumb = True
                    thumb_drag_offset = mx - thumb_x
                else:
                    dragging_world = True
                    drag_start_x = mx
                    scroll_start_x = scroll_x

            elif ev.type == pygame.MOUSEBUTTONUP and ev.button == 1:
                dragging_world = False
                dragging_thumb = False

            elif ev.type == pygame.MOUSEMOTION:
                if dragging_world:
                    dx = mx - drag_start_x
                    scroll_x = scroll_start_x - dx
                elif dragging_thumb:
                    new_thumb_x = mx - thumb_drag_offset
                    new_thumb_x = max(scrollbar_x,
                                      min(new_thumb_x, scrollbar_x + scrollbar_w - thumb_w))
                    scroll_ratio = (new_thumb_x - scrollbar_x) / (scrollbar_w - thumb_w)
                    scroll_x = scroll_ratio * max_scroll

        max_scroll = max(0, world_surface_w - viewer_w)

        # Update agent timers
        dt = clock.get_time() / 1000.0
        for a in agents:
            if a["timer"] > 0:
                a["timer"] -= dt

        scroll_x = max(0, min(scroll_x, max_scroll))

        # Draw world + sidebar
        world_surface.fill((245, 245, 245))
        draw_world(world_surface, grid, placement.start, images, origin, font, scroll_x, agents)
        draw_sidebar(world_surface, placement, current_seed, sidebar_origin, font, scroll_x, agents)

        # Render to screen
        screen.fill((245, 245, 245))
        screen.blit(world_surface, (-scroll_x, 0))

        # Scrollbar background
        pygame.draw.rect(
            screen,
            SCROLLBAR_BG,
            (scrollbar_x, scrollbar_y, scrollbar_w, SCROLLBAR_HEIGHT),
            border_radius=6
        )

        thumb_ratio = viewer_w / world_surface_w if world_surface_w > 0 else 1.0
        thumb_w = max(40, scrollbar_w * thumb_ratio)

        if max_scroll > 0:
            thumb_x = scrollbar_x + (scroll_x / max_scroll) * (scrollbar_w - thumb_w)
        else:
            thumb_x = scrollbar_x

        # Scrollbar thumb
        pygame.draw.rect(
            screen,
            SCROLLBAR_FG,
            (thumb_x, scrollbar_y, thumb_w, SCROLLBAR_HEIGHT),
            border_radius=6
        )

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
