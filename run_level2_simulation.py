"""
run_level2_simulation.py
==========================
Phase 54: canonical Level 2 entry point — "python run_level2_simulation.py"
-> dynamic simulation.

Thin wrapper: the real logic lives in run_level2_dynamic_simulation.py
(kept for its more detailed docstring/history); this is the clean,
short name Phase 54 asks for.
"""

from run_level2_dynamic_simulation import main

if __name__ == "__main__":
    main()
