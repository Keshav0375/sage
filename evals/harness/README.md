# Harness evals

Tasks that test **sage itself** (do the agents, skills and hooks behave?), independent of any
project. Same format as project evals (see the `sagectl/evals.py` docstring). The split is
assigned by hash. `heldout/` is sealed: agents run it only through
`sagectl eval run --split heldout`.

The seed tasks are deliberately small and fast, so a baseline costs minutes, not hours.
Add the real ones from `/retro`: every critical lesson that can be reproduced becomes a task.
