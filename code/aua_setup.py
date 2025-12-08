"""
aua_setup.py
------------
Setup window for configuring The OH Race simulation.

This module provides a Tkinter UI for selecting:
- Algorithms for 3 agents (Hill-Climbing, Stochastic HC, Simulated Annealing)
- Main and PAB building widths
- Counts of Angry individuals and Walls in each building

The UI validates all constraints, and upon successful input,
stores values in the global CONFIG dictionary and closes.

Note:
Both `aua_ui.py` and `aua_ui_patched.py` are used in this project.
The patched version was created later to fix usability and rendering
issues discovered during integration and testing. Both remain in the
submission for completeness and reproducibility.
"""

import tkinter as tk
from tkinter import ttk, messagebox

# Fixed building heights (used elsewhere)
MAIN_H = 7
PAB_H = 5

# Global configuration dictionary to be filled by the UI
CONFIG = {
    "agent1_algo": None,
    "agent2_algo": None,
    "agent3_algo": None,
    "main_w": None,
    "pab_w": None,
    "angry_main": None,
    "angry_pab": None,
    "walls_main": None,
    "walls_pab": None,
}


# ============================================================================
#  Setup Window
# ============================================================================
def open_setup_window():
    """Launch the Tkinter setup dialog."""

    root = tk.Tk()
    root.title("AUA World Setup")
    root.resizable(False, False)

    main_frame = tk.Frame(root, padx=20, pady=20)
    main_frame.pack()

    # ============================================================================
    #  Agent Algorithm Selection
    # ============================================================================
    tk.Label(
        main_frame, text="Agent Algorithms:", font=("Arial", 13, "bold")
    ).grid(row=0, column=0, columnspan=2, pady=(0, 10), sticky="w")

    ALGO_LIST = ["Hill-Climbing", "Stochastic Hill Climbing", "Simulated Annealing"]

    def algo_selector(label: str, row: int):
        tk.Label(main_frame, text=label, font=("Arial", 11)).grid(
            row=row, column=0, sticky="w", pady=3
        )
        combo = ttk.Combobox(main_frame, values=ALGO_LIST, state="readonly", width=28)
        combo.grid(row=row, column=1, sticky="w")
        return combo

    agent1_var = algo_selector("Agent 1:", 1)
    agent2_var = algo_selector("Agent 2:", 2)
    agent3_var = algo_selector("Agent 3:", 3)

    tk.Label(main_frame, text="", height=1).grid(row=4)

    # ============================================================================
    #  Main Building Inputs
    # ============================================================================
    tk.Label(
        main_frame, text="Main Building:", font=("Arial", 13, "bold")
    ).grid(row=5, column=0, columnspan=2, pady=(10, 5), sticky="w")

    # Width
    tk.Label(main_frame, text="Width (tiles):", font=("Arial", 11)).grid(
        row=6, column=0, sticky="w"
    )
    main_w_var = tk.Entry(main_frame, width=12)
    main_w_var.grid(row=6, column=1, sticky="w")

    tk.Label(
        main_frame, text="Allowed width: 7 to 100", font=("Arial", 9), fg="gray"
    ).grid(row=7, column=1, sticky="w")

    # Angry
    tk.Label(main_frame, text="Angry Count:", font=("Arial", 11)).grid(
        row=8, column=0, sticky="w", pady=(6, 0)
    )
    angry_main_var = tk.Entry(main_frame, width=12)
    angry_main_var.grid(row=8, column=1, sticky="w")

    main_angry_range = tk.Label(main_frame, text="", font=("Arial", 9), fg="gray")
    main_angry_range.grid(row=9, column=1, sticky="w")

    # Walls
    tk.Label(main_frame, text="Walls Count:", font=("Arial", 11)).grid(
        row=10, column=0, sticky="w", pady=(6, 0)
    )
    walls_main_var = tk.Entry(main_frame, width=12)
    walls_main_var.grid(row=10, column=1, sticky="w")

    main_walls_range = tk.Label(main_frame, text="", font=("Arial", 9), fg="gray")
    main_walls_range.grid(row=11, column=1, sticky="w")

    # ============================================================================
    #  PAB Building Inputs
    # ============================================================================
    tk.Label(
        main_frame, text="PAB Building:", font=("Arial", 13, "bold")
    ).grid(row=12, column=0, columnspan=2, pady=(15, 5), sticky="w")

    # Width
    tk.Label(main_frame, text="Width (tiles):", font=("Arial", 11)).grid(
        row=13, column=0, sticky="w"
    )
    pab_w_var = tk.Entry(main_frame, width=12)
    pab_w_var.grid(row=13, column=1, sticky="w")

    tk.Label(
        main_frame, text="Allowed width: 4 to 80", font=("Arial", 9), fg="gray"
    ).grid(row=14, column=1, sticky="w")

    # Angry
    tk.Label(main_frame, text="Angry Count:", font=("Arial", 11)).grid(
        row=15, column=0, sticky="w", pady=(6, 0)
    )
    angry_pab_var = tk.Entry(main_frame, width=12)
    angry_pab_var.grid(row=15, column=1, sticky="w")

    pab_angry_range = tk.Label(main_frame, text="", font=("Arial", 9), fg="gray")
    pab_angry_range.grid(row=16, column=1, sticky="w")

    # Walls
    tk.Label(main_frame, text="Walls Count:", font=("Arial", 11)).grid(
        row=17, column=0, sticky="w", pady=(6, 0)
    )
    walls_pab_var = tk.Entry(main_frame, width=12)
    walls_pab_var.grid(row=17, column=1, sticky="w")

    pab_walls_range = tk.Label(main_frame, text="", font=("Arial", 9), fg="gray")
    pab_walls_range.grid(row=18, column=1, sticky="w")

    # ============================================================================
    #  Live Range Update Logic
    # ============================================================================
    def update_main_ranges(*_):
        """Update allowed Angry and Walls ranges for Main based on width."""
        try:
            w = int(main_w_var.get())
            if not (7 <= w <= 100):
                main_angry_range.config(text="")
                main_walls_range.config(text="")
                return

            main_angry_range.config(text=f"Allowed Angry: 0 to {w}")

            try:
                a = int(angry_main_var.get())
                if 0 <= a <= w:
                    main_walls_range.config(text=f"Allowed Walls: 0 to {w - a}")
                else:
                    main_walls_range.config(text="")
            except ValueError:
                main_walls_range.config(text="")
        except ValueError:
            main_angry_range.config(text="")
            main_walls_range.config(text="")

    def update_pab_ranges(*_):
        """Update allowed Angry and Walls ranges for PAB based on width."""
        try:
            w = int(pab_w_var.get())
            if not (4 <= w <= 80):
                pab_angry_range.config(text="")
                pab_walls_range.config(text="")
                return

            pab_angry_range.config(text=f"Allowed Angry: 0 to {w}")

            try:
                a = int(angry_pab_var.get())
                if 0 <= a <= w:
                    pab_walls_range.config(text=f"Allowed Walls: 0 to {w - a}")
                else:
                    pab_walls_range.config(text="")
            except ValueError:
                pab_walls_range.config(text="")
        except ValueError:
            pab_angry_range.config(text="")
            pab_walls_range.config(text="")

    # Bind updates
    for w in (main_w_var, angry_main_var):
        w.bind("<KeyRelease>", update_main_ranges)

    for w in (pab_w_var, angry_pab_var):
        w.bind("<KeyRelease>", update_pab_ranges)

    # ============================================================================
    #  Submit Button
    # ============================================================================
    def submit():
        """Validate inputs, write CONFIG, and close the window."""
        try:
            # Read values
            main_w = int(main_w_var.get())
            pab_w = int(pab_w_var.get())
            angry_main = int(angry_main_var.get())
            angry_pab = int(angry_pab_var.get())
            walls_main = int(walls_main_var.get())
            walls_pab = int(walls_pab_var.get())

            # --- Validation ---
            if not (7 <= main_w <= 100):
                messagebox.showerror("Error", "Main width must be 7–100.")
                return
            if not (4 <= pab_w <= 80):
                messagebox.showerror("Error", "PAB width must be 4–80.")
                return

            if not (0 <= angry_main <= main_w):
                messagebox.showerror("Error", f"Main Angry must be between 0 and {main_w}.")
                return
            if not (0 <= walls_main <= (main_w - angry_main)):
                messagebox.showerror(
                    "Error", f"Main Walls must be between 0 and {main_w - angry_main}."
                )
                return

            if not (0 <= angry_pab <= pab_w):
                messagebox.showerror("Error", f"PAB Angry must be between 0 and {pab_w}.")
                return
            if not (0 <= walls_pab <= (pab_w - angry_pab)):
                messagebox.showerror(
                    "Error", f"PAB Walls must be between 0 and {pab_w - angry_pab}."
                )
                return

            # Algorithm selection validation
            algos = [agent1_var.get(), agent2_var.get(), agent3_var.get()]
            if "" in algos:
                messagebox.showerror("Error", "All 3 agents must pick an algorithm.")
                return
            if len(set(algos)) != 3:
                messagebox.showerror("Error", "Agents must use different algorithms.")
                return

            # Save into global CONFIG
            CONFIG.update(
                {
                    "agent1_algo": algos[0],
                    "agent2_algo": algos[1],
                    "agent3_algo": algos[2],
                    "main_w": main_w,
                    "pab_w": pab_w,
                    "angry_main": angry_main,
                    "angry_pab": angry_pab,
                    "walls_main": walls_main,
                    "walls_pab": walls_pab,
                }
            )

            root.destroy()

        except ValueError:
            messagebox.showerror("Error", "Invalid numeric input.")

    tk.Button(
        main_frame, text="Start Game", width=22, command=submit
    ).grid(row=19, column=0, columnspan=2, pady=20)

    root.mainloop()
