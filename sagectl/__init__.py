"""sagectl — the deterministic half of sage.

Everything an agent should not be trusted to do by judgement lives here: locating the active
phase, flipping task status, running the gate, logging traces and lessons, mining failures,
running held-in/held-out evals, the trash, the statusline. Stdlib only, Python >= 3.11.
"""

__version__ = "0.1.0"
