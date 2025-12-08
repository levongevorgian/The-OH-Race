# The OH Race --- Multi-Agent Pathfinding & Search Algorithms Simulator

This repository implements **The OH Race**, a custom multi-agent
pathfinding and search-algorithm simulation developed for **CS 246/346
-- Artificial Intelligence (AUA)**.\
Agents navigate through a multi‑building environment (MAIN, PAB, Bridge)
using classical search and local optimization algorithms.

The system supports: - **Interactive UI simulation** (pygame) -
**Headless batch mode** (Multiple seeds, no UI, automated CSV output) -
**Automated experiment pipelines** for academic reporting

------------------------------------------------------------------------

## 📁 Directory Structure

### Core Modules

#### [`aua_world.py`](aua_world.py)

World geometry, cell layout, BFS helpers, building definitions.

#### [`controller.py`](controller.py)

Agent coordination, simulation loop, metric tracking, collision
handling.

#### [`search_algorithms.py`](search_algorithms.py)

Implements 9 algorithms: - BFS\
- DFS\
- UCS\
- Greedy Best-First Search\
- A\*\
- Weighted A\*\
- Hill Climbing\
- Simulated Annealing\
- Random Restart Local Search

#### [`aua_setup.py`](aua_setup.py)

Parameter selection module for UI mode.

#### [`aua_ui.py`](aua_ui.py)

pygame interface for interactive visualization.

#### [`aua_ui_patched.py`](aua_ui_patched.py)

Fully headless module for automated batch runs (no window).

#### [`batch_runner.py`](batch_runner.py)

Runs **30 simulations** automatically using different random seeds and
saves metrics.

------------------------------------------------------------------------

## 📂 Results Directory Structure

All experiment outputs are stored under the `csv/` directory:

    csv/
        run_set_1/
            run_001.csv
            run_002.csv
            ...
            run_030.csv

        run_set_2/
            run_001.csv
            ...
            run_030.csv

        run_set_3/
            run_001.csv
            ...
            run_030.csv

Each folder corresponds to a separate batch experiment, and each
contains **30 CSV files**, one per simulation run (different seed →
different initial placement).

Each CSV includes: - Steps\
- Expansions\
- Runtime\
- Collisions\
- Success/failure flag\
- Final path length\
- Algorithm used

------------------------------------------------------------------------

## 📑 Report and Visualizations

### `report/`

This folder contains the academic components of the project:

-   **`final_report.pdf`**\
    The complete academic report submitted for the course.

-   **`analysis.Rmd`**\
    An R Markdown script containing:

    -   CSV loading
    -   Data aggregation
    -   Visualizations (boxplots, comparisons)
    -   Algorithm performance analysis

-   **`analysis.pdf`**\
    The knitted output of `analysis.Rmd`, containing:

    -   Final figures\
    -   Plots\
    -   Statistical summaries\
    -   Explanation of findings

**The R Markdown workflow allows complete reproducibility of the plots
and statistical analysis in the report.**

------------------------------------------------------------------------

## 🚀 Installation

``` bash
pip install -r requirements.txt
```

------------------------------------------------------------------------

## ▶️ Interactive UI Mode (pygame window)

``` bash
python3 aua_ui.py
```

Provides step-by-step visualization for demonstrations.

------------------------------------------------------------------------

## 🤖 Headless Batch Mode (30-run experiments)

``` bash
python3 batch_runner.py
```

This will generate:

    csv/run_set_X/run_001.csv
    ...
    csv/run_set_X/run_030.csv

No window is opened.

------------------------------------------------------------------------

## 🧪 Algorithms Compared

This project benchmarks classical and local-search AI algorithms in the
same controlled world.\
Metrics allow cross‑algorithm comparison using R Markdown analysis.

------------------------------------------------------------------------

## 📘 Licensing

MIT License --- see [`LICENSE`](LICENSE).
